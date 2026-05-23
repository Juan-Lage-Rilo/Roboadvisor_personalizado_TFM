# Context M4 · Backtesting y Validación

> Documento de scope, arquitectura y decisiones de diseño del módulo M4.
> Equivalente conceptual al PROJECT_CONTEXT.md pero acotado al módulo de backtesting.
> Fuente única de verdad para la implementación. Cualquier desviación debe justificarse aquí.

---

## 1. Objetivo y criterio Go/No-Go

**Objetivo:** evaluar el comportamiento histórico fuera de muestra (OOS) de las tres carteras optimizadas en M3, comparándolas contra dos benchmarks estándar (SPY y 60/40), y entregar evidencia cuantitativa de que el roboadvisor aporta valor frente a una asignación naïve.

**Criterio Go/No-Go (Fase 0, contractual):**

> M4 — `Sharpe(cartera_moderada) ≥ Sharpe(benchmark_60_40)` en el periodo walk-forward 2020-2026.

Criterios secundarios heredados de M2/M3:
- Ordenación esperada en OOS: `CAGR_agresivo > CAGR_moderado > CAGR_conservador`.
- Volatilidad realizada por perfil dentro de su cap declarado (8% / 15% / 25%). Si se excede, no es Fail automático: se documenta y se analiza en memoria.

---

## 2. Diseño metodológico

### 2.1 Split temporal (decisión fija, no walk-forward expanding)

| Periodo | Rango | Uso |
|---|---|---|
| **Train** | 2010-01-01 → 2019-12-31 | Estimación de μ, Σ y cálculo de pesos OOS-clean |
| **Test OOS** | 2020-01-01 → 2026-04-30 | Evaluación en M4 (datos que el optimizador nunca vio) |

**Justificación:** la simplificación a un único split fijo (en lugar de walk-forward expanding/rolling) es defendible porque:
- El periodo OOS contiene tres episodios de estrés real (COVID 03/2020, bear de 2022, subida de tipos 2022-2023) — material de sobra para la memoria.
- Mantiene la arquitectura simple y reproducible, evitando la complejidad de re-optimización en cada ventana.
- Coherente con el alcance de Fase 0 ("backtesting walk-forward con rebalanceo trimestral") — el rebalanceo es la pieza dinámica; la optimización se hace una vez.

**Limitación a documentar en memoria:** los pesos son estáticos durante OOS. No se reoptimiza ante cambios estructurales del mercado. Se explicita como simplificación deliberada y se contrasta con la posible extensión a walk-forward dinámico como trabajo futuro.

### 2.2 Eliminación del look-ahead bias en la estimación de parámetros

Para garantizar que el optimizador no observe el periodo OOS antes de generar pesos, **M4 ejecuta su propio paso de optimización al inicio del notebook**.

El flujo es:

1. Leer `outputs/m2/returns.parquet`.
2. Truncar a `index ≤ 2019-12-31`.
3. Recalcular μ (media anualizada × `TRADING_DAYS`) y Σ (Ledoit-Wolf) sobre la ventana truncada.
4. Invocar los mismos optimizadores que M3 (`MinVarianceOptimizer`, `MaxSharpeOptimizer`, `HRPOptimizer`, `EqualWeightOptimizer`) con la misma configuración de M3 (`PROFILES`, `MAX_VOL`, `PRIMARY_OPTIMIZER`, `ALTERNATIVE_OPTIMIZER`, `BASELINE_OPTIMIZER`, `RISK_FREE_RATE`).
5. Aplicar la regla de selección de M3 (best Sharpe sujeto a `vol_actual ≤ vol_cap × 1.01`).
6. Persistir el resultado en `outputs/m4/weights_oos_clean.parquet` + `outputs/m4/portfolios_summary_oos_clean.json`.

Esta separación deja a cada módulo con una autoridad distinta:

- **M3** es la autoridad sobre *"qué recomendar hoy"* con todo el histórico (`outputs/m3/weights.parquet`).
- **M4** es la autoridad sobre *"qué se habría recomendado en 2019 y cómo se comportó"* (`outputs/m4/weights_oos_clean.parquet`).

Ambas carteras conviven legítimamente. La separación está explícitamente documentada en el Bloque 9 del notebook M3 y se replica aquí.

### 2.3 Rebalanceo

