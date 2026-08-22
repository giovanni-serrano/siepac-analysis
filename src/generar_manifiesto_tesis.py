"""
generar_manifiesto_tesis.py — Inventario de salidas usadas por la tesis
====================================================
Etapa del pipeline : documentación y entrega
Entradas           : salidas/tesis/manifiesto_figuras.csv y
                     salidas/tesis/tablas/indice_tablas.csv
Salidas            : salidas/tesis/manifiesto.csv
Alimenta           : revisión, inserción y trazabilidad de la monografía
Fuente de datos    : generadores de figuras y tablas APA del pipeline

Reúne en un solo inventario todas las salidas oficiales. Las rutas se
guardan relativas a salidas/tesis/ para que sigan funcionando al clonar el
repositorio en cualquier ubicación.

Uso:  python src/generar_manifiesto_tesis.py   (desde la raíz)

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import csv
import logging
import sys
from pathlib import Path

import pandas as pd

from config_siepac import DIR_SALIDAS_TESIS

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

RUTA_FIGURAS = DIR_SALIDAS_TESIS / "manifiesto_figuras.csv"
RUTA_TABLAS = DIR_SALIDAS_TESIS / "tablas" / "indice_tablas.csv"
RUTA_TABLA_SOC2 = (DIR_SALIDAS_TESIS / "tablas" /
                   "tabla_07_soc2_regional_tesis.html")
RUTA_SALIDA = DIR_SALIDAS_TESIS / "manifiesto.csv"


def main() -> None:
    faltantes = [ruta for ruta in (RUTA_FIGURAS, RUTA_TABLAS, RUTA_TABLA_SOC2)
                 if not ruta.exists()]
    if faltantes:
        nombres = ", ".join(str(ruta) for ruta in faltantes)
        raise FileNotFoundError(
            f"VALIDACIÓN FALLIDA: faltan inventarios de entrada: {nombres}")

    figuras = pd.read_csv(RUTA_FIGURAS)
    tablas = pd.read_csv(RUTA_TABLAS)
    if len(figuras) != 22 or len(tablas) != 75:
        raise ValueError(
            "VALIDACIÓN FALLIDA: se esperaban 22 figuras y 75 tablas; "
            f"se encontraron {len(figuras)} y {len(tablas)}")

    filas: list[list[object]] = []
    for fila in figuras.itertuples(index=False):
        filas.append([
            "figura", fila.figura_sugerida, fila.dimension, fila.codigo,
            f"figuras/{fila.archivo}", fila.titulo, fila.medida_principal,
        ])
    filas.append([
        "tabla_tesis", 7, "soc", "SOC2_REGIONAL",
        "tablas/tabla_07_soc2_regional_tesis.html",
        "SOC2 regional agregado del SIEPAC, 2020–2024",
        "Tabla 7 del cuerpo de la tesis",
    ])
    for fila in tablas.itertuples(index=False):
        filas.append([
            "tabla", fila.numero, fila.dimension, fila.codigo,
            f"tablas/{fila.archivo}", fila.titulo, fila.seccion,
        ])

    # Los fragmentos #tabla-NN son enlaces internos del HTML consolidado.
    # Se comprueban archivo y ancla para no publicar un inventario con rutas
    # que funcionen solo en una copia local del proyecto.
    errores: list[str] = []
    contenidos: dict[Path, str] = {}
    for ruta_relativa in (str(fila[4]) for fila in filas):
        nombre, separador, fragmento = ruta_relativa.partition("#")
        ruta = DIR_SALIDAS_TESIS / nombre
        if not ruta.exists():
            errores.append(ruta_relativa)
            continue
        if separador:
            if ruta not in contenidos:
                contenidos[ruta] = ruta.read_text(encoding="utf-8")
            contenido = contenidos[ruta]
            if f'id="{fragmento}"' not in contenido:
                errores.append(ruta_relativa)
    if errores:
        raise FileNotFoundError(
            "VALIDACIÓN FALLIDA: rutas o anclas inexistentes: "
            + ", ".join(errores))

    DIR_SALIDAS_TESIS.mkdir(parents=True, exist_ok=True)
    with open(RUTA_SALIDA, "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.writer(f)
        escritor.writerow([
            "tipo", "numero", "dimension", "codigo", "archivo", "titulo",
            "criterio_o_seccion",
        ])
        escritor.writerows(filas)

    log.info("Listo: %d salidas inventariadas en %s", len(filas), RUTA_SALIDA)


if __name__ == "__main__":
    main()
