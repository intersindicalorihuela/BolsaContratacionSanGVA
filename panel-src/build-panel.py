#!/usr/bin/env python3
"""Genera panel/index.html (Panel Bolsa) a partir de los index.html publicados
de BolsaSanGVA y Contrataciones. El cruce se precomputa aquí, en el build:
el HTML final solo lleva resultados agregados, no los dos datasets enteros.

Uso:
  python3 build-panel.py --bolsa <ruta|url> --contrataciones <ruta|url> --out ../panel/index.html

Las rutas pueden ser ficheros locales o URLs (GitHub Pages).
"""
import argparse, json, re, unicodedata, datetime as dt
import urllib.request
from collections import defaultdict

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
    if s.startswith("ACTIVO EN PLAZA VACANTE"):
        return "V"
    if s.startswith("ACTIVO"):
        return "A"
    if s.startswith("BLOQUEADO"):
        return "B"
    if s.startswith("RESERVADO"):
        return "R"
    if s.startswith(("DESACTIVADO", "NO DISPONIBLE", "NO LOCALIZABLE")):
        return "N"
    return "O"

BUCKET_LBL = {"A": "ACTIVO", "V": "EN PLAZA VACANTE", "B": "BLOQUEADO",
              "R": "RESERVADO", "N": "NO DISPONIBLE", "O": "OTRA SITUACIÓN"}

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
    ccatsN = {catnorm(c): c for c in ccats}

    # --- grupos de bolsa ---
    grupos = []
    gidx = {}
    for c in sorted(bolsa["categories"], key=lambda x: x["id"]):
        parts = c["id"].split("·")
        base, pi, dpto = parts[0], len(parts) == 3, parts[-1]
        kstr = f"{catnorm(base)}|{'1' if pi else '0'}|{dpto}"
        gi = gidx.get(kstr)
        if gi is None:
            cc = ccatsN.get(catnorm(base))
            cat_lbl = CAT_LABELS.get(cc, CAT_LABELS.get(base, base.replace("_", " ").title())) if cc else \
                      CAT_LABELS.get(base, base.replace("_", " ").title())
            grupos.append({"id": kstr, "cat": cat_lbl, "pi": pi, "dpto": dpto,
                           "situ": [], "filas": [], "act": [], "meses": {}, "llam": {}, "cnt": {}})
            gi = len(grupos) - 1
            gidx[kstr] = gi
        g = grupos[gi]
        filas = []
        for row in sorted(bolsa["candidates"][c["id"]], key=lambda x: x[0]):
            s = row[2] or ""
            si = g["situ"].index(s) if s in g["situ"] else (g["situ"].append(s) or len(g["situ"]) - 1)
            b = bucket(s)
            filas.append([int(row[0]), nidx[nnorm(row[1])], b, si])
            g["cnt"][b] = g["cnt"].get(b, 0) + 1
            if b == "A":
                g["act"].append(int(row[0]))
        g["filas"] = filas

    # --- contratos: meses por grupo + puestos llamados (por nombre) ---
    pos2ni = [dict((f[0], f[1]) for f in g["filas"]) for g in grupos]
    name2ni = [set(f[1] for f in g["filas"]) for g in grupos]
    meses_by_g = [defaultdict(int) for _ in grupos]
    llam_by_g = [defaultdict(set) for _ in grupos]
    for r in sel:
        catn = catnorm(ccats[r[1]])
        dpto = contra["dptos"][r[3]]
        pi = r[7] == "P"
        m = (EPOCH + dt.timedelta(days=r[5])).strftime("%Y-%m")
        ni = nidx[nnorm(r[0])]
        cand = [catn + "|1|" + dpto, catn + "|0|" + dpto] if pi else [catn + "|0|" + dpto]
        hit = None
        for kstr in cand:
            gi = gidx.get(kstr)
            if gi is None:
                continue
            meses_by_g[gi][m] += 1
            if hit is None:
                if ni in name2ni[gi]:
                    hit = gi
                elif r[4] is not None and pos2ni[gi].get(r[4]) == ni:
                    hit = gi
        if hit is not None:
            # puesto: el que la persona tiene en ese grupo
            gi = hit
            for puesto, n2, _, _ in grupos[gi]["filas"]:
                if n2 == ni:
                    llam_by_g[gi][m].add(puesto)
                    break
            else:
                if r[4] is not None and r[4] in pos2ni[gi]:
                    llam_by_g[gi][m].add(r[4])

    tot_mes = defaultdict(int)
    for r in sel:
        tot_mes[(EPOCH + dt.timedelta(days=r[5])).strftime("%Y-%m")] += 1

    for gi, g in enumerate(grupos):
        g["meses"] = dict(sorted(meses_by_g[gi].items()))
        g["llam"] = {m: sorted(ps) for m, ps in sorted(llam_by_g[gi].items())}

    maxf = EPOCH + dt.timedelta(days=contra["maxfecha"])
    dcorte = EPOCH + dt.timedelta(days=contra["corte"])
    data = {
        "gen": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "fBolsa": bolsa.get("generated", ""),
        "corte": dcorte.isoformat(),
        "mesDef": maxf.strftime("%Y-%m"),
        "dpts": DPTS,
        "bucketLbl": BUCKET_LBL,
        "names": names,
        "grupos": grupos,
        "contratos": [[nidx[nnorm(r[0])], r[1], DPTS.index(contra["dptos"][r[3]]),
                       r[4], r[5], r[6], r[7], r[8], r[9], r[10],
                       (r[2] if r[2] >= 0 else None)] for r in sel],
        "ccats": ccats,
        "perfiles": contra["perfiles"],
        "tnom": {"A": "Acumulación de tareas", "C": "ATC/Guardias", "I": "Interinidad (vacante)",
                 "S": "Sustitución (también reserva de plaza)"},
        "totMes": dict(sorted(tot_mes.items())),
    }

    html = open(args.tpl, encoding="utf-8").read()
    js = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    js = js.replace("\\", "\\\\").replace("'", "\\'").replace("</", "<\\/")
    html = html.replace("{{DATA}}", js)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)

    act_total = sum(g["cnt"].get("A", 0) for g in grupos)
    print(f"OK: {len(grupos)} grupos de bolsa · {len(names)} nombres · {len(sel)} contratos en {'+'.join(DPTS)}")
    print(f"    activos: {act_total} · meses con datos: {min(tot_mes)}..{max(tot_mes)} · corte {data['corte']} · bolsa {data['fBolsa']}")
    llam_ult = sum(len(g["llam"].get(data["mesDef"], [])) for g in grupos)
    print(f"    personas llamadas en {data['mesDef']} (match nombre+puesto): {llam_ult}")
    import os
    print(f"    {args.out}: {os.path.getsize(args.out)/1024:.0f} KB")

if __name__ == "__main__":
    main()
