"""
resultados_indicadores.py — Intercambio común sin depender de productos Excel
====================================================
Etapa del pipeline : resultados estructurados (módulo importable)
Entradas           : CSV ECO y resultados_ECO/ENV/SOC.json
Salidas            : tablas base y paquetes comunes de series
Alimenta           : libros, resumen, tablas, figuras y visualizador
Fuente de datos    : ETL normalizados y libros originales del equipo
Uso                : importar funciones; invocadas por las etapas existentes
Notas metodológicas: mantiene fuentes, ponderadores, orden de operaciones y
                     precisión publicada. No sustituye insumos originales.
Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import json
import logging
import math
from pathlib import Path
import pandas as pd
from config_siepac import (PAISES_SIEPAC as PAISES, ANIOS_ANALISIS as ANIOS,
                           DIR_PROCESSED)
from calculos_indicadores import agregados_eco
from metadatos_indicadores import CODIGOS_ECO
log = logging.getLogger(__name__)


def _precision_publicada(valor):
    """Conserva la frontera decimal histórica de las celdas numéricas (16g).

    Los consumidores antes leían valores serializados por openpyxl. Mantener
    esa precisión aquí evita alterar su entrada al retirar el libro intermedio;
    los cálculos científicos y los CSV ECO conservan su precisión original.
    """
    if isinstance(valor, float):
        return None if math.isnan(valor) else float(format(valor, ".16g"))
    if isinstance(valor, list):
        return [_precision_publicada(v) for v in valor]
    if isinstance(valor, dict):
        return {k: _precision_publicada(v) for k, v in valor.items()}
    return valor


def guardar_resultado(ruta, contenido):
    ruta.write_text(json.dumps(_precision_publicada(contenido), ensure_ascii=False,
                               allow_nan=False), encoding="utf-8")


def guardar_base_eco(ruta, base):
    guardar_resultado(ruta, {"base": base.to_dict(orient="split")})


def guardar_dimension(ruta, tablas, agregados):
    guardar_resultado(ruta, {
        "base": tablas["BASE"].to_dict(orient="split"),
        "series": {c: tablas[c].to_dict(orient="split") for c in agregados},
        "agregados": agregados,
        **({"env6": tablas["ENV6"].to_dict(orient="split")} if "ENV6" in tablas else {}),
    })


def _leer_resultado(ruta):
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró {ruta}. Ejecuta antes: python src/run_pipeline.py")
    return json.loads(ruta.read_text(encoding="utf-8"))


def leer_bases(directorio=DIR_PROCESSED):
    """Bases por dimensión; ENV/SOC continúan siendo opcionales."""
    bases = {}
    for dim in ("ECO", "ENV", "SOC"):
        ruta = directorio / f"resultados_{dim}.json"
        if dim != "ECO" and not ruta.exists():
            continue
        bases[dim.lower()] = pd.DataFrame(**_leer_resultado(ruta)["base"])
    return bases


def cargar_datos(ruta_excel=None):
    """Carga CSV ECO y base estructurada; la ruta antigua identifica su carpeta.

    Se conserva el argumento posicional histórico sin abrir el libro.
    """
    directorio = Path(ruta_excel).parent if ruta_excel is not None else DIR_PROCESSED
    valores = pd.read_csv(directorio / "indicadores_ECO_valores.csv")
    hojas = {}
    for codigo in CODIGOS_ECO:
        df = valores.pivot(index="pais", columns="anio", values=codigo).reset_index()
        df.columns = ["pais"] + [int(c) for c in df.columns[1:]]
        hojas[codigo] = df
    hojas["tarifa_flag"] = valores[["pais", "anio", "tarifa_fuente_dato"]].copy()
    hojas["datos_base"] = pd.DataFrame(**_leer_resultado(
        directorio / "resultados_ECO.json")["base"])
    return hojas


def leer_series_extra(directorio=DIR_PROCESSED):
    """Lee series ENV/SOC sin nombres de hojas, posiciones ni etiquetas visuales."""
    paquete = {}
    for dim in ("ENV", "SOC"):
        ruta = directorio / f"resultados_{dim}.json"
        if not ruta.exists():
            log.warning("No encontrado: %s — se omite esa dimensión (la app se genera igual).", ruta.name)
            continue
        resultado = _leer_resultado(ruta)
        for clave, tabla in resultado["series"].items():
            hoja = pd.DataFrame(**tabla)
            paises = {p: [None if pd.isna(v) else round(float(v), 6)
                           for v in hoja.loc[p, ANIOS]] for p in PAISES}
            promedio = [round(float(hoja[a].mean(skipna=True)), 6) for a in ANIOS]
            agr = resultado["agregados"][clave]
            agregado = None if agr is None else [None if v is None else round(float(v), 6) for v in agr]
            paquete[clave] = {"paises": paises, "promedio": promedio, "agregado": agregado}
        if "env6" in resultado:
            e6 = pd.DataFrame(**resultado["env6"])
            paquete["ENV6"] = {
                p: {dest: [round(float(v), 2) for v in
                           e6[(e6["pais"] == p) & (e6["serie"] == origen)].iloc[0, 2:7]]
                    for dest, origen in (("biomasa", "Inyección Biomasa"), ("saldo", "Saldo MER"))}
                for p in PAISES}
    return paquete

def preparar_datos(hojas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Convierte las hojas (pais x anio) a UNA tabla larga:

        pais | anio | ECO1 | ECO3 | ... | ECO15 | tarifa_imputada

    El formato largo se comparte entre todos los consumidores.
    """
    largos = []
    for codigo in CODIGOS_ECO:
        largo = hojas[codigo].melt(id_vars="pais", var_name="anio",
                                   value_name=codigo)
        largos.append(largo.set_index(["pais", "anio"]))
    df = pd.concat(largos, axis=1).reset_index()

    # La bandera procede del CSV ECO y conserva la trazabilidad del ETL.
    flag = hojas["tarifa_flag"].rename(
        columns={"tarifa_fuente_dato": "tarifa_imputada"})
    flag["tarifa_imputada"] = flag["tarifa_imputada"] == "imputado_CAGR"
    df = df.merge(flag, on=["pais", "anio"], how="left")

    df["anio"] = df["anio"].astype(int)
    return df.sort_values(["pais", "anio"]).reset_index(drop=True)


def construir_paquete(df, base_df, extra) -> dict:
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
    for codigo in CODIGOS_ECO:
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
    return paquete


def construir_datos_json(df, base_df, extra):
    """Adaptador histórico para incrustar el paquete común en HTML."""
    return json.dumps(construir_paquete(df, base_df, extra), ensure_ascii=False)


def cargar_paquete():
    hojas = cargar_datos()
    return construir_paquete(preparar_datos(hojas), hojas["datos_base"], leer_series_extra())
