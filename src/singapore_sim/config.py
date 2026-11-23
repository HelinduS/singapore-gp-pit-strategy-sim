"""Configuration constants and calibrated parameter containers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RaceConfig:
    """Circuit and Safety Car configuration for the 62-lap Singapore GP."""

    total_laps: int = 62
    t_sc: float = 132.0
    sc_pit_discount: float = 0.50
    l_sc_mean: float = 4.0
    sc_window: int = 8
    min_stint_age_for_sc_pit: int = 5


@dataclass(frozen=True)
class CalibratedParams:
    """Physical lap-time, fuel-burn, and tyre-degradation parameters."""

    t_base: float
    fuel_effect: float
    delta: dict[str, float] = field(default_factory=dict)
    beta: dict[str, float] = field(default_factory=dict)
    sigma: float = 0.8853


# Representative fallback parameters calibrated from 2023-2025 Singapore GP data
DEFAULT_PARAMS = CalibratedParams(
    t_base=99.85,
    fuel_effect=-0.062,
    delta={"HARD": 0.0, "MEDIUM": -0.35, "SOFT": -0.75},
    beta={"HARD": 0.032, "MEDIUM": 0.058, "SOFT": 0.095},
    sigma=0.8853,
)
