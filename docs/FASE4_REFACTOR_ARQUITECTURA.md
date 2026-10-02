# Fase 4: refactor arquitectónico controlado

Fecha: 2026-10-02. Rama: `refactor/arquitectura`.
Referencia inmutable: `tests/fixtures/baseline/resultados.json`.
La fase separa responsabilidades conservando el comportamiento científico y
los comandos existentes. No introduce paquetes nuevos, clases, dependencias,
configuración adicional ni cambios en el orquestador de 18 etapas.
No se hizo commit, push, merge ni modificación de `main`.

## 1. Diagnóstico presentado antes de editar

Se leyeron completos `AGENTS.md`, `README.md`, `BASELINE_RESULTADOS.md`,
`FASE2_VALIDACIONES.md`, `AUDITORIA_ENV1_FALLBACK.md` y `tests/README.md`.
Se inspeccionaron los 27 módulos de `src/`, sus imports locales, los lectores
de archivos y los contratos de las pruebas. La rama era la solicitada y el
árbol de trabajo estaba limpio. La ejecución inicial dio **136 passed**.

Problemas principales:

- `viz_comun.py` mezclaba paleta, metadatos, lectura de productos, agregación
  científica y empaquetado; `procesar_dimensiones.py` dependía de él para
  calcular medias ponderadas.
- `generar_matriz_indicadores.py` mezclaba validaciones, cálculos pandas,
  metadatos, fórmulas Excel y formato del libro.
- `procesar_dimensiones.py` mezclaba lectura de fuentes, cruces de población,
  elección de ponderadores y escritura de libros.
- Los consumidores leían los Excel generados por nombres de hojas,
  `skiprows=2`, posiciones y la etiqueta `Agregado regional`. Cambiar la
  disposición visual podía romper los datos de otro producto.
- APA y Markdown repetían el empaquetado ECO y la adaptación de subseries.
  APA alojaba además estadísticos científicos puros.
- La aplicación tenía una plantilla HTML/CSS/JS extensa dentro del script.

No se encontraron ciclos locales. La dependencia científica → visualización
era innecesaria. `generar_explorador.py`, `generar_panel.py` y
`generar_manifiesto_tesis.py`, mencionados en contexto anterior, no existen en
esta rama; no se recrearon ni se contabilizan como archivos eliminados.

## 2. Mapa previo de fuentes, cálculos y consumidores

```text
data/raw/<variable>
  → diez ETL oficiales → CSV normalizados
data/raw_equipo/soc2_agregacion_regional/base_integrada.csv
  → etl_soc2 → CSV nacional, regional, sensibilidad y auditoría
CSV normalizados → consolidar_matriz → matrices tidy/wide
  → generar_matriz_indicadores [cálculo + metadatos + Excel y CSV ECO]
ENVs.xlsx + SOCs.xlsx + CSV población/SOC2
  → procesar_dimensiones [lectura + ponderación + Excel ENV/SOC]
                 ↘ importa media_ponderada desde viz_comun
Excel ECO/ENV/SOC + CSV ECO
  → viz_comun [lectura + agregados + FICHAS + JSON + paleta]
      → resumen Markdown/CSV
      → figuras
      → visualizador
      → tablas APA [además relee Datos_Base y calcula estadísticos]
índice de tablas + existencia de figuras → enlaces del visualizador
```

Los diez ETL oficiales son `etl_consumo_final_total`, `etl_consumo_industrial`,
`etl_generacion_por_fuente`, `etl_importaciones_exportaciones`, `etl_pib`,
`etl_poblacion_total`, `etl_poblacion_rural_urbana`, `etl_produccion_bruta`,
`etl_tarifa_electrica_media` y `etl_valor_agregado_industrial`. El último
también consume `pib.csv`, una dependencia entre datos normalizados necesaria
para calcular el valor agregado. `eco_cg_comun` lee la fuente complementaria
del equipo; no forma parte de los 15 IEDS.

