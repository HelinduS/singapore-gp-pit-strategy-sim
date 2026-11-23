"""Stretch Goal (X3): Two-car track position & overtaking threshold model."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

from singapore_sim.config import CalibratedParams, DEFAULT_PARAMS, RaceConfig
from singapore_sim.dtmc import generate_sc_scenarios
from singapore_sim.simulator import find_optimal_pit_laps


def simulate_two_car_traffic(
    pit_loss_s: float,
    p_sc_deploy: float,
    overtake_threshold_s: float = 1.2,
    dirty_air_gap_s: float = 0.8,
    params: CalibratedParams = DEFAULT_PARAMS,
    config: RaceConfig = RaceConfig(),
    n_sims: int = 3000,
    sc_window: int | None = None,
    seed: int = 42,
    noise_seed_a: int = 101,
    noise_seed_b: int = 202,
) -> tuple[float, float, float]:
    """Simulate Car A (1-stop) vs Car B (2-stop) with track-position blocking.

    When overtake_threshold_s == 0.0, Car B is never blocked and the result
    reduces identically to independent single-car CRN simulation.

    Returns:
        (mean_diff_s, ci_95_s, mean_laps_blocked)
    """
    eff_window = config.sc_window if sc_window is None else sc_window
    opt_1, opt_2, _ = find_optimal_pit_laps(params=params, config=config)

    sc_mat = generate_sc_scenarios(p_sc_deploy=p_sc_deploy, n_sims=n_sims, seed=seed, config=config)
    noise_a = np.random.default_rng(noise_seed_a).normal(0.0, params.sigma, size=(n_sims, config.total_laps))
    noise_b = np.random.default_rng(noise_seed_b).normal(0.0, params.sigma, size=(n_sims, config.total_laps))

    def setup_car(pit_laps: list[int], compounds: list[str]) -> dict:
        return {
            "n_stops": len(pit_laps),
            "targets": np.array(pit_laps, dtype=np.int32),
            "delta": np.array([params.delta[c] for c in compounds], dtype=np.float64),
            "beta": np.array([params.beta[c] for c in compounds], dtype=np.float64),
            "stint": np.zeros(n_sims, dtype=np.int32),
            "age": np.zeros(n_sims, dtype=np.float64),
            "cum_t": np.zeros(n_sims, dtype=np.float64),
        }

    car_a = setup_car(opt_1, ["MEDIUM", "HARD"])
    car_b = setup_car(opt_2, ["MEDIUM", "MEDIUM", "HARD"])
    laps_blocked = np.zeros(n_sims, dtype=np.int16)

    for lap in range(1, config.total_laps + 1):
        idx = lap - 1
        is_sc = sc_mat[:, idx] == 1

        def raw_lap(car: dict, n_arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
            g_t = (
                params.t_base
                + params.fuel_effect * lap
                + car["delta"][car["stint"]]
                + car["beta"][car["stint"]] * car["age"]
                + n_arr[:, idx]
            )
            lap_t = np.where(is_sc, config.t_sc, g_t)
            has_left = car["stint"] < car["n_stops"]
            nxt = car["targets"][np.minimum(car["stint"], car["n_stops"] - 1)]
            pit = (has_left & (lap == nxt)) | (
                has_left
                & is_sc
                & (eff_window > 0)
                & (lap >= nxt - eff_window)
                & (lap <= nxt)
                & (car["age"] >= config.min_stint_age_for_sc_pit)
            )
            eff_loss = np.where(is_sc, pit_loss_s * (1.0 - config.sc_pit_discount), pit_loss_s)
            return lap_t + np.where(pit, eff_loss, 0.0), pit

        ta, pit_a = raw_lap(car_a, noise_a)
        tb, pit_b = raw_lap(car_b, noise_b)

        if overtake_threshold_s > 0.0:
            b_behind = car_b["cum_t"] > car_a["cum_t"]
            pace_adv_b = ta - tb
            would_enter_dirty_air = (car_b["cum_t"] + tb) < (car_a["cum_t"] + ta + dirty_air_gap_s)
            blocked = (
                (~is_sc)
                & (~pit_a)
                & (~pit_b)
                & b_behind
                & would_enter_dirty_air
                & (pace_adv_b > 0.0)
                & (pace_adv_b < overtake_threshold_s)
            )
            tb_adj = np.where(
                blocked,
                np.maximum(tb, (car_a["cum_t"] + ta + dirty_air_gap_s) - car_b["cum_t"]),
                tb,
            )
            laps_blocked += blocked.astype(np.int16)
        else:
            tb_adj = tb

        car_a["cum_t"] += ta
        car_b["cum_t"] += tb_adj
        for car, pit in [(car_a, pit_a), (car_b, pit_b)]:
            car["stint"] = np.where(pit, car["stint"] + 1, car["stint"])
            car["age"] = np.where(pit, 0.0, car["age"] + 1.0)

    diff = car_b["cum_t"] - car_a["cum_t"]
    return (
        float(np.mean(diff)),
        float(1.96 * np.std(diff, ddof=1) / np.sqrt(n_sims)),
        float(np.mean(laps_blocked)),
    )


def run_traffic_sweep(
    pit_losses: Iterable[float],
    thresholds: Iterable[float] = (0.0, 1.0, 1.5, 2.0),
    p_sc_deploy: float = 0.025,
    params: CalibratedParams = DEFAULT_PARAMS,
    config: RaceConfig = RaceConfig(),
    n_sims: int = 3000,
    seed: int = 42,
) -> pd.DataFrame:
    """Sweep pit-stop loss across overtaking thresholds at fixed Safety Car probability."""
    rows = []
    for thr in thresholds:
        for loss in pit_losses:
            mean_diff, ci_95, avg_blk = simulate_two_car_traffic(
                pit_loss_s=float(loss),
                p_sc_deploy=p_sc_deploy,
                overtake_threshold_s=float(thr),
                params=params,
                config=config,
                n_sims=n_sims,
                seed=seed,
            )
            rows.append(
                {
                    "overtake_threshold_s": float(thr),
                    "pit_loss_s": float(loss),
                    "mean_diff_s": mean_diff,
                    "ci_95_s": ci_95,
                    "avg_laps_blocked": avg_blk,
                }
            )
    return pd.DataFrame(rows)
