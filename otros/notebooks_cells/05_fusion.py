# §5.1 — classify_profile
DIVERGENCE_THRESHOLDS: dict[str, dict[str, float]] = {
    "alta":  {"grave": 0.50, "moderado": 0.30, "leve": 0.18},
    "media": {"grave": 0.70, "moderado": 0.45, "leve": 0.25},
    "baja":  {"grave": 0.90, "moderado": 0.70, "leve": 0.50},
}
PROFILE_ORDER = ("agresivo", "moderado", "conservador")
VOLATILITY_CAP = {"conservador": 0.08, "moderado": 0.15, "agresivo": 0.25}


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
