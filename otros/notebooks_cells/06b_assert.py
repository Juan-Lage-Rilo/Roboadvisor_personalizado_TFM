# §6.2 — Aserción dura
failures = df_synth[~df_synth["pass"]]
if len(failures) > 0:
    raise AssertionError(
        f"{len(failures)} caso(s) fallaron:\n{failures.to_string(index=False)}"
    )
print("✅ 20/20 casos sintéticos pasan.")
