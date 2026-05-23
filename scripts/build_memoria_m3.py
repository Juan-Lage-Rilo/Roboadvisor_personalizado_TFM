"""Generate Memoria_M3.pdf with the visual identity of the M2 memoria."""
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

# ====== Palette (same as M2) ======
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
OUTPUT = str(PROJECT_ROOT / "docs" / "memorias" / "memoria_m3.pdf")

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
    canv.drawString(BODY_LEFT, COVER_FOOTER_Y, "TFM — Fase 1 (M3): Optimización de Carteras")
    canv.drawRightString(PAGE_W - BODY_RIGHT, COVER_FOOTER_Y, "Roboadvisor personalizado")
    canv.restoreState()


def draw_body(canv, doc):
    canv.saveState()
    canv.setFillColor(BG)
    canv.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canv.setFillColor(DEEPBLUE)
    canv.setFont("Helvetica-Bold", 9)
    canv.drawString(BODY_LEFT, HEADER_Y, "MEMORIA M3 — OPTIMIZACIÓN DE CARTERAS")
    canv.setFillColor(BRONZE)
    canv.drawRightString(PAGE_W - BODY_RIGHT, HEADER_Y, "TFM · Fase 1 · M3")
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
    title="Memoria M3 — Optimización de Carteras",
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
story.append(Paragraph("Memoria M3", st_title))
story.append(Paragraph("Optimización de carteras · Roboadvisor TFM", st_subtitle))
story.append(Spacer(1, 0.3 * cm))
story.append(
    Paragraph(
        "Construcción de tres carteras óptimas long-only UCITS — una por perfil de "
        "riesgo (<b>conservador</b>, <b>moderado</b>, <b>agresivo</b>) — combinando "
        "Mínima Varianza, Máximo Sharpe y Hierarchical Risk Parity, con caps de "
        "volatilidad gestionados mediante <i>cash blending</i>.",
        st_body,
    )
)
story.append(Spacer(1, 0.4 * cm))
story.append(
    callout(
        "Resultado",
        "Tres carteras seleccionadas — todas <b>PASS</b> en validación UCITS y vol "
        "cap. Sharpe ex-ante: <b>−0.127</b> (conservador, equal-weight), "
        "<b>0.449</b> (moderado, max-sharpe), <b>0.899</b> (agresivo, max-sharpe). "
        "Suite de 16 tests automatizados. Outputs (<code>weights.parquet</code> + "
        "<code>portfolios_summary.json</code>) listos para M4.",
        BRONZE,
    )
)
story.append(NextPageTemplate("body"))
story.append(PageBreak())

# --- TOC ---
story.append(Paragraph("Índice", st_h1))
toc_items = [
    ("1", "Contexto y objetivo", "s1"),
    ("2", "Inputs heredados de M2", "s2"),
    ("3", "Arquitectura del módulo m3_portfolio", "s3"),
    ("4", "Restricciones del problema", "s4"),
    ("5", "Estrategias de optimización por perfil", "s5"),
    ("6", "Manejo del vol cap: blending con cash", "s6"),
    ("7", "Resultados: 9 carteras candidatas", "s7"),
    ("8", "Selección final por perfil", "s8"),
    ("9", "Validación UCITS y de volatilidad", "s9"),
    ("10", "Tests automatizados", "s10"),
    ("11", "Outputs y handover a M4", "s11"),
    ("12", "Notas metodológicas y limitaciones", "s12"),
    ("13", "Nota metodológica: cartera ex-ante vs cartera OOS-clean", "s13"),
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
        "El <b>M3</b> es la fase de construcción de carteras óptimas del roboadvisor. "
        "Recibe del M2 un universo de 9 ETFs UCITS (3 por perfil) junto con sus "
        "retornos esperados y matriz de covarianza, y devuelve <b>tres carteras "
        "óptimas</b> — una por perfil — listas para evaluación en el M4 con "
        "backtesting walk-forward.",
        st_body,
    )
)
story.append(
    Paragraph(
        "El módulo se diseña como <b>paquete Python instalable</b> "
        "(<code>m3_portfolio</code>), independiente del notebook que lo orquesta. "
        "Esta separación permite reutilizarlo en M4 (rebalanceo periódico), testarlo "
        "con <code>pytest</code> y aplicar el principio de separación de "
        "responsabilidades.",
        st_body,
    )
)
story.append(
    callout(
        "Audiencia",
        "Tribunal de Data Science. La documentación se centra en arquitectura "
        "de software y resultados; los desarrollos matemáticos (frontera "
        "eficiente, clustering jerárquico) se referencian pero no se reproducen.",
        YELLOW,
    )
)

