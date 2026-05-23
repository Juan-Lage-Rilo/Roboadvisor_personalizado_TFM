"""Construcción de equity curves de benchmarks (SPY y 60/40)."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def build_spy_benchmark(
    spy_prices: pd.DataFrame | pd.Series,
    oos_start: str | pd.Timestamp,
    oos_end: str | pd.Timestamp,
) -> pd.Series:
    """Retornos diarios de SPY recortados al periodo OOS.

    Args:
        spy_prices: DataFrame o Series con precios diarios de SPY. Si es DataFrame,
            usa la columna 'Close' (o la primera columna si no existe).
        oos_start, oos_end: fechas inclusive del periodo OOS.

    Returns:
        Serie de retornos diarios con DatetimeIndex.
    """
    if isinstance(spy_prices, pd.DataFrame):
        col = "Close" if "Close" in spy_prices.columns else spy_prices.columns[0]
        prices = spy_prices[col]
    else:
        prices = spy_prices

    prices = prices.loc[oos_start:oos_end]
    if prices.empty:
        raise ValueError(
            f"No SPY data in OOS window [{oos_start}, {oos_end}]. "
            "Check outputs/m2/spy_prices.parquet coverage."
        )
    returns = prices.pct_change().dropna()
    returns.name = "spy"
    logger.info("SPY benchmark built: %d days, [%s, %s]", len(returns), returns.index.min().date(), returns.index.max().date())
    return returns


def build_60_40_benchmark(
    returns_m2: pd.DataFrame,
    equity_ticker: str = "CSPX.L",
    bond_ticker: str = "IEAG.AS",
    equity_weight: float = 0.6,
    rebalance_freq: str = "Q",
) -> pd.Series:
    """Retornos diarios de la cartera 60/40 sintética con rebalanceo trimestral.

    Construye la cartera combinando equity (CSPX.L) y bond (IEAG.AS) según los
    pesos `equity_weight` y `1-equity_weight`. Rebalancea al fin de cada periodo.

    Args:
        returns_m2: DataFrame de retornos diarios de M2.
        equity_ticker: ticker de renta variable (default CSPX.L).
        bond_ticker: ticker de renta fija (default IEAG.AS).
        equity_weight: peso de renta variable (default 0.6).
        rebalance_freq: 'M', 'Q' (default) o 'Y'.

    Returns:
        Serie de retornos diarios de la cartera 60/40 con rebalanceo.
    """
    missing = [t for t in (equity_ticker, bond_ticker) if t not in returns_m2.columns]
    if missing:
        raise ValueError(
            f"Tickers {missing} not in returns_m2 columns. "
            f"Available: {list(returns_m2.columns)}"
        )

    bond_weight = 1.0 - equity_weight
    target = {equity_ticker: equity_weight, bond_ticker: bond_weight}

    # Reutilizamos la lógica del engine para coherencia (sin cash)
    from m4_backtesting.engine import BacktestEngine

    engine = BacktestEngine(
        returns=returns_m2[[equity_ticker, bond_ticker]],
        target_weights=target,
        rebalance_freq=rebalance_freq,  # type: ignore[arg-type]
        drift_threshold=None,
        rf_annual=0.0,  # no hay cash en el 60/40
    )
    result = engine.run()
    returns = result.returns.copy()
    returns.name = "bench_60_40"
    logger.info(
        "60/40 benchmark built: %d days, %d rebalances",
        len(returns),
        len(result.rebalance_dates),
    )
    return returns