| Decisión | Valor | Justificación |
|---|---|---|
| Frecuencia | **Trimestral** (último día hábil de cada Q) | Contractual en Fase 0. Compromiso razonable entre coste de transacción (no modelado, pero implícito) y drift de pesos. |
| Política | **Reset a pesos objetivo** | El target weights OOS-clean se restaura. No hay drift permitido más allá del trimestre. |
| Capa adicional opcional | **Drift threshold** | Si entre rebalanceos algún peso supera `|w_actual − w_target| > 0.05`, rebalanceo intra-trimestral. Implementado pero desactivable por flag (`drift_threshold=None`) para reproducibilidad simple. |

### 2.4 Benchmarks

Dos benchmarks, idénticos a M2 §8 para coherencia narrativa:

- **SPY** (S&P 500 US, divisa USD): proxy de la "decisión naïve fácil" — comprar el índice más conocido.
- **BENCH_60_40** = `0.6·CSPX.L + 0.4·IEAG.AS` (sintético, en EUR): proxy académico de cartera diversificada. Mismo universo que el roboadvisor → comparación justa.

Reutilizar `outputs/m2/spy_prices.parquet` y reconstruir el 60/40 dentro de `benchmarks.py` con los retornos de M2 ya en disco (sin nuevas descargas de yfinance).

---

## 3. Estructura del módulo

Replica el patrón `src/m3_portfolio/` + `tests/m3_portfolio/`.

```
src/
└── m4_backtesting/
    ├── __init__.py             ← expone API pública
    ├── engine.py               ← BacktestEngine: aplica pesos sobre returns con rebalanceo
    ├── rebalancer.py           ← helpers: fechas de rebalanceo + drift detection
    ├── benchmarks.py           ← construye equity curves de SPY y 60/40
    ├── metrics.py              ← CAGR, Sharpe, Sortino, max_drawdown, Calmar (puro, sin QuantStats)
    └── weights_generator.py    ← regenera pesos OOS-clean invocando m3_portfolio

notebooks/
└── m4_backtesting.ipynb        ← orquestador: bloques 1-8

tests/
└── m4_backtesting/
    ├── __init__.py
    ├── conftest.py             ← fixtures: returns sintéticos 3 años, pesos ficticios, fechas Q
    ├── test_engine.py          ← invariantes: equity_curve(t=0)=1, no look-ahead, suma pesos=1
    ├── test_rebalancer.py      ← drift > threshold → rebalanceo correcto; alineación Q
    ├── test_metrics.py         ← CAGR/Sharpe/MDD vs valores calculados a mano
    └── test_weights_generator.py ← train_end_date respetado, índice max ≤ 2019-12-31

outputs/
└── m4/
    ├── weights_oos_clean.parquet           ← pesos generados con μ/Σ ≤ 2019-12-31
    ├── portfolios_summary_oos_clean.json   ← summary análogo al de M3
    ├── weights_comparison.parquet          ← side-by-side full vs OOS-clean (narrativa M4)
    ├── equity_curves.parquet               ← cartera por perfil + benchmarks, OOS
    ├── metrics_by_profile.json             ← CAGR, Sharpe, Sortino, MDD, Calmar por perfil y benchmarks
    ├── drawdown_series.parquet             ← serie de drawdown para análisis temporal
    ├── rebalance_log.parquet               ← fechas y pesos en cada rebalanceo (auditable)
    ├── report_conservador.html             ← QuantStats tearsheet OOS
    ├── report_moderado.html
    └── report_agresivo.html

scripts/
└── build_memoria_m4.py                     ← genera PDF de la memoria M4

docs/
└── memorias/
    ├── memoria_m4.md
    └── memoria_m4.pdf
```

---

## 4. Interfaz pública (anclaje del diseño)

### 4.1 `weights_generator.py`

```python
def regenerate_oos_clean_weights(
    returns: pd.DataFrame,
    train_end_date: pd.Timestamp,
    profiles: dict[str, list[str]],
    max_vol: dict[str, float],
    primary_optimizer: dict[str, type],
    alternative_optimizer: dict[str, type],
    baseline_optimizer: type,
    risk_free_rate: float,
    trading_days: int,
) -> dict[str, Portfolio]:
    """Regenera pesos OOS-clean invocando m3_portfolio sobre returns truncados."""
```

Encapsula la lógica de truncar + recalcular μ/Σ + invocar los optimizadores de M3 + aplicar la regla de selección. Las constantes de configuración (`PROFILES`, `MAX_VOL`, etc.) se pasan explícitamente desde el notebook para evitar acoplamiento implícito M3-M4.

### 4.2 `engine.py · BacktestEngine`

