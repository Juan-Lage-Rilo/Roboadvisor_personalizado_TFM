# §8.3 — Tabla Go/No-Go
checklist = [
    {"#": 1, "Criterion": "F1-macro >= 85% sobre allagree",
     "Status": "✅" if f1m >= TARGET_F1 else "❌",
     "Evidence": f"F1-macro = {f1m:.4f}"},
    {"#": 2, "Criterion": "20/20 casos sintéticos pasan",
     "Status": "✅" if n_pass == 20 else "❌",
     "Evidence": f"{n_pass}/20"},
    {"#": 3, "Criterion": "Inferencia < 2s por inversor",
     "Status": "✅" if avg_ms < 2000 else "❌",
     "Evidence": f"avg = {avg_ms:.0f} ms"},
    {"#": 4, "Criterion": "Outputs persistidos en disco",
     "Status": "✅",
     "Evidence": str(OUTPUTS_DIR.relative_to(PROJECT_ROOT))},
]
df_check = pd.DataFrame(checklist)
print(df_check.to_string(index=False))
df_check
