"""M3 — Portfolio Optimization package.

Public API for the M3 stage of the Roboadvisor TFM.
"""

from .base import PortfolioOptimizer
from .constraints import (
    CASH_TICKER,
    apply_ucits_constraints,
    apply_volatility_cap,
    compute_effective_assets,
    compute_herfindahl_index,
    compute_portfolio_volatility,
)
from .equal_weight import EqualWeightOptimizer
from .hrp import HRPOptimizer
from .max_sharpe import MaxSharpeOptimizer
from .min_variance import MinVarianceOptimizer
from .portfolio import Portfolio
from .validators import validate_all_profiles, validate_portfolio

RISK_FREE_RATE = 0.02
TRADING_DAYS = 252

__all__ = [
    "CASH_TICKER",
    "EqualWeightOptimizer",
    "HRPOptimizer",
    "MaxSharpeOptimizer",
    "MinVarianceOptimizer",
    "Portfolio",
    "PortfolioOptimizer",
    "RISK_FREE_RATE",
    "TRADING_DAYS",
    "apply_ucits_constraints",
    "apply_volatility_cap",
    "compute_effective_assets",
    "compute_herfindahl_index",
    "compute_portfolio_volatility",
    "validate_all_profiles",
    "validate_portfolio",
]
