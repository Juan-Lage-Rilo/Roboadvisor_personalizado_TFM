"""UCITS constraints, volatility cap and concentration metrics."""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

CASH_TICKER = "CASH"


def apply_ucits_constraints(weights: Dict[str, float]) -> Dict[str, float]:
    """Project arbitrary weights onto the UCITS feasible set.

    Clips negative weights to zero and renormalises to sum to one.

    Args:
        weights: Mapping ticker -> weight.

    Returns:
        New dict with non-negative weights summing to 1.0.

    Raises:
        ValueError: If all weights are non-positive (cannot renormalise).
    """
    clipped = {t: max(0.0, float(w)) for t, w in weights.items()}
    total = sum(clipped.values())
    if total <= 0.0:
        raise ValueError("Cannot renormalise weights with non-positive total.")
    return {t: w / total for t, w in clipped.items()}


def compute_portfolio_volatility(
    weights: Dict[str, float],
    cov: pd.DataFrame,
    tickers: List[str],
) -> float:
    """Annualised portfolio volatility ``sqrt(wᵀ Σ w)``.

    Only risk-asset weights (entries present in ``tickers``) contribute.
    Cash weights are ignored.
    """
    w = np.array([weights.get(t, 0.0) for t in tickers], dtype=float)
    sigma = cov.loc[tickers, tickers].values
    variance = float(w @ sigma @ w)
    return float(np.sqrt(max(variance, 0.0)))


def apply_volatility_cap(
    weights: Dict[str, float],
    cov: pd.DataFrame,
    tickers: List[str],
    max_volatility: float,
) -> Tuple[Dict[str, float], float]:
    """Blend portfolio with cash so the resulting volatility ≤ ``max_volatility``.

    Cash is modelled as a synthetic risk-free asset (vol = 0, correlation 0).
    Mixing a portfolio (vol σ_p) with weight α into cash yields vol = α · σ_p.
    Thus α = min(1, max_volatility / σ_p) and cash_weight = 1 - α.

    Args:
        weights: UCITS-feasible weights of the risk assets (sum to 1).
        cov: Annualised covariance matrix.
        tickers: Universe used for the risk portfolio.
        max_volatility: Annualised volatility cap.

    Returns:
        Tuple ``(weights_with_cash, cash_weight)`` where the dict still sums
        to 1.0 (including the ``"CASH"`` entry when blending kicks in).
    """
    vol = compute_portfolio_volatility(weights, cov, tickers)
    if vol <= max_volatility or vol == 0.0:
        return dict(weights), 0.0

    alpha = max_volatility / vol
    blended = {t: w * alpha for t, w in weights.items()}
    cash_weight = 1.0 - alpha
    blended[CASH_TICKER] = cash_weight
    logger.info(
        "Volatility cap binding: vol=%.4f > cap=%.4f; blended with cash=%.2f%%",
        vol,
        max_volatility,
        cash_weight * 100.0,
    )
    return blended, cash_weight


def compute_herfindahl_index(weights: Dict[str, float]) -> float:
    """HHI of the risk-asset weights (``CASH`` excluded).

    Ranges in ``[1/n, 1]`` where ``n`` is the number of risk assets present.
    """
    risk_weights = [w for t, w in weights.items() if t != CASH_TICKER and w > 0]
    if not risk_weights:
        return 0.0
    total = sum(risk_weights)
    if total <= 0.0:
        return 0.0
    normalized = [w / total for w in risk_weights]
    return float(sum(w * w for w in normalized))


def compute_effective_assets(
    weights: Dict[str, float],
    threshold: float = 0.01,
) -> int:
    """Count of risk assets whose weight exceeds ``threshold``."""
    return sum(
        1 for t, w in weights.items() if t != CASH_TICKER and w > threshold
    )
