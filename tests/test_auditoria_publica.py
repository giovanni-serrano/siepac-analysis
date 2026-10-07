"""Regresiones de presentación pública sin modificar la referencia científica."""

import csv
import io
import json
import subprocess
import re
import zipfile

import pytest
from playwright._impl._driver import compute_driver_executable

from baseline_utils import leer_web
from generar_visualizador import PLANTILLA
from eco_cg_comun import NOTA_CALIDAD_ECO_CG


@pytest.fixture
def ejecutar_js(raiz_resultados):
    """Ejecuta las funciones reales con el Node de Playwright, sin navegador."""
    web = leer_web(raiz_resultados / "graficos" / "visualizador_siepac.html")
    html = (raiz_resultados / "graficos" / "visualizador_siepac.html").read_text(encoding="utf-8")
    nota = json.JSONDecoder().raw_decode(html.split("const NOTA_CALIDAD_CG=", 1)[1])[0]
    assert nota == NOTA_CALIDAD_ECO_CG
    funciones = PLANTILLA.split("function esc(", 1)[1].split(
        'navPrincipal.addEventListener("scroll"', 1)[0]
    preambulo = "\n".join(
        f"const {nombre.upper()}={json.dumps(valor, ensure_ascii=False)};"
        for nombre, valor in web.items())

    def ejecutar(expresion):
        programa = preambulo + "\nconst NOTA_CALIDAD_CG=" + json.dumps(nota) + ";\nfunction esc(" + funciones
        programa += "\nPromise.resolve(" + expresion + ").then(r=>console.log(JSON.stringify(r)));"
        proceso = subprocess.run(
            [str(compute_driver_executable()[0]), "-"], input=programa,
            encoding="utf-8", capture_output=True)
        assert proceso.returncode == 0, proceso.stderr
        return json.loads(proceso.stdout)

    return ejecutar


@pytest.mark.parametrize("serie", ["ENV6_BIOMASA", "ENV6_SALDO"])
def test_env6_presenta_suma_sin_cambiar_magnitudes(ejecutar_js, referencia, serie):
    resultado = ejecutar_js(f"principal('ENV6', DATOS['{serie}'])")
    assert resultado["etiqueta"] == "Suma regional"
    assert resultado["valores"] == referencia["web"]["datos"][serie]["agregado"]
    tarjeta = ejecutar_js("tarjeta('ENV6')")
    assert "Suma regional" in tarjeta
    assert "razón de sumas" not in tarjeta
    tabla = ejecutar_js(
        f"tablaSerie(infoSerie('ENV6', {int(serie == 'ENV6_SALDO')}), "
        f"DATOS['{serie}'], principal('ENV6', DATOS['{serie}']))")
    assert "Suma regional" in tabla
    assert "razón de sumas" not in tabla


@pytest.mark.parametrize("codigo", ["ECO14", "ECO_CG"])
def test_banderas_llegan_a_tabla_leyenda_y_csv(ejecutar_js, referencia, codigo):
    datos = referencia["web"]["datos"]
    csv_texto = ejecutar_js(
        f"contenidoCSV('{codigo}', infoSerie('{codigo}'), DATOS['{codigo}'], "
        f"principal('{codigo}', DATOS['{codigo}']))")
    filas = list(csv.DictReader(io.StringIO(csv_texto.lstrip("\ufeff"))))
    assert len(filas) == 40
    assert set(filas[0]) == {"serie", "unidad", "pais_o_referencia", "anio", "valor", "bandera", "calidad"}
    nacionales = [f for f in filas if f["pais_o_referencia"] in datos[codigo]["paises"]]
    assert len(nacionales) == 30
    for fila in nacionales:
        pais, i = fila["pais_o_referencia"], int(fila["anio"]) - 2020
        assert float(fila["valor"]) == datos[codigo]["paises"][pais][i]
        marca = ("*" if datos["imputados"][pais][i] else "") if codigo == "ECO14" else datos[codigo]["banderas"][pais][i]
        assert fila["bandera"] == marca
        assert fila["calidad"]
    assert sum(bool(f["bandera"]) for f in nacionales) == (13 if codigo == "ECO14" else 3)
    tabla = ejecutar_js(f"tablaSerie(infoSerie('{codigo}'), DATOS['{codigo}'], principal('{codigo}', DATOS['{codigo}']))")
    assert tabla.count("<sup ") == (13 if codigo == "ECO14" else 3)
    leyenda = ejecutar_js(f"notaCalidad('{codigo}')")
    tarjeta = ejecutar_js(f"referenciaTarjeta('{codigo}')")
    if codigo == "ECO14":
        assert "El Salvador: 2022, 2023, 2024" in leyenda
        assert "6/6 países imputados" in tarjeta
        assert next(f for f in nacionales if f["pais_o_referencia"] == "El Salvador" and f["anio"] == "2022")["bandera"] == "*"
        assert next(f for f in nacionales if f["pais_o_referencia"] == "El Salvador" and f["anio"] == "2021")["calidad"] == "Observado"
    else:
        assert "proxy parcial de seis meses" in leyenda
        assert "2 países con bandera" in tarjeta
        for pais, anio, marca in [("Honduras", "2020", "*"), ("Costa Rica", "2024", "†"), ("El Salvador", "2024", "‡")]:
            fila = next(f for f in nacionales if f["pais_o_referencia"] == pais and f["anio"] == anio)
            assert fila["bandera"] == marca
            assert marca in fila["calidad"]


