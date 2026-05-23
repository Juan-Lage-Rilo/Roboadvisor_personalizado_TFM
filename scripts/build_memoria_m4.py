"""Generate memoria_m4.pdf with the visual identity of the M2/M3 memorias."""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_CENTER
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    NextPageTemplate,
)

# ====== Palette (same as M2/M3) ======
BG = HexColor("#FAFAF7")
TEXT = HexColor("#2E2E2E")
BLUE = HexColor("#A8C8E8")
DEEPBLUE = HexColor("#7AA8D0")
BRONZE = HexColor("#C9A96E")
YELLOW = HexColor("#F9E4A0")
ORANGE = HexColor("#F4C18F")
WHITE = HexColor("#FFFFFF")
SOFTGREY = HexColor("#E8E6E0")
MUTED = HexColor("#6B6B6B")
GREEN = HexColor("#9CC39C")
RED = HexColor("#E0A0A0")

PAGE_W, PAGE_H = A4

BODY_LEFT = 2.2 * cm
BODY_RIGHT = 2.2 * cm
BODY_TOP = 2.4 * cm
BODY_BOTTOM = 2.2 * cm

HEADER_Y = PAGE_H - 1.4 * cm
HEADER_LINE = PAGE_H - 1.7 * cm
FOOTER_LINE = 1.6 * cm
FOOTER_Y = 1.05 * cm

COVER_BAND_H = 4.0 * cm
COVER_FRAME_TOP = PAGE_H - COVER_BAND_H - 0.8 * cm
COVER_FRAME_BOTTOM = 5.0 * cm
COVER_FOOTER_LINE = 2.0 * cm
COVER_FOOTER_Y = 1.45 * cm

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
OUTPUT = str(PROJECT_ROOT / "docs" / "memorias" / "memoria_m4.pdf")

styles = getSampleStyleSheet()
st_title = ParagraphStyle(
    "Title",
    parent=styles["Title"],
    fontName="Helvetica-Bold",
    fontSize=24,
    leading=30,
    textColor=DEEPBLUE,
    alignment=TA_LEFT,
    spaceAfter=4,
)
st_subtitle = ParagraphStyle(
    "Subtitle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=12.5,
    leading=17,
    textColor=BRONZE,
    alignment=TA_LEFT,
    spaceAfter=14,
)
st_h1 = ParagraphStyle(
    "H1",
    parent=styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=16,
    leading=20,
    textColor=DEEPBLUE,
    spaceBefore=10,
    spaceAfter=8,
)
st_h3 = ParagraphStyle(
    "H3",
    parent=styles["Heading3"],
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=14,
    textColor=BRONZE,
    spaceBefore=10,
    spaceAfter=4,
)
st_body = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9.8,
    leading=14,
    textColor=TEXT,
    alignment=TA_JUSTIFY,
    spaceAfter=5,
)
st_bullet = ParagraphStyle(
    "Bullet", parent=st_body, leftIndent=14, bulletIndent=2, spaceAfter=3
)
st_caption = ParagraphStyle(
    "Caption",
    parent=styles["Normal"],
    fontName="Helvetica-Oblique",
    fontSize=8.5,
    leading=11,
    textColor=MUTED,
    spaceAfter=10,
)
st_callout_body = ParagraphStyle(
    "CalloutBody",
    parent=st_body,
    fontSize=9.5,
    leading=13.5,
    leftIndent=4,
    rightIndent=4,
    spaceBefore=2,
    spaceAfter=2,
)
st_toc = ParagraphStyle(
    "Toc",
    parent=st_body,
    fontSize=10.5,
    leading=16,
    textColor=TEXT,
    spaceAfter=2,
    leftIndent=4,
)
st_code = ParagraphStyle(
    "Code",
    parent=styles["Code"],
    fontName="Courier",
    fontSize=8.5,
    leading=11,
    textColor=TEXT,
    backColor=HexColor("#F3F0EA"),
    leftIndent=8,
    rightIndent=8,
    spaceBefore=4,
    spaceAfter=8,
)


def draw_cover(canv, doc):
    canv.saveState()
    canv.setFillColor(BG)
    canv.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canv.setFillColor(BLUE)
    canv.rect(0, PAGE_H - COVER_BAND_H, PAGE_W, COVER_BAND_H, fill=1, stroke=0)
    canv.setFillColor(DEEPBLUE)
    canv.rect(0, PAGE_H - COVER_BAND_H - 0.18 * cm, PAGE_W, 0.18 * cm, fill=1, stroke=0)
    by = 3.4 * cm
    canv.setFillColor(YELLOW)
    canv.rect(BODY_LEFT, by, 1.2 * cm, 1.2 * cm, fill=1, stroke=0)
    canv.setFillColor(ORANGE)
    canv.rect(BODY_LEFT + 1.4 * cm, by, 1.2 * cm, 1.2 * cm, fill=1, stroke=0)
    canv.setFillColor(BRONZE)
    canv.rect(BODY_LEFT + 2.8 * cm, by, 1.2 * cm, 1.2 * cm, fill=1, stroke=0)
    canv.setStrokeColor(BRONZE)
    canv.setLineWidth(0.6)
    canv.line(BODY_LEFT, COVER_FOOTER_LINE, PAGE_W - BODY_RIGHT, COVER_FOOTER_LINE)
    canv.setFont("Helvetica", 9)
    canv.setFillColor(TEXT)
    canv.drawString(BODY_LEFT, COVER_FOOTER_Y, "TFM — Fase 1 (M4): Backtesting y Validación")
    canv.drawRightString(PAGE_W - BODY_RIGHT, COVER_FOOTER_Y, "Roboadvisor personalizado")
    canv.restoreState()