# --- §2 ---
story.append(section_header("2", "Inputs heredados de M2", "s2"))
story.append(
    Paragraph(
        "El M3 <b>no recalcula</b> ni μ ni Σ: confía en los artefactos del M2. "
        "Esto evita inconsistencias entre fases y respeta el principio de <i>single "
        "source of truth</i>.",
        st_body,
    )
)
story.append(Spacer(1, 0.2 * cm))
story.append(
    styled_table(
        [
            ["Fichero", "Forma", "Contenido"],
            ["ETFs/returns.parquet", "(3 941, 9)", "Retornos diarios 2010-09 → 2026-05"],
            ["ETFs/mu.pkl", "Series[9]", "μ anualizado (media × 252)"],
            ["ETFs/cov_ledoit_wolf.pkl", "DataFrame[9×9]", "Σ Ledoit-Wolf (α≈0.0073, PD)"],
        ],
        col_widths=[6.0 * cm, 3.0 * cm, 7.5 * cm],
    )
)
story.append(Spacer(1, 0.3 * cm))
story.append(Paragraph("Universo por perfil:", st_h3))
story.append(
    styled_table(
        [
            ["Perfil", "Tickers", "Descripción"],
            ["Conservador", "IEAG.AS · EUNH.DE · IBCI.AS", "Renta fija EUR"],
            ["Moderado", "INFR.AS · IHYG.L · EXSA.DE", "Mixto global"],
            ["Agresivo", "CSPX.L · EQQQ.DE · EXI2.DE", "Renta variable global"],
        ],
        col_widths=[3.0 * cm, 7.0 * cm, 6.5 * cm],
    )
)

# --- §3 ---
story.append(section_header("3", "Arquitectura del módulo m3_portfolio", "s3"))
story.append(
    Paragraph(
        "El paquete sigue un patrón <b>Strategy + Protocol estructural</b>:",
        st_body,
    )
)
story.append(
    Paragraph(
        "• <b>PortfolioOptimizer</b> (PEP 544 Protocol) define el contrato mínimo: "
        "<code>optimize(mu, cov, tickers, max_volatility, profile, risk_free_rate) "
        "→ Portfolio</code>.",
        st_bullet,
    )
)
story.append(
    Paragraph(
        "• Cada <b>optimizador concreto</b> (Min-Variance, Max-Sharpe, HRP, "
        "Equal-Weight) implementa el método. La matemática vive en "
        "<code>PyPortfolioOpt</code>; el paquete actúa como <b>adaptador</b>.",
        st_bullet,
    )
)
story.append(
    Paragraph(
        "• Todos delegan en <code>_build.build_portfolio()</code>, que proyecta al "
        "simplex UCITS, aplica el vol cap (cash) y calcula las métricas. Garantiza "
        "que <b>ningún Portfolio sale del módulo violando restricciones</b>.",
        st_bullet,
    )
)
story.append(Spacer(1, 0.2 * cm))
story.append(Paragraph("Estructura de ficheros:", st_h3))
story.append(
    Paragraph(
        "roboadvisor/m3_portfolio/<br/>"
        "├── __init__.py · API pública<br/>"
        "├── portfolio.py · @dataclass(frozen) Portfolio<br/>"
        "├── base.py · Protocol PortfolioOptimizer<br/>"
        "├── constraints.py · UCITS + vol cap + HHI<br/>"
        "├── validators.py · validación post-hoc<br/>"
        "├── _build.py · ensamblador compartido<br/>"
        "├── min_variance.py · MinVarianceOptimizer<br/>"
        "├── max_sharpe.py · MaxSharpeOptimizer (con fallback)<br/>"
        "├── hrp.py · HRPOptimizer<br/>"
        "└── equal_weight.py · EqualWeightOptimizer (baseline)",
        st_code,
    )
)
story.append(
    callout(
        "Modelo de datos",
        "<code>Portfolio</code> es <b>frozen</b> (inmutable). Contiene: "
        "<code>profile, optimizer_name, weights, cash_weight, expected_return, "
        "expected_volatility, expected_sharpe, herfindahl_index, "
        "n_effective_assets, constraints_satisfied, validation_report</code>. "
        "La inmutabilidad evita modificaciones accidentales y facilita el paso "
        "por valor a M4.",
        DEEPBLUE,
    )
)

