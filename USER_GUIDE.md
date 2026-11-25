# Singapore GP Pit Strategy Sim — User Guide

## 1. Running the Notebook (Colab or Locally)
- **Google Colab (zero setup):** Open directly in [Google Colab](https://colab.research.google.com/github/HelinduS/singapore-gp-pit-strategy-sim/blob/main/notebook/singapore-gp-pit-strategy-sim.ipynb) and click **Runtime -> Run all**.
- **Locally:**
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Open `notebook/singapore-gp-pit-strategy-sim.ipynb` in VS Code or JupyterLab.
3. Run all cells from top to bottom. The notebook automatically resolves repository-root `data/` and `figures/` paths and uses `data/singapore_2023_2024_2025_clean_laps.csv` if live FastF1 endpoints are unavailable.

## 2. Running the CLI Analysis
- Run the CLI calibration and parameter-sweep summary:
  ```bash
  python scripts/run_analysis.py --n-sims 4000 --seed 42
  ```
  Pass `--csv-out results/` to export `pit_loss_sweep.csv` and `traffic_sweep.csv`.

## 3. Interactive Web Demo (`docs/index.html`)
Open `docs/index.html` in any modern browser:
- **Pit-Stop Time Loss (s):** Adjusts green-flag pit-lane loss from 15 s to 30 s (presets: `17.5 s`, `2025 (~21 s)`, `Pre-2025 (28 s)`).
- **Safety Car Probability ($p_{\text{SC}}$):** Adjusts per-lap probability of transitioning from Green to Safety Car.
- **Degradation Multiplier:** Scales compound degradation slopes $\beta_c$.
- **Overtaking Threshold ($\theta$, X3):** Models Marina Bay dirty-air blocking when a faster 2-stopper catches a 1-stopper (`0.0 s` = free air).
- **Opportunistic SC Pit Window:** Enables pitting up to 8 laps early under a Safety Car (stint age $\ge 5$ laps) at a 50% pit-loss discount.
- **Scenario Presets & Export:** Use **2024–25 Clean**, **Historic SC**, or **Traffic 2025** presets to jump to canonical regimes, and **Export Sweep CSV** to download the current break-even curve.
