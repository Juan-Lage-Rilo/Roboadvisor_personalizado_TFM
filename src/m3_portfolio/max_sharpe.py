"""Maximum Sharpe ratio optimizer (Markowitz, long-only)."""

from __future__ import annotations

import logging
from typing import List

import pandas as pd
from pypfopt import EfficientFrontier

from ._build import build_portfolio
from .portfolio import Portfolio

logger = logging.getLogger(__name__)


class MaxSharpeOptimizer:
    """Long-only max Sharpe portfolio.

    Cash blending (in ``_build.build_portfolio``) handles cases where the
    unconstrained tangency portfolio exceeds the per-profile volatility cap.
    """

    name = "max_sharpe"

    def optimize(
        self,
        mu: pd.Series,
        cov: pd.DataFrame,
        tickers: List[str],
        max_volatility: float,
        profile: str = "",
        risk_free_rate: float = 0.02,
    ) -> Portfolio:
        logger.info(
            "MaxSharpe optimize [%s]: n_assets=%d, vol_cap=%.2f%%, rf=%.2f%%",
            profile,
            len(tickers),
            max_volatility * 100.0,
            risk_free_rate * 100.0,
        )
        sub_mu = mu.loc[tickers]
        sub_cov = cov.loc[tickers, tickers]
        ef = EfficientFrontier(sub_mu, sub_cov, weight_bounds=(0.0, 1.0))
        if float(sub_mu.max()) <= risk_free_rate:
            logger.warning(
                "Max(mu)=%.4f <= rf=%.4f; max_sharpe is undefined. "
                "Falling back to min_volatility for profile=%s.",
                float(sub_mu.max()),
                risk_free_rate,
                profile,
            )
            ef.min_volatility()
        else:
            ef.max_sharpe(risk_free_rate=risk_free_rate)
        raw = ef.clean_weights(cutoff=0.0, rounding=None)
        return build_portfolio(
            raw_weights=dict(raw),
            profile=profile,
            optimizer_name=self.name,
            mu=mu,
            cov=cov,
            tickers=tickers,
            max_volatility=max_volatility,
            risk_free_rate=risk_free_rate,
        )