# --- §4 ---
story.append(section_header("4", "Restricciones del problema", "s4"))
story.append(Paragraph("UCITS (estructurales):", st_h3))
story.append(Paragraph("• <b>Long-only</b>: w<sub>i</sub> ≥ 0.", st_bullet))
story.append(Paragraph("• <b>Sin apalancamiento</b>: Σ w<sub>i</sub> = 1.", st_bullet))
story.append(
    Paragraph(
        "Se aplican vía proyección al simplex en <code>apply_ucits_constraints()</code>: "
        "clip a 0 los pesos negativos y renormalización.",
        st_body,
    )
)
story.append(Spacer(1, 0.2 * cm))
story.append(Paragraph("Cap de volatilidad por perfil:", st_h3))
story.append(
    styled_table(
        [
            ["Perfil", "max_volatility"],
            ["Conservador", "8 %"],
            ["Moderado", "15 %"],
            ["Agresivo", "25 %"],
        ],
        col_widths=[4.0 * cm, 4.0 * cm],
        align="CENTER",
    )
)
story.append(Spacer(1, 0.2 * cm))
story.append(
    Paragraph(
        "Restricción a nivel de cartera (no por activo). Aplicada <i>ex post</i> "
        "mediante blending con cash (§6).",
        st_body,
    )
)

# --- §5 ---
story.append(section_header("5", "Estrategias de optimización por perfil", "s5"))
story.append(
    styled_table(
        [
            ["Perfil", "Principal", "Alternativa", "Baseline"],
            ["Conservador", "Mínima varianza", "Máximo Sharpe", "Equal-weight"],
            ["Moderado", "Máximo Sharpe", "HRP", "Equal-weight"],
            ["Agresivo", "HRP", "Máximo Sharpe", "Equal-weight"],
        ],
        col_widths=[3.5 * cm, 4.0 * cm, 4.5 * cm, 4.5 * cm],
    )
)
story.append(Spacer(1, 0.3 * cm))
story.append(Paragraph("Justificación:", st_h3))
story.append(
    Paragraph(
        "• <b>Conservador → Min-Variance.</b> Maximiza robustez sin usar μ (ruidoso "
        "en RF EUR).",
        st_bullet,
    )
)
story.append(
    Paragraph(
        "• <b>Moderado → Max-Sharpe.</b> Punto de tangencia clásico de Markowitz.",
        st_bullet,
    )
)
story.append(
    Paragraph(
        "• <b>Agresivo → HRP.</b> Kurtosis > 3 (EQQQ.DE 65.3, IHYG.L 56.5) y "
        "asimetría negativa en 8/9 ETFs invalidan la normalidad de Markowitz puro. "
        "HRP no requiere invertir Σ; agrupa activos por clustering jerárquico y "
        "reparte riesgo por bisección recursiva.",
        st_bullet,
    )
)
story.append(
    Paragraph(
        "Generamos tres candidatas por perfil (principal, alternativa, baseline) "
        "para comparar cuantitativamente en lugar de adoptar la principal por "
        "convención.",
        st_body,
    )
)