| Responsabilidad previa | Ubicación |
| --- | --- |
| Cálculos ECO nacionales y validación | `generar_matriz_indicadores.calcular_valores`, lambdas de `INDICADORES` |
| Razones de sumas ECO | `viz_comun.agregados_eco`; fórmulas auditables equivalentes en el libro ECO |
| Media ponderada | `viz_comun.media_ponderada` |
| Ponderadores ENV y SOC3; SOC1 poblacional | `procesar_dimensiones`, tablas BASE y CSV de población |
| SOC2 nacional y agregado | `etl_soc2`: gasto e ingreso expandidos por clientes, razón de sumas |
| Promedio simple | Empaquetado en `viz_comun`, Markdown y APA; filas Excel y trazas de figuras |
| Mediana, DE poblacional, CV y estadísticos | `generar_tablas_apa`; mediana ECO-CG específica en `eco_cg_comun` |
| Fichas científicas y formato visual | `viz_comun.FICHAS`, incluidos hallazgos regionales |
| Definiciones fuera de FICHAS | `INDICADORES`, `CAT_ENV`, `CAT_SOC`, ponderadores, listas de series, ficha ECO-CG y catálogo de variables base APA |

Dependencias locales previas, agrupadas por función:

| Módulos | Imports locales previos |
| --- | --- |
| `config_siepac`, `catalogo_datos_raw` | Ninguno |
| `etl_comun`, `eco_cg_comun`, `figuras_comun`, `generar_capturas_readme` | `config_siepac` |
| Consumo final/industrial, PIB, población total/rural-urbana, tarifa, consolidación | `config_siepac`, `etl_comun` |
| Generación por fuente, importaciones/exportaciones, producción bruta, VAI, SOC2 | `config_siepac` |
| Verificación y manifiesto raw | `catalogo_datos_raw`, `config_siepac` |
| Matriz de indicadores | `config_siepac`, `etl_comun` |
| Dimensiones | `config_siepac`, `etl_comun`, `viz_comun` |
| `viz_comun` | `config_siepac` |
| Resumen | `config_siepac`, `viz_comun` |
| APA y visualizador | `config_siepac`, `eco_cg_comun`, `viz_comun` |
| Figuras | Los anteriores y `figuras_comun` |
| `run_pipeline` | Ninguno; ejecuta secuencialmente los scripts |

## 3. Arquitectura final y decisiones mínimas

```text
Fuentes → ETL específicos → CSV normalizados
                            ↓
          calculos_indicadores + datos_dimensiones
                            ↓
                resultados en DataFrames
                 ├─ libros Excel auditables
                 └─ CSV ECO + resultados_ECO/ENV/SOC.json
                                 ↓
                       resultados_indicadores
                         ├─ Markdown/CSV
                         ├─ tablas APA
                         ├─ figuras
                         └─ visualizador ← plantillas/visualizador.html

metadatos_indicadores → catálogos Excel
                     → presentacion_indicadores → productos públicos
viz_comun → paleta y reexportaciones compatibles
```

- `calculos_indicadores.py` contiene las ocho expresiones ECO, sus
  validaciones, las razones de sumas, la media ponderada y los estadísticos
  poblacionales extraídos. No depende de presentación ni realiza E/S.
- `datos_dimensiones.py` conserva la lectura particular de los **insumos
  originales** ENV/SOC, incluido el respaldo ENV1 corregido en fase 3,
  y prepara bases y agregados sin escribir productos.
- `metadatos_indicadores.py` es la fuente autoritativa de nombres, dimensiones,
  unidades, fórmulas legibles, descripciones, notas, hallazgos, subseries y
  ponderadores. Las listas de series se derivan del catálogo.
- `presentacion_indicadores.py` conserva formatos, sufijos, modos y notas
  visuales. Compone el contrato público histórico sin mutar las fichas
  científicas. Comparte la adaptación de subseries de Markdown y APA.
- `resultados_indicadores.py` define la escritura/lectura del intercambio y
  el empaquetado común de países, promedio, agregado e imputaciones. Es
  independiente de los generadores y de Plotly.
- Los generadores de libros conservan sus entradas de consola y exportan
  también los resultados estructurados desde los mismos DataFrames.
- La plantilla web se carga desde `src/plantillas/visualizador.html` y se
  incrusta íntegra junto con Plotly. El HTML final sigue siendo autocontenido.

Se mantuvo `src/` plano. No se justificaba migrar todos los scripts a un
paquete ni añadir infraestructura de ejecución. Las pruebas de arquitectura
comprueban que no hay ciclos y que las cuatro capas de datos/ciencia no
importan módulos de presentación.

