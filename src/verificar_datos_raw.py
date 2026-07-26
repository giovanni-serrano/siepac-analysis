"""
verificar_datos_raw.py — Verifica los datos crudos contra el manifiesto
====================================================
Etapa del pipeline : verificación previa (correr antes de run_pipeline.py
                     si acabas de clonar el repo o de descargar los datos)
Entradas           : src/catalogo_datos_raw.py, data/raw/<variable>/*
Salidas            : — (solo mensajes por consola; código de salida)
Fuente de datos    : —

Para cada variable del catálogo, confirma que exista un archivo que
cumpla el patrón esperado en `data/raw/<variable>/` y que su hash SHA-256
coincida con el de la copia verificada. Es la pieza que permite que
algunos archivos crudos (los de OLADE, ver notas de licenciamiento en
`catalogo_datos_raw.py`) no vivan en el repositorio sin perder la
capacidad de confirmar que la copia local es la correcta.

Un hash que no coincide NO es necesariamente un error: puede ser que la
fuente actualizó la serie. Se reporta como aviso, no bloquea. Un archivo
ausente si bloquea (código de salida 1), porque ningún ETL puede correr
sin él.

Uso:  python src/verificar_datos_raw.py   (ejecutar desde la raíz)

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import hashlib
import logging
import sys
from pathlib import Path

from catalogo_datos_raw import CATALOGO_RAW
from config_siepac import DIR_RAW

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

TAMANO_BLOQUE = 1024 * 1024  # 1 MiB, para no cargar archivos grandes enteros


def _sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(TAMANO_BLOQUE), b""):
            h.update(bloque)
    return h.hexdigest()


def _candidatos(carpeta: Path, patron: str) -> list[Path]:
    if not carpeta.exists():
        return []
    return sorted(f for f in carpeta.glob(patron)
                  if not f.name.startswith("~$"))


def main() -> None:
    faltantes, con_aviso, ok = [], [], []

    for entrada in CATALOGO_RAW:
        carpeta = DIR_RAW / entrada.carpeta
        candidatos = _candidatos(carpeta, entrada.patron)

        if not candidatos:
            faltantes.append(entrada)
            log.error("FALTA   %-32s sin archivo '%s' en data/raw/%s/",
                      entrada.variable, entrada.patron, entrada.carpeta)
            log.error("        Descargar de: %s", entrada.ruta_navegacion)
            continue

        if len(candidatos) > 1:
            log.warning("Hay %d archivos '%s' en data/raw/%s/; se verifica "
                       "el primero: %s", len(candidatos), entrada.patron,
                       entrada.carpeta, candidatos[0].name)

        archivo = candidatos[0]
        hash_real = _sha256(archivo)
        if hash_real == entrada.sha256:
            ok.append(entrada)
            log.info("OK      %-32s %s", entrada.variable, archivo.name)
        else:
            con_aviso.append(entrada)
            log.warning("DISTINTO %-31s %s", entrada.variable, archivo.name)
            log.warning("         hash esperado : %s", entrada.sha256)
            log.warning("         hash actual   : %s", hash_real)
            log.warning("         Puede ser una actualización legítima de "
                       "la fuente, o un archivo equivocado en la carpeta; "
                       "no bloquea el pipeline pero conviene confirmarlo.")

    total = len(CATALOGO_RAW)
    log.info("")
    log.info("Resumen: %d/%d verificados sin cambios, %d con hash distinto, "
             "%d faltantes.", len(ok), total, len(con_aviso), len(faltantes))

    if faltantes:
        log.error("Faltan %d archivo(s) crudo(s); ver data/raw/MANIFIESTO.md "
                  "para la ruta de descarga de cada uno.", len(faltantes))
        sys.exit(1)


if __name__ == "__main__":
    main()
