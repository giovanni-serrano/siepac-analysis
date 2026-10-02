# Fase 5: cierre, documentación, CI e integración

Fecha: 2026-10-02. Rama: `refactor/cierre`.
Base heredada: `8edcc92 refactor: separar calculos y productos del pipeline`.
Referencia histórica: tag `pre-refactor-2026`, commit `21f7128`.
Esta es la fase final; no añade arquitectura ni cambia decisiones científicas.
No se hizo commit, push, merge, squash ni modificación de `main`.

## 1. Estado inicial y diagnóstico

El árbol versionado estaba limpio. La fase 4 había cerrado con 140 pruebas,
pipeline 18/18, 6150 valores exactos y 22 figuras idénticas al estado inicial.
Se leyeron completos el contexto interno y los informes de las fases 1–4,
README, guía de pruebas, requisitos y workflow Pages. Se revisaron los módulos
actuales, sus consumidores y el diff acumulado desde el tag.

Los asuntos de cierre eran concretos: Pages no exigía pruebas; el README no
describía la preparación completa del entorno; Python 3.10 era incompatible
con las dependencias actuales; NumPy se importaba directamente pero solo
llegaba como dependencia transitiva; el contexto interno conservaba referencias
a módulos ausentes y a la antigua ubicación de FICHAS. El mensaje de fallo
DOCX atribuía tentativamente el problema a falta de Word sin demostrarlo.

## 2. Contexto interno y metodología aprobada

Se actualizó `AGENTS.md` por petición expresa del autor. Su copia anterior se
conserva localmente en `.venv/fase5-contexto-original/AGENTS.md`. Sigue ignorado
por Git y no se incorpora al sitio ni al diff público. `CLAUDE.md` ya importa
ese archivo, por lo que se conservó sin duplicar su contenido.

Se explicita que prevalece la fase cuantitativa aprobada:

- SOC2_PROM y SOC2_VULNERABLE tienen agregado por razón de sumas de gasto e
  ingreso reconstruidos mediante clientes residenciales y vulnerables proxy.
  No se sustituyen por una media de porcentajes ponderada solo por clientes.
- SOC3 tiene agregados rural y urbano con las poblaciones correspondientes;
  conserva su condición de aproximación y no observa el origen de la
  electricidad consumida por cada hogar.
- ECO14 no tiene agregado: su mediana de países es descriptiva y falta el
  ponderador de energía regulada vendida.
- ECO-CG no constituye un costo regional homogéneo ni un IEDS adicional.

El contexto ahora identifica `metadatos_indicadores.FICHAS`, separa formato
visual, cálculos y resultados, documenta los tres JSON y retira referencias
operativas al panel, explorador y manifiesto de tesis ausentes. Se aclara la
excepción histórica de escala/rotulación del PIB ambiental ya auditada,
sin modificar columnas, datos ni fórmulas. Las advertencias existentes de
imputación, proxies, ENV6 y PIB diferenciados se mantienen.

## 3. README y documentación vigente

El README conserva el alcance de tesis: seis países, 2020–2024, tres
dimensiones y 15 IEDS. Añade entorno virtual, instalación de ejecución y
pruebas, comandos de verificación, requisitos de navegador para figuras y
capturas, diferencia entre clon público y reproducción completa, CI previo
a Pages, trazabilidad y conversión DOCX opcional.

Se corrigieron referencias actuales de FICHAS en
`docs/arquitectura_visualizador_regional.md` y
`docs/GUIA_RAPIDA_INDICADORES_SIEPAC.md`. Los informes de fases anteriores
permanecen intactos: sus nombres de módulo y estados de pruebas describen
el momento auditado y no se reescribe esa historia. No se editó a mano ningún
producto generado ni el resumen metodológico.

## 4. Política de JSON intermedios

Todos viven en `data/processed/` y se regeneran con las etapas existentes.

| Archivo | Productor | Contenido | Consumidores |
| --- | --- | --- | --- |
| `resultados_ECO.json` | `generar_matriz_indicadores.py` | Base ECO; los valores nacionales siguen en `indicadores_ECO_valores.csv` | Resumen, tablas, figuras y visualizador mediante `resultados_indicadores` |
| `resultados_ENV.json` | `procesar_dimensiones.py` | Base, series, agregados ENV y ENV6 | Los mismos |
| `resultados_SOC.json` | `procesar_dimensiones.py` | Base, series y agregados SOC | Los mismos |

Son **productos intermedios, no fuentes científicas**. Se mantienen fuera de
Git: su regeneración requiere los insumos originales, incluidos los ocho
archivos oficiales que no se redistribuyen. No se promete regenerarlos desde
un clon público incompleto. La suite pública prueba el intercambio usando
fixtures en temporales, sin publicar copias de intermedios locales.

