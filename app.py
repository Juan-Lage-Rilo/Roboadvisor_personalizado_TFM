"""
Demo M5 — Roboadvisor TFM (Streamlit Cloud)
===========================================
Interfaz del módulo M1 (perfilado del inversor). El cuestionario MiFID II
documentado en ``docs/mifid/`` (12 preguntas cerradas B1–B4 + 3 abiertas)
alimenta el **modelo canónico de prudencia asimétrica** del notebook M1:

- las 12 cerradas producen un ``q_norm`` (Plantilla C sin B5, renormalizado)
  que fija el **perfil base**;
- el análisis de sentimiento NLP de las 3 abiertas **solo puede bajar** el
  perfil (nunca subirlo) vía ``classify_profile``;
- la **regla de suelo** (capacidad económica, P5/P6) actúa como puerta previa.

Todas las preguntas (cerradas y abiertas) son **obligatorias**: el formulario
no se procesa hasta que están completas. Los radios no llevan opción
preseleccionada (``index=None``) para evitar un sesgo silencioso hacia la
primera respuesta.

La inferencia NLP es REMOTA (HuggingFace Inference API, Opus-MT ES→EN →
FinBERT): la app no carga modelos en local. El token HF se lee de
``st.secrets["HF_TOKEN"]`` — nunca se hardcodea.

Tema / estética
---------------
Todo el aspecto (fondo negro, logo, marca, tarjetas blancas, tipografía) se
aplica por CSS dentro de este archivo. El **color del círculo del radio
seleccionado** lo dibuja BaseWeb a partir del ``primaryColor`` del tema de
Streamlit; el CSS intenta teñirlo de dorado, pero si tu versión lo ignora,
crea ``.streamlit/config.toml`` en la raíz del repo con::

    [theme]
    primaryColor = "#D6AD5B"
    backgroundColor = "#000000"
    secondaryBackgroundColor = "#121212"
    textColor = "#EDE7DA"

(``config.toml`` SÍ se commitea; solo ``.streamlit/secrets.toml`` va en
``.gitignore``.)
"""
from __future__ import annotations

from typing import Any

import streamlit as st

from src.m1_mifid_questionnaire import (
    OPEN_QUESTIONS,
    QUESTIONNAIRE,
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
    --ink:    #1A1A1A;
    --gold:   #B8924A;
    --gold-l: #D6AD5B;
    --muted:  #6F6A60;
    --line:   #E7E2D6;
}

/* Negro solo como margen alrededor del panel */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"] {
    background: #000000 !important;
}

/* ---------- GRAN RECUADRO BLANCO: todo el contenido vive aquí ---------- */
.block-container {
    max-width: 900px;
    background: #FFFFFF;
    border-radius: 16px;
    padding: 2.8rem 3.2rem 3.2rem;
    margin-top: 2.2rem;
    margin-bottom: 2.2rem;
    box-shadow: 0 12px 48px rgba(0, 0, 0, 0.55);
}

/* Tipografía + texto oscuro por defecto (todo va sobre blanco) */
html, body, [class*="css"], .stMarkdown, p, li, span, label {
    font-family: 'Inter', -apple-system, sans-serif;
    color: var(--ink);
}

/* ---------- Cabecera de marca (dentro del panel blanco) ---------- */
.brand-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.6rem;
}
/* Chapa negra para que el logo conserve su fondo mate sobre el blanco */
.logo-badge {
    background: #000000;
    border-radius: 10px;
    padding: 7px 9px;
    display: inline-flex;
    align-items: center;
}
.brand-name {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 1.9rem;
    font-weight: 600;
    letter-spacing: 1px;
    color: var(--gold);
}
.brand-name .ia { color: var(--ink); font-weight: 700; }

/* Título principal (sobre el blanco, sin recuadro adicional) */
.app-title {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-weight: 600;
    font-size: 2.5rem;
    line-height: 1.1;
    letter-spacing: 0.3px;
    color: var(--ink);
    margin: 0.2rem 0 0;
}
.app-rule {
    width: 56px; height: 2px; background: var(--gold);
    margin: 0.9rem 0 2rem 0; border: none;
}

/* Títulos de apartado en tinta serif */
[data-testid="stSubheader"], h2, h3 {
    font-family: 'Cormorant Garamond', Georgia, serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.2px;
    color: var(--ink) !important;
}

/* Captions */
[data-testid="stCaptionContainer"], .stCaption { color: var(--muted) !important; }

/* Divisores finos */
hr { border-color: var(--line) !important; }

/* ---------- Radios: SOLO texto oscuro; el control queda intacto ---------- */
/* Texto de la pregunta y de las opciones (targetea <p>, nunca el círculo) */
[data-testid="stRadio"] [data-testid="stWidgetLabel"] p,
[data-testid="stRadio"] [role="radiogroup"] label p {
    color: var(--ink) !important;
}
[data-testid="stRadio"] [role="radiogroup"] > label { margin: 3px 0; }
/* Círculo seleccionado en DORADO (no rojo), sin afectar al texto */
[data-testid="stRadio"] input[type="radio"] { accent-color: var(--gold); }
[data-testid="stRadio"] [data-baseweb="radio"] svg { fill: var(--gold); }
[data-testid="stRadio"] [data-baseweb="radio"] svg circle { fill: var(--gold); }

