"""
viz_comun.py — Código compartido de los visualizadores
====================================================
Etapa del pipeline : visualización (módulo común, no se ejecuta directo)
Entradas           : data/processed/indicadores_ECO_valores.csv,
                     data/processed/indicadores_ECO_SIEPAC.xlsx (Datos_Base)
                     y, opcionales, los libros ENV/SOC
Salidas            : — (lo importa el visualizador regional y los productos
                     documentales)
Alimenta           : — (fichas y datos de las 3 dimensiones)
Fuente de datos    : salidas del pipeline

Módulo común de generar_visualizador.py y de los productos documentales:
rutas de insumos, constantes de estética, fichas descriptivas de los
indicadores y funciones de carga/empaquetado. Aquí vive la fuente única de
metadatos que consumen las salidas públicas.

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import json
import logging
from pathlib import Path

import pandas as pd

from config_siepac import (PAISES_SIEPAC as PAISES, ANIOS_ANALISIS as ANIOS,
                            DIR_PROCESSED)

log = logging.getLogger(Path(__file__).stem)

# ---------------------------------------------------------------------------
# RUTAS DE INSUMOS
# ---------------------------------------------------------------------------

RUTA_EXCEL = DIR_PROCESSED / "indicadores_ECO_SIEPAC.xlsx"
# Valores ECO planos calculados por generar_matriz_indicadores.py. Se leen
# de aquí y NO de las hojas ECO del Excel: esas hojas contienen fórmulas y,
# si el libro no ha pasado por Microsoft Excel, no tienen resultado cacheado
# (pandas leería NaN).
RUTA_VALORES = DIR_PROCESSED / "indicadores_ECO_valores.csv"

# Libros de las dimensiones ambiental y social (producidos por
# procesar_dimensiones.py). Si no existen, la app se genera solo con la
# dimension economica y lo avisa por consola.
RUTA_ENV = DIR_PROCESSED / "indicadores_ENV_SIEPAC.xlsx"
RUTA_SOC = DIR_PROCESSED / "indicadores_SOC_SIEPAC.xlsx"
SERIES_ENV = ["ENV1_PC", "ENV1_PIB", "ENV2_SO2_PC", "ENV2_PAR_PC",
              "ENV2_SO2_PIB", "ENV2_PAR_PIB", "ENV3"]
SERIES_SOC = ["SOC1", "SOC2_PROM", "SOC2_VULNERABLE",
              "SOC3_RURAL", "SOC3_URB"]

# ---------------------------------------------------------------------------
# PALETA Y ESTÉTICA (tonos cálidos y sobrios sobre fondo crema)
# ---------------------------------------------------------------------------

COLOR_FONDO = "#FAF9F5"        # crema cálido
COLOR_TEXTO = "#1F1E1D"        # casi negro cálido
COLOR_TEXTO_SUAVE = "#6E6A63"  # gris topo para subtítulos
COLOR_GRILLA = "#E8E4DB"       # líneas de grilla muy suaves
FUENTE_TITULO = "Georgia, 'Times New Roman', serif"
FUENTE_CUERPO = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"

# Un color por país; Nicaragua lleva el terracota de acento del proyecto.
COLORES_PAIS = {
    "Costa Rica":  "#3E8A7B",   # verde bosque
    "El Salvador": "#5B84A8",   # azul pizarra
    "Guatemala":   "#C2963F",   # ocre
    "Honduras":    "#8B7BA8",   # lila grisaceo
    "Nicaragua":   "#D97757",   # terracota
    "Panamá":      "#6B705C",   # verde oliva
}


# ---------------------------------------------------------------------------
# CARGA Y PREPARACIÓN DE DATOS
# ---------------------------------------------------------------------------

def cargar_datos(ruta_excel: Path = RUTA_EXCEL) -> dict[str, pd.DataFrame]:
    """Carga los valores de los indicadores ECO y la matriz de datos base.

    Los VALORES vienen de indicadores_ECO_valores.csv (una fila por
    pais-anio, una columna por indicador); aqui se pivotea cada indicador
    al layout pais x anio que espera el resto del script. La hoja
    Datos_Base del Excel si se lee directo (contiene valores planos,
    no formulas).
    """
    if not RUTA_VALORES.exists():
        raise FileNotFoundError(
            f"No se encontró {RUTA_VALORES}.\n"
            "Ejecuta antes: python src/generar_matriz_indicadores.py "
            "(genera el CSV de valores junto con el Excel).")
    if not ruta_excel.exists():
        raise FileNotFoundError(
            f"No se encontró {ruta_excel}.\n"
            "Verifica que el archivo indicadores_ECO_SIEPAC.xlsx esté en "
            "data/processed/ (o ajusta RUTA_EXCEL al inicio del script).")

    valores = pd.read_csv(RUTA_VALORES)
    hojas = {}
    for codigo in ["ECO1", "ECO2", "ECO3", "ECO6", "ECO11", "ECO13", "ECO14", "ECO15"]:
        df = valores.pivot(index="pais", columns="anio",
                           values=codigo).reset_index()
        # Normalización de las columnas de año al intervalo 2020–2024.
        df.columns = ["pais"] + [int(c) for c in df.columns[1:]]
        hojas[codigo] = df

    # Bandera de imputacion (para ECO14) y la matriz completa de datos
    # base (para la vista "Matriz de datos base" de la app).
    hojas["tarifa_flag"] = valores[["pais", "anio", "tarifa_fuente_dato"]].copy()
    hojas["datos_base"] = pd.read_excel(ruta_excel, sheet_name="Datos_Base")
    return hojas


def preparar_datos(hojas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Convierte las hojas (pais x anio) a UNA tabla larga:

        pais | anio | ECO1 | ECO3 | ... | ECO15 | tarifa_imputada

    Este formato 'tidy' es el que Plotly Express consume directamente.
    """
    largos = []
    for codigo in ["ECO1", "ECO2", "ECO3", "ECO6", "ECO11", "ECO13", "ECO14", "ECO15"]:
        largo = hojas[codigo].melt(id_vars="pais", var_name="anio",
                                   value_name=codigo)
        largos.append(largo.set_index(["pais", "anio"]))
    df = pd.concat(largos, axis=1).reset_index()

    # Bandera de imputacion para ECO14 (viene de Datos_Base).
    flag = hojas["tarifa_flag"].rename(
        columns={"tarifa_fuente_dato": "tarifa_imputada"})
    flag["tarifa_imputada"] = flag["tarifa_imputada"] == "imputado_CAGR"
    df = df.merge(flag, on=["pais", "anio"], how="left")

    df["anio"] = df["anio"].astype(int)
    return df.sort_values(["pais", "anio"]).reset_index(drop=True)


