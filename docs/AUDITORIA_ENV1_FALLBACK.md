# Fase 3: auditoría del respaldo de ENV1

**Clasificación: B. Defecto real en una ruta no utilizada por los resultados
actuales.** El cálculo alternativo multiplicaba la intensidad por un millón.
Las 30 intensidades del insumo están precalculadas y ninguna activa esa ruta.
El diagnóstico A–D se presentó antes de modificar producción.

Rama de trabajo: `audit/env1-fallback`. Commit de partida:
`a46a9cd fix: endurecer validaciones de integridad del pipeline`.
Alcance: ENV1, seis países, 2020–2024, con los insumos locales existentes.
No se sustituye el PIB ambiental, no se reorganiza la arquitectura y no se
actualiza la referencia para acomodar diferencias.

## 1. Fórmula reconstruida y procedencia

Fuente: `data/raw_equipo/ENVs.xlsx`, hoja `ENV1`, filas 2–31.
Es un libro elaborado por el equipo, no una descarga del PIB económico.

| Columna | Cabecera del insumo | Uso |
| --- | --- | --- |
| A | País | Clave nacional |
| B | Año | Clave temporal |
| C | A: Emisiones GEI Centrales Eléctricas (Miles de t CO2eq) | Numerador |
| D | B: Población Total (Miles de personas) | Denominador per cápita |
| E | C: PIB Real (Millones USD Constantes) | Denominador de intensidad |
| F | ENV1: Emisiones per Cápita (t CO2eq / habitante) | Resultado precalculado per cápita |
| G | ENV1: Intensidad Emisiones (kg CO2eq / USD Constante) | Resultado precalculado por PIB |

Para una fila `r`, las dos salidas son:

```text
ENV1_PC  = (Cr × 10³ t) / (Dr × 10³ habitantes) = Cr / Dr t/habitante
ENV1_PIB = (Cr × 10⁶ kg) / (Er × 10⁶ USD)       = Cr / Er kg/USD
```

`procesar_dimensiones.leer_env()` lee F y G con `data_only=True`.
Solo G tiene respaldo. `FICHAS["ENV1"]`, en `src/viz_comun.py`, declara
las dos series y la fórmula de intensidad «Emisiones GEI (kg) ÷ PIB real
(USD constantes 2015)». `CAT_ENV` declara la misma unidad para el Excel.

La inspección con `data_only=False` encontró **cero fórmulas en la hoja
ENV1**: G2:G31 contiene 30 celdas numéricas, ninguna vacía. El libro actual
no permite recuperar una fórmula Excel original. Las equivalencias
reconstruidas serían `=C2/D2` y `=C2/E2`, respectivamente; no son fórmulas
encontradas en esas celdas. En particular, el prefijo «A:» de la cabecera
de emisiones no es la columna A de Excel: las emisiones están en C.

## 2. Unidad del numerador

C contiene miles de toneladas de CO₂eq de centrales eléctricas.
Una unidad almacenada equivale a `10³ t × 10³ kg/t = 10⁶ kg`.
Para la salida per cápita se requieren toneladas, por lo que su factor
es solamente 10³. No se cambia el perímetro del sector eléctrico.

## 3. Unidad del PIB ambiental

E contiene **millones de USD constantes**, no USD unitarios ni miles de USD.
Su cabecera lo declara y las 30 intensidades almacenadas concuerdan con
esa escala. Una unidad almacenada equivale a 10⁶ USD constantes.

El año base 2015 está declarado en los metadatos del proyecto. La cabecera
de este libro no especifica ese año; esta auditoría no certifica de forma
externa su deflactor ni su procedencia macroeconómica. Esa limitación es
independiente del factor millón, que sí se demuestra con el insumo.

`leer_env()` conserva E sin conversión en `BASE["pib_usd_const2015"]`.
Ese nombre y la nota de `Datos_Base` no expresan la escala en millones.
Se documenta la discrepancia de rotulación, sin renombrar columnas ni
alterar los productos congelados. No se usa `data/processed/pib.csv` ni
se reemplaza E por el PIB económico del Banco Mundial.

## 4. Conversiones y agregado

Para ENV1_PIB se necesitan dos conversiones de 10⁶: miles de toneladas a
kg, y millones de USD a USD. Se cancelan en el cociente. El respaldo
corregido usa directamente `f[2] / f[4]` y conserva la unidad kg CO₂eq/USD.