```python
from dataclasses import dataclass
from typing import Literal
import pandas as pd

@dataclass
class BacktestResult:
    equity_curve: pd.Series          # base 1.0 al inicio del OOS
    returns: pd.Series               # retornos diarios de la cartera
    weights_history: pd.DataFrame    # pesos efectivos por fecha
    rebalance_dates: list[pd.Timestamp]

class BacktestEngine:
    def __init__(
        self,
        returns: pd.DataFrame,                       # OOS, columnas = tickers
        target_weights: dict[str, float],            # incluye CASH si aplica
        rebalance_freq: Literal["M", "Q", "Y"] = "Q",
        drift_threshold: float | None = None,        # None = solo rebalance por calendar
        rf_annual: float = 0.02,                     # remuneración del cash
        trading_days: int = 252,
    ) -> None: ...

    def run(self) -> BacktestResult: ...
```

### 4.3 `metrics.py · funciones puras`

```python
def cagr(equity: pd.Series, periods_per_year: int = 252) -> float: ...
def annual_vol(returns: pd.Series, periods_per_year: int = 252) -> float: ...
def sharpe_ratio(returns: pd.Series, rf_annual: float = 0.02, periods_per_year: int = 252) -> float: ...
def sortino_ratio(returns: pd.Series, rf_annual: float = 0.02, periods_per_year: int = 252) -> float: ...
def max_drawdown(equity: pd.Series) -> tuple[float, pd.Timestamp, pd.Timestamp]: ...
def calmar_ratio(equity: pd.Series, periods_per_year: int = 252) -> float: ...
def drawdown_series(equity: pd.Series) -> pd.Series: ...
```

**Decisión:** métricas implementadas a mano en `metrics.py` (no se delega en QuantStats) para tener tests deterministas, independencia de versiones, y coherencia exacta con las fórmulas que aparecen en la memoria. QuantStats se usa **solo** para el tearsheet HTML, no para los números canónicos.

### 4.4 `benchmarks.py`

```python
def build_spy_benchmark(oos_start: str, oos_end: str) -> pd.Series:
    """Retornos diarios de SPY desde outputs/m2/spy_prices.parquet."""

def build_60_40_benchmark(returns_m2: pd.DataFrame) -> pd.Series:
    """0.6·CSPX.L + 0.4·IEAG.AS con rebalanceo Q."""
```

---

## 5. Convención de paths

Coherente con `PROJECT_CONTEXT.md`:

```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
M2_OUT = PROJECT_ROOT / "outputs" / "m2"
M3_OUT = PROJECT_ROOT / "outputs" / "m3"
M4_OUT = PROJECT_ROOT / "outputs" / "m4"

# Inputs canónicos
RETURNS_PATH         = M2_OUT / "returns.parquet"
SPY_PATH             = M2_OUT / "spy_prices.parquet"
WEIGHTS_M3_FULL_PATH = M3_OUT / "weights.parquet"          # solo para comparativa narrativa

# Generado por M4 al inicio del notebook (no preexiste)
WEIGHTS_OOS_CLEAN_PATH = M4_OUT / "weights_oos_clean.parquet"
SUMMARY_OOS_CLEAN_PATH = M4_OUT / "portfolios_summary_oos_clean.json"
```

---

## 6. Notebook orquestador (`m4_backtesting.ipynb`)

Estructura por bloques. Filosofía: orquestar y visualizar, no implementar (la lógica vive en `src/m4_backtesting/`). Las celdas markdown no desarrollan teoría — solo comentarios operativos.

| Bloque | Contenido | Output al disco |
|---|---|---|
| **0 · Setup** | Imports, paths, logging | — |
| **1 · Generación de pesos OOS-clean** | Trunca returns a `≤ 2019-12-31`, invoca `weights_generator.regenerate_oos_clean_weights` con la config de M3 | `weights_oos_clean.parquet`, `portfolios_summary_oos_clean.json` |
| **2 · Carga de datos OOS** | `returns_oos`, `weights_oos_clean`, `spy`, `bench_60_40` | — |
| **3 · Configuración del backtest** | Frecuencia (Q), drift threshold (None), rf=2%, fechas OOS | — |
| **4 · Ejecución por perfil** | Tres `BacktestEngine` (conservador, moderado, agresivo) → tres `BacktestResult` | `equity_curves.parquet`, `rebalance_log.parquet` |
| **5 · Benchmarks** | SPY + 60/40 sobre el mismo OOS, añadidos a `equity_curves.parquet` | — |
| **6 · Métricas comparativas** | Tabla CAGR/Sharpe/Sortino/MDD/Calmar de 5 series (3 perfiles + 2 benchmarks) | `metrics_by_profile.json`, `drawdown_series.parquet` |
| **7 · Visualizaciones** | Equity curves superpuestas (log), drawdown plot, distribución de retornos | (imágenes incrustadas) |
| **8 · Tearsheets QuantStats** | `qs.reports.html(returns, benchmark=bench_60_40, output=...)` por perfil | 3 × `report_*.html` |
| **9 · Comparativa pesos full vs OOS-clean** | Tabla side-by-side y delta por activo (narrativa M4) | `weights_comparison.parquet` |
| **10 · Validación final** | Print `[PASS]/[FAIL]` por criterio Go/No-Go | — |

