"""Tests del BacktestEngine."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from m4_backtesting.engine import BacktestEngine


class TestBacktestEngineInit:
    def test_invalid_weights_sum_raises(
        self, synthetic_returns: pd.DataFrame
    ) -> None:
        bad_weights = {"AAA.L": 0.5, "BBB.AS": 0.3}  # suma 0.8
        with pytest.raises(ValueError, match="must sum to 1"):
            BacktestEngine(synthetic_returns, bad_weights)

    def test_unknown_ticker_raises(self, synthetic_returns: pd.DataFrame) -> None:
        bad_weights = {"AAA.L": 0.5, "XXX.YY": 0.5}
        with pytest.raises(ValueError, match="not in returns columns"):
            BacktestEngine(synthetic_returns, bad_weights)

    def test_nan_in_returns_raises(
        self,
        synthetic_returns: pd.DataFrame,
        target_weights_no_cash: dict[str, float],
    ) -> None:
        returns_with_nan = synthetic_returns.copy()
        returns_with_nan.iloc[10, 0] = np.nan
        with pytest.raises(ValueError, match="NaN"):
            BacktestEngine(returns_with_nan, target_weights_no_cash)


class TestBacktestEngineRun:
    def test_equity_starts_at_one(
        self,
        synthetic_returns: pd.DataFrame,
        target_weights_no_cash: dict[str, float],
    ) -> None:
        engine = BacktestEngine(synthetic_returns, target_weights_no_cash)
        result = engine.run()
        assert result.equity_curve.iloc[0] == pytest.approx(1.0, abs=1e-12)

    def test_equity_length_matches_returns(
        self,
        synthetic_returns: pd.DataFrame,
        target_weights_no_cash: dict[str, float],
    ) -> None:
        engine = BacktestEngine(synthetic_returns, target_weights_no_cash)
        result = engine.run()
        assert len(result.equity_curve) == len(synthetic_returns)

    def test_weights_sum_to_one_at_rebalance(
        self,
        synthetic_returns: pd.DataFrame,
        target_weights_no_cash: dict[str, float],
    ) -> None:
        engine = BacktestEngine(synthetic_returns, target_weights_no_cash)
        result = engine.run()
        for date in result.rebalance_dates:
            row = result.weights_history.loc[date]
            assert row.sum() == pytest.approx(1.0, abs=1e-6)

    def test_cash_weight_supported(
        self,
        synthetic_returns: pd.DataFrame,
        target_weights_with_cash: dict[str, float],
    ) -> None:
        engine = BacktestEngine(
            synthetic_returns, target_weights_with_cash, rf_annual=0.02
        )
        result = engine.run()
        assert "CASH" in result.weights_history.columns
        # En cada rebalanceo, CASH debe volver a 0.2
        for date in result.rebalance_dates:
            assert result.weights_history.loc[date, "CASH"] == pytest.approx(
                0.2, abs=1e-6
            )

    def test_quarterly_rebalances_count(
        self,
        synthetic_returns: pd.DataFrame,
        target_weights_no_cash: dict[str, float],
    ) -> None:
        engine = BacktestEngine(
            synthetic_returns, target_weights_no_cash, rebalance_freq="Q"
        )
        result = engine.run()
        # 3 años × 4 trimestres - posibles bordes = entre 10 y 12
        assert 10 <= len(result.rebalance_dates) <= 12

    def test_no_lookahead_with_truncated_input(
        self,
        synthetic_returns: pd.DataFrame,
        target_weights_no_cash: dict[str, float],
    ) -> None:
        """Si truncamos los returns, la equity hasta la fecha de corte coincide.

        Es la garantía de que el engine solo lee información histórica de la serie
        que se le pasa, sin "mirar al futuro".
        """
        cutoff = synthetic_returns.index[252]  # 1 año
        truncated = synthetic_returns.loc[:cutoff]

        engine_full = BacktestEngine(synthetic_returns, target_weights_no_cash)
        engine_trunc = BacktestEngine(truncated, target_weights_no_cash)

        eq_full = engine_full.run().equity_curve.loc[:cutoff]
        eq_trunc = engine_trunc.run().equity_curve

        pd.testing.assert_series_equal(eq_full, eq_trunc, check_names=False)
