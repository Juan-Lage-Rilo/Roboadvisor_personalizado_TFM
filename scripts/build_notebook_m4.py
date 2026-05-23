"""Build notebooks/m4_backtesting.ipynb programmatically.

Ejecuta el pipeline end-to-end y empaqueta cada bloque como una celda
de Jupyter (markdown + code). Si el script termina sin errores y los
artefactos esperados aparecen en outputs/m4/, el notebook generado es
coherente con el contexto del módulo (ver docs/context_m4.md).
"""
from __future__ import annotations

import sys
from pathlib import Path

import nbformat as nbf

PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "m4_backtesting.ipynb"


def _md(text: str) -> nbf.NotebookNode:
    return nbf.v4.new_markdown_cell(text)


def _code(src: str) -> nbf.NotebookNode:
    return nbf.v4.new_code_cell(src)


def build() -> None:
    nb = nbf.v4.new_notebook()
    cells: list[nbf.NotebookNode] = []

    cells.append(_md(
        "# M4 — Backtesting y Validación walk-forward\n"
        "\n"
        "**Roboadvisor TFM.** Este notebook valida las tres carteras optimizadas en M3 "
        "sobre el periodo OOS 2020-01-02 → 2026-04-30, comparándolas contra SPY y la "
        "cartera 60/40 sintética (`0.6·CSPX.L + 0.4·IEAG.AS`). Los pesos se regeneran "
        "OOS-clean con μ/Σ ≤ 2019-12-31 para eliminar look-ahead bias.\n"
        "\n"
        "Criterio Go/No-Go: `Sharpe(moderado) ≥ Sharpe(60_40)`.\n"
        "\n"
        "## Bloque 0 — Setup"
    ))
    cells.append(_code(
        "# Bootstrap de paths (igual que M3)\n"
        "import sys\n"
        "from pathlib import Path as _P\n"
        "\n"
        "_repo = _P.cwd().resolve()\n"
        "while _repo != _repo.parent and not (_repo / \"src\" / \"roboadvisor_paths.py\").exists():\n"
        "    _repo = _repo.parent\n"
        "_src = _repo / \"src\"\n"
        "if str(_src) not in sys.path:\n"
        "    sys.path.insert(0, str(_src))\n"
        "\n"
        "import roboadvisor_paths as PATHS  # noqa: E402\n"
        "PATHS.ensure_dirs()\n"
        "M4_OUT = PATHS.OUTPUTS_DIR / \"m4\"\n"
        "M4_OUT.mkdir(parents=True, exist_ok=True)"
    ))
    cells.append(_code(
        "from __future__ import annotations\n"
        "\n"
        "import json\n"
        "import logging\n"
        "import pickle\n"
        "\n"
        "import matplotlib.pyplot as plt\n"
        "import numpy as np\n"
        "import pandas as pd\n"
        "import seaborn as sns\n"
        "\n"
        "from m3_portfolio import (\n"
        "    CASH_TICKER,\n"
        "    EqualWeightOptimizer,\n"
        "    HRPOptimizer,\n"
        "    MaxSharpeOptimizer,\n"
        "    MinVarianceOptimizer,\n"
        "    RISK_FREE_RATE,\n"
        "    TRADING_DAYS,\n"
        ")\n"
        "from m4_backtesting import (\n"
        "    BacktestEngine,\n"
        "    build_60_40_benchmark,\n"
        "    build_spy_benchmark,\n"
        "    cagr,\n"
        "    annual_vol,\n"
        "    calmar_ratio,\n"
        "    drawdown_series,\n"
        "    max_drawdown,\n"
        "    regenerate_oos_clean_weights,\n"
        "    sharpe_ratio,\n"
        "    sortino_ratio,\n"
        ")\n"
        "\n"
        "logging.basicConfig(level=logging.INFO, format=\"%(asctime)s %(name)s %(levelname)s %(message)s\", datefmt=\"%H:%M:%S\")\n"
        "logger = logging.getLogger(\"m4_notebook\")\n"
        "sns.set_theme(style=\"whitegrid\")\n"
        "plt.rcParams[\"figure.dpi\"] = 110"
    ))

    cells.append(_md(
        "## Bloque 1 — Generación de pesos OOS-clean\n"
        "\n"
        "Truncamos `returns.parquet` a `index ≤ 2019-12-31`, recalculamos μ y Σ "
        "(Ledoit-Wolf) sobre la ventana truncada y re-invocamos los optimizadores de M3 "
        "con la **misma** configuración (`PROFILES`, `MAX_VOL`, `PRIMARY_OPTIMIZER`, "
        "`ALTERNATIVE_OPTIMIZER`, `BASELINE_OPTIMIZER`). Aplicamos la regla de selección de "
        "M3 (best Sharpe ex-ante sujeto a `vol_actual ≤ vol_cap × 1.01`)."
    ))
    cells.append(_code(
        "# Config idéntica a la usada en M3 (notebook m3_optimizacion_carteras.ipynb)\n"
        "PROFILES: dict[str, list[str]] = {\n"
        "    \"conservador\": [\"IEAG.AS\", \"EUNH.DE\", \"IBCI.AS\"],\n"
        "    \"moderado\":    [\"INFR.AS\", \"IHYG.L\", \"EXSA.DE\"],\n"
        "    \"agresivo\":    [\"CSPX.L\", \"EQQQ.DE\", \"EXI2.DE\"],\n"
        "}\n"
        "MAX_VOL: dict[str, float] = {\"conservador\": 0.08, \"moderado\": 0.15, \"agresivo\": 0.25}\n"
        "PRIMARY_OPTIMIZER:     dict[str, type] = {\"conservador\": MinVarianceOptimizer, \"moderado\": MaxSharpeOptimizer, \"agresivo\": HRPOptimizer}\n"
        "ALTERNATIVE_OPTIMIZER: dict[str, type] = {\"conservador\": MaxSharpeOptimizer,   \"moderado\": HRPOptimizer,      \"agresivo\": MaxSharpeOptimizer}\n"
        "BASELINE_OPTIMIZER = EqualWeightOptimizer\n"
        "TRAIN_END = pd.Timestamp(\"2019-12-31\")\n"
        "OOS_START = pd.Timestamp(\"2020-01-02\")\n"
        "OOS_END   = pd.Timestamp(\"2026-04-30\")"
    ))
    cells.append(_code(
        "returns_full = pd.read_parquet(PATHS.M2_RETURNS_PARQUET)\n"
        "print(f\"returns_full: {returns_full.shape}, {returns_full.index.min().date()} → {returns_full.index.max().date()}\")\n"
        "\n"
        "selected_oos = regenerate_oos_clean_weights(\n"
        "    returns=returns_full,\n"
        "    train_end_date=TRAIN_END,\n"
        "    profiles=PROFILES,\n"
        "    max_vol=MAX_VOL,\n"
        "    primary_optimizer=PRIMARY_OPTIMIZER,\n"
        "    alternative_optimizer=ALTERNATIVE_OPTIMIZER,\n"
        "    baseline_optimizer=BASELINE_OPTIMIZER,\n"
        "    risk_free_rate=RISK_FREE_RATE,\n"
        "    trading_days=TRADING_DAYS,\n"
        ")\n"
        "for profile, p in selected_oos.items():\n"
        "    print(f\"[{profile:<11}] {p}\")"
    ))
    cells.append(_code(
        "# Persistir pesos OOS-clean y summary\n"
        "weights_rows = []\n"
        "for profile, p in selected_oos.items():\n"
        "    for ticker, w in p.weights.items():\n"
        "        weights_rows.append({\"profile\": profile, \"ticker\": ticker, \"weight\": float(w)})\n"
        "weights_oos_df = pd.DataFrame(weights_rows).set_index([\"profile\", \"ticker\"]).sort_index()\n"
        "weights_oos_path = M4_OUT / \"weights_oos_clean.parquet\"\n"
        "weights_oos_df.to_parquet(weights_oos_path)\n"
        "print(f\"Saved → {weights_oos_path}\")\n"
        "\n"
        "summary_oos = {\n"
        "    profile: {\n"
        "        \"optimizer\": p.optimizer_name,\n"
        "        \"weights\": {k: float(v) for k, v in p.weights.items()},\n"
        "        \"cash_weight\": float(p.cash_weight),\n"
        "        \"expected_return\": float(p.expected_return),\n"
        "        \"expected_volatility\": float(p.expected_volatility),\n"
        "        \"expected_sharpe\": float(p.expected_sharpe),\n"
        "        \"max_volatility\": float(MAX_VOL[profile]),\n"
        "    }\n"
        "    for profile, p in selected_oos.items()\n"
        "}\n"
        "summary_oos_path = M4_OUT / \"portfolios_summary_oos_clean.json\"\n"
        "with open(summary_oos_path, \"w\", encoding=\"utf-8\") as fh:\n"
        "    json.dump(summary_oos, fh, indent=2, ensure_ascii=False)\n"
        "print(f\"Saved → {summary_oos_path}\")\n"
        "weights_oos_df"
    ))

    cells.append(_md(
        "## Bloque 2 — Carga de datos OOS\n"
        "\n"
        "Recortamos `returns_full` a la ventana `[OOS_START, OOS_END]` y dejamos preparados "
        "los pesos objetivo (extraídos de las carteras OOS-clean)."
    ))
    cells.append(_code(
        "returns_oos = returns_full.loc[OOS_START:OOS_END].copy()\n"
        "print(f\"returns_oos: {returns_oos.shape}, {returns_oos.index.min().date()} → {returns_oos.index.max().date()}\")\n"
        "\n"
        "# Pesos objetivo por perfil (incluye CASH si aplica)\n"
        "target_weights: dict[str, dict[str, float]] = {\n"
        "    profile: {k: float(v) for k, v in p.weights.items() if v > 0 or k == CASH_TICKER}\n"
        "    for profile, p in selected_oos.items()\n"
        "}\n"
        "for profile, tw in target_weights.items():\n"
        "    print(profile, tw)"
    ))

    cells.append(_md(
        "## Bloque 3 — Configuración del backtest\n"
        "\n"
        "- Frecuencia de rebalanceo: **trimestral** (`Q`).\n"
        "- Drift threshold: `None` (solo rebalanceo por calendar, para reproducibilidad simple).\n"
        "- Risk-free anual: 2% (coherente con M3)."
    ))
    cells.append(_code(
        "BACKTEST_CONFIG = {\n"
        "    \"rebalance_freq\": \"Q\",\n"
        "    \"drift_threshold\": None,\n"
        "    \"rf_annual\": RISK_FREE_RATE,\n"
        "    \"trading_days\": TRADING_DAYS,\n"
        "}\n"
        "BACKTEST_CONFIG"
    ))

    cells.append(_md(
        "## Bloque 4 — Ejecución por perfil\n"
        "\n"
        "Tres `BacktestEngine`, uno por perfil. Cada uno produce un `BacktestResult` con "
        "equity curve base 1.0, retornos diarios, histórico de pesos y log de rebalanceos."
    ))
    cells.append(_code(
        "# Reordenamos columnas para que coincidan con el universo de cada perfil\n"
        "results: dict = {}\n"
        "for profile in PROFILES:\n"
        "    universe = [t for t in target_weights[profile] if t != CASH_TICKER]\n"
        "    engine = BacktestEngine(\n"
        "        returns=returns_oos[universe],\n"
        "        target_weights=target_weights[profile],\n"
        "        **BACKTEST_CONFIG,\n"
        "    )\n"
        "    results[profile] = engine.run()\n"
        "    r = results[profile]\n"
        "    print(f\"[{profile:<11}] equity_final={r.equity_curve.iloc[-1]:.4f}, rebalances={len(r.rebalance_dates)}\")"
    ))

    cells.append(_md(
        "## Bloque 5 — Benchmarks\n"
        "\n"
        "SPY (S&P 500 US, USD) y 60/40 sintético en EUR (`0.6·CSPX.L + 0.4·IEAG.AS` con "
        "rebalanceo trimestral)."
    ))
    cells.append(_code(
        "spy_prices = pd.read_parquet(PATHS.M2_OUTPUTS_DIR / \"spy_prices.parquet\")\n"
        "spy_returns = build_spy_benchmark(spy_prices, OOS_START, OOS_END)\n"
        "spy_equity = (1 + spy_returns).cumprod()\n"
        "spy_equity = pd.concat([pd.Series([1.0], index=[spy_equity.index[0] - pd.Timedelta(days=1)]), spy_equity])\n"
        "spy_equity.name = \"spy\"\n"
        "\n"
        "bench_60_40_returns = build_60_40_benchmark(returns_oos)\n"
        "bench_60_40_equity = (1 + bench_60_40_returns).cumprod()\n"
        "bench_60_40_equity.name = \"bench_60_40\"\n"
        "\n"
        "print(f\"SPY: {len(spy_returns)} días, equity final={spy_equity.iloc[-1]:.4f}\")\n"
        "print(f\"60/40: {len(bench_60_40_returns)} días, equity final={bench_60_40_equity.iloc[-1]:.4f}\")"
    ))
    cells.append(_code(
        "# Empaquetar equity curves para persistencia\n"
        "equity_curves = pd.DataFrame({\n"
        "    f\"equity_{profile}\": results[profile].equity_curve\n"
        "    for profile in PROFILES\n"
        "})\n"
        "equity_curves[\"equity_spy\"] = spy_equity.reindex(equity_curves.index).ffill()\n"
        "equity_curves[\"equity_60_40\"] = bench_60_40_equity.reindex(equity_curves.index).ffill()\n"
        "equity_curves.to_parquet(M4_OUT / \"equity_curves.parquet\")\n"
        "print(f\"Saved → {M4_OUT / 'equity_curves.parquet'}\")\n"
        "equity_curves.tail()"
    ))
    cells.append(_code(
        "# Log de rebalanceos\n"
        "rebalance_rows = []\n"
        "for profile, r in results.items():\n"
        "    for d in r.rebalance_dates:\n"
        "        rebalance_rows.append({\"profile\": profile, \"date\": d})\n"
        "rebalance_log_df = pd.DataFrame(rebalance_rows)\n"
        "rebalance_log_df.to_parquet(M4_OUT / \"rebalance_log.parquet\")\n"
        "print(f\"Saved → {M4_OUT / 'rebalance_log.parquet'} ({len(rebalance_log_df)} entradas)\")"
    ))

    cells.append(_md(
        "## Bloque 6 — Métricas comparativas\n"
        "\n"
        "CAGR, vol anualizada, Sharpe, Sortino, Max Drawdown y Calmar para los tres perfiles "
        "y los dos benchmarks. Implementación propia (`m4_backtesting.metrics`), no QuantStats."
    ))
    cells.append(_code(
        "def _metrics_for(equity: pd.Series, rets: pd.Series, rf: float = RISK_FREE_RATE) -> dict:\n"
        "    mdd, peak, trough = max_drawdown(equity)\n"
        "    return {\n"
        "        \"CAGR_%\": cagr(equity) * 100,\n"
        "        \"vol_%\": annual_vol(rets) * 100,\n"
        "        \"Sharpe\": sharpe_ratio(rets, rf_annual=rf),\n"
        "        \"Sortino\": sortino_ratio(rets, rf_annual=rf),\n"
        "        \"MDD_%\": mdd * 100,\n"
        "        \"Calmar\": calmar_ratio(equity),\n"
        "    }\n"
        "\n"
        "metrics_rows = []\n"
        "for profile in PROFILES:\n"
        "    m = _metrics_for(results[profile].equity_curve, results[profile].returns)\n"
        "    m[\"serie\"] = profile\n"
        "    metrics_rows.append(m)\n"
        "metrics_rows.append({\"serie\": \"SPY\", **_metrics_for(spy_equity, spy_returns)})\n"
        "metrics_rows.append({\"serie\": \"60/40\", **_metrics_for(bench_60_40_equity, bench_60_40_returns)})\n"
        "metrics_df = pd.DataFrame(metrics_rows).set_index(\"serie\")\n"
        "metrics_df = metrics_df[[\"CAGR_%\", \"vol_%\", \"Sharpe\", \"Sortino\", \"MDD_%\", \"Calmar\"]]\n"
        "metrics_df.round(3)"
    ))
    cells.append(_code(
        "# Persistir métricas y drawdown series\n"
        "metrics_dict = {idx: {k: float(v) for k, v in row.items()} for idx, row in metrics_df.iterrows()}\n"
        "with open(M4_OUT / \"metrics_by_profile.json\", \"w\", encoding=\"utf-8\") as fh:\n"
        "    json.dump(metrics_dict, fh, indent=2, ensure_ascii=False)\n"
        "\n"
        "dd_df = pd.DataFrame({\n"
        "    f\"dd_{profile}\": drawdown_series(results[profile].equity_curve) for profile in PROFILES\n"
        "})\n"
        "dd_df[\"dd_spy\"] = drawdown_series(spy_equity).reindex(dd_df.index).ffill()\n"
        "dd_df[\"dd_60_40\"] = drawdown_series(bench_60_40_equity).reindex(dd_df.index).ffill()\n"
        "dd_df.to_parquet(M4_OUT / \"drawdown_series.parquet\")\n"
        "print(f\"Saved → {M4_OUT / 'metrics_by_profile.json'}\")\n"
        "print(f\"Saved → {M4_OUT / 'drawdown_series.parquet'}\")"
    ))

    cells.append(_md(
        "## Bloque 7 — Visualizaciones\n"
        "\n"
        "Equity curves superpuestas (escala log), drawdown plot y distribución de retornos."
    ))
    cells.append(_code(
        "fig, ax = plt.subplots(figsize=(11, 5))\n"
        "for profile in PROFILES:\n"
        "    ax.plot(results[profile].equity_curve, label=f\"{profile}\", linewidth=1.5)\n"
        "ax.plot(spy_equity, label=\"SPY\", linewidth=1.0, linestyle=\"--\", color=\"#666666\")\n"
        "ax.plot(bench_60_40_equity, label=\"60/40\", linewidth=1.0, linestyle=\":\", color=\"#333333\")\n"
        "ax.set_yscale(\"log\")\n"
        "ax.set_title(\"Equity curves OOS (base 1.0, escala log) — 2020-2026\")\n"
        "ax.set_ylabel(\"equity (log)\")\n"
        "ax.legend()\n"
        "fig.tight_layout()\n"
        "plt.show()"
    ))
    cells.append(_code(
        "fig, ax = plt.subplots(figsize=(11, 4))\n"
        "for profile in PROFILES:\n"
        "    ax.fill_between(dd_df.index, dd_df[f\"dd_{profile}\"] * 100, 0, alpha=0.3, label=profile)\n"
        "ax.plot(dd_df.index, dd_df[\"dd_60_40\"] * 100, color=\"#333333\", linewidth=1.0, linestyle=\":\", label=\"60/40\")\n"
        "ax.set_title(\"Drawdown OOS por perfil vs 60/40\")\n"
        "ax.set_ylabel(\"drawdown (%)\")\n"
        "ax.legend()\n"
        "fig.tight_layout()\n"
        "plt.show()"
    ))
    cells.append(_code(
        "fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True)\n"
        "for ax, profile in zip(axes, PROFILES):\n"
        "    sns.histplot(results[profile].returns * 100, bins=60, ax=ax, kde=True)\n"
        "    ax.set_title(f\"Retornos diarios · {profile}\")\n"
        "    ax.set_xlabel(\"retorno diario (%)\")\n"
        "fig.tight_layout()\n"
        "plt.show()"
    ))

    cells.append(_md(
        "## Bloque 8 — Tearsheets QuantStats\n"
        "\n"
        "QuantStats genera el HTML descriptivo. Las métricas canónicas son las del bloque 6 "
        "(implementación propia), no las de QuantStats. Esto evita dependencias de versión."
    ))
    cells.append(_code(
        "try:\n"
        "    import quantstats as qs\n"
        "    qs.extend_pandas()\n"
        "    for profile in PROFILES:\n"
        "        rets = results[profile].returns.copy()\n"
        "        rets.index = pd.to_datetime(rets.index)\n"
        "        bench = bench_60_40_returns.reindex(rets.index).fillna(0.0)\n"
        "        out = M4_OUT / f\"report_{profile}.html\"\n"
        "        qs.reports.html(rets, benchmark=bench, output=str(out), title=f\"M4 · {profile} vs 60/40\")\n"
        "        print(f\"Saved → {out}\")\n"
        "except Exception as exc:\n"
        "    print(f\"[WARN] No se pudo generar tearsheet QuantStats: {exc}\")"
    ))

    cells.append(_md(
        "## Bloque 9 — Comparativa pesos full vs OOS-clean\n"
        "\n"
        "Side-by-side de los pesos de M3 (`outputs/m3/weights.parquet`, μ/Σ full history) "
        "frente a los OOS-clean (μ/Σ ≤ 2019-12-31). Útil para narrativa de la memoria."
    ))
    cells.append(_code(
        "weights_m3 = pd.read_parquet(PATHS.M3_WEIGHTS_PARQUET).rename(columns={\"weight\": \"weight_full\"})\n"
        "weights_oos_renamed = weights_oos_df.rename(columns={\"weight\": \"weight_oos\"})\n"
        "comparison = weights_oos_renamed.join(weights_m3, how=\"outer\").fillna(0.0)\n"
        "comparison[\"delta\"] = comparison[\"weight_oos\"] - comparison[\"weight_full\"]\n"
        "comparison_path = M4_OUT / \"weights_comparison.parquet\"\n"
        "comparison.to_parquet(comparison_path)\n"
        "print(f\"Saved → {comparison_path}\")\n"
        "comparison.round(4)"
    ))

    cells.append(_md(
        "## Bloque 10 — Validación final (Go/No-Go)"
    ))
    cells.append(_code(
        "sharpe_moderado = metrics_df.loc[\"moderado\", \"Sharpe\"]\n"
        "sharpe_60_40    = metrics_df.loc[\"60/40\", \"Sharpe\"]\n"
        "cagr_cons = metrics_df.loc[\"conservador\", \"CAGR_%\"]\n"
        "cagr_mod  = metrics_df.loc[\"moderado\", \"CAGR_%\"]\n"
        "cagr_agr  = metrics_df.loc[\"agresivo\", \"CAGR_%\"]\n"
        "vol_cons  = metrics_df.loc[\"conservador\", \"vol_%\"]\n"
        "vol_mod   = metrics_df.loc[\"moderado\", \"vol_%\"]\n"
        "vol_agr   = metrics_df.loc[\"agresivo\", \"vol_%\"]\n"
        "\n"
        "checks = {\n"
        "    \"GO/NOGO · Sharpe(moderado) >= Sharpe(60/40)\": sharpe_moderado >= sharpe_60_40,\n"
        "    \"Ordenación CAGR · agresivo > moderado > conservador\": cagr_agr > cagr_mod > cagr_cons,\n"
        "    \"Vol conservador <= 8%\": vol_cons <= 8.0,\n"
        "    \"Vol moderado <= 15%\":   vol_mod  <= 15.0,\n"
        "    \"Vol agresivo <= 25%\":   vol_agr  <= 25.0,\n"
        "}\n"
        "for desc, ok in checks.items():\n"
        "    tag = \"PASS\" if ok else \"FAIL\"\n"
        "    print(f\"  [{tag}] {desc}\")\n"
        "\n"
        "print()\n"
        "print(f\"Sharpe moderado: {sharpe_moderado:.4f}  |  Sharpe 60/40: {sharpe_60_40:.4f}\")\n"
        "print(f\"CAGR  cons / mod / agr: {cagr_cons:.2f}% / {cagr_mod:.2f}% / {cagr_agr:.2f}%\")\n"
        "print(f\"Vol   cons / mod / agr: {vol_cons:.2f}% / {vol_mod:.2f}% / {vol_agr:.2f}%\")"
    ))

    nb["cells"] = cells
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    }
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as fh:
        nbf.write(nb, fh)
    print(f"Wrote notebook → {NOTEBOOK_PATH}  ({len(cells)} celdas)")


if __name__ == "__main__":
    build()
