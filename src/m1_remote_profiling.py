"""
M1 — Perfilado del inversor por INFERENCIA REMOTA (demo M5 / Streamlit Cloud)
============================================================================
TFM · Roboadvisor personalizado para el inversor retail.

Este módulo es la variante de :mod:`src.m1_profiling` pensada para la demo
desplegada en Streamlit Cloud, donde la RAM disponible (~1 GB) NO permite cargar
``torch`` + ``transformers`` ni los pesos de los modelos en local. En su lugar,
la inferencia se delega en la **HuggingFace Inference API** mediante
:class:`huggingface_hub.InferenceClient`.

Diferencias frente al pipeline completo del notebook ``m1_nlp_profiling.ipynb``
------------------------------------------------------------------------------
- **Solo se usa la Rama A** del NLP dual: Opus-MT (ES→EN) → FinBERT, ambos vía
  API remota. La Rama B (RoBERTuito / pysentimiento) NO está soportada por el
  provider ``hf-inference``, por lo que se omite en la demo.
- Como sin Rama B no existe *agreement* inter-pipeline, la ``confidence`` no es
  calculable. La ruta canónica de la demo
  (:meth:`RemoteProfiler.profile_investor_questionnaire`) la **fija a "media"**
  (``CONFIDENCE_CLOUD_FIXED``), la banda intermedia honesta: ALTA/BAJA exigirían
  el agreement de la segunda red. La lógica de fusión en sí (``classify_profile``)
  se porta *verbatim*. (La ruta legacy de un solo texto,
  :meth:`profile_investor`, conserva la heurística ``_confidence_from_prob`` por
  compatibilidad, pero la app no la usa.)

Seguridad
---------
El token de HuggingFace NUNCA se hardcodea. Se lee de ``st.secrets["HF_TOKEN"]``
(en Streamlit Cloud o en ``.streamlit/secrets.toml``, ignorado por git) o, como
alternativa para scripts/tests, de la variable de entorno ``HF_TOKEN``.

Referencias
-----------
- Araci, D. (2019). FinBERT. arXiv:1908.10063.
- Tiedemann, J. & Thottingal, S. (2020). OPUS-MT. EAMT.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

from huggingface_hub import InferenceClient

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

__all__ = [
    "FINBERT_MODEL_ID",
    "OPUS_MT_ES_EN_MODEL_ID",
    "DIVERGENCE_THRESHOLDS",
    "PROFILE_ORDER",
    "VOLATILITY_CAP",
    "classify_profile",
    "classify_profile_advisory",
    "AGGRESSIVE_Q_NORM",
    "CONSERVATIVE_Q_NORM",
    "ADVISORY_FLAG_DIVERGENCE",
    "RemoteProfiler",
    "ProfileResult",
    "QuestionnaireProfileResult",
    "get_hf_token",
]

# ---------------------------------------------------------------------------
# Model IDs (Rama A únicamente — ver docstring del módulo)
# ---------------------------------------------------------------------------
FINBERT_MODEL_ID: str = "ProsusAI/finbert"
OPUS_MT_ES_EN_MODEL_ID: str = "Helsinki-NLP/opus-mt-es-en"

MAX_TEXT_CHARS: int = 512

# Mapeo de etiquetas FinBERT → signo del score, igual que en 03_inference.py.
_LABEL_MAP_FINBERT: dict[str, int] = {"positive": +1, "negative": -1, "neutral": 0}

# ===========================================================================
# Lógica de fusión — PORTADA VERBATIM de otros/notebooks_cells/05_fusion.py.
# NO MODIFICAR sin actualizar la memoria del TFM.
# ===========================================================================
DIVERGENCE_THRESHOLDS: dict[str, dict[str, float]] = {
    "alta":  {"grave": 0.50, "moderado": 0.30, "leve": 0.18},
    "media": {"grave": 0.70, "moderado": 0.45, "leve": 0.25},
    "baja":  {"grave": 0.90, "moderado": 0.70, "leve": 0.50},
}
PROFILE_ORDER = ("agresivo", "moderado", "conservador")
VOLATILITY_CAP = {"conservador": 0.08, "moderado": 0.15, "agresivo": 0.25}

# Confianza FIJA de la variante cloud (ver docstring del módulo). En Fase 0 la
# confianza sale del *agreement* inter-pipeline (FinBERT vs RoBERTuito); sin la
# Rama B, ALTA/BAJA no son alcanzables, así que se fija a la banda intermedia
# honesta "media". NO es un valor calculado: es una decisión documentada de la
# demo reducida.
CONFIDENCE_CLOUD_FIXED = "media"


def _base_profile(q_norm: float) -> str:
    if q_norm < -0.33:
        return "conservador"
    if q_norm < 0.33:
        return "moderado"
    return "agresivo"


def _downgrade(profile: str, steps: int) -> str:
    idx = PROFILE_ORDER.index(profile)
    return PROFILE_ORDER[min(idx + steps, len(PROFILE_ORDER) - 1)]


def classify_profile(
    q_score_normalized: float,
    sentiment_score: float,
    confidence: str,
) -> dict:
    """Aplica prudencia asimétrica al par (cuestionario, NLP)."""
    try:
        sentiment_norm = sentiment_score * 2.0 - 1.0  # [0,1] -> [-1,+1]
        divergence = q_score_normalized - sentiment_norm
        base = _base_profile(q_score_normalized)
        thr = DIVERGENCE_THRESHOLDS[confidence]

        flag_revisar = False
        steps = 0
        if divergence <= 0:
            steps = 0
        elif divergence > thr["grave"] and base == "agresivo":
            steps = 2
        elif divergence > thr["grave"]:
            steps = 1
        elif divergence > thr["moderado"]:
            steps = 1
        elif divergence > thr["leve"]:
            flag_revisar = True

        final = _downgrade(base, steps)
        return {
            "perfil_base": base,
            "perfil_final": final,
            "divergencia": round(float(divergence), 4),
            "flag_revisar": flag_revisar,
            "escalones_bajados": steps,
            "volatility_cap": VOLATILITY_CAP[final],
        }
    except Exception as exc:
        logger.error("classify_profile error: %s", exc)
        raise


# ===========================================================================
# Modelo de PRODUCCIÓN — el CUESTIONARIO decide, el NLP es ADVISORY.
# ===========================================================================
# Diagnóstico (casos reales caso_1/caso_2): FinBERT devuelve neutral (~0.5) para
# casi todos los textos de apetito de riesgo, porque mide polaridad de NOTICIAS
# financieras, no tolerancia al riesgo. El "sentimiento" no aporta señal fiable
# (`nlp_scores` ≈ [0.5, 0.5, 0.5] siempre), así que apostar el perfil al NLP
# genera falsos descensos. Decisión de diseño:
#
#   1. El perfil lo decide el CUESTIONARIO MiFID (q_norm + floor rule). El NLP
#      es ADVISORY: solo marca `flag_revisar` (aviso de consistencia para
#      revisión humana), NUNCA cambia el perfil. Es además lo correcto
#      regulatoriamente: un modelo de sentimiento no debe tumbar un cuestionario
#      de idoneidad.
#   2. Se RECALIBRA la frontera "agresivo": el corte del notebook (q_norm 0.33 =
#      score 66.5) etiquetaba como agresivos a perfiles borderline (p. ej.
#      score 74). Se sube a AGGRESSIVE_Q_NORM para exigir respuestas claramente
#      agresivas (protección retail; deliberadamente más estricto que Fase 0).
#
# `classify_profile` (notebook verbatim) se conserva como baseline de referencia.
AGGRESSIVE_Q_NORM = 0.55      # q_norm >= 0.55 (score >= 77.5)  -> agresivo
CONSERVATIVE_Q_NORM = -0.33   # q_norm <  -0.33 (score <  33.5) -> conservador
# Divergencia cuestionario-texto a partir de la cual se marca el aviso (no
# cambia el perfil; solo señala discrepancia para revisión humana).
ADVISORY_FLAG_DIVERGENCE = 0.45


def _base_profile_calibrated(q_norm: float) -> str:
    """Perfil base con las bandas recalibradas (frontera agresivo más estricta)."""
    if q_norm < CONSERVATIVE_Q_NORM:
        return "conservador"
    if q_norm < AGGRESSIVE_Q_NORM:
        return "moderado"
    return "agresivo"


def classify_profile_advisory(
    q_score_normalized: float,
    sentiment_score: float,
    confidence: str,
) -> dict:
    """Perfil decidido por el CUESTIONARIO; el NLP es solo ADVISORY.

    - ``perfil`` = banda recalibrada de ``q_norm`` (:func:`_base_profile_calibrated`).
      El NLP **no** lo cambia.
    - ``divergencia`` = ``q_norm - sentiment_norm`` se calcula solo para el aviso.
    - ``flag_revisar`` = la divergencia supera ``ADVISORY_FLAG_DIVERGENCE``
      (discrepancia notable cuestionario↔texto) → revisión humana.
    - ``escalones_bajados`` = 0 siempre.

    ``confidence`` se mantiene en la firma por compatibilidad de interfaz; no se
    usa para decidir (no es calculable sin la segunda red, ver módulo).
    """
    try:
        sentiment_norm = sentiment_score * 2.0 - 1.0  # [0,1] -> [-1,+1]
        divergence = q_score_normalized - sentiment_norm
        base = _base_profile_calibrated(q_score_normalized)
        return {
            "perfil_base": base,
            "perfil_final": base,            # el NLP no cambia el perfil
            "divergencia": round(float(divergence), 4),
            "flag_revisar": bool(divergence > ADVISORY_FLAG_DIVERGENCE),
            "escalones_bajados": 0,
            "volatility_cap": VOLATILITY_CAP[base],
        }
    except Exception as exc:
        logger.error("classify_profile_advisory error: %s", exc)
        raise


# ===========================================================================
# Token de HuggingFace — lectura segura (NUNCA hardcodeado)
# ===========================================================================
def get_hf_token() -> Optional[str]:
    """Devuelve el token HF desde ``st.secrets["HF_TOKEN"]`` o ``$HF_TOKEN``.

    Orden de prioridad:
        1. ``st.secrets["HF_TOKEN"]`` (Streamlit Cloud / .streamlit/secrets.toml).
        2. Variable de entorno ``HF_TOKEN`` (scripts, tests, CI).

    Returns
    -------
    Optional[str]
        El token, o ``None`` si no está configurado en ningún sitio.
    """
    # Import perezoso: el módulo debe poder importarse fuera de Streamlit.
    try:
        import streamlit as st  # noqa: WPS433 (import local intencionado)

        token = st.secrets.get("HF_TOKEN")  # type: ignore[attr-defined]
        if token:
            return str(token)
    except Exception:  # noqa: BLE001 — fuera de Streamlit o sin secrets.toml
        pass
    return os.environ.get("HF_TOKEN")


# ===========================================================================
# DTO de salida
# ===========================================================================
@dataclass(frozen=True)
class ProfileResult:
    """Resultado del perfilado por inferencia remota."""

    perfil_base: str
    perfil_final: str
    volatility_cap: float
    divergencia: float
    flag_revisar: bool
    escalones_bajados: int
    sentiment_score: float
    confidence: str
    q_norm: float
    q_score_raw: float
    texto_en: str

    def as_dict(self) -> dict:
        """Vista en dict, conveniente para mostrar en la demo."""
        return self.__dict__.copy()


@dataclass(frozen=True)
class QuestionnaireProfileResult:
    """Resultado del perfilado por **prudencia asimétrica** sobre el cuestionario
    MiFID completo (12 cerradas + 3 abiertas).

    Es la salida del modelo canónico de M1 aplicado a la ruta de la demo: el
    cuestionario produce ``q_norm`` y un ``perfil_base``; el NLP (media del
    sentimiento de las 3 respuestas abiertas) solo puede BAJAR el perfil vía
    :func:`classify_profile`. La regla de suelo actúa como puerta previa.
    """

    perfil: str               # perfil final (capitalizado, p. ej. "Conservador")
    sigma_max: float          # volatility cap del perfil final
    perfil_base: str          # perfil derivado solo del cuestionario (cerradas)
    perfil_final: str         # perfil tras la fusión NLP (minúsculas, interno)
    floor_rule_activa: bool
    q_norm: float
    score_cerradas: float     # score [0,1] de las cerradas (sin B5)
    sentiment_score: float    # media NLP [0,1] de las respuestas abiertas
    confidence: str           # alta / media / baja
    divergencia: float
    escalones_bajados: int
    flag_revisar: bool
    s1: float
    s2: float
    s3: float
    s4: float
    nlp_scores: tuple[float, ...] = ()   # sentiment [0,1] por respuesta abierta

    def as_dict(self) -> dict:
        d = self.__dict__.copy()
        d["nlp_scores"] = list(self.nlp_scores)
        return d


# ===========================================================================
# Perfilador remoto (Rama A vía HuggingFace Inference API)
# ===========================================================================
class RemoteProfiler:
    """Perfilador M1 que delega la inferencia en la HuggingFace Inference API.

    Parameters
    ----------
    token
        Token HF. Si es ``None``, se resuelve con :func:`get_hf_token`.
    translator_model_id, sentiment_model_id
        IDs de los modelos de la Rama A. Por defecto Opus-MT y FinBERT.
    timeout
        Timeout en segundos para las llamadas a la API.

    Raises
    ------
    ValueError
        Si no se encuentra ningún token HF.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        translator_model_id: str = OPUS_MT_ES_EN_MODEL_ID,
        sentiment_model_id: str = FINBERT_MODEL_ID,
        timeout: float = 30.0,
    ) -> None:
        resolved = token if token is not None else get_hf_token()
        if not resolved:
            raise ValueError(
                "No se encontró el token de HuggingFace. Configúralo en "
                "st.secrets['HF_TOKEN'] (.streamlit/secrets.toml) o en la "
                "variable de entorno HF_TOKEN."
            )
        self.translator_model_id = translator_model_id
        self.sentiment_model_id = sentiment_model_id
        self._client = InferenceClient(token=resolved, timeout=timeout)

    # --- Rama A: pasos individuales -------------------------------------
    def translate_es_to_en(self, text_es: str) -> str:
        """Traduce ES→EN vía Opus-MT remoto. Trunca a ``MAX_TEXT_CHARS``."""
        snippet = (text_es or "")[:MAX_TEXT_CHARS]
        try:
            out = self._client.translation(snippet, model=self.translator_model_id)
            return str(getattr(out, "translation_text", snippet))
        except Exception as exc:  # noqa: BLE001
            logger.error("translate_es_to_en error: %s", exc)
            return snippet

    def score_finbert(self, text_en: str) -> tuple[float, float]:
        """FinBERT remoto sobre texto EN.

        Returns
        -------
        tuple[float, float]
            ``(signed_score, top_prob)`` donde ``signed_score`` ∈ [-1, +1] es
            ``signo(label) * prob`` y ``top_prob`` ∈ [0, 1] es la probabilidad
            del label ganador (usada para derivar la confianza de la demo).
        """
        try:
            out = self._client.text_classification(
                text_en, model=self.sentiment_model_id
            )
            top = out[0]  # ordenado por score desc.
            label = str(top["label"]).lower()
            prob = float(top["score"])
            signed = float(_LABEL_MAP_FINBERT.get(label, 0)) * prob
            return signed, prob
        except Exception as exc:  # noqa: BLE001
            logger.error("score_finbert error: %s", exc)
            return 0.0, 0.0

    def nlp_proxy_score_es(self, text_es: str) -> float:
        """Traduce ES→EN y devuelve el score NLP de Plantilla C: 1.0/0.5/0.0.

        Mapea el top-label de FinBERT a {positivo→1.0, neutral→0.5,
        negativo→0.0}, exactamente como el proxy ``p1{3,4,5}_finbert`` del
        dataset de personas sintéticas (ver ``generate_personas.py``). Es el
        valor que consume el bloque B5 de
        :func:`src.m1_mifid_questionnaire.score_mifid`.

        Si el texto está vacío o la API falla, devuelve ``0.5`` (neutral) para
        no sesgar el bloque hacia ningún extremo.
        """
        if not (text_es or "").strip():
            return 0.5
        text_en = self.translate_es_to_en(text_es)
        try:
            out = self._client.text_classification(
                text_en, model=self.sentiment_model_id
            )
            label = str(out[0]["label"]).lower()
        except Exception as exc:  # noqa: BLE001
            logger.error("nlp_proxy_score_es error: %s", exc)
            return 0.5
        return {"positive": 1.0, "neutral": 0.5, "negative": 0.0}.get(label, 0.5)

    @staticmethod
    def _confidence_from_prob(prob: float) -> str:
        """Deriva la confianza de la probabilidad del top-label de FinBERT.

        Sustituye al *agreement* inter-pipeline del notebook (no disponible sin
        Rama B). Usa los mismos cortes que el notebook: 0.80 / 0.60.
        """
        if prob >= 0.80:
            return "alta"
        if prob >= 0.60:
            return "media"
        return "baja"

    # --- Pipeline completo ----------------------------------------------
    def profile_investor(self, texto_libre_es: str, q_score_raw: float) -> ProfileResult:
        """Pipeline demo: traducir → FinBERT → fusión (prudencia asimétrica).

        Parameters
        ----------
        texto_libre_es
            Respuesta abierta del inversor en castellano.
        q_score_raw
            Puntuación del cuestionario MiFID II en [0, 100].

        Raises
        ------
        ValueError
            Si ``q_score_raw`` está fuera de [0, 100].
        """
        if not 0.0 <= q_score_raw <= 100.0:
            raise ValueError(f"q_score_raw fuera de [0,100]: {q_score_raw}")

        q_norm = (q_score_raw - 50.0) / 50.0
        texto_en = self.translate_es_to_en(texto_libre_es)
        signed, top_prob = self.score_finbert(texto_en)
        # Solo Rama A: sentiment_score en [0,1] = (score_a + 1) / 2.
        sentiment_score = (signed + 1.0) / 2.0
        confidence = self._confidence_from_prob(top_prob)

        decision = classify_profile(q_norm, sentiment_score, confidence)

        return ProfileResult(
            perfil_base=decision["perfil_base"],
            perfil_final=decision["perfil_final"],
            volatility_cap=decision["volatility_cap"],
            divergencia=decision["divergencia"],
            flag_revisar=decision["flag_revisar"],
            escalones_bajados=decision["escalones_bajados"],
            sentiment_score=round(sentiment_score, 4),
            confidence=confidence,
            q_norm=round(q_norm, 4),
            q_score_raw=q_score_raw,
            texto_en=texto_en,
        )

    # --- Pipeline Plantilla C (cuestionario MiFID completo) -------------
    def profile_investor_mifid(
        self,
        closed: "Mapping[str, int]",
        textos_abiertos: "Sequence[str]",
    ):
        """Perfilado por el modelo **Plantilla C** (cuestionario MiFID completo).

        Combina las 12 respuestas cerradas (``p1``…``p12``) con el bloque B5
        de análisis de sentimiento: cada texto abierto se puntúa con
        :meth:`nlp_proxy_score_es` (1.0/0.5/0.0) y su media alimenta a
        :func:`src.m1_mifid_questionnaire.score_mifid`.

        Parameters
        ----------
        closed
            Puntos crudos de las 12 preguntas cerradas.
        textos_abiertos
            Respuestas libres P13–P15 en castellano.

        Returns
        -------
        src.m1_mifid_questionnaire.MiFIDResult
        """
        from src.m1_mifid_questionnaire import score_mifid

        nlp_scores = [self.nlp_proxy_score_es(t) for t in textos_abiertos]
        return score_mifid(closed, nlp_scores)

    # --- Pipeline canónico: prudencia asimétrica sobre el cuestionario --------
    def profile_investor_questionnaire(
        self,
        closed: "Mapping[str, int]",
        textos_abiertos: "Sequence[str]",
    ) -> "QuestionnaireProfileResult":
        """Perfilado por **prudencia asimétrica** sobre el cuestionario completo.

        Es el modelo canónico de M1 (el del notebook) aplicado a la demo:

        1. ``q_norm`` se deriva de las 12 cerradas (Plantilla C sin B5,
           renormalizado) → :func:`...closed_score_normalized`.
        2. El sentimiento NLP es la media de ``signo(top)·prob`` de FinBERT
           (mapeado a [0,1], fiel al notebook) sobre las respuestas abiertas NO
           vacías. Si todas están vacías, sentimiento neutral (0.5). La
           ``confidence`` se FIJA a ``"media"`` (``CONFIDENCE_CLOUD_FIXED``): sin
           Rama B no hay *agreement*, por lo que ALTA/BAJA no son alcanzables.
        3. La regla de suelo actúa como puerta previa: si está activa, el perfil
           es Conservador con independencia del score.
        4. En otro caso, :func:`classify_profile_advisory` fija el perfil por las
           bandas recalibradas del cuestionario. El NLP es **advisory**: solo
           marca ``flag_revisar`` ante divergencia notable cuestionario↔texto;
           NUNCA cambia el perfil (FinBERT no mide apetito de riesgo de forma
           fiable, ver módulo).

        Returns
        -------
        QuestionnaireProfileResult
        """
        from src.m1_mifid_questionnaire import (
            VOLATILITY_CAP as _VC,  # capitalizado: {"Conservador": 0.08, ...}
        )
        from src.m1_mifid_questionnaire import (
            closed_score_normalized,
            floor_rule_active,
        )

        cs = closed_score_normalized(closed)

        # Sentimiento sobre respuestas NO vacías: media de signo(top)·prob de
        # FinBERT, mapeado a [0,1]. Es la fórmula del notebook (03_inference.py),
        # no la discretización 1.0/0.5/0.0 del proxy de Plantilla C.
        sents: list[float] = []
        for t in textos_abiertos:
            if (t or "").strip():
                signed, _prob = self.score_finbert(self.translate_es_to_en(t))
                sents.append((signed + 1.0) / 2.0)
        sentiment_score = (sum(sents) / len(sents)) if sents else 0.5
        # Confianza FIJADA: sin Rama B (RoBERTuito) no hay agreement → "media".
        confidence = CONFIDENCE_CLOUD_FIXED

        floor_active = floor_rule_active(closed)
        # El cuestionario decide (bandas recalibradas); el NLP es advisory
        # (solo marca flag_revisar). Ver classify_profile_advisory.
        decision = classify_profile_advisory(cs.q_norm, sentiment_score, confidence)

        if floor_active:
            perfil_final = "conservador"
        else:
            perfil_final = decision["perfil_final"]

        perfil_cap = perfil_final.capitalize()
        return QuestionnaireProfileResult(
            perfil=perfil_cap,
            sigma_max=_VC[perfil_cap],
            perfil_base=decision["perfil_base"],
            perfil_final=perfil_final,
            floor_rule_activa=floor_active,
            q_norm=cs.q_norm,
            score_cerradas=cs.score01,
            sentiment_score=round(float(sentiment_score), 4),
            confidence=confidence,
            divergencia=decision["divergencia"],
            escalones_bajados=decision["escalones_bajados"],
            flag_revisar=decision["flag_revisar"],
            s1=cs.s1,
            s2=cs.s2,
            s3=cs.s3,
            s4=cs.s4,
            nlp_scores=tuple(round(x, 3) for x in sents),
        )
