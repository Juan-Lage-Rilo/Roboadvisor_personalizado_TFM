# §1.1 — Imports con install-guard
from __future__ import annotations

import json
import logging
import random
import sys
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

_required = {
    "transformers": "transformers",
    "torch":        "torch",
    "tqdm":         "tqdm",
    "pandas":       "pandas",
    "numpy":        "numpy",
    "sklearn":      "scikit-learn",
    "matplotlib":   "matplotlib",
    "seaborn":      "seaborn",
}
_missing = []
for mod, pkg in _required.items():
    try:
        __import__(mod)
    except ImportError:
        _missing.append(pkg)
if _missing:
    print(
        "[!] Faltan paquetes: "
        + ", ".join(_missing)
        + "\n    Instala con:\n    pip install "
        + " ".join(_missing)
        + " pysentimiento sentencepiece sacremoses"
    )

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
try:
    import torch
    _HAS_TORCH = True
except ImportError:
    torch = None  # type: ignore[assignment]
    _HAS_TORCH = False
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from tqdm.auto import tqdm

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("M1")

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
if _HAS_TORCH:
    torch.manual_seed(SEED)
    DEVICE = 0 if torch.cuda.is_available() else -1
else:
    DEVICE = -1
DEVICE_LABEL = "cuda" if DEVICE == 0 else "cpu"
logger.info("Device: %s (torch %s)", DEVICE_LABEL,
            "OK" if _HAS_TORCH else "MISSING -> mock mode")

plt.style.use("dark_background")
sns.set_palette("magma")

PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
PHRASEBANK_PATH = PROJECT_ROOT / "financial_phrasebank.csv"
OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "m1_outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

logger.info("Project root: %s", PROJECT_ROOT)
logger.info("Outputs dir : %s", OUTPUTS_DIR)
