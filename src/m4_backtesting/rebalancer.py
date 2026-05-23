"""Lógica de rebalanceo: fechas por calendar + drift threshold opcional."""
from __future__ import annotations

import logging
from typing import Literal

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

RebalanceFreq = Literal["M", "Q", "Y"]


def compute_rebalance_dates(
    index: pd.DatetimeIndex,
    freq: RebalanceFreq = "Q",
) -> list[pd.Timestamp]:
    """Calcula las fechas de rebalanceo por calendar.

    Devuelve la última fecha hábil presente en `index` dentro de cada periodo
    (mes, trimestre, año), excluyendo la primera fecha del índice (que es el
    inicio del backtest, no un rebalanceo).

    Args:
        index: DatetimeIndex del periodo OOS.
        freq: 'M' (mensual), 'Q' (trimestral) o 'Y' (anual).

    Returns:
        Lista de Timestamps con las fechas de rebalanceo ordenadas.
    """
    if len(index) == 0:
        return []

    # Agrupamos por periodo y nos quedamos con el último día hábil de cada uno
    period_freq_map: dict[str, str] = {"M": "M", "Q": "Q", "Y": "Y"}
    period_str = period_freq_map[freq]
    series = pd.Series(index, index=index)
    last_per_period = series.groupby(series.dt.to_period(period_str)).max()

    # Excluimos la primera fecha del índice (no es un rebalanceo, es t=0)
    first_date = index[0]
    dates = [d for d in last_per_period.tolist() if d > first_date]
    return sorted(dates)


def detect_drift(
    current_weights: dict[str, float],
    target_weights: dict[str, float],
    threshold: float,
) -> bool:
    """True si algún peso supera |w_actual - w_target| > threshold.

    Args:
        current_weights: pesos actuales (incluye CASH si aplica).
        target_weights: pesos objetivo del perfil.
        threshold: umbral absoluto de desviación (p.ej. 0.05 = 5pp).

    Returns:
        True si se debe rebalancear, False en caso contrario.
    """
    all_keys = set(current_weights.keys()) | set(target_weights.keys())
    for key in all_keys:
        delta = abs(current_weights.get(key, 0.0) - target_weights.get(key, 0.0))
        if delta > threshold:
            logger.debug(
                "Drift detected on %s: |%.4f - %.4f| = %.4f > %.4f",
                key,
                current_weights.get(key, 0.0),
                target_weights.get(key, 0.0),
                delta,
                threshold,
            )
            return True
    return False
