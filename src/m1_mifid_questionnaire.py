"""
M1 — Cuestionario MiFID II (Plantilla C) · scoring puro
=======================================================
TFM · Roboadvisor personalizado para el inversor retail.

Este módulo implementa el modelo de perfilado **Plantilla C** documentado en
``docs/mifid/guia_plantilla_mifid_test.md`` y validado al 100 % sobre las 30
personas sintéticas (ver ``scripts/generate_personas.py`` y
``docs/mifid/dataset_documentacion.md``).

A diferencia de :func:`src.m1_remote_profiling.classify_profile` (fusión por
*prudencia asimétrica* portada del notebook), Plantilla C combina **cinco
bloques ponderados** con **pesos adaptativos según el horizonte temporal**
(P8) y una **regla de suelo** (floor rule) de cumplimiento normativo:

    Score_final = w₁(h)·S₁ + w₂(h)·S₂ + w₃(h)·S₃ + w₄·S₄ + w₅(h)·S₅

El bloque B5 (``S5``) es el análisis de sentimiento NLP: media de los scores
de las tres respuestas abiertas (P13–P15), cada una mapeada a {0.0 negativo,
0.5 neutral, 1.0 positivo}.

Este módulo NO depende de Streamlit ni de la red: solo define el catálogo del
cuestionario y la aritmética del scoring. La inferencia NLP la aporta
:class:`src.m1_remote_profiling.RemoteProfiler`.

Referencias
-----------
- Reglamento Delegado (UE) 2017/565, Arts. 54–55; Directiva 2014/65/UE (MiFID II).
- López de Prado, M. (2016). Bodie, Merton & Samuelson (1992) — lifecycle investing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

__all__ = [
    "WEIGHTS_BY_HORIZON",
    "MAX_BLOCK",
    "PROFILE_BANDS",
    "VOLATILITY_CAP",
    "QUESTIONNAIRE",
    "CLOSED_KEYS",
    "OPEN_QUESTIONS",
    "MiFIDResult",
    "score_mifid",
    "ClosedScore",
    "closed_score_normalized",
    "floor_rule_active",
]

# ===========================================================================
# Constantes del modelo — PORTADAS de scripts/generate_personas.py.
# NO MODIFICAR sin re-validar contra las 30 personas sintéticas.
# ===========================================================================
# Pesos (B1, B2, B3, B4, B5) según el índice de horizonte temporal (P8).
WEIGHTS_BY_HORIZON: dict[int, tuple[float, float, float, float, float]] = {
    0: (0.15, 0.45, 0.25, 0.05, 0.10),   # < 1 año
    1: (0.20, 0.30, 0.35, 0.05, 0.10),   # 1–3 años
    2: (0.20, 0.20, 0.40, 0.05, 0.15),   # 3–7 años
    3: (0.15, 0.15, 0.45, 0.05, 0.20),   # > 7 años
}

# Máximos teóricos por bloque (denominador de normalización a [0,1]).
MAX_BLOCK: dict[str, int] = {
    "B1": 10,   # P1(3) + P2(4) + P3(3)
    "B2": 11,   # P4(3) + P5(3) + P6(3) + P7(2)
    "B3": 12,   # P8(3) + P9(3) + P10(3) + P11(3)
    "B4": 3,    # P12(3)
}

# Mapeo score_final → (perfil, σ máx anual M3). Bandas de la guía § 7.
PROFILE_BANDS: tuple[tuple[float, str, float], ...] = (
    (0.35, "Conservador", 0.08),
    (0.65, "Moderado", 0.15),
    (1.01, "Agresivo", 0.25),
)
VOLATILITY_CAP: dict[str, float] = {
    "Conservador": 0.08,
    "Moderado": 0.15,
    "Agresivo": 0.25,
}


# ===========================================================================
# Catálogo del cuestionario (12 cerradas + 3 abiertas)
# ===========================================================================
@dataclass(frozen=True)
class Question:
    """Una pregunta cerrada: clave, enunciado, ayuda y opciones (label→puntos)."""

    key: str
    block: str
    text: str
    options: tuple[tuple[str, int], ...]
    help: str = ""

    @property
    def labels(self) -> list[str]:
        return [lab for lab, _ in self.options]

    def points_for(self, label: str) -> int:
        for lab, pts in self.options:
            if lab == label:
                return pts
        raise KeyError(f"Opción no válida para {self.key}: {label!r}")


@dataclass(frozen=True)
class OpenQuestion:
    """Una pregunta abierta (alimenta el bloque B5 vía FinBERT)."""

    key: str
    text: str
    placeholder: str = ""


# --- Bloques cerrados -------------------------------------------------------
QUESTIONNAIRE: dict[str, dict] = {
    "B1": {
        "titulo": "Conocimientos y experiencia",
        "norma": "Reglamento Delegado (UE) 2017/565, Art. 55",
        "questions": [
            Question(
                "p1", "B1", "Nivel de formación financiera",
                (
                    ("Sin formación financiera", 0),
                    ("Formación básica / autodidacta", 1),
                    ("Formación media (cursos, grado afín)", 2),
                    ("Formación avanzada (posgrado, CFA o similar)", 3),
                ),
            ),
            Question(
                "p2", "B1", "Productos con los que ha operado en los últimos 3 años",
                (
                    ("Ninguno", 0),
                    ("Depósitos / cuentas remuneradas", 1),
                    ("Fondos de inversión / ETFs", 2),
                    ("Acciones y bonos directamente", 3),
                    ("Derivados, opciones o apalancamiento", 4),
                ),
            ),
            Question(
                "p3", "B1", "Frecuencia operativa habitual",
                (
                    ("Nunca he operado", 0),
                    ("Operaciones puntuales (alguna al año)", 1),
                    ("Operativa ocasional (varias al año)", 2),
                    ("Operativa frecuente (mensual o más)", 3),
                ),
            ),
        ],
    },
    "B2": {
        "titulo": "Situación financiera",
        "norma": "Reglamento Delegado (UE) 2017/565, Art. 54.3",
        "questions": [
            Question(
                "p4", "B2", "Capacidad de ahorro mensual",
                (
                    ("No consigo ahorrar", 0),
                    ("Menos del 15% de mis ingresos", 1),
                    ("Entre el 15% y el 30%", 2),
                    ("Más del 30%", 3),
                ),
            ),
            Question(
                "p5", "B2", "Impacto de perder el capital invertido",
                (
                    ("Catastrófico: comprometería mi nivel de vida", 0),
                    ("Grave: lo notaría seriamente", 1),
                    ("Moderado: lo asumiría con esfuerzo", 2),
                    ("Asumible: no afectaría a mi día a día", 3),
                ),
                help="Activa la regla de suelo si es 'Grave' o 'Catastrófico'.",
            ),
            Question(
                "p6", "B2", "Nivel de endeudamiento",
                (
                    ("Mis deudas superan el 50% de mis ingresos", 0),
                    ("Deudas entre el 30% y el 50%", 1),
                    ("Deudas por debajo del 30%", 2),
                    ("Sin deudas relevantes", 3),
                ),
                help="Activa la regla de suelo si las deudas superan el 50%.",
            ),
            Question(
                "p7", "B2", "Fondo de emergencia",
                (
                    ("No tengo fondo de emergencia", 0),
                    ("Cubro entre 1 y 3 meses de gastos", 1),
                    ("Cubro más de 3 meses de gastos", 2),
                ),
            ),
        ],
    },
    "B3": {
        "titulo": "Objetivos de inversión",
        "norma": "Reglamento Delegado (UE) 2017/565, Art. 54.2",
        "questions": [
            Question(
                "p8", "B3", "Horizonte temporal de la inversión",
                (
                    ("Menos de 1 año", 0),
                    ("Entre 1 y 3 años", 1),
                    ("Entre 3 y 7 años", 2),
                    ("Más de 7 años", 3),
                ),
                help="Metaparámetro: determina los pesos de todos los bloques.",
            ),
            Question(
                "p9", "B3", "Finalidad principal de la inversión",
                (
                    ("Preservar el capital", 0),
                    ("Obtener rentas estables", 1),
                    ("Crecimiento moderado del patrimonio", 2),
                    ("Maximizar la rentabilidad a largo plazo", 3),
                ),
            ),
            Question(
                "p10", "B3", "Reacción ante una caída del 20% de su cartera",
                (
                    ("Vendería todo para evitar más pérdidas", 0),
                    ("Vendería una parte", 1),
                    ("Mantendría la inversión", 2),
                    ("Aprovecharía para comprar más", 3),
                ),
            ),
            Question(
                "p11", "B3", "Pérdida máxima anual que aceptaría",
                (
                    ("No aceptaría ninguna pérdida", 0),
                    ("Hasta un 5%", 1),
                    ("Hasta un 15%", 2),
                    ("Más del 15%", 3),
                ),
            ),
        ],
    },
    "B4": {
        "titulo": "Preferencias de sostenibilidad (ESG)",
        "norma": "Reglamento Delegado (UE) 2021/1253 (Green MiFID)",
        "questions": [
            Question(
                "p12", "B4", "Preferencias de sostenibilidad",
                (
                    ("No tengo preferencias de sostenibilidad", 0),
                    ("Me interesa, pero no es determinante", 1),
                    ("Prefiero opciones sostenibles cuando sea posible", 2),
                    ("Es un requisito obligatorio", 3),
                ),
            ),
        ],
    },
}

# Preguntas abiertas (bloque B5 — análisis de sentimiento NLP).
OPEN_QUESTIONS: tuple[OpenQuestion, ...] = (
    OpenQuestion(
        "p13",
        "¿Cómo describiría su actitud general hacia el riesgo al invertir?",
        placeholder="Ej.: Prefiero rentabilidades modestas pero seguras...",
    ),
    OpenQuestion(
        "p14",
        "Imagine que su cartera cae un 30% a los seis meses. ¿Cómo reaccionaría?",
        placeholder="Ej.: Mantendría la inversión y esperaría a la recuperación...",
    ),
    OpenQuestion(
        "p15",
        "¿Cómo lleva la volatilidad del mercado en su día a día (sueño, atención a la cartera)?",
        placeholder="Ej.: No miro la cartera a diario, no me quita el sueño...",
    ),
)

# Orden canónico de las 12 claves cerradas.
CLOSED_KEYS: tuple[str, ...] = tuple(
    q.key for block in QUESTIONNAIRE.values() for q in block["questions"]
)


# ===========================================================================
# DTO de salida
# ===========================================================================
@dataclass(frozen=True)
class MiFIDResult:
    """Resultado del perfilado por Plantilla C."""

    perfil: str
    sigma_max: float
    score_final: float
    floor_rule_activa: bool
    s1: float
    s2: float
    s3: float
    s4: float
    s5: float
    pesos_horizonte: tuple[float, float, float, float, float]
    nlp_scores: tuple[float, ...] = field(default=())

    def as_dict(self) -> dict:
        return {
            "perfil": self.perfil,
            "sigma_max": self.sigma_max,
            "score_final": self.score_final,
            "floor_rule_activa": self.floor_rule_activa,
            "S1_conocimientos": self.s1,
            "S2_situacion_fin": self.s2,
            "S3_objetivos": self.s3,
            "S4_esg": self.s4,
            "S5_nlp": self.s5,
            "pesos_horizonte": list(self.pesos_horizonte),
            "nlp_scores": list(self.nlp_scores),
        }


# ===========================================================================
# Scoring — réplica exacta de calcular_scores() de generate_personas.py
# ===========================================================================
def score_mifid(
    closed: Mapping[str, int],
    nlp_scores: Sequence[float],
) -> MiFIDResult:
    """Calcula el perfil aplicando el modelo Plantilla C.

    Parameters
    ----------
    closed
        Puntos crudos de las 12 preguntas cerradas, claves ``p1``…``p12``.
    nlp_scores
        Lista de scores NLP en [0,1] (uno por respuesta abierta P13–P15).
        Su media es el bloque B5. Si está vacía, B5 = 0.0.

    Returns
    -------
    MiFIDResult
    """
    missing = [k for k in CLOSED_KEYS if k not in closed]
    if missing:
        raise ValueError(f"Faltan respuestas cerradas: {missing}")

    p = {k: int(closed[k]) for k in CLOSED_KEYS}

    s1 = (p["p1"] + p["p2"] + p["p3"]) / MAX_BLOCK["B1"]
    s2 = (p["p4"] + p["p5"] + p["p6"] + p["p7"]) / MAX_BLOCK["B2"]
    s3 = (p["p8"] + p["p9"] + p["p10"] + p["p11"]) / MAX_BLOCK["B3"]
    s4 = p["p12"] / MAX_BLOCK["B4"]
    s5 = (sum(nlp_scores) / len(nlp_scores)) if nlp_scores else 0.0

    w = WEIGHTS_BY_HORIZON[p["p8"]]
    score_final = w[0] * s1 + w[1] * s2 + w[2] * s3 + w[3] * s4 + w[4] * s5

    # Regla de suelo (floor rule): salvaguarda normativa de capacidad económica.
    floor_active = (p["p5"] <= 1) or (p["p6"] == 0)

    if floor_active:
        perfil, sigma = "Conservador", VOLATILITY_CAP["Conservador"]
    else:
        perfil, sigma = "Agresivo", VOLATILITY_CAP["Agresivo"]
        for techo, nombre, vol in PROFILE_BANDS:
            if score_final <= techo:
                perfil, sigma = nombre, vol
                break

    return MiFIDResult(
        perfil=perfil,
        sigma_max=sigma,
        score_final=round(float(score_final), 3),
        floor_rule_activa=floor_active,
        s1=round(s1, 3),
        s2=round(s2, 3),
        s3=round(s3, 3),
        s4=round(s4, 3),
        s5=round(s5, 3),
        pesos_horizonte=w,
        nlp_scores=tuple(round(float(x), 3) for x in nlp_scores),
    )


# ===========================================================================
# Puente cuestionario → prudencia asimétrica (modelo canónico del notebook M1)
# ===========================================================================
# El modelo canónico de M1 (``src.m1_remote_profiling.classify_profile``) fusiona
# un score de cuestionario ``q_norm`` ∈ [-1,+1] con el sentimiento NLP por
# *prudencia asimétrica* (el NLP solo puede BAJAR el perfil). El notebook usaba
# un slider [0,100] como ``q_score``; aquí ese valor se deriva del cuestionario
# MiFID completo (12 cerradas), reutilizando los pesos adaptativos por horizonte
# de Plantilla C **excluyendo el bloque B5** (que entra después como el NLP).
@dataclass(frozen=True)
class ClosedScore:
    """Score de los bloques cerrados (B1–B4), sin el bloque NLP B5.

    Attributes
    ----------
    s1, s2, s3, s4
        Scores normalizados [0,1] de cada bloque cerrado.
    score01
        Score agregado [0,1] con pesos adaptativos por horizonte
        renormalizados a suma 1 (sin B5).
    q_norm
        ``score01`` remapeado a [-1,+1] = entrada ``q_score_normalized`` de
        :func:`src.m1_remote_profiling.classify_profile`.
    pesos_horizonte_cerrados
        Los 4 pesos (w1..w4) renormalizados que producen ``score01``.
    """

    s1: float
    s2: float
    s3: float
    s4: float
    score01: float
    q_norm: float
    pesos_horizonte_cerrados: tuple[float, float, float, float]


def _closed_points(closed: Mapping[str, int]) -> dict[str, int]:
    missing = [k for k in CLOSED_KEYS if k not in closed]
    if missing:
        raise ValueError(f"Faltan respuestas cerradas: {missing}")
    return {k: int(closed[k]) for k in CLOSED_KEYS}


def closed_score_normalized(closed: Mapping[str, int]) -> ClosedScore:
    """Score de las 12 cerradas → ``q_norm`` ∈ [-1,+1] para prudencia asimétrica.

    Aplica los pesos adaptativos por horizonte (P8) de Plantilla C a B1–B4,
    **excluyendo B5**, y renormaliza los cuatro pesos restantes a suma 1 para que
    ``score01`` permanezca en [0,1]. Luego mapea a [-1,+1].
    """
    p = _closed_points(closed)

    s1 = (p["p1"] + p["p2"] + p["p3"]) / MAX_BLOCK["B1"]
    s2 = (p["p4"] + p["p5"] + p["p6"] + p["p7"]) / MAX_BLOCK["B2"]
    s3 = (p["p8"] + p["p9"] + p["p10"] + p["p11"]) / MAX_BLOCK["B3"]
    s4 = p["p12"] / MAX_BLOCK["B4"]

    w = WEIGHTS_BY_HORIZON[p["p8"]]
    w_closed = w[:4]
    denom = sum(w_closed)  # = 1 - w5; siempre > 0
    w_renorm = tuple(wi / denom for wi in w_closed)

    score01 = w_renorm[0] * s1 + w_renorm[1] * s2 + w_renorm[2] * s3 + w_renorm[3] * s4
    q_norm = score01 * 2.0 - 1.0

    return ClosedScore(
        s1=round(s1, 3),
        s2=round(s2, 3),
        s3=round(s3, 3),
        s4=round(s4, 3),
        score01=round(float(score01), 4),
        q_norm=round(float(q_norm), 4),
        pesos_horizonte_cerrados=tuple(round(x, 4) for x in w_renorm),  # type: ignore[arg-type]
    )


def floor_rule_active(closed: Mapping[str, int]) -> bool:
    """Regla de suelo (salvaguarda normativa de capacidad económica).

    Se activa si el impacto de perder el capital es grave/catastrófico
    (``p5`` ≤ 1) o si las deudas superan el 50 % de los ingresos (``p6`` == 0).
    Es independiente del apetito de riesgo y solo puede forzar el perfil a la
    baja (Conservador), por lo que es compatible con la prudencia asimétrica.
    """
    p = _closed_points(closed)
    return (p["p5"] <= 1) or (p["p6"] == 0)
