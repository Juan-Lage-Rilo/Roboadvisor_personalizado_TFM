"""
Demo M5 — Roboadvisor TFM (Streamlit Cloud)
===========================================
Interfaz de la demo del módulo M1 (perfilado del inversor) por INFERENCIA
REMOTA. La app NO carga modelos en local: delega en la HuggingFace Inference
API a través de :class:`src.m1_remote_profiling.RemoteProfiler` (Rama A:
Opus-MT ES→EN → FinBERT).

El token HF se lee de ``st.secrets["HF_TOKEN"]`` — nunca se hardcodea.
"""
from __future__ import annotations

import streamlit as st

from src.m1_remote_profiling import RemoteProfiler, get_hf_token

st.set_page_config(
    page_title="Roboadvisor TFM — Demo M1",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

st.title("Roboadvisor TFM — Perfilado del inversor (M1)")
st.caption(
    "Demo M5 · Inferencia remota vía HuggingFace Inference API "
    "(Opus-MT ES→EN → FinBERT). Sin modelos en local."
)


@st.cache_resource(show_spinner=False)
def _get_profiler() -> RemoteProfiler:
    """Crea (y cachea) el perfilador remoto. Requiere HF_TOKEN configurado."""
    return RemoteProfiler()


# --- Aviso temprano si falta el token --------------------------------------
if not get_hf_token():
    st.error(
        "Falta el token de HuggingFace. Configura `HF_TOKEN` en los *secrets* de "
        "Streamlit Cloud, o en `.streamlit/secrets.toml` para ejecución local:\n\n"
        "```toml\nHF_TOKEN = \"hf_tu_token_aqui\"\n```"
    )
    st.stop()


# --- Formulario ------------------------------------------------------------
with st.form("perfilado"):
    col_q, col_t = st.columns([1, 2])

    with col_q:
        q_score_raw = st.slider(
            "Puntuación del cuestionario MiFID II (0–100)",
            min_value=0.0,
            max_value=100.0,
            value=50.0,
            step=1.0,
            help="Resultado agregado del cuestionario cerrado (Rama A del flujo M1).",
        )

    with col_t:
        texto_libre_es = st.text_area(
            "Respuesta abierta del inversor (en castellano)",
            value="",
            height=160,
            placeholder=(
                "Ej.: No me gusta perder dinero. Prefiero rentabilidades modestas "
                "pero seguras..."
            ),
        )

    enviado = st.form_submit_button("Calcular perfil", type="primary")


# --- Inferencia y resultados ----------------------------------------------
if enviado:
    if not texto_libre_es.strip():
        st.warning("Introduce una respuesta abierta para analizar el sentimiento.")
        st.stop()

    with st.spinner("Consultando la HuggingFace Inference API…"):
        try:
            result = _get_profiler().profile_investor(texto_libre_es, q_score_raw)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Error en la inferencia remota: {exc}")
            st.stop()

    st.subheader("Resultado del perfilado")

    c1, c2, c3 = st.columns(3)
    c1.metric("Perfil base", result.perfil_base.capitalize())
    c2.metric(
        "Perfil final",
        result.perfil_final.capitalize(),
        delta=(
            f"-{result.escalones_bajados} escalón(es)"
            if result.escalones_bajados
            else "sin cambio"
        ),
        delta_color="inverse",
    )
    c3.metric("Vol. máx. anual (M3)", f"{result.volatility_cap:.0%}")

    if result.flag_revisar:
        st.warning(
            "⚠️ Divergencia leve detectada entre cuestionario y texto libre. "
            "Se recomienda revisión manual (no se baja el perfil)."
        )

    with st.expander("Detalle / trazabilidad"):
        st.json(
            {
                "q_score_raw": result.q_score_raw,
                "q_norm": result.q_norm,
                "sentiment_score": result.sentiment_score,
                "confidence": result.confidence,
                "divergencia": result.divergencia,
                "escalones_bajados": result.escalones_bajados,
                "flag_revisar": result.flag_revisar,
                "traduccion_en": result.texto_en,
            }
        )
        st.caption(
            "Nota demo: sin Rama B (RoBERTuito no soportado por hf-inference), la "
            "confianza se deriva de la probabilidad del top-label de FinBERT "
            "(umbrales 0.80/0.60). La lógica de fusión (prudencia asimétrica) es "
            "idéntica a la del notebook M1."
        )
