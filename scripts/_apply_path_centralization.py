"""One-off migration: inject `roboadvisor_paths` into the 5 notebooks.

Adds a bootstrap cell that wires ``sys.path`` to ``src/`` and imports
``roboadvisor_paths as PATHS``. Then surgically rewrites the
path-defining lines so every notebook reads/writes via the shared
registry. Idempotent: rerunning is a no-op.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

NOTEBOOK_DIR = Path(__file__).resolve().parent.parent / "notebooks"

BOOTSTRAP_MARK = "# --- roboadvisor_paths bootstrap (auto-inserted) ---"
BOOTSTRAP_SOURCE = f"""{BOOTSTRAP_MARK}
import sys
from pathlib import Path as _P

_repo = _P.cwd().resolve()
while _repo != _repo.parent and not (_repo / "src" / "roboadvisor_paths.py").exists():
    _repo = _repo.parent
_src = _repo / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

import roboadvisor_paths as PATHS  # noqa: E402
PATHS.ensure_dirs()
"""


def _has_bootstrap(nb: dict) -> bool:
    for c in nb["cells"]:
        if c["cell_type"] == "code" and BOOTSTRAP_MARK in "".join(c["source"]):
            return True
    return False


def _inject_bootstrap(nb: dict) -> None:
    cell = {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": BOOTSTRAP_SOURCE.splitlines(keepends=True),
    }
    # Insert before the first existing code cell so PATHS is available
    # everywhere downstream.
    for idx, c in enumerate(nb["cells"]):
        if c["cell_type"] == "code":
            nb["cells"].insert(idx, cell)
            return
    nb["cells"].insert(0, cell)


def _patch_source(cell: dict, replacements: Iterable[tuple[str, str]]) -> bool:
    src = "".join(cell["source"])
    new = src
    for old, repl in replacements:
        new = re.sub(old, repl, new)
    if new != src:
        cell["source"] = new.splitlines(keepends=True)
        return True
    return False


def patch_notebook(path: Path, replacements: Iterable[tuple[str, str]]) -> None:
    nb = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    if not _has_bootstrap(nb):
        _inject_bootstrap(nb)
        changed = True
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        if _patch_source(cell, replacements):
            changed = True
    if changed:
        path.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  patched: {path.name}")
    else:
        print(f"  unchanged: {path.name}")


M1_PHRASEBANK_PATCHES = [
    (r"DATA_PATH\s*=\s*Path\('financial_phrasebank\.csv'\)",
     "DATA_PATH = PATHS.PHRASEBANK_CSV"),
    (r"OUTPUT_PATH\s*=\s*Path\('financial_phrasebank_clean\.csv'\)",
     "OUTPUT_PATH = PATHS.DATA_DIR / 'financial_phrasebank_clean.csv'"),
]

M1_NLP_PATCHES = [
    (r"PROJECT_ROOT\s*=\s*Path\.cwd\(\)\.parent\s+if\s+Path\.cwd\(\)\.name\s*==\s*\"notebooks\"\s+else\s+Path\.cwd\(\)",
     "PROJECT_ROOT = PATHS.PROJECT_ROOT"),
    (r'PHRASEBANK_PATH\s*=\s*PROJECT_ROOT\s*/\s*"financial_phrasebank\.csv"',
     "PHRASEBANK_PATH = PATHS.PHRASEBANK_CSV"),
    (r'OUTPUTS_DIR\s*=\s*PROJECT_ROOT\s*/\s*"outputs"\s*/\s*"m1_outputs"',
     'OUTPUTS_DIR = PATHS.OUTPUTS_DIR / "m1_outputs"'),
]

M2_SEL_PATCHES = [
    (r"DATA_DIR\s*=\s*Path\('data'\)\s*\nDATA_DIR\.mkdir\(exist_ok=True\)",
     "DATA_DIR = PATHS.M2_OUTPUTS_DIR  # outputs go here; raw cache uses PATHS.ETF_PRICES_RAW"),
    (r"CACHE_PATH\s*=\s*DATA_DIR\s*/\s*'etf_prices_raw\.parquet'",
     "CACHE_PATH = PATHS.ETF_PRICES_RAW"),
    (r"spy_path\s*=\s*DATA_DIR\s*/\s*'spy_prices\.parquet'",
     "spy_path = PATHS.ETF_DATA_DIR / 'spy_prices.parquet'"),
]

M2_EDA_PATCHES = [
    (r"DATA_DIR\s*=\s*Path\('\.'\)\s*\nDATA_DIR\.mkdir\(exist_ok=True\)",
     "DATA_DIR = PATHS.M2_OUTPUTS_DIR"),
]

M3_PATCHES = [
    (r"NOTEBOOK_DIR\s*=\s*Path\.cwd\(\)\s*\nPACKAGE_ROOT\s*=\s*NOTEBOOK_DIR\.parent\s*\nif\s+str\(PACKAGE_ROOT\)\s+not\s+in\s+sys\.path:\s*\n\s*sys\.path\.insert\(0,\s*str\(PACKAGE_ROOT\)\)",
     "NOTEBOOK_DIR = PATHS.NOTEBOOKS_DIR\nPACKAGE_ROOT = PATHS.PROJECT_ROOT  # legacy alias"),
    (r'ETF_DIR\s*=\s*PACKAGE_ROOT\.parent\s*/\s*"ETFs"',
     "ETF_DIR = PATHS.M2_OUTPUTS_DIR"),
    (r'OUTPUT_DIR\s*=\s*PACKAGE_ROOT\s*/\s*"data"\s*/\s*"m3_outputs"',
     "OUTPUT_DIR = PATHS.M3_OUTPUTS_DIR"),
]


def main() -> None:
    print(f"Notebook dir: {NOTEBOOK_DIR}")
    patch_notebook(NOTEBOOK_DIR / "m1_financial_phrasebank.ipynb", M1_PHRASEBANK_PATCHES)
    patch_notebook(NOTEBOOK_DIR / "m1_nlp_profiling.ipynb", M1_NLP_PATCHES)
    patch_notebook(NOTEBOOK_DIR / "m2_seleccion_universo.ipynb", M2_SEL_PATCHES)
    patch_notebook(NOTEBOOK_DIR / "m2_eda_etfs_ucits.ipynb", M2_EDA_PATCHES)
    patch_notebook(NOTEBOOK_DIR / "m3_optimizacion_carteras.ipynb", M3_PATCHES)


if __name__ == "__main__":
    main()