El agregado regional se calcula con `media_ponderada()` y el denominador
ambiental E como peso (`PESOS_AGREGADO["ENV1_PIB"]`). Multiplicar todos los
pesos por el mismo millón no altera esa media: equivale a la razón de
sumas de emisiones en kg y PIB en USD, con el redondeo publicado a seis
decimales. El promedio simple de países sigue siendo una salida distinta.

## 5. Origen exacto del factor problemático

Código de partida, en `leer_env()`:

```python
series["ENV1_PIB"] = tabla("ENV1", 6,
    recalcular=lambda f: (f[2] * 1_000_000) / f[4])
```

La expresión convierte solo el numerador. El resultado numérico corresponde
a kg por **millón** de USD, pero se trata como kg por USD. Para numeradores
y denominadores no nulos:

```text
fallback_anterior / intensidad_correcta
= [(C × 10⁶) / E] / [(C × 10⁶) / (E × 10⁶)]
= 10⁶
```

No es un redondeo de presentación, ni una diferencia de PIB entre fuentes.

## 6. Reproducción numérica anterior a la corrección

Se ejecutó `leer_env()` sobre el archivo intacto y sobre una copia en memoria
con G2:G31 vacía. Se instrumentaron las llamadas a la lambda de respaldo:
0 llamadas en la primera lectura y 30 en la segunda. No se guardó la copia
en memoria ni se editó el archivo fuente. Los cocientes de las 30 filas
concuerdan con 10⁶ a `rtol=1e-12`, sin tolerancia absoluta.

| Caso | Precalculado / correcto (kg/USD) | Respaldo anterior | Cociente |
| --- | ---: | ---: | ---: |
| Costa Rica 2020, fila 2 | 0.000349979137773878 | 349.97913777387805 | 1000000.0000000001 |
| El Salvador 2020, fila 7 | 0.02376947740625567 | 23769.477406255664 | 999999.9999999998 |
| Guatemala 2020, fila 12 | 0.0445566580054208 | 44556.658005420795 | 999999.9999999999 |
| Honduras 2020, fila 17 | 0.1021744123135889 | 102174.41231358892 | 1000000.0000000002 |
| Nicaragua 2024, fila 26 | 0.09516828287913968 | 95168.28287913968 | 999999.9999999999 |
| Panamá 2024, fila 31 | 0.02932369718981657 | 29323.697189816572 | 1000000.0 |
| Sintético: C=4, E=2 | 2 | 2000000 | 1000000 |

Costa Rica 2020: C2 = 21.56596375291421 miles de t y
E2 = 61620.71228042172 millones de USD constantes. Esto equivale a
21,565,963.75291421 kg y 61,620,712,280.42172 USD. Su razón es la intensidad
almacenada, no 349.979 kg/USD.

El caso sintético del último xfail tiene 4 millones de kg y 2 millones de
USD: debe devolver 2 kg/USD. Antes de corregir, la suite reprodujo
`132 passed, 1 xfailed`. Los registros completos de las 30 observaciones y
la instrumentación se conservan localmente en
`.venv/env1-auditoria-previa.json` y
`.venv/auditoria-env1-fase3/evidencia_antes.json`.

## 7. Condición de activación

Dentro de la función local `tabla()`:

```python
v = f[col_valor]
if v is None and recalcular:
    v = recalcular(f)
```

Para ENV1_PIB, `col_valor=6` significa columna G. Se usa el respaldo si
G está vacía o si una fórmula no tiene resultado disponible cuando
openpyxl lee con `data_only=True`. Un cero presente no activa el respaldo.
Una cadena, un error de Excel o un NaN tampoco cumplen `v is None`; no se
añaden aquí nuevas políticas de validación para esos casos.

Con el insumo actual no se activa en ningún país ni año: 0 de 30.

## 8. Impacto sobre los resultados actuales

| Producto | Trazabilidad comprobada | Dependencia actual del respaldo |
| --- | --- | --- |
| Libro ambiental | `leer_env()` → `main()` → `hoja_serie()` → `indicadores_ENV_SIEPAC.xlsx`, hojas ENV1_PC y ENV1_PIB | Ninguna; F/G completas |
| CSV consolidado y resumen | `generar_resumen_indicadores._armar_datos()` → `leer_series_extra()` → `_generar_md()` | Ninguna; leen el Excel procesado |
| Visualizador regional | `generar_visualizador.main()` → `leer_series_extra()` → JSON DATOS | Ninguna; lee el Excel procesado |
| Figuras ENV1 | `generar_figuras_tesis.main()` → `leer_series_extra()` → `crear_figura_bloque()` → `ENV1_{PC,PIB}_bloque.png` | Ninguna; usan países, promedio y agregado del Excel |
| Tablas APA | `generar_tablas_apa._armar_datos()` → `leer_series_extra()` → generadores de tablas | Ninguna; usan el mismo paquete de series |
| Baseline | Ocho CSV, celdas de tres libros y DATOS/FICHAS/ANIOS/PAISES del HTML | Coincidencia exacta con los resultados actuales antes del cambio |
| Materiales cuantitativos de tesis del repositorio | Tablas y figuras anteriores | Ninguna ruta adicional de cálculo de ENV1 |

