# Pruebas de conservación científica

La fase 1 estableció la referencia sin cambiar `src`, los insumos ni los productos.
La referencia está en `fixtures/baseline/resultados.json`; la explicación y
las cifras regionales están en `../docs/BASELINE_RESULTADOS.md`.

La fase 2 endurece las validaciones de entradas inválidas: 13 de los 14
xfail originales pasaron a pruebas normales. En esa fase quedó pendiente D06
(escala del respaldo ENV1), fuera de su alcance metodológico. El mapa completo,
la comparación numérica y los resultados están en `../docs/FASE2_VALIDACIONES.md`.
`test_validaciones_integridad.py` añade casos de borde y comprueba que una
entrada inválida no sobrescribe las salidas ECO.

La fase 3 audita D06 y corrige únicamente el respaldo de ENV1: el PIB del
libro ambiental está en millones de USD constantes. Los 30 valores actuales
están precalculados y no activan esa ruta. Su prueba sintética pasa ahora sin
`xfail`; se añaden la reproducción de las 30 observaciones sin precalculados
y la conservación de valores presentes, incluido cero. Véase
`../docs/AUDITORIA_ENV1_FALLBACK.md` para la demostración y la comparación exacta.

La fase 4 mantiene las 136 pruebas anteriores y añade cuatro contratos en
`test_arquitectura.py`: capas científicas sin dependencias de presentación ni
ciclos locales, reexportaciones y fichas sin duplicación, consumo de resultados
estructurados con `read_excel` prohibido, y conservación íntegra de la plantilla
web. No cambia la referencia. El informe está en
`../docs/FASE4_REFACTOR_ARQUITECTURA.md`.

## CI y clon público

`.github/workflows/pages.yml` ejecuta la suite en Python 3.13.5 con los dos
archivos de requisitos fijados, en pushes, pull requests hacia `main` y
ejecuciones manuales. El trabajo de publicación tiene `needs: tests`: solo
despliega `main` si las pruebas terminan correctamente. No hay
`continue-on-error` ni se ejecutan los ETL con fuentes ausentes.

En un clon que contiene únicamente archivos versionados, el resultado esperado
es **132 passed, 8 skipped**: se omiten solo las ocho comparaciones de CSV de
`data/processed/`, ausentes por diseño. Sus cálculos siguen cubiertos mediante
la referencia fija y casos sintéticos. Los libros y HTML versionados, los
insumos ENV/SOC y SOC2 del equipo y los fixtures sí se comprueban.
Con todos los CSV locales presentes, se esperan **140 passed, 0 xfailed**.

La exportación de PNG está sustituida por captura de figuras en memoria en
las pruebas; CI no necesita instalar Chrome ni iniciar Word. Este trabajo
no certifica una reconstrucción completa desde las ocho fuentes oficiales
excluidas. Esa verificación se ejecuta localmente con la copia aislada.
Los JSON de fase 4 se prueban en temporales, sin copiar intermedios privados
al clon público ni convertirlos en nuevas fuentes científicas.

## Ejecutar

En un entorno con las dependencias del proyecto:

```powershell
python -m pip install -r requirements-test.txt
python -B -m pytest tests -q -rs -p no:cacheprovider
```

Para aislar las dependencias de pruebas de un entorno científico existente:

```powershell
python -m venv --system-site-packages .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-test.txt
.\.venv\Scripts\python.exe -B -m pytest tests -q -rx --tb=no -p no:cacheprovider
```

La segunda opción hereda las bibliotecas científicas instaladas. En un clon
sin ellas, instalar primero `requirements.txt` en el entorno elegido.
Si el sandbox impide escribir en el temporal del sistema, añadir
`--basetemp .venv/pytest-NOMBRE-NUEVO`: **usar siempre una ruta nueva**, porque
pytest elimina el contenido previo del directorio indicado.

## Tres niveles de protección

1. `test_contratos_cientificos.py`: ejemplos sintéticos con respuestas
   independientes, rechazo de entradas inválidas y defectos conocidos.
2. `test_regresion_resultados.py`: compara los productos con la referencia
   fija y vuelve a ejecutar cálculos y generadores en memoria. Comprueba
   también que el comparador detecta cambios deliberados de valor, signo,
   imputación, agregado y cobertura.
3. `ejecutar_pipeline_aislado.py`: copia únicamente `src`, `data/raw` y
   `data/raw_equipo` a una ruta nueva, ejecuta el orquestador intacto y compara
   los resultados reconstruidos. No requiere modificar las rutas de producción.

```powershell
python -B tests/ejecutar_pipeline_aislado.py --destino .venv/pipeline-NOMBRE-NUEVO
python -B -m pytest tests -q -rx --tb=no -p no:cacheprovider --resultados-dir .venv/pipeline-NOMBRE-NUEVO
```

La copia conserva `pipeline.log`, `originales_antes.json` y
`verificacion.json`. El último registra el código de salida, paridad y
preservación de los originales. Las pruebas numéricas usan tolerancias
`rtol=1e-12`, `atol=1e-9`; enteros contra enteros, textos, claves, banderas
y fórmulas son exactos. Los casos sintéticos que llaman funciones que ya
redondean a seis decimales admiten ese redondeo de presentación.

Las pruebas de comparación de los ocho CSV locales se omiten explícitamente
si no existen en un clon, pues Git los ignora. Los recálculos con la referencia
fija y los productos versionados siguen disponibles. La ejecución aislada
completa exige disponer de las fuentes oficiales locales; no descarga ninguna.
`--resultados-dir` cambia los productos e insumos inspeccionados por las pruebas
nuevas; las cuatro pruebas originales conservan su comportamiento y sus rutas.

## Fallos esperados

No quedan marcas `xfail` activas tras la fase 3. Los casos que documentaban
defectos siguen presentes como pruebas normales; no se han eliminado ni
relajado sus aserciones para acomodar la implementación.

## Custodia de la referencia

Las pruebas nunca reescriben el resultado esperado. `capturar_baseline.py`
es una operación manual, separada y rechaza sobrescribir una ruta existente:

```powershell
python tests/capturar_baseline.py --salida RUTA_NUEVA.json
```

No sustituir la referencia para hacer pasar una refactorización. Ante una
diferencia, investigar primero. Un cambio científico autorizado deberá tener
su revisión independiente y una nueva referencia con procedencia explícita.
Los hashes de producción guardados en la referencia documentan su origen;
no se exige que el código futuro tenga esos mismos hashes.

Los libros se comparan por sus celdas, incluyendo fórmulas y notas, sin
metadatos de ZIP ni estilos. Si una fase futura cambia deliberadamente su
disposición, deberá adaptar el lector conservando los valores esperados.
La paridad numérica no certifica la validez externa de la metodología ni la
equivalencia visual píxel a píxel de PNG/HTML/DOCX.
