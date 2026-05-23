"""Hierarchical Risk Parity optimizer (López de Prado, 2016)."""

from __future__ import annotations

import logging
from typing import List

import pandas as pd
from pypfopt import HRPOpt

from ._build import build_portfolio
from .portfolio import Portfolio

logger = logging.getLogger(__name__)


class HRPOptimizer:
    """Hierarchical Risk Parity, fed with the M2 Ledoit-Wolf covariance.

    HRP does not require ``mu``; it allocates by recursive bisection over a
    hierarchical clustering of the correlation matrix.
    """

    name = "hrp"

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
            "HRP optimize [%s]: n_assets=%d, vol_cap=%.2f%%",
            profile,
            len(tickers),
            max_volatility * 100.0,
        )
        sub_cov = cov.loc[tickers, tickers]
        hrp = HRPOpt(cov_matrix=sub_cov)
        hrp.optimize()
        raw = hrp.clean_weights(cutoff=0.0, rounding=None)
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
