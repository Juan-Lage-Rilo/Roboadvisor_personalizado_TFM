# §2.1 — Cargador con caché y fallback a mock
_MODEL_CACHE: dict[str, object] = {}
_USE_MOCK: bool = False  # se promueve a True automáticamente si falla la descarga


def _build_mock_pipeline(kind: str):
    """Mock determinista: devuelve scores estables por palabras clave.

    Permite ejecutar el notebook sin red. TODO: replace mock with real model.
    """
    rng = random.Random(SEED)

    def _mock(inputs, **kwargs):
        single = isinstance(inputs, str)
        texts = [inputs] if single else list(inputs)
        out = []
        for t in texts:
            t_lower = (t or "").lower()
            if kind == "translation":
                out.append({"translation_text": t})
                continue
            pos_kw = ("growth", "profit", "increase", "gain", "rose", "strong",
                      "beneficio", "subir", "ganar", "crecimiento", "fuerte",
                      "oportunidad", "maximizar", "rendimiento")
            neg_kw = ("loss", "decline", "decrease", "fell", "drop", "weak",
                      "perdida", "pérdida", "perder", "bajar", "caer", "débil",
                      "miedo", "ansiedad", "panico", "pánico", "retirar")
            score_p = sum(k in t_lower for k in pos_kw)
            score_n = sum(k in t_lower for k in neg_kw)
            if score_p > score_n:
                label, base = "positive", 0.92
            elif score_n > score_p:
                label, base = "negative", 0.92
            else:
                label, base = "neutral", 0.78
            jitter = (rng.random() - 0.5) * 0.04
            if kind == "robertuito":
                label = {"positive": "POS", "negative": "NEG", "neutral": "NEU"}[label]
            out.append({"label": label, "score": max(0.0, min(1.0, base + jitter))})
        return out[0] if single else out

    return _mock


def load_models() -> dict:
    # Carga FinBERT, RoBERTuito y Opus-MT ES->EN. Cachea entre llamadas.
    global _USE_MOCK
    if _MODEL_CACHE:
        return _MODEL_CACHE
    if not _HAS_TORCH:
        raise_exc: Exception = RuntimeError("torch no instalado -> activando mock")
    try:
        if not _HAS_TORCH:
            raise raise_exc
        from transformers import pipeline
        logger.info("Descargando FinBERT (ProsusAI/finbert)...")
        finbert = pipeline("text-classification", model="ProsusAI/finbert", device=DEVICE)
        logger.info("Descargando RoBERTuito (pysentimiento)...")
        robertuito = pipeline(
            "text-classification",
            model="pysentimiento/robertuito-sentiment-analysis",
            device=DEVICE,
        )
        logger.info("Descargando Opus-MT ES->EN...")
        translator = pipeline(
            "translation", model="Helsinki-NLP/opus-mt-es-en", device=DEVICE
        )
        _MODEL_CACHE.update({"finbert": finbert, "robertuito": robertuito,
                             "translator": translator})
        logger.info("Modelos cargados correctamente.")
    except Exception as exc:
        logger.error("Fallo al cargar modelos reales (%s). Activando MOCK.", exc)
        _USE_MOCK = True
        _MODEL_CACHE.update({
            "finbert":    _build_mock_pipeline("finbert"),
            "robertuito": _build_mock_pipeline("robertuito"),
            "translator": _build_mock_pipeline("translation"),
        })
    return _MODEL_CACHE


models = load_models()
print(f"Modo: {'MOCK (sin red)' if _USE_MOCK else 'REAL (HuggingFace)'}")
print(f"Pipelines disponibles: {list(models.keys())}")