def test_presentacion_sigue_banderas_del_paquete_sin_reconstruirlas(ejecutar_js):
    resultado = ejecutar_js("(() => { DATOS.imputados['El Salvador'][2]=false; DATOS.ECO_CG.banderas['Costa Rica'][4]=''; return [calidadDato('ECO14','El Salvador',2),calidadDato('ECO_CG','Costa Rica',4)]; })()")
    assert resultado[0] == {"bandera": "", "calidad": "Observado"}
    assert resultado[1]["bandera"] == ""


@pytest.mark.parametrize("indice", [0, 1])
def test_env6_etiqueta_grafico_metadatos_y_exportacion(ejecutar_js, indice):
    resultado = ejecutar_js("(() => { const inf=infoSerie('ENV6', " + str(indice) + "); const b=DATOS[inf.clave],p=principal('ENV6',b); return {csv:contenidoCSV('ENV6',inf,b,p),resumen:resumenAccesible(p,inf,b),leyenda:metaGraficoRegion(inf,p,'ENV6')}; })()")
    for texto in resultado.values():
        assert "Suma regional" in texto
        assert "razón de sumas" not in texto


@pytest.mark.parametrize("nombre", ["ENVs.xlsx", "SOCs.xlsx"])
def test_fuentes_publicas_sin_rutas_locales(nombre, raiz_resultados):
    with zipfile.ZipFile(raiz_resultados / "data" / "raw_equipo" / nombre) as libro:
        for miembro in libro.namelist():
            if miembro.endswith((".xml", ".rels")):
                xml = libro.read(miembro)
                assert b"absPath" not in xml, miembro
                assert not re.search(rb"[A-Za-z]:[\\/](?:Users|proyectos)[\\/]|file:///|/Users/|/home/", xml), miembro


@pytest.mark.parametrize("codigo", ["ECO14", "ECO_CG"])
def test_descarga_real_conserva_csv_y_banderas(ejecutar_js, codigo):
    resultado = ejecutar_js("""(async () => {
      const cod=""" + json.dumps(codigo) + """, inf=infoSerie(cod), b=DATOS[cod], p=principal(cod,b);
      let blob, pulsado=false, revocado=false;
      const enlace={click(){pulsado=true;}};
      globalThis.window={_csv:{cod,inf,b,p}};
      globalThis.document={createElement(){return enlace;}};
      globalThis.URL={createObjectURL(valor){blob=valor;return 'blob:prueba';},revokeObjectURL(){revocado=true;}};
      descargarCSV();
      return {contenido:await blob.text(),esperado:contenidoCSV(cod,inf,b,p),nombre:enlace.download,pulsado,revocado};
    })()""")
    assert resultado["contenido"].lstrip("\ufeff") == resultado["esperado"].lstrip("\ufeff")
    assert resultado["nombre"] == f"{codigo}_SIEPAC_2020_2024.csv"
    assert resultado["pulsado"] and resultado["revocado"]
    assert '"bandera","calidad"' in resultado["contenido"]


@pytest.mark.parametrize("indice", [0, 1])
def test_traza_env6_del_grafico_es_suma_regional(ejecutar_js, referencia, indice):
    resultado = ejecutar_js("""(() => {
      const inf=infoSerie('ENV6',""" + str(indice) + """),b=DATOS[inf.clave],p=principal('ENV6',b);
      let trazas; const panel={innerHTML:'',insertAdjacentHTML(){}};
      globalThis.document={getElementById(){return panel;}};
      globalThis.CONSULTA_MOVIL={matches:false};
      globalThis.Plotly={newPlot(id,tr){trazas=tr;}};
      vistaRegion('ENV6',FICHAS.ENV6,inf,b,p);
      return {nombre:trazas.at(-1).name,valores:trazas.at(-1).y,html:panel.innerHTML};
    })()""")
    assert resultado["nombre"] == "Suma regional"
    clave = ["ENV6_BIOMASA", "ENV6_SALDO"][indice]
    assert resultado["valores"] == referencia["web"]["datos"][clave]["agregado"]
    assert "razón de sumas" not in resultado["html"]