def draw_body(canv, doc):
    canv.saveState()
    canv.setFillColor(BG)
    canv.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canv.setFillColor(DEEPBLUE)
    canv.setFont("Helvetica-Bold", 9)
    canv.drawString(BODY_LEFT, HEADER_Y, "MEMORIA M4 — BACKTESTING Y VALIDACIÓN")
    canv.setFillColor(BRONZE)
    canv.drawRightString(PAGE_W - BODY_RIGHT, HEADER_Y, "TFM · Fase 1 · M4")
    canv.setStrokeColor(BLUE)
    canv.setLineWidth(0.5)
    canv.line(BODY_LEFT, HEADER_LINE, PAGE_W - BODY_RIGHT, HEADER_LINE)
    canv.setStrokeColor(BRONZE)
    canv.setLineWidth(0.4)
    canv.line(BODY_LEFT, FOOTER_LINE, PAGE_W - BODY_RIGHT, FOOTER_LINE)
    canv.setFont("Helvetica", 8.5)
    canv.setFillColor(MUTED)
    canv.drawString(BODY_LEFT, FOOTER_Y, "Juan Rilo · 2026")
    canv.drawRightString(PAGE_W - BODY_RIGHT, FOOTER_Y, f"Página {doc.page - 1}")
    canv.restoreState()


CONTENT_W = PAGE_W - BODY_LEFT - BODY_RIGHT


def callout(title, body_html, color=YELLOW):
    inner = [
        Paragraph(
            f"<b>{title}</b>",
            ParagraphStyle(
                "coT",
                parent=st_h3,
                textColor=DEEPBLUE,
                spaceBefore=0,
                spaceAfter=2,
                fontSize=10.5,
            ),
        ),
        Paragraph(body_html, st_callout_body),
    ]
    t = Table([[inner]], colWidths=[CONTENT_W])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), WHITE),
                ("LINEBEFORE", (0, 0), (0, -1), 3, color),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("BOX", (0, 0), (-1, -1), 0.3, SOFTGREY),
            ]
        )
    )
    return t


def styled_table(data, col_widths=None, header_bg=DEEPBLUE, header_fg=WHITE, zebra=True, align="LEFT"):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), header_fg),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.8),
        ("ALIGN", (0, 0), (-1, -1), align),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, BRONZE),
        ("TEXTCOLOR", (0, 1), (-1, -1), TEXT),
    ]
    if zebra:
        for i in range(1, len(data)):
            bg = HexColor("#F3F0EA") if i % 2 == 0 else WHITE
            style.append(("BACKGROUND", (0, i), (-1, i), bg))
    t.setStyle(TableStyle(style))
    return t


def section_header(num, title, anchor):
    block = Table(
        [
            [
                Paragraph(
                    f'<font color="#FFFFFF"><b>{num}</b></font>',
                    ParagraphStyle(
                        "n",
                        parent=st_h1,
                        textColor=WHITE,
                        alignment=TA_CENTER,
                        fontSize=18,
                        leading=20,
                    ),
                ),
                Paragraph(
                    f'<a name="{anchor}"/>{title}',
                    st_h1,
                ),
            ]
        ],
        colWidths=[1.05 * cm, CONTENT_W - 1.05 * cm],
    )
    block.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), DEEPBLUE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), 0),
                ("LEFTPADDING", (1, 0), (1, 0), 10),
                ("TOPPADDING", (0, 0), (0, 0), 4),
                ("BOTTOMPADDING", (0, 0), (0, 0), 4),
                ("TOPPADDING", (1, 0), (1, 0), 0),
                ("BOTTOMPADDING", (1, 0), (1, 0), 0),
            ]
        )
    )
    return block


doc = BaseDocTemplate(
    OUTPUT,
    pagesize=A4,
    leftMargin=BODY_LEFT,
    rightMargin=BODY_RIGHT,
    topMargin=BODY_TOP,
    bottomMargin=BODY_BOTTOM,
    title="Memoria M4 — Backtesting y Validación",
    author="Juan Rilo",
)

frame_cover = Frame(
    BODY_LEFT,
    COVER_FRAME_BOTTOM,
    CONTENT_W,
    COVER_FRAME_TOP - COVER_FRAME_BOTTOM,
    id="cover",
    leftPadding=0,
    rightPadding=0,
    topPadding=0,
    bottomPadding=0,
)
frame_body = Frame(
    BODY_LEFT,
    BODY_BOTTOM,
    CONTENT_W,
    PAGE_H - BODY_TOP - BODY_BOTTOM,
    id="body",
    leftPadding=0,
    rightPadding=0,
    topPadding=0,
    bottomPadding=0,
)
doc.addPageTemplates([
    PageTemplate(id="cover", frames=[frame_cover], onPage=draw_cover),
    PageTemplate(id="body", frames=[frame_body], onPage=draw_body),
])


