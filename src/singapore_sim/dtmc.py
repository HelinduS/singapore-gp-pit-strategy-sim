"""Two-state Discrete-Time Markov Chain (DTMC) for Safety Car neutralization."""

from __future__ import annotations

import numpy as np

from singapore_sim.config import RaceConfig


def compute_stationary_distribution(p_sc_deploy: float, l_sc_mean: float = 4.0) -> tuple[float, float]:
    """Return analytical stationary probabilities (pi_green, pi_sc) for the 2-state DTMC."""
    if p_sc_deploy < 0.0 or p_sc_deploy > 1.0:
        raise ValueError(f"p_sc_deploy must be in [0, 1], got {p_sc_deploy}")
    if l_sc_mean <= 0.0:
        raise ValueError(f"l_sc_mean must be positive, got {l_sc_mean}")
    p_10 = 1.0 / l_sc_mean
    if p_sc_deploy == 0.0:
        return 1.0, 0.0
    pi_sc = p_sc_deploy / (p_sc_deploy + p_10)
    return 1.0 - pi_sc, pi_sc


def generate_sc_scenarios(
    p_sc_deploy: float,
    n_sims: int,
    seed: int = 42,
    config: RaceConfig = RaceConfig(),
) -> np.ndarray:
    """Simulate an (n_sims, total_laps) binary Safety Car matrix via DTMC.

    State 0 = Green flag, State 1 = Safety Car.
    Lap 1 always starts under Green flag.
    """
    if p_sc_deploy < 0.0 or p_sc_deploy > 1.0:
        raise ValueError(f"p_sc_deploy must be in [0, 1], got {p_sc_deploy}")
    if n_sims <= 0:
        raise ValueError(f"n_sims must be positive, got {n_sims}")

    rng = np.random.default_rng(seed)
    p_10 = 1.0 / config.l_sc_mean
    sc_matrix = np.zeros((n_sims, config.total_laps), dtype=np.int8)

    if p_sc_deploy == 0.0:
        return sc_matrix

    state = np.zeros(n_sims, dtype=np.int8)
    for lap_idx in range(1, config.total_laps):
        u = rng.random(n_sims)
        to_sc = (state == 0) & (u < p_sc_deploy)
        stay_sc = (state == 1) & (u < (1.0 - p_10))
        state = (to_sc | stay_sc).astype(np.int8)
        sc_matrix[:, lap_idx] = state

    return sc_matrix
