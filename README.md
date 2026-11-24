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
- **Detalle de bolsa**: caja protagonista de **llamados del mes** (nombres, puestos y
  fechas de contrato, **ordenados por fecha: los últimos contratos arriba**), **estimación de espera** con los candidatos por delante al lado
  (en días cuando queda aproximadamente un mes o menos), el siguiente puesto no
  llamado, y el gráfico por meses plegado en segundo plano.
- **Filtro de contratos**: menú desplegable (cabecera) para ver en detalle solo los
  **cortos (5 días o menos)**, **no cortos (más de 5)**, **indeterminados** o
  **vacantes (interinidad)**. Afecta a la tabla de bolsas, a las barras mensuales,
  a los llamados del mes y a la media usada en la estimación. Las tarjetas de arriba
  muestran siempre el desglose completo del mes (cortos, más de 5 días, indeterminados
  y vacantes).
- **"¿Cuánto queda?" por situación**: al consultar tu puesto se desglosan los
  candidatos que cumplen las situaciones marcadas y tienen **número menor al tuyo**
  (los que se seleccionarán antes para una oferta). El "siguiente puesto no llamado"
  también respeta ese filtro. En **ENFERMERA/O** aparece además un **filtro de perfil**
  (Hemodinámica, Hemodiálisis, Intervencionismo, Área de pacientes críticos,
  Área de quirófano, o sin perfil) que reduce el recuento a las personas con ese
  perfil anotado en la bolsa; la ficha del candidato también muestra sus perfiles.
  Los demás grupos no lo muestran porque la bolsa no recoge perfiles para ellos.

  Las casillas por defecto son **DISPONIBLE, ACTIVO (No vacante) (DISPONIBLE
  ESPECIAL) y ACTIVO (DISPONIBLE ESPECIAL)**; el resto de situaciones queda
  minimizado en un desplegable "Otras situaciones de bolsa" y solo se muestran si lo
  despliegas. Situaciones con identidad propia, con el mismo texto completo que en
  la app de bolsa (las que agrupan más de una situación exacta lo indican debajo de
  la casilla):

  | Casilla | Situación en bolsa | Significado |
  |---|---|---|
  | **D** | DISPONIBLE | La masa llamable real: persona disponible esperando llamada. |
  | **E** | ACTIVO (DISPONIBLE ESPECIAL) | Trabaja pero pide además disponibilidad especial. |
  | **U** | ACTIVO (No vacante) (DISPONIBLE ESPECIAL) | Ya colocada (plaza no vacante) y además disponibilidad especial. |
  | **A** | ACTIVO | Activo a secas (muy poco frecuente). |
  | V | ACTIVO EN PLAZA VACANTE | Colocada en una plaza vacante; puede dejarla si llaman por otra. |
  | W | ACTIVO (No vacante) | Ya colocada en plaza no vacante. |
  | B | BLOQUEADO (también BLOQUEADO (DISPONIBLE ESPECIAL)) | |
  | R | RESERVADO (también RESERVADO (DISPONIBLE ESPECIAL)) | |
  | N | NO DISPONIBLE / DESACTIVADO: DESACTIVADO, DESACTIVADO (NO LOCALIZABLE), DESACTIVADO/A DE OFICIO, NO DISPONIBLE OTROS, NO DISPONIBLE POR PENALIZACIÓN, NO DISPONIBLE PROVISIONAL, NO DISPONIBLE RENUNCIA JUSTIFICADA, NO LOCALIZABLE | |
  | O | Otra situación no contemplada arriba | |
- **Por nombre**: buscador sobre las dos fuentes a la vez — situación actual en cada
  bolsa donde consta la persona, su **última llamada** y todos sus contratos con sus
  **fechas de inicio y fin** bien visibles y duración en días (departamento, tipo de
  nombramiento, breve, jornada y regla de 5 días de la app de Contrataciones).
- **Compartir consulta**: junto al número de puesto se muestra el **nombre de la
  persona consultada**, y un botón "Compartir consulta" genera una imagen (tarjeta
  con el logo y encabezado de Intersindical Salut Orihuela) con nombre, puesto,
  categoría y departamento, los filtros de situaciones aplicados y candidatos por
  delante, lista para
  enviar por WhatsApp (o copiar texto / descargar imagen).
- **Puestos pinchables**: en la ficha de una persona (y en los resultados del
  buscador), al pinchar sobre el **número de puesto** de una categoría y departamento
  se salta al Resumen con esa bolsa cargada y el puesto escrito en "Tu puesto en esta
  bolsa" (estimación lista).
- **Cabecera con la imagen del sindicato**: barra roja con la sesión y los filtros, y
  logo, título y recuadro "Datos actualizados a: ..." con los PNG del repositorio. Al
  compartir el enlace (p. ej. WhatsApp) la previsualización muestra el logo
  (og:image).

Mismo código de acceso que las otras apps (pídelo a tu delegado/a sindical).

La sesión se recuerda en el dispositivo: no hay que volver a teclear el código; "Cambiar de usuario" la borra.

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
