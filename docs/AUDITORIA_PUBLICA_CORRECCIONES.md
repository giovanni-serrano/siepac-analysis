# Correcciones de la auditoría pública

Fecha: 2026-10-02. Rama de trabajo: `fix/auditoria-publica`.
Referencia integrada: `post-refactor-2026` (`af9f8a5`).

Este es un parche de mantenimiento de presentación y privacidad. No cambia la
arquitectura, fórmulas, agregaciones, fuentes numéricas, metodología ni baseline.
No se realizaron commits, push, merge, releases ni cambios de configuración remota.

## Hallazgos, causas y correcciones

| Hallazgo | Causa | Corrección |
| --- | --- | --- |
| ENV6 se rotulaba como razón de sumas | `principal()` aplicaba la etiqueta genérica a cualquier serie con agregado | Caso específico de presentación «Suma regional», compartido por tarjeta, KPI, leyenda, resumen accesible, tabla y CSV |
| ECO14 omitía las imputaciones en tabla y CSV | La tabla/exportación solo consumían valores | Se consume `DATOS.imputados`: 13 marcas, incluidas El Salvador 2022 y las 12 observaciones de 2023–2024 |
| ECO-CG omitía banderas | `DATOS.ECO_CG.banderas` no llegaba a la presentación | Se muestran las tres marcas originales y la leyenda canónica `NOTA_CALIDAD_ECO_CG` |
| Dos XLSX exponían rutas locales | `x15ac:absPath` en `xl/workbook.xml` | Eliminación exclusiva de ese elemento; todos los demás miembros descomprimidos del ZIP permanecen idénticos |
| README SOC2 indicaba cuatro insumos | Conteo anterior a la estructura actual | Se indica tres, de acuerdo con los tres CSV existentes |
| Linguist apuntaba a tablas antiguas | Patrón histórico `tablas-apa/*.html` | Se cambia únicamente a `salidas/tesis/tablas/*.html` |

Las etiquetas no modifican los valores ENV6 ni su operación de suma. ECO14 sigue
sin agregado regional, y ECO-CG conserva su condición de serie complementaria
con proxies heterogéneos. SOC2 y SOC3 permanecen intactos.
Las fichas científicas y el objeto `FICHAS` incrustado no se modificaron. La leyenda
de calidad adicional se incorpora por separado, desde su constante existente.

## Banderas y descarga

ECO14 diferencia «Observado» e «Imputado mediante CAGR» usando exclusivamente los
booleanos del paquete. La leyenda enumera los país-años marcados, sin codificar
manualmente países o años. La tarjeta indica que 6/6 países están imputados en 2024.

ECO-CG conserva `*` para Honduras 2020, `†` para Costa Rica 2024 y `‡` para
El Salvador 2024. La leyenda original explica reconstrucción retrospectiva,
cobertura parcial de seis meses y cambio de bloque regulatorio. La ausencia de
marca se describe como «Sin bandera adicional; proxy nacional», sin equipararla
a una observación homogénea de costo. La tarjeta identifica dos países con
bandera en 2024. Los textos por marca se extraen de la leyenda canónica existente.

Las marcas se muestran como superíndices con texto accesible y descripción en
las celdas. Se conserva el diseño y CSS. Las vistas de región, países y datos
muestran la leyenda de calidad correspondiente.

**Cambio deliberado de contrato:** solo los CSV descargados dinámicamente de
ECO14 y ECO-CG pasan al formato largo:

```text
serie,unidad,pais_o_referencia,anio,valor,bandera,calidad
```

Cada descarga contiene 30 observaciones nacionales y 10 filas de referencias
(cinco promedios y cinco medianas). Los resúmenes explican las banderas de sus
insumos por país; no se clasifican como observaciones nacionales. Los números
se exportan sin redondeo adicional. Los demás indicadores conservan el CSV
ancho anterior; ENV6 cambia exclusivamente la denominación de su fila regional.
No se alteró ningún CSV científico del pipeline.

## Limpieza mínima de los XLSX

Antes de modificar cada libro se guardó una copia privada en el directorio
ignorado `.venv/auditoria-publica-20261002/originales/`. Se calcularon SHA-256 del
archivo y de cada miembro ZIP, inventario de hojas, dimensiones, número de
celdas y fórmulas. Se conservaron los inventarios antes y después.

