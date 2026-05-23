"""Post-hoc validation of optimized portfolios."""

from __future__ import annotations

import logging
from typing import Dict, List

import pandas as pd

from .constraints import (
    CASH_TICKER,
    compute_herfindahl_index,
    compute_portfolio_volatility,
)
from .portfolio import Portfolio

logger = logging.getLogger(__name__)

SUM_TOL = 1e-6
LONG_ONLY_TOL = 1e-6
VOL_CAP_TOL = 1.01  # 1% slack on vol cap
HHI_TOL = 1e-9


def validate_portfolio(
    portfolio: Portfolio,
    cov: pd.DataFrame,
    tickers: List[str],
    max_volatility: float,
) -> Dict[str, bool]:
    """Check UCITS, vol cap and concentration invariants.

    Returns:
        Dict with keys ``sum_to_one``, ``long_only``, ``vol_within_cap``,
        ``hhi_in_range``.
    """
    weights = portfolio.weights
    total = sum(weights.values())
    sum_to_one = abs(total - 1.0) < SUM_TOL

    long_only = all(w >= -LONG_ONLY_TOL for w in weights.values())

    risk_only = {t: w for t, w in weights.items() if t != CASH_TICKER}
    vol = compute_portfolio_volatility(risk_only, cov, tickers)
    cash = weights.get(CASH_TICKER, 0.0)
    realized_vol = (1.0 - cash) * vol  # cash has zero vol and zero correlation
    vol_within_cap = realized_vol <= max_volatility * VOL_CAP_TOL

    hhi = compute_herfindahl_index(weights)
    n_risk = sum(1 for t, w in weights.items() if t != CASH_TICKER and w > 0)
    lower = (1.0 / n_risk) - HHI_TOL if n_risk > 0 else 0.0
    upper = 1.0 + HHI_TOL
    hhi_in_range = (lower <= hhi <= upper) if n_risk > 0 else True

    report = {
        "sum_to_one": bool(sum_to_one),
        "long_only": bool(long_only),
        "vol_within_cap": bool(vol_within_cap),
        "hhi_in_range": bool(hhi_in_range),
    }
    logger.info("Validation %s: %s", portfolio.profile, report)
    return report


def validate_all_profiles(
    selected: Dict[str, Portfolio],
    cov: pd.DataFrame,
    profile_tickers: Dict[str, List[str]],
    max_volatilities: Dict[str, float],
) -> Dict[str, Dict[str, bool]]:
    """Run :func:`validate_portfolio` on each selected portfolio."""
    return {
        profile: validate_portfolio(
            portfolio,
            cov,
            profile_tickers[profile],
            max_volatilities[profile],
        )
        for profile, portfolio in selected.items()
    }
