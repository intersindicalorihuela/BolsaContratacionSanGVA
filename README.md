# Panel Bolsa · Sanidad GVA · Intersindical Salut Orihuela

Aplicación estática de una sola página que **combina las dos apps** de Intersindical Salut:

- [BolsaSanGVA](https://github.com/intersindicalorihuela/BolsaSanGVA) — situación en la bolsa (actualización quincenal).
- [Contrataciones](https://github.com/intersindicalorihuela/Contrataciones) — contratos del último mes.

El cruce se precomputa en el build: un script lee los `index.html` publicados de las dos
apps, normaliza y cruza ambas fuentes, y **solo incrusta en `index.html` los resultados**.
En vez de cargar los dos datasets enteros (~11 MB) el navegador recibe un único HTML de
~3.8 MB (~1 MB con el gzip de GitHub Pages) con todo lo ya calculado.

## Qué muestra

- **Resumen**: tabla de todas las bolsas (categoría · departamento, ordinarias y Pi) con
  candidatos, activos, contratos del mes, llamadas del mes y último puesto llamado.
- **Detalle de bolsa**: evolución mensual de llamadas, **estimación de espera**
  (activos por delante ÷ llamadas medias de los últimos 6 meses), el siguiente activo
  no llamado y el listado de puestos llamados con nombre y situación.
- **Filtro de contratos**: menú desplegable (cabecera) para ver en detalle solo los
  **cortos (5 días o menos)**, **no cortos (más de 5)**, **indeterminados** o
  **vacantes (interinidad)**. Afecta a la tabla de bolsas, a las barras mensuales,
  a los llamados del mes y a la media usada en la estimación. Las tarjetas de arriba
  muestran siempre el desglose completo del mes (cortos, más de 5 días, indeterminados
  y vacantes).
- **"¿Cuánto queda?" por situación**: al consultar tu puesto se desglosan los
  candidatos que tienes **por delante según su situación en bolsa** (ACTIVO, ACTIVO EN
  PLAZA VACANTE, BLOQUEADO, RESERVADO, NO DISPONIBLE...), y con casillas eliges qué
  situaciones cuentan para la estimación (por defecto solo ACTIVO). El "siguiente
  puesto no llamado" también respeta ese filtro.
- **Por nombre**: buscador sobre las dos fuentes a la vez — situación actual en cada
  bolsa donde consta la persona, su **última llamada** y todos sus contratos (fechas,
  departamento, tipo de nombramiento, breve, jornada y duración corto/indeterminado
  con la misma regla de 5 días de la app de Contrataciones).

Mismo código de acceso que las otras apps (pídelo a tu delegado/a sindical).

## Estructura

```
panel-src/
  build-panel.py      build: lee los dos index.html (local o URL), cruza y genera el panel
  template.html       diseño del panel ({{DATA}} es el hueco de los datos precomputados)
  test-panel.js       pruebas del panel generado
index.html            LA APP (generado, no editar a mano)
.github/workflows/
  actualizar-panel.yml  reconstruye el panel el 1 y el 16 de cada mes (o a mano)
manifest.json, sw.js, iconos   PWA, igual que las otras dos apps
```

## Actualización

1. **Automática**: cada 1 y 16 de mes el workflow de Actions descarga los `index.html`
   publicados de BolsaSanGVA y Contrataciones, regenera `index.html`, pasa las pruebas
   y lo commitea. También se puede lanzar a mano ("Run workflow").
2. **Manual**:
   ```
   python3 panel-src/build-panel.py --bolsa <index-bolsa> --contrataciones <index-contr> --tpl panel-src/template.html --out index.html
   node panel-src/test-panel.js
   ```

## Publicar en GitHub Pages

1. Settings → Pages → Deploy from a branch → `main` / root.
2. Quedará en `https://intersindicalorihuela.github.io/BolsaContratacionSanGVA/`.

## Cómo cruza los datos (importante)

- El cruce es **por nombre normalizado** dentro de la misma bolsa (categoría +
  departamento; los contratos de promoción interna cuentan solo en su bolsa Pi, y si
  no existe, en la ordinaria): se quitan tildes, `Mª`/`M.` se tratan como `MARIA` y
  se colapsan espacios.
- El campo `pos` de contrataciones **no** es el puesto en bolsa de quien la recibe
  (coincide con nombre y puesto solo en ~7% de los casos); se usa como pista
  secundaria, no como clave.
- Dos personas homónimas en la misma bolsa podrían confundirse: mismo límite que
  tienen las apps actuales.
- Los contratos detallados son los de los departamentos de las bolsas
  (ELCHE/ORIHUELA/TORREVIEJA); no se incluyen los del resto de la GVA.
- Las categorías de bolsa sin datos de contrataciones (Fisioterapeuta, Higienista
  Dental, Anatomía Patológica, Óptico-Optometrista, Gestión y Técnico de Función
  Administrativa) aparecen con sus cifras de bolsa pero sin contratos.
- La estimación de espera presume que se llama por orden a todos los activos; no
  descuenta no localizables ni reservas.

Herramienta sindical de uso orientativo; resultado NO oficial, extraído de SANGVA.
