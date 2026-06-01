"""
Demo M5 — Roboadvisor TFM (Streamlit Cloud)
===========================================
Interfaz del módulo M1 (perfilado del inversor) mediante el **cuestionario
MiFID II Plantilla C** documentado en ``docs/mifid/``: 12 preguntas cerradas
(bloques B1–B4) + 3 abiertas (B5, análisis de sentimiento NLP), con pesos
adaptativos por horizonte y regla de suelo.

Todas las preguntas (cerradas y abiertas) son **obligatorias**: el formulario
no se procesa hasta que están completas. Los radios no llevan opción
preseleccionada (``index=None``) para evitar un sesgo silencioso hacia la
primera respuesta.

La inferencia NLP es REMOTA (HuggingFace Inference API, Opus-MT ES→EN →
FinBERT): la app no carga modelos en local. El token HF se lee de
``st.secrets["HF_TOKEN"]`` — nunca se hardcodea.
"""
from __future__ import annotations

from typing import Any

import streamlit as st

from src.m1_mifid_questionnaire import (
    OPEN_QUESTIONS,
    QUESTIONNAIRE,
    score_mifid,
)
from src.m1_remote_profiling import RemoteProfiler, get_hf_token

st.set_page_config(
    page_title="Test MiFID II — Perfilado del inversor",
    page_icon="🧭",
    layout="centered",
)

# ===========================================================================
# Estética — fintech minimalista / lujo (tinta + dorado sobre marfil)
# --- Logo (SVG generado a partir del JSON de marca) ------------------------
# Monograma "I" en oro champán inspirado en una vela japonesa: cuerpo con
# remates tipo serif, mecha vertical que sobresale arriba/abajo y barras
# internas (huecos negros) que evocan columnas de candlestick. Flat vector,
# sin gradientes ni 3D, sobre negro mate.
_LOGO_SVG = """
<svg width="46" height="46" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"
     role="img" aria-label="InvestIA logo">
  <!-- mecha de la vela (sobresale arriba y abajo) -->
  <rect x="49" y="8"  width="2" height="84" fill="#D6AD5B"/>
  <!-- remate superior -->
  <rect x="31" y="17" width="38" height="7" fill="#D6AD5B"/>
  <!-- remate inferior -->
  <rect x="31" y="76" width="38" height="7" fill="#D6AD5B"/>
  <!-- cuerpo vertical de la I -->
  <rect x="37" y="24" width="26" height="52" fill="#D6AD5B"/>
  <!-- barras internas tipo candlestick (huecos sobre negro) -->
  <rect x="42.5" y="24" width="2.2" height="52" fill="#000000"/>
  <rect x="49"   y="24" width="2.2" height="52" fill="#000000"/>
  <rect x="55.5" y="24" width="2.2" height="52" fill="#000000"/>
</svg>
"""

# ===========================================================================
# NOTA: cadena normal (no f-string) para no tener que escapar las llaves CSS.
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@300;400;500;600&display=swap');

:root {
    --ink:    #111111;
    --gold:   #D6AD5B;
    --gold-d: #B8924A;
    --ivory:  #EDE7DA;
    --muted:  #9A958B;
    --line:   #2A2A2A;
    --panel:  #121212;
}

/* Fondo negro mate en toda la app */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"] {
    background: #000000 !important;
}

/* Tipografía + color de texto claro por defecto */
html, body, [class*="css"], .stMarkdown, p, li, span, label {
    font-family: 'Inter', -apple-system, sans-serif;
    color: var(--ivory);
}

.block-container { max-width: 820px; padding-top: 2rem; }

/* ---------- Cabecera de marca ---------- */
.brand-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.4rem;
}
.brand-left { display: flex; align-items: center; }
.brand-name {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 1.9rem;
    font-weight: 600;
    letter-spacing: 1px;
    color: var(--gold);
}
.brand-name .ia { color: #FFFFFF; font-weight: 700; }

/* Título dentro de recuadro blanco para legibilidad */
.title-box {
    display: inline-block;
    background: #FFFFFF;
    color: #111111;
    padding: 14px 22px;
    border-radius: 4px;
    border: 1px solid var(--gold);
}
.title-box .app-title {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-weight: 600;
    font-size: 2.1rem;
    line-height: 1.1;
    letter-spacing: 0.3px;
    color: #111111;
    margin: 0;
}
.app-rule {
    width: 56px; height: 2px; background: var(--gold);
    margin: 1rem 0 2rem 0; border: none;
}

/* Títulos de apartado (subheaders) en oro */
[data-testid="stSubheader"], h2, h3 {
    font-family: 'Cormorant Garamond', Georgia, serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.2px;
    color: var(--gold) !important;
}

/* Captions y etiquetas claras (sobre fondo negro) */
[data-testid="stCaptionContainer"], .stCaption { color: var(--muted) !important; }
[data-testid="stTextArea"] [data-testid="stWidgetLabel"] label { color: var(--ivory) !important; }

/* Divisores finos */
hr { border-color: var(--line) !important; }

/* ---------- Preguntas en tarjeta blanca ---------- */
[data-testid="stRadio"] {
    background: #FFFFFF;
    border: 1px solid var(--gold);
    border-radius: 6px;
    padding: 14px 18px;
    margin-bottom: 12px;
}
/* todo el texto de la tarjeta en tinta */
[data-testid="stRadio"] [data-testid="stWidgetLabel"] label,
[data-testid="stRadio"] label,
[data-testid="stRadio"] p,
[data-testid="stRadio"] div {
    color: #111111 !important;
}

/* Botón de radio: dorado con punto interior negro + sombra negra al marcar */
[data-baseweb="radio"] input:checked + div {
    background-color: var(--gold) !important;
    border-color: #000000 !important;
    box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.40) !important;
}
[data-baseweb="radio"] input:checked + div > div {
    background-color: #000000 !important;   /* punto interior negro */
}
/* círculo sin marcar, visible sobre blanco */
[data-baseweb="radio"] input:not(:checked) + div {
    background-color: #FFFFFF !important;
    border-color: #B7B0A0 !important;
}