def media_ponderada(valores: dict, pesos: dict) -> list:
    """Σ v·w / Σ w por año sobre {pais: [v_2020..v_2024]}; omite los
    países sin dato ese año. Con el denominador del indicador como peso
    es matemáticamente idéntica a la razón de sumas Σ N_i / Σ D_i."""
    salida = []
    for i in range(len(ANIOS)):
        num = den = 0.0
        for p in PAISES:
            v, w = valores[p][i], pesos[p][i]
            if v is None or w is None:
                continue
            num += v * w
            den += w
        salida.append(round(num / den, 6) if den else None)
    return salida


def agregados_eco(base: pd.DataFrame) -> dict:
    """Agregado regional (razón de sumas) de los indicadores ECO, desde
    la hoja Datos_Base: misma N/D que generar_matriz_indicadores (las
    filas 'Agregado regional' del Excel llevan estas fórmulas en
    paridad; si cambia una, cambia la otra). ECO14 devuelve None porque
    su resumen regional se define mediante la mediana de países."""
    g = (base[base["pais"].isin(PAISES)]
         .groupby("anio").sum(numeric_only=True).sort_index())
    renovables = (g["gen_hidro_kwh"] + g["gen_geotermia_kwh"]
                  + g["gen_eolica_kwh"] + g["gen_solar_kwh"]
                  + g["gen_biomasa_kwh"])
    neto = g["importaciones_kwh"] - g["exportaciones_kwh"]
    series = {
        "ECO1": g["consumo_final_total_kwh"] / g["poblacion_habitantes"],
        "ECO2": g["consumo_final_total_kwh"] / g["pib_usd_const2015"],
        "ECO3": g["consumo_final_total_kwh"] / g["produccion_bruta_kwh"] * 100,
        "ECO6": g["consumo_industrial_kwh"] / g["vai_usd_const2015"],
        "ECO11": g["gen_fosil_kwh"] / g["gen_total_kwh"] * 100,
        "ECO13": renovables / g["gen_total_kwh"] * 100,
        "ECO14": None,
        "ECO15": neto / (g["produccion_bruta_kwh"] + neto) * 100,
    }
    return {cod: (None if s is None
                  else [round(float(s.loc[a]), 6) for a in ANIOS])
            for cod, s in series.items()}


