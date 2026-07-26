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
| **`tablas_apa_SIEPAC.docx`** | **Las 49 tablas con su nota metodológica.** Para el anexo y para consultar fórmulas y fuentes. |
| **`tablas_apa_SIEPAC_sin_notas.docx`** | **Las mismas 49 tablas, solo tablas.** Para intercalar en el cuerpo del monográfico. |
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

Aun así, el Manual APA pide que una tabla se entienda sin recurrir al
texto. Las tablas que dependen de una advertencia —ECO14 y sus valores
imputados, SOC2 y la inconsistencia de Guatemala, ENV6 y su carácter
ilustrativo— deberían llevar su nota también en el cuerpo, o bien la
aclaración en el párrafo que las presenta. Las notas completas están en
la versión con notas.

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
  convierte en tablas de Word. Es exactamente lo que hace el script para
  producir el `.docx`.

## Cómo se generan los .docx

El script arma cada documento en HTML y luego le pide a Microsoft Word
que lo convierta. Por eso los `.docx` solo aparecen si hay Word instalado
en la máquina; si no lo hay, el script avisa y deja los HTML, que sirven
igual copiando y pegando. Para saltarse el paso:

```bash
python src/generar_tablas_apa.py --sin-docx
```

## Qué se versiona

En el repositorio solo viajan los dos documentos HTML, el índice y este
README. Los `.docx` y las tablas sueltas de `individuales/` están en
`.gitignore`: son salidas regenerables (los `.docx`, además, son
binarios que git no puede comparar entre versiones). Al clonar el
proyecto hay que ejecutar el script una vez para obtenerlos.

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

Si en el monográfico las tablas quedan intercaladas con otras, hay que
renumerarlas según su orden final de aparición.

## Cifras

Los valores no se recalculan aquí: se leen del mismo pipeline que
alimenta los visualizadores y `docs/resumen_indicadores_SIEPAC.md`, así
que las tres salidas no pueden divergir.

Las referencias APA de las fuentes están en la sección final del
documento y se editan en `FUENTES_APA` y `REFERENCIAS_APA`, dentro de
`src/generar_tablas_apa.py`. **Conviene revisarlas antes de entregar**:
el año de recuperación se tomó de la fecha de descarga de los archivos
en `data/raw/`, y las series de las dimensiones ambiental y social
(recopiladas por el equipo) no tienen todavía una referencia formal.
