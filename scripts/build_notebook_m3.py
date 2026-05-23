"""Build the M3 notebook programmatically via nbformat."""

from __future__ import annotations

import json
from pathlib import Path

import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []


def md(text: str) -> None:
    cells.append(nbf.v4.new_markdown_cell(text))


def code(src: str) -> None:
    cells.append(nbf.v4.new_code_cell(src))


# ============================================================
# § 0 — Setup y carga de datos
# ============================================================
md(
    "# M3 — Optimización de Carteras\n\n"
    "**Roboadvisor TFM.** Este notebook transforma los inputs históricos del M2 en "
    "tres carteras óptimas — una por perfil de riesgo (conservador, moderado, agresivo) "
    "— aplicando restricciones UCITS y caps de volatilidad. Salida: `weights.parquet` y "
    "`portfolios_summary.json`, consumidos por M4 (backtesting walk-forward).\n\n"
    "## § 0 — Setup y carga de datos"
)

code(
    """from __future__ import annotations

import json
import logging
import pickle
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

NOTEBOOK_DIR = Path.cwd()
PACKAGE_ROOT = NOTEBOOK_DIR.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from m3_portfolio import (  # noqa: E402
    CASH_TICKER,
    EqualWeightOptimizer,
    HRPOptimizer,
    MaxSharpeOptimizer,
    MinVarianceOptimizer,
    Portfolio,
    RISK_FREE_RATE,
    TRADING_DAYS,
    validate_portfolio,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("m3_notebook")

sns.set_theme(style="whitegrid")
plt.rcParams["figure.dpi"] = 110
"""
)

code(
    """PROFILES: dict[str, list[str]] = {
    "conservador": ["IEAG.AS", "EUNH.DE", "IBCI.AS"],
    "moderado":    ["INFR.AS", "IHYG.L", "EXSA.DE"],
    "agresivo":    ["CSPX.L", "EQQQ.DE", "EXI2.DE"],
}

MAX_VOL: dict[str, float] = {
    "conservador": 0.08,
    "moderado":    0.15,
    "agresivo":    0.25,
}

PRIMARY_OPTIMIZER: dict[str, type] = {
    "conservador": MinVarianceOptimizer,
    "moderado":    MaxSharpeOptimizer,
    "agresivo":    HRPOptimizer,
}

# Estrategia alternativa por perfil (segunda candidata).
ALTERNATIVE_OPTIMIZER: dict[str, type] = {
    "conservador": MaxSharpeOptimizer,
    "moderado":    HRPOptimizer,
    "agresivo":    MaxSharpeOptimizer,
}

# Baseline transversal: equal weight.
BASELINE_OPTIMIZER = EqualWeightOptimizer
"""
)

code(
    """ETF_DIR = PACKAGE_ROOT.parent / "ETFs"

returns = pd.read_parquet(ETF_DIR / "returns.parquet")
with open(ETF_DIR / "mu.pkl", "rb") as fh:
    mu = pickle.load(fh)
with open(ETF_DIR / "cov_ledoit_wolf.pkl", "rb") as fh:
    cov = pickle.load(fh)

# Normalise mu/cov to pandas with consistent ticker order.
if not isinstance(mu, pd.Series):
    mu = pd.Series(mu, index=returns.columns)
if not isinstance(cov, pd.DataFrame):
    cov = pd.DataFrame(cov, index=returns.columns, columns=returns.columns)

all_tickers = sorted({t for tks in PROFILES.values() for t in tks})
missing = [t for t in all_tickers if t not in mu.index or t not in cov.index]
assert not missing, f"Tickers ausentes en mu/cov: {missing}"

print(f"returns: {returns.shape}, periodo {returns.index.min().date()} → {returns.index.max().date()}")
print(f"mu: {mu.shape}, cov: {cov.shape}")
"""
)

# ============================================================
# § 1 — Estrategias por perfil
# ============================================================
md(
    "## § 1 — Estrategias por perfil\n\n"
    "Asignación principal y alternativa que se comparan en § 2.\n\n"
    "| Perfil | Vol cap | Optimizador principal | Alternativo | Baseline |\n"
    "|--------|---------|-----------------------|-------------|----------|\n"
    "| Conservador | 8%  | Mínima varianza | Máximo Sharpe | Equal-weight |\n"
    "| Moderado    | 15% | Máximo Sharpe   | HRP            | Equal-weight |\n"
    "| Agresivo    | 25% | HRP             | Máximo Sharpe  | Equal-weight |\n\n"
    "HRP entra en agresivo porque las colas pesadas y la asimetría negativa "
    "documentadas en M2 (kurtosis exceso > 3 en los 9 ETFs) debilitan los "
    "supuestos de normalidad de Markowitz. Cuando la cartera optimizada "
    "excede el `max_vol` del perfil, se mezcla linealmente con cash (rf=2%) "
    "hasta cumplir el cap."
)

# ============================================================
# § 2 — Optimización
# ============================================================
md(
    "## § 2 — Optimización: carteras candidatas\n\n"
    "Por cada perfil generamos 3 candidatas (principal, alternativa, equal-weight)."
)