`run_pipeline.py` ejecuta el procesamiento ambiental en el paso 14 y sus
consumidores en los pasos 15–18. Estos consumidores no llaman al respaldo.
La inspección de esta rama encuentra un único generador de visualizador
regional; las aplicaciones transitorias mencionadas en contexto anterior
no forman parte de sus scripts actuales.

La conclusión se refiere a los materiales generados por este repositorio.
No se certifica el origen de cifras copiadas a un manuscrito externo ni
versiones históricas que no se hayan proporcionado. No se interpreta la
ausencia de ese manuscrito como prueba de que carezca de errores.

## 9. Clasificación

**B. Defecto real pero ruta no utilizada.** Hay error dimensional en la
expresión anterior y evidencia directa de que ninguna de las 30
observaciones actuales la ejecuta. La concordancia de los precalculados
con C/E y la preservación del baseline separan el defecto latente de los
resultados científicos utilizados por el pipeline.

## 10. Evidencia y límites de la auditoría

- Encabezados, tipos de celda y valores del insumo inspeccionados.
- Cero fórmulas en ENV1 y cero valores faltantes en G2:G31.
- Ejecución instrumentada del lector real: 0 llamadas normales y 30 forzadas.
- Contraste dimensional de las 30 observaciones y caso sintético independiente.
- Seguimiento de productores y consumidores, más regresión contra la referencia.
- No se valida externamente el inventario de emisiones ni el año base del PIB.

SHA-256 del insumo `ENVs.xlsx`:
`851d4c5edb95f0ed80382db43065581ca2c85c5b6bf563870196fb14751a8bc3`.

SHA-256 del baseline:
`4fb610b68c9ffa0c6b5cdb8692063e89ef6fd07ee197b0ffa9da08d75ba5e8ce`.

La nota histórica de `CAT_ENV`, «Valor recuperado de la fórmula original
=(A×10⁶)/PIB», no demuestra que exista hoy una fórmula Excel. Solo resulta
dimensionalmente correcta si ese PIB significa USD unitarios. Aplicarla
directamente a E es incorrecto. Se conserva esa nota de salida para cumplir
la preservación exacta del baseline; su aclaración editorial y la escala
del nombre `pib_usd_const2015` quedan documentadas aquí, sin modificar datos.

## 11. Cambio mínimo aplicado

Se cambió únicamente la lambda de ENV1_PIB a `lambda f: f[2] / f[4]`.
Los comentarios explican la cancelación de conversiones y el encabezado
del módulo distingue valor almacenado de caché de fórmula. No se cambian
la condición de activación, los precalculados ni las salidas restantes.

Se retiró la marca xfail, conservando su aserción. Se añadieron dos casos
para comprobar la prioridad de valores presentes (0 y 7.5) y una prueba
que fuerza el respaldo en las 30 observaciones reales exclusivamente en
memoria. Esta última exige igualdad exacta de las demás tablas devueltas.
Para comparar un recálculo forzado contra decimales almacenados en Excel
usa `rtol=1e-12, atol=0`; eso no sustituye la igualdad exacta exigida a los
productos actuales regenerados contra el baseline.

## 12. Archivos modificados

- `src/procesar_dimensiones.py`: una expresión productiva y comentarios.
- `tests/test_contratos_cientificos.py`: retiro del xfail y dos casos de prioridad.
- `tests/test_regresion_resultados.py`: reproducción del respaldo con insumos reales.
- `tests/README.md`: estado actualizado de las pruebas.
- `docs/AUDITORIA_ENV1_FALLBACK.md`: este informe nuevo.

## 13. Pytest

Resultado final: **136 passed, 0 xfailed**, tanto con los productos originales
como con los reconstruidos en la copia aislada. No hubo fallos ni omisiones.
Desglose: 132 éxitos anteriores, el último xfail convertido en éxito y
tres casos nuevos. Las aserciones anteriores se conservaron.