# --- §6 ---
story.append(section_header("6", "Manejo del vol cap: blending con cash", "s6"))
story.append(
    Paragraph(
        "Cuando la cartera optimizada w* tiene σ<sub>p</sub> &gt; max_vol, se "
        "<b>mezcla linealmente con cash</b> (sintético, vol=0, retorno=rf=2 %):",
        st_body,
    )
)
story.append(
    Paragraph(
        "w_final = α · w*<br/>"
        "cash_weight = 1 − α<br/>"
        "α = min(1, max_vol / σ<sub>p</sub>)<br/>"
        "σ_final = α · σ<sub>p</sub>   ≤ max_vol<br/>"
        "μ_final = α · μ<sub>p</sub> + (1 − α) · rf",
        st_code,
    )
)
story.append(
    callout(
        "Por qué cash y no reescalado puro",
        "Reescalar pesos por α &lt; 1 y <b>renormalizar</b> a suma 1 (<i>w / Σw</i>) "
        "<b>no cambia la volatilidad</b>: es el mismo punto del simplex. La única "
        "forma matemáticamente consistente de reducir la varianza manteniendo "
        "UCITS es <b>añadir un activo libre de riesgo</b>. En la práctica, esto se "
        "traduce en una columna <code>CASH</code> en weights.parquet cuando "
        "aplica. Para los inputs históricos de M2, esta restricción no ha sido "
        "vinculante.",
        ORANGE,
    )
)

# --- §7 ---
story.append(section_header("7", "Resultados: 9 carteras candidatas", "s7"))
story.append(
    Paragraph(
        "Métricas <b>ex-ante</b> calculadas con μ y Σ del M2 (in-sample). "
        "La validación out-of-sample se hará en M4.",
        st_body,
    )
)
story.append(Paragraph("Conservador (cap 8 %):", st_h3))
story.append(
    styled_table(
        [
            ["Candidata", "Optimizador", "Ret %", "Vol %", "Sharpe", "HHI", "Cash %"],
            ["Principal", "min_variance", "1.24", "4.35", "−0.176", "0.86", "0"],
            ["Alternativa", "max_sharpe ⚠", "1.24", "4.35", "−0.176", "0.86", "0"],
            ["Baseline", "equal_weight", "1.41", "4.68", "−0.127", "0.33", "0"],
        ],
        col_widths=[2.6 * cm, 3.4 * cm, 1.8 * cm, 1.8 * cm, 2.0 * cm, 1.6 * cm, 1.8 * cm],
        align="CENTER",
    )
)
story.append(
    Paragraph(
        "<i>⚠ max(μ) ≈ 1.72 % &lt; rf = 2 %; max_sharpe cae a min_volatility con "
        "warning (§12, nota 1).</i>",
        st_caption,
    )
)
story.append(Paragraph("Moderado (cap 15 %):", st_h3))
story.append(
    styled_table(
        [
            ["Candidata", "Optimizador", "Ret %", "Vol %", "Sharpe", "HHI", "Cash %"],
            ["Principal", "max_sharpe", "8.30", "14.03", "0.449", "0.52", "0"],
            ["Alternativa", "hrp", "4.30", "7.12", "0.324", "0.67", "0"],
            ["Baseline", "equal_weight", "6.55", "10.55", "0.432", "0.33", "0"],
        ],
        col_widths=[2.6 * cm, 3.4 * cm, 1.8 * cm, 1.8 * cm, 2.0 * cm, 1.6 * cm, 1.8 * cm],
        align="CENTER",
    )
)
story.append(Paragraph("Agresivo (cap 25 %):", st_h3))
story.append(
    styled_table(
        [
            ["Candidata", "Optimizador", "Ret %", "Vol %", "Sharpe", "HHI", "Cash %"],
            ["Principal", "hrp", "15.14", "15.22", "0.863", "0.41", "0"],
            ["Alternativa", "max_sharpe", "17.06", "16.74", "0.899", "0.50", "0"],
            ["Baseline", "equal_weight", "16.09", "16.12", "0.874", "0.33", "0"],
        ],
        col_widths=[2.6 * cm, 3.4 * cm, 1.8 * cm, 1.8 * cm, 2.0 * cm, 1.6 * cm, 1.8 * cm],
        align="CENTER",
    )
)

