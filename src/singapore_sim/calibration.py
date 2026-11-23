"""Fuel- and driver-adjusted OLS calibration on clean Singapore GP laps."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from singapore_sim.config import CalibratedParams


def calibrate_ols_from_df(clean_laps: pd.DataFrame) -> Tuple[CalibratedParams, pd.DataFrame, float]:
    """Fit fuel- and driver-adjusted OLS model on clean green-flag laps.

    Model:
        LapTime_s ~ C(DriverSeason) + LapNumber + C(Compound, Treatment('HARD')) * TyreAge0
    """
    df_fit = clean_laps[clean_laps["LapNumber"] >= 2].copy()
    df_fit["TyreAge0"] = df_fit["TyreLife"] - 1.0
    df_fit["DriverSeason"] = df_fit["Season"].astype(str) + "_" + df_fit["Driver"].astype(str)

    ols_fit = smf.ols(
        "LapTime_s ~ C(DriverSeason) + LapNumber + C(Compound, Treatment(reference='HARD')) * TyreAge0",
        data=df_fit,
    ).fit()

    params = ols_fit.params
    key_terms = [k for k in params.index if not k.startswith("C(DriverSeason)")]
    summary_df = pd.DataFrame(
        {
            "coef": ols_fit.params[key_terms],
            "std_err": ols_fit.bse[key_terms],
            "t": ols_fit.tvalues[key_terms],
            "p_value": ols_fit.pvalues[key_terms],
        }
    )

    ds_2025 = [k for k in params.index if k.startswith("C(DriverSeason)[T.2025_")]
    median_2025_shift = float(np.median([params[k] for k in ds_2025])) if ds_2025 else 0.0

    t_base = float(params["Intercept"] + median_2025_shift)
    fuel_effect = float(params["LapNumber"])

    delta = {
        "HARD": 0.0,
        "MEDIUM": float(params.get("C(Compound, Treatment(reference='HARD'))[T.MEDIUM]", -0.45)),
        "SOFT": float(params.get("C(Compound, Treatment(reference='HARD'))[T.SOFT]", -0.90)),
    }

    beta_hard = float(params["TyreAge0"])
    beta = {
        "HARD": beta_hard,
        "MEDIUM": beta_hard
        + float(params.get("C(Compound, Treatment(reference='HARD'))[T.MEDIUM]:TyreAge0", 0.0)),
        "SOFT": beta_hard
        + float(params.get("C(Compound, Treatment(reference='HARD'))[T.SOFT]:TyreAge0", 0.0)),
    }
    sigma = float(np.std(ols_fit.resid, ddof=1))

    return (
        CalibratedParams(
            t_base=t_base,
            fuel_effect=fuel_effect,
            delta=delta,
            beta=beta,
            sigma=sigma,
        ),
        summary_df,
        float(ols_fit.rsquared),
    )


def calibrate_ols_from_csv(csv_path: str | Path) -> Tuple[CalibratedParams, pd.DataFrame, float]:
    """Load clean lap CSV and fit the OLS calibration model."""
    df = pd.read_csv(csv_path)
    return calibrate_ols_from_df(df)
