"""Pruebas de aceptación del agregado regional SOC2."""

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from etl_soc2 import calcular_regional, cargar_y_validar  # noqa: E402


class TestSOC2(unittest.TestCase):
    def test_resultados_regionales_autoritativos(self):
        calculado = calcular_regional(cargar_y_validar())
        esperado = pd.read_csv(
            RAIZ / "tests" / "fixtures" / "soc2" /
            "resultados_esperados.csv")
        columnas = ["SOC2_PROM", "SOC2_VULNERABLE",
                    "brecha_vulnerable_prom_pp"]
        self.assertEqual(calculado["anio"].tolist(), esperado["anio"].tolist())
        self.assertTrue(np.allclose(calculado[columnas], esperado[columnas],
                                    rtol=1e-12, atol=1e-12))


if __name__ == "__main__":
    unittest.main()