# --- §8 ---
story.append(section_header("8", "Selección final por perfil", "s8"))
story.append(
    Paragraph(
        "Criterio: <b>argmax(Sharpe) sujeto a σ ≤ max_vol × 1.01</b>.",
        st_body,
    )
)
story.append(
    styled_table(
        [
            ["Perfil", "Estrategia elegida", "Ret %", "Vol %", "Sharpe", "Cap"],
            ["Conservador", "equal_weight", "1.41", "4.68", "−0.127", "✓"],
            ["Moderado", "max_sharpe", "8.30", "14.03", "0.449", "✓"],
            ["Agresivo", "max_sharpe", "17.06", "16.74", "0.899", "✓"],
        ],
        col_widths=[3.0 * cm, 3.5 * cm, 2.0 * cm, 2.0 * cm, 2.5 * cm, 1.5 * cm],
        align="CENTER",
    )
)
story.append(Spacer(1, 0.3 * cm))
story.append(Paragraph("Lectura crítica:", st_h3))
story.append(
    Paragraph(
        "• <b>Conservador.</b> Sharpe negativo esperable y documentado: ETFs de RF "
        "EUR con CAGR &lt; rf=2 % (entorno ZIRP 2010-2021). El equal-weight gana "
        "porque la diversificación cruda baja el Sharpe menos que la concentración "
        "en min-variance. Con datos 2022+ (subida de tipos), la situación cambiará en M4.",
        st_bullet,
    )
)
story.append(
    Paragraph(
        "• <b>Agresivo.</b> Gana max_sharpe con Sharpe 0.899, <i>por encima del HRP "
        "designado como principal</i>. El criterio de selección es agnóstico al "
        "optimizador. La 'principal' es una <i>prior</i> metodológica, no un compromiso.",
        st_bullet,
    )
)
story.append(
    Paragraph(
        "• <b>Moderado.</b> Sharpe 0.449 &lt; 0.958 del benchmark 60/40 (M2). Esto "
        "es <b>ex-ante</b> con μ in-sample; el benchmark incluye toda la deriva "
        "alcista 2010-2026. Comparación justa en M4 walk-forward.",
        st_bullet,
    )
)

# --- §9 ---
story.append(section_header("9", "Validación UCITS y de volatilidad", "s9"))
story.append(
    Paragraph(
        "<code>validators.validate_portfolio()</code> ejecuta cuatro chequeos sobre "
        "las carteras seleccionadas:",
        st_body,
    )
)
story.append(
    styled_table(
        [
            ["Check", "Tolerancia", "Conservador", "Moderado", "Agresivo"],
            ["sum_to_one", "1e-6", "✓", "✓", "✓"],
            ["long_only", "-1e-6", "✓", "✓", "✓"],
            ["vol_within_cap", "× 1.01", "✓", "✓", "✓"],
            ["hhi_in_range", "[1/n, 1]", "✓", "✓", "✓"],
            ["STATUS", "", "PASS", "PASS", "PASS"],
        ],
        col_widths=[3.5 * cm, 2.5 * cm, 3.2 * cm, 3.2 * cm, 3.2 * cm],
        align="CENTER",
    )
)

# --- §10 ---
story.append(section_header("10", "Tests automatizados", "s10"))
story.append(
    Paragraph(
        "Suite con <b>16 tests</b> en <code>roboadvisor/tests/</code>, todos pasan "
        "en ~2 s.",
        st_body,
    )
)
story.append(
    styled_table(
        [
            ["Fichero", "N tests", "Cubre"],
            ["test_optimizers.py", "5", "Smoke tests × 4 optimizadores + 1/n"],
            ["test_constraints.py", "7", "UCITS, HHI, effective_assets, vol cap"],
            ["test_validators.py", "4", "Validación correcta + violaciones"],
        ],
        col_widths=[4.5 * cm, 2.2 * cm, 8.8 * cm],
    )
)
story.append(Spacer(1, 0.2 * cm))
story.append(
    Paragraph(
        "<code>conftest.py</code> define fixtures sintéticas (sample_cov 3×3 PD, "
        "sample_mu, sample_tickers, sample_max_volatility). Probar la lógica sin "
        "depender de los inputs reales.",
        st_body,
    )
)
story.append(Paragraph("Comando:", st_h3))
story.append(Paragraph("cd roboadvisor &amp;&amp; python -m pytest tests/ -v", st_code))

