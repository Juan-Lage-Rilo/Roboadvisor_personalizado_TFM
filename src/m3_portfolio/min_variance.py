"""Minimum variance optimizer (Markowitz, long-only)."""

from __future__ import annotations

import logging
from typing import List

import pandas as pd
from pypfopt import EfficientFrontier

from ._build import build_portfolio
from .portfolio import Portfolio

logger = logging.getLogger(__name__)


class MinVarianceOptimizer:
    """Long-only minimum variance portfolio using PyPortfolioOpt."""

    name = "min_variance"

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
            "MinVariance optimize [%s]: n_assets=%d, vol_cap=%.2f%%",
            profile,
            len(tickers),
            max_volatility * 100.0,
        )
        sub_mu = mu.loc[tickers]
        sub_cov = cov.loc[tickers, tickers]
        ef = EfficientFrontier(sub_mu, sub_cov, weight_bounds=(0.0, 1.0))
        ef.min_volatility()
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