# ===== Content =====
story = []

# --- Cover ---
story.append(Spacer(1, 0.4 * cm))
story.append(Paragraph("Memoria M4", st_title))
story.append(Paragraph("Backtesting y validación walk-forward · Roboadvisor TFM", st_subtitle))
story.append(Spacer(1, 0.3 * cm))
story.append(
    Paragraph(
        "Validación out-of-sample (OOS) de las tres carteras óptimas del M3 sobre el "
        "periodo <b>2020-01-02 → 2026-04-30</b>, con rebalanceo trimestral y comparación "
        "contra dos benchmarks (S&amp;P 500 y cartera 60/40 sintética). Los pesos se "
        "regeneran <b>OOS-clean</b> — con μ y Σ estimados únicamente hasta 2019-12-31 — "
        "para eliminar el <i>look-ahead bias</i> en la fase de estimación de parámetros.",
        st_body,
    )
)
story.append(Spacer(1, 0.4 * cm))
story.append(
    callout(
        "Resultado",
        "Backtest end-to-end con motor propio (rebalanceo + métricas sin QuantStats). "
        "Sharpe OOS: <b>−0.55</b> (conservador), <b>0.26</b> (moderado), <b>0.80</b> "
        "(agresivo). Ordenación de rentabilidad por perfil <b>PASS</b>; volatilidad "
        "realizada dentro del cap en los tres perfiles <b>PASS</b>. Go/No-Go "
        "(<i>Sharpe moderado ≥ Sharpe 60/40</i>): <b>FAIL</b> (0.26 &lt; 0.58) — "
        "resultado documentado, no defecto. Suite de <b>40 tests</b> en verde.",
        BRONZE,
    )
)
story.append(NextPageTemplate("body"))
story.append(PageBreak())

# --- TOC ---
story.append(Paragraph("Índice", st_h1))
toc_items = [
    ("1", "Contexto y objetivo", "s1"),
    ("2", "El problema del look-ahead bias y la solución OOS-clean", "s2"),
    ("3", "Arquitectura del módulo m4_backtesting", "s3"),
    ("4", "Generación de pesos OOS-clean", "s4"),
    ("5", "Motor de backtesting: drift y rebalanceo", "s5"),
    ("6", "Benchmarks: SPY y 60/40 sintético", "s6"),
    ("7", "Métricas: implementación propia", "s7"),
    ("8", "Configuración del backtest", "s8"),
    ("9", "Resultados OOS por perfil y benchmarks", "s9"),
    ("10", "Comparativa de pesos: full-history vs OOS-clean", "s10"),
    ("11", "Veredicto Go/No-Go y lectura crítica", "s11"),
    ("12", "Tests automatizados", "s12"),
    ("13", "Outputs y handover a M5", "s13"),
    ("14", "Notas metodológicas y limitaciones", "s14"),
    ("A", "Apéndice — Inventario de ficheros", "sA"),
]
for num, title, anchor in toc_items:
    story.append(
        Paragraph(
            f'<a href="#{anchor}" color="#7AA8D0">'
            f'<b>{num}.</b>&nbsp;&nbsp;{title}</a>',
            st_toc,
        )
    )
story.append(PageBreak())


# --- §1 ---
story.append(section_header("1", "Contexto y objetivo", "s1"))
story.append(
    Paragraph(
        "El <b>M4</b> es la fase de <b>validación</b> del roboadvisor. Toma las tres "
        "carteras construidas en M3 — una por perfil de riesgo (conservador, moderado, "
        "agresivo) — y responde la pregunta que M3 deliberadamente dejó abierta: "
        "<b>¿cómo se habrían comportado fuera de muestra?</b> Las métricas ex-ante de "
        "M3 (μ y Σ in-sample) son cotas optimistas; M4 las contrasta con un experimento "
        "<i>walk-forward</i> honesto sobre datos no vistos por el optimizador.",
        st_body,
    )
)
story.append(
    Paragraph(
        "Al igual que M3, el módulo se diseña como <b>paquete Python instalable</b> "
        "(<code>m4_backtesting</code>), independiente del notebook que lo orquesta. Esto "
        "permite testarlo con <code>pytest</code>, reusar el motor para construir el "
        "benchmark 60/40 y mantener la separación de responsabilidades entre lógica de "
        "negocio y orquestación.",
        st_body,
    )
)
story.append(
    callout(
        "Criterio Go/No-Go",
        "El gate de aceptación del M4 es <b>Sharpe(moderado) ≥ Sharpe(60/40)</b>: la "
        "cartera del perfil central debe batir, en ratio rentabilidad-riesgo, a la "
        "asignación pasiva de referencia. Se acompaña de dos chequeos estructurales: "
        "ordenación de CAGR por perfil (agresivo &gt; moderado &gt; conservador) y "
        "volatilidad realizada dentro del cap de cada perfil.",
        YELLOW,
    )
)

