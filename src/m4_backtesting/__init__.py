"""m4_backtesting · Módulo de backtesting walk-forward para el roboadvisor.

Este paquete implementa la validación OOS de las carteras optimizadas en M3,
con rebalanceo periódico y métricas independientes de QuantStats.

API pública:
    - regenerate_oos_clean_weights: genera pesos OOS-clean truncando returns a train_end_date.
    - BacktestEngine, BacktestResult: motor de simulación con rebalanceo.
    - build_spy_benchmark, build_60_40_benchmark: benchmarks comparativos.
    - cagr, annual_vol, sharpe_ratio, sortino_ratio, max_drawdown, calmar_ratio,
      drawdown_series: métricas estándar implementadas a mano.
"""
from m4_backtesting.benchmarks import build_60_40_benchmark, build_spy_benchmark
from m4_backtesting.engine import BacktestEngine, BacktestResult
from m4_backtesting.metrics import (
    annual_vol,
    cagr,
    calmar_ratio,
    drawdown_series,
    max_drawdown,
    sharpe_ratio,
    sortino_ratio,
)
from m4_backtesting.weights_generator import regenerate_oos_clean_weights

__all__ = [
    "BacktestEngine",
    "BacktestResult",
    "annual_vol",
    "build_60_40_benchmark",
    "build_spy_benchmark",
    "cagr",
    "calmar_ratio",
    "drawdown_series",
    "max_drawdown",
    "regenerate_oos_clean_weights",
    "sharpe_ratio",
    "sortino_ratio",
]

__version__ = "0.1.0"
