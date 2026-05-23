"""Tests for post-hoc portfolio validation."""

from __future__ import annotations

from m3_portfolio import Portfolio, validate_portfolio


def _make_portfolio(weights, vol):
    return Portfolio(
        profile="test",
        optimizer_name="dummy",
        weights=weights,
        cash_weight=weights.get("CASH", 0.0),
        expected_return=0.1,
        expected_volatility=vol,
        expected_sharpe=0.5,
        herfindahl_index=0.34,
        n_effective_assets=3,
        constraints_satisfied=True,
    )


def test_valid_portfolio_passes_all(sample_cov, sample_tickers, sample_max_volatility):
    weights = {t: 1.0 / 3 for t in sample_tickers}
    portfolio = _make_portfolio(weights, vol=0.05)
    report = validate_portfolio(
        portfolio, sample_cov, sample_tickers, sample_max_volatility
    )
    assert report == {
        "sum_to_one": True,
        "long_only": True,
        "vol_within_cap": True,
        "hhi_in_range": True,
    }


def test_detects_short_weights(sample_cov, sample_tickers, sample_max_volatility):
    weights = {"ASSET_A": -0.1, "ASSET_B": 0.6, "ASSET_C": 0.5}
    portfolio = _make_portfolio(weights, vol=0.05)
    report = validate_portfolio(
        portfolio, sample_cov, sample_tickers, sample_max_volatility
    )
    assert report["long_only"] is False


def test_detects_sum_not_one(sample_cov, sample_tickers, sample_max_volatility):
    weights = {"ASSET_A": 0.4, "ASSET_B": 0.4, "ASSET_C": 0.4}
    portfolio = _make_portfolio(weights, vol=0.05)
    report = validate_portfolio(
        portfolio, sample_cov, sample_tickers, sample_max_volatility
    )
    assert report["sum_to_one"] is False


def test_detects_vol_above_cap(sample_cov, sample_tickers):
    weights = {t: 1.0 / 3 for t in sample_tickers}
    portfolio = _make_portfolio(weights, vol=0.5)
    # Set a tiny cap so the actual risk-side vol exceeds it.
    report = validate_portfolio(
        portfolio, sample_cov, sample_tickers, max_volatility=0.001
    )
    assert report["vol_within_cap"] is False
