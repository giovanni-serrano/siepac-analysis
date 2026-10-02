"""Configuración exclusiva de pruebas; no cambia rutas de producción."""

import json
from pathlib import Path
import sys

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(Path(__file__).parent))


def pytest_addoption(parser):
    parser.addoption("--resultados-dir", type=Path, default=RAIZ,
                     help="Raíz de resultados actuales o de la ejecución aislada.")


@pytest.fixture(scope="session")
def referencia():
    ruta = Path(__file__).parent / "fixtures" / "baseline" / "resultados.json"
    return json.loads(ruta.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def raiz_resultados(request):
    return request.config.getoption("--resultados-dir").resolve()