`.gitignore` reemplaza el patrón `resultados_*.json` por esos tres nombres
exactos, para no ocultar futuros JSON de otra naturaleza. Añade únicamente
`.pytest_cache/` y `_site/` como caché y empaquetado. Conserva las exclusiones
de fuentes no redistribuibles, CSV regenerables, DOCX y documentos internos.
El catálogo raw, los extractos redistribuibles de PIB y población por zona,
las fuentes del equipo, los metadatos y los fixtures siguen versionados.

## 5. CI y publicación final

Se conserva un único workflow: `.github/workflows/pages.yml`.

- `tests` se ejecuta en pushes, PR dirigidos a `main` y ejecución manual.
  Usa `ubuntu-latest`, Python 3.13.5, `actions/checkout@v7` y
  `actions/setup-python@v7`; instala ambos archivos de requisitos, ejecuta
  `pip check` y `python -B -m pytest tests -q -rs`.
- `deploy` declara `needs: tests`, exige la referencia `refs/heads/main`
  y excluye eventos de PR. No contiene `always()` ni `continue-on-error`.
- Los permisos generales son solo `contents: read`; Pages e ID token están
  limitados al trabajo de despliegue. La concurrencia distingue referencias,
  evitando que una prueba de otra rama cancele la publicación de `main`.
- La lista permitida de archivos del sitio se conserva. No publica fuentes,
  código, fixtures, contexto interno ni resultados JSON intermedios.
- No ejecuta el pipeline completo: no dispone de las ocho fuentes excluidas.
  Tampoco instala Chrome o Word, porque la suite pública no exporta PNG ni DOCX.

Las ocho omisiones esperadas del clon público corresponden exclusivamente a
comparaciones de CSV locales ausentes. Los recálculos con baseline, casos
sintéticos, libros, datos/fichas web y fuentes del equipo sí se ejecutan.
Cualquier fallo de esas pruebas hace fallar CI e impide el despliegue.

