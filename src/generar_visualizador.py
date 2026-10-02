"""
generar_visualizador.py — Visualizador regional único del SIEPAC
====================================================
Etapa del pipeline : visualización y comunicación de resultados
Entradas           : matrices de indicadores en data/processed/,
                     data/raw_equipo/eco_cg_siepac.csv, figuras y tablas de
                     salidas/tesis/
Salidas            : graficos/visualizador_siepac.html
Alimenta           : consulta pública y defensa de la monografía
Fuente de datos    : salidas validadas del pipeline; fichas en metadatos_indicadores.py

Genera una aplicación HTML autocontenida y orientada primero al bloque
regional. Reúne resumen, comparación entre países, datos y metodología sin
duplicar cifras o fórmulas fuera de sus fuentes canónicas.

Uso:  python src/generar_visualizador.py   (desde la raíz del proyecto)

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

from copy import deepcopy
import json
import logging
import sys
from pathlib import Path

import pandas as pd
import plotly.offline as pyo

from config_siepac import (ANIOS_ANALISIS as ANIOS, DIR_GRAFICOS,
                           DIR_SALIDAS_TESIS, PAISES_SIEPAC as PAISES)
from eco_cg_comun import (CODIGO_ECO_CG, FICHA_ECO_CG, cargar_eco_cg,
                          serie_mediana_eco_cg)
from viz_comun import (COLORES_PAIS)
from presentacion_indicadores import FICHAS
from resultados_indicadores import (cargar_datos, construir_datos_json, leer_series_extra, preparar_datos)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

RUTA_SALIDA = DIR_GRAFICOS / "visualizador_siepac.html"
DIR_FIGURAS = DIR_SALIDAS_TESIS / "figuras"
RUTA_TABLAS = DIR_SALIDAS_TESIS / "tablas" / "indice_tablas.csv"


def _serie_eco_cg() -> dict:
    """Empaqueta ECO-CG como comparación descriptiva, nunca como agregado."""
    datos = cargar_eco_cg()
    pivote = (datos.pivot(index="anio", columns="pais", values=CODIGO_ECO_CG)
              .reindex(index=ANIOS, columns=PAISES))
    return {
        "paises": {
            pais: [round(float(valor), 6) for valor in pivote[pais]]
            for pais in PAISES
        },
        "promedio": [round(float(valor), 6)
                     for valor in pivote.mean(axis=1)],
        "mediana": [round(float(valor), 6)
                    for valor in serie_mediana_eco_cg(datos)],
        "agregado": None,
        "banderas": {
            pais: [str(valor) for valor in
                   datos[datos["pais"] == pais].sort_values("anio")["bandera"]]
            for pais in PAISES
        },
    }


def _normalizar_env6(paquete: dict) -> None:
    """Convierte las dos magnitudes ENV6 al contrato común de la interfaz."""
    origen = paquete.pop("ENV6")
    for destino, clave in (("ENV6_BIOMASA", "biomasa"),
                           ("ENV6_SALDO", "saldo")):
        paises = {pais: origen[pais][clave] for pais in PAISES}
        marco = pd.DataFrame(paises, index=ANIOS)
        paquete[destino] = {
            "paises": paises,
            "promedio": [round(float(v), 6) for v in marco.mean(axis=1)],
            "agregado": [round(float(v), 6) for v in marco.sum(axis=1)],
        }


def _fichas_visualizador() -> dict:
    """Extiende las fichas canónicas solo con metadatos propios de la UI."""
    fichas = deepcopy(FICHAS)
    fichas["ENV6"]["series"] = [
        ["ENV6_BIOMASA", "Inyección de biomasa", ",.1f", " GWh", "GWh",
         "Suma de la inyección de biomasa observada en los seis países"],
        ["ENV6_SALDO", "Saldo neto en el MER", ",.1f", " GWh", "GWh",
         "Suma de los saldos netos observados de los seis países"],
    ]
    ficha_cg = deepcopy(FICHA_ECO_CG)
    ficha_cg.update(tipo="eco_cg", complementaria=True)
    fichas[CODIGO_ECO_CG] = ficha_cg
    return fichas


def _enlaces_salidas(fichas: dict) -> dict:
    """Relaciona series con archivos oficiales sin generar un manifiesto."""
    if not RUTA_TABLAS.exists():
        raise FileNotFoundError(
            "VALIDACIÓN FALLIDA: genere antes las figuras y tablas APA")

    archivos_figura = {}
    for codigo, ficha in fichas.items():
        if codigo == "ENV6":
            archivos_figura.update({
                "ENV6": "ENV6_bloque.png",
                "ENV6_BIOMASA": "ENV6_bloque.png",
                "ENV6_SALDO": "ENV6_bloque.png",
            })
        elif ficha.get("series"):
            archivos_figura.update({
                serie[0]: f"{serie[0]}_bloque.png"
                for serie in ficha["series"]
            })
        else:
            archivos_figura[codigo] = f"{codigo}_bloque.png"

    faltantes = sorted({nombre for nombre in archivos_figura.values()
                        if not (DIR_FIGURAS / nombre).exists()})
    if faltantes:
        raise FileNotFoundError(
            "VALIDACIÓN FALLIDA: faltan figuras oficiales: " +
            ", ".join(faltantes))
    enlaces_figuras = {
        codigo: f"../salidas/tesis/figuras/{archivo}"
        for codigo, archivo in archivos_figura.items()
    }

    tablas = pd.read_csv(RUTA_TABLAS)
    claves_tabla = {
        serie[0] for codigo, ficha in fichas.items()
        if codigo != CODIGO_ECO_CG
        for serie in (ficha.get("series") or [[codigo]])
    }
    claves_tabla.add("ENV6")
    enlaces_tablas = {
        str(fila.codigo): f"../salidas/tesis/tablas/{fila.archivo}"
        for fila in tablas.itertuples(index=False)
        if str(fila.codigo) in claves_tabla
    }
    fila_cg = tablas[tablas["codigo"] == "eco_cg_usd_mwh"]
    if not fila_cg.empty:
        enlaces_tablas[CODIGO_ECO_CG] = (
            f"../salidas/tesis/tablas/{fila_cg.iloc[0]['archivo']}")
    return {"figuras": enlaces_figuras, "tablas": enlaces_tablas}


def _validar(paquete: dict, fichas: dict, enlaces: dict) -> None:
    """Detiene la publicación si falta una serie, país, año o figura."""
    if len(FICHAS) != 15:
        raise ValueError(
            f"VALIDACIÓN FALLIDA: se esperaban 15 IEDS; hay {len(FICHAS)}")

    claves = []
    for codigo, ficha in fichas.items():
        series = ficha.get("series") or [[codigo]]
        claves.extend(serie[0] for serie in series)
    errores = []
    sin_hallazgo = sorted(
        codigo for codigo, ficha in fichas.items()
        if not str(ficha.get("hallazgo_regional", "")).strip()
    )
    if sin_hallazgo:
        errores.append(f"hallazgos regionales ausentes: {sin_hallazgo}")
    for clave in claves:
        bloque = paquete.get(clave)
        if bloque is None:
            errores.append(f"serie ausente: {clave}")
            continue
        if set(bloque.get("paises", {})) != set(PAISES):
            errores.append(f"cobertura de países incompleta: {clave}")
            continue
        if any(len(bloque["paises"][pais]) != len(ANIOS) for pais in PAISES):
            errores.append(f"cobertura temporal incompleta: {clave}")

    figuras_requeridas = {
        serie[0] for ficha in fichas.values()
        for serie in (ficha.get("series") or [[]]) if serie
    }
    figuras_requeridas.update(
        codigo for codigo, ficha in fichas.items() if not ficha.get("series"))
    # ENV6 tiene una figura conjunta para sus dos magnitudes.
    figuras_requeridas.difference_update({"ENV6_BIOMASA", "ENV6_SALDO"})
    figuras_requeridas.add("ENV6")
    sin_figura = sorted(figuras_requeridas - set(enlaces["figuras"]))
    if sin_figura:
        errores.append(f"figuras no inventariadas: {sin_figura}")
    if errores:
        raise ValueError("VALIDACIÓN FALLIDA: " + "; ".join(errores))


def _sanear_plotly_js(codigo: str) -> str:
    """Escapa los dos controles C0 incluidos por Plotly antes de publicar."""
    return codigo.replace("\x01", r"\x01").replace("\x1a", r"\x1a")


PLANTILLA = (Path(__file__).parent / "plantillas" / "visualizador.html").read_text(encoding="utf-8")


def main() -> None:
    log.info("Cargando datos y fichas del pipeline...")
    hojas = cargar_datos()
    df = preparar_datos(hojas)
    paquete = json.loads(construir_datos_json(
        df, hojas["datos_base"], leer_series_extra()))
    _normalizar_env6(paquete)
    paquete[CODIGO_ECO_CG] = _serie_eco_cg()
    fichas = _fichas_visualizador()
    enlaces = _enlaces_salidas(fichas)
    _validar(paquete, fichas, enlaces)

    html = (PLANTILLA
            .replace("__PLOTLYJS__", _sanear_plotly_js(pyo.get_plotlyjs()))
            .replace("__DATOS__", json.dumps(paquete, ensure_ascii=False))
            .replace("__FICHAS__", json.dumps(fichas, ensure_ascii=False))
            .replace("__ANIOS__", json.dumps(ANIOS))
            .replace("__PAISES__", json.dumps(PAISES, ensure_ascii=False))
            .replace("__COLORES__", json.dumps(COLORES_PAIS,
                                                ensure_ascii=False))
            .replace("__SALIDAS__", json.dumps(enlaces,
                                                ensure_ascii=False)))
    marcadores = [m for m in ("__PLOTLYJS__", "__DATOS__", "__FICHAS__",
                               "__ANIOS__", "__PAISES__", "__COLORES__",
                               "__SALIDAS__") if m in html]
    if marcadores:
        raise ValueError(
            f"VALIDACIÓN FALLIDA: marcadores sin sustituir: {marcadores}")

    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    RUTA_SALIDA.write_text(html, encoding="utf-8")
    log.info("Exportado: %s (%.1f MB, autocontenido; 15 IEDS + ECO-CG)",
             RUTA_SALIDA, RUTA_SALIDA.stat().st_size / 1e6)


if __name__ == "__main__":
    main()
