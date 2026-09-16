"""Captura explícita de la referencia. Nunca se ejecuta desde las pruebas.

Uso: python tests/capturar_baseline.py --salida RUTA_NUEVA
La referencia no se actualiza automáticamente: cambiarla requiere revisión.
"""

import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import json
import platform
import subprocess

from baseline_utils import RAIZ, capturar, inventario_protegido
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", required=True, type=Path)
    args = parser.parse_args()
    if args.salida.exists():
        parser.error("La salida ya existe; no se sobrescriben referencias.")
    captura = capturar(RAIZ)
    captura["procedencia"] = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True).strip(),
        "python": platform.python_version(),
        "plataforma": platform.platform(),
        "dependencias": {p: version(p) for p in
                         ("pandas", "numpy", "openpyxl", "plotly", "kaleido", "pytest")},
        "archivos_sha256": inventario_protegido(RAIZ),
    }
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    with args.salida.open("x", encoding="utf-8") as archivo:
        json.dump(captura, archivo, ensure_ascii=False, indent=2, allow_nan=False)
        archivo.write("\n")
    print(f"Referencia creada: {args.salida}")


if __name__ == "__main__":
    main()
