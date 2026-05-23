"""Tests de m4_backtesting.rebalancer."""
from __future__ import annotations

import pandas as pd
import pytest

from m4_backtesting.rebalancer import compute_rebalance_dates, detect_drift


class TestComputeRebalanceDates:
    def test_quarterly_on_three_years(self) -> None:
        index = pd.bdate_range(start="2020-01-02", end="2022-12-30")
        dates = compute_rebalance_dates(index, freq="Q")
        # 3 años × 4 trimestres − 1 (excluimos el Q de la fecha inicial) = 11
        # Pero el primer Q1 2020 se excluye solo si el min(index) cae en él y es el último día hábil.
        # Aceptamos al menos 11 fechas, todas con día hábil <= fin de trimestre.
        assert len(dates) >= 11
        assert all(d > index[0] for d in dates)

    def test_yearly(self) -> None:
        index = pd.bdate_range(start="2020-01-02", end="2022-12-30")
        dates = compute_rebalance_dates(index, freq="Y")
        # 3 años → 2 cierres anuales después del primero (2020-12, 2021-12, 2022-12 = 3 menos el de inicio si aplica)
        assert len(dates) >= 2

    def test_empty_index(self) -> None:
        index = pd.DatetimeIndex([])
        assert compute_rebalance_dates(index, freq="Q") == []

    def test_dates_are_in_index(self) -> None:
        index = pd.bdate_range(start="2020-01-02", end="2021-12-31")
        dates = compute_rebalance_dates(index, freq="Q")
        for d in dates:
            assert d in index


class TestDetectDrift:
    def test_no_drift_returns_false(self) -> None:
        current = {"A": 0.5, "B": 0.5}
        target = {"A": 0.5, "B": 0.5}
        assert detect_drift(current, target, threshold=0.05) is False

    def test_small_drift_returns_false(self) -> None:
        current = {"A": 0.52, "B": 0.48}
        target = {"A": 0.5, "B": 0.5}
        assert detect_drift(current, target, threshold=0.05) is False

    def test_large_drift_returns_true(self) -> None:
        current = {"A": 0.6, "B": 0.4}
        target = {"A": 0.5, "B": 0.5}
        assert detect_drift(current, target, threshold=0.05) is True

    def test_missing_key_treated_as_zero(self) -> None:
        current = {"A": 1.0}  # B implícito = 0
        target = {"A": 0.5, "B": 0.5}
        # |0 - 0.5| = 0.5 > 0.05
        assert detect_drift(current, target, threshold=0.05) is True
