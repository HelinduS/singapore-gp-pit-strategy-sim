# Theory, Equations, and Numerical Verification

## 1. Lap-Time and Tyre Degradation Model
For race lap $t \in \{1, \dots, 62\}$ on compound $c \in \{\text{SOFT}, \text{MEDIUM}, \text{HARD}\}$ with tyre age $a_t \ge 1$:
$$T_t = T_{\text{base}} + \Delta_c + \beta_c (a_t - 1) + \varepsilon_t, \quad \varepsilon_t \sim \mathcal{N}(0, \sigma^2)$$

## 2. Two-State Discrete-Time Markov Chain (DTMC)
$$P = \begin{pmatrix} 1 - p_{01} & p_{01} \\ p_{10} & 1 - p_{10} \end{pmatrix}, \quad \pi_1 = \frac{p_{01}}{p_{01} + p_{10}}$$

## 3. Verification Checks
- **Deterministic Closed-Form Check:** Zero noise and zero Safety Car probability reduce total race time to an exact arithmetic series.
- **Analytic Pit-Lap Check:** Symmetric single-compound stints minimize total degradation at $p^* = \lfloor N/2 \rfloor$.
- **Stationary Distribution Check:** Long-run empirical and matrix-power state occupancy matches $\pi_1$.
