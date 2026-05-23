"""Motor de backtesting: aplica pesos sobre retornos OOS con rebalanceo."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd

from m4_backtesting.rebalancer import (
    RebalanceFreq,
    compute_rebalance_dates,
    detect_drift,
)

logger = logging.getLogger(__name__)

CASH_TICKER = "CASH"  # debe coincidir con m3_portfolio.CASH_TICKER
TRADING_DAYS = 252


@dataclass
class BacktestResult:
    """Resultado de un backtest.

    Attributes:
        equity_curve: serie temporal con base 1.0 al inicio.
        returns: retornos diarios de la cartera.
        weights_history: pesos efectivos por fecha (pre-rebalanceo).
        rebalance_dates: fechas en las que se rebalanceó.
        config: snapshot de la configuración usada (para auditoría).
    """

    equity_curve: pd.Series
    returns: pd.Series
    weights_history: pd.DataFrame
    rebalance_dates: list[pd.Timestamp]
    config: dict = field(default_factory=dict)


class BacktestEngine:
    """Motor de simulación de cartera con rebalanceo.

    Aplica pesos objetivo sobre una matriz de retornos diarios, dejando que
    los pesos driften entre rebalanceos y reseteándolos al objetivo en cada
    fecha de rebalanceo (o cuando se supera el `drift_threshold` si está activo).

    El cash (si está presente en target_weights con clave CASH_TICKER) devenga
    el `rf_annual` diariamente como retorno fijo.

    Args:
        returns: DataFrame de retornos diarios OOS. Columnas = tickers,
            índice = DatetimeIndex. No debe contener CASH (se añade internamente).
        target_weights: pesos objetivo del perfil. Debe sumar 1 (con tolerancia 1e-6).
            Puede incluir la clave CASH_TICKER.
        rebalance_freq: 'M', 'Q' (default) o 'Y'.
        drift_threshold: si no es None, rebalanceo intra-periodo cuando algún
            peso se desvía más de este umbral absoluto.
        rf_annual: tasa libre de riesgo anual (decimal) para remunerar el cash.
        trading_days: periodos por año (252 por defecto).

    Raises:
        ValueError: si target_weights no suma 1, o contiene tickers no presentes
            en `returns` (excepto CASH_TICKER), o `returns` tiene NaN.
    """

    def __init__(
        self,
        returns: pd.DataFrame,
        target_weights: dict[str, float],
        rebalance_freq: RebalanceFreq = "Q",
        drift_threshold: float | None = None,
        rf_annual: float = 0.02,
        trading_days: int = TRADING_DAYS,
    ) -> None:
        self._validate_inputs(returns, target_weights)
        self.returns = returns.copy()
        self.target_weights = dict(target_weights)
        self.rebalance_freq = rebalance_freq
        self.drift_threshold = drift_threshold
        self.rf_annual = rf_annual
        self.trading_days = trading_days
        self._daily_cash_return = (1 + rf_annual) ** (1 / trading_days) - 1

    @staticmethod
    def _validate_inputs(
        returns: pd.DataFrame,
        target_weights: dict[str, float],
    ) -> None:
        if returns.empty:
            raise ValueError("returns DataFrame is empty.")
        if returns.isna().any().any():
            raise ValueError("returns contains NaN values; clean before backtesting.")
        weight_sum = sum(target_weights.values())
        if not np.isclose(weight_sum, 1.0, atol=1e-6):
            raise ValueError(
                f"target_weights must sum to 1.0 (got {weight_sum:.6f})."
            )
        missing = [
            t for t in target_weights if t != CASH_TICKER and t not in returns.columns
        ]
        if missing:
            raise ValueError(
                f"target_weights contains tickers not in returns columns: {missing}"
            )

    def run(self) -> BacktestResult:
        """Ejecuta el backtest y devuelve el resultado."""
        # Construimos un universo extendido que incluye CASH
        tickers_active = [t for t in self.target_weights if t != CASH_TICKER]
        has_cash = CASH_TICKER in self.target_weights

        # Matriz de retornos extendida con columna CASH
        rets_extended = self.returns[tickers_active].copy()
        if has_cash:
            rets_extended[CASH_TICKER] = self._daily_cash_return

        # Fechas de rebalanceo por calendar
        calendar_rebalances = set(
            compute_rebalance_dates(rets_extended.index, freq=self.rebalance_freq)
        )

        # Estado inicial
        current_weights = dict(self.target_weights)
        equity_value = 1.0
        equity_history: list[float] = [equity_value]
        return_history: list[float] = [0.0]
        weights_history_rows: list[dict] = [
            {"date": rets_extended.index[0], **current_weights}
        ]
        rebalance_dates_log: list[pd.Timestamp] = []

        for i in range(1, len(rets_extended)):
            date = rets_extended.index[i]
            r_t = rets_extended.iloc[i]

            # Retorno diario de la cartera con los pesos actuales (pre-drift)
            portfolio_return = float(
                sum(current_weights.get(t, 0.0) * r_t[t] for t in r_t.index)
            )
            equity_value *= 1 + portfolio_return

            # Drift: los pesos se actualizan proporcionalmente al rendimiento
            # w_new = w_old * (1 + r_t) / (1 + portfolio_return)
            new_weights: dict[str, float] = {}
            denom = 1 + portfolio_return
            for ticker in current_weights:
                r_ticker = float(r_t[ticker])
                new_weights[ticker] = current_weights[ticker] * (1 + r_ticker) / denom
            current_weights = new_weights

            # ¿Toca rebalancear?
            do_rebalance = False
            if date in calendar_rebalances:
                do_rebalance = True
            elif self.drift_threshold is not None and detect_drift(
                current_weights, self.target_weights, self.drift_threshold
            ):
                do_rebalance = True

            if do_rebalance:
                current_weights = dict(self.target_weights)
                rebalance_dates_log.append(date)
                logger.debug("Rebalanced at %s", date)

            equity_history.append(equity_value)
            return_history.append(portfolio_return)
            weights_history_rows.append({"date": date, **current_weights})

        equity_curve = pd.Series(equity_history, index=rets_extended.index, name="equity")
        returns_series = pd.Series(
            return_history, index=rets_extended.index, name="returns"
        )
        weights_history_df = pd.DataFrame(weights_history_rows).set_index("date")

        config_snapshot = {
            "rebalance_freq": self.rebalance_freq,
            "drift_threshold": self.drift_threshold,
            "rf_annual": self.rf_annual,
            "trading_days": self.trading_days,
            "target_weights": self.target_weights,
            "n_rebalances": len(rebalance_dates_log),
        }
        logger.info(
            "Backtest done: %d days, %d rebalances, final_equity=%.4f",
            len(equity_curve),
            len(rebalance_dates_log),
            equity_value,
        )

        return BacktestResult(
            equity_curve=equity_curve,
            returns=returns_series,
            weights_history=weights_history_df,
            rebalance_dates=rebalance_dates_log,
            config=config_snapshot,
        )
