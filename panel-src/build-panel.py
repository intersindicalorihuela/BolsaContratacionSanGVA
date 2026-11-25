#!/usr/bin/env python3
"""Genera panel/index.html (Panel Bolsa) a partir de los index.html publicados
de BolsaSanGVA y Contrataciones. El cruce se precomputa aquí, en el build:
el HTML final solo lleva resultados agregados, no los dos datasets enteros.

Uso:
  python3 build-panel.py --bolsa <ruta|url> --contrataciones <ruta|url> --out ../index.html

Las rutas pueden ser ficheros locales o URLs (GitHub Pages).
"""
import argparse, json, re, unicodedata, datetime as dt
import urllib.request

DPTS = ["ELCHE", "ORIHUELA", "TORREVIEJA"]
EPOCH = dt.date(1970, 1, 1)

# ---------- extracción de los blobs embebidos ----------

def blob_bolsa(html):
    m = re.search(r"const BOLSA_DATA = JSON\.parse\('", html)
    if not m:
        raise SystemExit("ERROR: no encuentro BOLSA_DATA en el index de la bolsa")
    start, i, esc = m.end(), m.end(), False
    while i < len(html):
        c = html[i]
        if esc:
            esc = False
        elif c == "\\":
            esc = True
        elif c == "'":
            break
        i += 1
    s = html[start:i].replace("\\\\", "\x00").replace("\\'", "'")
    return json.loads(s.replace("\x00", "\\"))

def blob_contra(html):
    m = re.search(r'"maxfecha"', html)
    if not m:
        raise SystemExit("ERROR: no encuentro los datos de contrataciones")
    start = html.rfind("{", 0, m.start())
    depth, instr, esc = 0, False, False
    for i in range(start, len(html)):
        c = html[i]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
        else:
            if c == '"':
                instr = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(html[start:i + 1])
    raise SystemExit("ERROR: JSON de contrataciones sin cerrar")

