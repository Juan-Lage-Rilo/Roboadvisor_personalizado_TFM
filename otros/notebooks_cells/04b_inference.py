# §4.2 — Inferencia FinBERT (batched)
finbert = models["finbert"]
sentences = df_all["sentence"].tolist()
BATCH = 32

scores: list[float] = []
t0 = time.perf_counter()
for i in tqdm(range(0, len(sentences), BATCH), desc="FinBERT"):
    chunk = sentences[i:i + BATCH]
    try:
        outs = finbert(chunk, truncation=True, max_length=512)
        if isinstance(outs, dict):
            outs = [outs]
        for out in outs:
            scores.append(_to_signed_score(out["label"].lower(), out["score"], LABEL_MAP_FINBERT))
    except Exception as exc:
        logger.error("Batch %d falló: %s", i, exc)
        scores.extend([0.0] * len(chunk))
elapsed = time.perf_counter() - t0
logger.info("Inferencia completada en %.1fs (%.1f frases/s)",
            elapsed, len(sentences) / max(elapsed, 1e-6))

df_all["score"] = scores


def score_to_label(s: float) -> int:
    if s > 0.1:
        return +1
    if s < -0.1:
        return -1
    return 0


df_all["y_pred"] = df_all["score"].apply(score_to_label)
df_all.head()
