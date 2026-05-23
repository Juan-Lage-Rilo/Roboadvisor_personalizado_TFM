# §8.2 — Latencia media end-to-end (3 ejecuciones por persona)
times_ms = []
for p in personas:
    for _ in range(3):
        t0 = time.perf_counter()
        _ = profile_investor(p["texto"], p["q_score"], models)
        times_ms.append((time.perf_counter() - t0) * 1000.0)
avg_ms = float(np.mean(times_ms))
print(f"Latencia media end-to-end: {avg_ms:.1f} ms")