def cargar(src):
    if re.match(r"^https?://", src):
        req = urllib.request.Request(src, headers={"User-Agent": "panel-bolsa-build"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read().decode("utf-8")
    with open(src, encoding="utf-8") as f:
        return f.read()

# ---------- normalización ----------

def catnorm(s):
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", s)

def nnorm(s):
    s = unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode().upper()
    s = s.replace("ª", " ")
    s = re.sub(r"(^| )M( |$)", r"\1MARIA\2", s)
    s = re.sub(r"[^A-Z ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

CAT_LABELS = {
    "ADMINISTRATIVO": "Administrativo/a",
    "AUXILIAR ADMINISTRATIVO": "Auxiliar Administrativo/a",
    "CELADOR": "Celador/a",
    "ENFERMERA/O": "Enfermera/o",
    "TÉCNICO/A EN CUIDADOS AUXILIARES DE ENFERMERÍA": "TCAE",
    "T.E. LABORATORIO": "T.E. Laboratorio",
    "T.E. EN IMAGEN PARA EL DIAGNÓSTICO Y MEDICINA NUCLEAR": "T.E. Imagen p/ Diagnóstico",
    "TÉCNICO/A EN FARMACIA": "Técnico/a Farmacia",
    "FISIOTERAPEUTA": "Fisioterapeuta",
    "HIGIENISTA_DENTAL": "Higienista Dental",
    "TE_ANATOMIA_PATOLOGICA": "T.E. Anatomía Patológica",
    "OPTICO-OPTOMETRISTA": "Óptico-Optometrista",
    "TECNICO_DE_FUNCION_ADMINISTRATIVA": "Técnico/a Función Administrativa",
    "GESTION_FUNCION_ADMINISTRATIVA": "Gestión Función Administrativa",
}

def bucket(situ):
    s = (situ or "").upper()
    if s == "ACTIVA":
        return "A"
    if s.startswith("DISPONIBLE"):
        return "D"
    if s.startswith("ACTIVO (NO VACANTE)"):
        return "U" if "DISPONIBLE ESPECIAL" in s else "W"
    if s.startswith("ACTIVO EN PLAZA VACANTE"):
        return "V"
    if s.startswith("ACTIVO"):
        return "E" if "DISPONIBLE ESPECIAL" in s else "A"
    if s.startswith("BLOQUEADO"):
        return "B"
    if s.startswith("RESERVADO"):
        return "R"
    if s.startswith(("DESACTIVADO", "NO DISPONIBLE", "NO LOCALIZABLE")):
        return "N"
    return "O"

BUCKET_LBL = {"D": "DISPONIBLE", "E": "ACTIVO (DISPONIBLE ESPECIAL)",
              "U": "ACTIVO (No vacante) (DISPONIBLE ESPECIAL)",
              "A": "ACTIVO", "V": "ACTIVO EN PLAZA VACANTE", "W": "ACTIVO (No vacante)",
              "B": "BLOQUEADO", "R": "RESERVADO", "N": "NO DISPONIBLE / DESACTIVADO", "O": "OTRA SITUACIÓN"}

BUCKET_SITU = {
    "D": ["DISPONIBLE"],
    "E": ["ACTIVO (DISPONIBLE ESPECIAL)"],
    "U": ["ACTIVO (No vacante) (DISPONIBLE ESPECIAL)"],
    "A": ["ACTIVO", "ACTIVA"],
    "V": ["ACTIVO EN PLAZA VACANTE", "ACTIVO EN PLAZA VACANTE (DISP. VACANTES +5 AÑOS)"],
    "W": ["ACTIVO (No vacante)"],
    "B": ["BLOQUEADO", "BLOQUEADO (DISPONIBLE ESPECIAL)"],
    "R": ["RESERVADO", "RESERVADO (DISPONIBLE ESPECIAL)"],
    "N": ["DESACTIVADO", "DESACTIVADO (NO LOCALIZABLE)", "DESACTIVADO/A DE OFICIO",
          "NO DISPONIBLE OTROS", "NO DISPONIBLE POR PENALIZACIÓN", "NO DISPONIBLE PROVISIONAL",
          "NO DISPONIBLE RENUNCIA JUSTIFICADA", "NO DISPONIBLE RENUNCIA VOLUNTARIA", "NO LOCALIZABLE"],
    "O": ["Cualquier otra situación no incluida arriba"],
}

BUCKET_ORDEN = ["D", "E", "U", "A", "V", "W", "B", "R", "N", "O"]
BUCKET_LLAMABLE = {"A", "D", "E", "U"}

# ---------- build ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bolsa", required=True)
    ap.add_argument("--contrataciones", required=True)
    ap.add_argument("--tpl", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    bolsa = blob_bolsa(cargar(args.bolsa))
    contra = blob_contra(cargar(args.contrataciones))

    sel = [r for r in contra["rows"]
           if contra["dptos"][r[3]] in DPTS and r[5] is not None]

    names = set()
    for c in bolsa["categories"]:
        for row in bolsa["candidates"][c["id"]]:
            names.add(nnorm(row[1]))
    for r in sel:
        names.add(nnorm(r[0]))
    names = sorted(names)
    nidx = {n: i for i, n in enumerate(names)}

    ccats = contra["cats"]

    # --- grupos de bolsa ---
    grupos = []
    gidx = {}
    for c in sorted(bolsa["categories"], key=lambda x: x["id"]):
        parts = c["id"].split("·")
        base, pi, dpto = parts[0], len(parts) == 3, parts[-1]
        kstr = f"{catnorm(base)}|{'1' if pi else '0'}|{dpto}"
        gi = gidx.get(kstr)
        if gi is None:
            cat_lbl = CAT_LABELS.get(base, base.replace("_", " ").title())
            ccat_i = None
            for i, lbl in enumerate(ccats):
                if catnorm(lbl) == catnorm(base):
                    cat_lbl = CAT_LABELS.get(lbl, lbl.title())
                    ccat_i = i
                    break
            grupos.append({"id": kstr, "cat": cat_lbl, "pi": pi, "dpto": dpto, "ccat": ccat_i,
                           "situ": [], "filas": [], "act": [], "cnt": {}})
            gi = len(grupos) - 1
            gidx[kstr] = gi
        g = grupos[gi]
        filas = []
        pf_lista = [p for p in (c.get("perfiles") or []) if p and p != "Perfiles:"]
        pf_map = {}
        for row in sorted(bolsa["candidates"][c["id"]], key=lambda x: x[0]):
            s = row[2] or ""
            si = g["situ"].index(s) if s in g["situ"] else (g["situ"].append(s) or len(g["situ"]) - 1)
            b = bucket(s)
            filas.append([int(row[0]), nidx[nnorm(row[1])], b, si])
            g["cnt"][b] = g["cnt"].get(b, 0) + 1
            if b in BUCKET_LLAMABLE:
                g["act"].append(int(row[0]))
            pf_raw = (row[5] if len(row) > 5 else "") or ""
            if pf_raw and pf_raw.strip() != "Perfiles:":
                pfs = [x.strip() for x in pf_raw.split("|")]
                pfs = [x for x in pfs if x and x != "Perfiles:"]
                if pfs:
                    ni_ = filas[-1][1]
                    pset = pf_map.setdefault(ni_, set())
                    for p in pfs:
                        if p not in pf_lista:
                            pf_lista.append(p)
                        pset.add(pf_lista.index(p))
        g["filas"] = filas
        if pf_map:
            g["pfLista"] = pf_lista
            g["pf"] = [[ni, sorted(pf_map[ni])] for ni in sorted(pf_map)]

    maxf = EPOCH + dt.timedelta(days=contra["maxfecha"])
    dcorte = EPOCH + dt.timedelta(days=contra["corte"])
    data = {
        "bOrden": BUCKET_ORDEN,
        "fBolsa": bolsa.get("generated", ""),
        "corte": dcorte.isoformat(),
        "dpts": DPTS,
        "bucketLbl": BUCKET_LBL,
        "bucketSit": BUCKET_SITU,
        "names": names,
        "grupos": grupos,
        "contratos": [[nidx[nnorm(r[0])], r[1], DPTS.index(contra["dptos"][r[3]]),
                       r[4], r[5], r[6], r[7], r[8], r[9], r[10],
                       (r[2] if r[2] >= 0 else None)] for r in sel],
        "ccats": ccats,
        "perfiles": contra["perfiles"],
        "tnom": {"A": "Acumulación de tareas", "C": "ATC/Guardias", "I": "Interinidad (vacante)",
                 "S": "Sustitución (también reserva de plaza)"},
    }

    html = open(args.tpl, encoding="utf-8").read()
    js = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    js = js.replace("\\", "\\\\").replace("'", "\\'").replace("</", "<\\/")
    html = html.replace("{{DATA}}", js)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)

    act_total = sum(sum(g["cnt"].get(b, 0) for b in BUCKET_LLAMABLE) for g in grupos)
    print(f"OK: {len(grupos)} grupos de bolsa · {len(names)} nombres · {len(sel)} contratos en {'+'.join(DPTS)}")
    print(f"    activos: {act_total} · corte {data['corte']} · bolsa {data['fBolsa']}")
    import os
    print(f"    {args.out}: {os.path.getsize(args.out)/1024:.0f} KB")

if __name__ == "__main__":
    main()