## 4. Metadatos y variantes conservadas

Las unidades ECO y los títulos coincidentes se toman de `FICHAS`; las
fórmulas y unidades ENV/SOC coincidentes se toman de la subserie canónica.
Las diferencias literales del Excel se registran explícitamente en
`TEXTOS_EXCEL_ECO` y `TEXTOS_EXCEL_DIMENSIONES`, en el mismo módulo de
metadatos. Ejemplos: `CO2eq` frente a `CO₂eq`, `const.` frente a `constantes`,
títulos largos, textos de fuente y notas históricas.

No se sustituyen esas variantes por la redacción web: eso cambiaría las
celdas/textos congelados. Las plantillas de fórmulas Excel y formatos de
celda siguen en los generadores de libros; sus fórmulas ejecutables se
verifican contra el baseline. El catálogo de **variables de entrada** APA y
las referencias bibliográficas pertenecen al documento, no al catálogo IEDS.
ECO-CG mantiene su módulo específico y su condición complementaria.

La nota histórica ENV1 sobre la fórmula original y la rotulación de la
escala del PIB ambiental se conservan; sus límites ya están documentados en
`AUDITORIA_ENV1_FALLBACK.md`. Esta fase no hace una corrección editorial ni
metodológica adicional.

## 5. Dependencias producto → producto eliminadas

| Antes | Ahora |
| --- | --- |
| `Datos_Base` del Excel ECO → `viz_comun` | Base ECO estructurada → lector común |
| Hojas ENV/SOC con `skiprows=2` → series | Series y agregados con claves explícitas en JSON |
| Texto de fila `Agregado regional` → valor regional | Clave `agregados` del resultado |
| `Datos_Base` de tres libros → APA | `leer_bases()` común |
| Empaquetado ECO duplicado en APA y Markdown | `cargar_paquete()` común |

La dependencia del índice de tablas y de la existencia de figuras en el
visualizador se mantiene para construir/verificar enlaces, sin extraer de
ellos cifras científicas. Las capturas del README siguen leyendo la página
que deben fotografiar. Ninguna fuente original fue sustituida por un derivado.

Los JSON son intermedios regenerables y están ignorados por Git. Se conserva
en su serialización la precisión decimal histórica de las celdas numéricas
(`.16g`): antes los consumidores recibían los valores después de pasar por
openpyxl. Esta frontera evita que la retirada del Excel cambie sus entradas;
no se aplica a los cálculos originales ni al CSV ECO. La comparación exacta
comprueba el resultado de extremo a extremo, sin aumentar tolerancias.

## 6. Archivos y responsabilidades reubicadas

**Creados:**

- `src/calculos_indicadores.py`
- `src/datos_dimensiones.py`
- `src/metadatos_indicadores.py`
- `src/presentacion_indicadores.py`
- `src/resultados_indicadores.py`
- `src/plantillas/visualizador.html`
- `tests/test_arquitectura.py`
- `docs/FASE4_REFACTOR_ARQUITECTURA.md`

**Archivos completos movidos o eliminados:** ninguno. Se trasladaron
funciones, catálogos y el literal de la plantilla, conservando las entradas
de ejecución originales.

**Modificados:** `.gitignore`, `README.md`, `tests/README.md`,
`src/viz_comun.py`, `src/generar_matriz_indicadores.py`,
`src/procesar_dimensiones.py`, `src/generar_resumen_indicadores.py`,
`src/generar_tablas_apa.py`, `src/generar_figuras_tesis.py` y
`src/generar_visualizador.py`.

Las expresiones ECO y los controles siguen en el mismo orden. Las funciones
de media ponderada, agregado ECO y estadísticos conservan sus operaciones.
`leer_env` conserva la prioridad del precalculado, incluido cero, y la
lambda de respaldo `f[2] / f[4]`. El procesamiento ENV/SOC comparte los
agregados calculados con ambos exportadores, sin recalcular desde el libro.

## 7. Compatibilidad y límites deliberados

- Se conserva `python src/run_pipeline.py` y su lista de 18 etapas, sin cambios.
- Los scripts individuales mantienen nombre, argumentos y productos finales.
- `viz_comun` reexporta las funciones anteriores y las fichas públicas;
  los consumidores del repositorio usan directamente los módulos nuevos.
