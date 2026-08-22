"""
generar_visualizador.py — Visualizador regional único del SIEPAC
====================================================
Etapa del pipeline : visualización y comunicación de resultados
Entradas           : matrices de indicadores en data/processed/,
                     data/raw_equipo/eco_cg_siepac.csv, figuras y tablas de
                     salidas/tesis/
Salidas            : graficos/visualizador_siepac.html
Alimenta           : consulta pública y defensa de la monografía
Fuente de datos    : salidas validadas del pipeline; fichas en viz_comun.py

Genera una aplicación HTML autocontenida y orientada primero al bloque
regional. Reúne resumen, comparación entre países, datos y metodología sin
duplicar cifras o fórmulas fuera de sus fuentes canónicas.

Uso:  python src/generar_visualizador.py   (desde la raíz del proyecto)

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

from copy import deepcopy
import json
import logging
import sys
from pathlib import Path

import pandas as pd
import plotly.offline as pyo

from config_siepac import (ANIOS_ANALISIS as ANIOS, DIR_GRAFICOS,
                           DIR_SALIDAS_TESIS, PAISES_SIEPAC as PAISES)
from eco_cg_comun import (CODIGO_ECO_CG, FICHA_ECO_CG, cargar_eco_cg,
                          serie_mediana_eco_cg)
from viz_comun import (COLORES_PAIS, FICHAS, cargar_datos,
                       construir_datos_json, leer_series_extra,
                       preparar_datos)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

RUTA_SALIDA = DIR_GRAFICOS / "visualizador_siepac.html"
DIR_FIGURAS = DIR_SALIDAS_TESIS / "figuras"
RUTA_TABLAS = DIR_SALIDAS_TESIS / "tablas" / "indice_tablas.csv"


def _serie_eco_cg() -> dict:
    """Empaqueta ECO-CG como comparación descriptiva, nunca como agregado."""
    datos = cargar_eco_cg()
    pivote = (datos.pivot(index="anio", columns="pais", values=CODIGO_ECO_CG)
              .reindex(index=ANIOS, columns=PAISES))
    return {
        "paises": {
            pais: [round(float(valor), 6) for valor in pivote[pais]]
            for pais in PAISES
        },
        "promedio": [round(float(valor), 6)
                     for valor in pivote.mean(axis=1)],
        "mediana": [round(float(valor), 6)
                    for valor in serie_mediana_eco_cg(datos)],
        "agregado": None,
        "banderas": {
            pais: [str(valor) for valor in
                   datos[datos["pais"] == pais].sort_values("anio")["bandera"]]
            for pais in PAISES
        },
    }


def _normalizar_env6(paquete: dict) -> None:
    """Convierte las dos magnitudes ENV6 al contrato común de la interfaz."""
    origen = paquete.pop("ENV6")
    for destino, clave in (("ENV6_BIOMASA", "biomasa"),
                           ("ENV6_SALDO", "saldo")):
        paises = {pais: origen[pais][clave] for pais in PAISES}
        marco = pd.DataFrame(paises, index=ANIOS)
        paquete[destino] = {
            "paises": paises,
            "promedio": [round(float(v), 6) for v in marco.mean(axis=1)],
            "agregado": [round(float(v), 6) for v in marco.sum(axis=1)],
        }


def _fichas_visualizador() -> dict:
    """Extiende las fichas canónicas solo con metadatos propios de la UI."""
    fichas = deepcopy(FICHAS)
    fichas["ENV6"]["series"] = [
        ["ENV6_BIOMASA", "Inyección de biomasa", ",.1f", " GWh", "GWh",
         "Suma de la inyección de biomasa observada en los seis países"],
        ["ENV6_SALDO", "Saldo neto en el MER", ",.1f", " GWh", "GWh",
         "Suma de los saldos netos observados de los seis países"],
    ]
    ficha_cg = deepcopy(FICHA_ECO_CG)
    ficha_cg.update(tipo="eco_cg", complementaria=True)
    fichas[CODIGO_ECO_CG] = ficha_cg
    return fichas


def _enlaces_salidas(fichas: dict) -> dict:
    """Relaciona series con archivos oficiales sin generar un manifiesto."""
    if not RUTA_TABLAS.exists():
        raise FileNotFoundError(
            "VALIDACIÓN FALLIDA: genere antes las figuras y tablas APA")

    archivos_figura = {}
    for codigo, ficha in fichas.items():
        if codigo == "ENV6":
            archivos_figura.update({
                "ENV6": "ENV6_bloque.png",
                "ENV6_BIOMASA": "ENV6_bloque.png",
                "ENV6_SALDO": "ENV6_bloque.png",
            })
        elif ficha.get("series"):
            archivos_figura.update({
                serie[0]: f"{serie[0]}_bloque.png"
                for serie in ficha["series"]
            })
        else:
            archivos_figura[codigo] = f"{codigo}_bloque.png"

    faltantes = sorted({nombre for nombre in archivos_figura.values()
                        if not (DIR_FIGURAS / nombre).exists()})
    if faltantes:
        raise FileNotFoundError(
            "VALIDACIÓN FALLIDA: faltan figuras oficiales: " +
            ", ".join(faltantes))
    enlaces_figuras = {
        codigo: f"../salidas/tesis/figuras/{archivo}"
        for codigo, archivo in archivos_figura.items()
    }

    tablas = pd.read_csv(RUTA_TABLAS)
    claves_tabla = {
        serie[0] for codigo, ficha in fichas.items()
        if codigo != CODIGO_ECO_CG
        for serie in (ficha.get("series") or [[codigo]])
    }
    claves_tabla.add("ENV6")
    enlaces_tablas = {
        str(fila.codigo): f"../salidas/tesis/tablas/{fila.archivo}"
        for fila in tablas.itertuples(index=False)
        if str(fila.codigo) in claves_tabla
    }
    fila_cg = tablas[tablas["codigo"] == "eco_cg_usd_mwh"]
    if not fila_cg.empty:
        enlaces_tablas[CODIGO_ECO_CG] = (
            f"../salidas/tesis/tablas/{fila_cg.iloc[0]['archivo']}")
    return {"figuras": enlaces_figuras, "tablas": enlaces_tablas}


def _validar(paquete: dict, fichas: dict, enlaces: dict) -> None:
    """Detiene la publicación si falta una serie, país, año o figura."""
    if len(FICHAS) != 15:
        raise ValueError(
            f"VALIDACIÓN FALLIDA: se esperaban 15 IEDS; hay {len(FICHAS)}")

    claves = []
    for codigo, ficha in fichas.items():
        series = ficha.get("series") or [[codigo]]
        claves.extend(serie[0] for serie in series)
    errores = []
    sin_hallazgo = sorted(
        codigo for codigo, ficha in fichas.items()
        if not str(ficha.get("hallazgo_regional", "")).strip()
    )
    if sin_hallazgo:
        errores.append(f"hallazgos regionales ausentes: {sin_hallazgo}")
    for clave in claves:
        bloque = paquete.get(clave)
        if bloque is None:
            errores.append(f"serie ausente: {clave}")
            continue
        if set(bloque.get("paises", {})) != set(PAISES):
            errores.append(f"cobertura de países incompleta: {clave}")
            continue
        if any(len(bloque["paises"][pais]) != len(ANIOS) for pais in PAISES):
            errores.append(f"cobertura temporal incompleta: {clave}")

    figuras_requeridas = {
        serie[0] for ficha in fichas.values()
        for serie in (ficha.get("series") or [[]]) if serie
    }
    figuras_requeridas.update(
        codigo for codigo, ficha in fichas.items() if not ficha.get("series"))
    # ENV6 tiene una figura conjunta para sus dos magnitudes.
    figuras_requeridas.difference_update({"ENV6_BIOMASA", "ENV6_SALDO"})
    figuras_requeridas.add("ENV6")
    sin_figura = sorted(figuras_requeridas - set(enlaces["figuras"]))
    if sin_figura:
        errores.append(f"figuras no inventariadas: {sin_figura}")
    if errores:
        raise ValueError("VALIDACIÓN FALLIDA: " + "; ".join(errores))


def _sanear_plotly_js(codigo: str) -> str:
    """Escapa los dos controles C0 incluidos por Plotly antes de publicar."""
    return codigo.replace("\x01", r"\x01").replace("\x1a", r"\x1a")


PLANTILLA = r'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#173f64">
<meta name="description" content="Indicadores regionales económicos, sociales y ambientales del SIEPAC, 2020–2024.">
<title>Visualizador regional SIEPAC · 2020–2024</title>
<script>__PLOTLYJS__</script>
<style>
  :root {
    --azul:#173f64; --azul-2:#1f4e79; --naranja:#c85d22;
    --tinta:#17212b; --gris:#5f6b76; --borde:#dce2e7;
    --papel:#f7f8f6; --blanco:#fff; --banda:rgba(95,107,118,.16);
    --eco:#1f4e79; --soc:#8a4f7d; --env:#287a68;
    --sombra:0 12px 32px rgba(23,33,43,.08);
  }
  * { box-sizing:border-box; }
  html { scroll-behavior:smooth; }
  body { margin:0; background:var(--papel); color:var(--tinta);
    font-family:"Segoe UI",system-ui,-apple-system,sans-serif; }
  button,input,select { font:inherit; }
  button,a,select,input { touch-action:manipulation; }
  button { cursor:pointer; -webkit-tap-highlight-color:transparent; }
  a { color:var(--azul-2); }
  :focus-visible { outline:3px solid #f2a65a; outline-offset:3px; }
  .skip { position:absolute; left:-9999px; top:8px; z-index:100; }
  .skip:focus { left:12px; background:#fff; padding:10px 14px; }
  header { position:sticky; top:0; z-index:20; background:rgba(255,255,255,.96);
    border-bottom:1px solid var(--borde); backdrop-filter:blur(10px); }
  .top { max-width:1240px; height:68px; margin:auto; padding:0 24px;
    display:flex; align-items:center; gap:26px; }
  .brand { border:0; background:none; color:var(--tinta); padding:0;
    display:flex; align-items:center; gap:10px; font-weight:800; }
  .brand-mark { width:34px; height:34px; border-radius:10px;
    display:grid; place-items:center; background:var(--azul); color:#fff; }
  nav { display:flex; gap:4px; overflow-x:auto; flex:1; min-width:0;
    scrollbar-width:none; }
  nav::-webkit-scrollbar,.tabs::-webkit-scrollbar { display:none; }
  nav button { border:0; background:none; border-radius:999px; color:var(--gris);
    padding:9px 14px; white-space:nowrap; font-size:14px; font-weight:650; }
  nav button:hover,nav button.on { background:#edf2f5; color:var(--azul); }
  .periodo { color:var(--gris); font-size:13px; white-space:nowrap; }
  main { max-width:1240px; margin:auto; min-height:78vh; padding:0 24px 72px;
    scroll-margin-top:76px; }
  .hero { padding:68px 0 38px; display:grid; grid-template-columns:1.45fr .75fr;
    gap:48px; align-items:end; }
  .eyebrow { color:var(--naranja); text-transform:uppercase; letter-spacing:.12em;
    font-size:12px; font-weight:800; }
  h1 { margin:10px 0 0; max-width:780px; font-family:Georgia,serif;
    font-size:clamp(36px,5vw,64px); line-height:1.03; letter-spacing:-.035em; }
  .hero p { color:var(--gris); max-width:720px; font-size:17px; line-height:1.65; }
  .hero-stats { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
  .stat { background:#fff; border:1px solid var(--borde); border-radius:14px;
    padding:16px; box-shadow:0 2px 8px rgba(23,33,43,.04); }
  .stat b { display:block; color:var(--azul); font:700 27px Georgia,serif; }
  .stat span { color:var(--gris); font-size:12px; }
  .callout { border-left:4px solid var(--naranja); background:#fff8f2;
    border-radius:0 12px 12px 0; padding:14px 18px; color:#673417;
    line-height:1.5; font-size:14px; }
  .tools { margin:42px 0 18px; display:flex; align-items:end;
    justify-content:space-between; gap:18px; }
  .tools h2,.section-title { margin:0; font:700 27px Georgia,serif; }
  .tools p { color:var(--gris); margin:5px 0 0; }
  .search { min-width:260px; border:1px solid var(--borde); border-radius:10px;
    background:#fff; padding:10px 12px; color:var(--tinta); }
  .dimension { margin-top:34px; }
  .dimension-head { display:flex; align-items:center; gap:10px; margin-bottom:14px; }
  .dimension-head i { width:11px; height:11px; border-radius:50%; }
  .dimension-head h2 { margin:0; font-size:19px; }
  .dimension-head span { color:var(--gris); font-size:13px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr));
    gap:15px; }
  .card { text-align:left; border:1px solid var(--borde); background:#fff;
    border-radius:15px; padding:18px; min-height:176px; color:var(--tinta);
    transition:transform .16s,box-shadow .16s,border-color .16s; }
  .card:hover { transform:translateY(-2px); box-shadow:var(--sombra);
    border-color:#b8c6d1; }
  .card-top { display:flex; justify-content:space-between; gap:12px; }
  .code { color:var(--azul-2); font-size:12px; font-weight:850;
    letter-spacing:.06em; }
  .tag { color:var(--gris); background:#f0f3f5; padding:3px 7px;
    border-radius:999px; font-size:10px; }
  .card h3 { margin:13px 0 5px; font-size:16px; line-height:1.3; }
  .card p { margin:0; color:var(--gris); font-size:12px; line-height:1.45; }
  .card-value { margin-top:15px; display:flex; align-items:baseline; gap:6px; }
  .card-value b { font:700 23px Georgia,serif; }
  .card-value small { color:var(--gris); }
  .complemento { margin-top:44px; padding-top:26px; border-top:1px solid var(--borde); }
  .back { border:0; background:none; color:var(--azul-2); padding:30px 0 8px;
    font-weight:700; }
  .detail-head { padding:18px 0 24px; display:grid;
    grid-template-columns:1fr auto; gap:32px; align-items:end; }
  .detail-head h1 { font-size:clamp(30px,4vw,49px); }
  .detail-head p { color:var(--gris); max-width:780px; line-height:1.6; }
  .selector { border:1px solid var(--borde); border-radius:10px; background:#fff;
    padding:10px 12px; min-width:220px; }
  .tabs { display:flex; gap:5px; border-bottom:1px solid var(--borde);
    margin-bottom:22px; overflow-x:auto; }
  .tabs button { border:0; border-bottom:3px solid transparent; background:none;
    color:var(--gris); padding:12px 15px; white-space:nowrap; font-weight:700; }
  .tabs button.on { color:var(--azul); border-bottom-color:var(--naranja); }
  .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px;
    margin-bottom:18px; }
  .kpi { background:#fff; border:1px solid var(--borde); border-radius:13px;
    padding:15px 17px; }
  .kpi span { color:var(--gris); font-size:12px; }
  .kpi b { display:block; margin-top:5px; font:700 23px Georgia,serif; }
  .panel { background:#fff; border:1px solid var(--borde); border-radius:16px;
    padding:18px; box-shadow:0 2px 8px rgba(23,33,43,.035); }
  #chart { width:100%; height:520px; }
  .chart-mobile-meta { display:none; }
  .chart-unit { color:var(--gris); font-size:12px; font-weight:750; }
  .chart-legend-mobile { display:flex; flex-wrap:wrap; gap:9px 14px; }
  .legend-item { display:flex; align-items:center; gap:7px; color:var(--gris);
    font-size:12px; line-height:1.25; }
  .legend-swatch { width:22px; height:3px; border-radius:999px;
    flex:0 0 auto; background:var(--azul-2); }
  .legend-swatch.dashed { height:0; border-top:2px dashed #7b8791;
    background:none; }
  .legend-swatch.band { height:10px; border-radius:2px;
    background:var(--banda); }
  .chart-summary { margin:10px 4px 0; color:var(--gris); line-height:1.55;
    font-size:13px; }
  .finding { margin:16px 4px 2px; border-left:4px solid var(--azul-2);
    background:#eef4f8; border-radius:0 11px 11px 0; padding:13px 16px;
    color:#20384c; font-size:15px; line-height:1.55; }
  .note { margin-top:16px; border-left:3px solid var(--naranja);
    background:#fff8f2; padding:12px 15px; color:#673417; line-height:1.5; }
  .method-grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
  .method-card { background:#fff; border:1px solid var(--borde); border-radius:14px;
    padding:18px; }
  .method-card h3 { margin:0 0 8px; font-size:15px; }
  .method-card p { color:var(--gris); line-height:1.55; margin:5px 0; }
  .links { display:flex; gap:10px; flex-wrap:wrap; margin-top:16px; }
  .link-btn,.download { display:inline-block; border:1px solid var(--azul);
    border-radius:9px; padding:9px 13px; background:#fff; color:var(--azul);
    font-weight:700; text-decoration:none; }
  .print-note { align-self:center; color:var(--gris); font-size:12px; }
  .brand,nav button,.tabs button,.back,.selector,.search,.link-btn,.download {
    min-height:44px; }
  .download { background:var(--azul); color:#fff; }
  .table-wrap { overflow:auto; max-height:480px; margin-top:16px;
    border:1px solid var(--borde); border-radius:12px; }
  table { border-collapse:collapse; width:100%; background:#fff; font-size:13px; }
  th,td { padding:9px 11px; border-bottom:1px solid var(--borde);
    text-align:right; white-space:nowrap; }
  th { position:sticky; top:0; background:var(--azul); color:#fff; z-index:1; }
  th:first-child,td:first-child { text-align:left; position:sticky; left:0; }
  td:first-child { background:#fff; font-weight:600; }
  tr.summary td { background:#eef3f6; font-weight:750; }
  .methodology { padding:62px 0 30px; }
  .methodology > p { max-width:800px; color:var(--gris); line-height:1.65; }
  footer { background:var(--azul); color:#dce7ef; }
  .footer-in { max-width:1240px; margin:auto; padding:30px 24px;
    display:flex; justify-content:space-between; gap:30px; font-size:13px; }
  .footer-in strong { color:#fff; }
  .empty { padding:30px; color:var(--gris); text-align:center; }
  @media (max-width:1000px) {
    .hero { grid-template-columns:1fr; gap:28px; padding-top:52px; }
  }
  @media (max-width:800px) {
    .top { padding:0 14px; gap:12px; } .brand span:last-child,.periodo { display:none; }
    main { padding:0 14px 56px; } .hero { padding-top:44px; }
    .tools { align-items:stretch; flex-direction:column; } .search { min-width:0; width:100%; }
    .detail-head { grid-template-columns:1fr; } .selector { width:100%; }
    .method-grid { grid-template-columns:1fr; }
    nav.hay-mas { -webkit-mask-image:linear-gradient(to right,#000 0,#000 calc(100% - 30px),transparent);
      mask-image:linear-gradient(to right,#000 0,#000 calc(100% - 30px),transparent); }
    nav.hay-previo:not(.hay-mas) { -webkit-mask-image:linear-gradient(to right,transparent,#000 30px,#000 100%);
      mask-image:linear-gradient(to right,transparent,#000 30px,#000 100%); }
    nav.hay-previo.hay-mas { -webkit-mask-image:linear-gradient(to right,transparent,#000 30px,#000 calc(100% - 30px),transparent);
      mask-image:linear-gradient(to right,transparent,#000 30px,#000 calc(100% - 30px),transparent); }
  }
  @media (max-width:640px) {
    .grid,.kpis { grid-template-columns:1fr; }
    .panel { padding:10px; }
    #chart { height:360px; }
    .chart-mobile-meta { display:grid; gap:11px; padding:2px 8px 10px; }
    .finding { font-size:14px; }
    .detail-head h1 { font-size:clamp(29px,9vw,40px); }
    .footer-in { flex-direction:column; }
  }
  @media (max-width:420px) {
    .top { height:64px; }
    .hero-stats { grid-template-columns:1fr; }
    h1 { font-size:clamp(32px,11vw,42px); }
  }
  @media (max-height:500px) and (orientation:landscape) {
    header { position:static; }
    .hero { padding-top:30px; }
    #chart { height:320px; }
  }
  @media (prefers-reduced-motion:reduce) {
    html { scroll-behavior:auto; }
    .card { transition:none; }
  }
</style>
</head>
<body>
<a class="skip" href="#app">Saltar al contenido principal</a>
<header>
  <div class="top">
    <button class="brand" onclick="mostrarInicio('all')" aria-label="Ir al inicio">
      <span class="brand-mark" aria-hidden="true">S</span>
      <span>SIEPAC · Indicadores</span>
    </button>
    <nav aria-label="Dimensiones">
      <button data-dim="all" onclick="mostrarInicio('all')">Inicio</button>
      <button data-dim="eco" onclick="mostrarInicio('eco')">Económica</button>
      <button data-dim="soc" onclick="mostrarInicio('soc')">Social</button>
      <button data-dim="env" onclick="mostrarInicio('env')">Ambiental</button>
      <button data-dim="metodo" onclick="mostrarMetodo()">Metodología</button>
    </nav>
    <span class="periodo">2020–2024</span>
  </div>
</header>
<main id="app" tabindex="-1"></main>
<footer>
  <div class="footer-in">
    <div><strong>Tesis SIEPAC · UNI Nicaragua</strong><br>Fase cuantitativa trazable y reproducible con acceso a las fuentes</div>
    <div>Luis Giovanni Serrano Bello · Mariángeles Aracelly Olivares López<br>Jonathan Noel García Mendoza</div>
  </div>
</footer>
<script>
const DATOS=__DATOS__, FICHAS=__FICHAS__, ANIOS=__ANIOS__, PAISES=__PAISES__;
const COLORES=__COLORES__, SALIDAS=__SALIDAS__;
const DIMS={eco:["Económica","Costos, estructura y eficiencia","var(--eco)"],
  soc:["Social","Acceso, asequibilidad y equidad","var(--soc)"],
  env:["Ambiental","Emisiones y desempeño ambiental","var(--env)"]};
let estado={codigo:null,serie:0,vista:"region",filtro:"all"};
const app=document.getElementById("app");
const navPrincipal=document.querySelector("nav");
const VISTAS=[["region","Región"],["paises","Países"],["datos","Datos y método"]];
const CONSULTA_MOVIL=window.matchMedia("(max-width:640px)");

function esc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));}
function decimales(fmt){const m=String(fmt||"").match(/\.(\d+)f/);return m?+m[1]:2;}
function num(v,fmt){if(v===null||v===undefined||Number.isNaN(+v))return "s.d.";
  return (+v).toLocaleString("es-NI",{minimumFractionDigits:decimales(fmt),maximumFractionDigits:decimales(fmt)});}
function infoSerie(cod,idx=0){const f=FICHAS[cod];if(f.series){const s=f.series[Math.min(idx,f.series.length-1)];
  return {clave:s[0],etiqueta:s[1],formato:s[2],sufijo:s[3],unidad:s[4],formula:s[5]};}
  return {clave:cod,etiqueta:"",formato:f.formato,sufijo:f.sufijo,unidad:f.unidad,formula:f.formula};}
function mediana(vals){const a=vals.filter(v=>v!==null).map(Number).sort((x,y)=>x-y);const n=a.length;
  return n? (n%2?a[(n-1)/2]:(a[n/2-1]+a[n/2])/2):null;}
function serieMediana(b){return ANIOS.map((_,i)=>mediana(PAISES.map(p=>b.paises[p][i])));}
function principal(cod,b){if(cod==="ECO14")return {valores:serieMediana(b),etiqueta:"Mediana de países (sin ponderador)"};
  if(cod==="ECO_CG")return {valores:b.mediana,etiqueta:"Mediana de proxies nacionales"};
  if(b.agregado)return {valores:b.agregado,etiqueta:"Agregado regional (razón de sumas)"};
  return {valores:b.promedio,etiqueta:"Promedio de países (media simple)"};}
function actualizarPistaNav(){const previo=navPrincipal.scrollLeft>2;
  const mas=navPrincipal.scrollLeft+navPrincipal.clientWidth<navPrincipal.scrollWidth-2;
  navPrincipal.classList.toggle("hay-previo",previo);navPrincipal.classList.toggle("hay-mas",mas);}
function activarNav(dim){let activo=null;document.querySelectorAll("nav button").forEach(b=>{const on=b.dataset.dim===dim;
  b.classList.toggle("on",on);if(on){b.setAttribute("aria-current","page");activo=b;}else b.removeAttribute("aria-current");});
  if(activo)requestAnimationFrame(()=>{activo.scrollIntoView({block:"nearest",inline:"nearest"});actualizarPistaNav();});}
function valorTarjeta(cod){const inf=infoSerie(cod,0),b=DATOS[inf.clave],p=principal(cod,b);
  return num(p.valores.at(-1),inf.formato)+(inf.sufijo||"");}
function etiquetaCodigo(c){return c==="ECO_CG"?"ECO-CG":c;}

function tarjeta(cod){const f=FICHAS[cod];return `<button class="card" data-search="${esc((cod+" "+f.nombre+" "+f.descripcion).toLowerCase())}"
  onclick="abrirDetalle('${cod}')" aria-label="Abrir ${esc(etiquetaCodigo(cod)+" "+f.nombre)}">
  <div class="card-top"><span class="code">${esc(etiquetaCodigo(cod))}</span>${f.complementaria?'<span class="tag">Serie complementaria</span>':""}</div>
  <h3>${esc(f.nombre)}</h3><p>${esc(f.descripcion)}</p>
  <div class="card-value"><b>${esc(valorTarjeta(cod))}</b><small>referencia 2024</small></div></button>`;}
function bloqueDimension(dim,cods){if(!cods.length)return "";const d=DIMS[dim];return `<section class="dimension" data-section="${dim}">
  <div class="dimension-head"><i style="background:${d[2]}"></i><h2>${d[0]}</h2><span>${d[1]}</span></div>
  <div class="grid">${cods.map(tarjeta).join("")}</div></section>`;}

function mostrarInicio(filtro="all") {estado={codigo:null,serie:0,vista:"region",filtro};activarNav(filtro);
  const ieds=Object.keys(FICHAS).filter(c=>c!=="ECO_CG");
  const dims=["eco","soc","env"].filter(d=>filtro==="all"||filtro===d);
  app.innerHTML=`<section class="hero"><div><div class="eyebrow">Evaluación regional 2020–2024</div>
    <h1>El SIEPAC como sistema, sin perder de vista sus países.</h1>
    <p>Explore los Indicadores Energéticos de Desarrollo Sostenible con la medida regional correcta, el promedio del país típico y la dispersión entre los seis países.</p>
    <div class="callout"><strong>Dos referencias distintas:</strong> el agregado regional es una razón de sumas; el promedio de países asigna el mismo peso a cada nación.</div></div>
    <div class="hero-stats"><div class="stat"><b>15</b><span>indicadores IEDS</span></div><div class="stat"><b>21</b><span>salidas cuantitativas</span></div><div class="stat"><b>6</b><span>países interconectados</span></div><div class="stat"><b>5</b><span>años de análisis</span></div></div></section>
    <div class="tools"><div><h2>Indicadores</h2><p>Seleccione una tarjeta para consultar región, países, datos y método.</p></div>
    <input id="busqueda" class="search" type="search" placeholder="Buscar indicador o tema" aria-label="Buscar indicador"></div>
    <div id="catalogo">${dims.map(d=>bloqueDimension(d,ieds.filter(c=>FICHAS[c].dim===d))).join("")}
    ${(filtro==="all"||filtro==="eco")?`<section class="complemento"><div class="dimension-head"><i style="background:var(--naranja)"></i><h2>Serie económica complementaria</h2></div><div class="grid">${tarjeta("ECO_CG")}</div></section>`:""}</div>`;
  const q=document.getElementById("busqueda");q.addEventListener("input",()=>{const s=q.value.trim().toLowerCase();
    document.querySelectorAll(".card").forEach(c=>c.hidden=s&&!c.dataset.search.includes(s));
    document.querySelectorAll(".dimension,.complemento").forEach(sec=>sec.hidden=!sec.querySelector(".card:not([hidden])"));});
  app.focus();window.scrollTo(0,0);
}

function abrirDetalle(cod){estado.codigo=cod;estado.serie=0;estado.vista="region";activarNav(FICHAS[cod].dim);renderDetalle();}
function elegirSerie(i){estado.serie=+i;renderDetalle();}
function elegirVista(v,enfocar=false){estado.vista=v;renderDetalle();
  if(enfocar)requestAnimationFrame(()=>document.getElementById(`tab-${v}`)?.focus());}
function navegarTabs(e){const teclas=["ArrowLeft","ArrowRight","Home","End"];
  if(!teclas.includes(e.key))return;e.preventDefault();let i=VISTAS.findIndex(x=>x[0]===estado.vista);
  if(e.key==="Home")i=0;else if(e.key==="End")i=VISTAS.length-1;
  else i=(i+(e.key==="ArrowRight"?1:-1)+VISTAS.length)%VISTAS.length;
  elegirVista(VISTAS[i][0],true);}
function cambio(vals,tipo){const a=vals[0],b=vals.at(-1);if(a===null||b===null||a===0)return "s.d.";
  return tipo==="pp"?`${(b-a>=0?"+":"")}${num(b-a,".1f")} pp`:`${(b/a-1>=0?"+":"")}${num((b/a-1)*100,".1f")}%`;}
function rango2024(b,fmt,suf){const v=PAISES.map(p=>b.paises[p].at(-1)).filter(x=>x!==null);
  return `${num(Math.min(...v),fmt)}–${num(Math.max(...v),fmt)}${suf||""}`;}
function esMovil(){return CONSULTA_MOVIL.matches;}
function itemLeyenda(etiqueta,clase="",color=""){return `<span class="legend-item"><i class="legend-swatch ${clase}" ${color?`style="background:${color}"`:""}></i>${esc(etiqueta)}</span>`;}
function metaGraficoRegion(inf,p,cod){const color=cod==="ECO_CG"?"#c85d22":"#1f4e79";return `<div class="chart-mobile-meta">
  <span class="chart-unit">Unidad: ${esc(inf.unidad)}</span><div class="chart-legend-mobile" aria-label="Leyenda del gráfico">
  ${itemLeyenda(p.etiqueta,"",color)}${itemLeyenda("Promedio de países","dashed")}${itemLeyenda("Rango mínimo–máximo","band")}</div></div>`;}
function metaGraficoPaises(inf){return `<div class="chart-mobile-meta"><span class="chart-unit">Unidad: ${esc(inf.unidad)}</span>
  <div class="chart-legend-mobile" aria-label="Leyenda del gráfico">${PAISES.map(p=>itemLeyenda(p,"",COLORES[p])).join("")}</div></div>`;}

function renderDetalle(){const cod=estado.codigo,f=FICHAS[cod],inf=infoSerie(cod,estado.serie),b=DATOS[inf.clave],p=principal(cod,b);
  const opciones=f.series&&f.series.length>1?`<label>Serie<br><select class="selector" onchange="elegirSerie(this.value)">${f.series.map((s,i)=>`<option value="${i}" ${i===estado.serie?"selected":""}>${esc(s[1])}</option>`).join("")}</select></label>`:"";
  app.innerHTML=`<button class="back" onclick="mostrarInicio('${f.dim}')">← Volver a indicadores</button>
    <section class="detail-head"><div><div class="eyebrow">${esc(etiquetaCodigo(cod))} · ${esc(DIMS[f.dim][0])}</div><h1>${esc(f.nombre)}</h1>
    <p>${esc(f.descripcion)}</p></div>${opciones}</section>
    <div class="tabs" role="tablist" aria-label="Vistas del indicador" onkeydown="navegarTabs(event)">
      ${VISTAS.map(x=>`<button id="tab-${x[0]}" role="tab" aria-selected="${estado.vista===x[0]}" aria-controls="vista" tabindex="${estado.vista===x[0]?0:-1}" class="${estado.vista===x[0]?"on":""}" onclick="elegirVista('${x[0]}',true)">${x[1]}</button>`).join("")}</div>
    <section id="vista" role="tabpanel" aria-labelledby="tab-${estado.vista}" tabindex="0"></section>`;
  if(estado.vista==="region")vistaRegion(cod,f,inf,b,p);else if(estado.vista==="paises")vistaPaises(cod,f,inf,b,p);else vistaDatos(cod,f,inf,b,p);
  window.scrollTo(0,0);
}

function kpis(cod,f,inf,b,p){return `<div class="kpis"><div class="kpi"><span>${esc(p.etiqueta)} · 2024</span><b>${num(p.valores.at(-1),inf.formato)}${esc(inf.sufijo)}</b></div>
  <div class="kpi"><span>Cambio 2020–2024</span><b>${cambio(p.valores,f.delta)}</b></div>
  <div class="kpi"><span>Mínimo–máximo entre países · 2024</span><b>${rango2024(b,inf.formato,inf.sufijo)}</b></div></div>`;}
function baseLayout(inf,vista){const movil=esMovil();
  return {paper_bgcolor:"#fff",plot_bgcolor:"#fff",font:{family:"Segoe UI, sans-serif",color:"#17212b",size:movil?11:13},
    margin:movil?{l:48,r:8,t:14,b:36}:{l:96,r:28,t:28,b:80},hovermode:"x unified",showlegend:!movil,
    legend:{orientation:"h",y:-.18,x:.5,xanchor:"center"},
    xaxis:{tickvals:ANIOS,gridcolor:"#f1f3f4",fixedrange:true,tickfont:{size:movil?10:12}},
    yaxis:{gridcolor:"#e7ebee",ticksuffix:movil?"":inf.sufijo,zerolinecolor:"#9aa4ad",fixedrange:true,automargin:true,tickfont:{size:movil?10:12}}};}
const plotCfg={responsive:true,displaylogo:false,displayModeBar:false,scrollZoom:false};
function extremos(b){return ANIOS.map((_,i)=>{const v=PAISES.map(p=>b.paises[p][i]).filter(x=>x!==null);return [Math.min(...v),Math.max(...v)];});}
function resumenAccesible(p,inf,b){const i=ANIOS.length-1,e=extremos(b)[i];return `${p.etiqueta}: ${num(p.valores[i],inf.formato)}${inf.sufijo} en ${ANIOS[i]}. El rango nacional va de ${num(e[0],inf.formato)} a ${num(e[1],inf.formato)}${inf.sufijo}.`;}

function vistaRegion(cod,f,inf,b,p){document.getElementById("vista").innerHTML=kpis(cod,f,inf,b,p)+`<div class="panel"><div id="chart" role="img" aria-label="Evolución regional de ${esc(f.nombre)}"></div>${metaGraficoRegion(inf,p,cod)}<p class="finding"><strong>Conclusión regional.</strong> ${esc(f.hallazgo_regional)}</p><p class="chart-summary"><strong>Resumen del gráfico.</strong> ${esc(resumenAccesible(p,inf,b))}</p></div>${f.nota?`<div class="note"><strong>Nota metodológica.</strong> ${esc(f.nota)}</div>`:""}`;
  const ex=extremos(b),tr=[{x:ANIOS,y:ex.map(x=>x[1]),mode:"lines",line:{width:0},hoverinfo:"skip",showlegend:false},
    {x:ANIOS,y:ex.map(x=>x[0]),mode:"lines",line:{width:0},fill:"tonexty",fillcolor:"rgba(95,107,118,.16)",name:"Mínimo–máximo entre países"},
    {x:ANIOS,y:b.promedio,mode:"lines+markers",name:"Promedio de países (media simple)",line:{color:"#7b8791",width:2,dash:"dash"},marker:{size:7}}];
  tr.push({x:ANIOS,y:p.valores,mode:"lines+markers",name:p.etiqueta,line:{color:cod==="ECO_CG"?"#c85d22":"#1f4e79",width:4},marker:{size:9}});
  const ly=baseLayout(inf,"region");if(cod==="ECO15")ly.shapes=[{type:"line",x0:ANIOS[0],x1:ANIOS.at(-1),y0:0,y1:0,line:{color:"#68737d",dash:"dot"}}];
  if(cod==="ECO14"){ly.shapes=(ly.shapes||[]).concat([{type:"rect",xref:"x",yref:"paper",x0:2022.5,x1:2024.2,y0:0,y1:1,fillcolor:"rgba(0,0,0,.05)",line:{width:0},layer:"below"}]);ly.annotations=[{x:2023.5,y:1.04,yref:"paper",text:"imputación CAGR",showarrow:false,font:{size:11,color:"#5f6b76"}}];}
  Plotly.newPlot("chart",tr,ly,plotCfg);
}

function vistaPaises(cod,f,inf,b,p){document.getElementById("vista").innerHTML=kpis(cod,f,inf,b,p)+`<div class="panel"><div id="chart" role="img" aria-label="Comparación de los seis países para ${esc(f.nombre)}"></div>${metaGraficoPaises(inf)}<p class="chart-summary">Cada país conserva la misma prominencia visual; use la leyenda para aislar una serie.</p></div>${cod==="ECO14"?'<div class="note">Los marcadores huecos identifican valores imputados mediante CAGR.</div>':""}`;
  const tr=PAISES.map(pais=>({x:ANIOS,y:b.paises[pais],mode:"lines+markers",name:pais,line:{color:COLORES[pais],width:2.5},
    marker:{size:8,symbol:cod==="ECO14"?DATOS.imputados[pais].map(x=>x?"circle-open":"circle"):"circle"}}));
  const ly=baseLayout(inf,"paises");if(cod==="ECO15")ly.shapes=[{type:"line",x0:ANIOS[0],x1:ANIOS.at(-1),y0:0,y1:0,line:{color:"#68737d",dash:"dot"}}];Plotly.newPlot("chart",tr,ly,plotCfg);
}

function tablaSerie(inf,b,p){let h=`<div class="table-wrap"><table><caption style="position:absolute;left:-9999px">Valores de ${esc(inf.clave)} por país y año</caption><thead><tr><th scope="col">País o referencia</th>${ANIOS.map(a=>`<th scope="col">${a}</th>`).join("")}</tr></thead><tbody>`;
  PAISES.forEach(pa=>h+=`<tr><td>${esc(pa)}</td>${b.paises[pa].map(v=>`<td>${num(v,inf.formato)}</td>`).join("")}</tr>`);
  h+=`<tr class="summary"><td>Promedio de países</td>${b.promedio.map(v=>`<td>${num(v,inf.formato)}</td>`).join("")}</tr>`;
  if(p.etiqueta!=="Promedio de países (media simple)")h+=`<tr class="summary"><td>${esc(p.etiqueta)}</td>${p.valores.map(v=>`<td>${num(v,inf.formato)}</td>`).join("")}</tr>`;
  return h+="</tbody></table></div>";}
function enlaces(cod,clave){const fig=SALIDAS.figuras[clave]||SALIDAS.figuras[cod==="ECO_CG"?"ECO_CG":cod]||SALIDAS.figuras.ENV6;
  const tab=SALIDAS.tablas[clave]||SALIDAS.tablas[cod];return `<div class="links">${fig?`<a class="link-btn" href="${esc(fig)}">Abrir figura para la tesis</a>`:""}${tab?`<a class="link-btn" href="${esc(tab)}">Abrir tabla APA 7</a>`:""}<button class="download" onclick="descargarCSV()">Descargar CSV</button>${fig?'<span class="print-note">PNG horizontal de alta resolución; para móvil use la vista Región.</span>':""}</div>`;}
function vistaDatos(cod,f,inf,b,p){document.getElementById("vista").innerHTML=`<div class="method-grid"><article class="method-card"><h3>Definición</h3><p>${esc(f.descripcion)}</p><p><strong>Unidad:</strong> ${esc(inf.unidad||f.unidad)}</p></article>
  <article class="method-card"><h3>Fórmula o construcción</h3><p>${esc(inf.formula||f.formula||"Comparación descriptiva de series observadas")}</p><p><strong>Referencia principal:</strong> ${esc(p.etiqueta)}</p></article></div>
  ${f.nota?`<div class="note"><strong>Nota metodológica.</strong> ${esc(f.nota)}</div>`:""}${tablaSerie(inf,b,p)}${enlaces(cod,inf.clave)}`;
  window._csv={cod,inf,b,p};}
function descargarCSV(){const {cod,inf,b,p}=window._csv;const filas=[["pais_o_referencia",...ANIOS]];PAISES.forEach(pa=>filas.push([pa,...b.paises[pa]]));filas.push(["Promedio de países",...b.promedio]);if(p.etiqueta!=="Promedio de países (media simple)")filas.push([p.etiqueta,...p.valores]);
  const csv="\ufeff"+filas.map(r=>r.map(v=>`"${String(v??"").replaceAll('"','""')}"`).join(",")).join("\r\n");const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([csv],{type:"text/csv;charset=utf-8"}));a.download=inf.clave+"_SIEPAC_2020_2024.csv";a.click();URL.revokeObjectURL(a.href);}

function mostrarMetodo(){activarNav("metodo");app.innerHTML=`<section class="methodology"><div class="eyebrow">Criterio de lectura</div><h1>Cómo interpretar la región.</h1>
  <p>El visualizador distingue medidas que responden preguntas diferentes. La razón de sumas representa el SIEPAC como sistema; la media simple describe al país típico; la banda mínimo–máximo muestra heterogeneidad nacional.</p>
  <div class="method-grid"><article class="method-card"><h3>Agregado regional</h3><p>Σ numeradores ÷ Σ denominadores. Es la referencia principal cuando el indicador dispone de sus componentes.</p></article>
  <article class="method-card"><h3>Promedio de países</h3><p>Media aritmética de los seis valores nacionales. Cada país recibe el mismo peso.</p></article>
  <article class="method-card"><h3>Excepciones transparentes</h3><p>ECO14 y ECO-CG usan la mediana porque no existe un ponderador regional compatible. ENV6 suma dos magnitudes observadas y no calcula un cociente.</p></article>
  <article class="method-card"><h3>Reproducibilidad</h3><p>Las cifras, fórmulas, tablas y figuras proceden del mismo pipeline. Una corrección se realiza en el dato o generador de origen.</p></article></div>
  <div class="links"><a class="link-btn" href="../docs/resumen_indicadores_SIEPAC.md">Resumen metodológico</a><a class="link-btn" href="../salidas/tesis/tablas/tablas_apa_SIEPAC.html">Tablas APA 7</a></div></section>`;app.focus();window.scrollTo(0,0);}
navPrincipal.addEventListener("scroll",actualizarPistaNav,{passive:true});
window.addEventListener("resize",actualizarPistaNav);
CONSULTA_MOVIL.addEventListener("change",()=>{if(estado.codigo&&estado.vista!=="datos")renderDetalle();});
mostrarInicio("all");
requestAnimationFrame(actualizarPistaNav);
</script>
</body>
</html>
'''


def main() -> None:
    log.info("Cargando datos y fichas del pipeline...")
    hojas = cargar_datos()
    df = preparar_datos(hojas)
    paquete = json.loads(construir_datos_json(
        df, hojas["datos_base"], leer_series_extra()))
    _normalizar_env6(paquete)
    paquete[CODIGO_ECO_CG] = _serie_eco_cg()
    fichas = _fichas_visualizador()
    enlaces = _enlaces_salidas(fichas)
    _validar(paquete, fichas, enlaces)

    html = (PLANTILLA
            .replace("__PLOTLYJS__", _sanear_plotly_js(pyo.get_plotlyjs()))
            .replace("__DATOS__", json.dumps(paquete, ensure_ascii=False))
            .replace("__FICHAS__", json.dumps(fichas, ensure_ascii=False))
            .replace("__ANIOS__", json.dumps(ANIOS))
            .replace("__PAISES__", json.dumps(PAISES, ensure_ascii=False))
            .replace("__COLORES__", json.dumps(COLORES_PAIS,
                                                ensure_ascii=False))
            .replace("__SALIDAS__", json.dumps(enlaces,
                                                ensure_ascii=False)))
    marcadores = [m for m in ("__PLOTLYJS__", "__DATOS__", "__FICHAS__",
                               "__ANIOS__", "__PAISES__", "__COLORES__",
                               "__SALIDAS__") if m in html]
    if marcadores:
        raise ValueError(
            f"VALIDACIÓN FALLIDA: marcadores sin sustituir: {marcadores}")

    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    RUTA_SALIDA.write_text(html, encoding="utf-8")
    log.info("Exportado: %s (%.1f MB, autocontenido; 15 IEDS + ECO-CG)",
             RUTA_SALIDA, RUTA_SALIDA.stat().st_size / 1e6)


if __name__ == "__main__":
    main()