def leer_series_extra() -> dict:
    """Lee las hojas de los libros ENV y SOC (mismo layout que las ECO:
    fila 1 titulo, fila 2 formula, fila 3 encabezado). Devuelve
    {clave_serie: {paises: {...}, promedio: [...], agregado: [...]}} +
    ENV6 especial. El promedio (media simple) se recalcula aquí; el
    agregado (razón de sumas) se lee de la fila 'Agregado regional' que
    escribe procesar_dimensiones.py.
    Los valores faltantes quedan como None para que JSON los serialice
    como null."""
    paquete = {}
    for ruta, claves in [(RUTA_ENV, SERIES_ENV), (RUTA_SOC, SERIES_SOC)]:
        if not ruta.exists():
            log.warning("No encontrado: %s — se omite esa dimensión "
                        "(la app se genera igual).", ruta.name)
            continue
        for clave in claves:
            hoja = pd.read_excel(ruta, sheet_name=clave, skiprows=2)
            fila_agr = hoja[hoja["País"].astype(str)
                            .str.startswith("Agregado regional")]
            hoja = hoja[hoja["País"].isin(PAISES)].set_index("País")
            hoja.columns = [int(c) for c in hoja.columns]
            por_pais = {p: [None if pd.isna(v) else round(float(v), 6)
                            for v in hoja.loc[p, ANIOS]] for p in PAISES}
            promedio = [round(float(hoja[a].mean(skipna=True)), 6)
                        for a in ANIOS]
            agregado = None
            if not fila_agr.empty:
                agregado = [None if pd.isna(v) else round(float(v), 6)
                            for v in fila_agr.iloc[0, 1:1 + len(ANIOS)]]
            paquete[clave] = {"paises": por_pais, "promedio": promedio,
                              "agregado": agregado}
    if RUTA_ENV.exists():
        e6 = pd.read_excel(RUTA_ENV, sheet_name="ENV6", skiprows=2)
        env6 = {}
        for pais in PAISES:
            filas = e6[e6["País"] == pais]
            env6[pais] = {
                "biomasa": [round(float(v), 2) for v in
                            filas[filas["Serie"] == "Inyección Biomasa"]
                            .iloc[0, 2:7]],
                "saldo": [round(float(v), 2) for v in
                          filas[filas["Serie"] == "Saldo MER"].iloc[0, 2:7]],
            }
        paquete["ENV6"] = env6
    return paquete


