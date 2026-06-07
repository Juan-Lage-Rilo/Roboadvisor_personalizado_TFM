"""Regresión del modelo canónico de M1 (prudencia asimétrica) sobre la ruta de
la demo M5.

Cubre cinco capas:

1. Los **20 casos sintéticos** HD/LD/LC/EC del notebook (§6.1) contra
   ``classify_profile`` — la lógica de fusión portada verbatim (baseline).
2. Los **helpers puros** del puente cuestionario→q_norm y la regla de suelo.
3. Casos **end-to-end** (profiler simulado sin red): Sofía (texto conservador →
   Conservador), floor rule, confianza fija "media".
4. La **fusión mejorada** ``classify_profile_prudence`` (guarda de neutralidad):
   el NLP solo baja con evidencia de prudencia real; 2 escalones solo con señal
   negativa fuerte.
5. El **caso real del PDF** (``caso_erroneo``): agresivo coherente + texto que
   FinBERT lee neutral → ya NO baja a Conservador (regresión del falso descenso).
"""
from __future__ import annotations

import pytest

from m1_mifid_questionnaire import (
    CLOSED_KEYS,
    closed_score_normalized,
    floor_rule_active,
)
from m1_remote_profiling import (
    RemoteProfiler,
    classify_profile,
    classify_profile_prudence,
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
        if "MILD" in t:
            return -0.4, 0.60
        if "AGR" in t:
            return +0.9, 0.95
        return 0.0, 0.50


# Cuestionario agresivo SIN floor rule (p5=3, p6=3) — perfil AG01.
_AGRESIVO = {"p1": 3, "p2": 3, "p3": 3, "p4": 3, "p5": 3, "p6": 3, "p7": 2,
             "p8": 3, "p9": 3, "p10": 3, "p11": 3, "p12": 2}


def test_sofia_agresivo_mas_texto_conservador_baja_a_conservador():
    """El bug original: test agresivo + texto conservador → Conservador."""
    res = _FakeProfiler().profile_investor_questionnaire(
        _AGRESIVO, ["CONS", "CONS", "CONS"]
    )
    assert res.perfil_base == "agresivo"
    assert res.perfil == "Conservador"
    assert res.escalones_bajados == 2
    assert res.floor_rule_activa is False


def test_agresivo_alineado_se_mantiene():
    res = _FakeProfiler().profile_investor_questionnaire(
        _AGRESIVO, ["AGR", "AGR", "AGR"]
    )
    assert res.perfil == "Agresivo"
    assert res.escalones_bajados == 0


def test_floor_rule_domina_pese_a_texto_agresivo():
    """Capacidad económica grave (p5=1) → Conservador aunque el texto sea eufórico."""
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
# 4. Fusión mejorada: classify_profile_prudence (guarda de neutralidad)
# ---------------------------------------------------------------------------
def test_prudence_texto_neutral_no_baja_pero_flag():
    """q agresivo + sentimiento NEUTRAL (0.5) → NO baja; marca flag_revisar."""
    out = classify_profile_prudence(0.93, 0.50, "media")
    assert out["escalones_bajados"] == 0
    assert out["perfil_final"] == "agresivo"
    assert out["flag_revisar"] is True


def test_prudence_texto_positivo_no_baja_ni_flag():
    """q agresivo + sentimiento POSITIVO alineado → se mantiene, sin flag."""
    out = classify_profile_prudence(0.80, 0.85, "media")
    assert out["escalones_bajados"] == 0
    assert out["perfil_final"] == "agresivo"
    assert out["flag_revisar"] is False


def test_prudence_prudente_leve_baja_un_escalon():
    """q agresivo + prudencia LEVE (norm −0.4) → 1 escalón (no 2)."""
    out = classify_profile_prudence(0.92, 0.30, "media")  # sentiment_norm = -0.40
    assert out["escalones_bajados"] == 1
    assert out["perfil_final"] == "moderado"


def test_prudence_prudente_fuerte_baja_dos_escalones():
    """q agresivo + prudencia FUERTE (norm ≤ −0.6) → 2 escalones."""
    out = classify_profile_prudence(0.92, 0.05, "media")  # sentiment_norm = -0.90
    assert out["escalones_bajados"] == 2
    assert out["perfil_final"] == "conservador"


def test_prudence_nunca_sube():
    """Divergencia negativa (texto más agresivo que el test) nunca sube."""
    for q in (-0.99, -0.40, 0.0, 0.34):
        out = classify_profile_prudence(q, 0.99, "alta")
        assert out["escalones_bajados"] == 0
        assert out["perfil_final"] == out["perfil_base"]


# ---------------------------------------------------------------------------
# 5. Caso REAL del PDF (caso_erroneo): inversor CFA agresivo y coherente,
#    textos agresivos que FinBERT lee como NEUTRAL (sentiment 0.50).
#    Antes bajaba 2 escalones a Conservador (falso descenso); ahora se mantiene.
# ---------------------------------------------------------------------------
_CFA_AGRESIVO = {"p1": 3, "p2": 2, "p3": 3, "p4": 3, "p5": 3, "p6": 3, "p7": 2,
                 "p8": 3, "p9": 3, "p10": 3, "p11": 3, "p12": 3}


def test_caso_pdf_cfa_agresivo_texto_neutral_no_baja():
    """Regresión del caso_erroneo.pdf: agresivo coherente + texto neutral FinBERT."""
    res = _FakeProfiler().profile_investor_questionnaire(
        _CFA_AGRESIVO, ["x", "y", "z"]  # neutral en el FakeProfiler
    )
    assert res.perfil_base == "agresivo"
    assert res.sentiment_score == 0.5
    assert res.escalones_bajados == 0
    assert res.perfil == "Agresivo"
    assert res.flag_revisar is True  # divergencia notable, marcada para revisión
