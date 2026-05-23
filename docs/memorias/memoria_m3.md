# Memoria M3 — Optimización de Carteras

**Roboadvisor TFM · Fase 1 · Módulo 3**
Juan Rilo · 2026

---

## Índice

1. [Contexto y objetivo](#1-contexto-y-objetivo)
2. [Inputs heredados de M2](#2-inputs-heredados-de-m2)
3. [Arquitectura del módulo `m3_portfolio`](#3-arquitectura-del-módulo-m3_portfolio)
4. [Restricciones del problema](#4-restricciones-del-problema)
5. [Estrategias de optimización por perfil](#5-estrategias-de-optimización-por-perfil)
6. [Manejo del vol cap: blending con cash](#6-manejo-del-vol-cap-blending-con-cash)
7. [Resultados: 9 carteras candidatas](#7-resultados-9-carteras-candidatas)
8. [Selección final por perfil](#8-selección-final-por-perfil)
9. [Validación UCITS y de volatilidad](#9-validación-ucits-y-de-volatilidad)
10. [Tests automatizados](#10-tests-automatizados)
11. [Outputs y handover a M4](#11-outputs-y-handover-a-m4)
12. [Notas metodológicas y limitaciones](#12-notas-metodológicas-y-limitaciones)
13. [Nota metodológica: cartera ex-ante vs cartera OOS-clean](#13-nota-metodológica-cartera-ex-ante-vs-cartera-oos-clean)
14. [Apéndice A — Inventario de ficheros](#apéndice-a--inventario-de-ficheros)

---

## 1. Contexto y objetivo

El **M3** es la fase de **construcción de carteras óptimas** del roboadvisor. Recibe del M2 un universo de 9 ETFs UCITS (3 por perfil de riesgo) junto con sus retornos esperados y matriz de covarianza, y devuelve **tres carteras óptimas** —una por perfil: *conservador*, *moderado*, *agresivo*— listas para ser evaluadas en el M4 con backtesting walk-forward.

El módulo se diseña como **paquete Python instalable** (`m3_portfolio`), independiente del notebook que lo orquesta. Esta separación permite:

- **Reutilizar** los optimizadores en M4 (rebalanceo periódico) sin duplicar código.
- **Testar** la lógica de optimización con `pytest` antes de integrarla en el pipeline.
- Aplicar el principio de **separación de responsabilidades**: las clases optimizadoras no conocen al notebook ni al perfil del cliente; solo a su contrato.

> **Tribunal data science:** la documentación se centra en arquitectura de software y resultados; los desarrollos matemáticos profundos (frontera eficiente, clustering jerárquico) se referencian pero no se reproducen.

---

## 2. Inputs heredados de M2

| Fichero | Forma | Contenido |
|--------|-------|-----------|
| `ETFs/returns.parquet` | `(3 941, 9)` | Retornos diarios 2010-09-15 → 2026-05-01 |
| `ETFs/mu.pkl` | `pd.Series[9]` | μ anualizado = media histórica × 252 |
| `ETFs/cov_ledoit_wolf.pkl` | `pd.DataFrame[9×9]` | Σ con shrinkage Ledoit-Wolf (α ≈ 0.0073, PD garantizada) |

El M3 **no recalcula** ni μ ni Σ: confía en los artefactos del M2. Esto evita inconsistencias entre fases y respeta el principio de *single source of truth*.

**Universo por perfil (definido en M2):**

| Perfil | Tickers |
|--------|---------|
| Conservador | `IEAG.AS`, `EUNH.DE`, `IBCI.AS` (renta fija EUR) |
| Moderado | `INFR.AS`, `IHYG.L`, `EXSA.DE` (mixto global) |
| Agresivo | `CSPX.L`, `EQQQ.DE`, `EXI2.DE` (renta variable global) |

---

## 3. Arquitectura del módulo `m3_portfolio`

```
roboadvisor/
└── m3_portfolio/
    ├── __init__.py         # API pública (11+ exports)
    ├── portfolio.py        # @dataclass(frozen=True) Portfolio
    ├── base.py             # Protocol PortfolioOptimizer (estructural)
    ├── constraints.py      # UCITS, vol cap, HHI
    ├── validators.py       # validación post-hoc
    ├── _build.py           # ensamblador compartido (privado)
    ├── min_variance.py     # MinVarianceOptimizer
    ├── max_sharpe.py       # MaxSharpeOptimizer
    ├── hrp.py              # HRPOptimizer
    └── equal_weight.py     # EqualWeightOptimizer (baseline)
```

### Patrón de diseño

El paquete sigue un patrón **Strategy + Protocol estructural**:

- **`PortfolioOptimizer` (Protocol)** define el contrato mínimo: un método `optimize(mu, cov, tickers, max_volatility, profile, risk_free_rate) -> Portfolio`. Es un *Protocol* (PEP 544), no una clase abstracta; cualquier objeto con esa signatura cumple el tipo.
- Cada **optimizador concreto** (Min-Variance, Max-Sharpe, HRP, Equal-Weight) implementa el método. La lógica matemática vive en `PyPortfolioOpt`; el paquete actúa como **adaptador**.
- Tras la optimización, todos los optimizadores delegan en `_build.build_portfolio()`, que **proyecta** los pesos al simplex UCITS, aplica el vol cap (mezcla con cash) y calcula las métricas ex-ante. Esto garantiza que **ningún `Portfolio` puede salir del módulo violando restricciones**.

### Modelo de datos

`Portfolio` es una **dataclass frozen** (inmutable) con los siguientes campos:

- `profile`, `optimizer_name`, `weights: Dict[str, float]`
- `cash_weight: float` — fracción asignada al activo sintético `CASH`
- `expected_return`, `expected_volatility`, `expected_sharpe`
- `herfindahl_index`, `n_effective_assets`
- `constraints_satisfied: bool`
- `validation_report: Dict[str, bool]` — rellenado por el validador

La inmutabilidad evita modificaciones accidentales una vez optimizada la cartera y facilita el paso por valor entre el notebook y M4.

---

## 4. Restricciones del problema

### UCITS

Para cumplir con la directiva UCITS aplicable a ETFs minoristas:

1. **Long-only**: `w_i ≥ 0` para todo activo.
2. **Sin apalancamiento**: `Σ w_i = 1`.

Estas restricciones son **estructurales** y se aplican vía proyección al simplex en `apply_ucits_constraints()`: se *clipean* los pesos negativos a 0 y se renormaliza.

### Cap de volatilidad por perfil

| Perfil | `max_volatility` |
|--------|------------------|
| Conservador | 8 % |
| Moderado | 15 % |
| Agresivo | 25 % |

Es una **restricción a nivel de cartera** (no por activo). Se aplica *ex post* mediante blending con cash (ver §6).

---

## 5. Estrategias de optimización por perfil

| Perfil | Principal | Alternativa | Baseline |
|--------|-----------|-------------|----------|
| Conservador | **Mínima varianza** (Markowitz) | Máximo Sharpe | Equal-weight |
| Moderado | **Máximo Sharpe** (Markowitz, rf=2 %) | HRP | Equal-weight |
| Agresivo | **HRP** (López de Prado, 2016) | Máximo Sharpe | Equal-weight |

### Justificación

- **Conservador → Min-Variance**: el cliente conservador busca preservar capital; la frontera eficiente sin información sobre retornos esperados (que en RF EUR son muy ruidosos) maximiza la robustez.
- **Moderado → Max-Sharpe**: pondera retorno y riesgo simultáneamente. Es el punto de tangencia clásico de Markowitz.
- **Agresivo → HRP**: la kurtosis exceso > 3 en los 9 ETFs (EQQQ.DE 65.3, IHYG.L 56.5, documentado en M2) y la asimetría negativa en 8/9 ETFs **invalidan los supuestos de normalidad** de Markowitz puro. HRP no requiere invertir Σ ni asumir gaussianidad; agrupa activos por similaridad (clustering jerárquico) y reparte riesgo por bisección recursiva. Para el perfil más expuesto a colas, esto aporta robustez.

Generamos **tres candidatas por perfil** (principal, alternativa, baseline) para tener punto de comparación cuantitativo en lugar de adoptar la estrategia "principal" por convención.

---

## 6. Manejo del vol cap: blending con cash

Cuando la cartera optimizada `w*` tiene volatilidad `σ_p > max_vol`, se **mezcla linealmente con cash** (activo sintético, vol = 0, retorno = `rf` = 2 %):

```
w_final  = α · w*           ,    cash_weight = 1 − α
α        = min(1, max_vol / σ_p)
σ_final  = α · σ_p          ≤ max_vol
μ_final  = α · μ_p + (1 − α) · rf
```

### Por qué cash y no reescalado puro

Reescalar los pesos por un factor `α < 1` y **renormalizar** a suma 1 (`w / Σ w`) **no cambia la volatilidad** —es el mismo punto del simplex—. La única forma matemáticamente consistente de reducir la varianza manteniendo la restricción UCITS es **añadir un activo libre de riesgo**.

En la práctica esto se traduce en una columna `CASH` en `weights.parquet` cuando aplica. Para los inputs históricos de M2 esta restricción no ha sido vinculante (ver §7).

---

## 7. Resultados: 9 carteras candidatas

Métricas **ex-ante** calculadas con μ y Σ del M2 (in-sample). La validación out-of-sample se hará en M4.

### Conservador (cap 8 %)

| Candidata | Optimizador | Ret % | Vol % | Sharpe | HHI | Cash % |
|-----------|-------------|-------|-------|--------|-----|--------|
| Principal | min_variance | 1.24 | 4.35 | −0.176 | 0.86 | 0 |
| Alternativa | max_sharpe ⚠ | 1.24 | 4.35 | −0.176 | 0.86 | 0 |
| Baseline | equal_weight | 1.41 | 4.68 | −0.127 | 0.33 | 0 |

⚠ En conservador, `max(μ) ≈ 1.72 % < rf = 2 %`, por lo que `max_sharpe` cae automáticamente a `min_volatility` con warning (ver §12, nota 1).

### Moderado (cap 15 %)

| Candidata | Optimizador | Ret % | Vol % | Sharpe | HHI | Cash % |
|-----------|-------------|-------|-------|--------|-----|--------|
| Principal | max_sharpe | 8.30 | 14.03 | 0.449 | 0.52 | 0 |
| Alternativa | hrp | 4.30 | 7.12 | 0.324 | 0.67 | 0 |
| Baseline | equal_weight | 6.55 | 10.55 | 0.432 | 0.33 | 0 |

### Agresivo (cap 25 %)

| Candidata | Optimizador | Ret % | Vol % | Sharpe | HHI | Cash % |
|-----------|-------------|-------|-------|--------|-----|--------|
| Principal | hrp | 15.14 | 15.22 | 0.863 | 0.41 | 0 |
| Alternativa | max_sharpe | 17.06 | 16.74 | 0.899 | 0.50 | 0 |
| Baseline | equal_weight | 16.09 | 16.12 | 0.874 | 0.33 | 0 |

---

## 8. Selección final por perfil

**Criterio**: `argmax(Sharpe) s.t. σ ≤ max_vol × 1.01`.

| Perfil | Estrategia elegida | Ret % | Vol % | Sharpe | Cumple cap |
|--------|-------------------|-------|-------|--------|------------|
| Conservador | equal_weight | 1.41 | 4.68 | **−0.127** | ✓ |
| Moderado | max_sharpe | 8.30 | 14.03 | **0.449** | ✓ |
| Agresivo | max_sharpe | 17.06 | 16.74 | **0.899** | ✓ |

### Lectura crítica de la selección

- **Conservador**: el Sharpe negativo es esperable y está **documentado**: los ETFs de RF EUR tienen CAGR < rf=2 % durante el período histórico (entorno **ZIRP** 2010-2021). El propio M2 anticipó esta advertencia. El equal-weight gana porque la diversificación cruda baja el Sharpe menos que la concentración en min-variance (que aglutina en el activo con menor σ propio). En M4 con datos posteriores (2022+, subidas de tipos) la situación cambiará.
- **Agresivo**: gana `max_sharpe` con Sharpe 0.899, **por encima del HRP designado como principal**. El criterio de selección es agnóstico al optimizador; elige el que mejor puntúa cumpliendo restricciones. Este es el comportamiento deseado: la "principal" es una *prior* metodológica, no un compromiso.
- **Moderado**: Sharpe 0.449 < 0.958 del benchmark 60/40 documentado en M2. Esto es **ex-ante** con μ histórico in-sample; el benchmark cuyo Sharpe 0.958 ya incluye toda la deriva alcista 2010-2026. La comparación justa será en M4 con backtesting walk-forward.

---

## 9. Validación UCITS y de volatilidad

`validators.validate_portfolio()` ejecuta **cuatro chequeos** sobre las carteras seleccionadas:

| Check | Tolerancia | Conservador | Moderado | Agresivo |
|-------|-----------|-------------|----------|----------|
| `sum_to_one` | 1e-6 | ✓ | ✓ | ✓ |
| `long_only` | -1e-6 | ✓ | ✓ | ✓ |
| `vol_within_cap` | ×1.01 | ✓ | ✓ | ✓ |
| `hhi_in_range` | [1/n, 1] | ✓ | ✓ | ✓ |
| **STATUS** | | **PASS** | **PASS** | **PASS** |

---

## 10. Tests automatizados

Suite con **16 tests** en `roboadvisor/tests/`, todos pasan en ~2 s.

| Fichero | N | Cubre |
|---------|---|-------|
| `test_optimizers.py` | 5 | Smoke tests × 4 optimizadores + 1/n |
| `test_constraints.py` | 7 | UCITS, HHI, effective_assets, vol cap (blend + no-op) |
| `test_validators.py` | 4 | Validación correcta + detección de violaciones |

`conftest.py` define fixtures sintéticas: `sample_cov` (3×3 PD), `sample_mu`, `sample_tickers`, `sample_max_volatility`. Permite probar la lógica sin depender de los inputs reales.

Comando de ejecución:

```bash
cd roboadvisor
python -m pytest tests/ -v
```

---

## 11. Outputs y handover a M4

Dos artefactos consumidos por el siguiente módulo:

### `weights.parquet`

DataFrame con multi-índice `(profile, ticker)` → columna `weight`. Incluye fila `CASH` cuando el blending haya actuado.

```
                       weight
profile     ticker
agresivo    CSPX.L   0.5234
            EQQQ.DE  0.4766
            EXI2.DE  0.0000
conservador EUNH.DE  0.3333
            IBCI.AS  0.3333
            IEAG.AS  0.3333
moderado    EXSA.DE  0.6106
            IHYG.L   0.0000
            INFR.AS  0.3894
```

### `portfolios_summary.json`

Diccionario `{profile: {optimizer, selection, weights, cash_weight, expected_*, herfindahl_index, n_effective_assets, max_volatility, validation}}`. Pensado para auditoría legible y trazabilidad de la decisión (qué algoritmo fue elegido y por qué).

---

## 12. Notas metodológicas y limitaciones

1. **Max-Sharpe en perfil conservador.** El algoritmo de Markowitz exige `max(μ) > rf` para que el problema sea factible. Cuando esto no se cumple (caso ZIRP en RF EUR), `MaxSharpeOptimizer` **cae automáticamente a `min_volatility`** y emite un warning vía `logging`. Es la decisión más conservadora y queda registrada.

2. **In-sample bias.** Las métricas de §7 se calculan con μ y Σ históricos sobre los **mismos datos** usados para optimizar. Son cotas optimistas. La validación honesta es M4 (walk-forward, datos out-of-sample).

3. **HHI sólo sobre activos riesgo.** El índice de concentración excluye la columna `CASH` para que sea comparable entre carteras (sin cash) y carteras con cash blending.

4. **Tolerancias.** `1e-6` para sumas y long-only; `+1 %` slack sobre el vol cap (para absorber errores de redondeo de PyPortfolioOpt). Estos números están centralizados en `validators.py`.

5. **Reproducibilidad.** El notebook puede regenerarse desde código vía `notebooks/_build_notebook.py`, evitando merge conflicts en JSON.

---

## 13. Nota metodológica: cartera ex-ante vs cartera OOS-clean

Al arrancar la implementación del **M4 (backtesting walk-forward)** se identificó una sutileza temporal en el uso de los pesos producidos por este módulo. Esta sección la documenta para que la separación de roles entre M3 y M4 quede explícita en la memoria.

### El problema

Los pesos persistidos en `outputs/m3/weights.parquet` se han calculado con un vector de retornos esperados μ y una matriz de covarianza Σ estimados sobre **todo el histórico disponible** (`outputs/m2/returns.parquet`, 2010-09 → 2026-05). Es decir, los parámetros del optimizador ya “han visto” el régimen 2020-2026 (COVID, mercado bajista de 2022, subida de tipos del BCE). Si esos pesos se aplicaran sin más sobre una ventana out-of-sample (OOS) 2020-2026 y se reportasen métricas, el experimento contendría **look-ahead bias en la fase de estimación de parámetros**, incumpliendo el principio walk-forward que la Fase 0 del TFM declara como requisito contractual.

### La solución: dos carteras con roles disjuntos

En lugar de regenerar `weights.parquet` y perder la cartera “producción” que el roboadvisor recomendaría hoy, M3 y M4 coexisten con responsabilidades claramente separadas:

| Artefacto | Estimación de μ y Σ | Pregunta que responde |
|-----------|---------------------|-----------------------|
| **Cartera ex-ante (M3)** · `outputs/m3/weights.parquet` | Histórico completo 2010-09 → 2026-05 | *“¿Qué cartera debería recomendar el roboadvisor **hoy** a este perfil?”* |
| **Cartera OOS-clean (M4)** · `outputs/m4/weights_oos_clean.parquet` | Sólo 2010-09 → 2019-12-31 | *“¿Qué cartera **se habría** recomendado a finales de 2019 y cómo se habría comportado en 2020-2026?”* |

Ambas son **legítimas** y **necesarias**:

- La **ex-ante** es la cartera de producción. Es el output que un cliente real recibiría si abriera la cuenta hoy, porque incorpora toda la información disponible. Es la entrega que valida el funcionamiento integral del pipeline NLP → universo → optimización.
- La **OOS-clean** es la cartera de **validación científica**. Reusa los mismos optimizadores de `src/m3_portfolio/` (mismas restricciones UCITS, mismos vol caps, misma jerarquía principal/alternativa/baseline) pero con μ y Σ recalculados sobre la ventana de entrenamiento. Sus pesos se aplican al periodo OOS para producir métricas de QuantStats académicamente defendibles.

### Implicaciones para esta memoria

Toda la sección §7 (resultados de las 9 candidatas), §8 (selección final) y §9 (validación) se refieren a la **cartera ex-ante**. La cartera OOS-clean **no se calcula en M3** — vivirá en M4 y se reportará en la memoria del módulo siguiente. Las API públicas del paquete `m3_portfolio` no cambian: los optimizadores no saben de fechas, sólo de matrices (μ, Σ). Quién decide qué ventana temporal usar es responsabilidad del **orquestador** (este notebook para M3, el notebook de backtesting para M4), no del optimizador.

Esta separación —optimizador agnóstico al tiempo, orquestador responsable de la ventana— es la que permite reusar literalmente el mismo `MinVarianceOptimizer`, `MaxSharpeOptimizer` y `HRPOptimizer` en ambos contextos sin riesgo de contaminación temporal.

---

## Apéndice A — Inventario de ficheros

### Paquete

- `roboadvisor/m3_portfolio/portfolio.py` · dataclass `Portfolio`
- `roboadvisor/m3_portfolio/base.py` · Protocol `PortfolioOptimizer`
- `roboadvisor/m3_portfolio/constraints.py` · UCITS + vol cap + HHI
- `roboadvisor/m3_portfolio/validators.py` · validación post-hoc
- `roboadvisor/m3_portfolio/_build.py` · ensamblador compartido
- `roboadvisor/m3_portfolio/min_variance.py` · MinVarianceOptimizer
- `roboadvisor/m3_portfolio/max_sharpe.py` · MaxSharpeOptimizer (con fallback)
- `roboadvisor/m3_portfolio/hrp.py` · HRPOptimizer
- `roboadvisor/m3_portfolio/equal_weight.py` · EqualWeightOptimizer
- `roboadvisor/m3_portfolio/__init__.py` · API pública (15 exports)

### Tests

- `roboadvisor/tests/conftest.py`
- `roboadvisor/tests/test_optimizers.py`
- `roboadvisor/tests/test_constraints.py`
- `roboadvisor/tests/test_validators.py`

### Notebook

- `roboadvisor/notebooks/M3_optimizacion_carteras.ipynb` (orquestador)
- `roboadvisor/notebooks/_build_notebook.py` (regenerador)

### Outputs

- `roboadvisor/data/m3_outputs/weights.parquet`
- `roboadvisor/data/m3_outputs/portfolios_summary.json`
- `roboadvisor/data/m3_outputs/Memoria_M3.md` · este documento
- `roboadvisor/data/m3_outputs/Memoria_M3.pdf` · versión PDF
