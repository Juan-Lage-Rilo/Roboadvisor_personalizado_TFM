"""Project-wide path registry.

All notebooks and scripts should import from this module instead of
hard-coding relative paths. Anchors are resolved from this file's
location, so the layout works regardless of the current working
directory (``notebooks/``, ``scripts/``, repo root, etc.).

Layout (under ``PROJECT_ROOT``)::

    data/                 raw inputs (read-only)
    outputs/              generated artefacts (parquet, pkl, json)
    outputs/m2/           returns.parquet, mu.pkl, cov_ledoit_wolf.pkl
    outputs/m3/           weights.parquet, portfolios_summary.json
    data/etfs/            yfinance raw price cache
    data/financial_phrasebank/   Financial PhraseBank txt files
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

DATA_DIR: Path = PROJECT_ROOT / "data"
OUTPUTS_DIR: Path = PROJECT_ROOT / "outputs"
DOCS_DIR: Path = PROJECT_ROOT / "docs"
NOTEBOOKS_DIR: Path = PROJECT_ROOT / "notebooks"

# Module-specific output dirs (created on demand by ``ensure_dirs()``).
ARTIFACTS_DIR: Path = OUTPUTS_DIR
M2_OUTPUTS_DIR: Path = OUTPUTS_DIR / "m2"
M3_OUTPUTS_DIR: Path = OUTPUTS_DIR / "m3"
MODELS_DIR: Path = OUTPUTS_DIR / "models"

# Named data assets (raw inputs).
PHRASEBANK_DIR: Path = DATA_DIR / "financial_phrasebank"
PHRASEBANK_CSV: Path = DATA_DIR / "financial_phrasebank.csv"
ETF_DATA_DIR: Path = DATA_DIR / "etfs"
ETF_PRICES_RAW: Path = ETF_DATA_DIR / "etf_prices_raw.parquet"

# Named M2 artefacts (read by M3 and EDA).
M2_PRICES_PARQUET: Path = M2_OUTPUTS_DIR / "prices.parquet"
M2_RETURNS_PARQUET: Path = M2_OUTPUTS_DIR / "returns.parquet"
M2_LOG_RETURNS_PARQUET: Path = M2_OUTPUTS_DIR / "log_returns_full.parquet"
M2_MU_PKL: Path = M2_OUTPUTS_DIR / "mu.pkl"
M2_COV_PKL: Path = M2_OUTPUTS_DIR / "cov_ledoit_wolf.pkl"

# Named M3 artefacts.
M3_WEIGHTS_PARQUET: Path = M3_OUTPUTS_DIR / "weights.parquet"
M3_SUMMARY_JSON: Path = M3_OUTPUTS_DIR / "portfolios_summary.json"


def ensure_dirs() -> None:
    """Create all writable output directories if missing. Idempotent."""
    for d in (OUTPUTS_DIR, M2_OUTPUTS_DIR, M3_OUTPUTS_DIR, MODELS_DIR):
        d.mkdir(parents=True, exist_ok=True)


__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR",
    "OUTPUTS_DIR",
    "DOCS_DIR",
    "NOTEBOOKS_DIR",
    "ARTIFACTS_DIR",
    "M2_OUTPUTS_DIR",
    "M3_OUTPUTS_DIR",
    "MODELS_DIR",
    "PHRASEBANK_DIR",
    "PHRASEBANK_CSV",
    "ETF_DATA_DIR",
    "ETF_PRICES_RAW",
    "M2_PRICES_PARQUET",
    "M2_RETURNS_PARQUET",
    "M2_LOG_RETURNS_PARQUET",
    "M2_MU_PKL",
    "M2_COV_PKL",
    "M3_WEIGHTS_PARQUET",
    "M3_SUMMARY_JSON",
    "ensure_dirs",
]
