"""Generación de pesos OOS-clean reinvocando m3_portfolio sobre returns truncados.

Esta es la pieza crítica para garantizar la ausencia de look-ahead bias en la
fase de estimación de parámetros. Trunca el histórico a train_end_date,
recalcula μ y Σ, y ejecuta los mismos optimizadores de M3 con la misma
configuración. La selección final aplica la regla de M3: best Sharpe sujeto a
vol_actual <= vol_cap * 1.01.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf

if TYPE_CHECKING:
    # Import diferido para evitar dependencia circular en tests con mocks
    from m3_portfolio import Portfolio  # type: ignore[import-not-found]

logger = logging.getLogger(__name__)

TRADING_DAYS = 252


def _truncate_returns(
    returns: pd.DataFrame,
    train_end_date: pd.Timestamp,
) -> pd.DataFrame:
    """Trunca returns a index <= train_end_date. Levanta si queda vacío."""
    truncated = returns.loc[returns.index <= train_end_date]
    if truncated.empty:
        raise ValueError(
            f"Truncating returns to <= {train_end_date} leaves an empty DataFrame. "
            f"Original index range: [{returns.index.min()}, {returns.index.max()}]"
        )
    if len(truncated) < TRADING_DAYS:
        logger.warning(
            "Only %d days available after truncation; covariance estimate may be unstable.",
            len(truncated),
        )
    return truncated


def _estimate_mu_cov(
    returns: pd.DataFrame,
    trading_days: int = TRADING_DAYS,
) -> tuple[pd.Series, pd.DataFrame]:
    """μ anualizado (media × trading_days) y Σ anualizado (Ledoit-Wolf × trading_days).

    Coherente con el cálculo de M2 / M3.
    """
    mu = returns.mean() * trading_days
    lw = LedoitWolf().fit(returns.values)
    cov_matrix = lw.covariance_ * trading_days
    cov = pd.DataFrame(cov_matrix, index=returns.columns, columns=returns.columns)
    return mu, cov


def _pick_best(
    candidates: dict[str, "Portfolio"],
    vol_cap: float,
) -> tuple[str, "Portfolio"]:
    """Aplica la regla de selección de M3: best Sharpe sujeto a vol <= vol_cap * 1.01.

    Si ninguna cumple, devuelve la de menor volatilidad como fallback (con warning).
    """
    feasible = {
        label: p for label, p in candidates.items() if p.expected_volatility <= vol_cap * 1.01
    }
    if feasible:
        best_label = max(feasible.keys(), key=lambda k: feasible[k].expected_sharpe)
        return best_label, feasible[best_label]
    # Fallback: ninguna cumple el cap → la de menor volatilidad
    logger.warning(
        "No candidate respects vol_cap=%.4f. Falling back to min-volatility candidate.",
        vol_cap,
    )
    fallback_label = min(candidates.keys(), key=lambda k: candidates[k].expected_volatility)
    return fallback_label, candidates[fallback_label]


def regenerate_oos_clean_weights(
    returns: pd.DataFrame,
    train_end_date: pd.Timestamp,
    profiles: dict[str, list[str]],
    max_vol: dict[str, float],
    primary_optimizer: dict[str, type],
    alternative_optimizer: dict[str, type],
    baseline_optimizer: type,
    risk_free_rate: float = 0.02,
    trading_days: int = TRADING_DAYS,
) -> dict[str, "Portfolio"]:
    """Regenera pesos OOS-clean truncando returns y reinvocando m3_portfolio.

    Args:
        returns: DataFrame de retornos diarios completo (de M2).
        train_end_date: fecha inclusive hasta la que se trunca (típico: 2019-12-31).
        profiles: dict perfil → lista de tickers (idéntico a M3).
        max_vol: dict perfil → cap de volatilidad (idéntico a M3).
        primary_optimizer: dict perfil → clase de optimizador principal.
        alternative_optimizer: dict perfil → clase de optimizador alternativo.
        baseline_optimizer: clase del optimizador baseline (típico: EqualWeightOptimizer).
        risk_free_rate: rf anualizado (default 0.02).
        trading_days: periodos por año (default 252).

    Returns:
        Dict perfil → Portfolio seleccionado (el "mejor" según regla M3).
    """
    train_end_date = pd.Timestamp(train_end_date)
    truncated = _truncate_returns(returns, train_end_date)
    logger.info(
        "Returns truncated: [%s, %s], %d days, %d tickers",
        truncated.index.min().date(),
        truncated.index.max().date(),
        len(truncated),
        len(truncated.columns),
    )

    mu, cov = _estimate_mu_cov(truncated, trading_days=trading_days)
    logger.info("mu/cov estimated on train window (Ledoit-Wolf).")

    selected: dict[str, "Portfolio"] = {}
    for profile, tickers in profiles.items():
        cap = max_vol[profile]
        candidates: dict[str, "Portfolio"] = {}
        for label, opt_cls in [
            ("principal", primary_optimizer[profile]),
            ("alternativo", alternative_optimizer[profile]),
            ("baseline", baseline_optimizer),
        ]:
            optimizer = opt_cls()
            portfolio = optimizer.optimize(
                mu=mu,
                cov=cov,
                tickers=tickers,
                max_volatility=cap,
                profile=profile,
                risk_free_rate=risk_free_rate,
            )
            candidates[label] = portfolio
        best_label, best_portfolio = _pick_best(candidates, cap)
        selected[profile] = best_portfolio
        logger.info(
            "[%s] selected '%s' (vol=%.4f, sharpe=%.4f)",
            profile,
            best_label,
            best_portfolio.expected_volatility,
            best_portfolio.expected_sharpe,
        )
    return selected
