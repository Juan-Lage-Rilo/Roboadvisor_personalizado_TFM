"""Smoke tests for the four optimizers."""

from __future__ import annotations

import pytest

from m3_portfolio import (
    EqualWeightOptimizer,
    HRPOptimizer,
    MaxSharpeOptimizer,
    MinVarianceOptimizer,
    Portfolio,
)

OPTIMIZERS = [
    MinVarianceOptimizer,
    MaxSharpeOptimizer,
    HRPOptimizer,
    EqualWeightOptimizer,
]


@pytest.mark.parametrize("optimizer_cls", OPTIMIZERS)
def test_optimizer_returns_valid_portfolio(
    optimizer_cls,
    sample_mu,
    sample_cov,
    sample_tickers,
    sample_max_volatility,
):
    optimizer = optimizer_cls()
    portfolio = optimizer.optimize(
        mu=sample_mu,
        cov=sample_cov,
        tickers=sample_tickers,
        max_volatility=sample_max_volatility,
        profile="test",
    )

    assert isinstance(portfolio, Portfolio)
    total = sum(portfolio.weights.values())
    assert abs(total - 1.0) < 1e-6, f"weights must sum to 1, got {total}"
    assert all(
        w >= -1e-6 for w in portfolio.weights.values()
    ), "weights must be non-negative"
    assert portfolio.expected_volatility <= sample_max_volatility * 1.01
    assert portfolio.constraints_satisfied


def test_equal_weight_assigns_one_over_n(
    sample_mu, sample_cov, sample_tickers, sample_max_volatility
):
    portfolio = EqualWeightOptimizer().optimize(
        mu=sample_mu,
        cov=sample_cov,
        tickers=sample_tickers,
        max_volatility=sample_max_volatility,
    )
    n = len(sample_tickers)
    for ticker in sample_tickers:
        # may be slightly < 1/n if cash blending kicked in
        assert portfolio.weights.get(ticker, 0.0) <= 1.0 / n + 1e-6
        assert portfolio.weights.get(ticker, 0.0) > 0.0
