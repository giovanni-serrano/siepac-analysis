"""
generar_resumen_indicadores.py — Matriz consolidada de indicadores + fichas
====================================================
Etapa del pipeline : consolidación de resultados (posterior a
                     generar_matriz_indicadores.py y procesar_dimensiones.py)
Entradas           : data/processed/indicadores_ECO_valores.csv,
                     indicadores_ECO_SIEPAC.xlsx y, si existen, los libros
                     ENV/SOC (todo vía viz_comun.cargar_datos/leer_series_extra)
Salidas            : docs/resumen_indicadores_SIEPAC.md (fichas + tablas,
                     legible por humanos y por asistentes de IA) y
                     data/processed/indicadores_consolidados_tidy.csv
                     (una fila por serie-país-año, formato máquina)
Alimenta           : — (insumo para el análisis cualitativo de la tesis)
Fuente de datos    : salidas del pipeline

Uso:  python src/generar_resumen_indicadores.py   (ejecutar desde la raíz)

Consolida en un solo documento los indicadores calculados de las tres
dimensiones (ECO, ENV, SOC) junto con la ficha de cada uno (nombre,
unidad, fórmula, descripción y notas metodológicas), tomándolo todo de
viz_comun.py — la misma fuente única que alimenta los visualizadores —
para que no exista riesgo de divergencia entre productos.

Notas metodológicas:
  - Las dimensiones cuyos libros no existan se omiten con aviso (igual
    que en los visualizadores).
  - En ECO14 los valores imputados vía CAGR se marcan con * en el MD y
    con fuente_dato = "imputado_CAGR" en el CSV.

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import csv
import logging
import math
import sys
from datetime import date
from pathlib import Path

from config_siepac import RAIZ_PROYECTO, DIR_PROCESSED
from viz_comun import (ANIOS, FICHAS, PAISES, agregados_eco,
                       cargar_datos, leer_series_extra, preparar_datos)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

RUTA_MD = RAIZ_PROYECTO / "docs" / "resumen_indicadores_SIEPAC.md"
RUTA_CSV = DIR_PROCESSED / "indicadores_consolidados_tidy.csv"

NOMBRE_DIM = {"eco": "Dimensión económica", "env": "Dimensión ambiental",
              "soc": "Dimensión social"}


def _fmt(v, formato: str) -> str:
    """Formatea un valor con el formato d3 de la ficha (compatible con
    format() de Python: ',.0f', '.1f', etc.). None/NaN -> 's.d.'."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "s.d."
    return format(v, formato)


def _delta(v0, v4, tipo: str) -> str:
    """Variación 2020→2024: relativa (%) o en puntos porcentuales (pp),
    según el tipo declarado en la ficha."""
    es_nan = lambda v: isinstance(v, float) and math.isnan(v)
    if v0 is None or v4 is None or es_nan(v0) or es_nan(v4) or not v0:
        return "s.d."
    if tipo == "pp":
        return f"{v4 - v0:+.1f} pp"
    return f"{(v4 / v0 - 1) * 100:+.1f} %"


def _series_de(ficha: dict, codigo: str) -> list[dict]:
    """Lista de sub-series de una ficha con el mismo esquema que usan
    los visualizadores: clave de datos, etiqueta, formato, unidad y
    fórmula. Las fichas ECO no tienen 'series' (una sola salida)."""
    if not ficha.get("series"):
        return [dict(clave=codigo, etiqueta="", formato=ficha["formato"],
                     unidad=ficha["unidad"], formula=ficha["formula"])]
    return [dict(clave=s[0], etiqueta=s[1], formato=s[2], unidad=s[4],
                 formula=s[5]) for s in ficha["series"]]


def _armar_datos() -> tuple[dict, dict]:
    """Empaqueta {clave_serie: {paises: {...}, promedio: [...]}} para las
    tres dimensiones (mismo layout que los visualizadores) + imputados."""
    hojas = cargar_datos()
    df = preparar_datos(hojas)
    agregados = agregados_eco(hojas["datos_base"])
    datos = {}
    for codigo in [c for c, f in FICHAS.items() if f["dim"] == "eco"]:
        por_pais = {}
        for pais in PAISES:
            serie = (df[df["pais"] == pais].sort_values("anio")[codigo]
                     .round(6).tolist())
            por_pais[pais] = [None if (isinstance(v, float) and math.isnan(v))
                              else v for v in serie]
        promedio = [None if math.isnan(v) else v
                    for v in df.groupby("anio")[codigo].mean().sort_index()
                    .round(6).tolist()]
        datos[codigo] = {"paises": por_pais, "promedio": promedio,
                         "agregado": agregados.get(codigo)}
    datos.update(leer_series_extra())     # series ENV/SOC + ENV6
    imputados = {
        pais: df[df["pais"] == pais].sort_values("anio")["tarifa_imputada"]
              .tolist()
        for pais in PAISES
    }
    return datos, imputados


