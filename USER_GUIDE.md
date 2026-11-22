# Singapore GP Pit Strategy Sim — User Guide

## Running the Notebook Locally
1. Install dependencies from `requirements.txt`.
2. Open `notebook/singapore-gp-pit-strategy-sim.ipynb` in VS Code or JupyterLab.
3. Run all cells from top to bottom. If live FastF1 endpoints are unreachable, the notebook automatically falls back to calibrated Marina Bay parameters or cached CSV data in `data/`.

## Interactive Web Demo (`docs/index.html`)
- **Pit-Stop Time Loss (s):** Adjusts green-flag pit-lane loss from 15 s to 30 s.
- **Safety Car Probability ($p_{\text{SC}}$):** Adjusts per-lap probability of transitioning from Green to Safety Car.
- **Degradation Multiplier:** Scales compound degradation slopes $\beta_c$.
- **Controls:** Use **Start / Pause / Reset** to run Monte Carlo replications and compare 1-stop vs. 2-stop race-time distributions.