Se leyó el contenedor con `zipfile`, se eliminó exactamente un elemento
`<x15ac:absPath .../>` de `xl/workbook.xml` y se verificó que el XML continuara
siendo válido. Se escribió el contenedor manteniendo sus nombres de miembros,
su comentario y los `ZipInfo` originales. No se abrió ni guardó ningún libro
con Excel, LibreOffice, pandas u openpyxl para esta limpieza.

La nueva compresión modifica el contenedor binario. La comparación de los
contenidos descomprimidos demuestra que **solo cambia `xl/workbook.xml`**, y que
su único cambio de contenido es la supresión del elemento. Todas las hojas,
relaciones, estilos, tipos de celda, fórmulas, valores guardados y cadenas
compartidas permanecen byte a byte iguales. El inventario de nombres y
atributos de hojas también es idéntico.

| Libro | Miembros ZIP | Hojas | Celdas serializadas | Fórmulas | Único miembro modificado |
| --- | ---: | ---: | ---: | ---: | --- |
| ENVs.xlsx | 15 | 4 | 959 | 0 | `xl/workbook.xml` |
| SOCs.xlsx | 27 | 11 | 2630 | 865 | `xl/workbook.xml` |

Cero fórmulas en ENV significa que el libro fuente almacena sus resultados como
valores; no se recalculó ni se sustituyó ninguno.

**ENVs.xlsx — SHA-256**

- Antes: `851d4c5edb95f0ed80382db43065581ca2c85c5b6bf563870196fb14751a8bc3`
- Después: `660d0797d39ae1bfbe239c28126efefe865e746c9222095178dc2ae3184d714b`

**SOCs.xlsx — SHA-256**

- Antes: `53a1bf4a95d015559459e299bd8376c1e23a7a0f34aefdc6e717aa2bed1b35d2`
- Después: `61f993df2cf2e7299288486e976ce587654a0a1d79f0058732836adceccaaecc`

Inventario de hojas y dimensiones conservadas:

| Libro | Hoja | Dimensión | Celdas | Fórmulas |
| --- | --- | --- | ---: | ---: |
| ENVs.xlsx | ENV1 | A1:G31 | 217 | 0 |
| ENVs.xlsx | ENV2 | A1:J31 | 310 | 0 |
| ENVs.xlsx | ENV3 | A1:K31 | 341 | 0 |
| ENVs.xlsx | ENV6 | A1:G13 | 91 | 0 |
| SOCs.xlsx | SOC 1 | A1:I7 | 63 | 0 |
| SOCs.xlsx | SOC 2 NIC  (2) | A1:L25 | 154 | 53 |
| SOCs.xlsx | SOC 2 TOTAL | A1:H16 | 112 | 70 |
| SOCs.xlsx | SOC 2 CR | A1:AC30 | 251 | 82 |
| SOCs.xlsx | SOC 2 HD | A1:Q19 | 158 | 59 |
| SOCs.xlsx | SOC 2 ES | A2:K21 | 135 | 75 |
| SOCs.xlsx | SOC 2 GUA | A1:Q24 | 164 | 90 |
| SOCs.xlsx | SOC 2 PAN | A2:K25 | 164 | 68 |
| SOCs.xlsx | SOC 3 | A2:Y54 | 740 | 220 |
| SOCs.xlsx | Capacidad instalada | A1:H83 | 529 | 148 |
| SOCs.xlsx | Hoja1 | A1:D40 | 160 | 0 |

La evidencia completa por miembro se conserva localmente en
`.venv/auditoria-publica-20261002/equivalencia_xlsx.json`. El pipeline reconstruido
con estas fuentes confirma además igualdad exacta de sus resultados científicos.
Las copias originales privadas no se incorporan al parche.

## Investigación del redondeo ECO-CG — sin cambio de cifras

La mediana sigue calculándose en `eco_cg_comun.serie_mediana_eco_cg()` mediante
`groupby("anio")["ECO_CG"].median()`: para seis países se promedian los dos
valores centrales. No hay una diferencia de método de agregación.

