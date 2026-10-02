"""Ejecuta el pipeline intacto en una copia nueva y verifica paridad numérica.

Uso: python tests/ejecutar_pipeline_aislado.py --destino RUTA_NUEVA
No copia productos previos: el pipeline debe reconstruirlos desde los insumos.
Conserva copia, log y comprobantes para inspección; nunca borra originales.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from baseline_utils import (RAIZ, REFERENCIA, capturar, comparar,
                            inventario_protegido)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", required=True, type=Path)
    args = parser.parse_args()
    destino = args.destino.resolve()
    if destino.exists():
        parser.error("El destino debe ser nuevo; no se sobrescribe ni se borra.")
    # Evita que copytree copie su propia salida o escriba entre los originales.
    prohibidos = [RAIZ / p for p in ("src", "data", "docs", "graficos", "salidas", ".git")]
    if any(destino == p or p in destino.parents for p in prohibidos):
        parser.error("El destino no puede estar dentro de entradas, productos o .git.")
    antes = inventario_protegido(RAIZ)
    destino.mkdir(parents=True)
    for relativo in ("src", "data/raw", "data/raw_equipo"):
        shutil.copytree(RAIZ / relativo, destino / relativo,
                        ignore=shutil.ignore_patterns("__pycache__", "~$*"))
    (destino / "docs").mkdir()
    (destino / "originales_antes.json").write_text(
        json.dumps(antes, ensure_ascii=False, indent=2), encoding="utf-8")
    informe = {"destino": str(destino)}
    entorno = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        with (destino / "pipeline.log").open("w", encoding="utf-8") as log:
            proceso = subprocess.run(
                [sys.executable, "src/run_pipeline.py"], cwd=destino,
                env=entorno, stdout=log, stderr=subprocess.STDOUT)
        informe["codigo_salida"] = proceso.returncode
        if proceso.returncode:
            raise RuntimeError(f"Pipeline detenido; consulte {destino / 'pipeline.log'}")
        esperado = json.loads(REFERENCIA.read_text(encoding="utf-8"))
        actual = capturar(destino)
        for grupo in ("csv", "libros", "web"):
            comparar(actual[grupo], esperado[grupo], grupo)
        informe["paridad_cientifica"] = True
    finally:
        despues = inventario_protegido(RAIZ)
        informe["originales_intactos"] = antes == despues
        informe["archivos_protegidos"] = len(antes)
        (destino / "verificacion.json").write_text(
            json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        assert antes == despues, "Cambió el inventario de archivos originales."
    print(json.dumps(informe, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