# --- §2 ---
story.append(section_header("2", "El problema del look-ahead bias y la solución OOS-clean", "s2"))
story.append(
    Paragraph(
        "Los pesos persistidos por M3 en <code>outputs/m3/weights.parquet</code> se "
        "calcularon con μ y Σ estimados sobre <b>todo el histórico</b> (2010-09 → "
        "2026-05). Aplicarlos directamente sobre una ventana OOS 2020-2026 introduciría "
        "<b>look-ahead bias en la fase de estimación de parámetros</b>: el optimizador ya "
        "habría 'visto' el régimen que pretendemos validar, incumpliendo el requisito "
        "walk-forward declarado en la Fase 0 del TFM.",
        st_body,
    )
)
story.append(
    Paragraph(
        "La solución no es regenerar <code>weights.parquet</code> (eso destruiría la "
        "cartera de producción que el roboadvisor recomienda hoy), sino mantener "
        "<b>dos carteras con roles disjuntos</b>:",
        st_body,
    )
)
story.append(
    styled_table(
        [
            ["Artefacto", "μ y Σ", "Pregunta que responde"],
            [
                "Ex-ante (M3)\noutputs/m3/weights.parquet",
                "Histórico completo\n2010-09 → 2026-05",
                "¿Qué cartera recomienda el roboadvisor hoy?",
            ],
            [
                "OOS-clean (M4)\noutputs/m4/weights_oos_clean.parquet",
                "Sólo 2010-09 → 2019-12-31",
                "¿Qué se habría recomendado en 2019 y cómo se comportó después?",
            ],
        ],
        col_widths=[5.5 * cm, 4.3 * cm, 6.7 * cm],
    )
)
story.append(Spacer(1, 0.2 * cm))
story.append(
    callout(
        "Optimizador agnóstico al tiempo",
        "Los optimizadores de <code>m3_portfolio</code> no saben de fechas: sólo reciben "
        "matrices (μ, Σ). Quién decide la ventana temporal es el <b>orquestador</b>. Por "
        "eso M4 puede reusar literalmente <code>MinVarianceOptimizer</code>, "
        "<code>MaxSharpeOptimizer</code> y <code>HRPOptimizer</code> sobre returns "
        "truncados, sin riesgo de contaminación temporal y sin duplicar código.",
        DEEPBLUE,
    )
)

# --- §3 ---
story.append(section_header("3", "Arquitectura del módulo m4_backtesting", "s3"))
story.append(
    Paragraph(
        "El paquete separa las cuatro responsabilidades del backtesting en módulos "
        "independientes, todos sin estado compartido:",
        st_body,
    )
)
story.append(
    Paragraph(
        "• <b>weights_generator</b> — regenera los pesos OOS-clean truncando returns y "
        "reinvocando los optimizadores de M3 (la pieza anti-leakage).",
        st_bullet,
    )
)
story.append(
    Paragraph(
        "• <b>engine</b> — simula la cartera día a día: deja driftar los pesos entre "
        "rebalanceos y los resetea al objetivo en cada fecha de rebalanceo.",
        st_bullet,
    )
)
story.append(
    Paragraph(
        "• <b>rebalancer</b> — calcula las fechas de rebalanceo por calendar (M/Q/Y) y "
        "detecta drift por umbral absoluto opcional.",
        st_bullet,
    )
)
story.append(
    Paragraph(
        "• <b>benchmarks</b> — construye las equity curves de SPY y la cartera 60/40 "
        "sintética (esta última reusando el propio <code>BacktestEngine</code>).",
        st_bullet,
    )
)
story.append(
    Paragraph(
        "• <b>metrics</b> — CAGR, vol, Sharpe, Sortino, Max Drawdown y Calmar "
        "implementadas a mano (sin QuantStats), determinísticas y testables.",
        st_bullet,
    )
)
story.append(Spacer(1, 0.2 * cm))
story.append(Paragraph("Estructura de ficheros:", st_h3))
story.append(
    Paragraph(
        "src/m4_backtesting/<br/>"
        "├── __init__.py · API pública<br/>"
        "├── weights_generator.py · regenerate_oos_clean_weights()<br/>"
        "├── engine.py · BacktestEngine + BacktestResult<br/>"
        "├── rebalancer.py · compute_rebalance_dates() + detect_drift()<br/>"
        "├── benchmarks.py · build_spy_benchmark() + build_60_40_benchmark()<br/>"
        "└── metrics.py · cagr, annual_vol, sharpe, sortino, max_drawdown, calmar",
        st_code,
    )
)
story.append(
    callout(
        "Modelo de datos",
        "<code>BacktestResult</code> es un <code>@dataclass</code> que empaqueta: "
        "<code>equity_curve</code> (base 1.0), <code>returns</code> (diarios), "
        "<code>weights_history</code> (pesos efectivos pre-rebalanceo), "
        "<code>rebalance_dates</code> y un <code>config</code> snapshot para "
        "auditoría. Devolver toda la trazabilidad en un único objeto facilita la "
        "persistencia y el debugging.",
        DEEPBLUE,
    )
)

