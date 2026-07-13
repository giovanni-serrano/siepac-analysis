"""
etl_comun.py — Utilidades compartidas de los ETL
====================================================
Etapa del pipeline : soporte (módulo común, no se ejecuta directo)
Entradas           : —
Salidas            : — (lo importan los ETL de src/)

Funciones de apoyo que antes estaban duplicadas en varios ETL:
la localización del archivo de entrada dentro de la carpeta raw.

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import logging
from pathlib import Path

log = logging.getLogger(Path(__file__).stem)


def encontrar_archivo_entrada(raw_dir: Path, patron: str = "*.xlsx") -> Path:
    """Busca el primer archivo que cumpla el patrón dentro de raw_dir
    (ignora archivos temporales de Excel tipo ~$).

    Falla con mensaje claro si la carpeta no existe o no hay candidatos;
    si hay más de uno, avisa y usa el primero en orden alfabético.
    """
    if not raw_dir.exists():
        raise FileNotFoundError(f"La carpeta no existe:\n{raw_dir}")

    candidatos = [f for f in sorted(raw_dir.glob(patron))
                  if not f.name.startswith("~$")]

    if not candidatos:
        contenido = list(raw_dir.iterdir())
        raise FileNotFoundError(
            f"No se encontró ningún '{patron}' en:\n{raw_dir}\n"
            f"Contenido actual de la carpeta: "
            f"{contenido if contenido else '(vacía)'}"
        )

    if len(candidatos) > 1:
        log.warning("Hay %d archivos '%s', se usará: %s",
                    len(candidatos), patron, candidatos[0].name)

    return candidatos[0]
