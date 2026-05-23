"""
M1 — Investor Profiling Module
==============================
TFM · Roboadvisor personalizado para el inversor retail.

Este módulo implementa el pipeline de perfilado del inversor M1, combinando:

    - Rama A: Cuestionario MiFID II (11 preguntas cerradas).
    - Rama B: NLP dual sobre 3 respuestas abiertas en castellano.
        - Pipeline A: Opus-MT (ES→EN) + FinBERT (estándar académico EN).
        - Pipeline B: RoBERTuito (pysentimiento, nativo ES).
    - Fusión final con reglas de prudencia asimétrica.

El output es el input del módulo M3 (optimización de cartera): un perfil de
riesgo discreto y la restricción de volatilidad anual máxima asociada.

Estado
------
ESQUELETO — Frente 1 de la Fase 2. Los métodos críticos están declarados con
firma completa, docstring y ``raise NotImplementedError`` con etiqueta del
bloqueador. Esto permite congelar el contrato de interfaces antes de tener:

    1. El cuestionario MiFID II final (Fase 1C).
    2. Los 30 inversores sintéticos (Fase 1C).

Referencias
-----------
- Araci, D. (2019). FinBERT: Financial Sentiment Analysis with Pre-trained
  Language Models. arXiv:1908.10063.
- Malo, P., Sinha, A., Korhonen, P., Wallenius, J. & Takala, P. (2014). Good
  Debt or Bad Debt: Detecting Semantic Orientations in Economic Texts.
  JASIST 65(4), 782–796.
- Pérez, J. M. et al. (2021). pysentimiento: A Python Toolkit for Sentiment
  Analysis and SocialNLP tasks. arXiv:2106.09462.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Final, Literal, Optional, Sequence

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
__all__ = [
    # Enums
    "RiskProfile",
    "ConfidenceLevel",
    "MiFIDDimension",
    "FusionAction",
    # DTOs
    "QuestionnaireResponse",
    "FreeTextResponse",
    "UserInput",
    "QuestionnaireScore",
    "SentimentScore",
    "DualNLPResult",
    "M1Output",
    # Sub-pipelines
    "QuestionnaireScorer",
    "SentimentPipeline",
    "PipelineA",
    "PipelineB",
    "NLPDualPipeline",
    "FusionRules",
    # Orchestrator
    "M1Profiler",
    "score_investor_profile",
    # Exceptions
    "M1Error",
    "InvalidQuestionnaireError",
    "InvalidFreeTextError",
    "ModelLoadError",
    "TranslationError",
    "InferenceError",
]

# ---------------------------------------------------------------------------
# Logging — librería-friendly (sin handler por defecto)
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# ===========================================================================
# 1 · Enums
# ===========================================================================
class RiskProfile(str, Enum):
    """Tres perfiles discretos según Fase 0."""

    CONSERVADOR = "conservador"
    MODERADO = "moderado"
    AGRESIVO = "agresivo"


class ConfidenceLevel(str, Enum):
    """Confianza del acuerdo intra-NLP entre Pipeline A y Pipeline B."""

    ALTA = "alta"   # agreement >= 0.80
    MEDIA = "media"  # 0.60 <= agreement < 0.80
    BAJA = "baja"   # agreement < 0.60


class MiFIDDimension(str, Enum):
    """5 dimensiones del cuestionario MiFID II."""

    CONOCIMIENTO_EXPERIENCIA = "conocimiento_experiencia"
    SITUACION_FINANCIERA = "situacion_financiera"
    OBJETIVOS_INVERSION = "objetivos_inversion"
    TOLERANCIA_RIESGO = "tolerancia_riesgo"
    CAPACIDAD_PERDIDA = "capacidad_perdida"


class FusionAction(str, Enum):
    """Acciones posibles de la regla de fusión final."""

    BAJAR_DOS = "bajar_dos_escalones"
    BAJAR_UNO = "bajar_un_escalon"
    MANTENER_CON_FLAG = "mantener_con_flag_revisar"
    MANTENER = "mantener"


# ===========================================================================
# 2 · Constantes contractuales (Fase 0 · NO MODIFICAR sin actualizar la memoria)
# ===========================================================================

#: Pesos por dimensión MiFID II (deben sumar 1.0). Sec. 3.1 del PDF Fase 0.
MIFID_DIMENSION_WEIGHTS: Final[dict[MiFIDDimension, float]] = {
    MiFIDDimension.CONOCIMIENTO_EXPERIENCIA: 0.15,
    MiFIDDimension.SITUACION_FINANCIERA: 0.15,
    MiFIDDimension.OBJETIVOS_INVERSION: 0.20,
    MiFIDDimension.TOLERANCIA_RIESGO: 0.25,
    MiFIDDimension.CAPACIDAD_PERDIDA: 0.25,
}

#: Umbrales del cuestionario [0, 100] → perfil base. Sec. 3.1 del PDF Fase 0.
QUESTIONNAIRE_PROFILE_THRESHOLDS: Final[dict[RiskProfile, tuple[float, float]]] = {
    RiskProfile.CONSERVADOR: (0.0, 40.0),
    RiskProfile.MODERADO: (40.0001, 70.0),
    RiskProfile.AGRESIVO: (70.0001, 100.0),
}

#: Volatilidad anual máxima por perfil. Sec. 3.1 del PDF Fase 0. Consumido por M3.
PROFILE_VOLATILITY_CAP: Final[dict[RiskProfile, float]] = {
    RiskProfile.CONSERVADOR: 0.08,
    RiskProfile.MODERADO: 0.15,
    RiskProfile.AGRESIVO: 0.25,
}

#: Tabla de umbrales de divergencia modulada por confianza NLP. Sec. 3.3 del PDF.
DIVERGENCE_THRESHOLDS: Final[dict[ConfidenceLevel, dict[str, float]]] = {
    ConfidenceLevel.ALTA:  {"grave": 0.50, "moderado": 0.30, "leve": 0.18},
    ConfidenceLevel.MEDIA: {"grave": 0.70, "moderado": 0.45, "leve": 0.25},
    ConfidenceLevel.BAJA:  {"grave": 0.90, "moderado": 0.70, "leve": 0.50},
}

#: Umbrales de confianza sobre el agreement intra-NLP.
CONFIDENCE_HIGH_MIN: Final[float] = 0.80
CONFIDENCE_MEDIUM_MIN: Final[float] = 0.60

#: HuggingFace model IDs (Sec. 4 del PDF Fase 0).
FINBERT_MODEL_ID: Final[str] = "ProsusAI/finbert"
OPUS_MT_ES_EN_MODEL_ID: Final[str] = "Helsinki-NLP/opus-mt-es-en"
ROBERTUITO_MODEL_ID: Final[str] = "pysentimiento/robertuito-sentiment-analysis"

#: Constantes estructurales del cuestionario.
N_CLOSED_QUESTIONS: Final[int] = 11
N_OPEN_QUESTIONS: Final[int] = 3
MAX_TOKENS_FINBERT: Final[int] = 512

#: Orden canónico de perfiles (de más agresivo a más conservador). Usado en
#: la operación de "bajar escalones" de la fusión.
_PROFILE_ORDER: Final[tuple[RiskProfile, ...]] = (
    RiskProfile.AGRESIVO,
    RiskProfile.MODERADO,
    RiskProfile.CONSERVADOR,
)


# ===========================================================================
# 3 · Custom exceptions
# ===========================================================================
class M1Error(Exception):
    """Excepción base del módulo M1."""


class InvalidQuestionnaireError(M1Error, ValueError):
    """El cuestionario no cumple las precondiciones (n preguntas, rango, etc.)."""


class InvalidFreeTextError(M1Error, ValueError):
    """El texto libre no cumple las precondiciones (n respuestas, longitud, etc.)."""


class ModelLoadError(M1Error, RuntimeError):
    """Fallo al cargar un modelo HuggingFace."""


class TranslationError(M1Error, RuntimeError):
    """Fallo en la traducción ES→EN del Pipeline A."""


class InferenceError(M1Error, RuntimeError):
    """Fallo en la inferencia de un modelo de sentimiento."""


# ===========================================================================
# 4 · Data Transfer Objects (DTOs) — inmutables y validados
# ===========================================================================
@dataclass(frozen=True, slots=True)
class QuestionnaireResponse:
    """Las 11 respuestas cerradas del cuestionario MiFID II.

    Cada respuesta es un entero ≥ 1 que codifica la opción elegida por el
    usuario. El mapeo concreto opción → puntuación lo aplica
    :class:`QuestionnaireScorer`, una vez fijado el cuestionario en Fase 1C.

    Parameters
    ----------
    answers
        Tupla de longitud :data:`N_CLOSED_QUESTIONS` con valores ≥ 1.

    Raises
    ------
    InvalidQuestionnaireError
        Si la longitud no es la esperada o algún valor es < 1.
    """

    answers: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.answers) != N_CLOSED_QUESTIONS:
            raise InvalidQuestionnaireError(
                f"Se esperan {N_CLOSED_QUESTIONS} respuestas, "
                f"recibidas {len(self.answers)}."
            )
        if any(a < 1 for a in self.answers):
            raise InvalidQuestionnaireError(
                "Todas las respuestas deben ser enteros >= 1."
            )


@dataclass(frozen=True, slots=True)
class FreeTextResponse:
    """Las 3 respuestas abiertas en castellano del cuestionario M1.

    Parameters
    ----------
    texts
        Tupla de exactamente :data:`N_OPEN_QUESTIONS` cadenas no vacías.

    Raises
    ------
    InvalidFreeTextError
        Si la longitud no es la esperada o alguna cadena está vacía.
    """

    texts: tuple[str, ...]

    def __post_init__(self) -> None:
        if len(self.texts) != N_OPEN_QUESTIONS:
            raise InvalidFreeTextError(
                f"Se esperan {N_OPEN_QUESTIONS} respuestas abiertas, "
                f"recibidas {len(self.texts)}."
            )
        if any(not t or not t.strip() for t in self.texts):
            raise InvalidFreeTextError("Las respuestas abiertas no pueden estar vacías.")


@dataclass(frozen=True, slots=True)
class UserInput:
    """Input completo de un usuario para M1."""

    questionnaire: QuestionnaireResponse
    free_text: FreeTextResponse


@dataclass(frozen=True, slots=True)
class QuestionnaireScore:
    """Resultado del scoring del cuestionario MiFID II.

    Attributes
    ----------
    score
        Puntuación cruda en [0, 100].
    score_norm
        Normalización a [-1, +1] usada en el cálculo de divergencia.
        ``score_norm = (score - 50) / 50``.
    base_profile
        Perfil base derivado únicamente del cuestionario.
    dimension_scores
        Score parcial por dimensión MiFID II, útil para inspección y memoria.
    """

    score: float
    score_norm: float
    base_profile: RiskProfile
    dimension_scores: dict[MiFIDDimension, float]


@dataclass(frozen=True, slots=True)
class SentimentScore:
    """Resultado de un único pipeline NLP (A o B) sobre una frase.

    Attributes
    ----------
    score
        Score escalar en [-1, +1] = ``p_positive - p_negative``.
    p_positive, p_neutral, p_negative
        Probabilidades del clasificador (deben sumar ≈ 1.0).
    """

    score: float
    p_positive: float
    p_neutral: float
    p_negative: float


@dataclass(frozen=True, slots=True)
class DualNLPResult:
    """Fusión intra-NLP de los Pipelines A y B sobre las 3 respuestas.

    Attributes
    ----------
    score_a, score_b
        Score agregado de cada pipeline (media de las 3 respuestas).
    sentiment_score
        Score fusionado en [-1, +1] (media de score_a y score_b).
    agreement
        ``1 - |score_a - score_b| / 2`` ∈ [0, 1].
    confidence
        Discretización del agreement en {ALTA, MEDIA, BAJA}.
    """

    score_a: float
    score_b: float
    sentiment_score: float
    agreement: float
    confidence: ConfidenceLevel


@dataclass(frozen=True, slots=True)
class M1Output:
    """Output canónico del módulo M1, consumido por M3.

    Attributes
    ----------
    base_profile
        Perfil derivado solo del cuestionario.
    final_profile
        Perfil tras aplicar prudencia asimétrica.
    volatility_cap
        Restricción de volatilidad anual para M3, derivada de ``final_profile``.
    divergence
        ``q_norm - sentiment_score``.
    fusion_action
        Acción aplicada por las reglas de fusión.
    nlp_confidence
        Confianza intra-NLP usada para modular umbrales.
    flags
        Marcas cualitativas (p. ej. ``"REVISAR_TEXTO_LIBRE"``).
    questionnaire_score, nlp_result
        Trazabilidad completa del proceso, útil para la memoria y QA.
    """

    base_profile: RiskProfile
    final_profile: RiskProfile
    volatility_cap: float
    divergence: float
    fusion_action: FusionAction
    nlp_confidence: ConfidenceLevel
    flags: tuple[str, ...]
    questionnaire_score: QuestionnaireScore
    nlp_result: DualNLPResult


# ===========================================================================
# 5 · Sub-pipelines
# ===========================================================================
class QuestionnaireScorer:
    """Scorer del cuestionario MiFID II.

    Convierte 11 respuestas cerradas en (a) un score [0, 100] ponderado por
    dimensión, (b) un score normalizado [-1, +1] y (c) un perfil base discreto.

    Parameters
    ----------
    question_to_dimension
        Mapeo `índice_pregunta (0..10) → MiFIDDimension`. Pendiente de
        congelar tras Fase 1C.
    answer_value_table
        Mapeo `índice_pregunta → {opción: puntos_normalizados ∈ [0, 1]}`.
        Igualmente pendiente de Fase 1C.

    Notes
    -----
    Esta clase es la ÚNICA que tiene dependencia dura de Fase 1C: no se puede
    completar hasta que las 11 preguntas y sus opciones estén redactadas.
    """

    def __init__(
        self,
        question_to_dimension: Optional[dict[int, MiFIDDimension]] = None,
        answer_value_table: Optional[dict[int, dict[int, float]]] = None,
    ) -> None:
        self.question_to_dimension = question_to_dimension
        self.answer_value_table = answer_value_table

    def score(self, response: QuestionnaireResponse) -> QuestionnaireScore:
        """Puntúa el cuestionario y devuelve perfil base.

        Algoritmo (cuando se complete):
            1. Para cada respuesta, normalizar a [0, 1] vía ``answer_value_table``.
            2. Promediar dentro de cada dimensión.
            3. Combinar con ``MIFID_DIMENSION_WEIGHTS`` → score ∈ [0, 100].
            4. Mapear a ``RiskProfile`` con ``QUESTIONNAIRE_PROFILE_THRESHOLDS``.
            5. Calcular ``score_norm = (score - 50) / 50``.
        """
        raise NotImplementedError(
            "QuestionnaireScorer.score: pendiente de Fase 1C "
            "(redacción final de las 11 preguntas y tabla de opciones)."
        )

    @staticmethod
    def profile_from_score(score: float) -> RiskProfile:
        """Mapea un score [0, 100] a perfil base usando los umbrales contractuales."""
        if not 0.0 <= score <= 100.0:
            raise InvalidQuestionnaireError(
                f"Score fuera de rango [0, 100]: {score}."
            )
        if score <= 40.0:
            return RiskProfile.CONSERVADOR
        if score <= 70.0:
            return RiskProfile.MODERADO
        return RiskProfile.AGRESIVO

    @staticmethod
    def normalize(score: float) -> float:
        """``score_norm = (score - 50) / 50`` ∈ [-1, +1]."""
        return (score - 50.0) / 50.0


class SentimentPipeline(ABC):
    """Interfaz común para Pipeline A (FinBERT+MT) y Pipeline B (RoBERTuito).

    El contrato es el mismo: ``predict(textos_es) -> tuple[SentimentScore, ...]``.
    Cada implementación gestiona internamente sus particularidades (traducción,
    tokenización, dispositivo).
    """

    @abstractmethod
    def load(self) -> None:
        """Carga modelos en memoria. Idempotente."""

    @abstractmethod
    def predict(self, texts: Sequence[str]) -> tuple[SentimentScore, ...]:
        """Inferencia por lotes sobre textos en castellano."""

    def predict_one(self, text: str) -> SentimentScore:
        """Comodidad: inferencia sobre un único texto."""
        return self.predict([text])[0]


class PipelineA(SentimentPipeline):
    """Opus-MT (ES→EN) + FinBERT (ProsusAI/finbert).

    Pipeline estándar académico para sentimiento financiero en inglés. La
    traducción introduce ruido (Riesgo R1 de Fase 0); por eso se complementa
    con :class:`PipelineB` como control nativo en español.

    Parameters
    ----------
    translator_model_id
        Modelo de traducción. Por defecto ``Helsinki-NLP/opus-mt-es-en``.
    sentiment_model_id
        Modelo de sentimiento. Por defecto ``ProsusAI/finbert``.
    device
        ``"cuda"``, ``"cpu"`` o ``None`` (auto-detect).
    max_length
        Longitud máxima en tokens (FinBERT acepta hasta 512).
    """

    def __init__(
        self,
        translator_model_id: str = OPUS_MT_ES_EN_MODEL_ID,
        sentiment_model_id: str = FINBERT_MODEL_ID,
        device: Optional[str] = None,
        max_length: int = MAX_TOKENS_FINBERT,
    ) -> None:
        self.translator_model_id = translator_model_id
        self.sentiment_model_id = sentiment_model_id
        self.device = device
        self.max_length = max_length
        self._loaded: bool = False
        # Slots para los pipelines/tokenizers, materializados en load().
        self._translator: Optional[object] = None
        self._sentiment: Optional[object] = None

    def load(self) -> None:
        """Descarga (si hace falta) y carga Opus-MT y FinBERT en ``self.device``.

        Raises
        ------
        ModelLoadError
            Si alguno de los modelos no puede cargarse.
        """
        raise NotImplementedError("PipelineA.load: pendiente de implementación.")

    def translate(self, texts: Sequence[str]) -> tuple[str, ...]:
        """Traduce ES→EN. Útil de exponer para depuración y trazabilidad.

        Raises
        ------
        TranslationError
            Si el modelo de traducción falla.
        """
        raise NotImplementedError("PipelineA.translate: pendiente de implementación.")

    def predict(self, texts: Sequence[str]) -> tuple[SentimentScore, ...]:
        """``texts`` (ES) → traducción → FinBERT → SentimentScore por texto.

        Raises
        ------
        InferenceError
            Si la inferencia del clasificador falla.
        """
        raise NotImplementedError("PipelineA.predict: pendiente de implementación.")


class PipelineB(SentimentPipeline):
    """RoBERTuito (pysentimiento, nativo ES).

    Control nativo en español frente a la degradación introducida por la
    traducción automática del Pipeline A. Especialmente relevante para jerga
    coloquial financiera (``"me da palo"``, ``"me raya"``).

    Parameters
    ----------
    model_id
        Modelo de sentimiento. Por defecto
        ``pysentimiento/robertuito-sentiment-analysis``.
    device
        ``"cuda"``, ``"cpu"`` o ``None`` (auto-detect).
    """

    def __init__(
        self,
        model_id: str = ROBERTUITO_MODEL_ID,
        device: Optional[str] = None,
    ) -> None:
        self.model_id = model_id
        self.device = device
        self._loaded: bool = False
        self._analyzer: Optional[object] = None

    def load(self) -> None:
        """Carga el analyzer de pysentimiento.

        Raises
        ------
        ModelLoadError
            Si el modelo no puede cargarse.
        """
        raise NotImplementedError("PipelineB.load: pendiente de implementación.")

    def predict(self, texts: Sequence[str]) -> tuple[SentimentScore, ...]:
        """``texts`` (ES) → RoBERTuito → SentimentScore por texto.

        Notes
        -----
        pysentimiento devuelve etiquetas en clave {POS, NEU, NEG}; aquí se
        re-mapean a (p_positive, p_neutral, p_negative) para uniformizar
        con :class:`PipelineA`.

        Raises
        ------
        InferenceError
            Si la inferencia falla.
        """
        raise NotImplementedError("PipelineB.predict: pendiente de implementación.")


class NLPDualPipeline:
    """Orquesta los Pipelines A y B y calcula la fusión intra-NLP.

    Parameters
    ----------
    pipeline_a, pipeline_b
        Sub-pipelines. Pueden inyectarse mocks en tests unitarios.
    aggregation
        Función de agregación de las 3 respuestas a un escalar por pipeline.
        Por defecto ``"mean"``; ``"median"`` se ofrece como alternativa más
        robusta a outliers (a justificar en la memoria si se elige).
    """

    def __init__(
        self,
        pipeline_a: PipelineA,
        pipeline_b: PipelineB,
        aggregation: Literal["mean", "median"] = "mean",
    ) -> None:
        self.pipeline_a = pipeline_a
        self.pipeline_b = pipeline_b
        self.aggregation: Literal["mean", "median"] = aggregation

    def load(self) -> None:
        """Carga ambos sub-pipelines (lazy-cache si ya estaban cargados)."""
        self.pipeline_a.load()
        self.pipeline_b.load()

    def analyze(self, free_text: FreeTextResponse) -> DualNLPResult:
        """Pipeline completo de la rama B del flujo M1.

        Pasos:
            1. Predicción A y B sobre las 3 respuestas → 3 scores cada una.
            2. Agregación a escalar (``score_a``, ``score_b``).
            3. ``sentiment_score`` = media(score_a, score_b).
            4. ``agreement``      = 1 − |score_a − score_b| / 2.
            5. Discretización a ``ConfidenceLevel``.
        """
        raise NotImplementedError("NLPDualPipeline.analyze: pendiente de implementación.")

    @staticmethod
    def aggregate_scores(scores: Sequence[SentimentScore], how: Literal["mean", "median"]) -> float:
        """Agrega una secuencia de SentimentScore a un escalar en [-1, +1]."""
        raise NotImplementedError(
            "NLPDualPipeline.aggregate_scores: pendiente de implementación."
        )

    @staticmethod
    def compute_agreement(score_a: float, score_b: float) -> float:
        """``agreement = 1 − |score_a − score_b| / 2`` ∈ [0, 1]."""
        return 1.0 - abs(score_a - score_b) / 2.0

    @staticmethod
    def confidence_from_agreement(agreement: float) -> ConfidenceLevel:
        """Discretiza ``agreement`` ∈ [0, 1] en ``ConfidenceLevel``."""
        if agreement >= CONFIDENCE_HIGH_MIN:
            return ConfidenceLevel.ALTA
        if agreement >= CONFIDENCE_MEDIUM_MIN:
            return ConfidenceLevel.MEDIA
        return ConfidenceLevel.BAJA


# ===========================================================================
# 6 · Reglas de fusión final con prudencia asimétrica
# ===========================================================================
class FusionRules:
    """Reglas explícitas de fusión cuestionario ↔ NLP con prudencia asimétrica.

    Codifica el principio del TFM: el NLP **nunca sube** el perfil del usuario;
    solo puede bajarlo si detecta divergencia significativa con el cuestionario.
    Ver Sec. 3.3 del PDF Fase 0 y la infografía ``Pipeline_M1_Infografia.png``.

    Parameters
    ----------
    thresholds
        Tabla de umbrales por confianza NLP. Por defecto la cerrada en Fase 0
        (:data:`DIVERGENCE_THRESHOLDS`). Inyectable para análisis de
        sensibilidad en la memoria.
    """

    def __init__(
        self,
        thresholds: Optional[dict[ConfidenceLevel, dict[str, float]]] = None,
    ) -> None:
        self.thresholds = thresholds if thresholds is not None else DIVERGENCE_THRESHOLDS

    @staticmethod
    def compute_divergence(q_score: float, sentiment_score: float) -> float:
        """``divergence = q_norm − sentiment_score``.

        Positivo: el cuestionario es más agresivo que el texto libre
        (caso que puede activar el ajuste a la baja).
        Negativo: el texto libre es más positivo que el cuestionario
        (la prudencia asimétrica lo ignora).
        """
        q_norm = (q_score - 50.0) / 50.0
        return q_norm - sentiment_score

    def decide(
        self,
        base_profile: RiskProfile,
        divergence: float,
        confidence: ConfidenceLevel,
    ) -> tuple[RiskProfile, FusionAction, tuple[str, ...]]:
        """Aplica las reglas y devuelve ``(perfil_final, acción, flags)``.

        Reglas (en orden de evaluación):
            * ``divergence < 0`` → MANTENER (prudencia asimétrica).
            * ``divergence > umbral_grave``    → BAJAR_DOS (solo si AGRESIVO).
            * ``divergence > umbral_moderado`` → BAJAR_UNO.
            * ``divergence > umbral_leve``     → MANTENER_CON_FLAG.
            * resto                            → MANTENER.
        """
        raise NotImplementedError("FusionRules.decide: pendiente de implementación.")

    @staticmethod
    def downgrade(profile: RiskProfile, steps: int) -> RiskProfile:
        """Baja ``profile`` en ``steps`` escalones, con clamp en CONSERVADOR.

        Examples
        --------
        >>> FusionRules.downgrade(RiskProfile.AGRESIVO, 1)
        <RiskProfile.MODERADO: 'moderado'>
        >>> FusionRules.downgrade(RiskProfile.AGRESIVO, 2)
        <RiskProfile.CONSERVADOR: 'conservador'>
        >>> FusionRules.downgrade(RiskProfile.CONSERVADOR, 5)
        <RiskProfile.CONSERVADOR: 'conservador'>
        """
        if steps < 0:
            raise ValueError("'steps' debe ser >= 0 (prudencia asimétrica).")
        idx = _PROFILE_ORDER.index(profile)
        new_idx = min(idx + steps, len(_PROFILE_ORDER) - 1)
        return _PROFILE_ORDER[new_idx]


# ===========================================================================
# 7 · Orquestador de alto nivel
# ===========================================================================
class M1Profiler:
    """Orquestador end-to-end del módulo M1.

    Encapsula el grafo del pipeline::

        UserInput
            ├── QuestionnaireScorer  → QuestionnaireScore
            └── NLPDualPipeline      → DualNLPResult
                                            │
        FusionRules ────────────────────────┴───────→ M1Output

    Parameters
    ----------
    questionnaire_scorer, nlp_pipeline, fusion_rules
        Dependencias inyectadas (DI). Permite testear cada parte por separado
        usando dobles de prueba.
    """

    def __init__(
        self,
        questionnaire_scorer: QuestionnaireScorer,
        nlp_pipeline: NLPDualPipeline,
        fusion_rules: FusionRules,
    ) -> None:
        self.questionnaire_scorer = questionnaire_scorer
        self.nlp_pipeline = nlp_pipeline
        self.fusion_rules = fusion_rules

    @classmethod
    def default(cls, device: Optional[str] = None) -> "M1Profiler":
        """Factory con dependencias por defecto (modelos pre-entrenados).

        Conveniente para uso en notebooks; en tests usar el constructor
        directo con dobles de prueba.
        """
        return cls(
            questionnaire_scorer=QuestionnaireScorer(),
            nlp_pipeline=NLPDualPipeline(
                pipeline_a=PipelineA(device=device),
                pipeline_b=PipelineB(device=device),
            ),
            fusion_rules=FusionRules(),
        )

    def load(self) -> None:
        """Pre-carga modelos NLP. Útil para warm-up antes de un batch."""
        logger.info("Cargando modelos M1...")
        self.nlp_pipeline.load()
        logger.info("Modelos M1 cargados.")

    def profile(self, user_input: UserInput) -> M1Output:
        """Pipeline completo: ``UserInput`` → ``M1Output``.

        Pasos:
            1. Scorear cuestionario → ``QuestionnaireScore``.
            2. Analizar texto libre con NLP dual → ``DualNLPResult``.
            3. Calcular divergencia.
            4. Aplicar reglas de fusión con prudencia asimétrica.
            5. Mapear perfil final → ``volatility_cap``.
            6. Empaquetar todo en ``M1Output`` con trazabilidad completa.
        """
        raise NotImplementedError("M1Profiler.profile: pendiente de implementación.")


# ===========================================================================
# 8 · Función de conveniencia (la del README)
# ===========================================================================
def score_investor_profile(
    questionnaire_answers: Sequence[int],
    free_text_answers: Sequence[str],
    profiler: Optional[M1Profiler] = None,
) -> M1Output:
    """Helper de alto nivel mostrado en el README.

    Crea un :class:`UserInput`, instancia un :class:`M1Profiler` por defecto si
    no se pasa, y devuelve el :class:`M1Output`.

    Examples
    --------
    >>> answers = [3, 2, 4, 1, 3, 2, 4, 3, 2, 4, 3]
    >>> texts = [
    ...     "Prefiero inversiones seguras.",
    ...     "No me gusta perder capital.",
    ...     "Quiero estabilidad a largo plazo.",
    ... ]
    >>> result = score_investor_profile(answers, texts)  # doctest: +SKIP
    >>> result.final_profile  # doctest: +SKIP
    <RiskProfile.CONSERVADOR: 'conservador'>
    """
    user_input = UserInput(
        questionnaire=QuestionnaireResponse(answers=tuple(questionnaire_answers)),
        free_text=FreeTextResponse(texts=tuple(free_text_answers)),
    )
    profiler = profiler if profiler is not None else M1Profiler.default()
    profiler.load()
    return profiler.profile(user_input)


# ===========================================================================
# 9 · Smoke test mínimo (útil mientras se itera)
# ===========================================================================
if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    # Validación estructural — esto SÍ debe funcionar en el esqueleto.
    assert sum(MIFID_DIMENSION_WEIGHTS.values()) == 1.0, "Pesos MiFID II no suman 1.0"
    assert QuestionnaireScorer.profile_from_score(20.0) is RiskProfile.CONSERVADOR
    assert QuestionnaireScorer.profile_from_score(50.0) is RiskProfile.MODERADO
    assert QuestionnaireScorer.profile_from_score(85.0) is RiskProfile.AGRESIVO
    assert FusionRules.downgrade(RiskProfile.AGRESIVO, 1) is RiskProfile.MODERADO
    assert FusionRules.downgrade(RiskProfile.AGRESIVO, 2) is RiskProfile.CONSERVADOR
    assert FusionRules.downgrade(RiskProfile.CONSERVADOR, 5) is RiskProfile.CONSERVADOR
    assert NLPDualPipeline.compute_agreement(0.5, 0.5) == 1.0
    assert NLPDualPipeline.confidence_from_agreement(0.85) is ConfidenceLevel.ALTA
    assert NLPDualPipeline.confidence_from_agreement(0.70) is ConfidenceLevel.MEDIA
    assert NLPDualPipeline.confidence_from_agreement(0.40) is ConfidenceLevel.BAJA

    print("[OK] Esqueleto m1_profiling.py: invariantes contractuales verificadas.")
