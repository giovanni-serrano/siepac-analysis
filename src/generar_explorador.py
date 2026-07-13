"""
generar_explorador.py — Explorador HTML de indicadores por menú lateral
====================================================
Etapa del pipeline : visualización
Entradas           : data/processed/indicadores_ECO_valores.csv,
                     data/processed/indicadores_ECO_SIEPAC.xlsx (Datos_Base)
                     y, opcionales, los libros ENV/SOC
Salidas            : graficos/0_explorador_indicadores.html
Alimenta           : — (producto final para exploración de las 3 dimensiones)
Fuente de datos    : salidas del pipeline (generar_matriz_indicadores.py,
                     procesar_dimensiones.py)

Uso:  python src/generar_explorador.py   (ejecutar desde la raíz)

Notas metodológicas:
  - La carga de datos, las fichas de indicadores y la estética compartida
    viven en viz_comun.py (comunes con generar_panel.py).
  - El HTML resultante SÍ es autocontenido (Plotly embebido, datos
    incrustados): abre con doble clic, sin servidor, sin internet.

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import json
import logging
import sys
from pathlib import Path

import plotly.offline as pyo

from config_siepac import DIR_GRAFICOS
from viz_comun import (ANIOS, COLORES_PAIS, FICHAS, PAISES,
                       cargar_datos, construir_datos_json,
                       leer_series_extra, preparar_datos)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

RUTA_SALIDA = DIR_GRAFICOS / "0_explorador_indicadores.html"


PLANTILLA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Explorador de indicadores — SIEPAC 2020–2024</title>
<script>{plotlyjs}</script>
<style>
  :root {{
    --fondo: #FAF9F5; --panel: #F0EEE6; --texto: #1F1E1D;
    --suave: #6E6A63; --acento: #D97757; --borde: #E8E4DB;
  }}
  * {{ box-sizing: border-box; margin: 0; }}
  body {{
    background: var(--fondo); color: var(--texto);
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    display: flex; height: 100vh; overflow: hidden;
  }}
  /* ---------- menu lateral ---------- */
  nav {{
    width: 250px; min-width: 250px; background: var(--panel);
    border-right: 1px solid var(--borde); padding: 22px 14px;
    overflow-y: auto;
  }}
  nav h1 {{
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 19px; margin-bottom: 4px;
  }}
  nav p.sub {{ color: var(--suave); font-size: 12px; margin-bottom: 18px; }}
  nav button {{
    display: block; width: 100%; text-align: left; border: none;
    background: transparent; color: var(--texto); padding: 9px 12px;
    border-radius: 8px; cursor: pointer; font-size: 13.5px;
    margin-bottom: 3px; line-height: 1.3;
  }}
  nav button:hover {{ background: #E7E2D6; }}
  nav button.activo {{
    background: var(--acento); color: #fff; font-weight: 600;
  }}
  nav button .cod {{ font-weight: 700; margin-right: 6px; }}
  /* ---------- panel principal ---------- */
  main {{ flex: 1; padding: 26px 34px; overflow-y: auto; }}
  main h2 {{
    font-family: Georgia, 'Times New Roman', serif; font-size: 26px;
  }}
  main .unidad {{ color: var(--acento); font-size: 15px; font-weight: 600; }}
  main p.desc {{ color: var(--suave); max-width: 760px; margin: 10px 0 4px;
                 font-size: 14px; line-height: 1.5; }}
  main p.nota {{
    color: #8A5A2B; background: #FFF2CC; border-radius: 8px;
    padding: 8px 12px; font-size: 13px; max-width: 760px; margin-top: 8px;
    display: none;
  }}
  #kpis {{ display: flex; gap: 12px; flex-wrap: wrap; margin-top: 14px; }}
  .kpi {{ background: var(--panel); border: 1px solid var(--borde);
         border-radius: 10px; padding: 10px 16px; min-width: 170px; }}
  .kpi-t {{ font-size: 11px; color: var(--suave); }}
  .kpi-v {{ font-family: Georgia, 'Times New Roman', serif; font-size: 18px;
           margin-top: 2px; }}
  #toggle {{ margin-top: 12px; }}
  #toggle button {{ border: 1px solid var(--borde); background: var(--panel);
    color: var(--texto); padding: 6px 14px; cursor: pointer;
    font-size: 12.5px; border-radius: 8px 0 0 8px; }}
  #toggle button + button {{ border-radius: 0 8px 8px 0; border-left: none; }}
  #toggle button.activo {{ background: var(--acento); color: #fff;
    border-color: var(--acento); }}
  #toggle select.selector {{
    margin-left: 10px; padding: 6px 10px; border-radius: 8px;
    border: 1px solid var(--borde); background: var(--panel);
    color: var(--texto); font-size: 12.5px; cursor: pointer;
  }}
  #grafico {{ width: 100%; height: 58vh; min-height: 400px; margin-top: 10px; }}
  footer {{ color: var(--suave); font-size: 11.5px; margin-top: 10px; }}

  /* ---------- vistas de tabla (matrices) ---------- */
  nav .separador {{ border-top: 1px solid var(--borde); margin: 12px 4px; }}
  nav p.grupo {{ color: var(--suave); font-size: 10.5px; letter-spacing: .06em;
                text-transform: uppercase; margin: 4px 0 6px 4px; }}
  .autores {{ padding: 4px 12px 14px; font-size: 12.5px;
             line-height: 1.75; color: var(--texto); }}
  .autores-sub {{ margin-top: 6px; color: var(--suave);
                 font-size: 11px; line-height: 1.5; font-style: italic; }}
  .btn-descarga {{
    display: inline-block; margin-top: 12px; border: none; cursor: pointer;
    background: var(--acento); color: #fff; padding: 8px 16px;
    border-radius: 8px; font-size: 13px;
  }}
  .btn-descarga:hover {{ opacity: .9; }}
  .tabla-wrap {{
    margin-top: 14px; max-height: 62vh; overflow: auto;
    border: 1px solid var(--borde); border-radius: 10px; background: #fff;
  }}
  table.datos {{ border-collapse: collapse; width: 100%; font-size: 12px; }}
  table.datos th {{
    position: sticky; top: 0; background: #44546A; color: #fff;
    padding: 7px 10px; text-align: right; white-space: nowrap; z-index: 1;
  }}
  table.datos th:first-child, table.datos td:first-child {{
    text-align: left; position: sticky; left: 0; background: var(--panel);
  }}
  table.datos th:first-child {{ background: #44546A; z-index: 2; }}
  table.datos td {{
    padding: 6px 10px; text-align: right; border-bottom: 1px solid var(--borde);
    white-space: nowrap;
  }}
  table.datos tr:nth-child(even) td {{ background: #FBFAF6; }}
  table.datos tr:nth-child(even) td:first-child {{ background: #EFEDE4; }}
  .bloque-calc {{ margin-top: 26px; }}
  .bloque-calc h3 {{ font-family: Georgia, 'Times New Roman', serif;
                    font-size: 17px; }}
  .bloque-calc .formula {{
    font-style: italic; color: var(--suave); font-size: 13px; margin: 4px 0;
  }}

  /* ---------- diseño responsivo (móvil y pantallas angostas) ---------- */
  @media (max-width: 768px) {{
    body {{ flex-direction: column; height: auto; overflow: auto; }}
    nav {{
      width: 100%; min-width: 0; border-right: none;
      border-bottom: 1px solid var(--borde); padding: 12px 14px;
    }}
    nav p.sub {{ margin-bottom: 10px; }}
    /* el menú se vuelve una fila de botones deslizable con el dedo */
    #menu {{
      display: flex; overflow-x: auto; gap: 6px;
      -webkit-overflow-scrolling: touch; padding-bottom: 6px;
    }}
    nav button {{
      width: auto; flex: 0 0 auto; white-space: nowrap;
      margin-bottom: 0; font-size: 12.5px; padding: 8px 10px;
    }}
    main {{ padding: 16px 14px; overflow: visible; }}
    main h2 {{ font-size: 21px; }}
    .kpi {{ min-width: 0; flex: 1 1 calc(50% - 12px); padding: 8px 12px; }}
    .kpi-v {{ font-size: 15px; }}
    #grafico {{ height: 52vh; min-height: 330px; }}
  }}
</style>
</head>
<body>

<nav>
  <h1>⚡ SIEPAC 2020–2024</h1>
  <p class="sub">Dimensión económica · IEDS (OIEA/NU)<br>
     Clic en la leyenda para ocultar países.</p>
  <div id="menu"></div>
</nav>

<main>
  <h2 id="titulo"></h2>
  <div class="unidad" id="unidad"></div>
  <p class="desc" id="descripcion"></p>
  <p class="nota" id="nota"></p>
  <div id="vista-indicador">
    <div id="kpis"></div>
    <div id="toggle"></div>
    <div id="grafico"></div>
  </div>
  <div id="vista-tabla" style="display:none"></div>
  <footer>Fuente: indicadores_ECO_SIEPAC.xlsx — matriz IEDS de la tesis.
    Doble clic en una leyenda aísla ese país.</footer>
</main>

<script>
const DATOS = {datos_json};
const FICHAS = {fichas_json};
const COLORES = {colores_json};
const ANIOS = {anios_json};
const PAISES = {paises_json};

const ESTILO = {{
  paper_bgcolor: "#FAF9F5", plot_bgcolor: "#FAF9F5",
  font: {{ family: "'Segoe UI','Helvetica Neue',Arial,sans-serif",
          size: 13, color: "#1F1E1D" }},
  xaxis: {{ gridcolor: "#E8E4DB", tickvals: ANIOS, zerolinecolor: "#E8E4DB",
           automargin: true }},
  legend: {{ orientation: "h", y: -0.12, x: 0.5, xanchor: "center",
            bgcolor: "rgba(0,0,0,0)" }},
  margin: {{ l: 70, r: 30, t: 20, b: 70 }},
  hovermode: "x unified",
}};

let MODO = "serie";          // "serie", "barras" o "heatmap"
let CODIGO_ACTUAL = "ECO1";
let SERIE = 0;               // sub-serie activa (indicadores multi-salida)
let PAIS_ENV6 = "El Salvador";

const ETIQUETA_MODO = {{ serie: "Serie temporal", barras: "2020 vs 2024",
                        heatmap: "Mapa de calor" }};

function setModo(m) {{ MODO = m; render(CODIGO_ACTUAL); }}
function setSerie(i) {{ SERIE = +i; render(CODIGO_ACTUAL); }}
function setPaisEnv6(p) {{ PAIS_ENV6 = p; render(CODIGO_ACTUAL); }}

// Resuelve la sub-serie activa de una ficha: clave de datos, etiqueta,
// formato, sufijo, unidad y formula. Fichas ECO no tienen "series".
function infoSerie(codigo, ficha, idx) {{
  if (!ficha.series)
    return {{ clave: codigo, etiqueta: null, formato: ficha.formato,
             sufijo: ficha.sufijo, unidad: ficha.unidad,
             formula: ficha.formula }};
  const s = ficha.series[Math.min(idx, ficha.series.length - 1)];
  return {{ clave: s[0], etiqueta: s[1], formato: s[2], sufijo: s[3],
           unidad: s[4], formula: s[5] }};
}}

// Dibuja los controles: botones de modo + selector de sub-serie o de
// pais (ENV6) segun corresponda.
function renderToggle(ficha) {{
  let html = (ficha.modos || []).map(m =>
      "<button class='" + (m === MODO ? "activo" : "") +
      "' onclick=\\"setModo('" + m + "')\\">" + ETIQUETA_MODO[m] +
      "</button>").join("");
  if (ficha.series && ficha.series.length > 1) {{
    html += " <select class='selector' onchange='setSerie(this.value)'>" +
        ficha.series.map((s, i) => "<option value='" + i + "'" +
            (i === SERIE ? " selected" : "") + ">" + s[1] +
            "</option>").join("") + "</select>";
  }}
  if (ficha.tipo === "env6") {{
    html = "<select class='selector' onchange='setPaisEnv6(this.value)'>" +
        PAISES.map(p => "<option" + (p === PAIS_ENV6 ? " selected" : "") +
                   ">" + p + "</option>").join("") + "</select>";
  }}
  document.getElementById("toggle").innerHTML = html;
}}

// Formatea un numero segun el formato d3 de la ficha (n decimales).
function fmtNum(v, formato) {{
  if (v === null || v === undefined || Number.isNaN(v)) return "s.d.";
  const m = formato.match(/\\.(\\d)f/);
  const dec = m ? +m[1] : 0;
  return v.toLocaleString("es-NI",
      {{ minimumFractionDigits: dec, maximumFractionDigits: dec }});
}}

// Formato generico para la matriz de datos base (magnitudes muy dispares).
function fmtCelda(v) {{
  if (v === null) return "";
  if (typeof v === "string") return v;
  if (Number.isInteger(v) || Math.abs(v) >= 1000)
    return v.toLocaleString("es-NI", {{ maximumFractionDigits: 0 }});
  return v.toLocaleString("es-NI", {{ minimumFractionDigits: 2,
                                     maximumFractionDigits: 4 }});
}}

// Descarga un CSV construido en el navegador (sin servidor).
function descargarCSV(nombre, columnas, filas) {{
  const esc = c => {{
    const s = c === null || c === undefined ? "" : String(c);
    return /[",\\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }};
  const csv = [columnas.map(esc).join(",")]
      .concat(filas.map(f => f.map(esc).join(","))).join("\\n");
  const url = URL.createObjectURL(
      new Blob(["\\ufeff" + csv], {{ type: "text/csv;charset=utf-8" }}));
  const a = document.createElement("a");
  a.href = url; a.download = nombre; a.click();
  URL.revokeObjectURL(url);
}}

// Tarjetas resumen: promedio 2024, variacion 2020->2024, maximo y minimo.
function renderKPIs(codigo) {{
  const ficha = FICHAS[codigo];
  const inf = infoSerie(codigo, ficha, SERIE);
  const bloque = DATOS[inf.clave];
  const p0 = bloque.promedio[0], p4 = bloque.promedio[ANIOS.length - 1];
  const dif = ficha.delta === "pp" ? (p4 - p0) : ((p4 / p0 - 1) * 100);
  const deltaTxt = (dif >= 0 ? "▲ +" : "▼ −") + Math.abs(dif).toFixed(1) +
                   (ficha.delta === "pp" ? " pp" : " %");
  const v2024 = PAISES.map(p => [p, bloque.paises[p][ANIOS.length - 1]])
                      .filter(x => x[1] !== null)
                      .sort((a, b) => b[1] - a[1]);
  const tarjetas = [
    ["Promedio regional 2024", fmtNum(p4, inf.formato) + inf.sufijo],
    ["Variación regional 2020→2024", deltaTxt],
    ["Máximo 2024", v2024[0][0] + " · " + fmtNum(v2024[0][1], inf.formato)],
    ["Mínimo 2024", v2024[v2024.length - 1][0] + " · " +
        fmtNum(v2024[v2024.length - 1][1], inf.formato)],
  ];
  document.getElementById("kpis").innerHTML = tarjetas.map(t =>
      "<div class='kpi'><div class='kpi-t'>" + t[0] +
      "</div><div class='kpi-v'>" + t[1] + "</div></div>").join("");
}}

// Cambia entre la vista de indicador (grafico) y la de tablas (matrices).
function mostrarVista(cual) {{
  document.getElementById("vista-indicador").style.display =
      cual === "indicador" ? "block" : "none";
  document.getElementById("vista-tabla").style.display =
      cual === "tabla" ? "block" : "none";
}}

function marcarMenu(clave) {{
  document.querySelectorAll("#menu button").forEach(b =>
      b.classList.toggle("activo", b.dataset.cod === clave));
}}

// ----- Vista: Datos base por dimension (variables de entrada) -----
const BASES = {{
  eco: {{ clave: "base", nombre: "Dimensión económica",
    csv: "datos_base_ECO_SIEPAC.csv",
    desc: "Insumos de los ocho indicadores económicos, homologados a " +
          "unidades base: energía en kWh, PIB y VAI en USD constantes de " +
          "2015, tarifa en USD corrientes/MWh. La columna " +
          "tarifa_fuente_dato distingue observaciones reales de " +
          "imputaciones CAGR." }},
  env: {{ clave: "base_env", nombre: "Dimensión ambiental",
    csv: "datos_base_ENV_SIEPAC.csv",
    desc: "Variables de entrada de ENV1–ENV3: emisiones en miles de " +
          "toneladas (10³ t), población en miles de habitantes, PIB en " +
          "USD constantes de 2015 y producción bruta en GWh." }},
  soc: {{ clave: "base_soc", nombre: "Dimensión social",
    csv: "datos_base_SOC_SIEPAC.csv",
    desc: "Variables de entrada de SOC1 y SOC3, todas en %. Los insumos " +
          "monetarios de SOC2 (cargo medio e ingresos por grupo) " +
          "permanecen en las hojas por país de la fuente, en moneda " +
          "local." }},
}};

function renderTablaBase(dim) {{
  CODIGO_ACTUAL = null;
  marcarMenu("BASE_" + dim);
  const cfg = BASES[dim];
  const b = DATOS[cfg.clave];
  document.getElementById("titulo").textContent =
      "Datos base — " + cfg.nombre;
  document.getElementById("unidad").textContent =
      "Variables de entrada por país-año (2020–2024)";
  document.getElementById("descripcion").textContent = cfg.desc;
  document.getElementById("nota").style.display = "none";

  let html = "<div class='tabla-wrap'><table class='datos'><thead><tr>" +
      b.columnas.map(c => "<th>" + c + "</th>").join("") + "</tr></thead><tbody>";
  html += b.filas.map(f => "<tr>" +
      f.map(v => "<td>" + fmtCelda(v) + "</td>").join("") + "</tr>").join("");
  html += "</tbody></table></div>" +
      "<button class='btn-descarga' onclick=\\"descargarCSV(" +
      "BASES['" + dim + "'].csv, DATOS[BASES['" + dim + "'].clave]" +
      ".columnas, DATOS[BASES['" + dim + "'].clave].filas)\\">" +
      "⬇ Descargar CSV</button>";
  document.getElementById("vista-tabla").innerHTML = html;
  mostrarVista("tabla");
}}

// ----- Vista: Metodologia de calculo por dimension -----
function renderTablaCalculo(dim) {{
  CODIGO_ACTUAL = null;
  marcarMenu("CALC_" + dim);
  const cfg = BASES[dim];
  document.getElementById("titulo").textContent =
      "Metodología de cálculo — " + cfg.nombre;
  document.getElementById("unidad").textContent =
      "Fórmula y valores calculados, por indicador";
  document.getElementById("descripcion").textContent =
      "Cada bloque documenta la fórmula aplicada (metodología IEDS, " +
      "OIEA/NU 2005) y los valores resultantes por país y año. En ECO14, " +
      "el asterisco (*) marca valores imputados vía CAGR; s.d. = sin dato.";
  document.getElementById("nota").style.display = "none";

  let html = "";
  const filasCSV = [];
  Object.keys(FICHAS).filter(c => FICHAS[c].dim === dim).forEach(codigo => {{
    const ficha = FICHAS[codigo];

    // ENV6: tabla especial pais/serie x anios (ilustrativo, sin formula)
    if (ficha.tipo === "env6") {{
      html += "<div class='bloque-calc'><h3>" + codigo + " — " +
          ficha.nombre + " <span style='color:var(--acento);font-size:" +
          "13px'>(GWh)</span></h3><div class='formula'>" +
          ficha.descripcion + "</div>" +
          "<div class='tabla-wrap' style='max-height:none'>" +
          "<table class='datos'><thead><tr><th>País</th><th>Serie</th>" +
          ANIOS.map(a => "<th>" + a + "</th>").join("") +
          "</tr></thead><tbody>";
      PAISES.forEach(pais => {{
        [["Inyección Biomasa", "biomasa"], ["Saldo MER", "saldo"]]
        .forEach(([nom, k]) => {{
          html += "<tr><td>" + pais + "</td><td>" + nom + "</td>" +
              DATOS.ENV6[pais][k].map(v =>
                  "<td>" + fmtNum(v, ",.1f") + "</td>").join("") + "</tr>";
          DATOS.ENV6[pais][k].forEach((v, i) =>
              filasCSV.push([pais, ANIOS[i], "ENV6_" + k, v, ""]));
        }});
      }});
      html += "</tbody></table></div></div>";
      return;
    }}

    // Fichas normales: una tabla por sub-serie (o unica si no hay).
    const listaSeries = ficha.series
        ? ficha.series.map((s, i) => infoSerie(codigo, ficha, i))
        : [infoSerie(codigo, ficha, 0)];
    listaSeries.forEach(inf => {{
      const bloque = DATOS[inf.clave];
      html += "<div class='bloque-calc'><h3>" + codigo + " — " +
          ficha.nombre + (inf.etiqueta ? " · " + inf.etiqueta : "") +
          " <span style='color:var(--acento);font-size:13px'>(" +
          inf.unidad + ")</span></h3>" +
          "<div class='formula'>Fórmula: " + inf.formula + "</div>" +
          "<div class='tabla-wrap' style='max-height:none'>" +
          "<table class='datos'><thead><tr><th>País</th>" +
          ANIOS.map(a => "<th>" + a + "</th>").join("") +
          "</tr></thead><tbody>";
      PAISES.forEach(pais => {{
        html += "<tr><td>" + pais + "</td>";
        bloque.paises[pais].forEach((v, i) => {{
          const imp = inf.clave === "ECO14" && DATOS.imputados[pais][i];
          html += "<td>" + fmtNum(v, inf.formato) + (imp ? "*" : "") +
                  "</td>";
          filasCSV.push([pais, ANIOS[i], inf.clave, v,
                         imp ? "imputado_CAGR" : (v === null ? "sin_dato"
                                                             : "real")]);
        }});
        html += "</tr>";
      }});
      html += "<tr><td><b>Promedio regional</b></td>" +
          bloque.promedio.map(v => "<td><b>" + fmtNum(v, inf.formato) +
                                   "</b></td>").join("") +
          "</tr></tbody></table></div></div>";
    }});
  }});
  html += "<button class='btn-descarga' onclick='descargarCSVCalculo()'>" +
          "⬇ Descargar los indicadores de esta dimensión (CSV)</button>";
  window._filasCalc = filasCSV;
  window._csvCalcNombre = "indicadores_" + dim.toUpperCase() + "_SIEPAC.csv";
  document.getElementById("vista-tabla").innerHTML = html;
  mostrarVista("tabla");
}}

function descargarCSVCalculo() {{
  descargarCSV(window._csvCalcNombre,
               ["pais", "anio", "indicador", "valor", "fuente_dato"],
               window._filasCalc);
}}

// Construye las trazas (lineas, barras o mapa de calor) y redibuja.
function render(codigo) {{
  if (codigo !== CODIGO_ACTUAL) SERIE = 0;   // reinicia la sub-serie
  CODIGO_ACTUAL = codigo;
  const ficha = FICHAS[codigo];
  mostrarVista("indicador");
  marcarMenu(codigo);

  document.getElementById("titulo").textContent =
      codigo + " — " + ficha.nombre;
  document.getElementById("descripcion").textContent = ficha.descripcion;
  const nota = document.getElementById("nota");
  nota.textContent = ficha.nota;
  nota.style.display = ficha.nota ? "block" : "none";

  // ----- Vista especial ENV6: dos series observadas, pais a pais -----
  if (ficha.tipo === "env6") {{
    document.getElementById("unidad").textContent =
        ficha.unidad + " · " + PAIS_ENV6;
    document.getElementById("kpis").innerHTML = "";
    renderToggle(ficha);
    const d = DATOS.ENV6[PAIS_ENV6];
    const trazas6 = [
      {{ x: ANIOS, y: d.biomasa, name: "Inyección Biomasa", type: "bar",
        marker: {{ color: "#3E8A7B", opacity: 0.9 }},
        hovertemplate: "Biomasa %{{x}}: %{{y:,.1f}} GWh<extra></extra>" }},
      {{ x: ANIOS, y: d.saldo, name: "Saldo MER", type: "bar",
        marker: {{ color: "#D97757", opacity: 0.9 }},
        hovertemplate: "Saldo MER %{{x}}: %{{y:,.1f}} GWh<extra></extra>" }},
    ];
    const lay6 = structuredClone(ESTILO);
    lay6.barmode = "group"; lay6.hovermode = "closest";
    lay6.xaxis = {{ automargin: true, tickvals: ANIOS }};
    lay6.yaxis = {{ gridcolor: "#E8E4DB", ticksuffix: " GWh",
                   automargin: true, zerolinecolor: "#A63D2A",
                   zerolinewidth: 1.5 }};
    Plotly.react("grafico", trazas6, lay6,
                 {{ responsive: true, displaylogo: false }});
    return;
  }}

  if (!ficha.modos.includes(MODO)) MODO = "serie";
  renderToggle(ficha);
  renderKPIs(codigo);
  const inf = infoSerie(codigo, ficha, SERIE);
  const bloque = DATOS[inf.clave];
  document.getElementById("unidad").textContent =
      inf.unidad + (inf.etiqueta ? " · " + inf.etiqueta : "");

  let trazas;
  if (MODO === "barras") {{
    // Comparacion punta a punta: barras 2020 (tenues) vs 2024 (plenas).
    trazas = [2020, 2024].map((anio, i) => ({{
      x: PAISES,
      y: PAISES.map(p => bloque.paises[p][ANIOS.indexOf(anio)]),
      name: String(anio), type: "bar",
      marker: {{ color: PAISES.map(p => COLORES[p]),
                opacity: i === 0 ? 0.40 : 0.95 }},
      hovertemplate: "%{{x}} · " + anio + ": %{{y:" + inf.formato + "}}" +
                     inf.sufijo + "<extra></extra>",
    }}));
  }} else if (MODO === "heatmap") {{
    // Mapa de calor pais x anio. ECO15 usa escala divergente centrada
    // en 0 (verde = exportador neto, terracota = importador).
    const orden = [...PAISES].reverse();   // primer pais arriba
    const z = orden.map(p => bloque.paises[p]);
    const esDiv = codigo === "ECO15";
    trazas = [{{
      type: "heatmap", x: ANIOS.map(String), y: orden, z: z,
      colorscale: esDiv
          ? [[0, "#2F6B5E"], [0.5, "#FAF9F5"], [1, "#A63D2A"]]
          : [[0, "#FAF9F5"], [1, "#C05F3C"]],
      zmid: esDiv ? 0 : undefined,
      texttemplate: "%{{z:" + inf.formato + "}}",
      textfont: {{ size: 12 }},
      colorbar: {{ thickness: 12, outlinewidth: 0,
                  ticksuffix: inf.sufijo }},
      hovertemplate: "%{{y}} · %{{x}}: %{{z:" + inf.formato + "}}" +
                     inf.sufijo + "<extra></extra>",
    }}];
  }} else {{
    trazas = PAISES.map(pais => {{
      const traza = {{
        x: ANIOS, y: bloque.paises[pais], name: pais,
        mode: "lines+markers", type: "scatter",
        line: {{ color: COLORES[pais], width: 2.5 }},
        marker: {{ size: 8, color: COLORES[pais] }},
        hovertemplate: "%{{y:" + inf.formato + "}}" + inf.sufijo,
      }};
      // ECO14: puntos huecos donde la tarifa fue imputada via CAGR.
      if (codigo === "ECO14") {{
        traza.marker.symbol = DATOS.imputados[pais].map(
            imp => imp ? "circle-open" : "circle");
        traza.marker.line = {{ width: 2, color: COLORES[pais] }};
      }}
      return traza;
    }});

    // Promedio regional: linea gris discontinua, siempre al final.
    trazas.push({{
      x: ANIOS, y: bloque.promedio, name: "Promedio regional",
      mode: "lines", type: "scatter",
      line: {{ color: "#6E6A63", width: 2, dash: "dash" }},
      hovertemplate: "%{{y:" + inf.formato + "}}" + inf.sufijo,
    }});
  }}

  const layout = structuredClone(ESTILO);
  // automargin: el margen izquierdo crece hasta que la etiqueta del eje
  // quepa completa (corrige el recorte de "kWh/hab", "USD/MWh", etc.).
  layout.yaxis = {{ gridcolor: "#E8E4DB", ticksuffix: inf.sufijo,
                   tickformat: inf.formato, zerolinecolor: "#E8E4DB",
                   rangemode: "tozero", automargin: true }};
  if (MODO === "barras") {{
    layout.xaxis = {{ automargin: true }};   // eje categorico (paises)
    layout.barmode = "group";
    layout.hovermode = "closest";
  }}
  if (MODO === "heatmap") {{
    layout.xaxis = {{ automargin: true }};
    layout.yaxis = {{ automargin: true }};
    layout.hovermode = "closest";
  }}
  // ECO15 puede ser negativo: NO anclar a cero y marcar la frontera 0
  // (solo en las vistas con eje Y numerico: serie y barras).
  if (codigo === "ECO15" && MODO !== "heatmap") {{
    layout.yaxis.rangemode = "normal";
    layout.shapes = [{{ type: "line", xref: "paper", x0: 0, x1: 1,
        y0: 0, y1: 0,
        line: {{ color: "#A63D2A", width: 1.5, dash: "dot" }} }}];
    layout.annotations = [
      {{ xref: "paper", x: 0.01, y: 0, yshift: 14, xanchor: "left",
        showarrow: false, text: "↑ importador neto",
        font: {{ size: 11, color: "#A63D2A" }} }},
      {{ xref: "paper", x: 0.01, y: 0, yshift: -14, xanchor: "left",
        showarrow: false, text: "↓ exportador neto",
        font: {{ size: 11, color: "#2F6B5E" }} }},
    ];
  }}
  // ECO2 y ECO6 son valores pequenos: sin sufijo pegado en cada tick.
  if (codigo === "ECO2" || codigo === "ECO6") {{
    layout.yaxis.ticksuffix = "";
  }}

  Plotly.react("grafico", trazas, layout,
               {{ responsive: true, displaylogo: false }});
}}

// Construir el menu lateral agrupado por dimension + vistas de matrices.
const menu = document.getElementById("menu");
const NOMBRE_DIM = {{ eco: "Dimensión económica", env: "Dimensión ambiental",
                     soc: "Dimensión social" }};
let dimPrevia = null;
Object.keys(FICHAS).forEach(codigo => {{
  const ficha = FICHAS[codigo];
  // Omitir indicadores cuyas series no llegaron (archivo faltante).
  const clavePrueba = ficha.tipo === "env6" ? "ENV6"
      : (ficha.series ? ficha.series[0][0] : codigo);
  if (!(clavePrueba in DATOS)) return;
  if (ficha.dim !== dimPrevia) {{
    menu.insertAdjacentHTML("beforeend",
        (dimPrevia ? "<div class='separador'></div>" : "") +
        "<p class='grupo'>" + NOMBRE_DIM[ficha.dim] + "</p>");
    dimPrevia = ficha.dim;
  }}
  const b = document.createElement("button");
  b.dataset.cod = codigo;
  b.innerHTML = "<span class='cod'>" + codigo + "</span>" +
                FICHAS[codigo].nombre;
  b.onclick = () => render(codigo);
  menu.appendChild(b);
}});
// Seccion Datos: datos base y metodologia de calculo, por dimension.
function botonDato(clave, etiqueta, fn) {{
  const b = document.createElement("button");
  b.dataset.cod = clave;
  b.textContent = etiqueta;
  b.onclick = fn;
  menu.appendChild(b);
}}
menu.insertAdjacentHTML("beforeend",
    "<div class='separador'></div><p class='grupo'>Datos base</p>");
["eco", "env", "soc"].forEach(dim => {{
  if (DATOS[BASES[dim].clave])
    botonDato("BASE_" + dim, "📋 " + BASES[dim].nombre,
              () => renderTablaBase(dim));
}});
menu.insertAdjacentHTML("beforeend",
    "<div class='separador'></div><p class='grupo'>Metodología de cálculo</p>");
["eco", "env", "soc"].forEach(dim => {{
  const hay = Object.keys(FICHAS).some(c => {{
    const f = FICHAS[c];
    if (f.dim !== dim) return false;
    const k = f.tipo === "env6" ? "ENV6" : (f.series ? f.series[0][0] : c);
    return k in DATOS;
  }});
  if (hay)
    botonDato("CALC_" + dim, "🧮 " + BASES[dim].nombre,
              () => renderTablaCalculo(dim));
}});

// Autores del proyecto, al pie del menu.
menu.insertAdjacentHTML("beforeend",
    "<div class='separador'></div><p class='grupo'>Autores</p>" +
    "<div class='autores'>" +
    "Luis Giovanni Serrano Bello<br>" +
    "Mariángeles Aracelly Olivares López<br>" +
    "Jonathan Noel García Mendoza" +
    "<div class='autores-sub'>Ingeniería Eléctrica · UNI<br>" +
    "Managua, Nicaragua</div></div>");

render("ECO1");  // vista inicial
</script>
</body>
</html>
"""


def main() -> None:
    log.info("Leyendo datos del Excel...")
    hojas = cargar_datos()
    df = preparar_datos(hojas)

    html = PLANTILLA.format(
        plotlyjs=pyo.get_plotlyjs(),        # libreria embebida → offline
        datos_json=construir_datos_json(df, hojas["datos_base"],
                                        leer_series_extra()),
        fichas_json=json.dumps(FICHAS, ensure_ascii=False),
        colores_json=json.dumps(COLORES_PAIS, ensure_ascii=False),
        anios_json=json.dumps(ANIOS),
        paises_json=json.dumps(PAISES, ensure_ascii=False),
    )
    RUTA_SALIDA.parent.mkdir(exist_ok=True)
    RUTA_SALIDA.write_text(html, encoding="utf-8")
    log.info("Exportado: %s (%.1f MB, autocontenido)",
             RUTA_SALIDA, RUTA_SALIDA.stat().st_size / 1e6)


if __name__ == "__main__":
    main()