# --- §4 ---
story.append(section_header("4", "Generación de pesos OOS-clean", "s4"))
story.append(
    Paragraph(
        "<code>regenerate_oos_clean_weights()</code> ejecuta cuatro pasos: <b>(1)</b> "
        "trunca returns a <code>index ≤ 2019-12-31</code>; <b>(2)</b> recalcula μ "
        "(media × 252) y Σ (Ledoit-Wolf × 252), coherente con M2/M3; <b>(3)</b> genera "
        "tres candidatas por perfil (principal, alternativa, baseline) con la misma "
        "configuración de M3; <b>(4)</b> aplica la regla de selección de M3: "
        "<i>argmax(Sharpe) sujeto a σ ≤ cap × 1.01</i>.",
        st_body,
    )
)
story.append(Spacer(1, 0.2 * cm))
story.append(Paragraph("Carteras OOS-clean seleccionadas (μ/Σ ≤ 2019-12-31):", st_h3))
story.append(
    styled_table(
        [
            ["Perfil", "Optimizador", "Pesos (ticker: w)", "Ret*", "Vol*", "Sharpe*"],
            [
                "Conservador",
                "max_sharpe",
                "EUNH.DE 0.89 · IEAG.AS 0.11",
                "3.12%",
                "4.03%",
                "0.278",
            ],
            [
                "Moderado",
                "max_sharpe",
                "IHYG.L 0.56 · INFR.AS 0.38 · EXSA.DE 0.07",
                "5.58%",
                "7.05%",
                "0.508",
            ],
            [
                "Agresivo",
                "max_sharpe",
                "CSPX.L 0.65 · EQQQ.DE 0.35",
                "16.01%",
                "14.18%",
                "0.988",
            ],
        ],
        col_widths=[2.6 * cm, 2.4 * cm, 6.5 * cm, 1.5 * cm, 1.5 * cm, 1.6 * cm],
    )
)
story.append(
    Paragraph(
        "<i>* Métricas ex-ante calculadas sobre la ventana de entrenamiento "
        "(≤ 2019-12-31), no sobre el periodo OOS.</i>",
        st_caption,
    )
)
story.append(
    Paragraph(
        "El resultado se persiste en <code>weights_oos_clean.parquet</code> (multi-índice "
        "perfil × ticker) y <code>portfolios_summary_oos_clean.json</code>. Nótese que "
        "los tres perfiles eligen <code>max_sharpe</code> en la ventana de entrenamiento, "
        "una selección distinta a la de la cartera full-history (§10).",
        st_body,
    )
)

# --- §5 ---
story.append(section_header("5", "Motor de backtesting: drift y rebalanceo", "s5"))
story.append(
    Paragraph(
        "El <code>BacktestEngine</code> recorre los retornos diarios OOS aplicando los "
        "pesos objetivo. Entre rebalanceos, los pesos <b>driftan</b> de forma "
        "multiplicativa según el rendimiento de cada activo:",
        st_body,
    )
)
story.append(
    Paragraph(
        "r_p,t = Σ w_i,t · r_i,t<br/>"
        "equity_t = equity_(t−1) · (1 + r_p,t)<br/>"
        "w_i,(t+1) = w_i,t · (1 + r_i,t) / (1 + r_p,t)",
        st_code,
    )
)
story.append(
    Paragraph(
        "En cada fecha de rebalanceo (o si se supera el <code>drift_threshold</code>, "
        "desactivado por defecto), los pesos se resetean al objetivo. Las fechas de "
        "rebalanceo se calculan como el <b>último día hábil de cada periodo</b> presente "
        "en el índice, excluyendo t=0. Con frecuencia trimestral sobre 2020-2026 → "
        "<b>26 rebalanceos por perfil</b>.",
        st_body,
    )
)
story.append(
    callout(
        "Cash sintético",
        "Si los pesos objetivo incluyen la clave <code>CASH</code> (vol=0), el motor lo "
        "remunera diariamente al <code>rf_annual</code> compuesto: "
        "<code>(1+rf)^(1/252) − 1</code>. Para las carteras OOS-clean actuales el cash "
        "no es vinculante (las tres respetan su cap sin blending), pero el mecanismo "
        "queda implementado y testado por coherencia con M3.",
        ORANGE,
    )
)

# --- §6 ---
story.append(section_header("6", "Benchmarks: SPY y 60/40 sintético", "s6"))
story.append(
    Paragraph(
        "Dos referencias para contextualizar los resultados:",
        st_body,
    )
)
story.append(
    Paragraph(
        "• <b>SPY</b> — retornos diarios del S&amp;P 500 (USD) recortados al periodo OOS. "
        "Representa la renta variable pasiva pura.",
        st_bullet,
    )
)
story.append(
    Paragraph(
        "• <b>60/40 sintético</b> — <code>0.6·CSPX.L + 0.4·IEAG.AS</code> (renta "
        "variable + renta fija EUR) con rebalanceo trimestral. Es la asignación pasiva "
        "diversificada de libro de texto y constituye el listón del Go/No-Go.",
        st_bullet,
    )
)
story.append(
    Paragraph(
        "El 60/40 se construye <b>reutilizando el propio <code>BacktestEngine</code></b> "
        "(sin cash, rf=0), garantizando que cartera y benchmark se evalúan con "
        "exactamente la misma mecánica de drift y rebalanceo. Es una decisión de "
        "consistencia: cualquier diferencia de resultados es atribuible a los pesos, no a "
        "diferencias de implementación.",
        st_body,
    )
)