# ---------------------------------------------------------------------------
# Ficha de cada indicador: lo que la app muestra en pantalla.
#  - formato: como se pintan los numeros en eje/hover (sintaxis d3)
#  - sufijo:  unidad corta para el eje Y
#  - nota:    precisión metodológica que aparece bajo el título
# ---------------------------------------------------------------------------
FICHAS = {
    "ECO1": dict(
        nombre="Uso de energía per cápita",
        unidad="kWh/habitante",
        descripcion="Consumo final total dividido entre la población. "
                     "Refleja el nivel de acceso y uso efectivo de la "
                     "electricidad por persona.",
        formato=",.0f", sufijo=" kWh/hab", nota=""),
    "ECO2": dict(
        nombre="Uso de energía por unidad de PIB",
        unidad="kWh/USD const. 2015",
        descripcion="Cuánta energía consume la economía por cada dólar de "
                     "PIB real. Bajar en el tiempo sugiere desacople entre "
                     "crecimiento y consumo energético.",
        formato=".4f", sufijo="", nota=""),
    "ECO3": dict(
        nombre="Eficiencia de conversión y distribución",
        unidad="%",
        descripcion="Porcentaje de la producción bruta que llega como "
                     "consumo final. La brecha son pérdidas técnicas, "
                     "autoconsumo y saldo de intercambios.",
        formato=".1f", sufijo="%",
        nota="La razón relaciona consumo final y producción bruta; la "
             "brecha integra pérdidas, autoconsumo y saldo de intercambios."),
    "ECO6": dict(
        nombre="Intensidad energética de la industria",
        unidad="kWh/USD const. 2015",
        descripcion="Energía que necesita la industria por cada dólar de "
                     "valor agregado manufacturero. Menor = industria que "
                     "genera más valor por kWh.",
        formato=".4f", sufijo="",
        nota="El denominador es el valor agregado manufacturero "
             "(ODS 9.2.1, % del PIB × PIB real) y el numerador es el "
             "consumo industrial de electricidad reportado por OLADE."),
    "ECO11": dict(
        nombre="Fósiles en la electricidad",
        unidad="%",
        descripcion="Participación de la generación térmica fósil en la "
                     "generación total. El espejo de ECO13.",
        formato=".1f", sufijo="%", nota=""),
    "ECO13": dict(
        nombre="Renovables en la electricidad",
        unidad="%",
        descripcion="Hidro + geotermia + eólica + solar + biomasa como "
                     "porcentaje de la generación total.",
        formato=".1f", sufijo="%", nota=""),
    "ECO14": dict(
        nombre="Precio medio de la electricidad",
        unidad="USD corrientes/MWh",
        descripcion="Ingresos por energía regulada vendida entre energía "
                     "regulada consumida. En dólares corrientes de cada año.",
        formato=".1f", sufijo=" USD/MWh",
        nota_figura="Los puntos huecos identifican valores calculados vía CAGR "
                    "(2023–2024 en cinco países; 2022–2024 en El "
                    "Salvador).",
        nota="La serie se resume mediante la mediana de países, no mediante "
             "un agregado regional. La razón de sumas requiere la energía "
             "regulada vendida por país y año; 2023–2024 son totalmente "
             "imputados mediante CAGR."),
    "ECO15": dict(
        nombre="Dependencia de importaciones netas",
        unidad="%",
        descripcion="Importaciones netas sobre la oferta total. Los valores "
                     "positivos representan importación neta y los negativos, "
                     "exportación neta.",
        formato=".1f", sufijo="%",
        nota_figura="La línea punteada en 0 separa importadores "
                    "(arriba) de exportadores netos (abajo).",
        nota="En el agregado regional los intercambios dentro del MER "
             "se cancelan al sumar, por lo que la cifra del bloque mide "
             "su dependencia extrarregional y no el promedio de las "
             "dependencias nacionales."),
}

# Tipo de variación para las tarjetas resumen: 'pct' = cambio relativo (%),
# 'pp' = diferencia en puntos porcentuales (para indicadores que ya son %).
for _cod, _tipo in {"ECO1": "pct", "ECO2": "pct", "ECO3": "pp",
                    "ECO6": "pct", "ECO11": "pp", "ECO13": "pp",
                    "ECO14": "pct", "ECO15": "pp"}.items():
    FICHAS[_cod]["delta"] = _tipo

# Formula legible (para la Matriz de calculo) y modos de grafico por
# indicador: todos tienen serie temporal + barras 2020 vs 2024; los
# porcentuales admiten ademas mapa de calor (pais x anio), la vista que
# mejor condensa niveles y tendencia a la vez.
_EXTRA = {
    "ECO1":  ("Consumo final total (kWh) ÷ Población",
              ["serie", "barras"]),
    "ECO2":  ("Consumo final total (kWh) ÷ PIB real (USD constantes 2015)",
              ["serie", "barras"]),
    "ECO3":  ("(Consumo final total ÷ Producción bruta) × 100",
              ["serie", "barras", "heatmap"]),
    "ECO6":  ("Consumo industrial (kWh) ÷ Valor agregado manufacturero "
              "(USD 2015)",
              ["serie", "barras"]),
    "ECO11": ("(Generación térmica fósil ÷ Generación total) × 100",
              ["serie", "barras", "heatmap"]),
    "ECO13": ("(Hidro + Geotermia + Eólica + Solar + Biomasa) ÷ "
              "Generación total × 100",
              ["serie", "barras", "heatmap"]),
    "ECO14": ("Ingresos por energía regulada (USD) ÷ Energía regulada (MWh)",
              ["serie", "barras"]),
    "ECO15": ("(Importaciones − Exportaciones) ÷ (Producción bruta + "
              "Importaciones − Exportaciones) × 100",
              ["serie", "heatmap", "barras"]),
}
for _cod, (_formula, _modos) in _EXTRA.items():
    FICHAS[_cod]["formula"] = _formula
    FICHAS[_cod]["modos"] = _modos

