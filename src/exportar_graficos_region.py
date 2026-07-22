"""
exportar_graficos_region.py — Gráficos del SIEPAC como conjunto (monografía)
====================================================
Etapa del pipeline : visualización (posterior a generar_resumen_indicadores.py)
Entradas           : data/processed/indicadores_consolidados_tidy.csv,
                     matriz_consolidada_wide.csv y el Datos_Base del libro ENV
Salidas            : graficos/region/*.png (una figura por análisis regional),
                     graficos/region/tabla_agregados.csv y
                     graficos/region/LEYENDAS.md (pies de figura listos
                     para pegar en el documento)
Alimenta           : — (figuras estáticas del capítulo de análisis regional)
Fuente de datos    : salidas del pipeline

Uso:  python src/exportar_graficos_region.py   (ejecutar desde la raíz)

Exporta la estadística del BLOQUE como sistema, en PNG listos para el
documento de tesis (3000x1860 px, fondo blanco):

  1. Una figura por serie con agregado regional (15): la razón de sumas
     (foco, azul) contrastada con el promedio de países (gris punteado).
  2. Magnitudes absolutas del bloque: consumo final, generación por
     fuente (small multiples con ejes espejados), composición
     renovable/fósil, intercambios con el exterior, personas sin
     electricidad y emisiones GEI.

Decisiones de estética (coherentes con version-alt/DECISIONES_VISUALIZACION.md):
  - Un solo acento cromático: el azul #1F4E79 de la referencia regional.
  - El promedio de países acompaña en gris discontinuo (comparación
    honesta entre las dos medidas; ambas quedan etiquetadas).
  - Composición renovable/fósil con el par azul/pardo de la escala
    divergente del proyecto (distinguible bajo daltonismo; los
    segmentos llevan separador blanco y etiqueta directa).
  - Un solo eje por figura; nada de dobles escalas.

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import logging
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

from config_siepac import RAIZ_PROYECTO, DIR_PROCESSED, ANIOS_ANALISIS as ANIOS
from viz_comun import FICHAS, PAISES

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

DIR_SALIDA = RAIZ_PROYECTO / "graficos" / "region"
RUTA_TIDY = DIR_PROCESSED / "indicadores_consolidados_tidy.csv"
RUTA_WIDE = DIR_PROCESSED / "matriz_consolidada_wide.csv"
RUTA_ENV = DIR_PROCESSED / "indicadores_ENV_SIEPAC.xlsx"

# Lienzo lógico y escala: 3000x1860 px finales, igual que los otros
# exportadores del proyecto (nítido a ~16 cm de ancho en el documento).
ANCHO, ALTO, ESCALA = 1000, 620, 3

# ------------------------- paleta (sobria, de version-alt) ---------------
AZUL = "#1F4E79"      # referencia regional (contraste 8.66:1 s/ blanco)
PARDO = "#8C7355"     # polo cálido de la escala divergente (4.47:1)
GRIS_LINEA = "#8A8A8A"    # promedio de países (3.45:1, marca no textual)
GRIS_OSCURO = "#4A4A4A"   # saldo neto / texto secundario (8.86:1)
GRIS_GRILLA = "#EBEBEB"
TINTA = "#1A1A1A"

FUENTE = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"


def _layout(titulo: str, subtitulo: str, sufijo: str = "",
            formato: str = "", **extra) -> go.Layout:
    """Layout base: fondo blanco, grilla recesiva, título + subtítulo."""
    base = dict(
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font=dict(family=FUENTE, size=15, color=TINTA),
        title=dict(
            text=f"<b>{titulo}</b><br><sup style='color:#5B5B5B'>"
                 f"{subtitulo}</sup>",
            x=0.02, xanchor="left", font=dict(size=21)),
        legend=dict(orientation="h", y=-0.14, x=0.5, xanchor="center"),
        margin=dict(l=70, r=110, t=86, b=76),
        xaxis=dict(tickvals=ANIOS, gridcolor="#F5F5F5", automargin=True),
        yaxis=dict(gridcolor=GRIS_GRILLA, ticksuffix=sufijo,
                   tickformat=formato, rangemode="tozero",
                   automargin=True, zerolinecolor=GRIS_GRILLA),
    )
    base.update(extra)
    return go.Layout(base)


def _exportar(fig: go.Figure, nombre: str) -> None:
    ruta = DIR_SALIDA / f"{nombre}.png"
    pio.write_image(fig, ruta, width=ANCHO, height=ALTO, scale=ESCALA)
    log.info("  OK  region/%s.png", nombre)


def _etiqueta_final(fig, y, texto, color) -> None:
    """Etiqueta directa junto al último punto de una línea (2024)."""
    fig.add_annotation(x=ANIOS[-1], y=y, text=f"<b>{texto}</b>",
                       xanchor="left", xshift=8, showarrow=False,
                       font=dict(size=14, color=color))


# ---------------------------------------------------------------------------
# CATÁLOGO DE SERIES (nombre, unidad y formato desde viz_comun.FICHAS)
# ---------------------------------------------------------------------------

def _catalogo_series() -> dict[str, dict]:
    """{clave_serie: {nombre, unidad, formato, delta}} para las series
    con agregado regional, en el orden de FICHAS."""
    cat = {}
    for cod, f in FICHAS.items():
        if f.get("tipo") == "env6":
            continue
        if f.get("series"):
            for s in f["series"]:
                nombre = f["nombre"] + (f" — {s[1]}" if s[1] else "")
                cat[s[0]] = dict(nombre=nombre, unidad=s[4],
                                 formato=s[2], sufijo=s[3],
                                 delta=f["delta"])
        else:
            cat[cod] = dict(nombre=f["nombre"], unidad=f["unidad"],
                            formato=f["formato"], sufijo=f["sufijo"],
                            delta=f["delta"])
    return cat


def _fmt(v: float, formato: str) -> str:
    dec = int(formato[1]) if len(formato) > 2 and formato[0] == "." else 1
    return f"{v:,.{dec}f}"


def _delta_txt(v0: float, v4: float, tipo: str) -> str:
    if tipo == "pp":
        return f"{v4 - v0:+.1f} pp"
    return f"{(v4 / v0 - 1) * 100:+.1f} %"


# ---------------------------------------------------------------------------
# 1. AGREGADO vs PROMEDIO, POR SERIE
# ---------------------------------------------------------------------------

def figuras_series(tidy: pd.DataFrame, cat: dict) -> list[tuple]:
    """Una figura por serie con agregado. Devuelve filas de leyenda."""
    leyendas = []
    resumen = tidy[tidy["pais"].isin(["Promedio regional",
                                      "Agregado regional"])]
    for clave, info in cat.items():
        sub = resumen[resumen["serie"] == clave]
        agr = (sub[sub["pais"] == "Agregado regional"]
               .set_index("anio")["valor"].reindex(ANIOS))
        if agr.isna().all():
            continue          # ECO14 / SOC2 / SOC3: sin agregado
        prom = (sub[sub["pais"] == "Promedio regional"]
                .set_index("anio")["valor"].reindex(ANIOS))

        fig = go.Figure()
        fig.add_scatter(x=ANIOS, y=prom, name="Promedio de países "
                        "(media simple)", mode="lines+markers",
                        line=dict(color=GRIS_LINEA, width=2, dash="dash"),
                        marker=dict(size=7, color=GRIS_LINEA))
        fig.add_scatter(x=ANIOS, y=agr, name="Agregado regional "
                        "(razón de sumas)", mode="lines+markers",
                        line=dict(color=AZUL, width=3.4),
                        marker=dict(size=9, color=AZUL))
        _etiqueta_final(fig, agr.iloc[-1],
                        _fmt(agr.iloc[-1], info["formato"]), AZUL)
        _etiqueta_final(fig, prom.iloc[-1],
                        _fmt(prom.iloc[-1], info["formato"]), GRIS_LINEA)

        extra = {}
        if clave == "ECO15":   # puede acercarse a 0: no anclar el eje
            extra = dict(yaxis=dict(gridcolor=GRIS_GRILLA,
                         ticksuffix=info["sufijo"], rangemode="normal",
                         automargin=True, zerolinecolor=GRIS_LINEA))
        fig.update_layout(_layout(
            f"{clave} · {info['nombre']}",
            f"SIEPAC 2020–2024 · {info['unidad']} · el agregado pondera "
            "cada país por su denominador",
            sufijo=info["sufijo"], **extra))
        _exportar(fig, f"{clave}_agregado_vs_promedio")

        leyendas.append((
            f"{clave}_agregado_vs_promedio.png",
            f"{clave} — {info['nombre']} a nivel del bloque SIEPAC, "
            f"2020–2024. Agregado regional (razón de sumas): "
            f"{_fmt(agr.iloc[0], info['formato'])} → "
            f"{_fmt(agr.iloc[-1], info['formato'])} {info['unidad']} "
            f"({_delta_txt(agr.iloc[0], agr.iloc[-1], info['delta'])}); "
            f"promedio de países (media simple): "
            f"{_fmt(prom.iloc[0], info['formato'])} → "
            f"{_fmt(prom.iloc[-1], info['formato'])} "
            f"({_delta_txt(prom.iloc[0], prom.iloc[-1], info['delta'])}). "
            "Elaboración propia con datos de SIELAC-OLADE, CEPALSTAT y "
            "Banco Mundial."))
    return leyendas


# ---------------------------------------------------------------------------
# 2. MAGNITUDES ABSOLUTAS DEL BLOQUE
# ---------------------------------------------------------------------------

FUENTES_GEN = [  # (columna, nombre)
    ("gen_hidro_kwh", "Hidroeléctrica"),
    ("gen_geotermia_kwh", "Geotérmica"),
    ("gen_eolica_kwh", "Eólica"),
    ("gen_solar_kwh", "Solar"),
    ("gen_biomasa_kwh", "Biomasa"),
    ("gen_fosil_kwh", "Térmica fósil"),
]


def figuras_bloque(wide: pd.DataFrame) -> list[tuple]:
    leyendas = []
    g = (wide[wide["pais"].isin(PAISES)]
         .groupby("anio").sum(numeric_only=True).reindex(ANIOS))

    # --- consumo final total (TWh) ------------------------------------
    consumo = g["consumo_final_total_kwh"] / 1e9
    fig = go.Figure(go.Scatter(
        x=ANIOS, y=consumo, mode="lines+markers+text",
        text=[f"{v:.1f}" for v in consumo], textposition="top center",
        textfont=dict(size=13, color=AZUL),
        line=dict(color=AZUL, width=3.4), marker=dict(size=9, color=AZUL)))
    fig.update_layout(_layout(
        "Consumo final de electricidad del bloque SIEPAC",
        "Suma de los seis países · TWh", sufijo=" TWh",
        showlegend=False))
    _exportar(fig, "REGION_consumo_final")
    leyendas.append(("REGION_consumo_final.png",
        f"Consumo final de electricidad del bloque SIEPAC, 2020–2024: "
        f"{consumo.iloc[0]:.1f} → {consumo.iloc[-1]:.1f} TWh "
        f"({(consumo.iloc[-1]/consumo.iloc[0]-1)*100:+.1f} %). "
        "Elaboración propia con datos de SIELAC-OLADE."))

    # --- generación por fuente: small multiples 2x3, ejes espejados ---
    fig = make_subplots(rows=2, cols=3, shared_yaxes=False,
                        subplot_titles=[n for _, n in FUENTES_GEN],
                        vertical_spacing=0.22, horizontal_spacing=0.07)
    tope = max(g[c].max() for c, _ in FUENTES_GEN) / 1e9 * 1.08
    for i, (col, nombre) in enumerate(FUENTES_GEN):
        serie = g[col] / 1e9
        fig.add_scatter(x=ANIOS, y=serie, mode="lines+markers",
                        line=dict(color=AZUL, width=2.6),
                        marker=dict(size=6, color=AZUL),
                        showlegend=False,
                        row=i // 3 + 1, col=i % 3 + 1)
    fig.update_layout(_layout(
        "Generación eléctrica del bloque SIEPAC por fuente",
        "Suma de los seis países · TWh · mismo eje en los seis paneles",
        showlegend=False, margin=dict(l=70, r=40, t=110, b=60)))
    fig.update_annotations(font=dict(size=14))
    # Mismo rango Y en los seis paneles: la comparación de magnitudes
    # entre fuentes es el mensaje (la "planitud" de solar es el dato).
    # DESPUÉS de update_layout, para que el eje del panel 1 no pierda
    # el sufijo al ser pisado por el yaxis del layout base.
    fig.update_yaxes(range=[0, tope], gridcolor=GRIS_GRILLA,
                     ticksuffix=" TWh", tickformat="", rangemode="tozero",
                     tickfont=dict(size=11))
    fig.update_xaxes(tickvals=[2020, 2022, 2024], gridcolor="#F5F5F5",
                     tickfont=dict(size=11))
    _exportar(fig, "REGION_generacion_fuentes")
    leyendas.append(("REGION_generacion_fuentes.png",
        "Generación eléctrica del bloque SIEPAC por fuente, 2020–2024 "
        "(TWh; los seis paneles comparten escala para comparar "
        "magnitudes). Elaboración propia con datos de SIELAC-OLADE."))

    # --- composición renovable vs fósil (barras apiladas, 2 colores) --
    renov = (g[[c for c, _ in FUENTES_GEN[:-1]]].sum(axis=1)) / 1e9
    fosil = g["gen_fosil_kwh"] / 1e9
    pct = renov / (renov + fosil) * 100
    fig = go.Figure([
        go.Bar(x=ANIOS, y=renov, name="Renovable",
               marker=dict(color=AZUL, line=dict(color="#FFFFFF", width=2)),
               text=[f"{p:.1f}%" for p in pct], textposition="inside",
               insidetextanchor="middle",
               textfont=dict(size=13, color="#FFFFFF")),
        go.Bar(x=ANIOS, y=fosil, name="Térmica fósil",
               marker=dict(color=PARDO, line=dict(color="#FFFFFF", width=2))),
    ])
    fig.update_layout(_layout(
        "Composición de la generación del bloque SIEPAC",
        "Suma de los seis países · TWh · la etiqueta es el % renovable "
        "del bloque (ECO13 agregado)", sufijo=" TWh",
        barmode="stack", hovermode="closest",
        # La leyenda en el mismo orden visual del apilado
        # (Renovable abajo primero, fósil encima).
        legend=dict(orientation="h", y=-0.14, x=0.5, xanchor="center",
                    traceorder="normal")))
    _exportar(fig, "REGION_renovable_vs_fosil")
    leyendas.append(("REGION_renovable_vs_fosil.png",
        f"Composición renovable/fósil de la generación del bloque "
        f"SIEPAC, 2020–2024. La participación renovable del bloque pasó "
        f"de {pct.iloc[0]:.1f} % a {pct.iloc[-1]:.1f} % "
        f"({pct.iloc[-1]-pct.iloc[0]:+.1f} pp). Elaboración propia con "
        "datos de SIELAC-OLADE."))

    # --- intercambios con el exterior ---------------------------------
    imp = g["importaciones_kwh"] / 1e9
    exp = g["exportaciones_kwh"] / 1e9
    neto = imp - exp
    fig = go.Figure([
        go.Bar(x=ANIOS, y=imp, name="Importaciones (Σ 6 países)",
               marker=dict(color=AZUL)),
        go.Bar(x=ANIOS, y=exp, name="Exportaciones (Σ 6 países)",
               marker=dict(color=PARDO)),
        go.Scatter(x=ANIOS, y=neto, name="Saldo neto del bloque",
                   mode="lines+markers",
                   line=dict(color=GRIS_OSCURO, width=3),
                   marker=dict(size=8, color=GRIS_OSCURO)),
    ])
    # Etiqueta directa solo en el último punto, fuera de las barras
    # (las cifras año a año quedan en la leyenda de figura y el CSV).
    fig.add_annotation(x=ANIOS[-1], y=neto.iloc[-1],
                       text=f"<b>{neto.iloc[-1]:+.2f} TWh</b>",
                       xanchor="left", xshift=10, showarrow=False,
                       font=dict(size=14, color=GRIS_OSCURO))
    fig.update_layout(_layout(
        "Intercambios de electricidad del bloque SIEPAC",
        "TWh · al sumar los seis países lo intra-MER se cancela: el "
        "saldo neto es el intercambio extrarregional",
        sufijo=" TWh", barmode="group", hovermode="closest"))
    _exportar(fig, "REGION_intercambios")
    leyendas.append(("REGION_intercambios.png",
        f"Intercambios de electricidad del bloque SIEPAC, 2020–2024 "
        f"(TWh). Los flujos internos al MER se cancelan en la suma: el "
        f"saldo neto ({neto.iloc[0]:+.2f} → {neto.iloc[-1]:+.2f} TWh) "
        "corresponde al intercambio extrarregional del bloque. "
        "Elaboración propia con datos de SIELAC-OLADE."))

    return leyendas


def figura_soc1(tidy: pd.DataFrame, wide: pd.DataFrame) -> list[tuple]:
    """Personas sin electricidad en el bloque (numerador de SOC1)."""
    pob = (wide[wide["pais"].isin(PAISES)]
           .pivot(index="pais", columns="anio",
                  values="poblacion_habitantes").reindex(columns=ANIOS))
    soc1 = (tidy[(tidy["serie"] == "SOC1") & tidy["pais"].isin(PAISES)]
            .pivot(index="pais", columns="anio", values="valor")
            .reindex(columns=ANIOS))
    personas = (soc1 * pob / 100).sum() / 1e6      # millones
    fig = go.Figure(go.Bar(
        x=ANIOS, y=personas, marker=dict(color=AZUL),
        text=[f"{v:.2f} M" for v in personas], textposition="outside",
        textfont=dict(size=14, color=AZUL)))
    fig.update_layout(_layout(
        "Personas sin electricidad en el bloque SIEPAC",
        "Millones de personas · numerador del SOC1 agregado "
        "(% del bloque × población)", sufijo=" M",
        showlegend=False, hovermode="closest"))
    _exportar(fig, "REGION_personas_sin_electricidad")
    return [("REGION_personas_sin_electricidad.png",
        f"Personas sin acceso a electricidad en el bloque SIEPAC, "
        f"2020–2024: {personas.iloc[0]:.2f} → {personas.iloc[-1]:.2f} "
        f"millones. Equivale al SOC1 agregado ({(personas.iloc[-1]*1e6/pob[2024].sum()*100):.2f} % "
        "del bloque en 2024). Elaboración propia con datos del equipo "
        "de tesis y CEPAL-CELADE.")]


def figura_emisiones() -> list[tuple]:
    """Emisiones GEI del sector eléctrico del bloque (Mt CO2eq)."""
    base = pd.read_excel(RUTA_ENV, sheet_name="Datos_Base", skiprows=2)
    g = (base[base["pais"].isin(PAISES)]
         .groupby("anio")["emisiones_gei_10e3t"].sum().reindex(ANIOS))
    mt = g / 1e3      # 10^3 t -> Mt
    fig = go.Figure(go.Scatter(
        x=ANIOS, y=mt, mode="lines+markers+text",
        text=[f"{v:.1f}" for v in mt], textposition="top center",
        textfont=dict(size=13, color=AZUL),
        line=dict(color=AZUL, width=3.4), marker=dict(size=9, color=AZUL)))
    fig.update_layout(_layout(
        "Emisiones GEI del sector eléctrico del bloque SIEPAC",
        "Suma de los seis países · Mt CO₂eq", sufijo=" Mt",
        showlegend=False))
    _exportar(fig, "REGION_emisiones_gei")
    return [("REGION_emisiones_gei.png",
        f"Emisiones de GEI del sector eléctrico del bloque SIEPAC, "
        f"2020–2024: {mt.iloc[0]:.1f} → {mt.iloc[-1]:.1f} Mt CO₂eq "
        f"({(mt.iloc[-1]/mt.iloc[0]-1)*100:+.1f} %). Elaboración propia "
        "con datos del equipo de tesis (dimensión ambiental).")]


# ---------------------------------------------------------------------------
# 3. TABLA MÁQUINA + LEYENDAS
# ---------------------------------------------------------------------------

def exportar_tabla(tidy: pd.DataFrame, cat: dict) -> None:
    """CSV serie x año con ambas medidas y sus variaciones 2020→2024."""
    filas = []
    resumen = tidy[tidy["pais"].isin(["Promedio regional",
                                      "Agregado regional"])]
    for clave, info in cat.items():
        for medida, etiq in [("Promedio regional", "promedio_paises"),
                             ("Agregado regional", "agregado_razon_sumas")]:
            s = (resumen[(resumen["serie"] == clave)
                         & (resumen["pais"] == medida)]
                 .set_index("anio")["valor"].reindex(ANIOS))
            if s.isna().all():
                continue
            filas.append([clave, info["nombre"], info["unidad"], etiq,
                          *[round(v, 6) for v in s],
                          _delta_txt(s.iloc[0], s.iloc[-1], info["delta"])])
    df = pd.DataFrame(filas, columns=["serie", "nombre", "unidad",
                                      "medida", *ANIOS, "delta_2020_2024"])
    ruta = DIR_SALIDA / "tabla_agregados.csv"
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    log.info("  OK  region/tabla_agregados.csv (%d filas)", len(df))


def exportar_leyendas(leyendas: list[tuple]) -> None:
    md = ["# Pies de figura — análisis regional del SIEPAC",
          "",
          "Leyendas sugeridas para pegar bajo cada figura de "
          "`graficos/region/` en la monografía (numera las figuras según "
          "el orden final del documento). Todas las cifras salen del "
          "pipeline (`tabla_agregados.csv` en esta misma carpeta).",
          "",
          "**Nota metodológica común**: \"agregado regional\" = razón de "
          "sumas Σ numerador / Σ denominador de los seis países (el "
          "bloque como sistema); \"promedio de países\" = media simple "
          "(el país típico). Ver docs/resumen_indicadores_SIEPAC.md.",
          ""]
    for archivo, texto in leyendas:
        md.append(f"## {archivo}")
        md.append("")
        md.append(f"> **Figura N.** {texto}")
        md.append("")
    ruta = DIR_SALIDA / "LEYENDAS.md"
    ruta.write_text("\n".join(md), encoding="utf-8")
    log.info("  OK  region/LEYENDAS.md (%d figuras)", len(leyendas))


def main() -> None:
    DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    tidy = pd.read_csv(RUTA_TIDY)
    wide = pd.read_csv(RUTA_WIDE)
    cat = _catalogo_series()

    log.info("Exportando figuras regionales a graficos/region/ ...")
    leyendas = figuras_series(tidy, cat)
    leyendas += figuras_bloque(wide)
    leyendas += figura_soc1(tidy, wide)
    leyendas += figura_emisiones()
    exportar_tabla(tidy, cat)
    exportar_leyendas(leyendas)
    log.info("Listo: %d figuras + tabla + leyendas en graficos/region/",
             len(leyendas))


if __name__ == "__main__":
    main()
