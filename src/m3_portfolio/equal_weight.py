"""Equal-weight baseline allocator (1/n)."""

from __future__ import annotations

import logging
from typing import List

import pandas as pd

from ._build import build_portfolio
from .portfolio import Portfolio

logger = logging.getLogger(__name__)


class EqualWeightOptimizer:
    """1/n baseline. Useful as a sanity-check reference for the optimizers."""

    name = "equal_weight"

    def optimize(
        self,
        mu: pd.Series,
        cov: pd.DataFrame,
        tickers: List[str],
        max_volatility: float,
        profile: str = "",
        risk_free_rate: float = 0.02,
    ) -> Portfolio:
        n = len(tickers)
        logger.info(
            "EqualWeight optimize [%s]: n_assets=%d, vol_cap=%.2f%%",
            profile,
            n,
            max_volatility * 100.0,
        )
        raw = {t: 1.0 / n for t in tickers}
        return build_portfolio(
            raw_weights=raw,
            profile=profile,
            optimizer_name=self.name,
            mu=mu,
            cov=cov,
            tickers=tickers,
            max_volatility=max_volatility,
            risk_free_rate=risk_free_rate,
        )
