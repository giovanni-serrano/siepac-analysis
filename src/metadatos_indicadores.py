"""
metadatos_indicadores.py — Definiciones científicas autoritativas
====================================================
Etapa del pipeline : metadatos compartidos (módulo importable)
Entradas           : definiciones metodológicas documentadas del proyecto
Salidas            : FICHAS, series, ponderadores y variantes editoriales
Alimenta           : libros, resumen, tablas, figuras y visualizador
Fuente de datos    : fichas IEDS y decisiones de la tesis
Uso                : importar los catálogos
Notas metodológicas: conserva literalmente los textos publicados; las variantes
                     editoriales de Excel no redefinen las fórmulas científicas.
Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

FICHAS = {'ECO1': {'nombre': 'Uso de energía per cápita',
          'unidad': 'kWh/habitante',
          'descripcion': 'Consumo final total dividido entre la población. Refleja el nivel de '
                         'acceso y uso efectivo de la electricidad por persona.',
          'nota': '',
          'delta': 'pct',
          'formula': 'Consumo final total (kWh) ÷ Población',
          'dim': 'eco',
          'hallazgo_regional': 'El consumo eléctrico por habitante del bloque aumentó 10,9 % entre '
                               '2020 y 2024, mientras disminuyó la heterogeneidad relativa entre '
                               'países.'},
 'ECO2': {'nombre': 'Uso de energía por unidad de PIB',
          'unidad': 'kWh/USD const. 2015',
          'descripcion': 'Cuánta energía consume la economía por cada dólar de PIB real. Bajar en '
                         'el tiempo sugiere desacople entre crecimiento y consumo energético.',
          'nota': '',
          'delta': 'pct',
          'formula': 'Consumo final total (kWh) ÷ PIB real (USD constantes 2015)',
          'dim': 'eco',
          'hallazgo_regional': 'La intensidad eléctrica regional disminuyó 8,3 % entre 2020 y '
                               '2024, aunque las diferencias relativas entre las economías '
                               'nacionales se ampliaron.'},
 'ECO3': {'nombre': 'Eficiencia de conversión y distribución',
          'unidad': '%',
          'descripcion': 'Porcentaje de la producción bruta que llega como consumo final. La '
                         'brecha son pérdidas técnicas, autoconsumo y saldo de intercambios.',
          'nota': 'La razón relaciona consumo final y producción bruta; la brecha integra '
                  'pérdidas, autoconsumo y saldo de intercambios.',
          'delta': 'pp',
          'formula': '(Consumo final total ÷ Producción bruta) × 100',
          'dim': 'eco',
          'hallazgo_regional': 'La razón regional de conversión y distribución permaneció '
                               'prácticamente estable, de 82,4 % a 82,6 %, sin una mejora '
                               'sustantiva del nivel del bloque.'},
 'ECO6': {'nombre': 'Intensidad energética de la industria',
          'unidad': 'kWh/USD const. 2015',
          'descripcion': 'Energía que necesita la industria por cada dólar de valor agregado '
                         'manufacturero. Menor = industria que genera más valor por kWh.',
          'nota': 'El denominador es el valor agregado manufacturero (ODS 9.2.1, % del PIB × PIB '
                  'real) y el numerador es el consumo industrial de electricidad reportado por '
                  'OLADE.',
          'delta': 'pct',
          'formula': 'Consumo industrial (kWh) ÷ Valor agregado manufacturero (USD 2015)',
          'dim': 'eco',
          'hallazgo_regional': 'La intensidad eléctrica industrial del bloque aumentó 34,4 % entre '
                               '2020 y 2024, en contraste con la reducción observada en la '
                               'intensidad de la economía total.'},
 'ECO11': {'nombre': 'Fósiles en la electricidad',
           'unidad': '%',
           'descripcion': 'Participación de la generación térmica fósil en la generación total. El '
                          'espejo de ECO13.',
           'nota': '',
           'delta': 'pp',
           'formula': '(Generación térmica fósil ÷ Generación total) × 100',
           'dim': 'eco',
           'hallazgo_regional': 'La participación fósil en la generación regional aumentó de 25,0 '
                                '% a 33,0 % entre 2020 y 2024 y las diferencias relativas entre '
                                'países se redujeron.'},
 'ECO13': {'nombre': 'Renovables en la electricidad',
           'unidad': '%',
           'descripcion': 'Hidro + geotermia + eólica + solar + biomasa como porcentaje de la '
                          'generación total.',
           'nota': '',
           'delta': 'pp',
           'formula': '(Hidro + Geotermia + Eólica + Solar + Biomasa) ÷ Generación total × 100',
           'dim': 'eco',
           'hallazgo_regional': 'La participación renovable del bloque disminuyó de 75,0 % a 67,0 '
                                '% entre 2020 y 2024, lo que describe un cambio de composición y '
                                'no necesariamente una caída del volumen renovable.'},
 'ECO14': {'nombre': 'Precio medio de la electricidad',
           'unidad': 'USD corrientes/MWh',
           'descripcion': 'Ingresos por energía regulada vendida entre energía regulada consumida. '
                          'En dólares corrientes de cada año.',
           'nota': 'La serie se resume mediante la mediana de países, no mediante un agregado '
                   'regional. La razón de sumas requiere la energía regulada vendida por país y '
                   'año; 2023–2024 son totalmente imputados mediante CAGR.',
           'delta': 'pct',
           'formula': 'Ingresos por energía regulada (USD) ÷ Energía regulada (MWh)',
           'dim': 'eco',
           'hallazgo_regional': 'En el tramo con mayor respaldo observacional, la mediana de '
                                'países subió de 178,3 a 188,7 USD/MWh entre 2020 y 2022; los '
                                'valores de 2023–2024 son extrapolaciones.'},
 'ECO15': {'nombre': 'Dependencia de importaciones netas',
           'unidad': '%',
           'descripcion': 'Importaciones netas sobre la oferta total. Los valores positivos '
                          'representan importación neta y los negativos, exportación neta.',
           'nota': 'En el agregado regional los intercambios dentro del MER se cancelan al sumar, '
                   'por lo que la cifra del bloque mide su dependencia extrarregional y no el '
                   'promedio de las dependencias nacionales.',
           'delta': 'pp',
           'formula': '(Importaciones − Exportaciones) ÷ (Producción bruta + Importaciones − '
                      'Exportaciones) × 100',
           'dim': 'eco',
           'hallazgo_regional': 'La dependencia neta extrarregional aumentó de 1,7 % a 2,2 %, pero '
                                'se mantuvo reducida frente a la oferta eléctrica total del '
                                'bloque.'},
 'ENV1': {'nombre': 'Emisiones de GEI del sector eléctrico',
          'unidad': '',
          'formula': '',
          'delta': 'pct',
          'dim': 'env',
          'descripcion': 'Emisiones de gases de efecto invernadero (GEI) por la producción y uso '
                         'de energía, per cápita y por unidad de PIB. Cubre las emisiones de las '
                         'centrales eléctricas.',
          'nota': '',
          'hallazgo_regional': 'Las emisiones regionales de GEI disminuyeron hasta 2022 y luego '
                               'repuntaron, cerrando 2024 por encima de los niveles de 2020 tanto '
                               'por habitante como por unidad de PIB.',
          'series': [{'clave': 'ENV1_PC',
                      'etiqueta': 'Per cápita',
                      'unidad': 't CO₂eq/habitante',
                      'formula': 'Emisiones GEI de centrales eléctricas ÷ Población'},
                     {'clave': 'ENV1_PIB',
                      'etiqueta': 'Por unidad de PIB',
                      'unidad': 'kg CO₂eq/USD constantes 2015',
                      'formula': 'Emisiones GEI (kg) ÷ PIB real (USD constantes 2015)'}]},
 'ENV2': {'nombre': 'Contaminantes atmosféricos urbanos',
          'unidad': '',
          'formula': '',
          'delta': 'pct',
          'dim': 'env',
          'descripcion': 'Concentraciones ambientales de contaminantes atmosféricos en zonas '
                         'urbanas: SO₂ y partículas emitidas por las centrales eléctricas, per '
                         'cápita y por unidad de PIB.',
          'nota': '',
          'hallazgo_regional': 'Los contaminantes atmosféricos regionales descendieron al inicio '
                               'de la ventana y aumentaron en 2023–2024, con una heterogeneidad '
                               'nacional todavía elevada.',
          'series': [{'clave': 'ENV2_SO2_PC',
                      'etiqueta': 'SO₂ per cápita',
                      'unidad': 'kg/habitante',
                      'formula': 'Emisiones SO₂ de centrales eléctricas ÷ Población'},
                     {'clave': 'ENV2_PAR_PC',
                      'etiqueta': 'Partículas per cápita',
                      'unidad': 'kg/habitante',
                      'formula': 'Emisiones de partículas ÷ Población'},
                     {'clave': 'ENV2_SO2_PIB',
                      'etiqueta': 'SO₂ por PIB',
                      'unidad': 'g/USD constantes 2015',
                      'formula': 'Emisiones SO₂ (g) ÷ PIB real'},
                     {'clave': 'ENV2_PAR_PIB',
                      'etiqueta': 'Partículas por PIB',
                      'unidad': 'g/USD constantes 2015',
                      'formula': 'Emisiones de partículas (g) ÷ PIB real'}]},
 'ENV3': {'nombre': 'Emisiones atmosféricas del sistema',
          'unidad': '',
          'formula': '',
          'delta': 'pct',
          'dim': 'env',
          'descripcion': 'Emisiones de contaminantes atmosféricos procedentes de los sistemas '
                         'energéticos, en escala eléctrica: gramos emitidos por cada kWh de '
                         'producción bruta.',
          'nota': '',
          'hallazgo_regional': 'La intensidad regional de emisiones atmosféricas cayó hasta 2022 y '
                               'repuntó a 1,728 g/kWh en 2024, por encima del nivel de 2020.',
          'series': [{'clave': 'ENV3',
                      'etiqueta': 'Escala eléctrica',
                      'unidad': 'g/kWh',
                      'formula': '(SO₂ + NOx + CO + Partículas) ÷ Producción bruta'}]},
 'ENV6': {'nombre': 'Biomasa vs Saldo MER',
          'unidad': 'GWh',
          'formula': '',
          'delta': 'pct',
          'dim': 'env',
          'tipo': 'env6',
          'descripcion': 'Comparativo de inyección de biomasa vs saldo neto en el Mercado '
                         'Eléctrico Regional, por país. Saldo negativo = importador neto en el MER '
                         'ese año.',
          'nota': 'Comparativo de dos series expresadas en GWh; no calcula un cociente entre '
                  'ellas.',
          'hallazgo_regional': 'La biomasa sostuvo un aporte superior a 3.000 GWh durante la mayor '
                               'parte del período, mientras el saldo agregado del MER permaneció '
                               'cerca de cero por la compensación intrarregional.'},
 'SOC1': {'nombre': 'Población sin electricidad',
          'unidad': '',
          'formula': '',
          'delta': 'pp',
          'dim': 'soc',
          'descripcion': 'Porcentaje de hogares (o de población) sin electricidad o energía '
                         'comercial, o muy dependientes de energías no comerciales.',
          'nota': 'El agregado regional pondera cada país por su población (razón de sumas), '
                  'equivalente a personas sin electricidad del bloque ÷ población del bloque.',
          'hallazgo_regional': 'La población sin acceso a electricidad descendió hasta 6,72 % en '
                               '2024, aunque todavía representó aproximadamente 3,5 millones de '
                               'personas en el SIEPAC.',
          'series': [{'clave': 'SOC1',
                      'etiqueta': '',
                      'unidad': '%',
                      'formula': '100 − Tasa de electrificación total'}]},
 'SOC2': {'nombre': 'Ingreso destinado a electricidad',
          'unidad': '',
          'formula': '',
          'delta': 'pp',
          'dim': 'soc',
          'descripcion': 'Porcentaje del ingreso anual de referencia del hogar destinado a '
                         'electricidad, para el hogar promedio y el estrato vulnerable.',
          'nota': 'El agregado regional es una razón de sumas construida en USD. SOC2_PROM expande '
                  'por clientes residenciales; SOC2_VULNERABLE usa clientes vulnerables proxy (20 '
                  '% en cinco países y 29.6 % en Nicaragua). Cliente residencial se usa como '
                  'aproximación de unidad residencial consumidora conectada.',
          'hallazgo_regional': 'La carga del hogar promedio permaneció cerca del 2 %, mientras la '
                               'del estrato vulnerable siguió siendo más de seis veces mayor, con '
                               'una amplia brecha de asequibilidad.',
          'series': [{'clave': 'SOC2_PROM',
                      'etiqueta': 'Hogar promedio',
                      'unidad': '%',
                      'formula': 'Cargo anual medio residencial ÷ ingreso anual PROM × 100'},
                     {'clave': 'SOC2_VULNERABLE',
                      'etiqueta': 'Estrato vulnerable',
                      'unidad': '%',
                      'formula': 'Cargo anual medio residencial ÷ ingreso anual vulnerable × '
                                 '100'}]},
 'SOC3': {'nombre': 'Hogares con acceso a energía renovable',
          'unidad': '',
          'formula': '',
          'delta': 'pp',
          'dim': 'soc',
          'descripcion': 'Uso de energía en los hogares por grupo (rural/urbano) y combinación de '
                         'combustibles: hogares con acceso eléctrico ponderado por la '
                         'participación renovable de la generación.',
          'nota': 'Cada serie combina la tasa de electrificación de la zona con la participación '
                  'renovable de la generación nacional. El agregado rural pondera por población '
                  'rural y el urbano por población urbana.',
          'hallazgo_regional': 'El acceso urbano a electricidad de origen renovable permaneció por '
                               'encima del rural, pero ambos agregados se contrajeron con fuerza '
                               'entre 2022 y 2024.',
          'series': [{'clave': 'SOC3_RURAL',
                      'etiqueta': 'Rural',
                      'unidad': '%',
                      'formula': 'Tasa de electrificación rural × % renovable de la generación'},
                     {'clave': 'SOC3_URB',
                      'etiqueta': 'Urbano',
                      'unidad': '%',
                      'formula': 'Tasa de electrificación urbana × % renovable de la generación'}]}}

def ficha_serie(clave):
    """Definición científica de una salida nacional, identificada por código."""
    for codigo, ficha in FICHAS.items():
        if ficha.get("series"):
            for serie in ficha["series"]:
                if serie["clave"] == clave:
                    return serie
        elif codigo == clave:
            return ficha
    raise KeyError(clave)

# Listas de salidas derivadas del catálogo; ENV6 mantiene su contrato especial.
CODIGOS_ECO = [c for c, f in FICHAS.items() if f["dim"] == "eco"]
SERIES_ENV = [s["clave"] for f in FICHAS.values() if f["dim"] == "env"
              for s in f.get("series", [])]
SERIES_SOC = [s["clave"] for f in FICHAS.values() if f["dim"] == "soc"
              for s in f.get("series", [])]

# Denominadores propios de cada dimensión. El PIB ambiental no se sustituye
# por el económico. SOC2 ya llega agregado por razón de sumas desde su ETL.
PESOS_AGREGADO = {'ENV1_PC': 'poblacion_miles',
 'ENV1_PIB': 'pib_usd_const2015',
 'ENV2_SO2_PC': 'poblacion_miles',
 'ENV2_PAR_PC': 'poblacion_miles',
 'ENV2_SO2_PIB': 'pib_usd_const2015',
 'ENV2_PAR_PIB': 'pib_usd_const2015',
 'ENV3': 'produccion_bruta_gwh'}

PESOS_SOC3 = {'SOC3_RURAL': 'poblacion_rural_hab', 'SOC3_URB': 'poblacion_urbana_hab'}

# Redacciones históricas de Excel: solo se conservan literales donde difieren
# de FICHAS. Las coincidencias usan referencias a la definición autoritativa.
TEXTOS_EXCEL_ECO = {
    'ECO1': {
        'titulo': FICHAS['ECO1']['nombre'],
        'unidad': FICHAS['ECO1']['unidad'],
        'descripcion': 'Consumo Final Total (kWh) ÷ Población Total (habitantes)',
        'fuentes': 'SIELAC-OLADE (consumo); CEPAL-CELADE (población)',
    },
    'ECO2': {
        'titulo': FICHAS['ECO2']['nombre'],
        'unidad': FICHAS['ECO2']['unidad'],
        'descripcion': 'Consumo Final Total (kWh) ÷ PIB Real (USD constantes 2015)',
        'fuentes': 'SIELAC-OLADE (consumo); Banco Mundial NY.GDP.MKTP.KD (PIB)',
    },
    'ECO3': {
        'titulo': 'Eficiencia de la conversión y distribución de energía',
        'unidad': FICHAS['ECO3']['unidad'],
        'descripcion': '(Consumo Final Total ÷ Producción Bruta Total) × 100. Aproxima la eficiencia del sistema eléctrico desde generación hasta consumo final; no representa la cadena energética primaria completa.',
        'fuentes': 'SIELAC-OLADE (ambas variables)',
    },
    'ECO6': {
        'titulo': 'Intensidades energéticas de la industria',
        'unidad': FICHAS['ECO6']['unidad'],
        'descripcion': 'Consumo Final Industrial (kWh) ÷ Valor Agregado Manufacturero (USD constantes 2015). El VAM en USD ya fue calculado en el ETL como VAM%% (ODS 9.2.1) × PIB real.',
        'fuentes': 'SIELAC-OLADE (consumo industrial); CEPALSTAT ODS 9.2.1 × Banco Mundial (VAM)',
    },
    'ECO11': {
        'titulo': 'Porcentaje de combustibles fósiles en la electricidad',
        'unidad': FICHAS['ECO11']['unidad'],
        'descripcion': '(Generación Térmica Fósil ÷ Generación Total) × 100',
        'fuentes': 'SIELAC-OLADE (generación por tipo de fuente)',
    },
    'ECO13': {
        'titulo': 'Porcentaje de energías renovables en la electricidad',
        'unidad': FICHAS['ECO13']['unidad'],
        'descripcion': '(Hidro + Geotermia + Eólica + Solar + Biomasa) ÷ Generación Total × 100. La fórmula suma las cinco fuentes renovables explícitamente (no usa la columna agregada) para que el cálculo sea auditable componente a componente.',
        'fuentes': 'SIELAC-OLADE (generación por tipo de fuente)',
    },
    'ECO14': {
        'titulo': 'Precios de la energía de uso final por sector',
        'unidad': FICHAS['ECO14']['unidad'],
        'descripcion': 'Ingresos por energía regulada vendida (USD) ÷ energía regulada consumida (MWh), calculado en el ETL. En USD corrientes del año bajo análisis (no constantes). Las celdas sombreadas en amarillo son valores calculados mediante CAGR de la serie histórica 2015+ (ver Datos_Base, columna tarifa_fuente_dato).',
        'fuentes': 'CEPAL-SIECA (serie histórica); cálculo CAGR documentado en el ETL',
    },
    'ECO15': {
        'titulo': 'Dependencia de las importaciones netas de energía',
        'unidad': FICHAS['ECO15']['unidad'],
        'descripcion': '((Importaciones − Exportaciones) ÷ (Producción Bruta + Importaciones − Exportaciones)) × 100. Positivo = importador neto; negativo = exportador neto.',
        'fuentes': 'SIELAC-OLADE (matriz de balance energético; producción bruta)',
    },
}

TEXTOS_EXCEL_DIMENSIONES = {
    'ENV1_PC': {
        'titulo': 'ENV1 — Emisiones GEI per cápita',
        'unidad': 't CO2eq/habitante',
        'formula': 'Emisiones GEI de centrales eléctricas (10³ t) ÷ Población',
        'nota': 'Solo emisiones del sector de generación eléctrica.',
    },
    'ENV1_PIB': {
        'titulo': 'ENV1 — Emisiones GEI por unidad de PIB',
        'unidad': 'kg CO2eq/USD const. 2015',
        'formula': ficha_serie('ENV1_PIB')['formula'],
        # Redacción congelada; alcance y escala aclarados en AUDITORIA_ENV1_FALLBACK.md.
        'nota': 'Valor recuperado de la fórmula original =(A×10⁶)/PIB.',
    },
    'ENV2_SO2_PC': {
        'titulo': 'ENV2 — SO₂ per cápita',
        'unidad': ficha_serie('ENV2_SO2_PC')['unidad'],
        'formula': ficha_serie('ENV2_SO2_PC')['formula'],
        'nota': '',
    },
    'ENV2_PAR_PC': {
        'titulo': 'ENV2 — Partículas per cápita',
        'unidad': ficha_serie('ENV2_PAR_PC')['unidad'],
        'formula': ficha_serie('ENV2_PAR_PC')['formula'],
        'nota': '',
    },
    'ENV2_SO2_PIB': {
        'titulo': 'ENV2 — SO₂ por unidad de PIB',
        'unidad': 'g/USD const. 2015',
        'formula': ficha_serie('ENV2_SO2_PIB')['formula'],
        'nota': '',
    },
    'ENV2_PAR_PIB': {
        'titulo': 'ENV2 — Partículas por unidad de PIB',
        'unidad': 'g/USD const. 2015',
        'formula': ficha_serie('ENV2_PAR_PIB')['formula'],
        'nota': '',
    },
    'ENV3': {
        'titulo': 'ENV3 — Emisiones atmosféricas de los sistemas energéticos',
        'unidad': ficha_serie('ENV3')['unidad'],
        'formula': '(SO₂ + NOx + CO + PAR) ÷ Producción bruta',
        'nota': 'Escala eléctrica (g/kWh).',
    },
    'SOC1': {
        'titulo': 'SOC1 — Población sin acceso a electricidad',
        'unidad': ficha_serie('SOC1')['unidad'],
        'formula': ficha_serie('SOC1')['formula'],
        'nota': 'La columna TOTAL de la fuente (suma entre países) se descartó. La hoja cierra con dos resúmenes: Promedio de países (media simple) y Agregado regional (razón de sumas, ponderado por población: personas sin electricidad del bloque ÷ población del bloque).',
    },
    'SOC2_PROM': {
        'titulo': 'SOC2 — Ingreso destinado a electricidad (hogar promedio)',
        'unidad': ficha_serie('SOC2_PROM')['unidad'],
        'formula': 'Cargo anual medio residencial ÷ ingreso anual de referencia del hogar × 100',
        'nota': 'El agregado regional es la razón entre el gasto residencial proxy y el ingreso PROM proxy, ambos expandidos por clientes residenciales.',
    },
    'SOC2_VULNERABLE': {
        'titulo': 'SOC2 — Ingreso destinado a electricidad (estrato vulnerable)',
        'unidad': ficha_serie('SOC2_VULNERABLE')['unidad'],
        'formula': 'Cargo anual medio residencial ÷ ingreso anual del estrato vulnerable × 100',
        'nota': 'El agregado regional usa clientes vulnerables proxy: 20 % en cinco países y 29.6 % en Nicaragua.',
    },
    'SOC3_RURAL': {
        'titulo': 'SOC3 — Hogares rurales con acceso a energía renovable',
        'unidad': ficha_serie('SOC3_RURAL')['unidad'],
        'formula': ficha_serie('SOC3_RURAL')['formula'],
        'nota': 'Combina la tasa de electrificación rural con la participación renovable nacional. El agregado pondera por población rural.',
    },
    'SOC3_URB': {
        'titulo': 'SOC3 — Hogares urbanos con acceso a energía renovable',
        'unidad': ficha_serie('SOC3_URB')['unidad'],
        'formula': ficha_serie('SOC3_URB')['formula'],
        'nota': 'Combina la tasa de electrificación urbana con la participación renovable nacional. El agregado pondera por población urbana.',
    },
}