# --- §11 ---
story.append(section_header("11", "Outputs y handover a M4", "s11"))
story.append(Paragraph("Dos artefactos consumidos por el siguiente módulo:", st_body))
story.append(Paragraph("weights.parquet (multi-índice profile × ticker):", st_h3))
story.append(
    Paragraph(
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;weight<br/>"
        "profile&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ticker<br/>"
        "agresivo&nbsp;&nbsp;&nbsp;&nbsp;CSPX.L&nbsp;&nbsp;&nbsp;&nbsp;0.5234<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;EQQQ.DE&nbsp;&nbsp;0.4766<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;EXI2.DE&nbsp;&nbsp;0.0000<br/>"
        "conservador EUNH.DE&nbsp;&nbsp;0.3333<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;IBCI.AS&nbsp;&nbsp;0.3333<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;IEAG.AS&nbsp;&nbsp;0.3333<br/>"
        "moderado&nbsp;&nbsp;&nbsp;&nbsp;EXSA.DE&nbsp;&nbsp;0.6106<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;IHYG.L&nbsp;&nbsp;&nbsp;0.0000<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;INFR.AS&nbsp;&nbsp;0.3894",
        st_code,
    )
)
story.append(Paragraph("portfolios_summary.json:", st_h3))
story.append(
    Paragraph(
        "Diccionario <code>{profile: {optimizer, selection, weights, cash_weight, "
        "expected_*, herfindahl_index, n_effective_assets, max_volatility, "
        "validation}}</code>. Pensado para auditoría legible y trazabilidad de la "
        "decisión (qué algoritmo fue elegido y por qué).",
        st_body,
    )
)

# --- §12 ---
story.append(section_header("12", "Notas metodológicas y limitaciones", "s12"))
story.append(
    Paragraph(
        "<b>1. Max-Sharpe en conservador.</b> El algoritmo de Markowitz exige "
        "max(μ) &gt; rf. Si no se cumple (caso ZIRP), MaxSharpeOptimizer cae "
        "automáticamente a min_volatility y emite warning. Decisión conservadora "
        "y registrada.",
        st_body,
    )
)
story.append(
    Paragraph(
        "<b>2. In-sample bias.</b> Las métricas de §7 usan μ y Σ históricos sobre "
        "los <i>mismos datos</i> usados para optimizar. Son cotas optimistas. La "
        "validación honesta es M4 (walk-forward, out-of-sample).",
        st_body,
    )
)
story.append(
    Paragraph(
        "<b>3. HHI sólo sobre activos riesgo.</b> El índice excluye la columna "
        "CASH para que sea comparable entre carteras con y sin cash blending.",
        st_body,
    )
)
story.append(
    Paragraph(
        "<b>4. Tolerancias.</b> 1e-6 para sumas y long-only; +1 % slack sobre vol "
        "cap (errores de redondeo de PyPortfolioOpt). Centralizadas en validators.py.",
        st_body,
    )
)
story.append(
    Paragraph(
        "<b>5. Reproducibilidad.</b> El notebook puede regenerarse desde código "
        "vía <code>notebooks/_build_notebook.py</code>, evitando conflictos de "
        "merge en JSON.",
        st_body,
    )
)

