"""Regresión del modelo canónico de M1 (prudencia asimétrica) sobre la ruta de
la demo M5.

Cubre cinco capas:

1. Los **20 casos sintéticos** HD/LD/LC/EC del notebook (§6.1) contra
   ``classify_profile`` — la lógica de fusión portada verbatim (baseline histórico).
2. Los **helpers puros** del puente cuestionario→q_norm y la regla de suelo.
3. Casos **end-to-end** (profiler simulado sin red): el cuestionario decide,
   el NLP es advisory, floor rule, confianza fija "media".
4. El modelo de producción ``classify_profile_advisory``: el perfil sale del
   cuestionario (bandas recalibradas); el NLP NUNCA cambia el perfil, solo marca
   ``flag_revisar`` ante divergencia notable.
5. Los **casos reales** de los PDFs (regresión): caso_1 (CFA agresivo + texto
   neutral → se mantiene Agresivo + aviso) y caso_2 (borderline score 74 →
   Moderado por recalibración de la banda).
"""
from __future__ import annotations

import pytest

from m1_mifid_questionnaire import (
    CLOSED_KEYS,
    closed_score_normalized,
    floor_rule_active,
)
from m1_remote_profiling import (
    AGGRESSIVE_Q_NORM,
    RemoteProfiler,
    classify_profile,
    classify_profile_advisory,
)

# ---------------------------------------------------------------------------
# 1. Los 20 casos canónicos (otros/notebooks_cells/06a_synthetic.py)
# ---------------------------------------------------------------------------
SYNTHETIC_CASES = [
    ("HD1", +0.80, 0.05, "alta", "conservador"),
    ("HD2", +0.70, 0.10, "alta", "conservador"),
    ("HD3", +0.50, 0.55, "alta", "moderado"),
    ("HD4", +0.70, 0.55, "media", "moderado"),
    ("HD5", +0.50, 0.05, "alta", "conservador"),
    ("LD1", -0.80, 0.15, "alta", "conservador"),
    ("LD2", +0.00, 0.50, "alta", "moderado"),
    ("LD3", +0.80, 0.85, "alta", "agresivo"),
    ("LD4", -0.50, 0.30, "alta", "conservador"),
    ("LD5", +0.20, 0.55, "alta", "moderado"),
    ("LC1", +0.50, 0.35, "baja", "moderado"),
    ("LC2", +0.45, 0.30, "baja", "moderado"),
    ("LC3", +0.40, 0.40, "baja", "agresivo"),
    ("LC4", -0.20, 0.50, "baja", "moderado"),
    ("LC5", +0.40, 0.30, "baja", "moderado"),
    ("EC1", +0.00, 0.50, "alta", "moderado"),
    ("EC2", -0.99, 0.99, "baja", "conservador"),
    ("EC3", +0.99, 0.85, "media", "agresivo"),
    ("EC4", -0.40, 0.95, "alta", "conservador"),
    ("EC5", +0.34, 0.65, "alta", "agresivo"),
]


@pytest.mark.parametrize("cid,q_norm,sentiment,conf,expected", SYNTHETIC_CASES)
def test_classify_profile_synthetic(cid, q_norm, sentiment, conf, expected):
    out = classify_profile(q_norm, sentiment, conf)
    assert out["perfil_final"] == expected, f"{cid}: {out}"


def test_prudencia_asimetrica_nunca_sube():
    """Divergencia <= 0 (texto más agresivo que el test) nunca sube el perfil."""
    for q_norm in (-0.99, -0.40, 0.0, 0.34):
        out = classify_profile(q_norm, 0.99, "alta")
        assert out["escalones_bajados"] == 0
        assert out["perfil_final"] == out["perfil_base"]


# ---------------------------------------------------------------------------
# 2. Helpers puros: q_norm renormalizado y regla de suelo
# ---------------------------------------------------------------------------
def _closed(**overrides) -> dict[str, int]:
    base = {k: 0 for k in CLOSED_KEYS}
    base.update(overrides)
    return base


