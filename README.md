# 🤖 Roboadvisor Personalizado para el Inversor Retail

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
![HuggingFace](https://img.shields.io/badge/HuggingFace-FinBERT-FFD21E?logo=huggingface&logoColor=black)
![PyPortfolioOpt](https://img.shields.io/badge/PyPortfolioOpt-1.5.6-4CAF50)
![QuantStats](https://img.shields.io/badge/QuantStats-0.0.64-2196F3)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-orange?logo=jupyter&logoColor=white)
[![CI](https://github.com/Juan-Lage-Rilo/Roboadvisor_personalizado_TFM/actions/workflows/ci.yml/badge.svg)](https://github.com/Juan-Lage-Rilo/Roboadvisor_personalizado_TFM/actions/workflows/ci.yml)

> **Trabajo Fin de Máster** — Sistema de asesoramiento financiero automatizado que combina perfilado de riesgo (cuestionario MiFID II + NLP) con optimización moderna de carteras. Orientado al inversor retail sin experiencia financiera previa.

---

## 📋 Descripción General

Este proyecto implementa un **roboadvisor end-to-end** en Python que automatiza dos tareas centrales del asesoramiento financiero retail: (1) inferir el perfil de riesgo del inversor combinando un cuestionario de idoneidad MiFID II con análisis de sentimiento NLP de sus respuestas en texto libre, y (2) construir y validar una cartera de ETFs UCITS optimizada con restricciones de volatilidad derivadas de ese perfil.

El sistema clasifica al inversor en un perfil de riesgo (conservador / moderado / agresivo) con un cap de volatilidad anual asociado, evalúa varias candidatas de cartera (mínima varianza, máximo Sharpe, HRP y equal-weight) y selecciona automáticamente la de mayor Sharpe ex-ante sujeta al cap. Los resultados se validan out-of-sample contra benchmarks estándar (S&P 500 y cartera 60/40).

**Dataset de referencia NLP:** Financial PhraseBank — 14.780 frases financieras etiquetadas (`positive`, `negative`, `neutral`) con cuatro niveles de acuerdo entre anotadores.

---

## 🗂️ Fuentes de Datos

| Fuente | Formato | Contenido | Acceso |
|---|---|---|---|
| Financial PhraseBank | CSV | 14.780 frases financieras etiquetadas (`sentence`, `label`, `agreement_level`) | HuggingFace / archivo local |
| yfinance | API (REST) | Precios diarios OHLCV de ETFs UCITS | `yfinance` Python package |
| HuggingFace Inference API | API (REST) | Inferencia remota Opus-MT + FinBERT (demo M5) | Token HF gratuito |

---

## ⚙️ Stack Tecnológico

| Categoría | Herramienta | Uso |
|---|---|---|
| NLP / ML | `transformers` + `ProsusAI/finbert` · `pysentimiento` (RoBERTuito) | Pipeline NLP dual de sentimiento (EN traducido / ES nativo) |
| Traducción | `Helsinki-NLP/opus-mt-es-en` | Puente ES→EN para FinBERT |
| Datos de mercado | `yfinance` | Descarga de precios históricos de ETFs UCITS |
| Optimización | `PyPortfolioOpt` + `scikit-learn` (Ledoit-Wolf) | Min Variance, Max Sharpe, HRP, restricciones UCITS |
| Backtesting | Motor propio (`src/m4_backtesting`) + `QuantStats` (tearsheets) | CAGR, Sharpe, Sortino, max drawdown, Calmar |
| Demo interactiva | `Streamlit` + HF Inference API | Interfaz del cuestionario M1 (módulo M5) |
| Entorno | Python 3.13, Jupyter Notebook / VS Code | — |

---

## 📦 Instalación

```bash
git clone https://github.com/Juan-Lage-Rilo/Roboadvisor_personalizado_TFM.git
cd Roboadvisor_personalizado_TFM

# Paquete instalable + tests (entorno mínimo, el mismo que usa la CI):
pip install -e ".[dev]"

# Entorno local completo (notebooks NLP con torch, quantstats, pysentimiento):
pip install -r requirements-dev.txt
```

> `requirements.txt` (raíz) es **solo para el deploy en Streamlit Cloud**: deliberadamente ligero, sin `torch` ni `transformers`, porque la demo usa inferencia remota. Para trabajar en local usa `requirements-dev.txt` o `pip install -e ".[dev]"`.

---

## 📁 Estructura del Proyecto

```
Roboadvisor_personalizado_TFM/
│
├── notebooks/                          # Pipeline ejecutable, en orden M2 → M3 → M4 (M1 independiente)
│   ├── m1_financial_phrasebank.ipynb   #   EDA del Financial PhraseBank
│   ├── m1_nlp_profiling.ipynb          #   M1 · Perfilado NLP (FinBERT + RoBERTuito)
│   ├── m2_eda_etfs_ucits.ipynb         #   M2 · EDA del universo de ETFs UCITS
│   ├── m2_seleccion_universo.ipynb     #   M2 · Selección y limpieza → outputs/m2/
│   ├── m3_optimizacion_carteras.ipynb  #   M3 · Optimización por perfil → outputs/m3/
│   └── m4_backtesting.ipynb            #   M4 · Validación OOS vs benchmarks
│
├── src/
│   ├── roboadvisor_paths.py            # Registro central de rutas (PROJECT_ROOT)
│   ├── m1_mifid_questionnaire.py       # M1 · Cuestionario MiFID II (12 cerradas + 3 abiertas)
│   ├── m1_remote_profiling.py          # M1 · Perfilado vía HF Inference API (usado por la demo M5)
│   ├── m3_portfolio/                   # M3 · Paquete de optimización
│   │   ├── base.py                     #   Protocolo PortfolioOptimizer
│   │   ├── min_variance.py · max_sharpe.py · hrp.py · equal_weight.py
│   │   ├── constraints.py              #   Restricciones UCITS + vol-cap (mezcla con cash)
│   │   ├── portfolio.py                #   Dataclass Portfolio (pesos + métricas ex-ante)
│   │   └── validators.py
│   └── m4_backtesting/                 # M4 · Paquete de backtesting
│       ├── weights_generator.py        #   Pesos OOS-clean (μ/Σ estimados solo con train)
│       ├── engine.py                   #   BacktestEngine con rebalanceo y cash
│       ├── rebalancer.py · metrics.py · benchmarks.py
│
├── app.py                              # M5 · Demo Streamlit (cuestionario + NLP remoto)
├── tests/                              # pytest: m1, m3_portfolio, m4_backtesting
├── docs/mifid/                         # Metodología del cuestionario MiFID II
├── outputs/                            # Artefactos generados por los notebooks (no versionados)
├── data/                               # Datos raw (no versionados; los descargan los notebooks)
├── pyproject.toml                      # Paquete instalable + dependencias + config pytest
├── requirements.txt                    # Solo deploy Streamlit Cloud (ligero)
└── requirements-dev.txt                # Entorno local completo
```

> **Nota sobre M2:** no tiene módulo en `src/`; vive íntegramente en los notebooks y publica sus artefactos (`returns.parquet`, μ, Σ Ledoit-Wolf) en `outputs/m2/`, que M3 y M4 consumen.

---

## 🚀 Uso

El proyecto se ejecuta módulo a módulo. **Orden:** M2 → M3 → M4 (cada notebook genera los artefactos que consume el siguiente). M1 y M5 son independientes de esa cadena.

### M1 — Perfilado del inversor

El perfilado completo (cuestionario MiFID II + NLP dual con prudencia asimétrica) se desarrolla y valida en `notebooks/m1_nlp_profiling.ipynb`. La versión de producción —inferencia remota vía HuggingFace Inference API— es la que usa la demo M5:

```python
from m1_remote_profiling import RemoteProfiler, classify_profile_advisory
# Requiere HF_TOKEN (st.secrets o variable de entorno). Ver app.py y M5 más abajo.
```

### M2 — Universo de activos

Ejecutar `notebooks/m2_seleccion_universo.ipynb`. Descarga precios de ETFs UCITS vía yfinance, limpia y genera `outputs/m2/returns.parquet` (+ μ y Σ), inputs de M3 y M4.

### M3 — Optimización de cartera

```python
import pandas as pd
from sklearn.covariance import LedoitWolf
from m3_portfolio import MaxSharpeOptimizer, TRADING_DAYS

returns = pd.read_parquet("outputs/m2/returns.parquet")   # generado por M2
mu = returns.mean() * TRADING_DAYS
cov = pd.DataFrame(
    LedoitWolf().fit(returns.values).covariance_ * TRADING_DAYS,
    index=returns.columns, columns=returns.columns,
)

portfolio = MaxSharpeOptimizer().optimize(
    mu=mu, cov=cov,
    tickers=list(returns.columns),
    max_volatility=0.15,        # cap del perfil (derivado de M1)
    profile="moderado",
    risk_free_rate=0.02,
)
portfolio.weights               # dict ticker → peso (puede incluir CASH)
portfolio.expected_volatility   # vol ex-ante anualizada
portfolio.expected_sharpe
```

Optimizadores disponibles: `MinVarianceOptimizer`, `MaxSharpeOptimizer`, `HRPOptimizer`, `EqualWeightOptimizer`. Todos aplican restricciones UCITS y el cap de volatilidad (mezcla con cash si se excede).

### M4 — Backtesting (validación OOS)

```python
import pandas as pd
from m3_portfolio import MaxSharpeOptimizer, MinVarianceOptimizer, EqualWeightOptimizer
from m4_backtesting import (
    BacktestEngine, regenerate_oos_clean_weights,
    cagr, sharpe_ratio, max_drawdown,
)

returns = pd.read_parquet("outputs/m2/returns.parquet")

# 1) Pesos OOS-clean: μ/Σ estimados SOLO con datos <= train_end_date
selected = regenerate_oos_clean_weights(
    returns=returns,
    train_end_date=pd.Timestamp("2019-12-31"),
    profiles={"moderado": list(returns.columns)},
    max_vol={"moderado": 0.15},
    primary_optimizer={"moderado": MaxSharpeOptimizer},
    alternative_optimizer={"moderado": MinVarianceOptimizer},
    baseline_optimizer=EqualWeightOptimizer,
)

# 2) Simulación sobre la ventana OOS con rebalanceo trimestral
result = BacktestEngine(
    returns=returns.loc["2020-01-01":],
    target_weights=selected["moderado"].weights,
    rebalance_freq="Q",
    rf_annual=0.02,
).run()

mdd, peak, trough = max_drawdown(result.equity_curve)
print(cagr(result.equity_curve), sharpe_ratio(result.returns), mdd)
```

### M5 — Demo interactiva

```bash
# requiere HF_TOKEN en .streamlit/secrets.toml:
#   HF_TOKEN = "hf_tu_token_aqui"
streamlit run app.py
```

### Tests

```bash
pytest tests/    # m1 + m3_portfolio + m4_backtesting
```

---

## 🏗️ Arquitectura del Sistema

El sistema se organiza en cinco módulos con flujo de datos unidireccional:

```
[Cuestionario MiFID II + texto libre del usuario]
         │
         ▼
┌─────────────────────┐
│  M1 · Perfilado     │  Cuestionario (q_norm) + NLP dual advisory → perfil {conservador, moderado, agresivo}
└─────────┬───────────┘
          │  perfil → cap de volatilidad anual
          ▼
┌─────────────────────┐
│ M2 · Universo ETFs  │  yfinance → retornos diarios limpios (outputs/m2/)
└─────────┬───────────┘
          │  matriz de retornos + μ/Σ (Ledoit-Wolf)
          ▼
┌─────────────────────┐
│  M3 · Optimización  │  Min Variance / Max Sharpe / HRP + restricciones UCITS y vol-cap
└─────────┬───────────┘
          │  pesos por perfil (outputs/m3/)
          ▼
┌─────────────────────┐
│ M4 · Backtesting    │  Motor propio + QuantStats → métricas vs S&P 500 y 60/40
└─────────┬───────────┘
          │  (opcional)
          ▼
┌─────────────────────┐
│  M5 · Demo          │  Streamlit + HF Inference API → cuestionario interactivo (M1)
└─────────────────────┘
```

---

## 🔄 Pipeline de Perfilado (M1 en detalle)

El perfil **no** sale del NLP en solitario: lo fija el cuestionario MiFID II, y el NLP actúa como señal *advisory* bajo el principio de **prudencia asimétrica** (solo puede rebajar el perfil o emitir un aviso de revisión, nunca elevarlo).

| Etapa | Descripción |
|---|---|
| **Entrada** | 12 preguntas cerradas MiFID II + 3 respuestas abiertas en castellano |
| **Rama A (cuestionario)** | Scoring ponderado por dimensión → `q_norm` → perfil base |
| **Rama B (NLP dual)** | Pipeline A: Opus-MT ES→EN + FinBERT · Pipeline B: RoBERTuito (ES nativo) |
| **Fusión** | Media de ambos pipelines + medida de concordancia; regla de suelo por capacidad económica (P5/P6) |
| **Salida** | Perfil final {conservador, moderado, agresivo} + cap de volatilidad + flag de revisión |

**Verificación del pipeline NLP:** FinBERT zero-shot sobre Financial PhraseBank, subconjunto `allagree` (n = 2.264): accuracy 0,9717, F1-macro 0,9625.

> ⚠️ **Advertencia metodológica:** `ProsusAI/finbert` fue *fine-tuneado* sobre el propio Financial PhraseBank (Araci, 2019), por lo que estas cifras constituyen una evaluación in-domain sobre datos vistos en entrenamiento. Se reportan como **verificación de integración del pipeline** (tokenización, traducción ES→EN, mapeo de etiquetas), **no** como medida de generalización. La validación sobre un dataset no visto queda recogida en líneas futuras; la triangulación con RoBERTuito (pipeline B, modelo independiente) mitiga parcialmente esta limitación.

---

## 📐 Metodología de Optimización (M3)

Para cada perfil se evalúan **tres candidatas** de cartera y se selecciona automáticamente la que maximiza el Sharpe ex-ante sujeta al cap de volatilidad del perfil:

| Perfil | Cap de vol. | Candidata principal | Candidata alternativa | Baseline |
|---|---|---|---|---|
| Conservador | 8 %  | Mínima Varianza (Markowitz, 1952) | Máximo Sharpe (Sharpe, 1966) | Equal-weight |
| Moderado    | 15 % | Máximo Sharpe                       | HRP (López de Prado, 2016)    | Equal-weight |
| Agresivo    | 25 % | HRP                                 | Máximo Sharpe                   | Equal-weight |

**Regla de selección:** se elige la cartera con mayor Sharpe ex-ante entre las que cumplen `vol_anual ≤ cap × 1,01`. La estimación de μ y Σ usa Ledoit-Wolf shrinkage (Ledoit & Wolf, 2004). Si una candidata excede el cap, se mezcla linealmente con cash (rf anual = 2 %) hasta cumplirlo (`constraints.apply_volatility_cap`).

El cap de volatilidad de cada perfil queda fijado por el perfilado de M1 (cuestionario MiFID II + análisis de sentimiento NLP), bajo el principio de **prudencia asimétrica**: la señal NLP solo puede *rebajar* el perfil de riesgo, nunca elevarlo.

---

## 📊 Validación y Backtesting (M4)

La validación es un **backtest out-of-sample estático**, diseñado para eliminar el look-ahead bias en la estimación de parámetros:

- **Train:** μ y Σ (Ledoit-Wolf) estimados exclusivamente con datos ≤ 2019-12-31 (pesos *OOS-clean*, regenerados por `weights_generator`).
- **Test (OOS):** 2020-01-02 → 2026-04-30, ventana nunca vista en la estimación.
- **Rebalanceo:** trimestral, hacia los pesos objetivo (los pesos driftean entre rebalanceos; el cash devenga rf diaria).
- Las métricas canónicas las calcula una implementación propia (`m4_backtesting.metrics`); QuantStats se usa solo para los tearsheets HTML descriptivos.

> Los pesos objetivo se mantienen fijos durante toda la ventana OOS (no hay re-estimación rodante de μ/Σ). La extensión a walk-forward completo —re-optimización en cada rebalanceo con ventana expandible— está identificada como línea futura; la infraestructura ya lo permite (`regenerate_oos_clean_weights` parametriza `train_end_date`).

Métricas reportadas vs. benchmarks (S&P 500 / cartera 60/40):

| Métrica | Descripción |
|---|---|
| CAGR | Tasa de crecimiento anual compuesta |
| Sharpe Ratio | Rentabilidad ajustada por riesgo total |
| Sortino Ratio | Rentabilidad ajustada por riesgo a la baja |
| Max Drawdown | Caída máxima pico a valle |
| Calmar Ratio | CAGR / Max Drawdown |

---

## 📈 Resultados

Backtest OOS 2020-01-02 → 2026-04-30, pesos *OOS-clean* (μ y Σ estimados solo con datos ≤ 2019-12-31), rebalanceo trimestral, rf anual = 2 %. En este universo y ventana, la regla de selección elige **Máximo Sharpe** para los tres perfiles (ver § Metodología de Optimización).

| Perfil | Estrategia seleccionada | CAGR | Sharpe | Max Drawdown |
|---|---|---|---|---|
| Conservador | Máximo Sharpe | −1,60 % | −0,55 | −22,20 % |
| Moderado | Máximo Sharpe | +4,18 % | 0,26 | −28,20 % |
| Agresivo | Máximo Sharpe | +16,20 % | 0,80 | −31,78 % |
| *Benchmark S&P 500* | *Buy & Hold* | +15,05 % | 0,69 | −33,72 % |
| *Benchmark 60/40* | *Buy & Hold* | +8,26 % | 0,58 | −22,26 % |

### Discusión

El resultado del perfil conservador (CAGR negativo, drawdown comparable al 60/40) es un hallazgo del diseño experimental, no un artefacto: la ventana OOS arranca con el crash del COVID —el peor escenario posible para unos pesos estimados con datos pre-2020 y congelados durante seis años— y evidencia dos fragilidades conocidas de la optimización media-varianza con μ histórica (DeMiguel, Garlappi & Uppal, 2009): (1) la selección por Sharpe ex-ante eligió Máximo Sharpe también para el perfil conservador, descartando Mínima Varianza, y (2) el cap de volatilidad ex-ante (8 %) no acota el riesgo *realizado* cuando el régimen de mercado cambia respecto al período de estimación. Ambas observaciones motivan las líneas futuras: re-estimación periódica (walk-forward completo), selección de candidatas con penalización de drawdown y estimadores de riesgo condicionales.

---

## ✅ Tests y CI

- Suite `pytest` con cobertura de M1 (regresión de la prudencia asimétrica), M3 (optimizadores, restricciones, validadores) y M4 (motor, rebalanceo, métricas, generación de pesos).
- CI en GitHub Actions (Python 3.13) en cada push/PR a `main`.

---

## ⚠️ Limitaciones declaradas

- La evaluación NLP sobre Financial PhraseBank es in-domain (ver advertencia en § Pipeline M1).
- Backtest sin costes de transacción ni slippage; rf fija al 2 % anual.
- Validación OOS estática (pesos fijos), no walk-forward con re-estimación rodante.
- SPY (USD) como benchmark de carteras UCITS denominadas en EUR: el riesgo divisa no se cubre; el 60/40 sintético (`0.6·CSPX.L + 0.4·IEAG.AS`) actúa como benchmark homogéneo en EUR.

---

## 📚 Referencias Clave

- Markowitz, H. (1952). *Portfolio Selection*. Journal of Finance, 7(1), 77–91.
- Sharpe, W. F. (1966). *Mutual Fund Performance*. Journal of Business, 39(1), 119–138.
- Ledoit, O. & Wolf, M. (2004). *Honey, I Shrunk the Sample Covariance Matrix*. Journal of Portfolio Management, 30(4), 110–119.
- López de Prado, M. (2016). *Building Diversified Portfolios that Outperform Out-of-Sample*. Journal of Portfolio Management, 42(4).
- DeMiguel, V., Garlappi, L. & Uppal, R. (2009). *Optimal Versus Naive Diversification: How Inefficient is the 1/N Portfolio Strategy?* Review of Financial Studies, 22(5), 1915–1953.
- Araci, D. (2019). *FinBERT: Financial Sentiment Analysis with Pre-trained Language Models*. arXiv:1908.10063.
- Malo, P. et al. (2014). *Good Debt or Bad Debt: Detecting Semantic Orientations in Economic Texts*. JASIST 65(4), 782–796 (Financial PhraseBank).
- Pérez, J. M. et al. (2021). *pysentimiento: A Python Toolkit for Sentiment Analysis and SocialNLP tasks*. arXiv:2106.09462.

---

## 📄 Licencia

This project is for educational purposes. Please check their terms before any commercial use.
