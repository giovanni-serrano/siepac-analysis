# Línea base de resultados SIEPAC

Esta referencia caracteriza el comportamiento actual. No certifica que todo
el código sea correcto ni autoriza cambios metodológicos. Se conservaron
las cifras, fórmulas, unidades, imputaciones, interpretaciones y productos originales.

## Procedencia y alcance

- Fecha de captura (UTC): `2026-09-16T19:36:14.967584+00:00`.
- Commit de producción: `21f71282a11176ac74b9fe6c42b30c610b88da95`.
- Python: `3.13.5`; plataforma: `Windows-11-10.0.26200-SP0`.
- SHA-256 de `tests/fixtures/baseline/resultados.json`: `4fb610b68c9ffa0c6b5cdb8692063e89ef6fd07ee197b0ffa9da08d75ba5e8ce`.
- Captura: `python tests/capturar_baseline.py --salida tests/fixtures/baseline/resultados.json`.
- Documento: `tests/documentar_baseline.py`, leyendo exclusivamente esa captura y los comprobantes de ejecución.

Bibliotecas registradas: `pandas==3.0.5`, `numpy==2.5.1`, `openpyxl==3.1.5`, `plotly==6.9.0`, `kaleido==1.3.0`, `pytest==9.1.1`.

La captura contiene los valores nacionales completos, los dos resúmenes
regionales, banderas, fichas y todas las celdas de los tres libros, incluidas
sus fórmulas. Guarda hashes de insumos, código y productos para identificar
la procedencia; esos hashes no impiden una futura refactorización del código.

| Resultado capturado | Filas | Productor |
| --- | ---: | --- |
| `data/processed/matriz_consolidada_wide.csv` | 30 | `src/consolidar_matriz.py` |
| `data/processed/indicadores_ECO_valores.csv` | 30 | `src/generar_matriz_indicadores.py` |
| `data/processed/soc2_pais_anio.csv` | 30 | `src/etl_soc2.py` |
| `data/processed/soc2_regional.csv` | 5 | `src/etl_soc2.py` |
| `data/processed/soc2_sensibilidad.csv` | 5 | `src/etl_soc2.py` |
| `data/processed/poblacion_rural_urbana.csv` | 30 | `src/etl_poblacion_rural_urbana.py` |
| `data/processed/tarifa_electrica_media.csv` | 30 | `src/etl_tarifa_electrica_media.py` |
| `data/processed/indicadores_consolidados_tidy.csv` | 855 | `src/generar_resumen_indicadores.py` |

También se capturaron `data/processed/indicadores_{ECO,ENV,SOC}_SIEPAC.xlsx`
y los objetos DATOS, FICHAS, ANIOS y PAISES del HTML generado por
`src/generar_visualizador.py`. El libro ECO procede de
`generar_matriz_indicadores.py`; los libros ENV/SOC, de `procesar_dimensiones.py`.

## Resultados regionales actuales

Las cifras de esta tabla son las publicadas por el pipeline en el objeto
DATOS de `graficos/visualizador_siepac.html`; conservan su redondeo a seis
decimales. Los CSV y las celdas de los libros guardan en la referencia
la precisión disponible antes de ese redondeo.

Cada celda presenta **promedio simple / agregado**. El promedio responde
al país típico y el agregado al sistema. En ENV6, el segundo número es
la suma de magnitudes observadas, no una razón. «—» significa que no se
construye agregado. ECO-CG es complementaria y tampoco admite agregado.

