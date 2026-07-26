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
| **`tablas_apa_SIEPAC.docx`** | **Documento de Word con las 49 tablas.** Es el que se usa para redactar. |
| `tablas_apa_SIEPAC.html` | El mismo documento en HTML (del que se genera el .docx). Útil para revisarlo en el navegador. |
| `individuales/Tabla_NN_codigo.html` | Cada tabla suelta, cuando solo se necesita una. |
| `indice_tablas.csv` | Número, sección, código y título de cada tabla. Sirve para armar el «Índice de tablas» del monográfico. |

## Cómo pasar una tabla a la tesis

**Ruta normal.** Abrir `tablas_apa_SIEPAC.docx`, seleccionar la tabla que
se necesita —desde la línea **Tabla *n*** hasta el final de la *Nota*—,
copiar con `Ctrl+C` y pegar en el documento de la tesis con `Ctrl+V`.
Como origen y destino son documentos de Word, la tabla llega íntegra:
bordes, cursivas y tipografía.

Si el documento de la tesis usa otra tipografía o interlineado y se
quiere que la tabla lo adopte, pegar con **Pegar > Combinar formato**
(`Ctrl+Alt+V`).

**Otras rutas.**

- El `.docx` también sirve tal cual como **anexo completo** de la tesis:
  ya trae portada, índice de tablas y referencias de las fuentes.
- Desde `individuales/*.html`: abrir en el navegador, `Ctrl+C`, `Ctrl+V`
  en Word. Word conserva la estructura de la tabla al pegar HTML.
- Word abre los `.html` de forma nativa (**Archivo > Abrir**) y los
  convierte en tablas de Word. Es exactamente lo que hace el script para
  producir el `.docx`.

## Cómo se genera el .docx

El script arma las tablas en HTML y luego le pide a Microsoft Word que lo
convierta. Por eso el `.docx` solo aparece si hay Word instalado en la
máquina; si no lo hay, el script avisa y deja el HTML, que sirve igual
copiando y pegando. Para saltarse el paso:

```bash
python src/generar_tablas_apa.py --sin-docx
```

## Qué se versiona

En el repositorio solo viajan el documento HTML, el índice y este README.
El `.docx` y las tablas sueltas de `individuales/` están en `.gitignore`:
son salidas regenerables (el `.docx`, además, es un binario que git no
puede comparar entre versiones). Al clonar el proyecto hay que ejecutar
el script una vez para obtenerlos.

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
