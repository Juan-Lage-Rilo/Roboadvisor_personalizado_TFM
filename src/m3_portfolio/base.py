"""Protocol contract every portfolio optimizer must satisfy."""

from __future__ import annotations

from typing import List, Protocol, runtime_checkable

import pandas as pd

from .portfolio import Portfolio


@runtime_checkable
class PortfolioOptimizer(Protocol):
    """Structural type for portfolio optimizers.

    Implementations must expose ``optimize`` returning a :class:`Portfolio`.
    """

    def optimize(
        self,
        mu: pd.Series,
        cov: pd.DataFrame,
        tickers: List[str],
        max_volatility: float,
        profile: str = "",
        risk_free_rate: float = 0.02,
    ) -> Portfolio:
        """Run the optimization for a single profile.

        Args:
            mu: Annualised expected returns indexed by ticker.
            cov: Annualised covariance matrix indexed and columned by ticker.
            tickers: Subset of tickers to use for this profile.
            max_volatility: Annualised volatility cap (e.g. 0.15 for 15%).
            profile: Profile label stored in the resulting Portfolio.
            risk_free_rate: Annualised risk-free rate used for Sharpe and
                cash blending. Defaults to 0.02.

        Returns:
            A :class:`Portfolio` with weights (possibly including ``"CASH"``)
            and ex-ante metrics that respect the volatility cap.
        """
        ...