| Serie | Unidad publicada | 2020 | 2021 | 2022 | 2023 | 2024 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ECO1 | kWh/habitante | 1217.324140 / 959.079786 | 1302.658963 / 1037.127043 | 1332.520146 / 1041.149714 | 1379.865581 / 1080.176115 | 1311.788509 / 1063.361268 |
| ECO2 | kWh/USD const. 2015 | 0.224950 / 0.194847 | 0.222018 / 0.192425 | 0.214863 / 0.184945 | 0.215256 / 0.185369 | 0.215519 / 0.178630 |
| ECO3 | % | 84.484542 / 82.449370 | 85.378930 / 83.119751 | 85.375677 / 84.472214 | 84.616456 / 84.925301 | 83.602802 / 82.631436 |
| ECO6 | kWh/USD const. 2015 | 0.409442 / 0.369619 | 0.416210 / 0.379485 | 0.459123 / 0.437158 | 0.486602 / 0.458821 | 0.543975 / 0.496770 |
| ECO11 | % | 25.046800 / 24.965381 | 24.176180 / 23.947696 | 25.381400 / 24.301026 | 35.416964 / 34.897209 | 34.212943 / 32.966016 |
| ECO13 | % | 74.953200 / 75.034619 | 75.823820 / 76.052304 | 74.618600 / 75.698974 | 64.583036 / 65.102791 | 65.787057 / 67.033984 |
| ECO14 | USD corrientes/MWh | 183.376547 / — | 176.484089 / — | 191.173094 / — | 192.787980 / — | 194.608081 / — |
| ECO15 | % | 4.210340 / 1.654375 | 4.323620 / 1.685664 | 3.626831 / 1.757498 | 3.169206 / 2.478809 | 3.100820 / 2.166714 |
| ENV1_PC | t CO₂eq/habitante | 0.152458 / 0.166086 | 0.161050 / 0.174519 | 0.143495 / 0.134331 | 0.232998 / 0.211507 | 0.250056 / 0.238027 |
| ENV1_PIB | kg CO₂eq/USD constantes 2015 | 0.043246 / 0.032570 | 0.038559 / 0.031233 | 0.036572 / 0.022967 | 0.052249 / 0.034969 | 0.053482 / 0.038537 |
| ENV2_SO2_PC | kg/habitante | 1.202776 / 1.446198 | 1.184002 / 1.445258 | 1.129502 / 1.162884 | 1.628635 / 1.669315 | 1.619493 / 1.799328 |
| ENV2_PAR_PC | kg/habitante | 0.043020 / 0.042665 | 0.039927 / 0.037793 | 0.045368 / 0.041677 | 0.064640 / 0.058023 | 0.061231 / 0.057910 |
| ENV2_SO2_PIB | g/USD constantes 2015 | 0.441016 / 0.283603 | 0.382494 / 0.258651 | 0.355945 / 0.198823 | 0.447619 / 0.275991 | 0.447452 / 0.291314 |
| ENV2_PAR_PIB | g/USD constantes 2015 | 0.017137 / 0.008367 | 0.014201 / 0.006764 | 0.014754 / 0.007126 | 0.018261 / 0.009593 | 0.017640 / 0.009376 |
| ENV3 | g/kWh | 1.722350 / 1.490715 | 1.590276 / 1.381786 | 1.406307 / 1.157869 | 1.793789 / 1.626593 | 1.823141 / 1.727963 |
| SOC1 | % | 5.796667 / 7.569954 | 5.613333 / 7.566899 | 5.395000 / 7.290058 | 5.103333 / 6.949312 | 4.915500 / 6.719954 |
| SOC2_PROM | % | 3.618296 / 2.139755 | 3.285105 / 2.004943 | 3.344997 / 2.045459 | 3.228771 / 2.029724 | 3.158373 / 2.112804 |
| SOC2_VULNERABLE | % | 20.490799 / 13.662668 | 19.169767 / 12.735780 | 20.606395 / 12.628768 | 20.726475 / 12.437857 | 21.854638 / 12.949303 |
| SOC3_RURAL | % | 64.063834 / 57.986382 | 65.800894 / 59.376649 | 65.140508 / 60.277880 | 57.086908 / 52.261701 | 59.146172 / 51.210467 |
| SOC3_URB | % | 74.162445 / 73.200313 | 74.769919 / 73.138924 | 73.523903 / 73.140391 | 63.612927 / 63.012036 | 64.606930 / 61.945393 |
| ENV6_BIOMASA | GWh | 515.481667 / 3092.890000 | 568.960000 / 3413.760000 | 529.550000 / 3177.300000 | 537.806667 / 3226.840000 | 493.335000 / 2960.010000 |
| ENV6_SALDO | GWh | -7.066667 / -42.400000 | -2.166667 / -13.000000 | 4.883333 / 29.300000 | 10.466667 / 62.800000 | 4.300000 / 25.800000 |
| ECO_CG | USD corrientes/MWh | 82.621667 / — | 85.933333 / — | 103.948333 / — | 106.823333 / — | 112.856667 / — |

## Casos sensibles

### ECO14: imputaciones y ausencia de agregado

Fuente: `indicadores_ECO_valores.csv` y banderas publicadas. El agregado
se conserva como `null`. La mediana usada en las figuras es un resumen
descriptivo de países y no sustituye a un agregado regional.