# Dimension a la que pertenece cada indicador (agrupa el menu lateral).
for _cod in FICHAS:
    FICHAS[_cod]["dim"] = "eco"

# --- Fichas de las dimensiones ambiental y social ---------------------
# Los indicadores con varias salidas usan "series": lista de
# [clave_datos, etiqueta, formato, sufijo_eje, unidad, formula]; la app
# muestra un selector cuando hay mas de una.
FICHAS["ENV1"] = dict(
    nombre="Emisiones de GEI del sector eléctrico",
    unidad="", formato=".4f", sufijo="", formula="", delta="pct",
    modos=["serie", "barras"], dim="env",
    descripcion="Emisiones de gases de efecto invernadero (GEI) por la "
                "producción y uso de energía, per cápita y por unidad de "
                "PIB. Cubre las emisiones de las centrales eléctricas.",
    nota="",
    series=[
        ["ENV1_PC", "Per cápita", ".4f", " t/hab", "t CO₂eq/habitante",
         "Emisiones GEI de centrales eléctricas ÷ Población"],
        ["ENV1_PIB", "Por unidad de PIB", ".4f", " kg/USD",
         "kg CO₂eq/USD constantes 2015",
         "Emisiones GEI (kg) ÷ PIB real (USD constantes 2015)"],
    ])
FICHAS["ENV2"] = dict(
    nombre="Contaminantes atmosféricos urbanos",
    unidad="", formato=".4f", sufijo="", formula="", delta="pct",
    modos=["serie", "barras"], dim="env",
    descripcion="Concentraciones ambientales de contaminantes "
                "atmosféricos en zonas urbanas: SO₂ y partículas emitidas "
                "por las centrales eléctricas, per cápita y por unidad de "
                "PIB.",
    nota="",
    series=[
        ["ENV2_SO2_PC", "SO₂ per cápita", ".3f", " kg/hab", "kg/habitante",
         "Emisiones SO₂ de centrales eléctricas ÷ Población"],
        ["ENV2_PAR_PC", "Partículas per cápita", ".4f", " kg/hab",
         "kg/habitante", "Emisiones de partículas ÷ Población"],
        ["ENV2_SO2_PIB", "SO₂ por PIB", ".4f", " g/USD",
         "g/USD constantes 2015", "Emisiones SO₂ (g) ÷ PIB real"],
        ["ENV2_PAR_PIB", "Partículas por PIB", ".5f", " g/USD",
         "g/USD constantes 2015", "Emisiones de partículas (g) ÷ PIB real"],
    ])
FICHAS["ENV3"] = dict(
    nombre="Emisiones atmosféricas del sistema",
    unidad="", formato=".3f", sufijo="", formula="", delta="pct",
    modos=["serie", "barras", "heatmap"], dim="env",
    descripcion="Emisiones de contaminantes atmosféricos procedentes de "
                "los sistemas energéticos, en escala eléctrica: gramos "
                "emitidos por cada kWh de producción bruta.",
    nota="",
    series=[
        ["ENV3", "Escala eléctrica", ".3f", " g/kWh", "g/kWh",
         "(SO₂ + NOx + CO + Partículas) ÷ Producción bruta"],
    ])
FICHAS["ENV6"] = dict(
    nombre="Biomasa vs Saldo MER",
    unidad="GWh", formato=",.0f", sufijo=" GWh", formula="", delta="pct",
    modos=[], dim="env", tipo="env6",
    descripcion="Comparativo de inyección de biomasa vs saldo neto en el "
                "Mercado Eléctrico Regional, por país. Saldo negativo = "
                "importador neto en el MER ese año.",
    nota="Comparativo de dos series expresadas en GWh; no calcula un "
         "cociente entre ellas.")