code(
    """candidates: dict[str, dict[str, Portfolio]] = {}

for profile, tickers in PROFILES.items():
    candidates[profile] = {}
    cap = MAX_VOL[profile]
    for label, OptCls in [
        ("principal", PRIMARY_OPTIMIZER[profile]),
        ("alternativo", ALTERNATIVE_OPTIMIZER[profile]),
        ("baseline", BASELINE_OPTIMIZER),
    ]:
        optimizer = OptCls()
        portfolio = optimizer.optimize(
            mu=mu,
            cov=cov,
            tickers=tickers,
            max_volatility=cap,
            profile=profile,
            risk_free_rate=RISK_FREE_RATE,
        )
        candidates[profile][label] = portfolio
        print(f"[{profile:<11} | {label:<11}] {portfolio}")
"""
)

code(
    """fig, axes = plt.subplots(3, 3, figsize=(13, 10), sharey=True)
labels_order = ["principal", "alternativo", "baseline"]
for i, (profile, tickers) in enumerate(PROFILES.items()):
    for j, label in enumerate(labels_order):
        ax = axes[i, j]
        p = candidates[profile][label]
        keys = list(tickers) + ([CASH_TICKER] if p.cash_weight > 0 else [])
        vals = [p.weights.get(k, 0.0) for k in keys]
        colors = ["#4c72b0" if k != CASH_TICKER else "#bbbbbb" for k in keys]
        ax.bar(keys, vals, color=colors)
        ax.set_title(f"{profile} · {label}\\n{p.optimizer_name}", fontsize=10)
        ax.set_ylim(0, 1.0)
        ax.tick_params(axis="x", labelrotation=45)
fig.suptitle("Pesos de las carteras candidatas", y=1.0, fontsize=13)
fig.tight_layout()
plt.show()
"""
)

# ============================================================
# § 3 — Tabla comparativa
# ============================================================
md(
    "## § 3 — Tabla comparativa\n\n"
    "Métricas ex-ante (μ y covarianza históricos M2). Criterio de selección: "
    "**máximo Sharpe sujeto a `vol_actual ≤ vol_cap × 1.01`**."
)

code(
    """rows = []
for profile, opts in candidates.items():
    cap = MAX_VOL[profile]
    for label, p in opts.items():
        rows.append({
            "perfil": profile,
            "candidata": label,
            "optimizador": p.optimizer_name,
            "ret_esperado_%": p.expected_return * 100,
            "vol_esperada_%": p.expected_volatility * 100,
            "vol_cap_%": cap * 100,
            "sharpe": p.expected_sharpe,
            "HHI": p.herfindahl_index,
            "n_activos_efectivos": p.n_effective_assets,
            "cash_%": p.cash_weight * 100,
            "cumple_vol_cap": p.expected_volatility <= cap * 1.01,
        })
comparison = pd.DataFrame(rows)
comparison.style.format({
    "ret_esperado_%": "{:.2f}",
    "vol_esperada_%": "{:.2f}",
    "vol_cap_%": "{:.2f}",
    "sharpe": "{:.3f}",
    "HHI": "{:.3f}",
    "cash_%": "{:.2f}",
})
"""
)

# ============================================================
# § 4 — Selección final
# ============================================================
md(
    "## § 4 — Selección final\n\n"
    "Para cada perfil, elegimos la candidata con **mayor Sharpe** entre las que "
    "cumplen el vol cap."
)

code(
    """def pick_best(opts: dict[str, Portfolio], cap: float) -> tuple[str, Portfolio]:
    feasible = {l: p for l, p in opts.items() if p.expected_volatility <= cap * 1.01}
    pool = feasible if feasible else opts
    best_label = max(pool, key=lambda l: pool[l].expected_sharpe)
    return best_label, pool[best_label]

selected: dict[str, Portfolio] = {}
selection_log: dict[str, str] = {}
for profile, opts in candidates.items():
    label, portfolio = pick_best(opts, MAX_VOL[profile])
    selected[profile] = portfolio
    selection_log[profile] = label
    print(f"[{profile}] elegida: {label} ({portfolio.optimizer_name}) — sharpe={portfolio.expected_sharpe:.3f}")
"""
)

code(
    """fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
for ax, (profile, p) in zip(axes, selected.items()):
    items = [(k, v) for k, v in p.weights.items() if v > 1e-4]
    items.sort(key=lambda kv: -kv[1])
    labels = [k for k, _ in items]
    sizes = [v for _, v in items]
    colors = ["#bbbbbb" if k == CASH_TICKER else None for k in labels]
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90,
           colors=colors if any(c for c in colors) else None)
    ax.set_title(f"{profile} · {p.optimizer_name}")
fig.suptitle("Pesos de las carteras seleccionadas", fontsize=13)
fig.tight_layout()
plt.show()
"""
)

code(
    """summary_rows = []
for profile, p in selected.items():
    summary_rows.append({
        "perfil": profile,
        "optimizador": p.optimizer_name,
        "ret_%": p.expected_return * 100,
        "vol_%": p.expected_volatility * 100,
        "vol_cap_%": MAX_VOL[profile] * 100,
        "sharpe": p.expected_sharpe,
        "HHI": p.herfindahl_index,
        "n_eff": p.n_effective_assets,
        "cash_%": p.cash_weight * 100,
        "pesos": p.weight_string(),
    })
summary = pd.DataFrame(summary_rows)
summary
"""
)

