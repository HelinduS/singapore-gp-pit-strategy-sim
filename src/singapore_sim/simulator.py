"""Vectorized 62-lap Monte Carlo pit-strategy simulator with Common Random Numbers."""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
import pandas as pd

from singapore_sim.config import CalibratedParams, DEFAULT_PARAMS, RaceConfig
from singapore_sim.dtmc import generate_sc_scenarios


def deterministic_race_time(
    pit_laps: Sequence[int],
    compounds: Sequence[str],
    pit_loss_s: float,
    params: CalibratedParams = DEFAULT_PARAMS,
    config: RaceConfig = RaceConfig(),
) -> float:
    """Compute exact deterministic green-flag race time (sigma = 0, p_sc = 0)."""
    if len(compounds) != len(pit_laps) + 1:
        raise ValueError("len(compounds) must equal len(pit_laps) + 1")

    pit_set = set(pit_laps)
    stint_idx = 0
    tyre_age = 0
    total = 0.0
    for lap in range(1, config.total_laps + 1):
        c = compounds[stint_idx]
        total += params.t_base + params.fuel_effect * lap + params.delta[c] + params.beta[c] * tyre_age
        if lap in pit_set:
            total += pit_loss_s
            stint_idx += 1
            tyre_age = 0
        else:
            tyre_age += 1
    return total


def find_optimal_pit_laps(
    params: CalibratedParams = DEFAULT_PARAMS,
    config: RaceConfig = RaceConfig(),
) -> tuple[list[int], list[int], float]:
    """Grid search for optimal green-flag pit laps (1-stop M->H, 2-stop M->M->H).

    Returns:
        (opt_1_laps, opt_2_laps, deterministic_breakeven_pit_loss_s)
    """
    best_1_lap, best_1_t = min(
        (
            (p, deterministic_race_time([p], ["MEDIUM", "HARD"], 0.0, params=params, config=config))
            for p in range(10, config.total_laps - 9)
        ),
        key=lambda x: x[1],
    )
    best_2_laps, best_2_t = min(
        (
            (
                (p1, p2),
                deterministic_race_time([p1, p2], ["MEDIUM", "MEDIUM", "HARD"], 0.0, params=params, config=config),
            )
            for p1 in range(10, config.total_laps - 24)
            for p2 in range(p1 + 10, config.total_laps - 8)
        ),
        key=lambda x: x[1],
    )
    return [best_1_lap], list(best_2_laps), best_1_t - best_2_t


def simulate_strategy_on_scenarios(
    pit_laps: Sequence[int],
    compounds: Sequence[str],
    pit_loss_s: float,
    sc_matrix: np.ndarray,
    params: CalibratedParams = DEFAULT_PARAMS,
    config: RaceConfig = RaceConfig(),
    sigma: float | None = None,
    sc_window: int | None = None,
    noise_matrix: np.ndarray | None = None,
    noise_seed: int = 101,
) -> np.ndarray:
    """Simulate total race time across pre-generated Safety Car scenarios."""
    if len(compounds) != len(pit_laps) + 1:
        raise ValueError("len(compounds) must equal len(pit_laps) + 1")

    n_sims, n_laps = sc_matrix.shape
    if n_laps != config.total_laps:
        raise ValueError(f"sc_matrix must have {config.total_laps} columns, got {n_laps}")

    eff_sigma = params.sigma if sigma is None else sigma
    eff_window = config.sc_window if sc_window is None else sc_window

    if noise_matrix is not None:
        noise = noise_matrix
    elif eff_sigma > 0.0:
        noise = np.random.default_rng(noise_seed).normal(0.0, eff_sigma, size=(n_sims, n_laps))
    else:
        noise = np.zeros((n_sims, n_laps), dtype=np.float64)

    n_stops = len(pit_laps)
    targets = np.array(pit_laps, dtype=np.int32)
    c_delta = np.array([params.delta[c] for c in compounds], dtype=np.float64)
    c_beta = np.array([params.beta[c] for c in compounds], dtype=np.float64)

    stint = np.zeros(n_sims, dtype=np.int32)
    tyre_age = np.zeros(n_sims, dtype=np.float64)
    total_time = np.zeros(n_sims, dtype=np.float64)

    for lap in range(1, n_laps + 1):
        idx = lap - 1
        is_sc = sc_matrix[:, idx] == 1

        green_t = (
            params.t_base
            + params.fuel_effect * lap
            + c_delta[stint]
            + c_beta[stint] * tyre_age
            + noise[:, idx]
        )
        lap_t = np.where(is_sc, config.t_sc, green_t)

        has_stops_left = stint < n_stops
        next_target = targets[np.minimum(stint, max(n_stops - 1, 0))] if n_stops > 0 else np.zeros(n_sims, dtype=np.int32)

        scheduled_pit = has_stops_left & (lap == next_target)
        opportunistic_sc_pit = (
            has_stops_left
            & is_sc
            & (eff_window > 0)
            & (lap >= next_target - eff_window)
            & (lap <= next_target)
            & (tyre_age >= config.min_stint_age_for_sc_pit)
        )
        pit_now = scheduled_pit | opportunistic_sc_pit

        eff_pit_loss = np.where(is_sc, pit_loss_s * (1.0 - config.sc_pit_discount), pit_loss_s)
        total_time += lap_t + np.where(pit_now, eff_pit_loss, 0.0)

        stint = np.where(pit_now, stint + 1, stint)
        tyre_age = np.where(pit_now, 0.0, tyre_age + 1.0)

    return total_time


def run_pit_loss_sweep(
    pit_losses: Iterable[float],
    sc_probs: Iterable[float],
    params: CalibratedParams = DEFAULT_PARAMS,
    config: RaceConfig = RaceConfig(),
    sc_window: int | None = None,
    n_sims: int = 4000,
    seed: int = 42,
) -> pd.DataFrame:
    """Sweep pit-stop loss and Safety Car deployment probability using CRN."""
    opt_1, opt_2, _ = find_optimal_pit_laps(params=params, config=config)
    rows = []
    for p_sc in sc_probs:
        sc_mat = generate_sc_scenarios(p_sc_deploy=p_sc, n_sims=n_sims, seed=seed, config=config)
        p_any_sc = float(np.mean(sc_mat.any(axis=1)))
        for loss in pit_losses:
            t1 = simulate_strategy_on_scenarios(
                opt_1, ["MEDIUM", "HARD"], float(loss), sc_mat, params=params, config=config, sc_window=sc_window
            )
            t2 = simulate_strategy_on_scenarios(
                opt_2, ["MEDIUM", "MEDIUM", "HARD"], float(loss), sc_mat, params=params, config=config, sc_window=sc_window
            )
            diff = t2 - t1
            mean_diff = float(np.mean(diff))
            ci_95 = float(1.96 * np.std(diff, ddof=1) / np.sqrt(n_sims))
            rows.append(
                {
                    "p_sc_deploy": float(p_sc),
                    "p_any_sc": p_any_sc,
                    "pit_loss_s": float(loss),
                    "mean_diff_s": mean_diff,
                    "ci_95_s": ci_95,
                    "p_two_stop_faster": float(np.mean(diff < 0.0)),
                }
            )
    return pd.DataFrame(rows)
