#!/usr/bin/env bash
# =============================================================================
#  migrate.sh · Roboadvisor-TFM reorganización
#  Generado por Claude Cowork · 2026-05-12
#  Plan de referencia: REORGANIZATION_PLAN.md (Juan, 2026-05-12)
#
#  EJECUCIÓN:
#    cd C:\Users\juanl\OneDrive\Developer\Roboadvisor-TFM   # (desde Git Bash)
#    bash migrate.sh
#
#  Qué hace este script:
#    1. Crea la estructura de carpetas objetivo
#    2. Mueve archivos con git mv (preserva historial)
#    3. Genera migration_log.txt, AMBIGUOUS_FILES.md, PATH_UPDATES_PENDING.md
#    4. Elimina directorios vacíos
#    5. Hace el commit final
#
#  Lo que NO hace:
#    - No toca los archivos marcados FLAG (§3 del plan)
#    - No actualiza rutas en código (§4 del plan, fase manual de Juan)
#    - No modifica README.md
# =============================================================================

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"
LOG="$REPO_ROOT/migration_log.txt"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

log()  { echo "$1" | tee -a "$LOG"; }
ok()   { log "[OK]   git mv '$1'  →  '$2'"; }
skip() { log "[SKIP] '$1' — no existe en el repo"; }
flag() { log "[FLAG] '$1' — §3 ambiguo, no movido"; }
unmp() { log "[UNMAPPED] '$1' — fuera del plan, dejado en su lugar"; }
err()  { log "[ERR]  $1"; }