| Año | Valores centrales | Mediana decimal exacta | `repr` de la mediana Python | Paquete web, redondeado a 6 decimales | Tabla `.2f` | Web, dos decimales |
| --- | --- | --- | --- | --- | --- | --- |
| 2022 | 95.05 y 126.28 | 110.665 | 110.66499999999999 | 110.665 | 110.66 | 110.67 |
| 2024 | 101.56 y 124.89 | 113.225 | 113.225 | 113.225 | 113.22 | 113.23 |

Las representaciones binarias completas son:

- 2022: `110.664999999999992041921359486877918243408203125`.
- 2024: `113.224999999999994315658113919198513031005859375`.

`generar_tablas_apa._fmt()` ejecuta `format(v, formato)` con `.2f`. Python formatea
el float binario (en ambos casos ligeramente inferior al punto medio decimal).
`generar_visualizador._serie_eco_cg()` conserva su `round(float(valor), 6)`
histórico y lo serializa como 110.665/113.225. La función JS `num()` utiliza
`toLocaleString("es-NI", {minimumFractionDigits: 2, maximumFractionDigits: 2})`,
cuyo redondeo decimal predeterminado lleva estos casos a 110.67/113.23.
Por tanto, intervienen la representación binaria y dos políticas de formato;
no un cálculo científico diferente de la mediana. El documento metodológico
versionado coincide con la presentación de las tablas.

**Decisión aplicada:** solo se investiga y documenta. No se cambia `.2f`, `num()`,
la serialización de datos, las medianas, los documentos ni el baseline.

**Propuesta para una autorización posterior:** formatear las medianas ECO-CG
una sola vez en la capa de presentación con el mismo `format(v, ".2f")` usado
por las tablas, y suministrar esas cadenas de presentación a la web, manteniendo
por separado los valores numéricos actuales para gráficos, cálculos y CSV.
Esto reproduciría 110.66/113.22 en las salidas visibles sin alterar ninguna
mediana científica. No se implementa en este parche; no se recomienda intentar
corregirlo sumando/restando épsilon ni modificar valores para forzar coincidencia.
La evidencia de los cinco años está en `redondeo.json` dentro del directorio
local de comprobación.

## Pruebas añadidas y conservación de los contratos

Se añaden 13 casos en `tests/test_auditoria_publica.py`:

- Dos casos de valores, tarjeta y tabla ENV6.
- Dos casos de trazabilidad de banderas, leyenda, tarjeta y CSV ECO14/ECO-CG.
- Un caso que cambia banderas en memoria para demostrar que la UI sigue el
  paquete y no reconstruye marcas por país-año.
- Dos casos de resumen accesible, leyenda y exportación ENV6.
- Dos casos de ausencia de rutas privadas en los XLSX fuente.
- Dos casos de la descarga efectiva: Blob, contenido CSV, nombre y revocación.
- Dos casos de las trazas gráficas ENV6 y sus valores exactos.

Los tests ejecutan las funciones JavaScript reales con Node incluido en la
versión fijada de Playwright; no añaden dependencias ni requieren instalar un
navegador en CI. También verifican que la leyenda realmente incrustada en el
HTML coincide con la constante canónica.

La prueba de hash literal de la plantilla conserva la misma aserción estricta;
se registra el hash de la modificación de presentación autorizada:
`a3642239f69c89c0fa507d38b1ed811d301663f8ce6a554ddba1f6716d80adf1`.
No se eliminan pruebas ni se modifican expectativas científicas. El hash antiguo
certificaba identidad literal durante el refactor; mantenerlo frente a un cambio
expresamente solicitado en la plantilla sería incompatible con este parche.

## Validación final

Se utilizó `.venv/fase5-entorno-limpio/Scripts/python.exe`, el entorno ya
verificado. Python global carecía de pytest y el directorio principal de
procesados no contenía los JSON intermedios; no se instalaron paquetes ni se
rellenaron artificialmente esos intermedios. El producto entregado procede de
la ejecución completa aislada.