Se comprobó la estructura YAML, eventos, comandos, permisos y dependencia
entre trabajos. La semántica de `needs` se contrastó con la
[documentación de GitHub](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-jobs)
y la configuración de Python con
[actions/setup-python](https://github.com/actions/setup-python).
No se disparó una ejecución remota, porque esta fase no autoriza push ni
integración. La simulación pública local no se presenta como una ejecución
del runner Ubuntu de GitHub.

## 6. Dependencias y DOCX

| Dependencia | Uso | Decisión |
| --- | --- | --- |
| NumPy 2.5.1 | Validación numérica y ETL SOC2; pruebas | Se declara directamente la versión ya instalada y registrada en el baseline |
| pandas 3.0.5 | ETL, cálculos y tablas | Se conserva |
| openpyxl 3.1.5 | Lectura de fuentes y libros auditables | Se conserva |
| Plotly 6.9.0 | Figuras y biblioteca incrustada del visualizador | Se conserva |
| Kaleido 1.3.0 | Exportación PNG del pipeline | Se conserva; necesita Chrome/Chromium |
| Playwright 1.61.0 | Capturas opcionales del README | Se conserva; solo ese uso requiere instalar su navegador |
| pytest 9.1.1 | Exclusivo de pruebas | Sigue en `requirements-test.txt` |
| Word + PowerShell/COM | Conversión DOCX opcional en Windows | Dependencia del entorno, no paquete Python |

Los metadatos instalados declaran Python ≥3.11 para pandas y ≥3.12 para
NumPy. Se corrige el mínimo documentado a 3.12 y se usa la versión verificada
3.13.5 en CI. No se actualiza ninguna versión científica existente ni se
introduce un gestor nuevo. Los requisitos fijan dependencias directas, no
son un lock completo de transitivas; el registro de instalación permite
identificar el entorno comprobado. El requisito de Chrome y su instalación
se contrastaron con la [documentación de Plotly](https://plotly.com/python/static-image-export/).

**Diagnóstico DOCX demostrado:** el registro Windows contiene
`Word.Application`, pero una conversión aislada con log DEBUG falla al crear
el objeto COM con **HRESULT 0x80070520**, indicando que no existe la sesión
de inicio de sesión especificada. No es evidencia de ausencia de Word.
Se corrige solo el aviso, sin rediseñar la conversión ni sus rutas de salida.
El pipeline conserva los HTML y continúa; `--sin-docx` permite omitir el paso
al invocar el generador individualmente. DOCX requiere una sesión donde Word
pueda automatizarse y no se considera verificado en este entorno.

## 7. Limpieza prudente

No se eliminó ningún archivo. Se corrigió un comentario de paridad en el
generador ECO y el aviso DOCX descrito. La lógica científica no se tocó.

| Elemento revisado | Decisión y motivo |
| --- | --- |
| Panel, explorador y manifiesto de tesis antiguos | Ya ausentes del tag y rama; se corrigen referencias operativas, no se cuentan como eliminaciones |
| `viz_comun.py` | Se conserva: paleta importada por el visualizador y compatibilidad comprobada por tests |
| `generar_capturas_readme.py` | Se conserva: utilidad manual documentada, fuera de las 18 etapas |
| `verificar_datos_raw.py`, `generar_manifiesto_raw.py` | Se conservan: verificación y documentación del catálogo de fuentes |
| Scripts de captura/documentación del baseline | Se conservan: procedencia auditable y rechazo de sobrescritura; no se ejecutan para cambiar expectativas |
| Informes de fases 1–4 | Se conservan como trazabilidad histórica |
| Carpetas locales de análisis, tablas antiguas y evidencia bajo `.venv` | Se conservan: no se presume que su contenido sea prescindible; siguen ignoradas |
| `CLAUDE.md` | Se conserva: remite al contexto único actualizado |

## 8. Auditoría acumulada desde `pre-refactor-2026`

El tag apunta a `21f71282a11176ac74b9fe6c42b30c610b88da95`. Los cuatro commits
heredados son consecutivos y sus responsabilidades están explicadas:

| Clase | Commit o fase | Alcance |
| --- | --- | --- |
| Pruebas | `8a67355` y ampliaciones posteriores | Baseline, utilidades, contratos, casos defensivos y arquitectura; 136 pruebas originales de cierre científico más cuatro arquitectónicas |
| Validaciones | `a46a9cd` | Panel completo, duplicados, finitud, denominadores y banderas; sin alterar datos válidos |
| Corrección ENV1 | `54b04c9` | Única corrección científica: respaldo C/E en escala correcta, sin uso por los 30 precalculados actuales |
| Arquitectura | `8edcc92` | Extracciones, metadatos, JSON compartidos, plantilla y reexportaciones; comandos y resultados conservados |
| Documentación | Fases 1–5 | Informes, README y guías; contexto local no versionado |
| CI | Fase 5 sin commit | Pruebas previas a Pages y separación público/local |

Los 37 archivos cambiados entre el tag y el commit heredado se clasifican
completamente: 11 de pruebas/requisitos de pruebas, seis de documentación,
seis ETL/consolidación de validaciones y 14 de arquitectura/configuración.
La validación ECO/ENV y la corrección ENV1 atraviesan archivos posteriormente
reubicados; sus commits separados permiten distinguirlas del movimiento.
No se encontraron cambios ajenos a esas categorías.

La comparación acumulada de `data/`, `graficos/`, `salidas/`, `index.html` y
`src/run_pipeline.py` contra el tag no tiene diferencias. Los tests originales
SOC2 y visualizador tampoco se modificaron. El baseline permanece igual al
introducido en fase 1. En fase 5 solo cambia en producción un comentario y
un mensaje de log de error opcional; no cambian expresiones ejecutables de
cálculo, fórmulas, metadatos científicos ni plantillas de salida.

## 9. Validación final

Se creó `.venv/fase5-entorno-limpio` sin heredar paquetes del entorno anterior,
se instalaron ambos requisitos desde cero y `pip check` terminó sin conflictos.
Las versiones directas permanecieron iguales a las de la referencia. El
registro local está en `.venv/fase5-entorno-verificado.json`; la instalación
queda registrada en `.venv/fase5-instalacion-red.log`.

| Comprobación | Resultado |
| --- | --- |
| `python -B -m pytest -q` sobre el repositorio | **140 passed**, 0 skipped, 0 xfailed |
| Suite sobre copia de los 118 archivos versionados, sin insumos privados, CSV locales ni JSON intermedios | **132 passed, 8 skipped**, exclusivamente los CSV esperados |
| Pipeline aislado desde los insumos originales, usando el entorno recién instalado | **18/18 scripts OK**, salida 0 |
| Suite con `--resultados-dir .venv/pipeline-fase5-final` | **140 passed**, 0 skipped, 0 xfailed |
| Ocho CSV contra referencia fija | **3205 valores numéricos exactos**, además de claves y textos |
| Tres libros ECO/ENV/SOC contra referencia fija | **2025 valores numéricos exactos**, además de todas las celdas, fórmulas y fichas |
| Datos y metadatos del visualizador contra referencia fija | **920 valores numéricos exactos**, además de FICHAS, países y años |
| Total numérico | **6150 valores, cero diferencias**; sin tolerancia ni redondeo adicional |
| Figuras regeneradas | **22/22 PNG idénticos byte a byte** a los originales |
| Inventario protegido durante el pipeline | **181 archivos intactos** |
| Fuentes, fixtures y módulos versionados frente a `.gitignore` | Ninguno ocultado por las reglas |
| Diff de producción de esta fase | AST idéntico al heredado salvo el texto del aviso DOCX |

Las ejecuciones pytest usaron `-p no:cacheprovider` y destinos `--basetemp`
nuevos bajo `.venv`. Para la copia pública se invocó pytest desde la raíz
autorizada, apuntando a `.venv/fase5-clon-publico/tests`: sus fixtures y rutas
de producción se resuelven dentro de esa copia. Los intentos desde el
subdirectorio habían fallado por permisos del sandbox al crear temporales,
sin fallos de cálculo; cambiar el directorio de invocación resolvió ese límite.
Esta comprobación se hizo en Windows; no sustituye la primera ejecución remota
del workflow en Ubuntu.

Comandos principales, ejecutados con Python del entorno limpio:

```powershell
python -B -m pytest -q -p no:cacheprovider --basetemp .venv/pytest-fase5-cierre-total
python -X utf8 -B tests/ejecutar_pipeline_aislado.py --destino .venv/pipeline-fase5-final
python -B -m pytest tests -q --resultados-dir .venv/pipeline-fase5-final -p no:cacheprovider --basetemp .venv/pytest-fase5-final-aislado
```

Se conservaron copia, log y comprobantes locales en
`.venv/pipeline-fase5-final/`: `pipeline.log`, `originales_antes.json`,
`verificacion.json` y `comparacion_exacta.json`. La comparación exacta adicional
lee los ocho CSV, los tres libros y el objeto web completos, sin tolerancias;
el auxiliar local queda en `.venv/verificar_fase5_entrega.py`.

El SHA-256 de `tests/fixtures/baseline/resultados.json` sigue siendo:

```text
4fb610b68c9ffa0c6b5cdb8692063e89ef6fd07ee197b0ffa9da08d75ba5e8ce
```

**Diferencias no científicas aceptadas:** los dos HTML APA generales y el
resumen Markdown cambian únicamente la fecha `2026-08-22` por `2026-10-02`.
La Tabla 7 conserva igualdad literal. El visualizador conserva igualdad
completa al ordenar las claves de sus objetos JSON incrustados. No se
detectaron otras diferencias semánticas ni numéricas. Los libros se comparan
por celdas, fórmulas y contenido, sin exigir identidad del contenedor ZIP.
Los DOCX opcionales no se generaron por la limitación COM ya diagnosticada.

No se sobrescribieron productos originales ni se actualizó la referencia.

## 10. Inventario de esta fase

Creado: `docs/FASE5_CIERRE.md`.

Modificados versionados: `.github/workflows/pages.yml`, `.gitignore`,
`README.md`, `requirements.txt`, `tests/README.md`,
`docs/arquitectura_visualizador_regional.md`,
`docs/GUIA_RAPIDA_INDICADORES_SIEPAC.md`,
`src/generar_matriz_indicadores.py` y `src/generar_tablas_apa.py`.

Modificado local ignorado: `AGENTS.md`. Eliminados: ninguno.
`requirements-test.txt`, la arquitectura, el baseline y los tests se conservan.

## 11. Riesgos y recomendación de integración

La reproducción completa seguirá requiriendo los insumos oficiales locales;
las limitaciones de proxies, ECO14 y rotulación histórica ENV1/PIB no se
convierten en cambios de metodología durante el cierre. La generación DOCX
depende de una sesión Word funcional. La identidad binaria de PNG puede
depender de navegador, fuentes y plataforma; la suite pública comprueba sus
series en memoria y el cierre local contrasta los 22 PNG reconstruidos.

Con la validación final aprobada, el estado queda **preparado para integración**.
Se recomienda registrar los cambios públicos de esta fase en un commit de
cierre, abrir una revisión/PR de `refactor/cierre` hacia `main`, conservar los
commits separados de las cuatro fases anteriores y exigir el trabajo
`Pruebas del clon público` en verde en GitHub antes de integrar. El contexto
interno queda fuera del commit. Es una recomendación para el siguiente acto
de integración, no una operación realizada: no se hizo commit, push ni merge.
No se exige otra fase de refactor ni se modifica la protección remota de
ramas desde esta sesión.