- `generar_matriz_indicadores.calcular_valores` y
  `procesar_dimensiones.leer_env/leer_soc` siguen disponibles.
- El argumento histórico de `cargar_datos(ruta_excel)` identifica ahora la
  carpeta de los resultados; no abre el archivo Excel indicado.
- Tras actualizar una copia antigua, se debe ejecutar el pipeline para
  crear los tres JSON antes de ejecutar consumidores individuales. No hay
  fallback silencioso a los Excel generados; se informa el intermedio faltante.
- ENV/SOC conservan su carácter opcional para los lectores de productos.

Se conservaron los ETL específicos, la fórmula SOC2 en su ETL, el tratamiento
particular ENV6, las fórmulas Excel auditables, los textos metodológicos,
los estilos y el diseño web. APA sigue reuniendo construcción de tablas,
composición documental y conversión opcional a Word: fragmentar esas partes
habría dispersado convenciones editoriales compartidas. La separación útil
fue retirar de allí ciencia y acceso a productos Excel, no dividir por líneas.

## 8. Aclaración metodológica autorizada

El encargo adjunto contenía dos restricciones antiguas que negaban los
agregados SOC2 y SOC3. El usuario confirmó expresamente que prevalece la
fase cuantitativa aprobada:

- SOC2_PROM y SOC2_VULNERABLE tienen agregado por razón de sumas,
  reconstruyendo gasto e ingreso mediante clientes residenciales/proxy.
- SOC3 rural y urbano usan sus poblaciones respectivas; conservan su
  condición de aproximación metodológica.
- ECO14 continúa sin agregado por falta de energía regulada vendida.

No se cambió ninguna fórmula ni resultado por esa discrepancia. El usuario
pidió dejar constancia de que las versiones antiguas de `AGENTS.md` requieren
actualización. La copia local leída ya expresa esas ponderaciones; sí queda
pendiente actualizar en ese contexto interno la ubicación nueva de `FICHAS`
y las referencias a generadores ausentes. No se sobrescribió ese archivo
ignorado por Git.

## 9. Pruebas por bloque

| Punto de control | Resultado |
| --- | --- |
| Inicio | 136 passed |
| 1. Cálculos y estadísticos | 136 passed |
| 2. Metadatos | 136 passed |
| 3. Resultados estructurados | 136 passed; 139 con tres contratos nuevos |
| 4. Plantilla web | 139 passed |
| 5. Revisión APA, catálogos e imports | 139 passed |
| Suite final, incluida conservación de plantilla | 140 passed, 0 xfailed |

Las 136 pruebas anteriores permanecen intactas. No se retiraron pruebas,
marcas ni aserciones. Los cuatro contratos nuevos comprueban separación de
capas/ciclos, identidad de reexportaciones y aislamiento de fichas, lectura de
resultados con `pd.read_excel` prohibido, y SHA-256 de la plantilla original:
`989faef93dfb81a0f544045f880decf7e65b53b8cfee3f477dc1c5a8c925e1d7`.

Una primera ejecución aislada del bloque 3 se detuvo en la etapa 15 por una
tilde corrompida al trasladar la etiqueta `Inyección Biomasa` mediante una
tubería de PowerShell. Se corrigió la codificación UTF-8 y se repitió en una
copia nueva: **18/18**, igualdad exacta de CSV/libros/web y 178 archivos
originales protegidos intactos. La prueba nueva que recorre ENV6 por el
intercambio estructurado protege también ese recorrido. No fue un hallazgo
científico ni requirió modificar datos o expectativas.

## 10. Validación final