do_mv() {
  local src="$1" dst="$2"
  if git ls-files --error-unmatch "$src" &>/dev/null 2>&1; then
    git mv "$src" "$dst" && ok "$src" "$dst" || err "git mv '$src' '$dst' falló"
  elif [ -e "$src" ]; then
    # Existe en disco pero no en git (untracked) — mover con mv
    mkdir -p "$(dirname "$dst")"
    mv "$src" "$dst" && log "[MV-UNTRACKED] '$src'  →  '$dst' (no estaba en git)"
  else
    skip "$src"
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Init log
# ─────────────────────────────────────────────────────────────────────────────

cat > "$LOG" << LOGHEADER
# Migration Log · Roboadvisor-TFM reorganización
# Inicio: $TIMESTAMP
# Plan: REORGANIZATION_PLAN.md (Juan, 2026-05-12)
# Ejecutado por: Claude Cowork vía migrate.sh
#
# Formato:
#   [OK]           git mv exitoso
#   [MV-UNTRACKED] archivo existía en disco pero no en git (movido con mv)
#   [SKIP]         archivo no existe en origen
#   [FLAG]         archivo ambiguo §3, no tocado
#   [UNMAPPED]     archivo fuera del plan, no tocado
#   [ERR]          error en la operación

LOGHEADER

log "## Paso 1 · Crear estructura de carpetas"

mkdir -p \
  docs/memorias \
  docs/figuras \
  docs/referencias \
  docs/mifid \
  outputs/m1/personas \
  outputs/m2 \
  outputs/m3 \
  data/financial_phrasebank \
  data/etfs \
  scripts \
  tests/m3_portfolio \
  src/m3_portfolio \
  notebooks

log "[OK] Carpetas creadas"

# ─────────────────────────────────────────────────────────────────────────────
# §2.1 Archivos en raíz
# ─────────────────────────────────────────────────────────────────────────────

log ""
log "## §2.1 Archivos en raíz"

do_mv "TFM_Fase0_Diseno_Alcance.pdf"         "docs/fase0_diseno_alcance.pdf"
do_mv "TFM_Fase0_Diseno_Alcance.docx"        "docs/fase0_diseno_alcance.docx"
do_mv "tfm-checklist.html"                   "docs/tfm_checklist.html"
do_mv "guia_plantilla_mifid_test.md"         "docs/mifid/guia_plantilla_mifid_test.md"
do_mv "Pipeline_M1_Infografia.png"           "docs/figuras/pipeline_m1_infografia.png"
do_mv "Pipeline_M1_Infografia_v1.1.png"      "docs/figuras/pipeline_m1_infografia_v1.1.png"
do_mv "Financial Phrasebank EDA.html"        "docs/referencias/financial_phrasebank_eda.html"
do_mv "Financial_Phrasebank_Manual.pdf"      "docs/referencias/financial_phrasebank_manual.pdf"
do_mv "informe_eda_financial_phrasebank.pdf" "docs/memorias/informe_eda_financial_phrasebank.pdf"
do_mv "train-00000-of-00001.parquet"         "data/financial_phrasebank/train-00000-of-00001.parquet"

flag "financial_phrasebank.py"
flag "databases.ipynb"

# ─────────────────────────────────────────────────────────────────────────────
# §2.2 notebooks/
# ─────────────────────────────────────────────────────────────────────────────

log ""
log "## §2.2 notebooks/"

do_mv "notebooks/financial_phrasebank.ipynb"       "notebooks/m1_financial_phrasebank.ipynb"
do_mv "notebooks/M1_nlp_profiling.ipynb"           "notebooks/m1_nlp_profiling.ipynb"
do_mv "notebooks/versiones/_build_m1_notebook.py"  "scripts/build_notebook_m1.py"

# eda_etfs_ucits.ipynb no está en el mapping → UNMAPPED
unmp "notebooks/eda_etfs_ucits.ipynb"

flag "notebooks/_cells/ (01_setup.py … 09_validate.py)"

# ─────────────────────────────────────────────────────────────────────────────
# §2.3 src/ (sin cambios)
# ─────────────────────────────────────────────────────────────────────────────

log ""
log "## §2.3 src/ (sin cambios)"
log "[INFO] src/m1_profiling.py permanece en su lugar"

# ─────────────────────────────────────────────────────────────────────────────
# §2.4 ETFs/ (raíz)
# ─────────────────────────────────────────────────────────────────────────────

log ""
log "## §2.4 ETFs/ (archivos raíz)"

do_mv "ETFs/M2_seleccion_universo.ipynb"      "notebooks/m2_seleccion_universo.ipynb"
do_mv "ETFs/build_memoria.py"                 "scripts/build_memoria_m2.py"
do_mv "ETFs/Informe_M2_EDA_30ETFs.docx"       "docs/memorias/memoria_m2_etfs.docx"
do_mv "ETFs/Memoria_EDA_ETFs_UCITS.pdf"       "docs/memorias/memoria_m2_etfs.pdf"
do_mv "ETFs/prices.parquet"                   "outputs/m2/prices.parquet"
do_mv "ETFs/returns.parquet"                  "outputs/m2/returns.parquet"
do_mv "ETFs/mu.pkl"                           "outputs/m2/mu.pkl"
do_mv "ETFs/cov_ledoit_wolf.pkl"              "outputs/m2/cov_ledoit_wolf.pkl"
do_mv "ETFs/output.png"                       "outputs/m2/output.png"

flag "ETFs/Cell 4.csv"

# ─────────────────────────────────────────────────────────────────────────────
# §2.5 ETFs/data/
# ─────────────────────────────────────────────────────────────────────────────

log ""
log "## §2.5 ETFs/data/"

do_mv "ETFs/data/etf_prices_raw.parquet"  "data/etfs/etf_prices_raw.parquet"
do_mv "ETFs/data/selected_etfs.json"      "outputs/m2/selected_etfs.json"
do_mv "ETFs/data/spy_prices.parquet"      "outputs/m2/spy_prices.parquet"

flag "ETFs/data/log_returns_full.parquet"
flag "ETFs/data/returns_selected.parquet"
flag "ETFs/data/mu_expected_returns.csv"
flag "ETFs/data/cov_matrix_lw.npy"

# ─────────────────────────────────────────────────────────────────────────────
# §2.6 MiFiD/
# ─────────────────────────────────────────────────────────────────────────────

log ""
log "## §2.6 MiFiD/"

do_mv "MiFiD/dataset_documentacion.md"                        "docs/mifid/dataset_documentacion.md"
do_mv "MiFiD/deep-research-report.md"                        "docs/mifid/deep_research_report.md"
do_mv "MiFiD/personas_generator.py"                          "scripts/generate_personas.py"
do_mv "MiFiD/personas_sinteticas_M1_plantilla_c.json"        "outputs/m1/personas/personas_sinteticas_M1_plantilla_c.json"
do_mv "MiFiD/personas_sinteticas_M1_plantilla_c.xlsx"        "outputs/m1/personas/personas_sinteticas_M1_plantilla_c.xlsx"

# ─────────────────────────────────────────────────────────────────────────────
# §2.7 roboadvisor/
# ─────────────────────────────────────────────────────────────────────────────

log ""
log "## §2.7 roboadvisor/"

# m3_portfolio package
do_mv "roboadvisor/m3_portfolio/__init__.py"    "src/m3_portfolio/__init__.py"
do_mv "roboadvisor/m3_portfolio/base.py"        "src/m3_portfolio/base.py"
do_mv "roboadvisor/m3_portfolio/portfolio.py"   "src/m3_portfolio/portfolio.py"
do_mv "roboadvisor/m3_portfolio/min_variance.py""src/m3_portfolio/min_variance.py"
do_mv "roboadvisor/m3_portfolio/max_sharpe.py"  "src/m3_portfolio/max_sharpe.py"
do_mv "roboadvisor/m3_portfolio/hrp.py"         "src/m3_portfolio/hrp.py"
do_mv "roboadvisor/m3_portfolio/equal_weight.py""src/m3_portfolio/equal_weight.py"
do_mv "roboadvisor/m3_portfolio/constraints.py" "src/m3_portfolio/constraints.py"
do_mv "roboadvisor/m3_portfolio/validators.py"  "src/m3_portfolio/validators.py"
do_mv "roboadvisor/m3_portfolio/_build.py"      "scripts/build_m3_package.py"

# notebooks
do_mv "roboadvisor/notebooks/M3_optimizacion_carteras.ipynb" "notebooks/m3_optimizacion_carteras.ipynb"
do_mv "roboadvisor/notebooks/_build_notebook.py"             "scripts/build_notebook_m3.py"

# tests
do_mv "roboadvisor/tests/conftest.py"           "tests/m3_portfolio/conftest.py"
do_mv "roboadvisor/tests/test_optimizers.py"    "tests/m3_portfolio/test_optimizers.py"
do_mv "roboadvisor/tests/test_constraints.py"   "tests/m3_portfolio/test_constraints.py"
do_mv "roboadvisor/tests/test_validators.py"    "tests/m3_portfolio/test_validators.py"

# data/m3_outputs
do_mv "roboadvisor/data/m3_outputs/portfolios_summary.json"  "outputs/m3/portfolios_summary.json"
do_mv "roboadvisor/data/m3_outputs/weights.parquet"          "outputs/m3/weights.parquet"
do_mv "roboadvisor/data/m3_outputs/Memoria_M3.md"            "docs/memorias/memoria_m3.md"
do_mv "roboadvisor/data/m3_outputs/Memoria_M3.pdf"           "docs/memorias/memoria_m3.pdf"
do_mv "roboadvisor/data/m3_outputs/build_memoria_m3.py"      "scripts/build_memoria_m3.py"

# ─────────────────────────────────────────────────────────────────────────────
# §2.8 outputs/ (estructura actual)
# ─────────────────────────────────────────────────────────────────────────────

log ""
log "## §2.8 outputs/ (estructura actual)"

do_mv "outputs/Memoria_Fase1_TFM.pdf"         "docs/memorias/memoria_fase1.pdf"
do_mv "outputs/Memoria_M1_NLP_TFM.pdf"        "docs/memorias/memoria_m1_nlp.pdf"
do_mv "outputs/financial_phrasebank.csv"       "outputs/m1/financial_phrasebank.csv"
do_mv "outputs/financial_phrasebank_clean.csv" "outputs/m1/financial_phrasebank_clean.csv"

# FinancialPhraseBank: las txts están anidadas un nivel extra en el repo real
# Estructura real: outputs/FinancialPhraseBank-v1.0/FinancialPhraseBank-v1.0/Sentences_*.txt
for txt in Sentences_AllAgree Sentences_75Agree Sentences_66Agree Sentences_50Agree; do
  NESTED="outputs/FinancialPhraseBank-v1.0/FinancialPhraseBank-v1.0/${txt}.txt"
  FLAT="outputs/FinancialPhraseBank-v1.0/${txt}.txt"
  if git ls-files --error-unmatch "$NESTED" &>/dev/null 2>&1 || [ -e "$NESTED" ]; then
    do_mv "$NESTED" "data/financial_phrasebank/${txt}.txt"
  elif git ls-files --error-unmatch "$FLAT" &>/dev/null 2>&1 || [ -e "$FLAT" ]; then
    do_mv "$FLAT" "data/financial_phrasebank/${txt}.txt"
  else
    skip "$txt.txt"
  fi
done

# Archivos extras dentro de FinancialPhraseBank-v1.0 (License.txt, README.txt, __MACOSX)
for extra in \
  "outputs/FinancialPhraseBank-v1.0/FinancialPhraseBank-v1.0/License.txt" \
  "outputs/FinancialPhraseBank-v1.0/FinancialPhraseBank-v1.0/README.txt"; do
  if [ -e "$extra" ]; then
    unmp "$extra"
  fi
done

do_mv "outputs/m1_outputs/profile_thresholds.json"       "outputs/m1/profile_thresholds.json"
do_mv "outputs/m1_outputs/synthetic_test_cases.csv"      "outputs/m1/synthetic_test_cases.csv"
do_mv "outputs/m1_outputs/validation_results.csv"        "outputs/m1/validation_results.csv"
do_mv "outputs/m1_outputs/finbert_confusion_matrix.png"  "outputs/m1/finbert_confusion_matrix.png"

# ─────────────────────────────────────────────────────────────────────────────
# §2.9 Eliminar directorios vacíos (o con sólo flags/unmapped)
# ─────────────────────────────────────────────────────────────────────────────

log ""
log "## §2.9 Limpiar directorios vacíos"

clean_dir() {
  local dir="$1"
  if [ -d "$dir" ]; then
    # Contar archivos no ocultos y no .gitkeep
    local count
    count=$(find "$dir" -not -path '*/.git/*' -not -name '.gitkeep' -type f 2>/dev/null | wc -l)
    if [ "$count" -eq 0 ]; then
      git rm -r --cached "$dir" 2>/dev/null || true
      rm -rf "$dir"
      log "[RMDIR] '$dir' — eliminado (vacío)"
    else
      log "[SKIP-RMDIR] '$dir' — aún tiene $count archivo(s) (flags/unmapped), no eliminado"
      find "$dir" -not -path '*/.git/*' -type f | while read -r f; do
        log "          → $f"
      done
    fi
  else
    log "[SKIP-RMDIR] '$dir' — no existe"
  fi
}

# Directorios del plan §2.9:
clean_dir "outputs/FinancialPhraseBank-v1.0/__MACOSX"
clean_dir "outputs/FinancialPhraseBank-v1.0/FinancialPhraseBank-v1.0"
clean_dir "outputs/FinancialPhraseBank-v1.0"
clean_dir "outputs/m1_outputs"
clean_dir "roboadvisor/m3_portfolio/__pycache__"
clean_dir "roboadvisor/tests/__pycache__"
clean_dir "roboadvisor/.pytest_cache"
clean_dir "roboadvisor/m3_portfolio"
clean_dir "roboadvisor/notebooks"
clean_dir "roboadvisor/tests"
clean_dir "roboadvisor/data/m3_outputs"
clean_dir "roboadvisor/data"
clean_dir "roboadvisor"
clean_dir "ETFs/data"
clean_dir "ETFs"
clean_dir "MiFiD"
clean_dir "notebooks/versiones"
# _cells: dejar para Juan (§3)

# ─────────────────────────────────────────────────────────────────────────────
# Generar AMBIGUOUS_FILES.md
# ─────────────────────────────────────────────────────────────────────────────

log ""
log "## Generando AMBIGUOUS_FILES.md"

cat > AMBIGUOUS_FILES.md << 'AMBEOF'
# Archivos ambiguos · revisión manual de Juan

Generado por `migrate.sh` · 2026-05-12
Estos archivos **no han sido movidos**. Juan debe revisar cada uno y decidir.

---

## §3.1 Posibles duplicados M2 (ETFs/ vs ETFs/data/)

| Archivo | Hipótesis | Acción a verificar |
|---|---|---|
| `ETFs/data/returns_selected.parquet` | ¿Versión vieja de `ETFs/returns.parquet`? | Comparar timestamps y shape. Si idéntico → eliminar. Si distinto → `outputs/m2/returns_selected.parquet` y documentar. |
| `ETFs/data/log_returns_full.parquet` | ¿Log returns del universo pre-selección? | Si sí → `outputs/m2/log_returns_full.parquet` y documentar. |
| `ETFs/data/mu_expected_returns.csv` | ¿Export CSV de `ETFs/mu.pkl`? | Si es export legible → `outputs/m2/mu_expected_returns.csv`. Si versión vieja → eliminar. |
| `ETFs/data/cov_matrix_lw.npy` | ¿Versión NumPy de `ETFs/cov_ledoit_wolf.pkl`? | Mismo criterio. |

**Comando para comparar parquets:**
```bash
python -c "
import pandas as pd
a = pd.read_parquet('outputs/m2/returns.parquet')
b = pd.read_parquet('ETFs/data/returns_selected.parquet')
print('Shape A:', a.shape, '| Shape B:', b.shape)
print('Iguales:', a.equals(b))
"
```

---

## §3.2 Archivos sueltos sin contexto claro

| Archivo | Hipótesis | Acción |
|---|---|---|
| `financial_phrasebank.py` (raíz) | Script auxiliar antiguo, posiblemente reemplazado por el notebook | Inspeccionar: ¿obsoleto → eliminar? ¿reutilizable → `scripts/`? |
| `databases.ipynb` (raíz) | Notebook exploratorio inicial sin uso aparente | Inspeccionar: → `notebooks/exploratorio/` o eliminar |
| `ETFs/Cell 4.csv` | Probablemente export accidental de una celda | Verificar contenido. Si es residuo → eliminar. |
| `notebooks/_cells/01_setup.py … 09_validate.py` | Celdas sueltas del notebook M1 | Si el notebook ya está construido vía `build_notebook_m1.py`, este directorio puede eliminarse. Confirmar. |
| `notebooks/eda_etfs_ucits.ipynb` | No estaba en el mapping del plan | ¿Es el M2 EDA original? Si sí → renombrar a `notebooks/m2_eda_etfs_ucits.ipynb`. |

---

## §3.3 Archivos extras dentro de FinancialPhraseBank-v1.0

| Archivo | Hipótesis | Acción |
|---|---|---|
| `outputs/FinancialPhraseBank-v1.0/FinancialPhraseBank-v1.0/License.txt` | Licencia del dataset | Mover a `data/financial_phrasebank/License.txt` o eliminar del repo (no es dato). |
| `outputs/FinancialPhraseBank-v1.0/FinancialPhraseBank-v1.0/README.txt` | README del dataset | Igual que arriba. |
| `outputs/FinancialPhraseBank-v1.0/__MACOSX/` | Artefacto macOS de descompresión | Eliminar: `git rm -r 'outputs/FinancialPhraseBank-v1.0/__MACOSX'` |

AMBEOF

git add AMBIGUOUS_FILES.md && log "[OK] AMBIGUOUS_FILES.md generado y añadido a git"

# ─────────────────────────────────────────────────────────────────────────────
# Generar PATH_UPDATES_PENDING.md
# ─────────────────────────────────────────────────────────────────────────────

log ""
log "## Generando PATH_UPDATES_PENDING.md"

cat > PATH_UPDATES_PENDING.md << 'PATHEOF'
# Actualizaciones de rutas pendientes · revisión manual de Juan

Generado por `migrate.sh` · 2026-05-12
**Esta fase es manual.** Actualizar las rutas archivo a archivo,
ejecutando el notebook tras cada cambio para verificar.

---

## Archivos con rutas hardcodeadas confirmadas (§4.1 del plan)

| Archivo | Ruta vieja | Ruta nueva |
|---|---|---|
| `notebooks/m3_optimizacion_carteras.ipynb` | `PACKAGE_ROOT.parent / "ETFs"` → `returns.parquet`, `mu.pkl`, `cov_ledoit_wolf.pkl` | `PROJECT_ROOT / "outputs" / "m2"` |
| `notebooks/m1_nlp_profiling.ipynb` | rutas a `outputs/m1_outputs/` | `outputs/m1/` |
| `notebooks/m1_financial_phrasebank.ipynb` | posible referencia a `outputs/FinancialPhraseBank-v1.0/` o CSV en raíz | `data/financial_phrasebank/` |
| `notebooks/m2_seleccion_universo.ipynb` | rutas a `ETFs/data/` y `ETFs/` (raíz) | `outputs/m2/` y `data/etfs/` para inputs |
| `notebooks/m2_eda_etfs_ucits.ipynb` | rutas similares a M2 | igual que arriba |
| `src/m3_portfolio/*.py` | inspeccionar imports relativos | sin cambios si solo lógica matemática |
| `scripts/build_memoria_m2.py` | rutas a `ETFs/data/` | `outputs/m2/` |
| `scripts/build_memoria_m3.py` | rutas a `roboadvisor/data/m3_outputs/` | `outputs/m3/` y `docs/memorias/` |

---

## Patrón recomendado para todas las rutas (§4.2 del plan)

Añadir al inicio de cada notebook/script:

```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # ajustar según profundidad
DATA    = PROJECT_ROOT / "data"
OUTPUTS = PROJECT_ROOT / "outputs"
DOCS    = PROJECT_ROOT / "docs"

M2_OUT  = OUTPUTS / "m2"
M3_OUT  = OUTPUTS / "m3"
FPB_DATA = DATA / "financial_phrasebank"
ETF_DATA = DATA / "etfs"
```

---

## Checklist post-actualización

- [ ] `notebooks/m3_optimizacion_carteras.ipynb` ejecuta end-to-end sin errores de path
- [ ] `notebooks/m1_nlp_profiling.ipynb` ejecuta end-to-end
- [ ] `notebooks/m1_financial_phrasebank.ipynb` ejecuta end-to-end
- [ ] `notebooks/m2_seleccion_universo.ipynb` ejecuta end-to-end
- [ ] `notebooks/m2_eda_etfs_ucits.ipynb` (o equivalente) ejecuta end-to-end
- [ ] `pytest tests/` pasa
- [ ] Borrar `outputs/m1/`, `outputs/m2/`, `outputs/m3/` y re-ejecutar notebooks reconstruye todo

PATHEOF

git add PATH_UPDATES_PENDING.md && log "[OK] PATH_UPDATES_PENDING.md generado y añadido a git"

# ─────────────────────────────────────────────────────────────────────────────
# Nota sobre README
# ─────────────────────────────────────────────────────────────────────────────

log ""
log "## Pendiente (manual)"
log "[NOTE] README.md: actualizar sección 'Estructura del Proyecto' para reflejar nueva estructura."
log "[NOTE] La sección actual describe 'data/raw/' y 'data/processed/' que ya no aplican."

# ─────────────────────────────────────────────────────────────────────────────
# Commit final
# ─────────────────────────────────────────────────────────────────────────────

log ""
log "## Commit final"

git add migration_log.txt

git add -A 2>/dev/null || true

git commit -m "refactor: reorganize project structure (data/outputs/docs split). See migration_log.txt"
log "[OK] Commit realizado"

log ""
log "## Migración completada: $(date '+%Y-%m-%d %H:%M:%S')"
log ""
log "Próximos pasos para Juan:"
log "  1. Revisar AMBIGUOUS_FILES.md y decidir sobre los archivos FLAG"
log "  2. Actualizar rutas en notebooks/scripts (PATH_UPDATES_PENDING.md)"
log "  3. Actualizar README.md sección 'Estructura del Proyecto'"
log "  4. Ejecutar: pytest tests/"
log "  5. Test de reproducibilidad: borrar outputs/ y re-ejecutar los 5 notebooks"

echo ""
echo "✅  migrate.sh completado. Revisa migration_log.txt para el detalle completo."