def test_q_norm_extremos():
    todo_cero = _closed()
    assert closed_score_normalized(todo_cero).q_norm == pytest.approx(-1.0)

    todo_max = {"p1": 3, "p2": 4, "p3": 3, "p4": 3, "p5": 3, "p6": 3, "p7": 2,
                "p8": 3, "p9": 3, "p10": 3, "p11": 3, "p12": 3}
    assert closed_score_normalized(todo_max).q_norm == pytest.approx(+1.0)


def test_q_norm_pesos_cerrados_suman_uno():
    cs = closed_score_normalized(_closed(p8=2))
    assert sum(cs.pesos_horizonte_cerrados) == pytest.approx(1.0, abs=1e-6)


def test_floor_rule():
    assert floor_rule_active(_closed(p5=1, p6=3)) is True   # impacto grave
    assert floor_rule_active(_closed(p5=0, p6=3)) is True   # catastrófico
    assert floor_rule_active(_closed(p5=3, p6=0)) is True   # deudas > 50%
    assert floor_rule_active(_closed(p5=2, p6=1)) is False  # ni una ni otra


# ---------------------------------------------------------------------------
# 3. End-to-end con profiler simulado (sin red)
# ---------------------------------------------------------------------------
class _FakeProfiler(RemoteProfiler):
    """RemoteProfiler que no toca la red: el sentimiento se lee del propio texto.

    Convención de los textos de test:
      'CONS' → muy negativo (prudencia fuerte, norm −0.9)
      'MILD' → algo negativo (prudencia leve,   norm −0.4)
      'AGR'  → muy positivo (norm +0.9)
      otro   → neutral (norm 0.0)
    """

    def __init__(self) -> None:  # noqa: D107 — salta la resolución de token HF
        pass

    def translate_es_to_en(self, text_es: str) -> str:  # noqa: D102
        return text_es

    def score_finbert(self, text_en: str) -> tuple[float, float]:  # noqa: D102
        t = (text_en or "").upper()
        if "CONS" in t:
            return -0.9, 0.95
        if "AGR" in t:
            return +0.9, 0.95
        return 0.0, 0.50


# Cuestionario fuertemente agresivo SIN floor rule (q_norm ≈ 0.93).
_AGRESIVO = {"p1": 3, "p2": 3, "p3": 3, "p4": 3, "p5": 3, "p6": 3, "p7": 2,
             "p8": 3, "p9": 3, "p10": 3, "p11": 3, "p12": 2}


def test_agresivo_fuerte_se_mantiene_con_texto_neutral():
    """q_norm alto (0.93) + texto neutral → Agresivo (el cuestionario decide)."""
    res = _FakeProfiler().profile_investor_questionnaire(_AGRESIVO, ["x", "y", "z"])
    assert res.perfil_base == "agresivo"
    assert res.perfil == "Agresivo"
    assert res.escalones_bajados == 0


def test_nlp_es_advisory_no_baja_el_perfil():
    """El NLP NUNCA cambia el perfil: aun con texto 'conservador' sigue Agresivo,
    solo marca flag_revisar para revisión humana (FinBERT no es fiable)."""
    res = _FakeProfiler().profile_investor_questionnaire(
        _AGRESIVO, ["CONS", "CONS", "CONS"]
    )
    assert res.perfil == "Agresivo"          # advisory: el NLP no baja
    assert res.escalones_bajados == 0
    assert res.flag_revisar is True          # pero avisa de la divergencia


def test_agresivo_alineado_no_marca_aviso():
    """Texto positivo alineado con cuestionario agresivo → sin aviso."""
    res = _FakeProfiler().profile_investor_questionnaire(
        _AGRESIVO, ["AGR", "AGR", "AGR"]
    )
    assert res.perfil == "Agresivo"
    assert res.flag_revisar is False


def test_floor_rule_domina():
    """Capacidad económica grave (p5=1) → Conservador (puerta previa)."""
    closed = dict(_AGRESIVO, p5=1)
    res = _FakeProfiler().profile_investor_questionnaire(closed, ["AGR", "AGR", "AGR"])
    assert res.floor_rule_activa is True
    assert res.perfil == "Conservador"


