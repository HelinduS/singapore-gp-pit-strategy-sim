"""CLI runner for calibrating, sweeping, and summarizing Singapore GP pit strategies."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from singapore_sim.calibration import calibrate_ols_from_csv  # noqa: E402
from singapore_sim.config import DEFAULT_PARAMS, RaceConfig  # noqa: E402
from singapore_sim.simulator import find_optimal_pit_laps, run_pit_loss_sweep  # noqa: E402
from singapore_sim.traffic import run_traffic_sweep  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Singapore GP Pit Strategy Monte Carlo & DTMC CLI")
    parser.add_argument("--n-sims", type=int, default=2000, help="Monte Carlo replications per grid point")
    parser.add_argument("--seed", type=int, default=42, help="Base RNG seed")
    parser.add_argument("--csv-out", type=Path, default=None, help="Optional directory to export sweep CSVs")
    args = parser.parse_args()

    csv_path = REPO_ROOT / "data" / "singapore_2023_2024_2025_clean_laps.csv"
    if csv_path.exists():
        params, _, r2 = calibrate_ols_from_csv(csv_path)
        print(f"Calibrated OLS from {csv_path.name} (R^2={r2:.4f}, sigma={params.sigma:.4f} s)")
    else:
        params = DEFAULT_PARAMS
        print("Using DEFAULT_PARAMS fallback.")

    config = RaceConfig()
    opt_1, opt_2, det_be = find_optimal_pit_laps(params=params, config=config)
    print(f"Optimal 1-stop (M->H): {opt_1} | Optimal 2-stop (M->M->H): {opt_2} | Det. break-even: {det_be:.2f} s")

    pit_losses = np.linspace(15.0, 30.0, 16)
    sc_probs = (0.000, 0.015, 0.030, 0.045)
    sweep_df = run_pit_loss_sweep(pit_losses, sc_probs, params=params, config=config, n_sims=args.n_sims, seed=args.seed)

    print("\n=== Break-Even Pit-Stop Loss by Safety Car Probability ===")
    for p_sc in sc_probs:
        sub = sweep_df[sweep_df["p_sc_deploy"] == p_sc]
        be = float(np.interp(0.0, sub["mean_diff_s"], sub["pit_loss_s"])) if sub["mean_diff_s"].iloc[0] <= 0 else float("nan")
        print(f"  p_SC={p_sc:.3f}/lap | P(any SC)={sub['p_any_sc'].iloc[0]*100:5.1f}% | Break-even={be:5.2f} s")

    traffic_df = run_traffic_sweep(pit_losses, thresholds=(0.0, 1.2, 2.0), p_sc_deploy=0.025, params=params, config=config, n_sims=args.n_sims, seed=args.seed)
    print("\n=== Two-Car Traffic Penalty (p_SC=0.025/lap, pit_loss=21.0 s) ===")
    for thr, grp in traffic_df.groupby("overtake_threshold_s"):
        row_21 = grp.loc[(grp["pit_loss_s"] - 21.0).abs().idxmin()]
        print(f"  threshold={thr:.1f} s/lap | E[T2-T1]={row_21['mean_diff_s']:+6.2f} s | avg_blocked={row_21['avg_laps_blocked']:4.2f} laps")

    if args.csv_out is not None:
        args.csv_out.mkdir(parents=True, exist_ok=True)
        sweep_df.to_csv(args.csv_out / "pit_loss_sweep.csv", index=False)
        traffic_df.to_csv(args.csv_out / "traffic_sweep.csv", index=False)
        print(f"\nExported sweep CSVs to {args.csv_out}")


if __name__ == "__main__":
    main()
