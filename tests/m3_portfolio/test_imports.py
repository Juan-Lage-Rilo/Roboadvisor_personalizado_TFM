"""Smoke-test that the public API and internal helpers import cleanly.

Guards against regressions like the missing ``_build.py`` that broke
``m3_optimizacion_carteras.ipynb`` execution.
"""

from __future__ import annotations


def test_public_api_imports() -> None:
    from m3_portfolio import (
        CASH_TICKER,
        EqualWeightOptimizer,
        HRPOptimizer,
        MaxSharpeOptimizer,
        MinVarianceOptimizer,
        Portfolio,
        PortfolioOptimizer,
        RISK_FREE_RATE,
        TRADING_DAYS,
        apply_ucits_constraints,
        apply_volatility_cap,
        compute_effective_assets,
        compute_herfindahl_index,
        compute_portfolio_volatility,
        validate_all_profiles,
        validate_portfolio,
    )

    assert CASH_TICKER == "CASH"
    assert RISK_FREE_RATE == 0.02
    assert TRADING_DAYS == 252


def test_build_module_importable() -> None:
    from m3_portfolio._build import build_portfolio

    assert callable(build_portfolio)


def test_every_optimizer_can_import_build() -> None:
    # The four optimizer modules all depend on ``_build.build_portfolio``;
    # importing them surfaces any broken relative import.
    from m3_portfolio import equal_weight, hrp, max_sharpe, min_variance

    for mod in (equal_weight, hrp, max_sharpe, min_variance):
        assert hasattr(mod, "build_portfolio")
