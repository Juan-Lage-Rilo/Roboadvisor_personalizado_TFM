# §4.1 — Carga y filtrado del PhraseBank
df_pb = pd.read_csv(PHRASEBANK_PATH)
logger.info("PhraseBank cargado: %d filas, columnas=%s", len(df_pb), list(df_pb.columns))

df_all = df_pb[df_pb["agreement_level"] == "allagree"].reset_index(drop=True).copy()
logger.info("Subconjunto allagree: %d filas", len(df_all))

LABEL_TO_INT = {"negative": -1, "neutral": 0, "positive": +1}
df_all["y_true"] = df_all["label"].map(LABEL_TO_INT)
df_all.head()
