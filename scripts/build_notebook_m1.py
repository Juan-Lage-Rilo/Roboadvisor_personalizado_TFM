# -*- coding: utf-8 -*-
"""Build M1_nlp_profiling.ipynb. Avoids nested triple-quote issues by storing
each cell's source as a list of lines and reading code-cell bodies from
external .py files in ./_cells/."""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf

HERE = Path(__file__).parent
CELLS_DIR = HERE / "_cells"
OUT = HERE / "M1_nlp_profiling.ipynb"

nb = nbf.v4.new_notebook()
cells = []


def md(text: str) -> None:
    cells.append(nbf.v4.new_markdown_cell(text))


def code_from(name: str) -> None:
    src = (CELLS_DIR / name).read_text(encoding="utf-8")
    cells.append(nbf.v4.new_code_cell(src.rstrip("\n")))


# ---------- Header ----------
md(
    "# M1 · NLP Profiling — Robo-advisor TFM\n\n"
    "Pipeline NLP dual para clasificar el **perfil de riesgo del inversor** "
    "(conservador / moderado / agresivo) combinando cuestionario MiFID II y "
    "análisis de respuestas en texto libre.\n\n"
    "**Stack**: FinBERT (zero-shot, EN) + RoBERTuito (ES nativo) + Opus-MT "
    "(ES→EN) sobre PyTorch CPU.\n\n"
    "**Validación**: Financial PhraseBank (`allagree`, ~2.264 frases) "
    "— objetivo F1-macro ≥ 0.85.\n\n"
    "**Fusión final**: prudencia asimétrica (el NLP solo puede "
    "*bajar* el perfil, nunca subirlo)."
)

md("## §1 · Setup & imports")
code_from("01_setup.py")

md(
    "## §2 · Carga de modelos (lazy + caché)\n\n"
    "Tres pipelines de HuggingFace cacheados en un dict de módulo. "
    "Si alguna descarga falla (red / timeout), se activa un **mock determinista** "
    "vía `_USE_MOCK = True`, manteniendo el resto del notebook ejecutable end-to-end."
)
code_from("02_models.py")

md(
    "## §3 · Funciones de inferencia\n\n"
    "Contrato común: cualquier score de sentimiento se devuelve en `[-1, +1]` "
    "(`+1`=positivo, `-1`=negativo, `0`=neutral, ponderado por la confianza del modelo)."
)
code_from("03_inference.py")

md(
    "## §4 · Validación zero-shot sobre Financial PhraseBank "
    "(`allagree`)\n\n"
    "Subconjunto consensual (~2.264 frases). FinBERT se aplica directamente "
    "sobre el inglés original. Mapping: `score > 0.1 → positive`, "
    "`< -0.1 → negative`, resto `neutral`. **Go/No-Go**: F1-macro ≥ 0.85."
)
code_from("04a_load_pb.py")
code_from("04b_inference.py")
code_from("04c_metrics.py")
code_from("04d_alert.py")

md(
    "## §5 · Reglas de fusión (clasificación de perfil MiFID II)\n\n"
    "Prudencia asimétrica: el NLP **solo puede bajar** el perfil. "
    "Umbrales modulados por la confianza del acuerdo intra-NLP."
)
code_from("05_fusion.py")

md("## §6 · Validación con 20 casos sintéticos")
code_from("06a_synthetic.py")
code_from("06b_assert.py")

md("## §7 · Demo end-to-end (3 personas)")
code_from("07_demo.py")

md("## §8 · Outputs para M3")
code_from("08a_persist.py")
code_from("08b_latency.py")
code_from("08c_checklist.py")

md("## §9 · Validación de integridad del notebook")
code_from("09_validate.py")

nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.10"},
}
nbf.write(nb, OUT)
print(f"Wrote {OUT} with {len(cells)} cells")
