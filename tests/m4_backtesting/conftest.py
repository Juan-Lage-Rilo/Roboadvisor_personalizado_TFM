"""Fixtures sintéticas para los tests de m4_backtesting.

Convención:
    - Retornos diarios sintéticos de 3 años (~756 días hábiles).
    - 3 tickers ficticios + CASH disponible.
    - Pesos ficticios que suman 1 con y sin cash.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


N_DAYS = 252 * 3  # 3 años hábiles


@pytest.fixture
def synthetic_returns() -> pd.DataFrame:
    """Retornos diarios sintéticos para 3 tickers, 3 años, sin NaN.

    Reproducible: semilla fija. Distribución normal con medias/vols realistas.
    """
    rng = np.random.default_rng(seed=42)
    dates = pd.bdate_range(start="2020-01-02", periods=N_DAYS)
    data = {
        "AAA.L": rng.normal(loc=0.0004, scale=0.012, size=N_DAYS),  # equity ~10% / 19%
        "BBB.AS": rng.normal(loc=0.00015, scale=0.004, size=N_DAYS),  # bond ~4% / 6%
        "CCC.DE": rng.normal(loc=0.00025, scale=0.008, size=N_DAYS),  # mixed
    }
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def target_weights_no_cash() -> dict[str, float]:
    """Pesos objetivo sin componente cash."""
    return {"AAA.L": 0.5, "BBB.AS": 0.3, "CCC.DE": 0.2}


@pytest.fixture
def target_weights_with_cash() -> dict[str, float]:
    """Pesos objetivo con 20% en cash."""
    return {"AAA.L": 0.4, "BBB.AS": 0.25, "CCC.DE": 0.15, "CASH": 0.2}


@pytest.fixture
def flat_equity() -> pd.Series:
    """Equity curve plana en 1.0 (retornos cero)."""
    dates = pd.bdate_range(start="2020-01-02", periods=N_DAYS)
    return pd.Series(1.0, index=dates, name="equity")


@pytest.fixture
def equity_with_known_drawdown() -> pd.Series:
    """Equity que sube a 2.0, cae a 1.8 (10% drawdown), luego recupera a 2.2.

    MDD esperado = -0.10, peak = índice del 2.0, trough = índice del 1.8.
    """
    values = [1.0, 1.5, 2.0, 1.9, 1.8, 1.85, 2.0, 2.1, 2.2]
    dates = pd.bdate_range(start="2020-01-02", periods=len(values))
    return pd.Series(values, index=dates, name="equity")


@pytest.fixture
def equity_5pct_cagr() -> pd.Series:
    """Equity que crece exactamente 5% anualizado durante 1 año (253 puntos).

    `cagr(equity)` calcula con `n_periods = len(equity) - 1`, así que para que
    el CAGR salga exactamente 0.05 cuando periods_per_year=252, necesitamos
    n_periods = 252 → len(equity) = 253.
    """
    n_periods = 252
    n_points = n_periods + 1
    dates = pd.bdate_range(start="2020-01-02", periods=n_points)
    daily_growth = 1.05 ** (1 / n_periods)
    values = [daily_growth ** i for i in range(n_points)]
    return pd.Series(values, index=dates, name="equity")
