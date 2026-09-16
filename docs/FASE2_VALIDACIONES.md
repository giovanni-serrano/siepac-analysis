# Fase 2: validaciones defensivas

Rama: `refactor/validaciones`. Base: `8a67355`.
La referencia científica sigue siendo `tests/fixtures/baseline/resultados.json`.
No se cambian fórmulas, unidades, agregaciones, imputaciones, fichas ni valores
precalculados. No se reorganizan módulos. No se hace commit ni push.

## Mapa de los 14 xfail originales

Todos los casos pertenecen a `tests/test_contratos_cientificos.py`.
Los parámetros identifican los casos individuales de las pruebas compartidas.
A significa validación defensiva; B, asunto científico fuera de alcance.

| ID | Prueba y parámetros | Antes | Comportamiento deseado / final | Producción | Clase |
| --- | --- | --- | --- | --- | --- |
| D01.1 | `test_etl_debe_rechazar_cobertura_invalida[duplicado-etl_consumo_final_total]` | Aceptaba con aviso | Rechaza y muestra clave; prueba normal pasa | `etl_consumo_final_total.py` | A |
| D01.2 | `test_etl_debe_rechazar_cobertura_invalida[anio_ausente-etl_consumo_final_total]` | Aceptaba | Exige 2020–2024; prueba normal pasa | mismo | A |
| D01.3 | `test_etl_debe_rechazar_cobertura_invalida[duplicado-etl_consumo_industrial]` | Aceptaba con aviso | Rechaza y muestra clave; prueba normal pasa | `etl_consumo_industrial.py` | A |
| D01.4 | `test_etl_debe_rechazar_cobertura_invalida[anio_ausente-etl_consumo_industrial]` | Aceptaba | Exige 2020–2024; prueba normal pasa | mismo | A |
| D01.5 | `test_etl_debe_rechazar_cobertura_invalida[duplicado-etl_poblacion_total]` | Aceptaba con aviso | Rechaza y muestra clave; prueba normal pasa | `etl_poblacion_total.py` | A |
| D01.6 | `test_etl_debe_rechazar_cobertura_invalida[anio_ausente-etl_poblacion_total]` | Aceptaba | Exige 2020–2024; prueba normal pasa | mismo | A |
| D02.1 | `test_consolidacion_debe_rechazar_panel_incompleto[duplicado]` | Elegía primer valor | Rechaza antes del pivot; prueba normal pasa | `consolidar_matriz.py` | A |
| D02.2 | `test_consolidacion_debe_rechazar_panel_incompleto[pais_ausente]` | Avisaba y continuaba | Exige seis países; prueba normal pasa | mismo | A |
| D02.3 | `test_consolidacion_debe_rechazar_panel_incompleto[anio_ausente]` | Aceptaba | Exige cinco años; prueba normal pasa | mismo | A |
| D02.4 | `test_consolidacion_debe_rechazar_panel_incompleto[variable_ausente]` | Aceptaba | Exige todos los insumos; prueba normal pasa | mismo | A |
| D03 | `test_tarifa_debe_rechazar_anio_ausente` | Avisaba y continuaba | Exige panel final completo después de CAGR; prueba normal pasa | `etl_tarifa_electrica_media.py` | A |
| D04 | `test_eco_debe_rechazar_denominador_cero` | Producía infinito | Rechaza antes del cálculo y guardado; prueba normal pasa | `generar_matriz_indicadores.py` | A |
| D05 | `test_lectura_env_debe_rechazar_duplicados` | Sobrescribía en diccionario | Rechaza claves originales antes de construir diccionarios; prueba normal pasa | `procesar_dimensiones.py` | A |
| D06 | `test_env1_sin_cache_debe_conservar_escala` | Respaldo con discrepancia de escala | Auditoría metodológica pendiente; permanece `xfail(strict=True)` | `procesar_dimensiones.py` | **B, FUERA DE ALCANCE** |

## Cambios localizados

Ocho archivos de producción modificados:

- `src/etl_comun.py`: controles compartidos de columnas, claves únicas, cobertura
  completa y valores finitos; errores `VALIDACIÓN FALLIDA` con contexto y registros.
- `src/etl_consumo_final_total.py`, `src/etl_consumo_industrial.py` y
  `src/etl_poblacion_total.py`: panel explícito de seis países × cinco años,
  unicidad y valores finitos antes de guardar.
- `src/consolidar_matriz.py`: insumos obligatorios, controles antes de transformar
  y guardar, y `pivot` sin selección silenciosa del primer registro. Se mantiene
  la normalización preexistente `Panama` → `Panamá` y se revisan sus colisiones.
- `src/etl_tarifa_electrica_media.py`: unicidad de la historia antes del CAGR,
  base del CAGR positiva, cobertura final obligatoria y banderas admitidas
  `real` / `imputado_CAGR`. No exige un panel histórico completo antes de imputar.
