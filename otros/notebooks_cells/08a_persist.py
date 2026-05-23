# §8.1 — Persistir resultados a disco
validation_path = OUTPUTS_DIR / "validation_results.csv"
df_all[["sentence", "label", "y_true", "score", "y_pred"]].rename(
    columns={"label": "true_label_str", "y_true": "true_label",
             "y_pred": "pred_label", "score": "score"}
).to_csv(validation_path, index=False)

synth_path = OUTPUTS_DIR / "synthetic_test_cases.csv"
df_synth.to_csv(synth_path, index=False)

thresholds_path = OUTPUTS_DIR / "profile_thresholds.json"
thresholds_payload = {
    "divergence_thresholds": DIVERGENCE_THRESHOLDS,
    "base_profile_q_norm_cuts": {"conservador": -0.33, "moderado": 0.33},
    "volatility_cap": VOLATILITY_CAP,
    "score_to_label_cuts": {"positive": 0.1, "negative": -0.1},
    "confidence_cuts": {"alta": 0.80, "media": 0.60},
    "seed": SEED,
}
thresholds_path.write_text(json.dumps(thresholds_payload, indent=2, ensure_ascii=False))

for p in (validation_path, synth_path, thresholds_path):
    print(f"  -> {p.relative_to(PROJECT_ROOT)}")
