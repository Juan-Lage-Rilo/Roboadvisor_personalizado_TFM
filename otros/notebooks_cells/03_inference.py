# §3.1 — Helpers de scoring
LABEL_MAP_FINBERT = {"positive": +1, "negative": -1, "neutral": 0}
LABEL_MAP_ROBERTUITO = {"POS": +1, "NEG": -1, "NEU": 0}


def _to_signed_score(label: str, score: float, mapping: dict[str, int]) -> float:
    """(label, prob) -> score firmado en [-1, +1]."""
    sign = mapping.get(label, 0)
    return float(sign) * float(score)


def score_finbert(text_en: str, model) -> float:
    """Sentimiento FinBERT sobre texto EN. Returns score in [-1, +1]."""
    try:
        out = model(text_en, truncation=True, max_length=512)
        if isinstance(out, list):
            out = out[0]
        return _to_signed_score(out["label"].lower(), out["score"], LABEL_MAP_FINBERT)
    except Exception as exc:
        logger.error("score_finbert error: %s", exc)
        return 0.0


def score_robertuito(text_es: str, model) -> float:
    """Sentimiento RoBERTuito sobre texto ES nativo. Returns score in [-1, +1]."""
    try:
        out = model(text_es, truncation=True, max_length=128)
        if isinstance(out, list):
            out = out[0]
        return _to_signed_score(out["label"].upper(), out["score"], LABEL_MAP_ROBERTUITO)
    except Exception as exc:
        logger.error("score_robertuito error: %s", exc)
        return 0.0


def translate_es_to_en(text: str, translator) -> str:
    """Traduce ES->EN. Trunca a 512 chars antes para evitar OOM."""
    try:
        snippet = (text or "")[:512]
        out = translator(snippet)
        if isinstance(out, list):
            out = out[0]
        return str(out.get("translation_text", snippet))
    except Exception as exc:
        logger.error("translate_es_to_en error: %s", exc)
        return text or ""


def dual_nlp_score(text_es: str, models: dict) -> dict:
    """Pipeline dual: FinBERT(traducido) + RoBERTuito(nativo) + fusion.

    Returns:
      score_a, score_b      : float en [-1, +1]
      sentiment_score       : media normalizada a [0, 1]
      agreement             : 1 - |score_a - score_b|/2
      confidence            : 'alta' (>=0.80) | 'media' (>=0.60) | 'baja'
    """
    try:
        text_en = translate_es_to_en(text_es, models["translator"])
        score_a = score_finbert(text_en, models["finbert"])
        score_b = score_robertuito(text_es, models["robertuito"])
        mean_signed = (score_a + score_b) / 2.0
        sentiment_score = (mean_signed + 1.0) / 2.0
        agreement = 1.0 - abs(score_a - score_b) / 2.0
        if agreement >= 0.80:
            conf = "alta"
        elif agreement >= 0.60:
            conf = "media"
        else:
            conf = "baja"
        return {
            "score_a": score_a,
            "score_b": score_b,
            "sentiment_score": sentiment_score,
            "agreement": agreement,
            "confidence": conf,
        }
    except Exception as exc:
        logger.error("dual_nlp_score error: %s", exc)
        return {"score_a": 0.0, "score_b": 0.0, "sentiment_score": 0.5,
                "agreement": 1.0, "confidence": "baja"}