- `src/generar_matriz_indicadores.py`: insumos finitos y denominadores positivos;
  incluye energía disponible de ECO15. Conserva negativos del numerador y del
  indicador. Calcula y valida antes de escribir Excel o CSV; rechaza resultados
  no finitos sin sustituirlos por cero ni imputarlos.
- `src/procesar_dimensiones.py`: controla claves de las hojas originales ENV1,
  ENV2 y ENV3 antes de `int()` y de los diccionarios. El respaldo ENV1 es idéntico.

Los años de ENV3 son texto en la fuente actual. Se aceptan para la comparación
de claves, sin cambiar las celdas ni los valores; `2020` y `"2020"` se consideran
la misma clave. Se rechazan años no enteros y huecos país-año aun cuando los
conjuntos de países y años estén presentes por separado.

Las excepciones conservan el mecanismo de interrupción del pipeline (`SystemExit`).
No se modifican las funciones de agregación ni los catálogos científicos.

## Pruebas

- Modificado `tests/test_contratos_cientificos.py`: se retiran exclusivamente
  las marcas xfail de D01–D05; D06 queda explícitamente fuera de alcance.
- Creado `tests/test_validaciones_integridad.py`: 52 casos parametrizados de
  huecos, años inválidos/equivalentes, claves ENV1/2/3, denominadores cero,
  negativos y no finitos, disponibilidad ECO15, banderas de tarifa, historia
  insuficiente y preservación de salidas ante entradas inválidas.
- Las cuatro pruebas originales y `tests/test_regresion_resultados.py` permanecen
  intactas. Se mantiene íntegra la referencia y el documento de fase 1.
- Actualizado `tests/README.md` con el estado de la fase 2.

Estado inicial: `67 passed, 14 xfailed`.
Resultado final: **132 passed, 1 xfailed**, sin fallos inesperados ni omisiones.
Desglose: 67 éxitos anteriores + 13 validaciones corregidas + 52 casos nuevos.

Comandos de verificación (cada temporal indicado debe ser nuevo):

```powershell
.\.venv\Scripts\python.exe -X utf8 -B -m pytest -q -p no:cacheprovider --basetemp .venv/pytest-fase2-final
.\.venv\Scripts\python.exe -X utf8 -B tests/ejecutar_pipeline_aislado.py --destino .venv/pipeline-fase2-validaciones
.\.venv\Scripts\python.exe -X utf8 -B -m pytest tests -q -p no:cacheprovider --basetemp .venv/pytest-fase2-final-aislado --resultados-dir .venv/pipeline-fase2-validaciones
```

## Pipeline y comparación numérica

El pipeline reconstruyó las salidas desde los insumos en la copia aislada:
**18/18 etapas, código 0**. La verificación existente confirmó paridad de los
ocho CSV, celdas de los tres libros y datos/fichas del visualizador.

Además se compararon recursivamente esos mismos resultados por igualdad exacta,
sin aplicar tolerancias: **6.150 escalares numéricos, cero diferencias**.
También coinciden los demás valores, textos, fórmulas, banderas y claves de los
grupos comparados. No se encontraron diferencias pequeñas que quedaran ocultas
por las tolerancias habituales de regresión.

SHA-256 de la referencia, intacto respecto a la fase 1:
`4fb610b68c9ffa0c6b5cdb8692063e89ef6fd07ee197b0ffa9da08d75ba5e8ce`.

La ejecución aislada preservó sus 171 archivos originales protegidos, incluidas
las versiones editadas de los scripts, según su inventario anterior/posterior.
Frente al commit `8a67355`, los cambios de producción se limitan a los ocho
scripts enumerados; los insumos y productos originales permanecen intactos.
Las lambdas científicas de ECO y dimensiones se contrastaron por AST y son
idénticas. El baseline y sus pruebas se contrastaron con Git considerando la
normalización CRLF/LF del checkout, sin reescribirlos.

Comprobantes locales en `.venv/pipeline-fase2-validaciones/`:
`pipeline.log`, `originales_antes.json`, `verificacion.json` y
`comparacion_exacta.json`. `.venv` continúa ignorado por Git.

## Pendientes y siguiente fase

D06 requiere una auditoría metodológica independiente. No activar su ruta de
respaldo asumiendo que esta fase corrigió la escala; su prueba sigue mostrando
el defecto. Las salidas precalculadas actuales conservan sus resultados.

La paridad aquí demostrada corresponde a los productos numéricos seleccionados
por la fase 1; no es una comparación visual píxel a píxel ni una certificación
de todas las rutas de error de todos los ETL. La conversión opcional de los
dos DOCX no se completó en esta ejecución; el log indica posible falta de Word.
Los HTML y las 22 figuras sí se generaron. Se conservan los avisos existentes
que interpretan exportaciones eléctricas vacías de Nicaragua como cero.

Como siguiente fase, revisar estos cambios defensivos antes de iniciar una
extracción gradual de responsabilidades. Mantener las pruebas y la referencia
fija en cada paso. Cualquier corrección científica debe tratarse por separado.
