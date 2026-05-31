"""
Demo M5 — Roboadvisor TFM (Streamlit Cloud)
===========================================
Interfaz del módulo M1 (perfilado del inversor) mediante el **cuestionario
MiFID II Plantilla C** documentado en ``docs/mifid/``: 12 preguntas cerradas
(bloques B1–B4) + 3 abiertas (B5, análisis de sentimiento NLP), con pesos
adaptativos por horizonte y regla de suelo.

La inferencia NLP es REMOTA (HuggingFace Inference API, Opus-MT ES→EN →
FinBERT): la app no carga modelos en local. El token HF se lee de
``st.secrets["HF_TOKEN"]`` — nunca se hardcodea.
"""
from __future__ import annotations

import streamlit as st

from src.m1_mifid_questionnaire import (
    OPEN_QUESTIONS,
    QUESTIONNAIRE,
    score_mifid,
)
from src.m1_remote_profiling import RemoteProfiler, get_hf_token

st.set_page_config(
    page_title="Roboadvisor TFM — Perfilado MiFID",
    page_icon="🧭",
    layout="wide",
)

# --- Color por perfil (para tarjetas de resultado) -------------------------
_PERFIL_COLOR = {
    "Conservador": "#2E7D32",
    "Moderado": "#F9A825",
    "Agresivo": "#C62828",
}


@st.cache_resource(show_spinner=False)
def _get_profiler() -> RemoteProfiler:
    """Crea (y cachea) el perfilador remoto. Requiere HF_TOKEN configurado."""
    return RemoteProfiler()


# ===========================================================================
# Cabecera
# ===========================================================================
st.title("🧭 Roboadvisor TFM — Perfilado del inversor (M1)")
st.caption(
    "Cuestionario MiFID II · **Plantilla C** (pesos adaptativos por horizonte + "
    "regla de suelo). Análisis de sentimiento remoto: Opus-MT ES→EN → FinBERT."
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
with st.form("cuestionario_mifid"):
    closed: dict[str, int] = {}

    for block_id, block in QUESTIONNAIRE.items():
        st.subheader(f"{block_id} · {block['titulo']}")
        st.caption(block["norma"])
        for q in block["questions"]:
            label = st.radio(
                q.text,
                options=q.labels,
                index=0,
                help=q.help or None,
                key=q.key,
            )
            closed[q.key] = q.points_for(label)
        st.divider()

    st.subheader("B5 · Análisis de sentimiento (respuestas abiertas)")
    st.caption(
        "Tres preguntas abiertas, cada una procesada con FinBERT vía API. "
        "Déjalas en blanco para tratarlas como neutrales."
    )
    textos: list[str] = []
    for oq in OPEN_QUESTIONS:
        textos.append(
            st.text_area(oq.text, value="", height=90, placeholder=oq.placeholder, key=oq.key)
        )

    enviado = st.form_submit_button("Calcular perfil", type="primary")


# ===========================================================================
# Inferencia y resultados
# ===========================================================================
if enviado:
    with st.spinner("Analizando respuestas abiertas con la HuggingFace Inference API…"):
        try:
            profiler = _get_profiler()
            nlp_scores = [profiler.nlp_proxy_score_es(t) for t in textos]
            result = score_mifid(closed, nlp_scores)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Error en el perfilado: {exc}")
            st.stop()

    st.subheader("Resultado del perfilado")

    color = _PERFIL_COLOR.get(result.perfil, "#455A64")
    st.markdown(
        f"""
        <div style="background:{color};padding:18px 22px;border-radius:12px;
                    color:white;margin-bottom:10px;">
            <div style="font-size:0.9rem;opacity:0.85;">PERFIL DE RIESGO</div>
            <div style="font-size:2rem;font-weight:700;">{result.perfil}</div>
            <div style="font-size:1rem;opacity:0.9;">
                Volatilidad máxima anual (M3): {result.sigma_max:.0%}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Score final", f"{result.score_final:.3f}", help="Rango [0, 1].")
    c2.metric("Bloque NLP (B5)", f"{result.s5:.2f}")
    c3.metric(
        "Regla de suelo",
        "Activa" if result.floor_rule_activa else "No activa",
    )

    if result.floor_rule_activa:
        st.warning(
            "⚠️ **Regla de suelo activada**: tu capacidad económica declarada "
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
                    "B1 · Conocimientos",
                    "B2 · Situación financiera",
                    "B3 · Objetivos",
                    "B4 · ESG",
                    "B5 · NLP (sentimiento)",
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
            "Los pesos cambian según el horizonte temporal (P8). El NLP (B5) "
            "es la media de las 3 respuestas abiertas (positivo=1.0 · "
            "neutral=0.5 · negativo=0.0)."
        )

    with st.expander("Detalle / trazabilidad (JSON)"):
        st.json(result.as_dict())