# --- §13 ---
story.append(
    section_header(
        "13", "Nota metodológica: cartera ex-ante vs cartera OOS-clean", "s13"
    )
)
story.append(
    Paragraph(
        "Al arrancar la implementación del <b>M4 (backtesting walk-forward)</b> "
        "se identificó una sutileza temporal en el uso de los pesos producidos "
        "por este módulo. Esta sección la documenta para que la separación de "
        "roles entre M3 y M4 quede explícita en la memoria.",
        st_body,
    )
)
story.append(Paragraph("El problema:", st_h3))
story.append(
    Paragraph(
        "Los pesos persistidos en <code>outputs/m3/weights.parquet</code> se "
        "han calculado con μ y Σ estimados sobre <b>todo el histórico "
        "disponible</b> (2010-09 → 2026-05). Es decir, los parámetros del "
        "optimizador ya 'han visto' el régimen 2020-2026. Si esos pesos se "
        "aplicaran sin más sobre una ventana OOS 2020-2026, el experimento "
        "contendría <b>look-ahead bias en la fase de estimación de "
        "parámetros</b>, incumpliendo el principio walk-forward que la Fase 0 "
        "del TFM declara como requisito contractual.",
        st_body,
    )
)
story.append(Paragraph("La solución: dos carteras con roles disjuntos", st_h3))
story.append(
    Paragraph(
        "En lugar de regenerar <code>weights.parquet</code> y perder la "
        "cartera 'producción' que el roboadvisor recomendaría hoy, M3 y M4 "
        "coexisten con responsabilidades claramente separadas:",
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
                "¿Qué se habría recomendado en 2019 y cómo se comportó?",
            ],
        ],
        col_widths=[5.5 * cm, 4.5 * cm, 6.5 * cm],
    )
)
story.append(Spacer(1, 0.2 * cm))
story.append(
    Paragraph(
        "Ambas son <b>legítimas</b> y <b>necesarias</b>:",
        st_body,
    )
)
story.append(
    Paragraph(
        "• La <b>ex-ante</b> es la cartera de producción: el output que un "
        "cliente real recibiría si abriera la cuenta hoy, porque incorpora "
        "toda la información disponible.",
        st_bullet,
    )
)
story.append(
    Paragraph(
        "• La <b>OOS-clean</b> es la cartera de <b>validación científica</b>. "
        "Reusa los mismos optimizadores de <code>src/m3_portfolio/</code> "
        "(mismas restricciones UCITS, mismos vol caps) pero con μ y Σ "
        "recalculados sobre la ventana de entrenamiento. Sus pesos se aplican "
        "al periodo OOS para producir métricas defendibles.",
        st_bullet,
    )
)
story.append(
    callout(
        "Optimizador agnóstico al tiempo",
        "Las API públicas del paquete <code>m3_portfolio</code> no cambian: los "
        "optimizadores no saben de fechas, sólo de matrices (μ, Σ). Quién "
        "decide qué ventana temporal usar es responsabilidad del "
        "<b>orquestador</b> (este notebook para M3, el notebook de backtesting "
        "para M4), no del optimizador. Esta separación permite reusar "
        "literalmente el mismo <code>MinVarianceOptimizer</code>, "
        "<code>MaxSharpeOptimizer</code> y <code>HRPOptimizer</code> en ambos "
        "contextos sin riesgo de contaminación temporal.",
        DEEPBLUE,
    )
)

# --- Apéndice ---
story.append(section_header("A", "Apéndice — Inventario de ficheros", "sA"))
story.append(Paragraph("Paquete (m3_portfolio):", st_h3))
for f, desc in [
    ("portfolio.py", "dataclass Portfolio"),
    ("base.py", "Protocol PortfolioOptimizer"),
    ("constraints.py", "UCITS + vol cap + HHI"),
    ("validators.py", "validación post-hoc"),
    ("_build.py", "ensamblador compartido"),
    ("min_variance.py", "MinVarianceOptimizer"),
    ("max_sharpe.py", "MaxSharpeOptimizer (con fallback)"),
    ("hrp.py", "HRPOptimizer"),
    ("equal_weight.py", "EqualWeightOptimizer"),
    ("__init__.py", "API pública"),
]:
    story.append(Paragraph(f"• <code>{f}</code> — {desc}", st_bullet))
story.append(Paragraph("Tests (tests/):", st_h3))
for f in ["conftest.py", "test_optimizers.py", "test_constraints.py", "test_validators.py"]:
    story.append(Paragraph(f"• <code>{f}</code>", st_bullet))
story.append(Paragraph("Notebook (notebooks/):", st_h3))
story.append(Paragraph("• <code>M3_optimizacion_carteras.ipynb</code> — orquestador", st_bullet))
story.append(Paragraph("• <code>_build_notebook.py</code> — regenerador", st_bullet))
story.append(Paragraph("Outputs (data/m3_outputs/):", st_h3))
for f in ["weights.parquet", "portfolios_summary.json", "Memoria_M3.md", "Memoria_M3.pdf"]:
    story.append(Paragraph(f"• <code>{f}</code>", st_bullet))


# Build
doc.build(story)
print(f"Wrote {OUTPUT}")
