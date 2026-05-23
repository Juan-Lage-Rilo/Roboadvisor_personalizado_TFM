"""Métricas financieras puras para backtesting.

Todas las funciones son determinísticas y no dependen de QuantStats.
Convenciones:
    - returns: serie de retornos diarios simples (no compuestos), índice DatetimeIndex.
    - equity: curva de equity con base 1.0 al inicio.
    - periods_per_year: 252 por defecto (días hábiles).
    - rf_annual: tasa libre de riesgo anualizada (decimal, p.ej. 0.02).
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

TRADING_DAYS = 252


def cagr(equity: pd.Series, periods_per_year: int = TRADING_DAYS) -> float:
    """CAGR anualizado a partir de una equity curve.

    Args:
        equity: curva de equity con base 1.0 al inicio. Índice DatetimeIndex.
        periods_per_year: número de periodos por año (252 por defecto).

    Returns:
        CAGR en decimal (p.ej. 0.075 = 7.5%). Devuelve NaN si la serie está vacía
        o si equity[-1] <= 0.
    """
    if equity.empty or equity.iloc[-1] <= 0:
        return float("nan")
    n_periods = len(equity) - 1
    if n_periods <= 0:
        return 0.0
    total_return = equity.iloc[-1] / equity.iloc[0]
    return float(total_return ** (periods_per_year / n_periods) - 1)


def annual_vol(returns: pd.Series, periods_per_year: int = TRADING_DAYS) -> float:
    """Volatilidad anualizada de una serie de retornos.

    Usa ddof=1 (varianza muestral) para coherencia con M3.
    """
    if returns.empty:
        return float("nan")
    return float(returns.std(ddof=1) * np.sqrt(periods_per_year))


def sharpe_ratio(
    returns: pd.Series,
    rf_annual: float = 0.02,
    periods_per_year: int = TRADING_DAYS,
) -> float:
    """Ratio de Sharpe anualizado.

    Sharpe = (mean(r) * periods - rf_annual) / (std(r) * sqrt(periods))

    Devuelve NaN si la volatilidad es 0 o la serie está vacía.
    """
    if returns.empty:
        return float("nan")
    vol = annual_vol(returns, periods_per_year)
    if vol == 0 or np.isnan(vol):
        return float("nan")
    annualized_return = float(returns.mean() * periods_per_year)
    return (annualized_return - rf_annual) / vol


def sortino_ratio(
    returns: pd.Series,
    rf_annual: float = 0.02,
    periods_per_year: int = TRADING_DAYS,
) -> float:
    """Ratio de Sortino anualizado.

    Sortino = (annualized_return - rf_annual) / downside_deviation_annualized

    Downside deviation usa solo retornos negativos respecto al MAR diario (rf/periods).
    Devuelve NaN si no hay retornos negativos.
    """
    if returns.empty:
        return float("nan")
    mar_daily = rf_annual / periods_per_year
    downside = returns[returns < mar_daily] - mar_daily
    if downside.empty:
        return float("nan")
    downside_std = float(np.sqrt((downside ** 2).mean()) * np.sqrt(periods_per_year))
    if downside_std == 0:
        return float("nan")
    annualized_return = float(returns.mean() * periods_per_year)
    return (annualized_return - rf_annual) / downside_std


def max_drawdown(equity: pd.Series) -> tuple[float, pd.Timestamp | None, pd.Timestamp | None]:
    """Maximum drawdown y fechas de peak/trough.

    Returns:
        (mdd, peak_date, trough_date) donde mdd es negativo (p.ej. -0.35).
        Si la serie está vacía o no hay drawdown, devuelve (0.0, None, None).
    """
    if equity.empty:
        return 0.0, None, None
    running_max = equity.cummax()
    dd = (equity / running_max) - 1
    trough_date = dd.idxmin()
    mdd = float(dd.loc[trough_date])
    if mdd >= 0:
        return 0.0, None, None
    # Peak: último máximo antes del trough
    peak_date = equity.loc[:trough_date].idxmax()
    return mdd, peak_date, trough_date


def calmar_ratio(equity: pd.Series, periods_per_year: int = TRADING_DAYS) -> float:
    """Calmar = CAGR / |max_drawdown|. NaN si no hay drawdown."""
    mdd, _, _ = max_drawdown(equity)
    if mdd == 0:
        return float("nan")
    return cagr(equity, periods_per_year) / abs(mdd)


def drawdown_series(equity: pd.Series) -> pd.Series:
    """Serie temporal de drawdown: (equity / running_max) - 1."""
    if equity.empty:
        return pd.Series(dtype=float)
    running_max = equity.cummax()
    return (equity / running_max) - 1