def _tabla_md(bloque: dict, formato: str, delta_tipo: str,
              imputados: dict | None) -> list[str]:
    """Tabla Markdown país x año con las filas resumen y columna de
    variación 2020→2024. Cierra con el promedio de países (media
    simple) y, cuando la serie tiene denominador disponible, el
    agregado regional (razón de sumas). Los imputados de ECO14 llevan
    asterisco."""
    lineas = ["| País | " + " | ".join(str(a) for a in ANIOS) +
              " | Δ 2020→2024 |",
              "|---|" + "---|" * (len(ANIOS) + 1)]
    for pais in PAISES:
        vals = bloque["paises"][pais]
        celdas = []
        for i, v in enumerate(vals):
            marca = "\\*" if imputados and imputados[pais][i] else ""
            celdas.append(_fmt(v, formato) + marca)
        lineas.append(f"| {pais} | " + " | ".join(celdas) +
                      f" | {_delta(vals[0], vals[-1], delta_tipo)} |")
    prom = bloque["promedio"]
    lineas.append("| **Promedio de países** (media simple) | " +
                  " | ".join(f"**{_fmt(v, formato)}**" for v in prom) +
                  f" | **{_delta(prom[0], prom[-1], delta_tipo)}** |")
    agr = bloque.get("agregado")
    if agr:
        lineas.append("| **Agregado regional** (razón de sumas) | " +
                      " | ".join(f"**{_fmt(v, formato)}**" for v in agr) +
                      f" | **{_delta(agr[0], agr[-1], delta_tipo)}** |")
    return lineas


