# §4.3 — Métricas + matriz de confusión
y_true = df_all["y_true"].to_numpy()
y_pred = df_all["y_pred"].to_numpy()

acc = accuracy_score(y_true, y_pred)
f1m = f1_score(y_true, y_pred, average="macro", labels=[-1, 0, 1])
cm = confusion_matrix(y_true, y_pred, labels=[-1, 0, 1])

metrics_df = pd.DataFrame(
    {"métrica": ["Accuracy", "F1-macro", "n"],
     "valor":   [f"{acc:.4f}", f"{f1m:.4f}", f"{len(df_all)}"]}
)
print(metrics_df.to_string(index=False))

fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="magma",
            xticklabels=["neg", "neu", "pos"],
            yticklabels=["neg", "neu", "pos"], ax=ax, cbar=True)
ax.set_xlabel("Predicho")
ax.set_ylabel("Real")
ax.set_title(f"FinBERT zero-shot · allagree · F1-macro={f1m:.3f}")
plt.tight_layout()
fig.savefig(OUTPUTS_DIR / "finbert_confusion_matrix.png", dpi=140, facecolor=fig.get_facecolor())
plt.show()
