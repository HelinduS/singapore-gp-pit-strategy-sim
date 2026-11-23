# Singapore GP Pit Strategy Sim — Theory, Equations, and Numerical Verification

## 1. Empirical Lap-Time, Fuel-Burn, and Tyre-Degradation Model
For race lap $t \in \{1, \dots, 62\}$ on compound $c \in \{\text{SOFT}, \text{MEDIUM}, \text{HARD}\}$ with zero-indexed tyre age $a_t = \text{TyreLife}_t - 1 \ge 0$:

$$T_t = T_{\text{base}} + \gamma \cdot t + \Delta_c + \beta_c a_t + \varepsilon_t, \quad \varepsilon_t \sim \mathcal{N}(0, \sigma^2)$$

where:
- $T_{\text{base}}$ is the representative 2025 front-runner baseline pace on fresh `HARD` tyres;
- $\gamma < 0$ (`FUEL_EFFECT`) captures fuel-mass burn over the 62-lap race;
- $\Delta_c$ is the compound pace offset relative to `HARD` ($\Delta_{\text{HARD}} = 0$);
- $\beta_c$ is the linear tyre degradation slope (s/lap);
- $\sigma$ is the within-driver residual standard deviation.

Parameters are estimated via driver-season-adjusted OLS on clean green-flag laps ($t \ge 2$) from the 2023–2025 Singapore Grands Prix (`data/singapore_2023_2024_2025_clean_laps.csv`).

## 2. Two-State Discrete-Time Markov Chain (DTMC)
Race neutralization follows a two-state Markov chain with states $\{0: \text{Green}, 1: \text{Safety Car}\}$:

$$P = \begin{pmatrix} 1 - p_{01} & p_{01} \\ p_{10} & 1 - p_{10} \end{pmatrix}, \quad \pi_1 = \frac{p_{01}}{p_{01} + p_{10}}$$

where $p_{01} = p_{\text{SC}}$ is the per-lap Safety Car deployment probability and $p_{10} = 1 / L_{\text{SC}}$ ($L_{\text{SC}} = 4.0$ laps) is the per-lap green-flag resumption probability. Under Safety Car conditions, lap time is neutralized to $T_{\text{SC}} = 132.0\text{ s}$ and pit-stop time loss is discounted by $50\%$.

## 3. Common Random Numbers (CRN) Variance Reduction
To compare 2-stop ($T_2$) against 1-stop ($T_1$) with minimal Monte Carlo variance, both strategies are evaluated on the exact same $(N_{\text{sims}} \times 62)$ Safety Car scenario matrix and paired Gaussian lap-noise matrices, yielding:

$$\operatorname{Var}(T_2 - T_1) = \operatorname{Var}(T_2) + \operatorname{Var}(T_1) - 2\operatorname{Cov}(T_2, T_1)$$

with $95\%$ confidence interval $\bar{D} \pm 1.96 \cdot s_D / \sqrt{N_{\text{sims}}}$.

## 4. Two-Car Track Position & Overtaking Threshold (X3)
In the two-car extension (`src/singapore_sim/traffic.py`), Car A executes the optimal 1-stop and Car B executes the optimal 2-stop. When Car B trails Car A on a green-flag lap and would enter Car A's dirty-air wake ($< 0.8\text{ s}$) with a pace advantage $0 < T_{A,t} - T_{B,t} < \theta_{\text{overtake}}$, Car B is held behind Car A at the dirty-air gap. Setting $\theta_{\text{overtake}} = 0.0\text{ s}$ recovers the single-car free-air result identically.

## 5. Verification Benchmarks
All numerical checks are verified in the notebook:
1. **Deterministic Closed-Form Check:** With $\sigma = 0$ and $p_{\text{SC}} = 0$, simulated total race time matches the exact arithmetic series to $< 10^{-9}\text{ s}$.
2. **Analytic Pit-Lap Check:** Under symmetric linear degradation and zero fuel effect, grid search recovers $p^* = \lfloor N/2 \rfloor = 31$.
3. **DTMC Stationary Distribution Check:** Matrix power iteration $P^{500}$ and long-horizon Monte Carlo occupancy converge to $\pi_1$.
4. **CRN Variance Reduction Check:** Paired $\operatorname{Var}(T_2 - T_1)$ is strictly smaller than independent-run variance.
5. **X3 Free-Air Limit Check:** `simulate_two_car_traffic(..., overtake_threshold_s=0.0)` matches independent single-car CRN simulation to $< 10^{-12}\text{ s}$.