# --- §7 ---
story.append(section_header("7", "Métricas: implementación propia", "s7"))
story.append(
    Paragraph(
        "Las métricas canónicas se implementan a mano en <code>m4_backtesting.metrics</code>, "
        "sin depender de QuantStats. Esto las hace determinísticas, testables y robustas "
        "frente a cambios de versión de librerías externas. QuantStats se usa "
        "<i>únicamente</i> para los tearsheets HTML descriptivos (§13).",
        st_body,
    )
)
story.append(
    styled_table(
        [
            ["Métrica", "Definición", "Convención"],
            ["CAGR", "(equity_T/equity_0)^(252/n) − 1", "anualizada"],
            ["Vol", "std(r) · √252", "ddof=1 (muestral, como M3)"],
            ["Sharpe", "(mean(r)·252 − rf) / vol", "rf = 2%"],
            ["Sortino", "(ret_anual − rf) / downside_dev", "MAR diario = rf/252"],
            ["Max Drawdown", "min(equity/cummax − 1)", "negativo, con fechas peak/trough"],
            ["Calmar", "CAGR / |MDD|", "—"],
        ],
        col_widths=[3.0 * cm, 6.5 * cm, 6.6 * cm],
    )
)

# --- §8 ---
story.append(section_header("8", "Configuración del backtest", "s8"))
story.append(
    styled_table(
        [
            ["Parámetro", "Valor"],
            ["Periodo OOS", "2020-01-02 → 2026-04-30"],
            ["Ventana de entrenamiento (μ/Σ)", "2010-09 → 2019-12-31"],
            ["Frecuencia de rebalanceo", "Trimestral (Q) → 26 rebalanceos/perfil"],
            ["Drift threshold", "None (solo rebalanceo por calendar)"],
            ["Risk-free anual", "2% (coherente con M3)"],
            ["Trading days/año", "252"],
        ],
        col_widths=[7.0 * cm, 9.1 * cm],
    )
)
story.append(Spacer(1, 0.2 * cm))
story.append(
    Paragraph(
        "Se opta por rebalanceo puramente por calendar (sin drift threshold) para "
        "maximizar la reproducibilidad y la simplicidad interpretativa del experimento.",
        st_body,
    )
)

# --- §9 ---
story.append(section_header("9", "Resultados OOS por perfil y benchmarks", "s9"))
story.append(
    Paragraph(
        "Métricas <b>realizadas</b> sobre el periodo 2020-2026 (out-of-sample real). "
        "Estos son los números honestos del módulo.",
        st_body,
    )
)
story.append(
    styled_table(
        [
            ["Serie", "CAGR", "Vol", "Sharpe", "Sortino", "MDD", "Calmar"],
            ["Conservador", "−1.60%", "6.17%", "−0.554", "−0.549", "−22.20%", "−0.072"],
            ["Moderado", "4.18%", "10.06%", "0.259", "0.232", "−28.20%", "0.148"],
            ["Agresivo", "16.20%", "18.50%", "0.796", "0.731", "−31.78%", "0.510"],
            ["SPY", "15.05%", "20.46%", "0.690", "0.654", "−33.72%", "0.446"],
            ["60/40", "8.26%", "11.31%", "0.581", "0.547", "−22.26%", "0.371"],
        ],
        col_widths=[3.0 * cm, 2.3 * cm, 2.0 * cm, 2.2 * cm, 2.2 * cm, 2.4 * cm, 2.0 * cm],
        align="CENTER",
    )
)
story.append(Spacer(1, 0.2 * cm))
story.append(Paragraph("Lectura por perfil:", st_h3))
story.append(
    Paragraph(
        "• <b>Conservador.</b> CAGR y Sharpe negativos. La renta fija EUR sufre la "
        "subida de tipos de 2022-2023; con cap de vol al 8% y sin componente de renta "
        "variable, no hay motor de rentabilidad. La vol realizada (6.17%) queda por "
        "debajo del cap.",
        st_bullet,
    )
)
story.append(
    Paragraph(
        "• <b>Moderado.</b> CAGR 4.18%, Sharpe 0.259. Positivo pero por debajo del "
        "60/40 — el origen del FAIL del Go/No-Go (§11).",
        st_bullet,
    )
)
story.append(
    Paragraph(
        "• <b>Agresivo.</b> El mejor perfil: CAGR 16.20% y Sharpe 0.796, <b>batiendo a "
        "SPY</b> (0.690) con menos volatilidad (18.50% vs 20.46%) y menor drawdown. La "
        "combinación CSPX.L + EQQQ.DE capturó el rally tecnológico con mejor perfil "
        "rentabilidad-riesgo que el índice puro.",
        st_bullet,
    )
)