FICHAS["SOC1"] = dict(
    nombre="Población sin electricidad",
    unidad="", formato=".2f", sufijo="%", formula="", delta="pp",
    modos=["serie", "barras", "heatmap"], dim="soc",
    descripcion="Porcentaje de hogares (o de población) sin electricidad "
                "o energía comercial, o muy dependientes de energías no "
                "comerciales.",
    nota="El agregado regional pondera cada país por su población "
         "(razón de sumas), equivalente a personas sin electricidad del "
         "bloque ÷ población del bloque.",
    series=[
        ["SOC1", "", ".2f", "%", "%", "100 − Tasa de electrificación total"],
    ])
FICHAS["SOC2"] = dict(
    nombre="Ingreso destinado a electricidad",
    unidad="", formato=".2f", sufijo="%", formula="", delta="pp",
    modos=["serie", "barras", "heatmap"], dim="soc",
    descripcion="Porcentaje del ingreso anual de referencia del hogar "
                "destinado a electricidad, para el hogar promedio y el "
                "estrato vulnerable.",
    nota="El agregado regional es una razón de sumas construida en USD. "
         "SOC2_PROM expande por clientes residenciales; "
         "SOC2_VULNERABLE usa clientes vulnerables proxy (20 % en cinco "
         "países y 29.6 % en Nicaragua). Cliente residencial se usa como "
         "aproximación de unidad residencial consumidora conectada.",
    series=[
        ["SOC2_PROM", "Hogar promedio", ".2f", "%", "%",
         "Cargo anual medio residencial ÷ ingreso anual PROM × 100"],
        ["SOC2_VULNERABLE", "Estrato vulnerable", ".2f", "%", "%",
         "Cargo anual medio residencial ÷ ingreso anual vulnerable × 100"],
    ])
FICHAS["SOC3"] = dict(
    nombre="Hogares con acceso a energía renovable",
    unidad="", formato=".1f", sufijo="%", formula="", delta="pp",
    modos=["serie", "barras", "heatmap"], dim="soc",
    descripcion="Uso de energía en los hogares por grupo (rural/urbano) y "
                "combinación de combustibles: hogares con acceso "
                "eléctrico ponderado por la participación renovable de la "
                "generación.",
    nota="Cada serie combina la tasa de electrificación de la zona con la "
         "participación renovable de la generación nacional. El agregado "
         "rural pondera por población rural y el urbano por población "
         "urbana.",
    series=[
        ["SOC3_RURAL", "Rural", ".1f", "%", "%",
         "Tasa de electrificación rural × % renovable de la generación"],
        ["SOC3_URB", "Urbano", ".1f", "%", "%",
         "Tasa de electrificación urbana × % renovable de la generación"],
    ])

