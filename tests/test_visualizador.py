"""Pruebas de estructura del visualizador regional único."""

import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from generar_visualizador import (  # noqa: E402
    CODIGO_ECO_CG,
    FICHAS,
    RUTA_SALIDA,
    _fichas_visualizador,
    _sanear_plotly_js,
)


class TestVisualizador(unittest.TestCase):
    def test_catalogo_distingue_ieds_y_serie_complementaria(self):
        fichas = _fichas_visualizador()
        self.assertEqual(len(FICHAS), 15)
        self.assertEqual(len(fichas), 16)
        self.assertTrue(fichas[CODIGO_ECO_CG]["complementaria"])
        self.assertEqual(len(fichas["ENV6"]["series"]), 2)
        self.assertTrue(all(f["hallazgo_regional"].strip()
                            for f in fichas.values()))

    def test_html_autocontenido_generado(self):
        contenido = RUTA_SALIDA.read_text(encoding="utf-8")
        self.assertIn("Visualizador regional SIEPAC", contenido)
        self.assertIn("El SIEPAC como sistema", contenido)
        self.assertIn("Mínimo–máximo entre países", contenido)
        self.assertIn("Conclusión regional.", contenido)
        self.assertIn("ECO_CG", contenido)
        self.assertNotIn("Manifiesto de salidas", contenido)
        self.assertNotIn('"base_env"', contenido)
        self.assertNotIn('"base_soc"', contenido)
        self.assertNotIn("__DATOS__", contenido)
        self.assertNotIn("__PLOTLYJS__", contenido)
        self.assertIn('@media (max-width:640px)', contenido)
        self.assertIn('@media (prefers-reduced-motion:reduce)', contenido)
        self.assertIn('aria-controls="vista"', contenido)
        self.assertIn('role="tabpanel"', contenido)
        self.assertIn('function navegarTabs', contenido)
        self.assertIn('displayModeBar:false', contenido)
        self.assertIn('class="chart-mobile-meta"', contenido)
        self.assertIn('showlegend:!movil', contenido)
        self.assertIn('Abrir figura para la tesis', contenido)
        self.assertIn('para móvil use la vista Región', contenido)
        controles = [ord(c) for c in contenido
                     if ord(c) < 32 and c not in "\t\n\r"]
        self.assertEqual(controles, [])

    def test_sanitiza_controles_incrustados_por_plotly(self):
        self.assertEqual(_sanear_plotly_js("a\x01b\x1ac"),
                         r"a\x01b\x1ac")


if __name__ == "__main__":
    unittest.main()