# --- §10 ---
story.append(section_header("10", "Comparativa de pesos: full-history vs OOS-clean", "s10"))
story.append(
    Paragraph(
        "Persistida en <code>weights_comparison.parquet</code>. Cuantifica cuánto cambia "
        "la recomendación al restringir la información a ≤ 2019:",
        st_body,
    )
)
story.append(
    styled_table(
        [
            ["Perfil", "Ticker", "w_full (M3)", "w_oos (M4)", "Δ"],
            ["Conservador", "EUNH.DE", "0.333", "0.890", "+0.557"],
            ["", "IEAG.AS", "0.333", "0.110", "−0.224"],
            ["", "IBCI.AS", "0.333", "0.000", "−0.333"],
            ["Moderado", "IHYG.L", "0.000", "0.557", "+0.557"],
            ["", "INFR.AS", "0.372", "0.376", "+0.004"],
            ["", "EXSA.DE", "0.628", "0.068", "−0.561"],
            ["Agresivo", "CSPX.L", "0.507", "0.647", "+0.140"],
            ["", "EQQQ.DE", "0.493", "0.353", "−0.140"],
        ],
        col_widths=[3.0 * cm, 3.0 * cm, 3.3 * cm, 3.3 * cm, 3.0 * cm],
        align="CENTER",
    )
)
story.append(Spacer(1, 0.2 * cm))
story.append(
    Paragraph(
        "• <b>Moderado</b> sufre la mayor reasignación: con datos sólo hasta 2019, el "
        "optimizador carga el <b>56% en IHYG.L</b> (high yield) frente al 0% de la "
        "cartera full-history. Ese activo fue precisamente el más penalizado por la "
        "subida de tipos posterior — la raíz cuantitativa del FAIL.",
        st_bullet,
    )
)
story.append(
    Paragraph(
        "• <b>Agresivo</b> es el más estable: la reasignación CSPX↔EQQQ es modesta "
        "(±0.14), lo que explica su buen comportamiento OOS — la decisión de 2019 ya "
        "era robusta.",
        st_bullet,
    )
)

# --- §11 ---
story.append(section_header("11", "Veredicto Go/No-Go y lectura crítica", "s11"))
story.append(
    styled_table(
        [
            ["Chequeo", "Condición", "Resultado"],
            ["Go/No-Go", "Sharpe(moderado) ≥ Sharpe(60/40)", "FAIL  (0.259 < 0.581)"],
            ["Ordenación CAGR", "agresivo > moderado > conservador", "PASS  (16.20 > 4.18 > −1.60)"],
            ["Vol cap conservador", "vol realizada ≤ 8%", "PASS  (6.17%)"],
            ["Vol cap moderado", "vol realizada ≤ 15%", "PASS  (10.06%)"],
            ["Vol cap agresivo", "vol realizada ≤ 25%", "PASS  (18.50%)"],
        ],
        col_widths=[3.8 * cm, 6.8 * cm, 5.5 * cm],
    )
)
story.append(Spacer(1, 0.2 * cm))
story.append(
    callout(
        "El FAIL es un hallazgo, no un bug",
        "El gate del perfil moderado falla, y el módulo lo reporta con honestidad en "
        "lugar de ocultarlo. El experimento OOS-clean es metodológicamente correcto: "
        "precisamente por eso descubre una limitación real de la cartera moderada.",
        RED,
    )
)
story.append(Spacer(1, 0.2 * cm))
story.append(Paragraph("Diagnóstico del FAIL:", st_h3))
story.append(
    Paragraph(
        "El universo del perfil moderado (<code>INFR.AS, IHYG.L, EXSA.DE</code>) no "
        "contiene exposición directa al S&amp;P 500, mientras que el 60/40 sí "
        "(<code>CSPX.L</code>). Cuando los parámetros se estiman sólo con datos ≤ 2019, "
        "el max-Sharpe se concentra en <b>IHYG.L</b> (high yield), el activo que peor se "
        "comportó en el shock de tipos 2022-2023. La cartera moderada queda así "
        "estructuralmente penalizada frente a un benchmark que combina equity de calidad "
        "y duración corta.",
        st_body,
    )
)
story.append(
    Paragraph(
        "Líneas de mejora para discusión en la memoria: (1) incluir un ETF de equity "
        "global en el universo moderado; (2) revisar el cap de vol (15% puede ser "
        "demasiado bajo para exigirle batir al 60/40 en Sharpe); (3) explorar rebalanceo "
        "por drift en lugar de calendar. Ninguna requiere cambios en el motor — sólo en "
        "la configuración del universo, decisión que pertenece a M2/M3.",
        st_body,
    )
)

# --- §12 ---
story.append(section_header("12", "Tests automatizados", "s12"))
story.append(
    Paragraph(
        "Suite con <b>40 tests</b> en <code>tests/m4_backtesting/</code>, todos en verde.",
        st_body,
    )
)
story.append(
    styled_table(
        [
            ["Fichero", "N tests", "Cubre"],
            ["test_metrics.py", "13", "CAGR, vol, Sharpe, Sortino, MDD, Calmar + edge cases"],
            ["test_weights_generator.py", "10", "Truncado, estimación μ/Σ, regla de selección"],
            ["test_engine.py", "9", "Drift, rebalanceo, cash, validación de inputs"],
            ["test_rebalancer.py", "8", "Fechas por calendar (M/Q/Y) + detección de drift"],
        ],
        col_widths=[5.0 * cm, 2.0 * cm, 9.1 * cm],
    )
)
story.append(Spacer(1, 0.2 * cm))
story.append(
    Paragraph(
        "<code>conftest.py</code> define fixtures sintéticas (returns de prueba, pesos "
        "objetivo, mocks de <code>Portfolio</code>) que permiten testar la lógica sin "
        "depender de los artefactos reales de M2/M3.",
        st_body,
    )
)
story.append(Paragraph("Comando:", st_h3))
story.append(Paragraph("python -m pytest tests/m4_backtesting/ -v", st_code))