def _generar_md(datos: dict, imputados: dict) -> str:
    md = [f"""# Matriz consolidada de indicadores — SIEPAC 2020–2024

**Proyecto:** Evaluación del suministro de energía eléctrica en el SIEPAC:
perspectivas económicas, sociales y ambientales. Monográfico de
Ingeniería Eléctrica, Universidad Nacional de Ingeniería (Nicaragua).
**Metodología:** indicadores IEDS (*Energy Indicators for Sustainable
Development*, OIEA/NU, 2005).
**Cobertura:** {', '.join(PAISES)} — los seis países interconectados por
el SIEPAC — ventana {ANIOS[0]}–{ANIOS[-1]}.
**Fuentes de datos:** SIELAC·OLADE, CEPALSTAT·CEPAL, Banco Mundial (WDI)
y EOR (Mercado Eléctrico Regional).
**Documento generado automáticamente** por
`src/generar_resumen_indicadores.py` el {date.today().isoformat()};
los valores provienen del mismo pipeline que alimenta los visualizadores.

## Cómo leer este documento

Cada indicador incluye su ficha (unidad, fórmula, descripción y notas
metodológicas) y su tabla de valores por país y año, con la variación
2020→2024 (relativa en % para magnitudes; en puntos porcentuales, pp,
para indicadores que ya son porcentajes). "s.d." = sin dato.
Los indicadores con varias salidas (p. ej. per cápita y por PIB)
presentan una tabla por sub-serie.

Cada tabla cierra con dos resúmenes que responden preguntas distintas:

- **Promedio de países** (media simple, peso 1/6 por país): ¿cómo está
  el país típico del bloque? Sensible por igual a países grandes y
  pequeños.
- **Agregado regional** (razón de sumas, Σ numerador / Σ denominador,
  que equivale a ponderar cada país por su denominador): ¿cómo está el
  SIEPAC como sistema? Es el agregado correcto cuando el texto habla de
  "la región" o "el bloque".

Ambos son legítimos pero pueden divergir mucho (incluso en el signo de
la tendencia, como en ECO15): al citar cifras regionales debe indicarse
cuál de los dos se usa. Las series sin denominador disponible en el
repositorio (ECO14: energía regulada vendida; SOC2: hogares e ingresos
en USD; SOC3: población rural/urbana) solo presentan el promedio de
países, y su nota metodológica lo advierte.
"""]
    filas_csv = []

    dim_previa = None
    for codigo, ficha in FICHAS.items():
        # ENV6: comparativo ilustrativo de dos series observadas.
        if ficha.get("tipo") == "env6":
            if "ENV6" not in datos:
                continue
            if ficha["dim"] != dim_previa:
                md.append(f"\n## {NOMBRE_DIM[ficha['dim']]}\n")
                dim_previa = ficha["dim"]
            md.append(f"\n### {codigo} · {ficha['nombre']}\n")
            md.append(f"**Unidad:** {ficha['unidad']}.\n")
            md.append(ficha["descripcion"] + "\n")
            if ficha["nota"]:
                md.append(f"> Nota metodológica: {ficha['nota']}\n")
            md.append("| País | Serie | " +
                      " | ".join(str(a) for a in ANIOS) + " |")
            md.append("|---|---|" + "---|" * len(ANIOS))
            for pais in PAISES:
                for nombre_s, k in [("Inyección Biomasa", "biomasa"),
                                    ("Saldo MER", "saldo")]:
                    vals = datos["ENV6"][pais][k]
                    md.append(f"| {pais} | {nombre_s} | " +
                              " | ".join(_fmt(v, ",.1f") for v in vals) +
                              " |")
                    for anio, v in zip(ANIOS, vals):
                        filas_csv.append([ficha["dim"], codigo,
                                          f"ENV6_{k}", nombre_s,
                                          ficha["nombre"], pais, anio, v,
                                          ficha["unidad"], "real"])
            continue

        series = [s for s in _series_de(ficha, codigo)
                  if s["clave"] in datos]
        if not series:
            log.warning("Sin datos, se omite del resumen: %s", codigo)
            continue

        if ficha["dim"] != dim_previa:
            md.append(f"\n## {NOMBRE_DIM[ficha['dim']]}\n")
            dim_previa = ficha["dim"]

        md.append(f"\n### {codigo} · {ficha['nombre']}\n")
        md.append(ficha["descripcion"] + "\n")
        if ficha["nota"]:
            md.append(f"> Nota metodológica: {ficha['nota']}\n")

        for s in series:
            bloque = datos[s["clave"]]
            titulo_s = f" — {s['etiqueta']}" if s["etiqueta"] else ""
            md.append(f"**{s['clave']}{titulo_s}** · Unidad: "
                      f"{s['unidad']} · Fórmula: {s['formula']}\n")
            marcas = imputados if s["clave"] == "ECO14" else None
            md.extend(_tabla_md(bloque, s["formato"], ficha["delta"],
                                marcas))
            md.append("")
            for pais in PAISES:
                for i, (anio, v) in enumerate(zip(ANIOS,
                                                  bloque["paises"][pais])):
                    fuente = ("imputado_CAGR" if marcas and marcas[pais][i]
                              else ("sin_dato" if v is None else "real"))
                    filas_csv.append([ficha["dim"], codigo, s["clave"],
                                      s["etiqueta"], ficha["nombre"], pais,
                                      anio, v, s["unidad"], fuente])
            # Filas resumen: se conserva la etiqueta histórica "Promedio
            # regional" (media simple) por compatibilidad y se añade el
            # "Agregado regional" (razón de sumas) cuando existe.
            for anio, v in zip(ANIOS, bloque["promedio"]):
                filas_csv.append([ficha["dim"], codigo, s["clave"],
                                  s["etiqueta"], ficha["nombre"],
                                  "Promedio regional", anio, v,
                                  s["unidad"], "calculado_media_simple"])
            for anio, v in zip(ANIOS, bloque.get("agregado") or []):
                filas_csv.append([ficha["dim"], codigo, s["clave"],
                                  s["etiqueta"], ficha["nombre"],
                                  "Agregado regional", anio, v,
                                  s["unidad"], "calculado_razon_sumas"])

    md.append("""
## Trazabilidad

Los valores de este documento se calculan con las fórmulas indicadas a
partir de las variables base del pipeline (`data/processed/`), en
unidades homologadas: energía en kWh, PIB y valor agregado industrial en
USD constantes de 2015, tarifa en USD corrientes/MWh. Las mismas cifras,
con sus tablas de datos base, pueden auditarse en los visualizadores del
proyecto (`graficos/`); en los libros Excel, las filas "Agregado
regional (razón de sumas)" llevan fórmulas SUM auditables hacia
Datos_Base. La versión máquina de esta matriz está en
`data/processed/indicadores_consolidados_tidy.csv` (el promedio de
países aparece como pais = "Promedio regional" con fuente_dato =
"calculado_media_simple"; el agregado, como "Agregado regional" con
"calculado_razon_sumas").

\\* Valor imputado vía CAGR (no observación directa de la fuente).
""")
    return "\n".join(md), filas_csv


def main() -> None:
    log.info("Consolidando indicadores de las tres dimensiones...")
    datos, imputados = _armar_datos()
    contenido, filas_csv = _generar_md(datos, imputados)

    RUTA_MD.parent.mkdir(exist_ok=True)
    RUTA_MD.write_text(contenido, encoding="utf-8")
    log.info("Exportado: %s (%.0f KB)", RUTA_MD,
             RUTA_MD.stat().st_size / 1024)

    with open(RUTA_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["dimension", "indicador", "serie", "sub_serie",
                    "nombre", "pais", "anio", "valor", "unidad",
                    "fuente_dato"])
        w.writerows(filas_csv)
    log.info("Exportado: %s (%d filas)", RUTA_CSV, len(filas_csv))


if __name__ == "__main__":
    main()
