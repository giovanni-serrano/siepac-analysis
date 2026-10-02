"""Contratos de separación y paridad del intercambio estructurado."""

import ast
import hashlib
import json
from pathlib import Path

import pandas as pd

import calculos_indicadores as calculos
import metadatos_indicadores as metadatos
import presentacion_indicadores as presentacion
import resultados_indicadores as resultados
import viz_comun
from config_siepac import ANIOS_ANALISIS as ANIOS, PAISES_SIEPAC as PAISES


def test_plantilla_web_conserva_texto_anterior():
    from generar_visualizador import PLANTILLA
    # SHA-256 del literal previo a la extracción; excluye datos dinámicos.
    assert hashlib.sha256(PLANTILLA.encode("utf-8")).hexdigest() == (
        "989faef93dfb81a0f544045f880decf7e65b53b8cfee3f477dc1c5a8c925e1d7")


def test_capas_cientificas_no_importan_presentacion_y_no_hay_ciclos():
    src = Path(__file__).resolve().parents[1] / "src"
    modulos = {p.stem: ast.parse(p.read_text(encoding="utf-8-sig"))
               for p in src.glob("*.py")}
    grafo = {
        nombre: {n.module for n in ast.walk(arbol)
                 if isinstance(n, ast.ImportFrom) and n.module in modulos}
        for nombre, arbol in modulos.items()}
    prohibidos = {"viz_comun", "presentacion_indicadores", "figuras_comun"}
    prohibidos.update(n for n in modulos if n.startswith("generar_"))

    def visitar(nombre, camino):
        assert nombre not in camino, camino + [nombre]
        for dependencia in grafo[nombre]:
            visitar(dependencia, camino + [nombre])

    for nombre in modulos:
        visitar(nombre, [])
    for nombre in ("calculos_indicadores", "metadatos_indicadores",
                   "datos_dimensiones", "resultados_indicadores"):
        assert not grafo[nombre] & prohibidos


def test_fachada_y_fichas_no_duplican_definiciones():
    assert viz_comun.media_ponderada is calculos.media_ponderada
    assert viz_comun.agregados_eco is calculos.agregados_eco
    assert viz_comun.cargar_datos is resultados.cargar_datos
    assert viz_comun.FICHAS is presentacion.FICHAS
    for ficha in metadatos.FICHAS.values():
        assert not {"formato", "sufijo", "modos", "nota_figura"} & ficha.keys()
    copia = presentacion.construir_fichas()
    copia["ECO1"]["unidad"] = "alterada"
    assert metadatos.FICHAS["ECO1"]["unidad"] == "kWh/habitante"


def test_productos_consumen_resultados_sin_excel(referencia, tmp_path, monkeypatch):
    """Reconstruye el intercambio desde la referencia fija y prohíbe read_excel.

    No crea libros: una regresión a producto→producto debe fallar aquí.
    """
    eco = referencia["libros"]["indicadores_ECO_SIEPAC.xlsx"]["Datos_Base"]
    resultados.guardar_base_eco(tmp_path / "resultados_ECO.json",
                               pd.DataFrame(eco[1:], columns=eco[0]))
    pd.DataFrame(referencia["csv"]["indicadores_ECO_valores.csv"]).to_csv(
        tmp_path / "indicadores_ECO_valores.csv", index=False)
    bases_esperadas = {"eco": pd.DataFrame(eco[1:], columns=eco[0])}
    for dim in ("ENV", "SOC"):
        libro = referencia["libros"][f"indicadores_{dim}_SIEPAC.xlsx"]
        base = libro["Datos_Base"]
        tablas = {"BASE": pd.DataFrame(base[3:], columns=base[2])}
        bases_esperadas[dim.lower()] = tablas["BASE"]
        agregados = {}
        for clave, filas in libro.items():
            if clave in {"Metodologia", "Datos_Base", "ENV6"}:
                continue
            tablas[clave] = pd.DataFrame([f[1:6] for f in filas[3:9]],
                                         index=PAISES, columns=ANIOS)
            agregados[clave] = referencia["web"]["datos"][clave]["agregado"]
        if dim == "ENV":
            tablas["ENV6"] = pd.DataFrame(libro["ENV6"][3:],
                                          columns=["pais", "serie", *ANIOS])
        resultados.guardar_dimension(tmp_path / f"resultados_{dim}.json", tablas, agregados)

    def prohibido(*args, **kwargs):
        raise AssertionError("Un consumidor intentó releer un producto Excel")

    monkeypatch.setattr(pd, "read_excel", prohibido)
    hojas = resultados.cargar_datos(tmp_path / "libro_inexistente.xlsx")
    extra = resultados.leer_series_extra(tmp_path)
    paquete = resultados.construir_paquete(resultados.preparar_datos(hojas),
                                           hojas["datos_base"], extra)
    for clave, bloque in paquete.items():
        if clave == "ENV6":
            for pais in PAISES:
                assert bloque[pais]["biomasa"] == referencia["web"]["datos"]["ENV6_BIOMASA"]["paises"][pais]
                assert bloque[pais]["saldo"] == referencia["web"]["datos"]["ENV6_SALDO"]["paises"][pais]
        else:
            assert json.dumps(bloque, sort_keys=True) == json.dumps(
                referencia["web"]["datos"][clave], sort_keys=True), clave
    for dim, base in resultados.leer_bases(tmp_path).items():
        pd.testing.assert_frame_equal(base, bases_esperadas[dim], check_exact=True,
                                      check_dtype=False)