/* Botón: oro sobre negro */
.stButton > button, .stFormSubmitButton > button {
    background: var(--gold);
    color: #000000;
    border: 1px solid var(--gold);
    border-radius: 2px;
    padding: 0.55rem 1.6rem;
    font-weight: 600;
    letter-spacing: 0.4px;
    transition: all .18s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    background: transparent;
    color: var(--gold);
}

/* Inputs sobre fondo oscuro */
.stTextArea textarea {
    border-radius: 2px !important;
    border: 1px solid var(--line) !important;
    background: var(--panel) !important;
    color: var(--ivory) !important;
}
.stTextArea textarea:focus { border-color: var(--gold) !important; box-shadow: none !important; }

/* Formulario sin recuadro propio (las tarjetas dan la estructura) */
[data-testid="stForm"] { border: none; padding: 0; }

/* Métricas */
[data-testid="stMetricValue"] {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-weight: 600;
    color: var(--ivory);
}
[data-testid="stMetricLabel"] { color: var(--muted) !important; }

/* Tablas legibles sobre negro */
table { color: var(--ivory) !important; }
thead th { color: var(--gold) !important; border-color: var(--line) !important; }
tbody td, tbody th { border-color: var(--line) !important; }

/* Ocultar cromo de Streamlit */
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }
</style>
"""
st.markdown(_CSS, unsafe_allow_html=True)

# --- Paleta sobria por perfil (para la tarjeta de resultado) ---------------
_PERFIL_COLOR = {
    "Conservador": "#1F4D3A",  # verde bosque
    "Moderado": "#9A7A38",     # bronce/dorado oscuro
    "Agresivo": "#7A2E2E",     # burdeos
}


@st.cache_resource(show_spinner=False)
def _get_profiler() -> RemoteProfiler:
    """Crea (y cachea) el perfilador remoto. Requiere HF_TOKEN configurado."""
    return RemoteProfiler()


# ===========================================================================
# Cabecera  (cambio 1: título único, sin subtítulo)
# ===========================================================================
st.markdown(
    f"""
    <div class="brand-bar">
        <div class="brand-left">{_LOGO_SVG}</div>
        <div class="brand-name">Invest<span class="ia">IA</span></div>
    </div>
    <div class="title-box">
        <div class="app-title">Test MiFID II · Perfilado del inversor</div>
    </div>
    <hr class="app-rule">
    """,
    unsafe_allow_html=True,
)

# --- Aviso temprano si falta el token --------------------------------------
if not get_hf_token():
    st.error(
        "Falta el token de HuggingFace. Configura `HF_TOKEN` en los *secrets* de "
        "Streamlit Cloud, o en `.streamlit/secrets.toml` para ejecución local:\n\n"
        "```toml\nHF_TOKEN = \"hf_tu_token_aqui\"\n```"
    )
    st.stop()


# ===========================================================================
# Formulario — cuestionario completo
# ===========================================================================
# Índice key -> objeto pregunta, para calcular puntos solo tras validar.
_Q_BY_KEY = {
    q.key: q
    for block in QUESTIONNAIRE.values()
    for q in block["questions"]
}

with st.form("cuestionario_mifid"):
    # Cambio 3: guardamos la etiqueta seleccionada (puede ser None) y
    # puntuamos después de validar que no falte ninguna respuesta.
    closed_labels: dict[str, str | None] = {}

    for block in QUESTIONNAIRE.values():
        # Cambio 2: solo el título descriptivo, sin índice de bloque.
        st.subheader(block["titulo"])
        st.caption(block["norma"])
        for q in block["questions"]:
            closed_labels[q.key] = st.radio(
                q.text,
                options=q.labels,
                index=None,  # sin preselección -> respuesta obligatoria real
                help=q.help or None,
                key=q.key,
            )
        st.divider()

    # Cambio 2: título descriptivo sin "B5 ·".
    st.subheader("Análisis de sentimiento (respuestas abiertas)")
    # Cambio 3: ya no se pueden dejar en blanco.
    st.caption(
        "Tres preguntas abiertas, cada una procesada con FinBERT vía API. "
        "Todas son obligatorias."
    )
    textos: list[str] = []
    for oq in OPEN_QUESTIONS:
        textos.append(
            st.text_area(
                oq.text, value="", height=90, placeholder=oq.placeholder, key=oq.key
            )
        )

    enviado = st.form_submit_button("Calcular perfil", type="primary")


# ===========================================================================
# Validación de obligatoriedad  (cambio 3)
# ===========================================================================
if enviado:
    faltan_cerradas = [k for k, v in closed_labels.items() if v is None]
    faltan_abiertas = [i + 1 for i, t in enumerate(textos) if not t.strip()]

    if faltan_cerradas or faltan_abiertas:
        partes: list[str] = []
        if faltan_cerradas:
            partes.append(
                f"{len(faltan_cerradas)} pregunta(s) cerrada(s) sin responder"
            )
        if faltan_abiertas:
            partes.append(
                "respuesta(s) abierta(s) en blanco: "
                + ", ".join(f"#{n}" for n in faltan_abiertas)
            )
        st.error(
            "Todas las preguntas son obligatorias. Completa: " + " · ".join(partes) + "."
        )
        st.stop()

    # Todas respondidas -> ahora sí puntuamos las cerradas.
    closed: dict[str, int] = {
        k: _Q_BY_KEY[k].points_for(label)
        for k, label in closed_labels.items()
        if label is not None
    }

    # =======================================================================
    # Inferencia
    # =======================================================================
    with st.spinner("Analizando respuestas abiertas con la HuggingFace Inference API…"):
        try:
            profiler = _get_profiler()
            nlp_scores = [profiler.nlp_proxy_score_es(t) for t in textos]
            result = score_mifid(closed, nlp_scores)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Error en el perfilado: {exc}")
            st.stop()

    # =======================================================================
    # Resultado del perfilado  (solo el veredicto)
    # =======================================================================
    st.subheader("Resultado del perfilado")

    color = _PERFIL_COLOR.get(result.perfil, "#37413B")
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{color} 0%,{color}E6 100%);
                    padding:26px 30px;border-radius:6px;color:#FFFFFF;
                    border:1px solid rgba(184,146,74,0.45);
                    box-shadow:0 1px 0 rgba(0,0,0,0.04);margin-bottom:8px;">
            <div style="font-size:0.72rem;letter-spacing:2px;text-transform:uppercase;
                        opacity:0.8;">Perfil de riesgo</div>
            <div style="font-family:'Cormorant Garamond',Georgia,serif;font-size:2.6rem;
                        font-weight:600;line-height:1.1;">{result.perfil}</div>
            <div style="font-size:0.95rem;opacity:0.9;margin-top:4px;">
                Volatilidad máxima anual (M3): {result.sigma_max:.0%}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # =======================================================================
    # Nota para el asesor  (cambio 4: justificación + score, apartado aparte)
    # =======================================================================
    st.subheader("Nota para el asesor")
    st.caption(
        "Justificación del perfil asignado y puntuación de soporte. Información "
        "interna de trazabilidad, no destinada al cliente final."
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Score final", f"{result.score_final:.3f}", help="Rango [0, 1].")
    c2.metric("Bloque NLP", f"{result.s5:.2f}")
    c3.metric(
        "Regla de suelo",
        "Activa" if result.floor_rule_activa else "No activa",
    )

    if result.floor_rule_activa:
        st.warning(
            "**Regla de suelo activada**: la capacidad económica declarada "
            "(impacto grave de una pérdida o endeudamiento alto) fija el perfil "
            "en **Conservador** con independencia del score numérico. Es una "
            "salvaguarda regulatoria (Directrices ESMA)."
        )

    # --- Desglose por bloques ----------------------------------------------
    with st.expander("¿Por qué este perfil? — desglose por bloques", expanded=True):
        pesos = result.pesos_horizonte
        st.markdown("**Score = Σ pesoᵢ(horizonte) · Sᵢ**")
        st.table(
            {
                "Bloque": [
                    "Conocimientos",
                    "Situación financiera",
                    "Objetivos",
                    "ESG",
                    "NLP (sentimiento)",
                ],
                "Score (Sᵢ)": [result.s1, result.s2, result.s3, result.s4, result.s5],
                "Peso": [f"{w:.0%}" for w in pesos],
                "Aportación": [
                    round(pesos[i] * s, 3)
                    for i, s in enumerate(
                        [result.s1, result.s2, result.s3, result.s4, result.s5]
                    )
                ],
            }
        )
        st.caption(
            "Los pesos cambian según el horizonte temporal (P8). El NLP es la "
            "media de las 3 respuestas abiertas (positivo=1.0 · neutral=0.5 · "
            "negativo=0.0)."
        )

    with st.expander("Detalle / trazabilidad (JSON)"):
        detalle: dict[str, Any] = result.as_dict()
        st.json(detalle)