# --- §13 ---
story.append(section_header("13", "Outputs y handover a M5", "s13"))
story.append(
    Paragraph(
        "El M4 produce <b>diez artefactos</b> en <code>outputs/m4/</code>, consumibles "
        "por la capa de aplicación M5:",
        st_body,
    )
)
story.append(
    styled_table(
        [
            ["Artefacto", "Contenido"],
            ["weights_oos_clean.parquet", "Pesos OOS-clean (perfil × ticker)"],
            ["portfolios_summary_oos_clean.json", "Resumen por perfil (optimizador, pesos, métricas ex-ante)"],
            ["equity_curves.parquet", "Equity curves: 3 perfiles + SPY + 60/40"],
            ["drawdown_series.parquet", "Series de drawdown por perfil y benchmarks"],
            ["metrics_by_profile.json", "Métricas OOS realizadas (tabla §9)"],
            ["rebalance_log.parquet", "Fechas de rebalanceo (26/perfil)"],
            ["weights_comparison.parquet", "Comparativa full-history vs OOS-clean (§10)"],
            ["report_{conservador,moderado,agresivo}.html", "Tearsheets QuantStats (3)"],
        ],
        col_widths=[6.5 * cm, 9.6 * cm],
    )
)
story.append(Spacer(1, 0.2 * cm))
story.append(
    Paragraph(
        "Las métricas canónicas para M5 son las de <code>metrics_by_profile.json</code> "
        "(implementación propia). Los HTML de QuantStats son material descriptivo de "
        "apoyo, no fuente de verdad.",
        st_body,
    )
)

# --- §14 ---
story.append(section_header("14", "Notas metodológicas y limitaciones", "s14"))
story.append(
    Paragraph(
        "<b>1. OOS-clean parcial.</b> El experimento elimina el look-ahead bias en la "
        "<i>estimación de parámetros</i> (μ/Σ ≤ 2019), pero los pesos se mantienen fijos "
        "durante todo el OOS — no es un walk-forward con re-optimización rodante. Es una "
        "validación honesta de la decisión de 2019, no de un sistema adaptativo.",
        st_body,
    )
)
story.append(
    Paragraph(
        "<b>2. Universo congelado.</b> El conjunto de ETFs por perfil se fija en M2 con "
        "criterio de disponibilidad a 2026. Un ETF lanzado en 2015 no habría estado "
        "disponible para un inversor en 2010, sesgo de supervivencia residual asumido y "
        "documentado.",
        st_body,
    )
)
story.append(
    Paragraph(
        "<b>3. Sin costes de transacción.</b> El backtest no modela comisiones ni "
        "slippage. Con rebalanceo trimestral el impacto es bajo, pero las métricas son "
        "cotas superiores frente a la ejecución real.",
        st_body,
    )
)
story.append(
    Paragraph(
        "<b>4. Divisa.</b> SPY se compara en USD frente a carteras EUR; el 60/40 (en EUR) "
        "es el benchmark primario y justo para el Go/No-Go. SPY es contexto, no listón.",
        st_body,
    )
)
story.append(
    Paragraph(
        "<b>5. Reproducibilidad.</b> El notebook se regenera desde código vía "
        "<code>scripts/build_notebook_m4.py</code>, y esta memoria desde "
        "<code>scripts/build_memoria_m4.py</code>, evitando conflictos de merge en JSON.",
        st_body,
    )
)

# --- Apéndice ---
story.append(section_header("A", "Apéndice — Inventario de ficheros", "sA"))
story.append(Paragraph("Paquete (src/m4_backtesting):", st_h3))
for f, desc in [
    ("__init__.py", "API pública"),
    ("weights_generator.py", "regenerate_oos_clean_weights()"),
    ("engine.py", "BacktestEngine + BacktestResult"),
    ("rebalancer.py", "compute_rebalance_dates() + detect_drift()"),
    ("benchmarks.py", "build_spy_benchmark() + build_60_40_benchmark()"),
    ("metrics.py", "métricas financieras puras (sin QuantStats)"),
]:
    story.append(Paragraph(f"• <code>{f}</code> — {desc}", st_bullet))
story.append(Paragraph("Tests (tests/m4_backtesting):", st_h3))
for f in ["conftest.py", "test_metrics.py", "test_weights_generator.py", "test_engine.py", "test_rebalancer.py"]:
    story.append(Paragraph(f"• <code>{f}</code>", st_bullet))
story.append(Paragraph("Notebook (notebooks/):", st_h3))
story.append(Paragraph("• <code>m4_backtesting.ipynb</code> — orquestador (bloques 0-10)", st_bullet))
story.append(Paragraph("• <code>scripts/build_notebook_m4.py</code> — regenerador", st_bullet))
story.append(Paragraph("Outputs (outputs/m4/):", st_h3))
for f in [
    "weights_oos_clean.parquet", "portfolios_summary_oos_clean.json",
    "equity_curves.parquet", "drawdown_series.parquet", "metrics_by_profile.json",
    "rebalance_log.parquet", "weights_comparison.parquet",
    "report_{conservador,moderado,agresivo}.html",
]:
    story.append(Paragraph(f"• <code>{f}</code>", st_bullet))


# Build
doc.build(story)
print(f"Wrote {OUTPUT}")