/* Botón en dorado */
.stButton > button, .stFormSubmitButton > button {
    background: var(--gold);
    color: #FFFFFF;
    border: 1px solid var(--gold);
    border-radius: 3px;
    padding: 0.55rem 1.7rem;
    font-weight: 600;
    letter-spacing: 0.4px;
    transition: all .18s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    background: #FFFFFF;
    color: var(--gold);
}

/* Inputs (preguntas abiertas) sobre blanco */
.stTextArea textarea {
    border-radius: 3px !important;
    border: 1px solid var(--line) !important;
    background: #FFFFFF !important;
    color: var(--ink) !important;
}
.stTextArea textarea:focus { border-color: var(--gold) !important; box-shadow: none !important; }

/* Formulario sin recuadro propio */
[data-testid="stForm"] { border: none; padding: 0; }

/* Métricas */
[data-testid="stMetricValue"] {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-weight: 600;
    color: var(--ink);
}
[data-testid="stMetricLabel"] { color: var(--muted) !important; }

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
        <div class="logo-badge">{_LOGO_SVG}</div>
        <div class="brand-name">Invest<span class="ia">IA</span></div>
    </div>
    <div class="app-title">Test MiFID II · Perfilado del inversor</div>
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
    # Inferencia — modelo canónico de prudencia asimétrica
    # =======================================================================
    with st.spinner("Analizando respuestas abiertas con la HuggingFace Inference API…"):
        try:
            profiler = _get_profiler()
            result = profiler.profile_investor_questionnaire(closed, textos)
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
    # Nota para el asesor  (justificación + trazabilidad, apartado aparte)
    # =======================================================================
    st.subheader("Nota para el asesor")
    st.caption(
        "Justificación del perfil asignado y métricas de soporte. Información "
        "interna de trazabilidad, no destinada al cliente final."
    )

    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Perfil base (cuestionario)",
        result.perfil_base.capitalize(),
        help="Derivado solo de las 12 preguntas cerradas (q_norm).",
    )
    c2.metric(
        "Escalones bajados por NLP",
        result.escalones_bajados,
        help="La prudencia asimétrica solo permite bajar, nunca subir.",
    )
    c3.metric(
        "Regla de suelo",
        "Activa" if result.floor_rule_activa else "No activa",
    )

    if result.floor_rule_activa:
        st.warning(
            "**Regla de suelo activada**: la capacidad económica declarada "
            "(impacto grave de una pérdida o endeudamiento alto) fija el perfil "
            "en **Conservador** con independencia del resto. Es una salvaguarda "
            "regulatoria (Directrices ESMA)."
        )
    elif result.escalones_bajados > 0:
        st.info(
            f"El análisis de sentimiento ha **bajado** el perfil de "
            f"*{result.perfil_base}* a *{result.perfil_final}* "
            f"({result.escalones_bajados} escalón/es): el texto libre es más "
            f"prudente que las respuestas cerradas (divergencia "
            f"{result.divergencia:+.2f})."
        )
    elif result.flag_revisar:
        st.info(
            "Divergencia leve entre cuestionario y texto libre: se mantiene el "
            "perfil base, pero queda marcado para **revisión del texto**."
        )

    # --- Desglose: fusión por prudencia asimétrica -------------------------
    with st.expander("¿Por qué este perfil? — fusión por prudencia asimétrica", expanded=True):
        st.markdown(
            "El cuestionario fija el **perfil base**; el NLP solo puede **bajarlo** "
            "según la *divergencia* = `q_norm − sentiment_norm`."
        )
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("q_norm (cuestionario)", f"{result.q_norm:+.2f}", help="Rango [-1, +1].")
        m2.metric("Sentimiento NLP", f"{result.sentiment_score:.2f}", help="Rango [0, 1].")
        m3.metric("Divergencia", f"{result.divergencia:+.2f}")
        m4.metric("Confianza NLP", result.confidence.capitalize())
        st.table(
            {
                "Bloque cerrado": [
                    "Conocimientos",
                    "Situación financiera",
                    "Objetivos",
                    "ESG",
                ],
                "Score (Sᵢ)": [result.s1, result.s2, result.s3, result.s4],
            }
        )
        st.caption(
            f"Perfil base **{result.perfil_base}** → final **{result.perfil_final}** "
            f"({result.escalones_bajados} escalón/es). El sentimiento es la media "
            "del análisis FinBERT de las respuestas abiertas (prob-weighted)."
        )

    with st.expander("Detalle / trazabilidad (JSON)"):
        detalle: dict[str, Any] = result.as_dict()
        st.json(detalle)
