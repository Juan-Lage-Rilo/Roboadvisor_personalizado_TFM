# 🤖 Roboadvisor Personalizado para el Inversor Retail

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![HuggingFace](https://img.shields.io/badge/HuggingFace-FinBERT-FFD21E?logo=huggingface&logoColor=black)
![PyPortfolioOpt](https://img.shields.io/badge/PyPortfolioOpt-1.5+-4CAF50)
![QuantStats](https://img.shields.io/badge/QuantStats-0.0.62+-2196F3)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-orange?logo=jupyter&logoColor=white)

> **Trabajo Fin de Máster** — Sistema de asesoramiento financiero automatizado que combina perfilado de riesgo por NLP con optimización moderna de carteras. Orientado al inversor retail sin experiencia financiera previa.

---

## 📋 Descripción General

Este proyecto implementa un **roboadvisor end-to-end** en Python que automatiza dos tareas centrales del asesoramiento financiero retail: (1) inferir el perfil de riesgo del inversor a partir del análisis de sentimiento de texto libre mediante FinBERT, y (2) construir y validar una cartera de ETFs globales optimizada con restricciones de volatilidad derivadas de ese perfil.

El sistema procesa el lenguaje natural del usuario, lo traduce a un perfil de riesgo (conservador / moderado / agresivo) con un cap de volatilidad anual asociado, evalúa varias candidatas de cartera (mínima varianza, máximo Sharpe, HRP y equal-weight) y selecciona automáticamente la de mayor Sharpe ex-ante sujeta al cap. Los resultados se backtestean contra benchmarks estándar (S&P 500 y cartera 60/40).

**Dataset de entrenamiento/validación NLP:** Financial PhraseBank — 14.780 frases financieras etiquetadas (`positive`, `negative`, `neutral`) con cuatro niveles de acuerdo entre anotadores.

---

## 🗂️ Fuentes de Datos

| Fuente | Formato | Contenido | Acceso |
|---|---|---|---|
| Financial PhraseBank | CSV | 14.780 frases financieras etiquetadas (3 columnas: `sentence`, `label`, `agreement_level`) | HuggingFace / archivo local |
| Financial Tweets Sentiment | CSV | Tweets financieros etiquetados por sentimiento | HuggingFace Datasets |
| yfinance | API (REST) | Precios diarios OHLCV de ETFs globales | `yfinance` Python package |
| FRED (Federal Reserve) | API (REST) | Tipos de interés libres de riesgo (T-Bill) | `fredapi` Python package |
| Alpha Vantage | API (REST) | Datos de mercado complementarios | API key gratuita |

---

## ⚙️ Stack Tecnológico

| Categoría | Herramienta | Uso |
|---|---|---|
| NLP / ML | `transformers` (HuggingFace) + `ProsusAI/finbert` | Inferencia de sentimiento financiero |
| Datos de mercado | `yfinance` | Descarga de precios históricos de ETFs |
| Optimización | `PyPortfolioOpt` | Markowitz, Max Sharpe, HRP |
| Backtesting | `QuantStats` | CAGR, Sharpe, Sortino, max drawdown |
| Datos macroeconómicos | `fredapi` | Tasa libre de riesgo |
| Demo interactiva | `Streamlit` | Interfaz usuario (módulo opcional) |
| Entorno | Python 3.10+, Jupyter Notebook / VS Code | — |

---

## 📦 Instalación

```bash
pip install transformers torch yfinance pyportfolioopt quantstats fredapi pandas numpy matplotlib seaborn streamlit
```

Para usar la GPU en la inferencia FinBERT (recomendado):

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

## 📁 Estructura del Proyecto

```
roboadvisor-tfm/
│
├── data/
│   ├── raw/
│   │   ├── financial_phrasebank.csv       # 14.780 frases etiquetadas
│   │   └── financial_tweets_sentiment.csv # Dataset de tweets financieros
│   └── processed/
│       └── etf_returns.parquet            # Retornos diarios limpios de ETFs
│
├── notebooks/
│   ├── M1_nlp_profiling.ipynb             # Módulo 1: Perfilado NLP
│   ├── M2_asset_universe.ipynb            # Módulo 2: Universo de activos
│   ├── M3_portfolio_optimization.ipynb    # Módulo 3: Optimización de cartera
│   ├── M4_backtesting.ipynb               # Módulo 4: Backtesting y validación
│   └── financial_phrasebank.ipynb         # EDA del dataset de entrenamiento
│
├── src/
│   ├── m1_profiling.py                    # Lógica de perfilado (reutilizable)
│   ├── m2_universe.py                     # Construcción del universo de activos
│   ├── m3_optimizer.py                    # Optimizadores de cartera
│   └── m4_backtest.py                     # Motor de backtesting walk-forward
│
├── app/
│   └── streamlit_app.py                   # Demo interactiva M5 (opcional)
│
├── outputs/
│   ├── Pipeline_M1_Infografia.png         # Infografía del pipeline NLP
│   └── [resultados de backtesting]        # Generados en M4
│
├── TFM_Fase0_Diseno_Alcance.pdf           # Blueprint del proyecto
├── requirements.txt
└── README.md
```

---

## 🚀 Uso

El proyecto se ejecuta módulo a módulo en orden. Cada módulo produce un output que sirve como input del siguiente.

### Paso 1 — Perfilado NLP (M1)

```python
from src.m1_profiling import score_investor_profile

texto_usuario = "Prefiero inversiones seguras, no me gusta perder capital."
score, perfil = score_investor_profile(texto_usuario)
# score: 0.21  →  perfil: "conservador"
```

### Paso 2 — Universo de activos (M2)

```python
from src.m2_universe import build_asset_universe

returns = build_asset_universe(
    tickers=["AGG", "VTI", "EEM", "GLD", "TLT"],
    start="2015-01-01",
    end="2024-12-31"
)
```

### Paso 3 — Optimización (M3)

```python
from src.m3_optimizer import optimize_portfolio

weights = optimize_portfolio(
    returns=returns,
    max_volatility=score * 0.20,  # restricción derivada del perfil
    method="max_sharpe"           # o "hrp", "min_volatility"
)
```

### Paso 4 — Backtesting (M4)

```python
from src.m4_backtest import run_walkforward_backtest

results = run_walkforward_backtest(
    returns=returns,
    weights_fn=optimize_portfolio,
    profile_score=score,
    window_years=3,
    rebalance_freq="Q"
)
```

---

## 🏗️ Arquitectura del Sistema

El sistema se organiza en cinco módulos con flujo de datos unidireccional:

```
[Texto libre del usuario]
         │
         ▼
┌─────────────────────┐
│  M1 · Perfilado NLP │  FinBERT → score 0-1 → perfil {conservador, moderado, agresivo}
└─────────┬───────────┘
          │  score de riesgo (volatilidad máxima permitida)
          ▼
┌─────────────────────┐
│ M2 · Universo ETFs  │  yfinance → retornos diarios limpios
└─────────┬───────────┘
          │  matriz de retornos
          ▼
┌─────────────────────┐
│  M3 · Optimización  │  PyPortfolioOpt → pesos óptimos con restricción de vol.
└─────────┬───────────┘
          │  cartera ponderada
          ▼
┌─────────────────────┐
│ M4 · Backtesting    │  QuantStats → métricas vs S&P 500 y 60/40
└─────────┬───────────┘
          │  (opcional)
          ▼
┌─────────────────────┐
│  M5 · Demo          │  Streamlit → UI interactiva end-to-end
└─────────────────────┘
```

---

## 🔄 Pipeline NLP (M1 en detalle)

| Etapa | Descripción |
|---|---|
| **Entrada** | Texto libre del inversor (respuestas a cuestionario o descripción de objetivos) |
| **Tokenización** | `AutoTokenizer` de ProsusAI/finbert, max 512 tokens |
| **Inferencia** | FinBERT zero-shot → probabilidades {positive, negative, neutral} |
| **Agregación** | Score de riesgo = f(P_positive, P_negative) normalizado a [0, 1] |
| **Clasificación** | 0.0–0.33 → conservador · 0.34–0.66 → moderado · 0.67–1.0 → agresivo |
| **Salida** | `(score: float, label: str, volatility_cap: float)` |

**Dataset de validación:** Financial PhraseBank — 14.780 frases con cuatro niveles de acuerdo entre anotadores (`all_agree`, `75_agree`, `66_agree`, `50_agree`). Se usa el subconjunto `all_agree` (mayor calidad) para evaluar la precisión del modelo en dominio financiero.

---

## 📐 Metodología de Optimización (M3)

Para cada perfil se evalúan **tres candidatas** de cartera y se selecciona automáticamente la que maximiza el Sharpe ex-ante sujeta al cap de volatilidad del perfil:

| Perfil | Cap de vol. | Candidata principal | Candidata alternativa | Baseline |
|---|---|---|---|---|
| Conservador | 8 %  | Mínima Varianza (Markowitz, 1952) | Máximo Sharpe (Sharpe, 1966) | Equal-weight |
| Moderado    | 15 % | Máximo Sharpe                       | HRP (López de Prado, 2016)    | Equal-weight |
| Agresivo    | 25 % | HRP                                 | Máximo Sharpe                   | Equal-weight |

**Regla de selección:** se elige la cartera con mayor Sharpe ex-ante entre las que cumplen `vol_anual ≤ cap × 1,01`. La estimación de μ y Σ usa Ledoit-Wolf shrinkage (Ledoit & Wolf, 2004). Si todas las candidatas violan el cap, la cartera ganadora se mezcla linealmente con cash (rf anual = 2 %) hasta cumplirlo.

El cap de volatilidad de cada perfil queda fijado por el perfilado de M1 (cuestionario MiFID II + análisis de sentimiento NLP), bajo el principio de **prudencia asimétrica**: la señal NLP solo puede *rebajar* el perfil de riesgo, nunca elevarlo.

---

## 📊 Validación y Backtesting (M4)

El backtesting se implementa mediante **walk-forward validation** para evitar look-ahead bias:
- Ventana de entrenamiento: 3 años
- Ventana de test: 1 año
- Rebalanceo: trimestral

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

**Precisión del modelo NLP (M1)** sobre Financial PhraseBank (subconjunto `allagree`, n = 2.264), zero-shot con FinBERT:

| Métrica | Valor |
|---|---|
| Accuracy | 0,9717 |
| F1-Score (macro) | 0,9625 |
| Clases evaluadas | negative / neutral / positive |

---

## 📚 Referencias Clave

- Markowitz, H. (1952). *Portfolio Selection*. Journal of Finance, 7(1), 77–91.
- Sharpe, W. F. (1966). *Mutual Fund Performance*. Journal of Business, 39(1), 119–138.
- Ledoit, O. & Wolf, M. (2004). *Honey, I Shrunk the Sample Covariance Matrix*. Journal of Portfolio Management, 30(4), 110–119.
- López de Prado, M. (2016). *Building Diversified Portfolios that Outperform Out-of-Sample*. Journal of Portfolio Management, 42(4).
- Yang, Y. et al. (2020). *FinBERT: A Pretrained Language Model for Financial Communications*. arXiv:2006.08097.
- Malo, P. et al. (2014). *Good Debt or Bad Debt: Detecting Semantic Orientations in Economic Texts*. JASIST (Financial PhraseBank).

---

## 📄 Licencia

This project is for educational purposes. Please check their terms before any commercial use.
