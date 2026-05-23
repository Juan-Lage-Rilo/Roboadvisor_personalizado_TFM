"""Shared portfolio assembly logic used by every optimizer."""

from __future__ import annotations

import logging
from typing import Dict, List

import numpy as np
import pandas as pd

from .constraints import (
    CASH_TICKER,
    apply_ucits_constraints,
    apply_volatility_cap,
    compute_effective_assets,
    compute_herfindahl_index,
    compute_portfolio_volatility,
)
from .portfolio import Portfolio

logger = logging.getLogger(__name__)


def build_portfolio(
    raw_weights: Dict[str, float],
    profile: str,
    optimizer_name: str,
    mu: pd.Series,
    cov: pd.DataFrame,
    tickers: List[str],
    max_volatility: float,
    risk_free_rate: float,
) -> Portfolio:
    """Apply UCITS + vol-cap projections to raw optimizer weights and
    return an immutable ``Portfolio`` with ex-ante metrics.

    Args:
        raw_weights: Optimizer output (may violate constraints).
        profile: Risk profile name.
        optimizer_name: Identifier of the calling optimizer.
        mu: Annualised expected returns indexed by ticker.
        cov: Annualised covariance matrix.
        tickers: Risk-asset universe (CASH excluded).
        max_volatility: Profile volatility cap (annualised).
        risk_free_rate: Annualised risk-free rate.

    Returns:
        Fully populated ``Portfolio`` instance.
    """
    ucits = apply_ucits_constraints(raw_weights)
    blended, cash_weight = apply_volatility_cap(ucits, cov, tickers, max_volatility)

    risk_only = {t: w for t, w in blended.items() if t != CASH_TICKER}
    risk_return = float(
        np.sum([risk_only.get(t, 0.0) * float(mu[t]) for t in tickers])
    )
    expected_return = (1.0 - cash_weight) * risk_return + cash_weight * risk_free_rate
    expected_volatility = (1.0 - cash_weight) * compute_portfolio_volatility(
        risk_only, cov, tickers
    )
    if expected_volatility > 1e-12:
        expected_sharpe = (expected_return - risk_free_rate) / expected_volatility
    else:
        expected_sharpe = float("nan")

    hhi = compute_herfindahl_index(blended)
    n_eff = compute_effective_assets(blended)

    constraints_ok = (
        abs(sum(blended.values()) - 1.0) < 1e-6
        and all(w >= -1e-6 for w in blended.values())
        and expected_volatility <= max_volatility * 1.01
    )

    portfolio = Portfolio(
        profile=profile,
        optimizer_name=optimizer_name,
        weights=blended,
        cash_weight=cash_weight,
        expected_return=expected_return,
        expected_volatility=expected_volatility,
        expected_sharpe=expected_sharpe,
        herfindahl_index=hhi,
        n_effective_assets=n_eff,
        constraints_satisfied=constraints_ok,
    )
    logger.info("Built %s", portfolio)
    return portfolio
