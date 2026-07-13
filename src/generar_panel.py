"""
generar_panel.py — Panel HTML tipo producto (portada + detalle + datos)
====================================================
Etapa del pipeline : visualización
Entradas           : data/processed/indicadores_ECO_valores.csv,
                     data/processed/indicadores_ECO_SIEPAC.xlsx (Datos_Base)
                     y, opcionales, los libros ENV/SOC
Salidas            : graficos/panel_siepac.html
Alimenta           : — (producto final para presentación de las 3 dimensiones)
Fuente de datos    : salidas del pipeline (generar_matriz_indicadores.py,
                     procesar_dimensiones.py)

Uso:  python src/generar_panel.py   (ejecutar desde la raíz)

Versión "producto" del explorador: portada con galería de indicadores
(KPI + sparkline), vista de detalle con filtros de país e insights
automáticos, y sección de datos y metodología por dimensión.

Notas metodológicas:
  - La carga de datos, las fichas de indicadores y la estética compartida
    viven en viz_comun.py (comunes con generar_explorador.py).
  - El HTML resultante SÍ es autocontenido: abre con doble clic,
    sin internet.

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import json
import logging
import sys
from pathlib import Path

import plotly.offline as pyo

from config_siepac import DIR_GRAFICOS
from viz_comun import (ANIOS, FICHAS, PAISES,
                       cargar_datos, construir_datos_json,
                       leer_series_extra, preparar_datos)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

RUTA_SALIDA = DIR_GRAFICOS / "panel_siepac.html"



PLANTILLA_PANEL = r'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Panel SIEPAC · Indicadores energéticos 2020–2024</title>
<script>__PLOTLYJS__</script>
<style>
  :root {
    --coral: #FF385C; --negro: #111111; --texto: #1A1A1A;
    --gris: #6B7280; --borde: #EBEBEB; --suave: #F7F7F7;
    --sombra: 0 6px 16px rgba(0,0,0,.12);
    --sombra-s: 0 1px 2px rgba(0,0,0,.08);
    --radio: 16px;
    --fuente: 'Inter', 'Segoe UI', system-ui, -apple-system,
              'Helvetica Neue', Arial, sans-serif;
  }
  * { box-sizing: border-box; margin: 0; }
  html { scroll-behavior: smooth; }
  body { font-family: var(--fuente); color: var(--texto); background: #fff; }
  button { font-family: inherit; cursor: pointer; }

  /* ---------- barra superior ---------- */
  #topbar {
    position: sticky; top: 0; z-index: 20; background: rgba(255,255,255,.92);
    backdrop-filter: blur(8px); border-bottom: 1px solid var(--borde);
    display: flex; align-items: center; gap: 18px; padding: 0 24px;
    height: 64px;
  }
  #marca { display: flex; align-items: center; gap: 9px; font-weight: 800;
           font-size: 17px; letter-spacing: -0.02em; white-space: nowrap; }
  #marca .punto { width: 26px; height: 26px; border-radius: 8px;
    background: var(--coral); color: #fff; display: grid;
    place-items: center; font-size: 14px; }
  #tabs { display: flex; gap: 6px; overflow-x: auto; flex: 1;
          -webkit-overflow-scrolling: touch; }
  #tabs button {
    border: none; background: transparent; color: var(--gris);
    padding: 9px 15px; border-radius: 22px; font-size: 13.5px;
    font-weight: 600; white-space: nowrap;
  }
  #tabs button:hover { background: var(--suave); color: var(--texto); }
  #tabs button.on { background: var(--negro); color: #fff; }
  #rango { font-size: 12.5px; font-weight: 600; color: var(--gris);
           border: 1px solid var(--borde); border-radius: 20px;
           padding: 7px 13px; white-space: nowrap; }

  /* ---------- contenido ---------- */
  #contenido { max-width: 1180px; margin: 0 auto; padding: 0 24px 72px; }

  .hero { padding: 52px 0 34px; }
  .hero h1 { font-size: clamp(30px, 4.4vw, 46px); font-weight: 800;
             letter-spacing: -0.035em; line-height: 1.08; max-width: 720px; }
  .hero p { color: var(--gris); font-size: 16px; margin-top: 12px;
            max-width: 640px; line-height: 1.55; }
  .hero-stats { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 22px; }
  .stat-chip { border: 1px solid var(--borde); border-radius: 14px;
    padding: 12px 18px; box-shadow: var(--sombra-s); }
  .stat-chip b { display: block; font-size: 20px; font-weight: 800;
                 letter-spacing: -0.02em; font-variant-numeric: tabular-nums; }
  .stat-chip span { font-size: 12px; color: var(--gris); }

  .seccion { margin-top: 40px; }
  .seccion > h2 { font-size: 21px; font-weight: 800;
                  letter-spacing: -0.02em; }
  .seccion > p.sub { color: var(--gris); font-size: 13.5px; margin-top: 3px; }

  .grid { display: grid; gap: 22px; margin-top: 18px;
          grid-template-columns: repeat(auto-fill, minmax(265px, 1fr)); }
  .card {
    text-align: left; border: 1px solid var(--borde); background: #fff;
    border-radius: var(--radio); padding: 18px 18px 14px;
    transition: transform .15s ease, box-shadow .15s ease;
  }
  .card:hover { transform: translateY(-3px); box-shadow: var(--sombra); }
  .card .cod { display: inline-flex; align-items: center; gap: 6px;
    font-size: 11px; font-weight: 700; letter-spacing: .05em;
    color: var(--gris); }
  .card .cod i { width: 8px; height: 8px; border-radius: 50%;
                 display: inline-block; }
  .card h3 { font-size: 15px; font-weight: 700; margin-top: 8px;
             letter-spacing: -0.01em; line-height: 1.3; min-height: 39px; }
  .card .kpi { display: flex; align-items: baseline; gap: 8px;
               margin-top: 10px; flex-wrap: wrap; }
  .card .kpi b { font-size: 24px; font-weight: 800;
    letter-spacing: -0.02em; font-variant-numeric: tabular-nums; }
  .card .kpi small { color: var(--gris); font-size: 12px; }
  .pill { font-size: 11.5px; font-weight: 700; border-radius: 12px;
          padding: 3px 9px; background: var(--suave); color: var(--texto);
          font-variant-numeric: tabular-nums; }
  .card svg { display: block; margin-top: 10px; width: 100%; height: 46px; }

  /* ---------- detalle ---------- */
  .volver { border: none; background: transparent; color: var(--texto);
    font-size: 14px; font-weight: 600; padding: 22px 0 0;
    display: inline-flex; gap: 6px; align-items: center; }
  .volver:hover { color: var(--coral); }
  .det-head { margin-top: 14px; }
  .det-head h2 { font-size: clamp(22px, 3vw, 30px); font-weight: 800;
                 letter-spacing: -0.025em; }
  .det-head .unidad { color: var(--coral); font-weight: 700;
                      font-size: 14px; margin-top: 3px; }
  .det-head p.desc { color: var(--gris); max-width: 760px; margin-top: 8px;
                     font-size: 14px; line-height: 1.55; }
  .aviso { background: #FFF5F6; border: 1px solid #FFD3DB; color: #99263C;
    border-radius: 12px; padding: 10px 14px; font-size: 13px;
    max-width: 760px; margin-top: 12px; line-height: 1.5; }

  .controles { display: flex; gap: 12px; flex-wrap: wrap;
               align-items: center; margin-top: 18px; }
  .seg { display: inline-flex; background: var(--suave);
         border-radius: 24px; padding: 4px; }
  .seg button { border: none; background: transparent; color: var(--gris);
    font-size: 12.5px; font-weight: 600; padding: 8px 14px;
    border-radius: 20px; }
  .seg button.on { background: #fff; color: var(--texto);
                   box-shadow: var(--sombra-s); }
  .chips { display: flex; gap: 8px; flex-wrap: wrap; }
  .chip { display: inline-flex; align-items: center; gap: 7px;
    border: 1px solid var(--borde); background: #fff; color: var(--texto);
    border-radius: 20px; padding: 7px 13px; font-size: 12.5px;
    font-weight: 600; }
  .chip i { width: 9px; height: 9px; border-radius: 50%; }
  .chip.off { color: #B8BCC4; }
  .chip.off i { opacity: .25; }
  .chip:hover { border-color: var(--negro); }

  .kpis { display: grid; gap: 14px; margin-top: 20px;
          grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); }
  .kpi-box { border: 1px solid var(--borde); border-radius: 14px;
             padding: 14px 16px; }
  .kpi-box span { font-size: 11.5px; color: var(--gris); font-weight: 600; }
  .kpi-box b { display: block; font-size: 22px; font-weight: 800;
    margin-top: 4px; letter-spacing: -0.02em;
    font-variant-numeric: tabular-nums; }

  .chart-card { border: 1px solid var(--borde); border-radius: var(--radio);
    margin-top: 20px; padding: 10px; box-shadow: var(--sombra-s); }
  #chart { width: 100%; height: 55vh; min-height: 380px; }
  .insight { margin-top: 14px; font-size: 14px; color: var(--texto);
    background: var(--suave); border-radius: 12px; padding: 12px 16px;
    max-width: 760px; line-height: 1.5; }

  /* ---------- datos ---------- */
  .btn-negro { background: var(--negro); color: #fff; border: none;
    border-radius: 24px; padding: 12px 22px; font-size: 13.5px;
    font-weight: 700; margin-top: 16px; }
  .btn-negro:hover { background: #000; }
  .tabla-card { border: 1px solid var(--borde); border-radius: var(--radio);
    overflow: auto; max-height: 62vh; margin-top: 18px;
    box-shadow: var(--sombra-s); }
  table.t { border-collapse: collapse; width: 100%; font-size: 12.5px; }
  table.t th { position: sticky; top: 0; background: #fff; z-index: 1;
    text-align: right; padding: 11px 12px; font-size: 11px;
    letter-spacing: .04em; color: var(--gris); font-weight: 700;
    border-bottom: 1px solid var(--borde); white-space: nowrap; }
  table.t th:first-child, table.t td:first-child {
    text-align: left; position: sticky; left: 0; background: #fff; }
  table.t td { padding: 9px 12px; text-align: right; white-space: nowrap;
    border-bottom: 1px solid var(--suave);
    font-variant-numeric: tabular-nums; }
  table.t tr:hover td { background: var(--suave); }
  .bloque { margin-top: 34px; }
  .bloque h3 { font-size: 17px; font-weight: 800; letter-spacing: -0.015em; }
  .bloque .formula { color: var(--gris); font-size: 13px; margin-top: 4px; }

  /* ---------- footer ---------- */
  footer { background: var(--negro); color: #D1D5DB; margin-top: 60px; }
  .foot-in { max-width: 1180px; margin: 0 auto; padding: 44px 24px 26px;
    display: grid; gap: 30px;
    grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); }
  footer h4 { color: #fff; font-size: 13px; letter-spacing: .06em;
              text-transform: uppercase; margin-bottom: 12px; }
  footer p, footer li { font-size: 13.5px; line-height: 1.8;
                        list-style: none; }
  footer .linea { border-top: 1px solid #2A2A2A; margin-top: 8px; }
  footer .cierre { max-width: 1180px; margin: 0 auto; padding: 16px 24px;
    font-size: 12px; color: #8B8F98; display: flex; gap: 10px;
    flex-wrap: wrap; justify-content: space-between; }

  @media (max-width: 640px) {
    #topbar { padding: 0 14px; gap: 10px; }
    #rango { display: none; }
    #contenido { padding: 0 14px 56px; }
    .hero { padding: 34px 0 22px; }
    #chart { height: 48vh; min-height: 320px; }
  }
  @media (prefers-reduced-motion: reduce) {
    * { transition: none !important; }
    html { scroll-behavior: auto; }
  }
</style>
</head>
<body>

<nav id="topbar">
  <div id="marca"><span class="punto">⚡</span>Panel SIEPAC</div>
  <div id="tabs"></div>
  <div id="rango">2020–2024</div>
</nav>

<main id="contenido"></main>

<footer>
  <div class="foot-in">
    <div>
      <h4>El proyecto</h4>
      <p>Evaluación del suministro de energía eléctrica en el SIEPAC:
      perspectivas económicas, sociales y ambientales. Monográfico para
      optar al título de Ingeniería Eléctrica.</p>
    </div>
    <div>
      <h4>Autores</h4>
      <li>Luis Giovanni Serrano Bello</li>
      <li>Mariángeles Aracelly Olivares López</li>
      <li>Jonathan Noel García Mendoza</li>
    </div>
    <div>
      <h4>Fuentes de datos</h4>
      <li>SIELAC · OLADE</li>
      <li>CEPALSTAT · CEPAL</li>
      <li>Banco Mundial · WDI</li>
      <li>EOR · Mercado Eléctrico Regional</li>
    </div>
  </div>
  <div class="linea"></div>
  <div class="cierre">
    <span>Universidad Nacional de Ingeniería · Managua, Nicaragua · 2026</span>
    <span>Metodología IEDS (OIEA/NU, 2005)</span>
  </div>
</footer>

<script>
const DATOS = __DATOS__;
const FICHAS = __FICHAS__;
const ANIOS = __ANIOS__;
const PAISES = __PAISES__;
const IDX_FIN = ANIOS.length - 1;   // índice del último año de la ventana

// Paleta de producto: un color distinguible por país; Nicaragua lleva el
// coral de acento del panel y Panamá va en negro para máximo contraste.
const COLORES = {
  "Costa Rica": "#00A699", "El Salvador": "#4C6FFF",
  "Guatemala": "#FFB400", "Honduras": "#8B5CF6",
  "Nicaragua": "#FF385C", "Panamá": "#111111",
};
const COLOR_DIM = { eco: "#00A699", env: "#4C6FFF", soc: "#FF385C" };
const NOMBRE_DIM = { eco: "Económica", env: "Ambiental", soc: "Social" };
const SUB_DIM = {
  eco: "Costos, precios, intensidad y estructura del suministro",
  env: "Emisiones y huella atmosférica del sistema eléctrico",
  soc: "Acceso, asequibilidad y equidad energética",
};
const ETIQ_MODO = { serie: "Serie temporal", barras: "2020 vs 2024",
                    heatmap: "Mapa de calor" };
const BASES = {
  eco: { clave: "base", csv: "datos_base_ECO_SIEPAC.csv",
    desc: "Insumos de los ocho indicadores económicos, homologados a " +
      "unidades base: energía en kWh, PIB y VAI en USD constantes de " +
      "2015, tarifa en USD corrientes/MWh." },
  env: { clave: "base_env", csv: "datos_base_ENV_SIEPAC.csv",
    desc: "Variables de entrada de ENV1–ENV3: emisiones en 10³ t, " +
      "población en miles, PIB en USD constantes de 2015 y producción " +
      "bruta en GWh." },
  soc: { clave: "base_soc", csv: "datos_base_SOC_SIEPAC.csv",
    desc: "Variables de entrada de SOC1 y SOC3, en %. Los insumos " +
      "monetarios de SOC2 permanecen en las hojas por país de la " +
      "fuente, en moneda local." },
};

// ------------------------- estado global -------------------------
let VISTA = "inicio";          // inicio | detalle | datos
let DIM = "all";               // filtro de la portada
let COD = null, SERIE = 0, MODO = "serie";
let PAIS_ENV6 = "El Salvador";
let ACTIVOS = new Set(PAISES);
let TAB_DATOS = { dim: "eco", tipo: "base" };

// ------------------------- utilidades -------------------------
function claveDe(cod, idx) {
  const f = FICHAS[cod];
  if (f.tipo === "env6") return "ENV6";
  return f.series ? f.series[Math.min(idx || 0, f.series.length - 1)][0]
                  : cod;
}
function existe(cod) { return claveDe(cod, 0) in DATOS; }
function infoSerie(cod, idx) {
  const f = FICHAS[cod];
  if (!f.series)
    return { clave: cod, etiqueta: null, formato: f.formato,
             sufijo: f.sufijo, unidad: f.unidad, formula: f.formula };
  const s = f.series[Math.min(idx, f.series.length - 1)];
  return { clave: s[0], etiqueta: s[1], formato: s[2], sufijo: s[3],
           unidad: s[4], formula: s[5] };
}
function fmtNum(v, formato) {
  if (v === null || v === undefined || Number.isNaN(v)) return "s.d.";
  const m = formato.match(/\.(\d)f/);
  const dec = m ? +m[1] : 0;
  return v.toLocaleString("es-NI",
      { minimumFractionDigits: dec, maximumFractionDigits: dec });
}
function fmtCelda(v) {
  if (v === null) return "";
  if (typeof v === "string") return v;
  if (Number.isInteger(v) || Math.abs(v) >= 1000)
    return v.toLocaleString("es-NI", { maximumFractionDigits: 0 });
  return v.toLocaleString("es-NI", { minimumFractionDigits: 2,
                                     maximumFractionDigits: 4 });
}
function deltaTexto(cod, vals) {
  const f = FICHAS[cod];
  const v0 = vals[0], v4 = vals[vals.length - 1];
  if (v0 === null || v4 === null) return "";
  const dif = f.delta === "pp" ? (v4 - v0) : ((v4 / v0 - 1) * 100);
  return (dif >= 0 ? "▲ +" : "▼ −") + Math.abs(dif).toFixed(1) +
         (f.delta === "pp" ? " pp" : " %");
}
function descargarCSV(nombre, columnas, filas) {
  const esc = c => {
    const s = c === null || c === undefined ? "" : String(c);
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  };
  const csv = [columnas.map(esc).join(",")]
      .concat(filas.map(f => f.map(esc).join(","))).join("\n");
  const url = URL.createObjectURL(
      new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url; a.download = nombre; a.click();
  URL.revokeObjectURL(url);
}
function sparkline(vals, color) {
  const puntos = vals.map((v, i) => [i, v]).filter(p => p[1] !== null);
  if (puntos.length < 2) return "";
  const ys = puntos.map(p => p[1]);
  const min = Math.min(...ys), max = Math.max(...ys);
  const W = 220, H = 46, P = 5;
  const x = i => P + i * (W - 2 * P) / (vals.length - 1);
  const y = v => max === min ? H / 2
      : H - P - (v - min) * (H - 2 * P) / (max - min);
  const pts = puntos.map(p => x(p[0]).toFixed(1) + "," +
                              y(p[1]).toFixed(1)).join(" ");
  const fin = puntos[puntos.length - 1];
  return "<svg viewBox='0 0 " + W + " " + H + "' preserveAspectRatio='none'>" +
      "<polyline points='" + pts + "' fill='none' stroke='" + color +
      "' stroke-width='2.5' stroke-linecap='round'/>" +
      "<circle cx='" + x(fin[0]).toFixed(1) + "' cy='" +
      y(fin[1]).toFixed(1) + "' r='3.4' fill='" + color + "'/></svg>";
}

// ------------------------- navegacion -------------------------
function renderNav() {
  const tabs = [["inicio_all", "Inicio"], ["inicio_eco", "Económica"],
                ["inicio_env", "Ambiental"], ["inicio_soc", "Social"],
                ["datos", "Datos y metodología"]];
  document.getElementById("tabs").innerHTML = tabs.map(([id, tx]) => {
    const on = (VISTA === "datos" && id === "datos") ||
        (VISTA !== "datos" && id === "inicio_" + DIM);
    return "<button class='" + (on ? "on" : "") +
        "' onclick=\"navegar('" + id + "')\">" + tx + "</button>";
  }).join("");
}
function navegar(id) {
  if (id === "datos") { VISTA = "datos"; vistaDatos(); }
  else { VISTA = "inicio"; DIM = id.split("_")[1]; vistaInicio(); }
  window.scrollTo(0, 0);
}

// ------------------------- portada -------------------------
function statHero() {
  const s = [];
  if (DATOS.ECO13) s.push([fmtNum(DATOS.ECO13.promedio[IDX_FIN], ".1f") + "%",
      "generación renovable regional · 2024"]);
  if (DATOS.ECO14) s.push([fmtNum(DATOS.ECO14.promedio[IDX_FIN], ".1f") + " USD/MWh",
      "precio medio regional · 2024"]);
  if (DATOS.SOC1) s.push([fmtNum(DATOS.SOC1.promedio[IDX_FIN], ".1f") + "%",
      "población sin electricidad · 2024"]);
  if (DATOS.ENV3) s.push([fmtNum(DATOS.ENV3.promedio[IDX_FIN], ".2f") + " g/kWh",
      "emisiones atmosféricas · 2024"]);
  return s.map(([b, t]) => "<div class='stat-chip'><b>" + b + "</b><span>" +
      t + "</span></div>").join("");
}
function tarjeta(cod) {
  const f = FICHAS[cod];
  let kpi, delta = "", spark;
  if (f.tipo === "env6") {
    const saldoProm = ANIOS.map((a, i) =>
        PAISES.reduce((s, p) => s + DATOS.ENV6[p].saldo[i], 0) / PAISES.length);
    kpi = "<b>6</b><small>países · 2 series (GWh)</small>";
    delta = "<span class='pill'>Ilustrativo</span>";
    spark = sparkline(saldoProm, COLOR_DIM[f.dim]);
  } else {
    const inf = infoSerie(cod, 0);
    const prom = DATOS[inf.clave].promedio;
    kpi = "<b>" + fmtNum(prom[IDX_FIN], inf.formato) + "</b><small>" +
          inf.unidad + " · 2024</small>";
    const d = deltaTexto(cod, prom);
    if (d) delta = "<span class='pill'>" + d + "</span>";
    spark = sparkline(prom, COLOR_DIM[f.dim]);
  }
  return "<button class='card' onclick=\"abrirDetalle('" + cod + "')\">" +
      "<span class='cod'><i style='background:" + COLOR_DIM[f.dim] +
      "'></i>" + cod + "</span><h3>" + f.nombre + "</h3>" +
      "<div class='kpi'>" + kpi + delta + "</div>" + spark + "</button>";
}
function vistaInicio() {
  renderNav();
  let html = "";
  if (DIM === "all") {
    html += "<div class='hero'><h1>El pulso energético de Centroamérica," +
        " en un solo panel.</h1>" +
        "<p>15 indicadores de desarrollo sostenible (OIEA/NU) para los " +
        "seis países del SIEPAC, 2020–2024. Datos oficiales, cálculos " +
        "trazables y tres dimensiones para responder una pregunta: ¿la " +
        "integración eléctrica regional avanza hacia un modelo " +
        "sostenible?</p><div class='hero-stats'>" + statHero() +
        "</div></div>";
  }
  ["eco", "env", "soc"].forEach(dim => {
    if (DIM !== "all" && DIM !== dim) return;
    const cods = Object.keys(FICHAS)
        .filter(c => FICHAS[c].dim === dim && existe(c));
    if (!cods.length) return;
    html += "<section class='seccion'><h2>Dimensión " +
        NOMBRE_DIM[dim].toLowerCase() + "</h2><p class='sub'>" +
        SUB_DIM[dim] + "</p><div class='grid'>" +
        cods.map(tarjeta).join("") + "</div></section>";
  });
  document.getElementById("contenido").innerHTML = html;
}

// ------------------------- detalle -------------------------
function abrirDetalle(cod) {
  if (cod !== COD) { SERIE = 0; MODO = "serie"; ACTIVOS = new Set(PAISES); }
  COD = cod; VISTA = "detalle";
  renderNav();
  renderDetalle();
  window.scrollTo(0, 0);
}
function setSerie(i) { SERIE = +i; renderDetalle(); }
function setModo(m) { MODO = m; renderDetalle(); }
function setPaisEnv6(p) { PAIS_ENV6 = p; renderDetalle(); }
function togglePais(p) {
  if (ACTIVOS.has(p)) { if (ACTIVOS.size > 1) ACTIVOS.delete(p); }
  else ACTIVOS.add(p);
  renderDetalle();
}
function segmentado(items, activo, fn) {
  return "<div class='seg'>" + items.map(([v, tx]) =>
      "<button class='" + (String(v) === String(activo) ? "on" : "") +
      "' onclick=\"" + fn + "('" + v + "')\">" + tx +
      "</button>").join("") + "</div>";
}
function insightDe(cod, inf) {
  const bloque = DATOS[inf.clave];
  const f = FICHAS[cod];
  let mejor = null;
  PAISES.forEach(p => {
    const v = bloque.paises[p];
    if (v[0] === null || v[IDX_FIN] === null) return;
    const dif = f.delta === "pp" ? v[IDX_FIN] - v[0]
                                 : (v[IDX_FIN] / v[0] - 1) * 100;
    if (!mejor || Math.abs(dif) > Math.abs(mejor[1])) mejor = [p, dif];
  });
  if (!mejor) return "";
  const signo = mejor[1] >= 0 ? "▲ +" : "▼ −";
  return "<div class='insight'>💡 <b>" + mejor[0] + "</b> registró la " +
      "mayor variación del periodo: " + signo +
      Math.abs(mejor[1]).toFixed(1) + (f.delta === "pp" ? " pp" : " %") +
      " entre 2020 y 2024.</div>";
}
function renderDetalle() {
  const f = FICHAS[COD];
  const c = document.getElementById("contenido");

  let head = "<button class='volver' onclick=\"navegar('inicio_" + f.dim +
      "')\">← Dimensión " + NOMBRE_DIM[f.dim].toLowerCase() + "</button>" +
      "<div class='det-head'><span class='cod' style='font-size:12px;" +
      "font-weight:700;color:" + COLOR_DIM[f.dim] + "'>" + COD +
      "</span><h2>" + f.nombre + "</h2>";

  // ---- ENV6: vista ilustrativa por pais ----
  if (f.tipo === "env6") {
    head += "<div class='unidad'>GWh · " + PAIS_ENV6 + "</div>" +
        "<p class='desc'>" + f.descripcion + "</p>" +
        (f.nota ? "<div class='aviso'>" + f.nota + "</div>" : "") + "</div>";
    const chips = "<div class='chips'>" + PAISES.map(p =>
        "<button class='chip " + (p === PAIS_ENV6 ? "" : "off") +
        "' onclick=\"setPaisEnv6('" + p + "')\"><i style='background:" +
        COLORES[p] + "'></i>" + p + "</button>").join("") + "</div>";
    c.innerHTML = head + "<div class='controles'>" + chips + "</div>" +
        "<div class='chart-card'><div id='chart'></div></div>";
    const d = DATOS.ENV6[PAIS_ENV6];
    Plotly.react("chart", [
      { x: ANIOS, y: d.biomasa, name: "Inyección Biomasa", type: "bar",
        marker: { color: "#00A699" },
        hovertemplate: "Biomasa %{x}: %{y:,.1f} GWh<extra></extra>" },
      { x: ANIOS, y: d.saldo, name: "Saldo MER", type: "bar",
        marker: { color: "#111111" },
        hovertemplate: "Saldo MER %{x}: %{y:,.1f} GWh<extra></extra>" },
    ], layoutBase({ barmode: "group", hovermode: "closest",
        yaxis: { ticksuffix: " GWh", automargin: true,
                 gridcolor: "#EBEBEB", zerolinecolor: "#FF385C",
                 zerolinewidth: 1.5 },
        xaxis: { tickvals: ANIOS, automargin: true } }),
      { responsive: true, displaylogo: false });
    return;
  }

  const inf = infoSerie(COD, SERIE);
  const bloque = DATOS[inf.clave];
  head += "<div class='unidad'>" + inf.unidad +
      (inf.etiqueta ? " · " + inf.etiqueta : "") + "</div>" +
      "<p class='desc'>" + f.descripcion + "</p>" +
      (f.nota ? "<div class='aviso'>" + f.nota + "</div>" : "") + "</div>";

  let controles = segmentado(
      f.modos.map(m => [m, ETIQ_MODO[m]]), MODO, "setModo");
  if (f.series && f.series.length > 1)
    controles += segmentado(
        f.series.map((s, i) => [i, s[1]]), SERIE, "setSerie");
  controles += "<div class='chips'>" + PAISES.map(p =>
      "<button class='chip " + (ACTIVOS.has(p) ? "" : "off") +
      "' onclick=\"togglePais('" + p + "')\"><i style='background:" +
      COLORES[p] + "'></i>" + p + "</button>").join("") + "</div>";

  const prom = bloque.promedio;
  const v24 = PAISES.map(p => [p, bloque.paises[p][IDX_FIN]])
      .filter(x => x[1] !== null).sort((a, b) => b[1] - a[1]);
  const kpis = [
    ["Promedio regional 2024", fmtNum(prom[IDX_FIN], inf.formato) + inf.sufijo],
    ["Variación 2020→2024", deltaTexto(COD, prom) || "s.d."],
    ["Máximo 2024", v24[0][0] + " · " + fmtNum(v24[0][1], inf.formato)],
    ["Mínimo 2024", v24[v24.length - 1][0] + " · " +
        fmtNum(v24[v24.length - 1][1], inf.formato)],
  ].map(([t, v]) => "<div class='kpi-box'><span>" + t + "</span><b>" + v +
        "</b></div>").join("");

  c.innerHTML = head + "<div class='controles'>" + controles + "</div>" +
      "<div class='kpis'>" + kpis + "</div>" +
      "<div class='chart-card'><div id='chart'></div></div>" +
      insightDe(COD, inf);
  graficar(COD, inf, bloque);
}
function layoutBase(extra) {
  return Object.assign({
    paper_bgcolor: "#fff", plot_bgcolor: "#fff",
    font: { family: "'Inter','Segoe UI',system-ui,sans-serif",
            size: 13, color: "#1A1A1A" },
    legend: { orientation: "h", y: -0.14, x: 0.5, xanchor: "center" },
    margin: { l: 60, r: 24, t: 16, b: 64 },
    hovermode: "x unified",
  }, extra);
}
function graficar(cod, inf, bloque) {
  const sel = PAISES.filter(p => ACTIVOS.has(p));
  let trazas, extra = {};
  if (MODO === "barras") {
    trazas = [2020, 2024].map((anio, i) => ({
      x: sel, y: sel.map(p => bloque.paises[p][ANIOS.indexOf(anio)]),
      name: String(anio), type: "bar",
      marker: { color: sel.map(p => COLORES[p]),
                opacity: i === 0 ? 0.35 : 0.95 },
      hovertemplate: "%{x} · " + anio + ": %{y:" + inf.formato + "}" +
                     inf.sufijo + "<extra></extra>",
    }));
    extra = { barmode: "group", hovermode: "closest",
      xaxis: { automargin: true },
      yaxis: { gridcolor: "#EBEBEB", ticksuffix: inf.sufijo,
               tickformat: inf.formato, rangemode: "tozero",
               automargin: true } };
  } else if (MODO === "heatmap") {
    const orden = [...sel].reverse();
    const esDiv = cod === "ECO15";
    trazas = [{ type: "heatmap", x: ANIOS.map(String), y: orden,
      z: orden.map(p => bloque.paises[p]),
      colorscale: esDiv
          ? [[0, "#00A699"], [0.5, "#FFFFFF"], [1, "#FF385C"]]
          : [[0, "#FFFFFF"], [1, "#FF385C"]],
      zmid: esDiv ? 0 : undefined,
      texttemplate: "%{z:" + inf.formato + "}", textfont: { size: 12 },
      colorbar: { thickness: 12, outlinewidth: 0, ticksuffix: inf.sufijo },
      hovertemplate: "%{y} · %{x}: %{z:" + inf.formato + "}" + inf.sufijo +
                     "<extra></extra>" }];
    extra = { hovermode: "closest", xaxis: { automargin: true },
              yaxis: { automargin: true } };
  } else {
    trazas = sel.map(p => {
      const t = { x: ANIOS, y: bloque.paises[p], name: p,
        mode: "lines+markers", type: "scatter",
        line: { color: COLORES[p], width: 2.6 },
        marker: { size: 7.5, color: COLORES[p] },
        hovertemplate: "%{y:" + inf.formato + "}" + inf.sufijo };
      if (inf.clave === "ECO14") {
        t.marker.symbol = DATOS.imputados[p].map(
            i => i ? "circle-open" : "circle");
        t.marker.line = { width: 2, color: COLORES[p] };
      }
      return t;
    });
    trazas.push({ x: ANIOS, y: bloque.promedio, name: "Promedio regional",
      mode: "lines", type: "scatter",
      line: { color: "#9CA3AF", width: 2, dash: "dash" },
      hovertemplate: "%{y:" + inf.formato + "}" + inf.sufijo });
    extra = { xaxis: { tickvals: ANIOS, gridcolor: "#F1F1F1",
                       automargin: true },
      yaxis: { gridcolor: "#EBEBEB", ticksuffix: inf.sufijo,
               tickformat: inf.formato, rangemode: "tozero",
               automargin: true } };
  }
  if (cod === "ECO2" || cod === "ECO6") extra.yaxis.ticksuffix = "";
  const layout = layoutBase(extra);
  if (cod === "ECO15" && MODO !== "heatmap") {
    layout.yaxis.rangemode = "normal";
    layout.shapes = [{ type: "line", xref: "paper", x0: 0, x1: 1,
      y0: 0, y1: 0, line: { color: "#FF385C", width: 1.5, dash: "dot" } }];
    layout.annotations = [
      { xref: "paper", x: 0.01, y: 0, yshift: 14, xanchor: "left",
        showarrow: false, text: "↑ importador neto",
        font: { size: 11, color: "#FF385C" } },
      { xref: "paper", x: 0.01, y: 0, yshift: -14, xanchor: "left",
        showarrow: false, text: "↓ exportador neto",
        font: { size: 11, color: "#00A699" } }];
  }
  Plotly.react("chart", trazas, layout,
               { responsive: true, displaylogo: false });
}

// ------------------------- datos y metodologia -------------------------
function setDatosDim(d) { TAB_DATOS.dim = d; vistaDatos(); }
function setDatosTipo(t) { TAB_DATOS.tipo = t; vistaDatos(); }
function descargarCalculo() {
  descargarCSV(window._csvNombre, ["pais", "anio", "indicador", "valor",
      "fuente_dato"], window._filas);
}
function vistaDatos() {
  renderNav();
  const dims = ["eco", "env", "soc"].filter(d => DATOS[BASES[d].clave] ||
      Object.keys(FICHAS).some(c => FICHAS[c].dim === d && existe(c)));
  if (!dims.includes(TAB_DATOS.dim)) TAB_DATOS.dim = dims[0];
  const { dim, tipo } = TAB_DATOS;

  let html = "<div class='hero' style='padding-bottom:10px'>" +
      "<h1>Datos y metodología</h1>" +
      "<p>Las variables de entrada y las fórmulas de cálculo de cada " +
      "dimensión, listas para auditar o reutilizar en otros " +
      "proyectos.</p></div><div class='controles'>" +
      segmentado(dims.map(d => [d, NOMBRE_DIM[d]]), dim, "setDatosDim") +
      segmentado([["base", "Datos base"], ["calc", "Metodología de cálculo"]],
                 tipo, "setDatosTipo") + "</div>";

  if (tipo === "base") {
    const cfg = BASES[dim], b = DATOS[cfg.clave];
    if (!b) { html += "<p class='sub' style='margin-top:20px;color:" +
        "var(--gris)'>Esta dimensión no incluye tabla de datos base." +
        "</p>"; }
    else {
      html += "<p class='sub' style='margin-top:18px;color:var(--gris);" +
          "max-width:760px'>" + cfg.desc + "</p>" +
          "<div class='tabla-card'><table class='t'><thead><tr>" +
          b.columnas.map(c => "<th>" + c + "</th>").join("") +
          "</tr></thead><tbody>" +
          b.filas.map(f => "<tr>" + f.map(v => "<td>" + fmtCelda(v) +
              "</td>").join("") + "</tr>").join("") +
          "</tbody></table></div>" +
          "<button class='btn-negro' onclick=\"descargarCSV(BASES['" + dim +
          "'].csv, DATOS[BASES['" + dim + "'].clave].columnas, " +
          "DATOS[BASES['" + dim + "'].clave].filas)\">" +
          "Descargar CSV</button>";
    }
  } else {
    const filas = [];
    Object.keys(FICHAS).filter(c => FICHAS[c].dim === dim && existe(c))
    .forEach(cod => {
      const f = FICHAS[cod];
      if (f.tipo === "env6") {
        html += "<div class='bloque'><h3>" + cod + " · " + f.nombre +
            " <span style='color:var(--coral);font-size:13px'>(GWh)" +
            "</span></h3><div class='formula'>" + f.descripcion +
            "</div><div class='tabla-card' style='max-height:none'>" +
            "<table class='t'><thead><tr><th>País</th><th>Serie</th>" +
            ANIOS.map(a => "<th>" + a + "</th>").join("") +
            "</tr></thead><tbody>";
        PAISES.forEach(p => {
          [["Inyección Biomasa", "biomasa"], ["Saldo MER", "saldo"]]
          .forEach(([nom, k]) => {
            html += "<tr><td>" + p + "</td><td>" + nom + "</td>" +
                DATOS.ENV6[p][k].map(v => "<td>" + fmtNum(v, ",.1f") +
                    "</td>").join("") + "</tr>";
            DATOS.ENV6[p][k].forEach((v, i) =>
                filas.push([p, ANIOS[i], "ENV6_" + k, v, ""]));
          });
        });
        html += "</tbody></table></div></div>";
        return;
      }
      const lista = f.series
          ? f.series.map((s, i) => infoSerie(cod, i))
          : [infoSerie(cod, 0)];
      lista.forEach(inf => {
        const bloque = DATOS[inf.clave];
        html += "<div class='bloque'><h3>" + cod + " · " + f.nombre +
            (inf.etiqueta ? " — " + inf.etiqueta : "") +
            " <span style='color:var(--coral);font-size:13px'>(" +
            inf.unidad + ")</span></h3><div class='formula'>Fórmula: " +
            inf.formula + "</div>" +
            "<div class='tabla-card' style='max-height:none'>" +
            "<table class='t'><thead><tr><th>País</th>" +
            ANIOS.map(a => "<th>" + a + "</th>").join("") +
            "</tr></thead><tbody>";
        PAISES.forEach(p => {
          html += "<tr><td>" + p + "</td>";
          bloque.paises[p].forEach((v, i) => {
            const imp = inf.clave === "ECO14" && DATOS.imputados[p][i];
            html += "<td>" + fmtNum(v, inf.formato) + (imp ? "*" : "") +
                    "</td>";
            filas.push([p, ANIOS[i], inf.clave, v,
                imp ? "imputado_CAGR" : (v === null ? "sin_dato" : "real")]);
          });
          html += "</tr>";
        });
        html += "<tr><td><b>Promedio regional</b></td>" +
            bloque.promedio.map(v => "<td><b>" + fmtNum(v, inf.formato) +
                "</b></td>").join("") + "</tr></tbody></table></div></div>";
      });
    });
    window._filas = filas;
    window._csvNombre = "indicadores_" + dim.toUpperCase() + "_SIEPAC.csv";
    html += "<button class='btn-negro' onclick='descargarCalculo()'>" +
        "Descargar indicadores (CSV)</button>";
  }
  document.getElementById("contenido").innerHTML = html;
}

// ------------------------- arranque -------------------------
renderNav();
vistaInicio();
</script>
</body>
</html>
'''


def main() -> None:
    log.info("Leyendo datos del Excel...")
    hojas = cargar_datos()
    df = preparar_datos(hojas)
    datos_json = construir_datos_json(df, hojas["datos_base"],
                                      leer_series_extra())
    html = (PLANTILLA_PANEL
            .replace("__DATOS__", datos_json)
            .replace("__FICHAS__", json.dumps(FICHAS, ensure_ascii=False))
            .replace("__ANIOS__", json.dumps(ANIOS))
            .replace("__PAISES__", json.dumps(PAISES, ensure_ascii=False))
            .replace("__PLOTLYJS__", pyo.get_plotlyjs()))
    RUTA_SALIDA.parent.mkdir(exist_ok=True)
    RUTA_SALIDA.write_text(html, encoding="utf-8")
    log.info("Exportado: %s (%.1f MB, autocontenido)",
             RUTA_SALIDA, RUTA_SALIDA.stat().st_size / 1e6)


if __name__ == "__main__":
    main()