def test_confianza_siempre_media_en_cloud():
    """La variante cloud fija confidence="media" (sin agreement inter-pipeline)."""
    for textos in (["CONS", "CONS", "CONS"], ["AGR", "AGR", "AGR"], ["x", "y", "z"]):
        res = _FakeProfiler().profile_investor_questionnaire(_AGRESIVO, textos)
        assert res.confidence == "media"


# ---------------------------------------------------------------------------
# 4. classify_profile_advisory: el cuestionario decide, el NLP es advisory
# ---------------------------------------------------------------------------
def test_advisory_nunca_cambia_el_perfil():
    """Pase lo que pase con el sentimiento, perfil_final == perfil_base."""
    for q in (-0.99, -0.40, 0.0, 0.34, 0.48, 0.93):
        for sent in (0.0, 0.5, 1.0):
            out = classify_profile_advisory(q, sent, "media")
            assert out["escalones_bajados"] == 0
            assert out["perfil_final"] == out["perfil_base"]


def test_advisory_banda_recalibrada():
    """Frontera 'agresivo' recalibrada: score 74 (q_norm 0.48) → Moderado."""
    assert classify_profile_advisory(0.48, 0.5, "media")["perfil_base"] == "moderado"
    assert classify_profile_advisory(0.93, 0.5, "media")["perfil_base"] == "agresivo"
    # Justo en la frontera AGGRESSIVE_Q_NORM.
    assert classify_profile_advisory(AGGRESSIVE_Q_NORM, 0.5, "media")["perfil_base"] == "agresivo"
    assert classify_profile_advisory(AGGRESSIVE_Q_NORM - 0.01, 0.5, "media")["perfil_base"] == "moderado"


def test_advisory_flag_por_divergencia():
    """El aviso salta con divergencia notable (texto no confirma el cuestionario)."""
    assert classify_profile_advisory(0.93, 0.5, "media")["flag_revisar"] is True   # div 0.93
    assert classify_profile_advisory(0.93, 0.95, "media")["flag_revisar"] is False  # alineado


# ---------------------------------------------------------------------------
# 5. Casos REALES de los PDFs (regresión).
# ---------------------------------------------------------------------------
# caso_1 (caso_erroneo): CFA agresivo, textos que FinBERT lee neutral.
# Antes bajaba 2 escalones a Conservador; ahora se mantiene Agresivo + aviso.
_CFA_AGRESIVO = {"p1": 3, "p2": 2, "p3": 3, "p4": 3, "p5": 3, "p6": 3, "p7": 2,
                 "p8": 3, "p9": 3, "p10": 3, "p11": 3, "p12": 3}
# caso_2: q_norm ≈ 0.48 (score 74), borderline. Antes Agresivo; ahora Moderado.
_CASO2 = {"p1": 3, "p2": 2, "p3": 3, "p4": 3, "p5": 3, "p6": 2, "p7": 2,
          "p8": 3, "p9": 2, "p10": 2, "p11": 2, "p12": 0}


def test_caso1_cfa_agresivo_texto_neutral_se_mantiene():
    """caso_erroneo.pdf: agresivo fuerte + texto neutral → Agresivo + aviso."""
    res = _FakeProfiler().profile_investor_questionnaire(_CFA_AGRESIVO, ["x", "y", "z"])
    assert res.perfil == "Agresivo"
    assert res.escalones_bajados == 0
    assert res.flag_revisar is True


def test_caso2_borderline_baja_a_moderado_por_banda():
    """caso_2.pdf: score 74 (q_norm 0.48) borderline → Moderado por recalibración."""
    res = _FakeProfiler().profile_investor_questionnaire(_CASO2, ["x", "y", "z"])
    assert round(res.q_norm, 2) == 0.48
    assert res.floor_rule_activa is False
    assert res.perfil == "Moderado"