| País | 2020 | 2021 | 2022 | 2023 | 2024 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Costa Rica | 155.176570100 | 131.047563800 | 130.710393400 | 126.913142317* | 123.226204695* |
| El Salvador | 172.100000000 | 181.300000000 | 179.716239934* | 178.146314925* | 176.590104116* |
| Guatemala | 198.416995600 | 205.130585400 | 223.860894100 | 228.072279510* | 232.362891652* |
| Honduras | 177.579629500 | 183.403532200 | 235.373200100 | 250.456662786* | 266.506721698* |
| Nicaragua | 217.986087000 | 195.322851200 | 196.477153600 | 195.411668966* | 194.351962396* |
| Panamá | 179.000000000 | 162.700000000 | 180.900679900 | 177.727814394* | 174.610598626* |

\* `imputado_CAGR`: 13 de 30 observaciones; las 12 de 2023–2024 son imputadas.

### ECO15: exportadores netos

Fuente: `indicadores_ECO_valores.csv`. Se conservan todos los valores
nacionales y regionales en la referencia. Casos negativos de 2024:

| País | ECO15 (%) |
| --- | ---: |
| El Salvador | -0.502968682992 |
| Panamá | -4.170630179240 |

### SOC2: razón de sumas con clientes residenciales

Fuente: `etl_soc2.py` → `soc2_regional.csv`. La fuente canónica sigue
siendo `data/raw_equipo/soc2_agregacion_regional/base_integrada.csv`.
Estos resultados usan magnitudes de gasto e ingreso expandidas por clientes,
no una media de porcentajes ponderada solamente por clientes.

| Año | SOC2_PROM (%) | SOC2_VULNERABLE (%) | Brecha (pp) |
| --- | ---: | ---: | ---: |
| 2020 | 2.139755107334278 | 13.662667839041184 | 11.522912731706906 |
| 2021 | 2.004943223486199 | 12.735779954776739 | 10.730836731290539 |
| 2022 | 2.045459401634776 | 12.628768246556641 | 10.583308844921865 |
| 2023 | 2.029724011393092 | 12.437856705475999 | 10.408132694082907 |
| 2024 | 2.112803729840648 | 12.949303219454952 | 10.836499489614305 |

### SOC1, SOC3, ENV6 y denominadores

Los valores regionales de SOC1 y SOC3 figuran en la tabla anterior para
los cinco años. Las pruebas ejercitan el orquestador de dimensiones con
poblaciones sintéticas diferentes: SOC1 usa población total; SOC3 rural
y urbano usan sus respectivas poblaciones. Se conserva el proxy de mix
renovable nacional uniforme entre zonas y la heterogeneidad de SOC2.

ENV6 conserva dos series y sus signos. No se calcula un cociente ni se
interpreta la suma del saldo neto como flujo intrarregional bruto.

Los dos PIB se conservan por separado. **Discrepancia de rotulación vigente:**
`ENVs.xlsx` expresa el PIB en millones de USD constantes y el código conserva
esa magnitud en una columna llamada `pib_usd_const2015`, cuya nota declara
USD. La tabla siguiente conserva los números literales de las salidas;
no convierte ni sustituye valores del pipeline.

| País y año | PIB ECO (USD, valor almacenado) | PIB ENV (millones según fuente, valor almacenado) |
| --- | ---: | ---: |
| Costa Rica 2024 | 76264229553 | 76705.539804019 |
| El Salvador 2024 | 29062047321 | 29992.017467030 |
| Guatemala 2024 | 83989981407 | 90510.289588010 |
| Honduras 2024 | 27858556650 | 28268.520756430 |
| Nicaragua 2024 | 15841222425 | 15301.625165155 |
| Panamá 2024 | 77318963570 | 81219.618004584 |

## Auditoría de las cuatro pruebas preexistentes

| Prueba | Qué protege | Límite |
| --- | --- | --- |
| SOC2: resultados regionales autoritativos | Cinco años de dos indicadores y brecha frente a una referencia fija | No prueba rechazo de insumos ni otras dimensiones |
| Catálogo del visualizador | 15 IEDS, ECO-CG separada, dos magnitudes ENV6 y presencia de hallazgos | Estructura; no verifica cifras ni validez del hallazgo |
| HTML autocontenido | Textos, marcadores, elementos de accesibilidad y ausencia de controles | Inspecciona el archivo existente; no ejecuta navegador ni cálculos |
| Saneamiento de Plotly | Escape de dos caracteres de control | Higiene de serialización, no comportamiento científico |