# ============================================================
# § 5 — Validación
# ============================================================
md(
    "## § 5 — Validación UCITS y volatilidad\n\n"
    "Chequeos: suma de pesos = 1, long-only, vol respeta cap, HHI en rango."
)

code(
    """validation_rows = []
for profile, p in selected.items():
    report = validate_portfolio(p, cov, PROFILES[profile], MAX_VOL[profile])
    validation_rows.append({"perfil": profile, **report,
                            "STATUS": "PASS" if all(report.values()) else "FAIL"})
validation_df = pd.DataFrame(validation_rows)
validation_df
"""
)

# ============================================================
# § 6 — Export para M4
# ============================================================
md(
    "## § 6 — Export para M4\n\n"
    "Persistimos pesos (parquet multi-índice) y resumen (JSON)."
)

code(
    """OUTPUT_DIR = PACKAGE_ROOT / "data" / "m3_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

weights_rows = []
for profile, p in selected.items():
    for ticker, w in p.weights.items():
        weights_rows.append({"profile": profile, "ticker": ticker, "weight": w})
weights_df = pd.DataFrame(weights_rows).set_index(["profile", "ticker"]).sort_index()
weights_path = OUTPUT_DIR / "weights.parquet"
weights_df.to_parquet(weights_path)
print(f"Saved weights → {weights_path}")
weights_df
"""
)

code(
    """summary_dict: dict[str, dict] = {}
for profile, p in selected.items():
    report = validate_portfolio(p, cov, PROFILES[profile], MAX_VOL[profile])
    summary_dict[profile] = {
        "optimizer": p.optimizer_name,
        "selection": selection_log[profile],
        "weights": {k: float(v) for k, v in p.weights.items()},
        "cash_weight": float(p.cash_weight),
        "expected_return": float(p.expected_return),
        "expected_volatility": float(p.expected_volatility),
        "expected_sharpe": float(p.expected_sharpe),
        "herfindahl_index": float(p.herfindahl_index),
        "n_effective_assets": int(p.n_effective_assets),
        "max_volatility": float(MAX_VOL[profile]),
        "validation": report,
    }
summary_path = OUTPUT_DIR / "portfolios_summary.json"
with open(summary_path, "w", encoding="utf-8") as fh:
    json.dump(summary_dict, fh, indent=2, ensure_ascii=False)
print(f"Saved summary → {summary_path}")
"""
)

code(
    """checklist = {
    "weights.parquet existe": weights_path.exists(),
    "portfolios_summary.json existe": summary_path.exists(),
    "3 perfiles seleccionados": len(selected) == 3,
    "Validación PASS en los 3 perfiles": all(
        all(validate_portfolio(p, cov, PROFILES[prof], MAX_VOL[prof]).values())
        for prof, p in selected.items()
    ),
    "Pesos suman 1 ± 1e-6": all(
        abs(sum(p.weights.values()) - 1.0) < 1e-6 for p in selected.values()
    ),
}
for k, v in checklist.items():
    print(f"  [{'PASS' if v else 'FAIL'}] {k}")
"""
)

# ============================================================
# Bloque 9 — Nota sobre validación temporal (anclaje OOS para M4)
# ============================================================
md(
    "## Bloque 9 — Nota sobre validación temporal\n\n"
    "Los pesos generados en este notebook usan **μ y Σ estimados sobre el "
    "histórico completo** (`returns.parquet`, 2010-09 → 2026-05). "
    "Representan la cartera que el roboadvisor recomendaría **hoy** con toda la "
    "información disponible — es el output canónico de M3 para el inversor real.\n\n"
    "La **validación walk-forward** de estos pesos sobre el periodo OOS "
    "2020-2026 se realiza en M4, donde se **regeneran pesos OOS-clean** con μ "
    "y Σ restringidos a 2010-2019. Esto garantiza ausencia de *look-ahead bias* "
    "en la fase de estimación de parámetros y permite comparar:\n\n"
    "- **Cartera ex-ante (M3):** `outputs/m3/weights.parquet` — μ/Σ sobre todo "
    "el histórico, autoridad sobre *\"qué recomendar hoy\"*.\n"
    "- **Cartera OOS-clean (M4):** `outputs/m4/weights_oos_clean.parquet` — "
    "μ/Σ ≤ 2019-12-31, autoridad sobre *\"qué se habría recomendado en 2019 y "
    "cómo se comportó\"*.\n\n"
    "Ambas carteras conviven legítimamente y cumplen funciones disjuntas. La "
    "separación de responsabilidades (M3 = optimización in-sample, M4 = "
    "validación walk-forward) hace el backtest académicamente defendible."
)


nb["cells"] = cells
# Canonical destination after the 2026-05-12 reorg.
out_path = Path(__file__).resolve().parent.parent / "notebooks" / "m3_optimizacion_carteras.ipynb"
nbf.write(nb, out_path)
print(f"Wrote {out_path}")
