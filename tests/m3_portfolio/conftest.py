"""Shared pytest fixtures for the m3_portfolio test suite."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
import pytest

# Make `m3_portfolio` importable without an installed package.
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))


@pytest.fixture
def sample_tickers() -> List[str]:
    return ["ASSET_A", "ASSET_B", "ASSET_C"]


@pytest.fixture
def sample_cov(sample_tickers: List[str]) -> pd.DataFrame:
    rng = np.random.default_rng(seed=42)
    a = rng.standard_normal((3, 3)) * 0.05
    sigma = a @ a.T + 1e-4 * np.eye(3)
    return pd.DataFrame(sigma, index=sample_tickers, columns=sample_tickers)


@pytest.fixture
def sample_mu(sample_tickers: List[str]) -> pd.Series:
    return pd.Series([0.05, 0.08, 0.12], index=sample_tickers)


@pytest.fixture
def sample_max_volatility() -> float:
    return 0.15
