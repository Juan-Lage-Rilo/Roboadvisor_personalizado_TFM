"""Tests deterministas de m4_backtesting.metrics."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from m4_backtesting.metrics import (
    annual_vol,
    cagr,
    calmar_ratio,
    drawdown_series,
    max_drawdown,
    sharpe_ratio,
    sortino_ratio,
)


class TestCAGR:
    def test_flat_equity_returns_zero(self, flat_equity: pd.Series) -> None:
        assert cagr(flat_equity) == pytest.approx(0.0, abs=1e-10)

    def test_5pct_growth(self, equity_5pct_cagr: pd.Series) -> None:
        assert cagr(equity_5pct_cagr) == pytest.approx(0.05, abs=1e-6)

    def test_empty_returns_nan(self) -> None:
        empty = pd.Series(dtype=float)
        assert np.isnan(cagr(empty))


class TestAnnualVol:
    def test_flat_returns_zero_vol(self) -> None:
        zeros = pd.Series([0.0] * 100)
        assert annual_vol(zeros) == pytest.approx(0.0, abs=1e-10)

    def test_known_vol(self) -> None:
        # std=0.01 diaria * sqrt(252) = ~0.1587
        rng = np.random.default_rng(seed=0)
        rets = pd.Series(rng.normal(0, 0.01, size=10_000))
        assert annual_vol(rets) == pytest.approx(0.01 * np.sqrt(252), rel=0.05)


class TestSharpe:
    def test_zero_vol_returns_nan(self) -> None:
        zeros = pd.Series([0.0] * 100)
        assert np.isnan(sharpe_ratio(zeros))

    def test_positive_excess_return(self) -> None:
        # Retornos diarios constantes de 0.001 → ann return ~25.2%
        # Con vol cero → NaN; pero si añadimos algo de vol, Sharpe positivo
        rng = np.random.default_rng(seed=0)
        rets = pd.Series(rng.normal(0.001, 0.01, size=10_000))
        assert sharpe_ratio(rets, rf_annual=0.0) > 0


class TestSortino:
    def test_no_downside_returns_nan(self) -> None:
        # Todos los retornos por encima del MAR → no hay downside
        rets = pd.Series([0.001] * 252)
        assert np.isnan(sortino_ratio(rets, rf_annual=0.0))


class TestMaxDrawdown:
    def test_flat_equity_no_drawdown(self, flat_equity: pd.Series) -> None:
        mdd, peak, trough = max_drawdown(flat_equity)
        assert mdd == 0.0
        assert peak is None
        assert trough is None

    def test_known_drawdown_10pct(self, equity_with_known_drawdown: pd.Series) -> None:
        mdd, peak, trough = max_drawdown(equity_with_known_drawdown)
        assert mdd == pytest.approx(-0.10, abs=1e-10)
        assert peak is not None
        assert trough is not None
        assert equity_with_known_drawdown.loc[peak] == 2.0
        assert equity_with_known_drawdown.loc[trough] == 1.8


class TestCalmar:
    def test_flat_returns_nan(self, flat_equity: pd.Series) -> None:
        assert np.isnan(calmar_ratio(flat_equity))


class TestDrawdownSeries:
    def test_first_value_is_zero(self, equity_with_known_drawdown: pd.Series) -> None:
        dd = drawdown_series(equity_with_known_drawdown)
        assert dd.iloc[0] == pytest.approx(0.0, abs=1e-10)

    def test_min_matches_max_drawdown(self, equity_with_known_drawdown: pd.Series) -> None:
        dd = drawdown_series(equity_with_known_drawdown)
        mdd, _, _ = max_drawdown(equity_with_known_drawdown)
        assert dd.min() == pytest.approx(mdd, abs=1e-10)