| Comprobación | Resultado |
| --- | --- |
| Tras ENV6 | 142 passed |
| Tras banderas | 147 passed |
| Tras limpieza XLSX | 149 passed |
| Tras correcciones documentales | 149 passed |
| Suite con los casos adicionales de descarga y gráfico | 153 passed |
| Suite sobre resultados reconstruidos | 153 passed |
| Copia de archivos públicos, sin fuentes privadas ni CSV regenerables | 145 passed, 8 skipped, exclusivamente las ocho comparaciones esperadas |
| Pipeline aislado desde los insumos | 18/18; código de salida 0 |
| CSV científicos: ocho archivos | 3205 valores numéricos exactos |
| Libros ECO/ENV/SOC: celdas, fórmulas y notas | 2025 valores numéricos exactos |
| Datos y fichas del visualizador, países y años | 920 valores numéricos exactos |
| Total | 6150 valores exactos, sin tolerancia adicional |
| Figuras PNG | 22/22 idénticas byte a byte |
| Inventario original durante el pipeline | 181 archivos intactos |
| Revisión visual local en Chrome | Tarjetas, tablas ECO14/ECO-CG y ENV6 comprobados; sin errores JS registrados |
| `git diff --check` | Sin errores |

Las comparaciones exactas se hicieron mediante igualdad de las estructuras
completas leídas con `baseline_utils.capturar`, además de las pruebas regulares.
Se contrastaron explícitamente `ENV6_BIOMASA`, `ENV6_SALDO`, `ECO14`, `ECO_CG`
y `imputados`: todos idénticos al baseline, incluidas las banderas originales.

El SHA-256 del baseline permanece:

```text
4fb610b68c9ffa0c6b5cdb8692063e89ef6fd07ee197b0ffa9da08d75ba5e8ce
```

Comandos principales (en PowerShell, `$pythonParche` identifica el ejecutable
anterior; los destinos deben ser nuevos en otra reproducción):

```powershell
& $pythonParche -X utf8 -B -m pytest -q -p no:cacheprovider --basetemp .venv/pytest-auditoria-final
& $pythonParche -X utf8 -B tests/ejecutar_pipeline_aislado.py --destino .venv/pipeline-auditoria-publica-20261002
& $pythonParche -X utf8 -B -m pytest tests -q -p no:cacheprovider --resultados-dir .venv/pipeline-auditoria-publica-20261002 --basetemp .venv/pytest-auditoria-aislado-02
git diff --check
```

El log y la verificación del pipeline están en
`.venv/pipeline-auditoria-publica-20261002/`. La comparación exacta adicional y
la evidencia de limpieza/redondeo están en `.venv/auditoria-publica-20261002/`.

## Archivos del parche

Creados:

- `docs/AUDITORIA_PUBLICA_CORRECCIONES.md`.
- `tests/test_auditoria_publica.py`.

Modificados:

- `src/plantillas/visualizador.html`.
- `src/generar_visualizador.py`.
- `graficos/visualizador_siepac.html`, regenerado por el pipeline aislado.
- `data/raw_equipo/ENVs.xlsx` y `data/raw_equipo/SOCs.xlsx`, solo metadato privado.
- `data/raw_equipo/soc2_agregacion_regional/README.md`.
- `.gitattributes`.
- `tests/test_arquitectura.py`, hash de presentación y comentario explicativo.

No se modifica el README general, dependencias, fórmulas, capas científicas,
fuentes privadas, baseline ni otros productos versionados.

## Diferencias restantes y alcance de la entrega

- La diferencia visible de redondeo ECO-CG permanece por instrucción expresa;
  está explicada y cuenta con una propuesta, no con una corrección de datos.
- Los dos XLSX cambian de hash por el metadato y la recompresión; su contenido
  científico está demostrado idéntico.
- El HTML cambia de presentación y los dos CSV dinámicos cambian de esquema;
  no cambian los objetos científicos incrustados.
- En la copia aislada, el resumen Markdown y los dos HTML APA generales solo
  cambian la fecha de generación de 2026-08-22 a 2026-10-02. No se trasladan al
  repositorio esos cambios ajenos al parche. La Tabla 7 sigue idéntica.
- Word/COM no pudo generar los DOCX opcionales en esta sesión; el pipeline
  conservó los HTML y terminó correctamente. Persisten los avisos conocidos
  de exportaciones vacías de Nicaragua interpretadas como cero por el ETL.
- No se hizo publicación remota. La simulación del clon público fue local,
  no una nueva ejecución de GitHub Actions.

El parche queda preparado para revisión/PR, con la diferencia de redondeo
explícitamente conservada. No se crea PR ni se realiza integración desde esta
intervención.