# Lectura sintética tomada de la sección de resultados de la tesis. Se
# conserva como metadato canónico para que el HTML sea siempre regenerable y
# no acumule interpretaciones editadas a mano.
HALLAZGOS_REGIONALES = {
    "ECO1": (
        "El consumo eléctrico por habitante del bloque aumentó 10,9 % entre "
        "2020 y 2024, mientras disminuyó la heterogeneidad relativa entre "
        "países."
    ),
    "ECO2": (
        "La intensidad eléctrica regional disminuyó 8,3 % entre 2020 y "
        "2024, aunque las diferencias relativas entre las economías "
        "nacionales se ampliaron."
    ),
    "ECO3": (
        "La razón regional de conversión y distribución permaneció "
        "prácticamente estable, de 82,4 % a 82,6 %, sin una mejora "
        "sustantiva del nivel del bloque."
    ),
    "ECO6": (
        "La intensidad eléctrica industrial del bloque aumentó 34,4 % "
        "entre 2020 y 2024, en contraste con la reducción observada en la "
        "intensidad de la economía total."
    ),
    "ECO11": (
        "La participación fósil en la generación regional aumentó de "
        "25,0 % a 33,0 % entre 2020 y 2024 y las diferencias relativas "
        "entre países se redujeron."
    ),
    "ECO13": (
        "La participación renovable del bloque disminuyó de 75,0 % a "
        "67,0 % entre 2020 y 2024, lo que describe un cambio de composición "
        "y no necesariamente una caída del volumen renovable."
    ),
    "ECO14": (
        "En el tramo con mayor respaldo observacional, la mediana de países "
        "subió de 178,3 a 188,7 USD/MWh entre 2020 y 2022; los valores de "
        "2023–2024 son extrapolaciones."
    ),
    "ECO15": (
        "La dependencia neta extrarregional aumentó de 1,7 % a 2,2 %, pero "
        "se mantuvo reducida frente a la oferta eléctrica total del bloque."
    ),
    "SOC1": (
        "La población sin acceso a electricidad descendió hasta 6,72 % en "
        "2024, aunque todavía representó aproximadamente 3,5 millones de "
        "personas en el SIEPAC."
    ),
    "SOC2": (
        "La carga del hogar promedio permaneció cerca del 2 %, mientras la "
        "del estrato vulnerable siguió siendo más de seis veces mayor, con "
        "una amplia brecha de asequibilidad."
    ),
    "SOC3": (
        "El acceso urbano a electricidad de origen renovable permaneció por "
        "encima del rural, pero ambos agregados se contrajeron con fuerza "
        "entre 2022 y 2024."
    ),
    "ENV1": (
        "Las emisiones regionales de GEI disminuyeron hasta 2022 y luego "
        "repuntaron, cerrando 2024 por encima de los niveles de 2020 tanto "
        "por habitante como por unidad de PIB."
    ),
    "ENV2": (
        "Los contaminantes atmosféricos regionales descendieron al inicio "
        "de la ventana y aumentaron en 2023–2024, con una heterogeneidad "
        "nacional todavía elevada."
    ),
    "ENV3": (
        "La intensidad regional de emisiones atmosféricas cayó hasta 2022 y "
        "repuntó a 1,728 g/kWh en 2024, por encima del nivel de 2020."
    ),
    "ENV6": (
        "La biomasa sostuvo un aporte superior a 3.000 GWh durante la mayor "
        "parte del período, mientras el saldo agregado del MER permaneció "
        "cerca de cero por la compensación intrarregional."
    ),
}
for _cod, _hallazgo in HALLAZGOS_REGIONALES.items():
    FICHAS[_cod]["hallazgo_regional"] = _hallazgo

# `nota_figura` describe convenciones visuales del gráfico; `nota` contiene
# información metodológica común a todos los formatos. Las tablas APA usan
# únicamente `nota` y los visualizadores presentan ambas.
for _cod in FICHAS:
    FICHAS[_cod].setdefault("nota_figura", "")


def construir_datos_json(df, base_df, extra) -> str:
    """Empaqueta los datos como JSON para incrustar en el HTML.

    Estructura: {ECO1: {paises: {Nicaragua: [v2020..v2024], ...},
                        promedio: [...], agregado: [...] | null},  ...,
                 imputados: {Nicaragua: [false,false,false,true,true], ...}}

    promedio = media simple de los seis países ("el país típico");
    agregado = razón de sumas Σ N/Σ D ("el bloque como sistema"), null
    cuando la ficha define un estadístico de los valores nacionales.
    """
    agregados = agregados_eco(base_df)
    paquete = {}
    for codigo in [c for c, f in FICHAS.items() if f["dim"] == "eco"]:
        por_pais = {}
        for pais in PAISES:
            serie = (df[df["pais"] == pais].sort_values("anio")[codigo]
                     .round(6).tolist())
            por_pais[pais] = serie
        promedio = (df.groupby("anio")[codigo].mean().sort_index()
                    .round(6).tolist())
        paquete[codigo] = {"paises": por_pais, "promedio": promedio,
                           "agregado": agregados.get(codigo)}

    paquete["imputados"] = {
        pais: df[df["pais"] == pais].sort_values("anio")["tarifa_imputada"]
              .tolist()
        for pais in PAISES
    }

    # El visualizador publica únicamente las series que realmente consume;
    # las matrices base permanecen en los libros procesados y tablas APA.
    paquete.update(extra)   # series ENV/SOC + ENV6 (si existen)
    return json.dumps(paquete, ensure_ascii=False)
