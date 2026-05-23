"""
Genera Memoria_EDA_ETFs_UCITS.pdf con paleta personalizada.
Universo actualizado: INFR.AS sustituye a IQQP.DE.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_CENTER
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
    Table, TableStyle, PageBreak, NextPageTemplate
)

# ===== Paleta =====
BG       = HexColor('#FAFAF7')
TEXT     = HexColor('#2E2E2E')
BLUE     = HexColor('#A8C8E8')
DEEPBLUE = HexColor('#7AA8D0')
BRONZE   = HexColor('#C9A96E')
YELLOW   = HexColor('#F9E4A0')
ORANGE   = HexColor('#F4C18F')
WHITE    = HexColor('#FFFFFF')
SOFTGREY = HexColor('#E8E6E0')
MUTED    = HexColor('#6B6B6B')

PAGE_W, PAGE_H = A4

# ===== Layout (todas las medidas explícitas) =====
# Body
BODY_LEFT   = 2.2 * cm
BODY_RIGHT  = 2.2 * cm
BODY_TOP    = 2.4 * cm   # frame arranca a PAGE_H - BODY_TOP
BODY_BOTTOM = 2.2 * cm   # frame termina aquí

# Header / footer body
HEADER_Y    = PAGE_H - 1.4 * cm   # texto cabecera
HEADER_LINE = PAGE_H - 1.7 * cm   # línea bajo cabecera
FOOTER_LINE = 1.6 * cm
FOOTER_Y    = 1.05 * cm

# Cover
COVER_BAND_H   = 4.0 * cm                # banda azul superior
COVER_FRAME_TOP    = PAGE_H - COVER_BAND_H - 0.8 * cm   # margen libre bajo la banda
COVER_FRAME_BOTTOM = 5.0 * cm            # deja espacio para bloques deco + footer
COVER_FOOTER_LINE  = 2.0 * cm
COVER_FOOTER_Y     = 1.45 * cm

OUTPUT = 'C:/Users/juanl/OneDrive/Developer/TFM/ETFs/Memoria_EDA_ETFs_UCITS.pdf'

# ===== Estilos =====
styles = getSampleStyleSheet()
st_title = ParagraphStyle('Title', parent=styles['Title'], fontName='Helvetica-Bold',
    fontSize=24, leading=30, textColor=DEEPBLUE, alignment=TA_LEFT, spaceAfter=4)
st_subtitle = ParagraphStyle('Subtitle', parent=styles['Normal'], fontName='Helvetica',
    fontSize=12.5, leading=17, textColor=BRONZE, alignment=TA_LEFT, spaceAfter=14)
st_h1 = ParagraphStyle('H1', parent=styles['Heading1'], fontName='Helvetica-Bold',
    fontSize=16, leading=20, textColor=DEEPBLUE, spaceBefore=10, spaceAfter=8)
st_h3 = ParagraphStyle('H3', parent=styles['Heading3'], fontName='Helvetica-Bold',
    fontSize=10.5, leading=13, textColor=BRONZE, spaceBefore=8, spaceAfter=4)
st_body = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica',
    fontSize=9.8, leading=14, textColor=TEXT, alignment=TA_JUSTIFY, spaceAfter=5)
st_bullet = ParagraphStyle('Bullet', parent=st_body, leftIndent=14, bulletIndent=2,
    spaceAfter=3)
st_caption = ParagraphStyle('Caption', parent=styles['Normal'], fontName='Helvetica-Oblique',
    fontSize=8.5, leading=11, textColor=MUTED, spaceAfter=10)
st_callout_body = ParagraphStyle('CalloutBody', parent=st_body, fontSize=9.5, leading=13.5,
    leftIndent=4, rightIndent=4, spaceBefore=2, spaceAfter=2)


# ===== Decoración de página =====
def draw_cover(canv, doc):
    canv.saveState()
    canv.setFillColor(BG); canv.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # Banda superior
    canv.setFillColor(BLUE)
    canv.rect(0, PAGE_H - COVER_BAND_H, PAGE_W, COVER_BAND_H, fill=1, stroke=0)
    canv.setFillColor(DEEPBLUE)
    canv.rect(0, PAGE_H - COVER_BAND_H - 0.18*cm, PAGE_W, 0.18*cm, fill=1, stroke=0)
    # Bloques decorativos inferiores
    by = 3.4*cm
    canv.setFillColor(YELLOW); canv.rect(BODY_LEFT,            by, 1.2*cm, 1.2*cm, fill=1, stroke=0)
    canv.setFillColor(ORANGE); canv.rect(BODY_LEFT + 1.4*cm,   by, 1.2*cm, 1.2*cm, fill=1, stroke=0)
    canv.setFillColor(BRONZE); canv.rect(BODY_LEFT + 2.8*cm,   by, 1.2*cm, 1.2*cm, fill=1, stroke=0)
    # Footer
    canv.setStrokeColor(BRONZE); canv.setLineWidth(0.6)
    canv.line(BODY_LEFT, COVER_FOOTER_LINE, PAGE_W - BODY_RIGHT, COVER_FOOTER_LINE)
    canv.setFont('Helvetica', 9); canv.setFillColor(TEXT)
    canv.drawString(BODY_LEFT, COVER_FOOTER_Y,
                    'TFM — Fase 1 (M2): Análisis Exploratorio de Datos')
    canv.drawRightString(PAGE_W - BODY_RIGHT, COVER_FOOTER_Y,
                         'Universo de ETFs UCITS')
    canv.restoreState()


def draw_body(canv, doc):
    canv.saveState()
    canv.setFillColor(BG); canv.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # Cabecera
    canv.setFillColor(DEEPBLUE)
    canv.setFont('Helvetica-Bold', 9)
    canv.drawString(BODY_LEFT, HEADER_Y, 'MEMORIA EDA — ETFs UCITS')
    canv.setFillColor(BRONZE)
    canv.drawRightString(PAGE_W - BODY_RIGHT, HEADER_Y, 'TFM · Fase 1 · M2')
    canv.setStrokeColor(BLUE); canv.setLineWidth(0.5)
    canv.line(BODY_LEFT, HEADER_LINE, PAGE_W - BODY_RIGHT, HEADER_LINE)
    # Footer
    canv.setStrokeColor(BRONZE); canv.setLineWidth(0.4)
    canv.line(BODY_LEFT, FOOTER_LINE, PAGE_W - BODY_RIGHT, FOOTER_LINE)
    canv.setFont('Helvetica', 8.5); canv.setFillColor(MUTED)
    canv.drawString(BODY_LEFT, FOOTER_Y, 'Juan Rilo · 2026')
    canv.drawRightString(PAGE_W - BODY_RIGHT, FOOTER_Y, f'Página {doc.page - 1}')
    canv.restoreState()


# ===== Helpers =====
CONTENT_W = PAGE_W - BODY_LEFT - BODY_RIGHT

def callout(title, body_html, color=YELLOW):
    inner = [
        Paragraph(f'<b>{title}</b>', ParagraphStyle('coT', parent=st_h3,
            textColor=DEEPBLUE, spaceBefore=0, spaceAfter=2, fontSize=10.5)),
        Paragraph(body_html, st_callout_body),
    ]
    t = Table([[inner]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), WHITE),
        ('LINEBEFORE', (0,0), (0,-1), 3, color),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.3, SOFTGREY),
    ]))
    return t


def styled_table(data, col_widths=None, header_bg=DEEPBLUE, header_fg=WHITE,
                 zebra=True, align='LEFT'):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ('BACKGROUND', (0,0), (-1,0), header_bg),
        ('TEXTCOLOR',  (0,0), (-1,0), header_fg),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 8.8),
        ('ALIGN',      (0,0), (-1,-1), align),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING',  (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING',   (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0), (-1,-1), 5),
        ('LINEBELOW', (0,0), (-1,0), 0.6, BRONZE),
        ('TEXTCOLOR', (0,1), (-1,-1), TEXT),
    ]
    if zebra:
        for i in range(1, len(data)):
            bg = HexColor('#F3F0EA') if i % 2 == 0 else WHITE
            style.append(('BACKGROUND', (0,i), (-1,i), bg))
    t.setStyle(TableStyle(style))
    return t


def section_header(num, title):
    block = Table([
        [Paragraph(f'<font color="#FFFFFF"><b>{num}</b></font>',
                   ParagraphStyle('n', parent=st_h1, textColor=WHITE,
                                  alignment=TA_CENTER, fontSize=18, leading=20)),
         Paragraph(title, st_h1)]
    ], colWidths=[1.05*cm, CONTENT_W - 1.05*cm])
    block.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), DEEPBLUE),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (0,0), 0),
        ('RIGHTPADDING', (0,0), (0,0), 0),
        ('LEFTPADDING', (1,0), (1,0), 10),
        ('TOPPADDING', (0,0), (0,0), 4),
        ('BOTTOMPADDING', (0,0), (0,0), 4),
        ('TOPPADDING', (1,0), (1,0), 0),
        ('BOTTOMPADDING', (1,0), (1,0), 0),
    ]))
    return block


# ===== Documento =====
doc = BaseDocTemplate(OUTPUT, pagesize=A4,
    leftMargin=BODY_LEFT, rightMargin=BODY_RIGHT,
    topMargin=BODY_TOP, bottomMargin=BODY_BOTTOM,
    title='Memoria EDA — ETFs UCITS', author='Juan Rilo')

frame_cover = Frame(
    BODY_LEFT, COVER_FRAME_BOTTOM,
    CONTENT_W, COVER_FRAME_TOP - COVER_FRAME_BOTTOM,
    id='cover',
    leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
)
frame_body = Frame(
    BODY_LEFT, BODY_BOTTOM,
    CONTENT_W, PAGE_H - BODY_TOP - BODY_BOTTOM,
    id='body',
    leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
)

doc.addPageTemplates([
    PageTemplate(id='Cover', frames=[frame_cover], onPage=draw_cover),
    PageTemplate(id='Body',  frames=[frame_body],  onPage=draw_body),
])

story = []

# ==================== PORTADA ====================
story.append(Paragraph('Memoria de Análisis<br/>Exploratorio de Datos', st_title))
story.append(Paragraph('Universo de ETFs UCITS para construcción de carteras multiperfil',
                       st_subtitle))
story.append(Spacer(1, 0.3*cm))

meta = [
    ['Fase del TFM',     'Fase 1 — Módulo M2 (EDA)'],
    ['Notebook',         'eda_etfs_ucits.ipynb'],
    ['Período de datos', '2010-09-06 → 2026-04-24 (15.92 años)'],
    ['Universo',         '9 ETFs UCITS multiclase'],
    ['Outputs M3',       'returns.parquet · mu.pkl · cov_ledoit_wolf.pkl'],
    ['Autor',            'Juan Rilo'],
    ['Fecha',            '25 de abril de 2026'],
]
mt = Table(meta, colWidths=[4.3*cm, CONTENT_W - 4.3*cm])
mt.setStyle(TableStyle([
    ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
    ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
    ('FONTSIZE', (0,0), (-1,-1), 9.5),
    ('TEXTCOLOR', (0,0), (0,-1), DEEPBLUE),
    ('TEXTCOLOR', (1,0), (1,-1), TEXT),
    ('LINEBELOW', (0,0), (-1,-1), 0.3, SOFTGREY),
    ('TOPPADDING', (0,0), (-1,-1), 6),
    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ('LEFTPADDING', (0,0), (-1,-1), 0),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
]))
story.append(mt)

story.append(Spacer(1, 0.7*cm))
story.append(callout(
    'Propósito de este documento',
    'Documentar de forma reproducible el proceso de análisis exploratorio realizado sobre el '
    'universo de 9 ETFs UCITS, las decisiones metodológicas tomadas, los hallazgos relevantes '
    'y los inputs estadísticos generados para alimentar el módulo de optimización de carteras (M3).',
    color=BRONZE
))

story.append(NextPageTemplate('Body'))
story.append(PageBreak())

# ==================== ÍNDICE ====================
story.append(Paragraph('Índice', st_h1))
story.append(Spacer(1, 0.2*cm))
toc_data = [
    ['1.', 'Objetivos y alcance', '3'],
    ['2.', 'Universo de ETFs seleccionado', '3'],
    ['3.', 'Descarga y carga de datos', '4'],
    ['4.', 'Calidad de datos y limpieza', '5'],
    ['5.', 'Retornos diarios y momentos', '6'],
    ['6.', 'Volatilidad anualizada', '7'],
    ['7.', 'Matriz de correlaciones', '8'],
    ['8.', 'Matriz de covarianza con Ledoit-Wolf', '9'],
    ['9.', 'Análisis de drawdowns', '10'],
    ['10.','Comparativa frente a benchmarks', '10'],
    ['11.','Decisiones metodológicas — síntesis', '11'],
    ['12.','Veredicto Go/No-Go de Fase 1', '12'],
    ['13.','Outputs y trazabilidad para M3', '12'],
]
toc = Table(toc_data, colWidths=[1.0*cm, CONTENT_W - 2.5*cm, 1.5*cm])
toc.setStyle(TableStyle([
    ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
    ('TEXTCOLOR', (0,0), (0,-1), BRONZE),
    ('FONTSIZE', (0,0), (-1,-1), 10),
    ('TEXTCOLOR', (1,0), (1,-1), TEXT),
    ('TEXTCOLOR', (2,0), (2,-1), DEEPBLUE),
    ('ALIGN', (2,0), (2,-1), 'RIGHT'),
    ('LINEBELOW', (0,0), (-1,-1), 0.3, SOFTGREY),
    ('TOPPADDING', (0,0), (-1,-1), 7),
    ('BOTTOMPADDING', (0,0), (-1,-1), 7),
]))
story.append(toc)
story.append(PageBreak())

# ==================== 1. OBJETIVOS ====================
story.append(section_header('1', 'Objetivos y alcance'))
story.append(Paragraph(
    'El presente análisis exploratorio constituye la fase de validación previa a la optimización '
    'de carteras del TFM. Su objetivo es triple: (i) verificar la idoneidad estadística del universo '
    'de ETFs preseleccionado en la Fase 0, (ii) caracterizar el comportamiento histórico de cada '
    'activo en términos de retorno, riesgo, asimetría y comovimiento, y (iii) generar los inputs '
    'depurados que consumirá el motor de optimización (M3) sin necesidad de reprocesado posterior.',
    st_body))

story.append(Paragraph('Hipótesis a validar', st_h3))
for h in [
    'Los 9 ETFs disponen de historia común suficiente (≥ 10 años) para estimar momentos de forma robusta.',
    'Cada ETF se sitúa, en términos de volatilidad y drawdown, en el rango esperado para su clase de activo.',
    'El universo presenta diversidad de comovimiento suficiente para construir carteras eficientes.',
    'La covarianza muestral es razonablemente estable o, en caso contrario, el shrinkage de Ledoit-Wolf la regulariza.',
]:
    story.append(Paragraph(f'• {h}', st_bullet))

story.append(Spacer(1, 0.15*cm))
story.append(callout(
    'Criterio de éxito de la fase',
    'La fase se considera <b>superada</b> cuando: (1) todos los ETFs cuentan con datos limpios desde la '
    'fecha común de inicio, (2) no se observan pares con correlación &gt; 0.95 (redundancia crítica), '
    '(3) la matriz Σ resultante es definida positiva, y (4) los outputs <i>mu</i> y <i>Σ</i> quedan '
    'persistidos y reproducibles.', color=ORANGE))

# ==================== 2. UNIVERSO ====================
story.append(section_header('2', 'Universo de ETFs seleccionado'))
story.append(Paragraph(
    'El universo se compone de 9 ETFs UCITS cotizados en mercados europeos, seleccionados por su '
    'liquidez, replicabilidad física, costes ajustados (TER &lt; 0.50%) y por cubrir las principales '
    'clases de activo necesarias para construir tres perfiles de inversor: conservador, moderado y agresivo.',
    st_body))

universe = [
    ['Ticker', 'Nombre', 'Clase de activo', 'Perfil'],
    ['IBGS.AS', 'iShares EUR Govt Bond 1-3yr',     'RF soberana corto EUR',    'Conservador'],
    ['IEAG.AS', 'iShares Core EUR Govt Bond',      'RF soberana agregada EUR', 'Conservador'],
    ['EUNH.DE', 'iShares Core EUR Corp Bond IG',   'RF corporativa IG EUR',    'Conservador / Moderado'],
    ['IHYG.L',  'iShares EUR High Yield Corp',     'RF high yield EUR',        'Moderado'],
    ['EXSA.DE', 'iShares STOXX Europe 600',        'RV Europa',                'Moderado / Agresivo'],
    ['INFR.AS', 'iShares Global Infrastructure',   'Infraestructura (real)',   'Moderado'],
    ['IEEM.L',  'iShares MSCI EM (Dist)',          'RV emergentes',            'Agresivo'],
    ['IWDA.AS', 'iShares Core MSCI World',         'RV global desarrollada',   'Moderado / Agresivo'],
    ['EQQQ.DE', 'Invesco Nasdaq-100 UCITS',        'RV tecnológica US',        'Agresivo'],
]
story.append(Spacer(1, 0.15*cm))
story.append(styled_table(universe,
    col_widths=[1.9*cm, 5.0*cm, 4.5*cm, CONTENT_W - 11.4*cm]))
story.append(Spacer(1, 0.1*cm))
story.append(Paragraph(
    'Tabla 1. Universo definitivo del estudio. Sustitución de IQQP.DE (Property, σ=18.5%) por '
    'INFR.AS (Infrastructure, σ=13.8%) — véase decisión D7.', st_caption))
story.append(PageBreak())

# ==================== 3. DESCARGA ====================
story.append(section_header('3', 'Descarga y carga de datos'))
story.append(Paragraph(
    'Los precios diarios ajustados (dividendos y splits) se obtienen mediante <i>yfinance</i> con '
    'parámetro <font face="Courier">auto_adjust=True</font>, desde el 1 de enero de 2010 hasta la '
    'fecha de ejecución. La columna utilizada es <i>Close</i>, ya ajustada por dividendos y splits, '
    'lo que garantiza retornos totales comparables.', st_body))

story.append(Paragraph('Decisión: precios ajustados frente a precios crudos', st_h3))
story.append(Paragraph(
    'Se opta por precios ajustados porque la métrica de interés es el <b>retorno total al inversor</b>, '
    'no la cotización nominal. Para ETFs de distribución (como IEEM.L) ignorar dividendos infravaloraría '
    'sistemáticamente el retorno.', st_body))

story.append(Paragraph('Inspección inicial', st_h3))
inspect = [
    ['Ticker', 'Primera fecha disponible', '% missing pre-limpieza'],
    ['IBGS.AS', '2010-01-04', '0.29%'],
    ['IEAG.AS', '2010-01-04', '0.26%'],
    ['EUNH.DE', '2010-01-04', '1.03%'],
    ['IHYG.L',  '2010-09-03', '5.59%'],
    ['EXSA.DE', '2010-01-04', '1.08%'],
    ['INFR.AS', '2010-01-04', '0.31%'],
    ['IEEM.L',  '2010-01-04', '1.60%'],
    ['IWDA.AS', '2010-01-04', '0.29%'],
    ['EQQQ.DE', '2010-01-04', '1.08%'],
]
story.append(styled_table(inspect, col_widths=[3.0*cm, 5.5*cm, CONTENT_W - 8.5*cm]))
story.append(Spacer(1, 0.1*cm))
story.append(Paragraph('Tabla 2. Cobertura inicial por ticker.', st_caption))

story.append(callout(
    'Hallazgo · IHYG.L marca el inicio común',
    'IHYG.L (high yield EUR) es el ETF con cotización más tardía: 3 de septiembre de 2010. Esto fija '
    'el período común a partir del cual se realizan todos los cálculos: <b>2010-09-06 a 2026-04-24</b>. '
    'Se acepta esta restricción ya que aún quedan <b>15.92 años</b> de historia, holgadamente por '
    'encima del umbral de 10 años establecido como criterio go/no-go.', color=BLUE))

# ==================== 4. CALIDAD ====================
story.append(section_header('4', 'Calidad de datos y limpieza'))
story.append(Paragraph('Se aplican tres pasos de limpieza, en orden:', st_body))

story.append(Paragraph('① Forward-fill limitado', st_h3))
story.append(Paragraph(
    'Los días de festivo cruzados entre mercados (LSE, Xetra, Euronext) generan NaN aislados. '
    'Se aplica <font face="Courier">ffill(limit=3)</font>: rellenar como máximo 3 días consecutivos. '
    'Esto absorbe el calendario sin enmascarar suspensiones de cotización reales.', st_body))

story.append(Paragraph('② Recorte al período común', st_h3))
story.append(Paragraph(
    'Se descartan las fechas anteriores a la primera observación válida del último ETF en incorporarse '
    '(IHYG.L, 2010-09-06). El resultado son 4 012 observaciones diarias completas para los 9 activos.',
    st_body))

story.append(Paragraph('③ Filtro de bad ticks (decisión crítica)', st_h3))
story.append(Paragraph(
    'La inspección posterior reveló <b>anomalías evidentes en EQQQ.DE</b>: precios aislados que se '
    'desviaban más del 30 % del baseline durante una sola sesión y volvían el día siguiente '
    '(p. ej., 2011-06-02: salto del precio normal ~37 € a 53 €). Sin filtrado, la volatilidad '
    'anualizada inflaba a 38.8 %, frente al 21 % real, y la correlación con IWDA caía a 0.41 '
    '(debería estar próxima a 0.78).', st_body))

story.append(callout(
    'Regla aplicada',
    'Se marca como bad tick cualquier observación cuyo retorno frente al día anterior <b>y</b> frente al '
    'día siguiente exceda el ±20 % en valor absoluto, con signos coherentes con un round-trip '
    '(spike-y-vuelta). Estas observaciones se sustituyen por NaN y se rellenan vía forward-fill. El filtro '
    'corrigió 7 ticks en EQQQ.DE concentrados en 2011, sin afectar a ningún otro ticker.', color=ORANGE))

story.append(Paragraph(
    'El umbral del 20 % es deliberadamente conservador: ni siquiera el lunes negro del COVID '
    '(16-marzo-2020, –12 % en S&amp;P 500) lo cruzaría.', st_body))

story.append(PageBreak())

# ==================== 5. RETORNOS ====================
story.append(section_header('5', 'Retornos diarios y momentos'))
story.append(Paragraph(
    'Se calculan los retornos simples mediante <font face="Courier">pct_change()</font>. '
    'Se prefieren a los logarítmicos porque la teoría de carteras de Markowitz que se aplicará en M3 '
    'asume retornos aritméticos: el retorno de la cartera es la combinación lineal ponderada de los '
    'retornos de los activos, propiedad que solo cumple <i>r</i> = Δp/p.', st_body))

returns_tbl = [
    ['Ticker', 'μ anual', 'σ diaria', 'Skewness', 'Kurtosis exc.'],
    ['IBGS.AS', '0.76%',  '0.13%', '–1.02', '31.9'],
    ['IEAG.AS', '1.17%',  '0.28%', '–0.63', '12.9'],
    ['EUNH.DE', '1.26%',  '0.32%', '–0.07', '7.6'],
    ['IHYG.L',  '3.54%',  '0.42%', '–2.39', '56.3'],
    ['EXSA.DE', '9.03%',  '1.02%', '–0.78', '10.3'],
    ['INFR.AS', '7.15%',  '0.87%', '–0.76', '10.3'],
    ['IEEM.L',  '5.57%',  '1.16%', '–0.36', '4.9'],
    ['IWDA.AS', '12.38%', '0.96%', '–0.53', '7.0'],
    ['EQQQ.DE', '20.15%', '1.35%', '+1.22', '65.4'],
]
story.append(styled_table(returns_tbl,
    col_widths=[2.4*cm, 2.5*cm, 2.5*cm, 2.5*cm, CONTENT_W - 9.9*cm],
    align='CENTER'))
story.append(Spacer(1, 0.1*cm))
story.append(Paragraph(
    'Tabla 3. Estadísticos descriptivos de los retornos diarios. μ anualizado × 252.', st_caption))

story.append(Paragraph('Hallazgos clave', st_h3))
for b in [
    '<b>Fat tails universales:</b> todos los ETFs presentan kurtosis exceso significativamente positiva '
    '(rango 4.9–65.4). Los retornos no son normales; los percentiles extremos están infraestimados por '
    'una distribución gaussiana. Justifica usar HRP o métricas robustas en M3 además de Markowitz puro.',
    '<b>Asimetría negativa generalizada en RF:</b> IHYG.L (–2.39) e IBGS.AS (–1.02) presentan '
    'la cola izquierda más severa, coherente con riesgo de eventos de crédito y tipos.',
    '<b>EQQQ.DE positivamente asimétrico:</b> skew = +1.22, dominado por días de fuerte rebote '
    'tecnológico — consistente con la era post-2010 del Nasdaq.',
    '<b>Coherencia con clase de activo:</b> los retornos medios anualizados encajan con expectativas '
    'académicas: RF EUR ≈ 0–4 %, RV global desarrollada ≈ 9–12 %, infraestructura ≈ 7 %, Nasdaq ≈ 20 %.',
]:
    story.append(Paragraph(f'• {b}', st_bullet))

# ==================== 6. VOLATILIDAD ====================
story.append(section_header('6', 'Volatilidad anualizada'))
story.append(Paragraph(
    'La volatilidad anualizada se obtiene como σ<sub>diaria</sub> × √252, asumiendo independencia '
    'entre observaciones consecutivas (la autocorrelación serial de retornos diarios de ETFs líquidos '
    'es estadísticamente despreciable).', st_body))

vol_tbl = [
    ['Perfil esperado', 'Ticker', 'σ anual', 'Encaja en perfil'],
    ['Conservador (< 8%)',     'IBGS.AS', '1.99%',  '✓'],
    ['Conservador',            'IEAG.AS', '4.37%',  '✓'],
    ['Conservador',            'EUNH.DE', '5.14%',  '✓'],
    ['Moderado (8 – 18%)',     'IHYG.L',  '6.58%',  '✓ (límite bajo)'],
    ['Moderado / Agresivo',    'EXSA.DE', '16.19%', '✓'],
    ['Moderado (diversific.)', 'INFR.AS', '13.78%', '✓'],
    ['Agresivo (> 15%)',       'IEEM.L',  '18.46%', '✓'],
    ['Moderado / Agresivo',    'IWDA.AS', '15.20%', '✓'],
    ['Agresivo',               'EQQQ.DE', '21.36%', '✓'],
]
story.append(styled_table(vol_tbl,
    col_widths=[5.0*cm, 2.5*cm, 2.3*cm, CONTENT_W - 9.8*cm], align='CENTER'))
story.append(Spacer(1, 0.1*cm))
story.append(Paragraph('Tabla 4. Volatilidad anualizada por ETF y validación frente al perfil objetivo.',
    st_caption))

story.append(callout(
    'Validación · Universo coherente con el diseño de perfiles',
    'Tras la sustitución de IQQP.DE por INFR.AS, los <b>9 ETFs encajan en su perfil objetivo</b>. '
    'INFR.AS aporta exposición a infraestructura global (real assets) con σ = 13.78 %, propia de un '
    'activo de riesgo moderado, no de un equity emergente disfrazado.', color=ORANGE))

story.append(PageBreak())

# ==================== 7. CORRELACIONES ====================
story.append(section_header('7', 'Matriz de correlaciones'))
story.append(Paragraph(
    'Se calcula la correlación de Pearson sobre retornos diarios. Es la métrica estándar para input '
    'directo en optimización media-varianza. La interpretación se centra en dos extremos: pares con '
    'ρ > 0.85 (redundancia) y pares con ρ < 0.20 (diversificadores eficientes).', st_body))

story.append(Paragraph('Pares con ρ > 0.85 — redundancia potencial', st_h3))
high_corr = [
    ['Par', 'ρ', 'Interpretación'],
    ['IEAG.AS / EUNH.DE', '0.91', 'Govt EUR vs Corp IG EUR — duración y curva de tipos comunes'],
    ['EXSA.DE / IWDA.AS', '0.87', 'Europa pesa ~17 % en MSCI World; comovimiento estructural'],
]
story.append(styled_table(high_corr, col_widths=[5.5*cm, 1.6*cm, CONTENT_W - 7.1*cm], align='LEFT'))

story.append(Paragraph('Pares con ρ < 0.10 — diversificadores eficientes', st_h3))
low_corr = [
    ['Par', 'ρ', 'Interpretación'],
    ['EUNH.DE / IEEM.L',  '0.01', 'Crédito IG europeo vs RV emergente — vehículos de riesgo distintos'],
    ['IEAG.AS / IEEM.L',  '0.03', 'RF soberana EUR descorrelacionada de emergentes'],
    ['EUNH.DE / IWDA.AS', '0.04', 'Crédito IG y RV global desarrollada actúan en regímenes opuestos'],
    ['EUNH.DE / EQQQ.DE', '0.04', 'Excelente complemento defensivo de la cartera tecnológica'],
    ['IBGS.AS / EQQQ.DE', '0.06', 'RF corto vs Nasdaq — descorrelación clásica risk-on/risk-off'],
]
story.append(styled_table(low_corr, col_widths=[5.5*cm, 1.6*cm, CONTENT_W - 7.1*cm], align='LEFT'))
story.append(Spacer(1, 0.1*cm))

story.append(Paragraph('INFR.AS · perfil de correlaciones', st_h3))
story.append(Paragraph(
    'INFR.AS muestra ρ moderada con renta variable global (0.77 con IWDA, 0.67 con EXSA), pero '
    '<b>baja con renta fija EUR</b> (0.12 con IBGS, 0.17 con IEAG, 0.15 con EUNH). Este perfil lo '
    'convierte en un complemento eficiente para el bloque defensivo de las carteras moderadas: aporta '
    'retorno tipo equity con escasa correlación con el grueso de la RF, mejorando la frontera eficiente.',
    st_body))

story.append(callout(
    'Decisión · Mantener IEAG y EUNH a pesar de ρ = 0.91',
    'A pesar de su elevada correlación, ambos ETFs cumplen funciones distintas en términos de '
    'exposición (soberano vs. corporativo IG). El optimizador en M3 tendrá libertad para asignar peso '
    'cero a uno de ellos si la frontera eficiente lo dicta. Se prefiere ofrecer al motor un universo '
    'ligeramente redundante que cercenarlo arbitrariamente.', color=BRONZE))

# ==================== 8. LEDOIT-WOLF ====================
story.append(section_header('8', 'Matriz de covarianza con Ledoit-Wolf'))
story.append(Paragraph(
    'La covarianza muestral es un estimador insesgado pero altamente <b>ruidoso</b> cuando el número '
    'de activos N es grande relativo a las observaciones T. Pequeños errores en Σ se amplifican en '
    'pesos extremos al invertir la matriz dentro del problema de Markowitz. Para mitigarlo se aplica '
    'el shrinkage de Ledoit-Wolf:', st_body))

story.append(Paragraph(
    '<para alignment="center"><b>Σ<sub>LW</sub> = (1 − α) · S + α · F</b></para>',
    ParagraphStyle('eq', parent=st_body, alignment=TA_CENTER, fontSize=11,
                   textColor=DEEPBLUE, spaceBefore=4, spaceAfter=8)))

story.append(Paragraph(
    'donde S es la covarianza muestral, F es un target estructurado (matriz con varianzas en la diagonal '
    'y correlación promedio fuera de ella) y α es el coeficiente óptimo de mezcla, estimado analíticamente '
    'según Ledoit y Wolf (2004).', st_body))

story.append(Paragraph('Resultado obtenido', st_h3))
lw_tbl = [
    ['Métrica', 'Valor', 'Lectura'],
    ['Coeficiente α',         '0.0073', 'Muy bajo: la muestral es ya bastante estable'],
    ['‖S − Σ_LW‖_F / ‖S‖_F',  '< 1%',   'Σ apenas se modifica respecto a la muestral'],
    ['Σ_LW definida positiva','Sí',     'Apta como input directo del optimizador en M3'],
]
story.append(styled_table(lw_tbl, col_widths=[5.0*cm, 2.5*cm, CONTENT_W - 7.5*cm], align='LEFT'))

story.append(callout(
    'Justificación de mantener Ledoit-Wolf pese a α bajo',
    'Con T ≈ 4 012 observaciones y N = 9 activos, el ratio T/N es elevado y la muestral es '
    'razonablemente estable, lo que explica el α reducido. Aún así, se conserva el estimador shrinked '
    'como input de M3 por tres motivos: (i) garantía formal de matriz definida positiva, (ii) coste '
    'computacional nulo, (iii) coherencia metodológica con la literatura de carteras robustas — '
    'defensible académicamente.', color=YELLOW))

story.append(PageBreak())

# ==================== 9. DRAWDOWNS ====================
story.append(section_header('9', 'Análisis de drawdowns'))
story.append(Paragraph(
    'El drawdown se calcula como la caída relativa desde el máximo histórico acumulado: '
    'DD<sub>t</sub> = P<sub>t</sub> / max(P<sub>τ≤t</sub>) − 1. El máximo drawdown (MDD) cuantifica '
    'la pérdida más severa que un inversor habría sufrido manteniendo el ETF de forma continua.',
    st_body))

dd_tbl = [
    ['Ticker', 'MDD', 'Fecha', 'Episodio dominante'],
    ['IBGS.AS', '–6.15%',  '2023-03-07', 'Subida de tipos BCE'],
    ['IEAG.AS', '–20.51%', '2022-10-21', 'Peor año histórico para soberanos EUR (2022)'],
    ['EUNH.DE', '–22.43%', '2023-09-28', 'Crédito IG; tipos altos sostenidos'],
    ['IHYG.L',  '–25.61%', '2020-03-18', 'COVID 2020'],
    ['EXSA.DE', '–35.70%', '2020-03-18', 'COVID 2020'],
    ['INFR.AS', '–34.56%', '2020-03-23', 'COVID 2020 (utilities y transporte)'],
    ['IEEM.L',  '–37.41%', '2016-01-20', 'Devaluación CNY / sell-off emergentes'],
    ['IWDA.AS', '–33.63%', '2020-03-23', 'COVID 2020'],
    ['EQQQ.DE', '–31.30%', '2022-12-28', 'Bear tecnológico 2022'],
]
story.append(styled_table(dd_tbl,
    col_widths=[2.2*cm, 2.2*cm, 2.5*cm, CONTENT_W - 6.9*cm], align='LEFT'))
story.append(Spacer(1, 0.1*cm))
story.append(Paragraph('Tabla 5. Máximo drawdown observado en el período común y episodio responsable.',
    st_caption))

story.append(Paragraph(
    'Mensaje clave para la memoria al cliente final: <b>incluso los activos calificados como '
    'conservadores han experimentado pérdidas significativas en escenarios concretos</b> (IEAG –20.5% '
    'en 2022 al subir el BCE los tipos, EUNH –22.4% en 2023). Las expectativas de drawdown deben '
    'fijarse mirando 2022 y 2020, no únicamente el promedio.', st_body))

# ==================== 10. BENCHMARKS ====================
story.append(section_header('10', 'Comparativa frente a benchmarks'))
story.append(Paragraph(
    'Se construyen dos benchmarks de referencia: (1) cartera 60/40 estática usando '
    '<font face="Courier">0.6 · IWDA + 0.4 · IEAG</font>, considerada el "mínimo competitivo" para '
    'una cartera diversificada; (2) SPY como proxy de RV americana de referencia.', st_body))

story.append(callout(
    'Criterio de éxito M4 (heredado de Fase 0)',
    'La cartera moderada construida en M4 deberá presentar un Sharpe ratio histórico (en backtest fuera '
    'de muestra) <b>igual o superior</b> al del benchmark 60/40 sobre el mismo período. De lo contrario, '
    'el motor de optimización no aporta valor frente a una asignación naive.', color=BLUE))

story.append(PageBreak())

# ==================== 11. DECISIONES ====================
story.append(section_header('11', 'Decisiones metodológicas — síntesis'))
story.append(Paragraph(
    'Se recopilan en una única tabla las decisiones tomadas durante el EDA, su motivación y su '
    'impacto previsible en fases posteriores. Esta tabla es la principal aportación documental de '
    'la memoria para garantizar trazabilidad.', st_body))

dec = [
    ['#', 'Decisión', 'Motivación', 'Impacto en fases siguientes'],
    ['D1', 'Período: 2010-09-06 → 2026-04-24',
       'Inicio común determinado por IHYG.L; 15.92 años cubren ZIRP, COVID y normalización post-2022.',
       'Inputs robustos a M3.'],
    ['D2', 'Precios ajustados (auto_adjust=True)',
       'Métrica relevante = retorno total al inversor; ETFs de distribución requieren ajuste por dividendos.',
       'Evita sesgo a la baja en RF y RV emergente.'],
    ['D3', 'Forward-fill ≤ 3 días',
       'Absorbe festivos cruzados sin enmascarar suspensiones reales.',
       'Series alineadas en calendario común.'],
    ['D4', 'Filtro bad-tick ±20 % round-trip',
       'EQQQ.DE tiene ticks erróneos en 2011. Sin filtro, σ inflada de 21 % a 39 %.',
       'σ y ρ realistas.'],
    ['D5', 'Retornos simples (no log)',
       'Compatibilidad directa con la formulación lineal de Markowitz.',
       'Pesos óptimos interpretables sin transformación.'],
    ['D6', 'Mantener IEAG y EUNH pese a ρ = 0.91',
       'Cumplen funciones distintas (soberano vs. crédito IG); el optimizador puede asignar peso cero.',
       'Universo de 9 activos preservado en M3.'],
    ['D7', 'Sustituir IQQP.DE por INFR.AS',
       'IQQP σ = 18.5 % (equivalente a RV emergente) no era diversificador moderado. INFR σ = 13.8 % y baja correlación con RF.',
       'Perfil moderado correctamente representado.'],
    ['D8', 'Conservar Ledoit-Wolf pese a α = 0.0073',
       'Garantiza Σ definida positiva, coste nulo, defensible académicamente.',
       'Σ_LW como input estable del problema cuadrático en M3.'],
    ['D9', 'Anualización con 252 días de mercado',
       'Convención estándar; coherente con la literatura y proveedores.',
       'Métricas comparables con benchmarks externos.'],
]
# Convertir celdas de texto largo a Paragraph para que envuelvan
def wrap_cell(text, font_size=8.2):
    style = ParagraphStyle('cell', parent=st_body, fontSize=font_size,
                           leading=font_size + 2, alignment=TA_LEFT, spaceAfter=0)
    return Paragraph(text, style)

dec_wrapped = [dec[0]]
for row in dec[1:]:
    dec_wrapped.append([row[0]] + [wrap_cell(c) for c in row[1:]])

story.append(styled_table(dec_wrapped,
    col_widths=[0.9*cm, 4.0*cm, 6.4*cm, CONTENT_W - 11.3*cm], align='LEFT'))
story.append(Spacer(1, 0.1*cm))
story.append(Paragraph('Tabla 6. Registro de decisiones metodológicas del EDA.', st_caption))

story.append(PageBreak())

# ==================== 12. GO/NO-GO ====================
story.append(section_header('12', 'Veredicto Go/No-Go de Fase 1'))
story.append(Paragraph('Aplicamos los criterios definidos en la Fase 0 para decidir si se procede a M3:',
    st_body))

checklist = [
    ['#', 'Criterio', 'Resultado', 'Estado'],
    ['1', 'Todos los tickers con ≥ 10 años de historia común', '15.92 años', '✓'],
    ['2', 'Missing post-limpieza < 1% en todos los ETFs',     '0% tras alineamiento', '✓'],
    ['3', 'Volatilidades coherentes con el perfil',            '9 de 9 ETFs encajan', '✓'],
    ['4', 'Ningún par con ρ > 0.95',                           'Máximo: 0.91 (IEAG/EUNH)', '✓'],
    ['5', 'Σ_LW definida positiva',                            'Verificado por Cholesky', '✓'],
    ['6', 'MDD por perfil dentro de tolerancias',              'Documentado y aceptado', '✓'],
    ['7', 'Outputs persistidos y reproducibles',               '4 ficheros generados', '✓'],
]
story.append(styled_table(checklist,
    col_widths=[0.9*cm, 6.5*cm, 5.5*cm, CONTENT_W - 12.9*cm], align='LEFT'))

story.append(Spacer(1, 0.3*cm))
story.append(callout(
    'Veredicto · GO',
    'Se cumplen los <b>siete criterios</b> de la Fase 1. Los inputs estadísticos quedan validados y '
    'persistidos; el siguiente módulo (M3 — Optimización de carteras) puede consumirlos sin reproceso.',
    color=ORANGE))

# ==================== 13. OUTPUTS ====================
story.append(section_header('13', 'Outputs y trazabilidad para M3'))
story.append(Paragraph(
    'El notebook deja en disco cuatro artefactos, todos en el mismo directorio que el propio '
    'notebook, listos para ser cargados desde el módulo de optimización:', st_body))

outputs = [
    ['Fichero', 'Contenido', 'Uso en M3'],
    ['prices.parquet',        'Precios ajustados diarios (raw, sin recortar)', 'Auditoría / re-cálculo'],
    ['returns.parquet',       'Retornos diarios alineados, post-limpieza',     'Backtest, HRP'],
    ['mu.pkl',                'Vector retornos esperados anualizados (9 × 1)', 'Markowitz (objetivo)'],
    ['cov_ledoit_wolf.pkl',   'Matriz de covarianza Ledoit-Wolf (9 × 9)',      'Markowitz (riesgo)'],
]
story.append(styled_table(outputs,
    col_widths=[4.5*cm, 6.5*cm, CONTENT_W - 11.0*cm], align='LEFT'))
story.append(Spacer(1, 0.15*cm))

story.append(Paragraph('Reproducibilidad', st_h3))
story.append(Paragraph(
    'El proceso completo es reproducible ejecutando el notebook end-to-end. Las dependencias son: '
    '<font face="Courier">yfinance, pandas, numpy, scikit-learn, seaborn, matplotlib</font>. '
    'El único elemento no determinista son los precios devueltos por yfinance, que pueden variar '
    'marginalmente si Yahoo Finance corrige datos históricos retroactivamente. La estructura del '
    'pipeline y todas las decisiones documentadas en esta memoria permanecen invariantes.', st_body))

story.append(Spacer(1, 0.4*cm))
end_block = Table([[
    Paragraph('<b>Fin de la memoria</b>',
              ParagraphStyle('end', parent=st_body, textColor=WHITE,
                             alignment=TA_CENTER, fontSize=11)),
]], colWidths=[CONTENT_W])
end_block.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,-1), DEEPBLUE),
    ('TOPPADDING', (0,0), (-1,-1), 10),
    ('BOTTOMPADDING', (0,0), (-1,-1), 10),
]))
story.append(end_block)

doc.build(story)
print(f'OK -> {OUTPUT}')
