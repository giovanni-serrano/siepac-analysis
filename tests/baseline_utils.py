"""Lectura y comparación de resultados, sin ejecutar ni modificar producción."""

import csv
import hashlib
import json
import math
from pathlib import Path

import openpyxl

RAIZ = Path(__file__).resolve().parents[1]
REFERENCIA = Path(__file__).parent / "fixtures" / "baseline" / "resultados.json"
CSV_RESULTADOS = (
    "matriz_consolidada_wide.csv", "indicadores_ECO_valores.csv",
    "soc2_pais_anio.csv", "soc2_regional.csv", "soc2_sensibilidad.csv",
    "poblacion_rural_urbana.csv", "tarifa_electrica_media.csv",
    "indicadores_consolidados_tidy.csv",
)
LIBROS = tuple(f"indicadores_{dim}_SIEPAC.xlsx" for dim in ("ECO", "ENV", "SOC"))


def sha256(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def leer_csv(ruta):
    """Conserva texto y convierte solo literales numéricos, sin redondear."""
    def valor(texto):
        if texto == "":
            return None
        try:
            return int(texto)
        except ValueError:
            try:
                numero = float(texto)
                if not math.isfinite(numero):
                    raise ValueError(f"Valor no finito en {ruta}: {texto}")
                return numero
            except ValueError:
                if texto.lower() in {"nan", "inf", "-inf", "infinity"}:
                    raise
                return texto
    with Path(ruta).open(encoding="utf-8-sig", newline="") as archivo:
        return [{k: valor(v) for k, v in fila.items()}
                for fila in csv.DictReader(archivo)]


def leer_libro(ruta):
    """Congela valores y fórmulas; excluye estilos y metadatos del ZIP."""
    libro = openpyxl.load_workbook(ruta, data_only=False, read_only=True)
    try:
        return {hoja.title: [list(fila) for fila in hoja.iter_rows(values_only=True)]
                for hoja in libro}
    finally:
        libro.close()


def leer_web(ruta):
    texto = Path(ruta).read_text(encoding="utf-8")
    inicio = texto.index("const DATOS=") + len("const DATOS=")
    decoder = json.JSONDecoder()
    datos, longitud = decoder.raw_decode(texto[inicio:])
    resto = texto[inicio + longitud:]
    resultado = {"datos": datos}
    for nombre in ("FICHAS", "ANIOS", "PAISES"):
        posicion = resto.index(f"{nombre}=") + len(nombre) + 1
        valor, longitud = decoder.raw_decode(resto[posicion:])
        resultado[nombre.lower()] = valor
        resto = resto[posicion + longitud:]
    return resultado


def capturar(raiz):
    raiz = Path(raiz)
    procesados = raiz / "data" / "processed"
    return {
        "csv": {nombre: leer_csv(procesados / nombre) for nombre in CSV_RESULTADOS},
        "libros": {nombre: leer_libro(procesados / nombre) for nombre in LIBROS},
        "web": leer_web(raiz / "graficos" / "visualizador_siepac.html"),
    }


def comparar(actual, esperado, ruta="resultado"):
    """Diagnóstico por ruta; números a rtol=1e-12 / atol=1e-9, resto exacto."""
    if isinstance(esperado, dict):
        assert isinstance(actual, dict), ruta
        assert actual.keys() == esperado.keys(), f"{ruta}: claves diferentes"
        for clave in esperado:
            comparar(actual[clave], esperado[clave], f"{ruta}.{clave}")
    elif isinstance(esperado, list):
        assert isinstance(actual, list), ruta
        assert len(actual) == len(esperado), f"{ruta}: longitud diferente"
        for i, (a, e) in enumerate(zip(actual, esperado)):
            comparar(a, e, f"{ruta}[{i}]")
    elif isinstance(esperado, bool) or esperado is None or isinstance(esperado, str):
        assert actual == esperado and type(actual) is type(esperado), ruta
    elif isinstance(esperado, int) and isinstance(actual, int):
        assert actual == esperado, f"{ruta}: {actual} != {esperado}"
    else:
        assert isinstance(actual, (int, float)) and not isinstance(actual, bool), ruta
        assert math.isclose(actual, esperado, rel_tol=1e-12, abs_tol=1e-9), (
            f"{ruta}: {actual} != {esperado}")


def inventario_protegido(raiz):
    """Incluye insumos locales ignorados y productos; nunca lee .git ni .venv."""
    raiz = Path(raiz)
    archivos = []
    for carpeta in ("src", "data", "graficos", "salidas", "docs"):
        archivos.extend(p for p in (raiz / carpeta).rglob("*") if p.is_file()
                        and "__pycache__" not in p.parts
                        and p.name != "BASELINE_RESULTADOS.md")
    archivos.extend(raiz / p for p in ("requirements.txt", "README.md", "index.html"))
    return {p.relative_to(raiz).as_posix(): sha256(p) for p in sorted(archivos)}
