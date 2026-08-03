# Tablas en formato APA 7 — fase cuantitativa

Tablas de las variables base y de los indicadores calculados, con el
formato de la 7.ª edición del Manual APA, listas para el monográfico.

Se generan con:

```bash
python src/generar_tablas_apa.py
```

## Qué hay en esta carpeta

| Archivo | Para qué sirve |
| --- | --- |
| **`tablas_apa_SIEPAC.docx`** | **Las 73 tablas con su nota metodológica.** Para el anexo y para consultar fórmulas y fuentes. |
| **`tablas_apa_SIEPAC_sin_notas.docx`** | **Las mismas 73 tablas, solo tablas.** Para intercalar en el cuerpo del monográfico. |
| `tablas_apa_SIEPAC*.html` | Los mismos dos documentos en HTML (de ahí se generan los .docx). Útiles para revisarlos en el navegador. |
| `individuales/Tabla_NN_codigo.html` | Cada tabla suelta, con nota, cuando solo se necesita una. |
| `indice_tablas.csv` | Número, sección, código y título de cada tabla. Sirve para armar el «Índice de tablas» del monográfico. |

Los dos documentos tienen **la misma numeración y las mismas cifras**
(se generan de los mismos datos en la misma corrida), así que la Tabla 29
es la misma en ambos y se pueden usar en paralelo.

### Cuál usar

La versión **sin notas** lleva la unidad de medida en el título, entre
paréntesis, para que ninguna tabla quede sin declarar en qué se expresan
sus cifras.

La versión con notas incorpora fórmula, criterio de agregación y fuente. La
versión sin notas mantiene únicamente el título, la unidad y las cifras para
su integración en el cuerpo del documento.

## Cómo pasar una tabla a la tesis

**Ruta normal.** Abrir el `.docx` que corresponda, seleccionar la tabla
que se necesita —desde la línea **Tabla *n*** hasta el final de la tabla
(o de la *Nota*, en la versión con notas)—, copiar con `Ctrl+C` y pegar
en el documento de la tesis con `Ctrl+V`. Como origen y destino son
documentos de Word, la tabla llega íntegra: bordes, cursivas y
tipografía.

Si el documento de la tesis usa otra tipografía o interlineado y se
quiere que la tabla lo adopte, pegar con **Pegar > Combinar formato**
(`Ctrl+Alt+V`).

**Otras rutas.**

- `tablas_apa_SIEPAC.docx` también sirve tal cual como **anexo completo**
  de la tesis: ya trae portada, índice de tablas y referencias de las
  fuentes.
- Desde `individuales/*.html`: abrir en el navegador, `Ctrl+C`, `Ctrl+V`
  en Word. Word conserva la estructura de la tabla al pegar HTML.
- Word abre los `.html` de forma nativa (**Archivo > Abrir**) y los
  convierte en tablas de Word; el script automatiza este proceso.

## Cómo se generan los .docx

El script genera cada documento en HTML y utiliza Microsoft Word para la
conversión. Los `.docx` requieren una instalación de Word; cuando no está
disponible, se conservan los HTML como formato de intercambio. Para omitir
la conversión:

```bash
python src/generar_tablas_apa.py --sin-docx
```

## Qué se versiona

En el repositorio solo viajan los dos documentos HTML, el índice y este
README. Los `.docx` y las tablas sueltas de `individuales/` están en
`.gitignore`: son salidas regenerables (los `.docx`, además, son
binarios que git no puede comparar entre versiones). Al clonar el
proyecto debe ejecutar el script una vez para obtenerlos.

## Formato aplicado

- Número de tabla en negrita, sobre el título en cursiva.
- Encabezados de columna centrados.
- Sin líneas verticales; líneas horizontales solo arriba y abajo de los
  encabezados, antes de las filas de resumen y al cierre de la tabla.
- Nota al pie que declara unidad, fórmula, criterio de agregación y
  fuente.
- Times New Roman, cuerpo de tabla a 10.5 pt.

## Numeración

La numeración es correlativa dentro del documento: primero las tablas de
datos base y luego las de indicadores. Para invertir ese orden:

```bash
python src/generar_tablas_apa.py --orden indicadores
```

Si las tablas se intercalan con otras, deben renumerarse según su orden
final de aparición.

## Cifras

Los valores se leen del mismo pipeline que alimenta los visualizadores y
`docs/resumen_indicadores_SIEPAC.md`, lo que mantiene consistencia entre
las tres salidas.

Las referencias APA se generan desde `FUENTES_APA` y `REFERENCIAS_APA`, en
`src/generar_tablas_apa.py`. Las notas identifican las matrices ENVs.xlsx y
SOCs.xlsx como insumos del estudio y citan por separado las fuentes externas
empleadas por el pipeline.