```powershell
.\.venv\Scripts\python.exe -X utf8 -B -m pytest -q -p no:cacheprovider --basetemp .venv/pytest-fase3-final
.\.venv\Scripts\python.exe -X utf8 -B -m pytest tests -q -p no:cacheprovider --basetemp .venv/pytest-fase3-final-aislado --resultados-dir .venv/pipeline-fase3-env1
```

Las rutas temporales de estos comandos ya existen. Para repetirlos, elegir
nombres nuevos: pytest puede borrar el contenido previo de `--basetemp`.
El contraste adicional de los 30 respaldos corregidos contra los
precalculados arrojó una diferencia absoluta máxima de
`6.938893903907228e-17` y relativa máxima de `6.393439967404091e-16`.

## 14. Pipeline aislado

**18/18 scripts OK, código de salida 0**, desde una copia nueva de código
e insumos, sin reutilizar productos previos:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B tests/ejecutar_pipeline_aislado.py --destino .venv/pipeline-fase3-env1
```

Para repetir, usar un destino nuevo. El ejecutor rechaza sobrescribirlo.
`verificacion.json` confirmó paridad científica y **173 archivos originales
protegidos intactos durante la ejecución**, incluidas las versiones de código
y del informe presentes al iniciarla. El informe se completó posteriormente
con estos resultados. Los insumos y productos de la raíz no se regeneraron.

El log conserva los avisos previos de exportaciones eléctricas vacías de
Nicaragua interpretadas como cero. La conversión opcional de las dos tablas
a DOCX no se completó; el aviso sugiere falta de Word, sin demostrar esa causa.
Se generaron los HTML, los tres libros, el visualizador y las 22 figuras.
El fallo opcional de DOCX no abortó ninguna etapa del pipeline.

Comprobantes locales: `.venv/pipeline-fase3-env1/pipeline.log`,
`originales_antes.json`, `verificacion.json` y `comparacion_exacta.json`.
Estas evidencias temporales permanecen fuera de Git.

## 15. Comparación exacta y custodia del baseline

Antes de modificar producción coincidían exactamente los ocho CSV, los
valores/fórmulas/notas de los tres libros y los objetos del visualizador.
Después de reconstruirlos se verificó igualdad recursiva, incluidos los
tipos de valores, sin `isclose`, redondeo adicional ni tolerancias:

| Grupo | Escalares numéricos | Diferencias exactas |
| --- | ---: | ---: |
| Ocho CSV | 3205 | 0 |
| Celdas de los tres libros | 2025 | 0 |
| Objetos del visualizador | 920 | 0 |
| **Total** | **6150** | **0** |

También coincidieron textos, fórmulas, claves, longitudes, nulos y banderas.
El SHA-256 del baseline sigue siendo el documentado en el apartado 10.
No se actualizó la referencia ni los documentos históricos de fases 1–2.

Como comprobación adicional fuera del alcance numérico de la referencia:

- **22 de 22 PNG idénticos byte a byte**, incluidas las dos figuras ENV1.
- Los dos HTML generales de tablas APA coinciden íntegramente al sustituir
  únicamente `el YYYY-MM-DD` por un marcador en memoria: fecha original
  `2026-08-22`, fecha nueva `2026-10-02`. No se modificaron esos archivos.
- `tabla_07_soc2_regional_tesis.html` coincide sin normalizar la fecha.

El análisis del AST de `procesar_dimensiones.py` frente a HEAD confirmó
que, descontando el docstring, la única diferencia ejecutable es la
expresión de la lambda ENV1_PIB. El inventario anterior a la auditoría
confirmó que solo ese script cambió entre los archivos de producción ya
existentes; se preservaron los insumos y productos originales. Las pruebas
y documentación cambiadas son las enumeradas en el apartado 12.

Para repetir una comprobación exacta breve después de reconstruir en una
ruta nueva, ejecutar este código Python con esa raíz:

```python
import json
import sys
from pathlib import Path
sys.path.insert(0, "tests")
from baseline_utils import REFERENCIA, capturar

esperado = json.loads(REFERENCIA.read_text(encoding="utf-8"))
actual = capturar(Path(".venv/pipeline-fase3-env1"))
for grupo in ("csv", "libros", "web"):
    # Serializar distingue también 1 de 1.0, sin tolerancias numéricas.
    assert json.dumps(actual[grupo], sort_keys=True) == json.dumps(
        esperado[grupo], sort_keys=True), grupo
```

No se hicieron commits, push ni cambios de historial.