---

## 7. Política de tests (pytest)

Cubre cuatro invariantes mínimos:

1. **No look-ahead en `weights_generator`** — `test_weights_generator.py::test_train_end_date_respected`: el DataFrame que se pasa a los optimizadores tiene `index.max() ≤ train_end_date`.
2. **No look-ahead en el engine** — `test_engine.py::test_no_lookahead`: dada una serie con `NaN` antes del inicio del OOS, la equity curve es invariante (no se leen).
3. **Suma de pesos = 1 ± 1e-6** en cada punto del backtest, incluyendo cash.
4. **Métricas determinísticas** — `test_metrics.py`:
   - Serie de retornos constante r=0 → CAGR=0, Sharpe=NaN gestionado, MDD=0.
   - Serie con drawdown exacto del 10% → MDD ≈ −0.10.
   - Serie con retorno anualizado 5% → CAGR ≈ 0.05.

Comando de aceptación:
```bash
pytest tests/m4_backtesting/ -v
```

---

## 8. Riesgos metodológicos (acotados a M4)

Las decisiones sobre look-ahead, cash weight, rf=2%, long-only y selección entre optimizadores están resueltas en M3 (ver Bloque 9 del notebook M3 y memoria M3). Esta tabla cubre únicamente lo que se gestiona en M4.

| Riesgo | Mitigación |
|---|---|
| **Survivorship bias** en el universo M2 | Reconocer en memoria. Los 9 ETFs supervivientes son los seleccionados; los descartados por iliquidez/historial corto se documentaron en M2. |
| **Sin costes de transacción** | Out-of-scope Fase 0. El rebalanceo trimestral minimiza el impacto en cualquier modelo realista. Mencionar como simplificación en memoria. |
| **QuantStats versión-dependiente** | Métricas canónicas en `metrics.py` propias. QuantStats solo para tearsheet visual. |
| **Pesos estáticos durante OOS** | Documentado como simplificación deliberada (ver §2.1). Trabajo futuro: walk-forward expanding. |

---

## 9. Conexión hacia M5 (opcional)

`BacktestEngine` se diseña como callable sin estado persistente fuera de su input → cualquier app Streamlit puede importarlo y ejecutarlo con pesos arbitrarios. La interfaz fija de `BacktestResult` desacopla la UI del motor.

---

## 10. Definition of Done (M4)

Marcar todos antes de pasar a M5 o cerrar la memoria:

- [ ] `src/m4_backtesting/` implementado, importable, con type hints completos.
- [ ] `pytest tests/m4_backtesting/ -v` pasa al 100%.
- [ ] `notebooks/m4_backtesting.ipynb` ejecuta end-to-end sin errores tras `Restart & Run All`.
- [ ] `outputs/m4/` contiene los 10 artefactos listados en §3.
- [ ] Criterio Go/No-Go evaluado: `Sharpe_moderado` vs `Sharpe_60_40` con veredicto explícito.
- [ ] Ordenación CAGR (`agresivo > moderado > conservador`) reportada.
- [ ] Volatilidad realizada OOS por perfil dentro de su cap (8%/15%/25%) — flag si se excede, no es Fail automático.
- [ ] Sección "Comparativa pesos full vs OOS-clean" en memoria M4 con tabla y comentario.
- [ ] `docs/memorias/memoria_m4.pdf` generada por `scripts/build_memoria_m4.py`.

---

## Apéndice A · Decisiones que NO se toman en M4

Para evitar scope creep:

- ❌ Re-optimización dinámica (walk-forward expanding/rolling) — trabajo futuro.
- ❌ Modelado de costes de transacción — out-of-scope Fase 0.
- ❌ Black-Litterman — explorado en M3 como extensión, no entra en M4.
- ❌ Stress testing sintético (Monte Carlo de escenarios) — los datos OOS reales ya cubren tres episodios de estrés.
- ❌ Optimización de hiperparámetros del rebalanceo (M vs Q vs Y) — fijado a Q por Fase 0.

---

*Última revisión: 2026-05-13 · Versión 2.0*
