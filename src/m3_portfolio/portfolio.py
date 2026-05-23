"""Portfolio dataclass: container of weights and ex-ante metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class Portfolio:
    """Immutable container of an optimized portfolio.

    Attributes:
        profile: Risk profile name (e.g. "conservador").
        optimizer_name: Optimization strategy identifier.
        weights: Mapping ticker -> weight in [0, 1]. May include synthetic
            ``"CASH"`` entry when the optimized portfolio has been blended
            with risk-free cash to satisfy a volatility cap.
        cash_weight: Fraction allocated to cash (rf asset). 0.0 when the
            unconstrained optimum already respects the vol cap.
        expected_return: Annualised expected return (post cash blending).
        expected_volatility: Annualised expected volatility (post cash blending).
        expected_sharpe: ``(expected_return - risk_free_rate) / expected_volatility``.
        herfindahl_index: HHI computed over risk assets only (excludes CASH).
        n_effective_assets: Count of risk assets with weight above a threshold.
        constraints_satisfied: True when UCITS + vol cap pass at construction.
        validation_report: Post-hoc validation flags. Empty until populated by
            :func:`m3_portfolio.validators.validate_portfolio`.
    """

    profile: str
    optimizer_name: str
    weights: Dict[str, float]
    cash_weight: float
    expected_return: float
    expected_volatility: float
    expected_sharpe: float
    herfindahl_index: float
    n_effective_assets: int
    constraints_satisfied: bool
    validation_report: Dict[str, bool] = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"Portfolio(profile={self.profile!r}, optimizer={self.optimizer_name!r}, "
            f"ret={self.expected_return:.2%}, vol={self.expected_volatility:.2%}, "
            f"sharpe={self.expected_sharpe:.3f}, cash={self.cash_weight:.2%}, "
            f"hhi={self.herfindahl_index:.3f}, n_eff={self.n_effective_assets})"
        )

    def weight_string(self) -> str:
        """Compact string of non-zero weights, sorted descending."""
        items = sorted(self.weights.items(), key=lambda kv: -kv[1])
        return " | ".join(f"{t} {w:.1%}" for t, w in items if w > 0)