Las cuatro se mantuvieron intactas y pasan. La prueba SOC2 ya era una
regresión científica útil; las otras tres protegen estructura/presentación.

## Debilidades detectadas, sin corregir

| ID | Hallazgo demostrado | Casos xfail estrictos |
| --- | --- | ---: |
| D01 | Consumo final, consumo industrial y población total aceptan duplicados o un año completo ausente | 6 |
| D02 | Consolidación continúa con duplicados, país ausente, año ausente o variable ausente; `aggfunc=first` descarta el duplicado conflictivo | 4 |
| D03 | Tarifa acepta un año ausente si los registros restantes no tienen nulos | 1 |
| D04 | El cálculo ECO no rechaza un denominador cero y puede producir infinito | 1 |
| D05 | La lectura ENV sobrescribe claves repetidas con la última fila | 1 |
| D06 | El respaldo de ENV1 sin valor precalculado usa PIB en millones como USD y multiplica por 10⁶ la intensidad del caso sintético | 1 |

D06 no cambia los resultados precalculados actuales. Se comprobó con un
libro sintético que reproduce la unidad del encabezado de la fuente. La
discrepancia de nombre/nota del PIB ambiental también se conserva como
limitación pendiente. Los xfail verifican defectos concretos; errores
inesperados de preparación no se convierten en fallos esperados.

Otras limitaciones observadas: fichas y fórmulas repartidas entre módulos;
lectura de resultados a través del formato de los Excel; conclusiones con
cifras literales; publicación Pages sin pruebas previas. No se modificó
ninguno de esos comportamientos. El contexto local menciona generadores
transitorios ya ausentes; para esta ejecución se siguió el orquestador real.

## Ejecución y conservación

Se ejecutó `tests/ejecutar_pipeline_aislado.py --destino .venv/baseline-pipeline`.
La copia comenzó sin productos procesados; usó los mismos scripts e insumos.
`src/run_pipeline.py` completó **18/18** etapas con código de salida **0**.
Los ocho CSV, las celdas de los tres libros y los datos/fichas web coinciden
con la captura bajo las tolerancias definidas. Se generaron 22 figuras y
los HTML consolidados de 75 tablas. No se compararon píxeles de las figuras.

Se verificó por SHA-256 que los **171 archivos originales** protegidos permanecieron intactos.
El pipeline avisó que las exportaciones eléctricas vacías de Nicaragua
2020–2024 se interpretan como cero. Ese comportamiento existente no se alteró.
La conversión opcional de los dos DOCX no se completó; el log indica que
Word podría no estar disponible. No se verificaron los DOCX en esta ejecución.

Resultado de pytest, incluyendo las cuatro pruebas originales:

```text
67 passed, 14 xfailed in 3.69s
```

Las comparaciones de productos se ejecutaron contra la copia reconstruida
con `--resultados-dir .venv/baseline-pipeline`. Los recálculos y contratos
importan los módulos originales intactos. No hubo fallos inesperados ni
pruebas omitidas en esa ejecución. Los 14 xfail corresponden a seis
debilidades, no a catorce errores científicos independientes.

Los comprobantes locales son `.venv/baseline-pipeline/pipeline.log`,
`originales_antes.json`, `verificacion.json` y el log de pytest indicado
al generar este documento. `.venv` está ignorado por Git.

## Uso en la siguiente fase

Consultar `tests/README.md`. Los valores esperados son fijos; las pruebas
no los regeneran. No reemplazar la referencia para resolver diferencias.
Una refactorización debe conservarla; una corrección científica requiere
revisión separada. Los xfail son estrictos: un arreglo futuro exige revisar
la prueba y retirar su marca. Para mostrar los defectos como fallos ordinarios
puede ejecutarse pytest con `--runxfail` sobre esos casos.

Tolerancias de regresión: `rtol=1e-12`, `atol=1e-9`; igualdad exacta para
enteros contra enteros, textos, fórmulas, banderas y claves. Los tests de
presentación admiten el redondeo ya existente a seis decimales. La captura
de libros excluye estilos y metadatos binarios; HTML se compara por sus
objetos de datos y fichas. Las fuentes oficiales siguen siendo necesarias
para reproducir todo desde cero; no se redistribuyen en las pruebas.