Comandos utilizados, siempre con rutas temporales nuevas:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B -m pytest -q -p no:cacheprovider --basetemp .venv/pytest-fase4-final
.\.venv\Scripts\python.exe -X utf8 -B tests/ejecutar_pipeline_aislado.py --destino .venv/pipeline-fase4-final
.\.venv\Scripts\python.exe -X utf8 -B -m pytest tests -q -p no:cacheprovider --basetemp .venv/pytest-fase4-final-aislado-verificado --resultados-dir .venv/pipeline-fase4-final
```

La suite terminó con **140 passed, 0 xfailed**, tanto antes de reconstruir
como sobre los productos de la copia final. La reconstrucción completó
**18/18 scripts OK, código 0**. `verificacion.json` confirmó paridad y los
**180 archivos originales protegidos intactos** durante la ejecución. Este
informe se completó después con los resultados; los productos de la copia
principal no se regeneraron.

La comparación adicional usa igualdad recursiva mediante JSON ordenado,
conservando tipos numéricos y sin tolerancias, redondeos nuevos ni `isclose`:

| Grupo | Escalares numéricos | Diferencias exactas |
| --- | ---: | ---: |
| Ocho CSV | 3205 | 0 |
| Valores y fórmulas de los tres libros | 2025 | 0 |
| Datos y fichas del visualizador | 920 | 0 |
| **Total** | **6150** | **0** |

También coinciden claves, longitudes, textos, fórmulas Excel, unidades,
notas, banderas, nulos, promedios y agregados. El hash de la referencia
permanece intacto:
`4fb610b68c9ffa0c6b5cdb8692063e89ef6fd07ee197b0ffa9da08d75ba5e8ce`.

Verificaciones adicionales y diferencias encontradas:

- **22/22 PNG idénticos byte a byte**, incluidos ENV1, SOC2, SOC3 y ECO14.
- Los dos HTML generales APA y el resumen Markdown coinciden íntegramente
  al normalizar solo la fecha de elaboración: `2026-08-22` → `2026-10-02`.
  La comparación no modifica los archivos.
- La Tabla 7 SOC2 HTML coincide literalmente, sin normalizar fechas.
- El visualizador coincide íntegramente al ordenar las claves de sus objetos
  JSON incrustados. La composición de fichas cambia el orden de propiedades,
  no su contenido. La plantilla HTML/CSS/JS conserva su SHA-256 original.
- El AST de las ocho lambdas ECO, `media_ponderada`, `agregados_eco`, los
  cuatro estadísticos trasladados y `leer_env` es idéntico al de `HEAD`.
- `git diff --check` no encontró errores de espacios. Git avisó de la
  normalización futura LF/CRLF en documentación; no es un cambio de cifras.
- El log conserva los cinco avisos existentes de exportación eléctrica vacía
  de Nicaragua interpretada como cero. Las dos conversiones opcionales DOCX
  no se completaron; el aviso sugiere falta de Word, sin demostrar esa causa.
  No se atribuye a esta ejecución una validación de esos DOCX.

Una invocación de pytest con `--resultados-dir` y sin el argumento `tests`
fue rechazada por el analizador de argumentos, antes de ejecutar pruebas.
Se corrigió el comando para cargar el `conftest.py` correspondiente y se
obtuvo el resultado completo anterior. No se modificaron tests por ello.

Comprobantes locales en `.venv/pipeline-fase4-final/`: `pipeline.log`,
`originales_antes.json`, `verificacion.json` y `comparacion_exacta.json`.
El script adicional está en `.venv/verificar_fase4_entrega.py`; sus aserciones
leen los originales y escriben únicamente el informe local. Estos materiales
temporales quedan fuera de Git. Las comprobaciones de plantilla y archivos
no sustituyen una nueva prueba interactiva en navegador; no se hizo un
rediseño ni se alteró el código HTML/CSS/JS de la interfaz.

## 11. Riesgos y fase 5 de cierre

- Revisar el diff y el informe antes de decidir la integración; no hay commit
  ni publicación en esta fase.
- Actualizar el contexto interno `AGENTS.md`/`CLAUDE.md` de forma autorizada,
  especialmente ubicación de fichas y referencias históricas, manteniendo su
  exclusión de Git.
- Documentar en la entrega que una copia antigua necesita regenerar los tres
  intermedios JSON con el mismo comando habitual.
- Tratar por separado las aclaraciones editoriales pendientes de ENV1/PIB;
  no incorporarlas como cambios científicos disimulados en el refactor.
- La igualdad comprobada cubre los datos actuales y los casos sintéticos
  existentes. No certifica externamente las fuentes ni resuelve la falta
  del ponderador ECO14, sus imputaciones o los límites de los proxies.
- La conversión opcional DOCX depende del entorno con Word. El contrato
  numérico y documental principal se verifica sobre CSV, libros, HTML y PNG.
