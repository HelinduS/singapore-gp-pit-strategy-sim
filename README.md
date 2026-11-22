# Singapore GP Pit Strategy Sim

**When Does a Two-Stop Beat a One-Stop at the Singapore Grand Prix?**

A stochastic Monte Carlo and discrete-time Markov chain (DTMC) race-strategy simulator quantifying the break-even pit-stop time loss at Marina Bay Street Circuit.

- **Live Web Demo:** `https://<your-github-username>.github.io/singapore-gp-pit-strategy-sim/`
- [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/<your-github-username>/singapore-gp-pit-strategy-sim/blob/main/notebook/singapore-gp-pit-strategy-sim.ipynb)

## Overview & Question

At the Marina Bay Street Circuit, high pit-lane time loss historically locked teams into one-stop strategies. Raising the Singapore pit-lane speed limit in 2025 cut pit-stop loss from roughly 28 s to 21 s, yet one-stop strategies still dominated. At the same time, Safety Car deployments strongly discount pit-stop loss—and Marina Bay shifted from a 100% Safety Car streak (2008–2023) to zero Safety Cars in 2024 and 2025.

**Core Question:** How small must the green-flag pit-stop time loss be before a two-stop strategy outperforms a one-stop on expected 62-lap race time, and how does the per-lap Safety Car probability shift that break-even threshold?

## Quick Start

### Run Locally in VS Code / Jupyter
```bash
git clone https://github.com/<your-github-username>/singapore-gp-pit-strategy-sim.git
cd singapore-gp-pit-strategy-sim
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter lab notebook/singapore-gp-pit-strategy-sim.ipynb
```

### Open the Interactive Web Demo
Open `docs/index.html` directly in any modern browser (Chrome, Edge, Firefox) or visit the GitHub Pages link above.

## User Guide

See [USER_GUIDE.md](USER_GUIDE.md) for parameter definitions, interactive controls, and sample scenarios.

## Model and Mathematics Summary

Lap time $T_t$ on lap $t$ with compound $c$ and tyre age $a_t$ is modeled as $T_t = T_{\text{base}} + \Delta_c + \beta_c (a_t - 1) + \varepsilon_t$ with $\varepsilon_t \sim \mathcal{N}(0, \sigma^2)$, calibrated via OLS regression on clean green-flag laps from the 2023–2024 Singapore Grands Prix. Race neutralization follows a two-state discrete-time Markov chain ($\text{Green} \leftrightarrow \text{Safety Car}$), discounting pit-stop loss under Safety Car conditions. Full derivations and verification proofs are documented in [THEORY.md](THEORY.md).

## Verification

The simulator is verified against three analytical benchmarks before running parameter sweeps:
1. **Deterministic Limit vs. Closed-Form Sum:** Setting $\sigma = 0$ and $p_{\text{SC}} = 0$ matches the exact arithmetic series total race time to machine precision ($< 10^{-9}$ s).
2. **Analytic Optimal Pit Lap vs. Grid Search:** Under symmetric linear degradation, grid search recovers the exact analytical optimum $p^* = N / 2 = 31$.
3. **DTMC Stationary Distribution:** Matrix power iteration $P^{500}$ converges to the analytical stationary probability $\pi_1 = p_{01} / (p_{01} + p_{10})$ within $10^{-6}$.

## Concepts Applied

This project applies empirical input modelling and ordinary least-squares parameter calibration, normal and uniform random variate generation, a two-state discrete-time Markov chain (DTMC) for race neutralization, and vectorized Monte Carlo integration with Law of Large Numbers confidence intervals, verified against closed-form deterministic limits and stationary chain distributions.

## Results, Limitations & Future Work

- **Results:** Under zero-Safety-Car conditions ($p_{\text{SC}} = 0$), green-flag pit-stop loss must drop below ~16–18 s before a two-stop strategy breaks even against a one-stop, explaining why teams remained on one-stop plans even after the 2025 pit-lane speed limit increase (~21 s loss). Higher Safety Car deployment probabilities shift the break-even threshold upward toward 20–22 s.
- **Limitations:** The baseline model simulates a single car in free air without track-position traffic penalties, out-lap tyre warm-up transient losses, or fuel-burn mass evolution.
- **Future Work:** Extend the simulator to a multi-car field with overtaking time-loss thresholds and Bayesian MCMC posterior sampling over tyre degradation rates.

## Key References

1. A. M. Law, *Simulation Modeling and Analysis*, 5th ed. McGraw-Hill, 2015.
2. FastF1 Python Library, Formula 1 Timing & Telemetry Data API (`https://docs.fastf1.dev/`).

Full bibliography with DOIs and links is available in [REFERENCES.md](REFERENCES.md).

## AI-Assistance Note

AI coding and writing assistants were used during development for scaffolding, code verification checks, and documentation structure; all equations, statistical fits, and numerical assertions were independently verified.

## Licence & Data Credits

- **Code Licence:** MIT License (see [LICENSE](LICENSE)).
- **Data Credits:** Historical Formula 1 session timing data accessed via the open-source FastF1 interface for non-commercial analytical research.
