"""Tests for UCITS constraints and concentration metrics."""

from __future__ import annotations

import pytest

from m3_portfolio import (
    apply_ucits_constraints,
    apply_volatility_cap,
    compute_effective_assets,
    compute_herfindahl_index,
)
from m3_portfolio.constraints import CASH_TICKER


def test_apply_ucits_clips_and_normalises():
    raw = {"A": -0.2, "B": 0.6, "C": 0.8}
    out = apply_ucits_constraints(raw)
    assert all(w >= 0.0 for w in out.values())
    assert abs(sum(out.values()) - 1.0) < 1e-9
    assert out["A"] == 0.0


def test_apply_ucits_raises_on_all_zero():
    with pytest.raises(ValueError):
        apply_ucits_constraints({"A": -1.0, "B": 0.0})


def test_hhi_equal_weights(sample_tickers):
    n = len(sample_tickers)
    weights = {t: 1.0 / n for t in sample_tickers}
    assert compute_herfindahl_index(weights) == pytest.approx(1.0 / n)


def test_hhi_excludes_cash(sample_tickers):
    n = len(sample_tickers)
    weights = {t: 0.5 / n for t in sample_tickers}
    weights[CASH_TICKER] = 0.5
    # HHI computed on risk side only -> equal weight HHI = 1/n
    assert compute_herfindahl_index(weights) == pytest.approx(1.0 / n)


def test_effective_assets_counts_above_threshold():
    weights = {"A": 0.5, "B": 0.49, "C": 0.005, "D": 0.005}
    assert compute_effective_assets(weights, threshold=0.01) == 2


def test_volatility_cap_blends_cash_when_above(sample_cov, sample_tickers):
    weights = {t: 1.0 / 3 for t in sample_tickers}
    # Use an unreachably low cap to force blending.
    blended, cash = apply_volatility_cap(
        weights, sample_cov, sample_tickers, max_volatility=0.001
    )
    assert cash > 0.0
    assert CASH_TICKER in blended
    assert abs(sum(blended.values()) - 1.0) < 1e-9


def test_volatility_cap_noop_when_below(sample_cov, sample_tickers):
    weights = {t: 1.0 / 3 for t in sample_tickers}
    blended, cash = apply_volatility_cap(
        weights, sample_cov, sample_tickers, max_volatility=10.0
    )
    assert cash == 0.0
    assert CASH_TICKER not in blended
