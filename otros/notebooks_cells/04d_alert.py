# §4.4 — Alerta Go/No-Go
TARGET_F1 = 0.85
if f1m < TARGET_F1:
    print(f"⚠️ WARNING: F1-macro={f1m:.3f} < {TARGET_F1} → Fine-tuning may be needed")
else:
    print(f"✅ OK: F1-macro={f1m:.3f} ≥ {TARGET_F1} (zero-shot suficiente)")
