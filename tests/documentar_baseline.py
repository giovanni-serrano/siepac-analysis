"""Genera el registro legible desde la referencia fija y comprobantes locales.

Uso: python tests/documentar_baseline.py --ejecucion RUTA --pruebas-log RUTA
No consulta fuentes externas ni sobrescribe un documento existente.
"""

import argparse
import json
from pathlib import Path
import re

from baseline_utils import RAIZ, REFERENCIA, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ejecucion", required=True, type=Path)
    parser.add_argument("--pruebas-log", required=True, type=Path)
    args = parser.parse_args()
    salida = RAIZ / "docs" / "BASELINE_RESULTADOS.md"
    if salida.exists():
        parser.error("El documento ya existe; no se sobrescribe.")
    ref = json.loads(REFERENCIA.read_text(encoding="utf-8"))
    prueba = args.pruebas_log.read_text(encoding="utf-8")
    resumen = re.findall(r"\d+ passed[^\n]*", prueba)[-1].strip()
    recibo = json.loads((args.ejecucion / "verificacion.json").read_text(encoding="utf-8"))
    assert recibo["codigo_salida"] == 0 and recibo["paridad_cientifica"] and recibo["originales_intactos"]
    origen = ref["procedencia"]
    web = ref["web"]
    datos = web["datos"]
    anios = web["anios"]
    paises = web["paises"]
    lineas = [
        "# Línea base de resultados SIEPAC", "",
        "Esta referencia caracteriza el comportamiento actual. No certifica que todo",
        "el código sea correcto ni autoriza cambios metodológicos. Se conservaron",
        "las cifras, fórmulas, unidades, imputaciones, interpretaciones y productos originales.", "",
        "## Procedencia y alcance", "",
        f"- Fecha de captura (UTC): `{origen['fecha_utc']}`.",
        f"- Commit de producción: `{origen['commit']}`.",
        f"- Python: `{origen['python']}`; plataforma: `{origen['plataforma']}`.",
        f"- SHA-256 de `tests/fixtures/baseline/resultados.json`: `{sha256(REFERENCIA)}`.",
        "- Captura: `python tests/capturar_baseline.py --salida tests/fixtures/baseline/resultados.json`.",
        "- Documento: `tests/documentar_baseline.py`, leyendo exclusivamente esa captura y los comprobantes de ejecución.", "",
        "Bibliotecas registradas: " + ", ".join(f"`{p}=={v}`" for p, v in origen["dependencias"].items()) + ".", "",
        "La captura contiene los valores nacionales completos, los dos resúmenes",
        "regionales, banderas, fichas y todas las celdas de los tres libros, incluidas",
        "sus fórmulas. Guarda hashes de insumos, código y productos para identificar",
        "la procedencia; esos hashes no impiden una futura refactorización del código.", "",
        "| Resultado capturado | Filas | Productor |",
        "| --- | ---: | --- |",
    ]
    productores = {
        "matriz_consolidada_wide.csv": "consolidar_matriz.py",
        "indicadores_ECO_valores.csv": "generar_matriz_indicadores.py",
        "soc2_pais_anio.csv": "etl_soc2.py", "soc2_regional.csv": "etl_soc2.py",
        "soc2_sensibilidad.csv": "etl_soc2.py",
        "poblacion_rural_urbana.csv": "etl_poblacion_rural_urbana.py",
        "tarifa_electrica_media.csv": "etl_tarifa_electrica_media.py",
        "indicadores_consolidados_tidy.csv": "generar_resumen_indicadores.py",
    }
    for nombre, filas in ref["csv"].items():
        lineas.append(f"| `data/processed/{nombre}` | {len(filas)} | `src/{productores[nombre]}` |")
    lineas += ["",
        "También se capturaron `data/processed/indicadores_{ECO,ENV,SOC}_SIEPAC.xlsx`",
        "y los objetos DATOS, FICHAS, ANIOS y PAISES del HTML generado por",
        "`src/generar_visualizador.py`. El libro ECO procede de",
        "`generar_matriz_indicadores.py`; los libros ENV/SOC, de `procesar_dimensiones.py`.", "",
        "## Resultados regionales actuales", "",
        "Las cifras de esta tabla son las publicadas por el pipeline en el objeto",
        "DATOS de `graficos/visualizador_siepac.html`; conservan su redondeo a seis",
        "decimales. Los CSV y las celdas de los libros guardan en la referencia",
        "la precisión disponible antes de ese redondeo.", "",
        "Cada celda presenta **promedio simple / agregado**. El promedio responde",
        "al país típico y el agregado al sistema. En ENV6, el segundo número es",
        "la suma de magnitudes observadas, no una razón. «—» significa que no se",
        "construye agregado. ECO-CG es complementaria y tampoco admite agregado.", "",
        "| Serie | Unidad publicada | " + " | ".join(map(str, anios)) + " |",
        "| --- | --- | " + " | ".join(["---:"] * len(anios)) + " |",
    ]
    unidades = {}
    for codigo, ficha in web["fichas"].items():
        for serie in ficha.get("series") or [[codigo, "", "", "", ficha["unidad"]]]:
            unidades[serie[0]] = serie[4]
    for codigo, bloque in datos.items():
        if codigo == "imputados":
            continue
        celdas = []
        for i in range(len(anios)):
            agr = "—" if bloque["agregado"] is None else f"{bloque['agregado'][i]:.6f}"
            celdas.append(f"{bloque['promedio'][i]:.6f} / {agr}")
        lineas.append(f"| {codigo} | {unidades[codigo]} | " + " | ".join(celdas) + " |")
    lineas += ["", "## Casos sensibles", "", "### ECO14: imputaciones y ausencia de agregado", "",
        "Fuente: `indicadores_ECO_valores.csv` y banderas publicadas. El agregado",
        "se conserva como `null`. La mediana usada en las figuras es un resumen",
        "descriptivo de países y no sustituye a un agregado regional.", "",
        "| País | " + " | ".join(map(str, anios)) + " |",
        "| --- | " + " | ".join(["---:"] * len(anios)) + " |",
    ]
    for pais in paises:
        filas = sorted((r for r in ref["csv"]["indicadores_ECO_valores.csv"] if r["pais"] == pais), key=lambda r: r["anio"])
        lineas.append(f"| {pais} | " + " | ".join(
            f"{r['ECO14']:.9f}" + ("*" if r["tarifa_fuente_dato"] == "imputado_CAGR" else "") for r in filas) + " |")
    n_imp = sum(sum(v) for v in datos["imputados"].values())
    lineas += ["", rf"\* `imputado_CAGR`: {n_imp} de 30 observaciones; las 12 de 2023–2024 son imputadas.", "",
        "### ECO15: exportadores netos", "",
        "Fuente: `indicadores_ECO_valores.csv`. Se conservan todos los valores",
        "nacionales y regionales en la referencia. Casos negativos de 2024:", "",
        "| País | ECO15 (%) |", "| --- | ---: |",
    ]
    for r in ref["csv"]["indicadores_ECO_valores.csv"]:
        if r["anio"] == 2024 and r["ECO15"] < 0:
            lineas.append(f"| {r['pais']} | {r['ECO15']:.12f} |")
    lineas += ["", "### SOC2: razón de sumas con clientes residenciales", "",
        "Fuente: `etl_soc2.py` → `soc2_regional.csv`. La fuente canónica sigue",
        "siendo `data/raw_equipo/soc2_agregacion_regional/base_integrada.csv`.",
        "Estos resultados usan magnitudes de gasto e ingreso expandidas por clientes,",
        "no una media de porcentajes ponderada solamente por clientes.", "",
        "| Año | SOC2_PROM (%) | SOC2_VULNERABLE (%) | Brecha (pp) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for r in ref["csv"]["soc2_regional.csv"]:
        lineas.append(f"| {r['anio']} | {r['SOC2_PROM']:.15f} | {r['SOC2_VULNERABLE']:.15f} | {r['brecha_vulnerable_prom_pp']:.15f} |")
    lineas += ["", "### SOC1, SOC3, ENV6 y denominadores", "",
        "Los valores regionales de SOC1 y SOC3 figuran en la tabla anterior para",
        "los cinco años. Las pruebas ejercitan el orquestador de dimensiones con",
        "poblaciones sintéticas diferentes: SOC1 usa población total; SOC3 rural",
        "y urbano usan sus respectivas poblaciones. Se conserva el proxy de mix",
        "renovable nacional uniforme entre zonas y la heterogeneidad de SOC2.", "",
        "ENV6 conserva dos series y sus signos. No se calcula un cociente ni se",
        "interpreta la suma del saldo neto como flujo intrarregional bruto.", "",
        "Los dos PIB se conservan por separado. **Discrepancia de rotulación vigente:**",
        "`ENVs.xlsx` expresa el PIB en millones de USD constantes y el código conserva",
        "esa magnitud en una columna llamada `pib_usd_const2015`, cuya nota declara",
        "USD. La tabla siguiente conserva los números literales de las salidas;",
        "no convierte ni sustituye valores del pipeline.", "",
        "| País y año | PIB ECO (USD, valor almacenado) | PIB ENV (millones según fuente, valor almacenado) |",
        "| --- | ---: | ---: |",
    ]
    env_base = ref["libros"]["indicadores_ENV_SIEPAC.xlsx"]["Datos_Base"]
    env_por_clave = {(r[0], r[1]): dict(zip(env_base[2], r)) for r in env_base[3:]}
    for r in ref["csv"]["matriz_consolidada_wide.csv"]:
        if r["anio"] == 2024:
            e = env_por_clave[(r["pais"], r["anio"])]
            lineas.append(f"| {r['pais']} {r['anio']} | {r['pib_usd_const2015']:.0f} | {e['pib_usd_const2015']:.9f} |")
    lineas += ["", "## Auditoría de las cuatro pruebas preexistentes", "",
        "| Prueba | Qué protege | Límite |", "| --- | --- | --- |",
        "| SOC2: resultados regionales autoritativos | Cinco años de dos indicadores y brecha frente a una referencia fija | No prueba rechazo de insumos ni otras dimensiones |",
        "| Catálogo del visualizador | 15 IEDS, ECO-CG separada, dos magnitudes ENV6 y presencia de hallazgos | Estructura; no verifica cifras ni validez del hallazgo |",
        "| HTML autocontenido | Textos, marcadores, elementos de accesibilidad y ausencia de controles | Inspecciona el archivo existente; no ejecuta navegador ni cálculos |",
        "| Saneamiento de Plotly | Escape de dos caracteres de control | Higiene de serialización, no comportamiento científico |", "",
        "Las cuatro se mantuvieron intactas y pasan. La prueba SOC2 ya era una",
        "regresión científica útil; las otras tres protegen estructura/presentación.", "",
        "## Debilidades detectadas, sin corregir", "",
        "| ID | Hallazgo demostrado | Casos xfail estrictos |",
        "| --- | --- | ---: |",
        "| D01 | Consumo final, consumo industrial y población total aceptan duplicados o un año completo ausente | 6 |",
        "| D02 | Consolidación continúa con duplicados, país ausente, año ausente o variable ausente; `aggfunc=first` descarta el duplicado conflictivo | 4 |",
        "| D03 | Tarifa acepta un año ausente si los registros restantes no tienen nulos | 1 |",
        "| D04 | El cálculo ECO no rechaza un denominador cero y puede producir infinito | 1 |",
        "| D05 | La lectura ENV sobrescribe claves repetidas con la última fila | 1 |",
        "| D06 | El respaldo de ENV1 sin valor precalculado usa PIB en millones como USD y multiplica por 10⁶ la intensidad del caso sintético | 1 |", "",
        "D06 no cambia los resultados precalculados actuales. Se comprobó con un",
        "libro sintético que reproduce la unidad del encabezado de la fuente. La",
        "discrepancia de nombre/nota del PIB ambiental también se conserva como",
        "limitación pendiente. Los xfail verifican defectos concretos; errores",
        "inesperados de preparación no se convierten en fallos esperados.", "",
        "Otras limitaciones observadas: fichas y fórmulas repartidas entre módulos;",
        "lectura de resultados a través del formato de los Excel; conclusiones con",
        "cifras literales; publicación Pages sin pruebas previas. No se modificó",
        "ninguno de esos comportamientos. El contexto local menciona generadores",
        "transitorios ya ausentes; para esta ejecución se siguió el orquestador real.", "",
        "## Ejecución y conservación", "",
        "Se ejecutó `tests/ejecutar_pipeline_aislado.py --destino .venv/baseline-pipeline`.",
        "La copia comenzó sin productos procesados; usó los mismos scripts e insumos.",
        "`src/run_pipeline.py` completó **18/18** etapas con código de salida **0**.",
        "Los ocho CSV, las celdas de los tres libros y los datos/fichas web coinciden",
        "con la captura bajo las tolerancias definidas. Se generaron 22 figuras y",
        "los HTML consolidados de 75 tablas. No se compararon píxeles de las figuras.", "",
        f"Se verificó por SHA-256 que los **{recibo['archivos_protegidos']} archivos originales** protegidos permanecieron intactos.",
        "El pipeline avisó que las exportaciones eléctricas vacías de Nicaragua",
        "2020–2024 se interpretan como cero. Ese comportamiento existente no se alteró.",
        "La conversión opcional de los dos DOCX no se completó; el log indica que",
        "Word podría no estar disponible. No se verificaron los DOCX en esta ejecución.", "",
        "Resultado de pytest, incluyendo las cuatro pruebas originales:", "", "```text", resumen, "```", "",
        "Las comparaciones de productos se ejecutaron contra la copia reconstruida",
        "con `--resultados-dir .venv/baseline-pipeline`. Los recálculos y contratos",
        "importan los módulos originales intactos. No hubo fallos inesperados ni",
        "pruebas omitidas en esa ejecución. Los 14 xfail corresponden a seis",
        "debilidades, no a catorce errores científicos independientes.", "",
        "Los comprobantes locales son `.venv/baseline-pipeline/pipeline.log`,",
        "`originales_antes.json`, `verificacion.json` y el log de pytest indicado",
        "al generar este documento. `.venv` está ignorado por Git.", "",
        "## Uso en la siguiente fase", "",
        "Consultar `tests/README.md`. Los valores esperados son fijos; las pruebas",
        "no los regeneran. No reemplazar la referencia para resolver diferencias.",
        "Una refactorización debe conservarla; una corrección científica requiere",
        "revisión separada. Los xfail son estrictos: un arreglo futuro exige revisar",
        "la prueba y retirar su marca. Para mostrar los defectos como fallos ordinarios",
        "puede ejecutarse pytest con `--runxfail` sobre esos casos.", "",
        "Tolerancias de regresión: `rtol=1e-12`, `atol=1e-9`; igualdad exacta para",
        "enteros contra enteros, textos, fórmulas, banderas y claves. Los tests de",
        "presentación admiten el redondeo ya existente a seis decimales. La captura",
        "de libros excluye estilos y metadatos binarios; HTML se compara por sus",
        "objetos de datos y fichas. Las fuentes oficiales siguen siendo necesarias",
        "para reproducir todo desde cero; no se redistribuyen en las pruebas.", "",
    ]
    with salida.open("x", encoding="utf-8") as archivo:
        archivo.write("\n".join(lineas))
    print(f"Documento creado: {salida}")


if __name__ == "__main__":
    main()
