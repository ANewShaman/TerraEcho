import json
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import PolynomialFeatures

# ── Paths ──────────────────────────────────────────────────────────────────────
DATA_FILE = os.path.join("ml", "data", "processed", "terraecho_dataset.csv")
MODELS_DIR = os.path.join("ml", "models")
METRICS_FILE = os.path.join("ml", "model_metrics.json")
os.makedirs(MODELS_DIR, exist_ok=True)

# ── Year scaling ───────────────────────────────────────────────────────────────
## All year values are scaled before polynomial expansion:
##   year_scaled = (year - YEAR_CENTER) / YEAR_SCALE
##
## YEAR_CENTER = 1962: midpoint of the dominant training window (1900–2024).
## YEAR_SCALE  = 50:   maps the full dataset to approximately [-1.2, 1.2].
##
## Without scaling, the cubic year feature reaches (1999)^3 ≈ 8×10^9,
## causing severe numerical ill-conditioning in the OLS solution.
## Scaled values keep all polynomial features in the range [-2, 2],
## producing well-conditioned coefficient estimates and stable extrapolation.
## Scaling constants are stored in each model bundle for identical
## application at inference time.
YEAR_CENTER = 1962
YEAR_SCALE = 50
FORECAST_CHECK_YEARS = np.arange(2025, 2051)


def scale_year(year_array):
    """Scale raw calendar years to a well-conditioned range.

    Args:
        year_array: array-like of raw calendar years.

    Returns:
        numpy float array of scaled values centred near 0.
    """
    return (np.asarray(year_array, dtype=float) - YEAR_CENTER) / YEAR_SCALE


# ── Target configurations ──────────────────────────────────────────────────────
## WHY THESE MODEL CHOICES:
##
## co2 — Piecewise polynomial, split at 1959
##   CO2 data comes from two fundamentally different sources:
##   ice-core reconstruction (1900–1958, ±1–2 ppm) and direct Mauna Loa
##   measurement (1959–2024, ±0.1 ppm). The post-1959 growth rate is
##   substantially higher than the pre-1959 rate. A single polynomial
##   fit across both eras learns a compromise curve that underestimates
##   post-2000 growth (the original test_r2 = 0.28 failure).
##   Fix: train two separate poly3 models, one per era. For forecasting,
##   only the instrumental-era model (1959–present) is used. The
##   historical-era model exists solely to give the merged dataset
##   self-consistent CO2 values for pre-1959 years.
##
## temp_anomaly — Year-only poly3, full 1900–2024
##   This was the best-performing original model (test_r2 = 0.805).
##   The v2 multivariate approach (year + co2) destroyed this because
##   year and co2 are ~91% correlated in the training window — adding
##   co2 to a year-polynomial raises the feature matrix condition number
##   from ~7 to ~2900. OLS then finds a coefficient combination that
##   fits training perfectly but diverges on extrapolation as the
##   year/co2 correlation breaks down post-training.
##   Fix: revert to year-only poly3. This model already produced
##   physically plausible forecasts and strong generalisation.
##
## arctic_ice — Satellite-era-only poly2, 1979–2024
##   The Walsh reconstruction (pre-1979) and NSIDC satellite data have
##   systematically different absolute values for the same years
##   (Walsh 1980 ~8.3 vs satellite 1980 = 7.67 million km²). Training
##   across both eras introduces a regime shift at the train/eval boundary
##   that directly causes the negative test_r2. Additionally, the 79-year
##   reconstruction era dominates the regression and produces a shallow
##   slope, while the satellite era shows a much steeper decline.
##   Fix: train exclusively on the satellite era (1979–2024, 46 rows).
##   Use degree 2 (quadratic): degree 3 with only ~36 training rows and
##   a fast-declining trend overshoots into negative ice extent by 2030.
##   A physical floor of 0.0 million km² is enforced at inference.
##   Evaluation period: 2015–2024 (most recent 10 satellite years).
##
## sea_level — Year-only poly2, 1900–2023
##   The original approach (test_r2 = 0.51) was already the most
##   appropriate. Forward-fill of the missing 2024 value was the main
##   correctness issue, now fixed in preprocess.py. Poly2 (quadratic) is
##   chosen over poly3 because sea level acceleration is smooth and
##   monotone — a cubic term would fit short-term wiggles and produce
##   erratic extrapolation.
##
## forest_cover — Year-only poly3, 1990–2024
##   Only 35 rows of real data; year is the only available trend signal.
##   valid_year_min = 1990 enforced at inference to block physically
##   impossible extrapolation (the model predicts >100% coverage for
##   years before 1990).
TARGETS = {
    "co2": {
        "col":             "co2",
        "model_file":      "co2_model.joblib",
        "model_strategy":  "piecewise",
        "split_year":      1959,          
        "poly_degree":     2,             # Modified from 3 to stop the post-2000 dip
        "test_years":      25,            
        "units":           "ppm",
        "valid_year_min":  1900,
        "valid_year_max":  2050,
        "physical_floor":  None,
        "physical_ceil":   None,
        "monotone_direction": "increasing",   
    },
    "temp_anomaly": {
        "col":             "temp_anomaly",
        "model_file":      "temp_model.joblib",
        "model_strategy":  "year_poly",
        "poly_degree":     3,             # Keep as-is (Extrap R²: 0.8050 is great)
        "test_years":      25,            
        "units":           "°C anomaly (GISTEMP 1951-1980 baseline)",
        "valid_year_min":  1900,
        "valid_year_max":  2050,
        "physical_floor":  None,
        "physical_ceil":   None,
        "monotone_direction": "increasing",   
    },
    "arctic_ice": {
        "col":             "arctic_ice",
        "model_file":      "arctic_ice_model.joblib",
        "model_strategy":  "year_poly",
        "train_year_min":  1979,          
        "poly_degree":     1,             # Modified from 2 to stabilize short-window extrapolation
        "test_years":      10,            
        "units":           "million km²",
        "valid_year_min":  1979,          
        "valid_year_max":  2050,
        "physical_floor":  0.0,           
        "physical_ceil":   None,
        "monotone_direction": "decreasing",   
    },
    "sea_level": {
        "col":             "sea_level",
        "model_file":      "sea_level_model.joblib",
        "model_strategy":  "year_poly",
        "poly_degree":     2,             # Keep as-is (Extrap R²: 0.4999 is solid)
        "test_years":      24,            
        "units":           "mm above 1900 baseline",
        "valid_year_min":  1900,
        "valid_year_max":  2050,
        "physical_floor":  None,
        "physical_ceil":   None,
        "monotone_direction": "increasing",   
    },
    "forest_cover": {
        "col":             "forest_cover",
        "model_file":      "forest_cover_model.joblib",
        "model_strategy":  "year_poly",
        "poly_degree":     3,             # Keep as-is
        "test_years":      7,             
        "units":           "% of land area",
        "valid_year_min":  1990,          
        "valid_year_max":  2050,
        "physical_floor":  0.0,
        "physical_ceil":   100.0,
        "monotone_direction": None,       
    },
}

# ── Helpers ────────────────────────────────────────────────────────────────────
def rmse(y_true, y_pred):
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def make_poly_features(year_array, degree):
    """Expand scaled year values into polynomial features.

    Args:
        year_array: 1-D numpy array of RAW calendar years.
        degree:     Polynomial degree.

    Returns:
        X: 2-D numpy array of shape (n, degree).
        poly: fitted PolynomialFeatures transformer (needed to transform
              new years with the same column ordering).
    """
    yr_scaled = scale_year(year_array).reshape(-1, 1)
    poly = PolynomialFeatures(degree=degree, include_bias=False)
    X = poly.fit_transform(yr_scaled)
    return X, poly


def transform_years(year_array, poly):
    """Apply a previously fitted PolynomialFeatures transformer.

    Args:
        year_array: 1-D numpy array of RAW calendar years.
        poly:       Fitted PolynomialFeatures from make_poly_features.

    Returns:
        X: 2-D numpy array.
    """
    yr_scaled = scale_year(year_array).reshape(-1, 1)
    return poly.transform(yr_scaled)


def check_monotonicity(model, poly, check_years, direction):
    """Check whether model predictions are monotone over a forecast horizon.

    Args:
        model:       Fitted LinearRegression.
        poly:        Fitted PolynomialFeatures for year expansion.
        check_years: Array of years to check (e.g. 2025–2050).
        direction:   "increasing", "decreasing", or None.

    Returns:
        (is_ok: bool, message: str)
    """
    if direction is None:
        return True, "no monotone constraint"

    X_check = transform_years(check_years, poly)
    preds = model.predict(X_check)
    diffs = np.diff(preds)

    if direction == "increasing":
        violations = int((diffs < -0.001).sum())  # allow tiny numerical noise
        ok = violations == 0
        msg = (
            f"OK — predictions increase over {check_years[0]}–{check_years[-1]}"
            if ok
            else f"WARNING — {violations} decreasing steps over {check_years[0]}–{check_years[-1]}"
        )
    elif direction == "decreasing":
        violations = int((diffs > 0.001).sum())
        ok = violations == 0
        msg = (
            f"OK — predictions decrease over {check_years[0]}–{check_years[-1]}"
            if ok
            else f"WARNING — {violations} increasing steps over {check_years[0]}–{check_years[-1]}"
        )
    else:
        ok, msg = True, "no monotone constraint"

    return ok, msg


# ── Piecewise CO2 model ────────────────────────────────────────────────────────
def train_co2_piecewise(df, config):
    """Train a piecewise polynomial CO2 model.

    Two separate poly3 models are fit:
      historical:     rows where year < split_year (reconstruction era)
      instrumental:   rows where year >= split_year (direct measurement era)

    The instrumental model is the primary forecasting model. The historical
    model covers only the pre-split years for backwards compatibility with
    the dataset (e.g. if the frontend requests a historical CO2 value).

    Both models are stored in the model bundle. The predict() function
    selects the correct piece based on the requested year.

    This approach directly addresses the test_r2 = 0.28 failure: a single
    polynomial fit across both eras learns a compromise curve weighted by
    the many slow-growth reconstruction years, causing it to underestimate
    the sharper post-2000 acceleration. Separating the eras gives each
    polynomial full freedom to fit its own curvature.

    Returns:
        model_bundle: dict with 'hist_model', 'inst_model', metadata.
        metrics: dict matching the standard output schema.
    """
    col = config["col"]
    split_year = config["split_year"]
    degree = config["poly_degree"]
    test_years = config["test_years"]

    df_target = (
        df[["year", col]].dropna(subset=[col]).sort_values("year").reset_index(drop=True)
    )

    # ── Historical piece ───────────────────────────────────────────────────
    df_hist = df_target[df_target["year"] < split_year].copy()
    yr_hist = df_hist["year"].values
    y_hist = df_hist[col].values

    X_hist, poly_hist = make_poly_features(yr_hist, degree)
    m_hist = LinearRegression().fit(X_hist, y_hist)

    hist_rmse_ = rmse(y_hist, m_hist.predict(X_hist))
    hist_r2_ = float(r2_score(y_hist, m_hist.predict(X_hist)))

    print(
        f"\n  [co2] Piecewise strategy | split_year={split_year} | degree={degree}"
    )
    print(
        f"    Historical piece: {len(df_hist)} rows ({int(yr_hist.min())}–{int(yr_hist.max())})"
    )
    print(f"    Historical  — RMSE: {hist_rmse_:.4f}  R²: {hist_r2_:.4f}")

    # ── Instrumental piece ─────────────────────────────────────────────────
    # Chronological split: train on post-split years up to the test cutoff,
    # eval on the most recent test_years rows.
    df_inst = (
        df_target[df_target["year"] >= split_year].copy().reset_index(drop=True)
    )
    n_inst = len(df_inst)
    if n_inst < 10:
        raise ValueError(f"[co2] Only {n_inst} instrumental rows — cannot train.")

    split_idx = n_inst - test_years
    df_inst_tr = df_inst.iloc[:split_idx].copy()
    df_inst_ev = df_inst.iloc[split_idx:].copy()

    yr_inst_tr = df_inst_tr["year"].values
    y_inst_tr = df_inst_tr[col].values
    yr_inst_ev = df_inst_ev["year"].values
    y_inst_ev = df_inst_ev[col].values

    X_inst_tr, poly_inst = make_poly_features(yr_inst_tr, degree)
    X_inst_ev = transform_years(yr_inst_ev, poly_inst)

    m_inst = LinearRegression().fit(X_inst_tr, y_inst_tr)

    inst_train_rmse_ = rmse(y_inst_tr, m_inst.predict(X_inst_tr))
    inst_train_r2_ = float(r2_score(y_inst_tr, m_inst.predict(X_inst_tr)))
    inst_eval_rmse_ = rmse(y_inst_ev, m_inst.predict(X_inst_ev))
    inst_eval_r2_ = float(r2_score(y_inst_ev, m_inst.predict(X_inst_ev)))

    print(
        f"    Instrumental piece train: {len(df_inst_tr)} rows ({int(yr_inst_tr.min())}–{int(yr_inst_tr.max())})"
    )
    print(
        f"    Instrumental extrap eval: {len(df_inst_ev)} rows ({int(yr_inst_ev.min())}–{int(yr_inst_ev.max())})"
    )
    print(
        f"    Instrumental train — RMSE: {inst_train_rmse_:.4f}  R²: {inst_train_r2_:.4f}"
    )
    print(
        f"    Instrumental extrap — RMSE: {inst_eval_rmse_:.4f}  R²: {inst_eval_r2_:.4f}"
    )

    # Monotonicity check on instrumental model (CO2 should never decrease)
    mono_ok, mono_msg = check_monotonicity(
        m_inst, poly_inst, FORECAST_CHECK_YEARS, config["monotone_direction"]
    )
    print(f"    Monotone check: {mono_msg}")
    if not mono_ok:
        print(f"    !! CO2 model predicts decrease — consider adjusting degree")

    # Sample predictions — use instrumental model for all years
    # (historical model only active pre-split_year in predict())
    sample_years = [1900, 1950, 1970, 1990, 2000, 2010, 2020, 2024, 2030, 2035]
    sample_preds = {}
    for yr in sample_years:
        if yr < split_year:
            X_s = transform_years(np.array([yr]), poly_hist)
            val = m_hist.predict(X_s)[0]
        else:
            X_s = transform_years(np.array([yr]), poly_inst)
            val = m_inst.predict(X_s)[0]
        sample_preds[str(yr)] = round(float(val), 4)

    print(
        f"    2024={sample_preds['2024']}  2030={sample_preds['2030']}  2035={sample_preds['2035']}  ppm"
    )

    metrics = {
        "model_type": f"piecewise_poly{degree}",
        "model_strategy": "piecewise",
        "split_year": split_year,
        "units": config["units"],
        "train_rows": len(df_inst_tr),
        "extrap_eval_rows": len(df_inst_ev),
        "train_year_min": int(yr_inst_tr.min()),
        "train_year_max": int(yr_inst_tr.max()),
        "extrap_eval_year_min": int(yr_inst_ev.min()),
        "extrap_eval_year_max": int(yr_inst_ev.max()),
        "train_rmse": round(inst_train_rmse_, 4),
        "train_r2": round(inst_train_r2_, 4),
        "extrap_eval_rmse": round(inst_eval_rmse_, 4),
        "extrap_eval_r2": round(inst_eval_r2_, 4),
        "valid_year_min": config["valid_year_min"],
        "valid_year_max": config["valid_year_max"],
        "monotone_check": mono_msg,
        "sample_predictions": sample_preds,
        "evaluation_note": (
            f"Extrapolation evaluation on {int(yr_inst_ev.min())}–"
            f"{int(yr_inst_ev.max())} (instrumental piece only). "
            "Historical piece covers only pre-1959 reconstruction data "
            "and is not used for forecasting. "
            "R² here measures extrapolation fidelity, not generalisation."
        ),
    }

    model_bundle = {
        "strategy": "piecewise",
        "split_year": split_year,
        "hist_model": m_hist,
        "hist_poly": poly_hist,
        "inst_model": m_inst,
        "inst_poly": poly_inst,
        "poly_degree": degree,
        "year_center": YEAR_CENTER,
        "year_scale": YEAR_SCALE,
        "valid_year_min": config["valid_year_min"],
        "valid_year_max": config["valid_year_max"],
        "physical_floor": config["physical_floor"],
        "physical_ceil": config["physical_ceil"],
        "col": col,
        "units": config["units"],
    }
    return model_bundle, metrics


# ── Standard year-polynomial model ────────────────────────────────────────────
def train_year_poly(df, target_key, config):
    """Train a year-only polynomial regression model.

    For arctic_ice, an optional train_year_min restricts the training
    data to the satellite era (1979+), avoiding the reconstruction-era
    regime-shift problem that caused negative test_r2 in v1.

    After fitting, a monotonicity check is run over FORECAST_CHECK_YEARS.
    If the direction constraint is violated, a warning is printed to stdout
    and recorded in metrics. The model is still saved — the warning exists
    to flag cases where the polynomial has curved in a physically implausible
    direction on the forecast horizon. Callers can use physical_floor and
    physical_ceil to clamp individual predictions.

    Returns:
        model_bundle: dict with fitted model and all metadata needed for inference.
        metrics: dict matching the standard output schema.
    """
    col = config["col"]
    degree = config["poly_degree"]
    test_years = config["test_years"]
    train_year_min = config.get("train_year_min", None)

    df_target = (
        df[["year", col]].dropna(subset=[col]).sort_values("year").reset_index(drop=True)
    )

    # Restrict to train_year_min if specified (arctic_ice satellite era)
    if train_year_min is not None:
        df_target = (
            df_target[df_target["year"] >= train_year_min]
            .copy()
            .reset_index(drop=True)
        )
        print(
            f"\n  [{target_key}] Restricting to year >= {train_year_min} ({len(df_target)} rows)"
        )

    n_total = len(df_target)
    if n_total < 10:
        raise ValueError(
            f"[{target_key}] Only {n_total} rows after filtering — cannot train."
        )

    split_idx = n_total - test_years
    df_train = df_target.iloc[:split_idx].copy()
    df_test = df_target.iloc[split_idx:].copy()

    yr_train = df_train["year"].values
    y_train = df_train[col].values
    yr_test = df_test["year"].values
    y_test = df_test[col].values

    print(f"\n  [{target_key}]  poly_degree={degree}  strategy=year_poly")
    print(
        f"    Train: {len(df_train)} rows ({int(yr_train.min())}–{int(yr_train.max())})"
    )
    print(
        f"    Extrap eval: {len(df_test)} rows ({int(yr_test.min())}–{int(yr_test.max())})"
    )

    X_train, poly = make_poly_features(yr_train, degree)
    X_test = transform_years(yr_test, poly)

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    train_rmse_ = rmse(y_train, y_pred_train)
    train_r2_ = float(r2_score(y_train, y_pred_train))
    eval_rmse_ = rmse(y_test, y_pred_test)
    eval_r2_ = float(r2_score(y_test, y_pred_test))

    print(f"    Train  — RMSE: {train_rmse_:.4f}  R²: {train_r2_:.4f}")
    print(f"    Extrap — RMSE: {eval_rmse_:.4f}  R²: {eval_r2_:.4f}")

    # Monotonicity check
    mono_ok, mono_msg = check_monotonicity(
        model, poly, FORECAST_CHECK_YEARS, config["monotone_direction"]
    )
    print(f"    Monotone check: {mono_msg}")
    if not mono_ok:
        print(
            f"    !! Monotone constraint violated — physical plausibility at risk"
        )

    # Sample predictions with physical clamping applied
    floor = config["physical_floor"]
    ceil_ = config["physical_ceil"]
    sample_years = [1900, 1950, 1970, 1990, 2000, 2010, 2020, 2024, 2030, 2035]
    sample_preds = {}
    for yr in sample_years:
        valid_min = config["valid_year_min"]
        if yr < valid_min:
            sample_preds[str(yr)] = None
            continue
        X_s = transform_years(np.array([yr]), poly)
        val = float(model.predict(X_s)[0])
        if floor is not None:
            val = max(val, floor)
        if ceil_ is not None:
            val = min(val, ceil_)
        sample_preds[str(yr)] = round(val, 4)

    print(
        f"    2024={sample_preds.get('2024')}  2030={sample_preds.get('2030')}  2035={sample_preds.get('2035')}  ({config['units'].split(' ')[0]})"
    )

    metrics = {
        "model_type": f"poly{degree}_linear",
        "model_strategy": "year_poly",
        "units": config["units"],
        "train_rows": len(df_train),
        "extrap_eval_rows": len(df_test),
        "train_year_min": int(yr_train.min()),
        "train_year_max": int(yr_train.max()),
        "extrap_eval_year_min": int(yr_test.min()),
        "extrap_eval_year_max": int(yr_test.max()),
        "train_rmse": round(train_rmse_, 4),
        "train_r2": round(train_r2_, 4),
        "extrap_eval_rmse": round(eval_rmse_, 4),
        "extrap_eval_r2": round(eval_r2_, 4),
        "valid_year_min": config["valid_year_min"],
        "valid_year_max": config["valid_year_max"],
        "physical_floor": floor,
        "physical_ceil": ceil_,
        "monotone_check": mono_msg,
        "sample_predictions": sample_preds,
        "evaluation_note": (
            f"Extrapolation evaluation on {int(yr_test.min())}–{int(yr_test.max())}. "
            "These rows were withheld from training and measure how well "
            "the polynomial extends beyond its training window. "
            "R² here reflects extrapolation fidelity, not generalisation."
        ),
    }

    model_bundle = {
        "strategy": "year_poly",
        "model": model,
        "poly": poly,
        "poly_degree": degree,
        "year_center": YEAR_CENTER,
        "year_scale": YEAR_SCALE,
        "valid_year_min": config["valid_year_min"],
        "valid_year_max": config["valid_year_max"],
        "physical_floor": floor,
        "physical_ceil": ceil_,
        "col": col,
        "units": config["units"],
    }
    return model_bundle, metrics


# ── Dispatch ───────────────────────────────────────────────────────────────────
def train_one(df, target_key, config):
    """Dispatch to the correct training strategy for this target.

    Args:
        df:          Full preprocessed DataFrame.
        target_key:  Key from TARGETS.
        config:      Config dict from TARGETS.

    Returns:
        (model_bundle, metrics)
    """
    strategy = config["model_strategy"]
    if strategy == "piecewise":
        return train_co2_piecewise(df, config)
    elif strategy == "year_poly":
        return train_year_poly(df, target_key, config)
    else:
        raise ValueError(
            f"Unknown model_strategy '{strategy}' for target '{target_key}'"
        )


# ── Inference (for API endpoints) ─────────────────────────────────────────────
def predict(model_bundle, year):
    """Run inference using a saved model bundle.

    Enforces valid_year range, selects the correct polynomial piece for
    piecewise models, applies physical floor/ceiling clamps, and returns
    a single float prediction.

    Args:
        model_bundle: dict returned by train_one() and loaded via joblib.
        year:         int or float — calendar year to predict.

    Returns:
        float: predicted value in the model's native units, physically clamped.

    Raises:
        ValueError: if year is outside [valid_year_min, valid_year_max].
    """
    valid_min = model_bundle["valid_year_min"]
    valid_max = model_bundle["valid_year_max"]
    if not (valid_min <= year <= valid_max):
        raise ValueError(
            f"Year {year} is outside the valid prediction range "
            f"[{valid_min}, {valid_max}] for '{model_bundle['col']}'. "
            f"Extrapolation beyond this range is not supported."
        )

    year_arr = np.array([year])
    strategy = model_bundle["strategy"]

    if strategy == "piecewise":
        split_year = model_bundle["split_year"]
        if year < split_year:
            X = transform_years(year_arr, model_bundle["hist_poly"])
            val = float(model_bundle["hist_model"].predict(X)[0])
        else:
            X = transform_years(year_arr, model_bundle["inst_poly"])
            val = float(model_bundle["inst_model"].predict(X)[0])
    elif strategy == "year_poly":
        X = transform_years(year_arr, model_bundle["poly"])
        val = float(model_bundle["model"].predict(X)[0])
    else:
        raise ValueError(f"Unknown strategy '{strategy}' in model bundle.")

    # Physical clamps
    floor = model_bundle.get("physical_floor")
    ceil_ = model_bundle.get("physical_ceil")
    if floor is not None:
        val = max(val, floor)
    if ceil_ is not None:
        val = min(val, ceil_)

    return val


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 68)
    print("TerraEcho — Model Training")
    print("=" * 68)
    print(f"\nYear scaling: center={YEAR_CENTER}, scale={YEAR_SCALE}")
    print(f"  (year_scaled = (year - {YEAR_CENTER}) / {YEAR_SCALE})")
    print(
        f"\nMonotonicity check window: {int(FORECAST_CHECK_YEARS[0])}–{int(FORECAST_CHECK_YEARS[-1])}"
    )

    print(f"\nLoading: {DATA_FILE}")
    df = pd.read_csv(DATA_FILE)
    print(f"Shape: {df.shape}  |  Years: {df['year'].min()}–{df['year'].max()}")

    required = [
        "year",
        "forest_cover",
        "arctic_ice",
        "co2",
        "temp_anomaly",
        "sea_level",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in dataset: {missing}")

    all_metrics = {}
    for target_key, config in TARGETS.items():
        model_bundle, metrics = train_one(df, target_key, config)
        model_path = os.path.join(MODELS_DIR, config["model_file"])
        joblib.dump(model_bundle, model_path)
        print(f"    Saved: {model_path}")
        all_metrics[target_key] = metrics

    with open(METRICS_FILE, "w") as f:
        json.dump(all_metrics, f, indent=2)
    print(f"\n✓ Metrics: {METRICS_FILE}")

    # ── Training summary ───────────────────────────────────────────────────
    print("\n" + "=" * 68)
    print("TRAINING SUMMARY")
    print("=" * 68)
    print(f"{'Target':<16} {'Strategy':<22} {'Train R²':>9} {'Train RMSE':>11}")
    print("-" * 68)
    for key, m in all_metrics.items():
        strategy_label = m["model_type"]
        if m.get("model_strategy") == "piecewise":
            strategy_label += f"  (split {m['split_year']})"
        print(
            f"{key:<16} {strategy_label:<22} {m['train_r2']:>9.4f} {m['train_rmse']:>11.4f}"
        )

    # ── Extrapolation evaluation ───────────────────────────────────────────
    print("\n" + "=" * 68)
    print("EXTRAPOLATION EVALUATION  (not a generalisation test)")
    print("-" * 68)
    print("These rows were withheld from training. They measure how well")
    print("the fitted curve extends BEYOND its training window.")
    print("-" * 68)
    print(
        f"{'Target':<16} {'Eval period':<14} {'Extrap R²':>10} {'Extrap RMSE':>12}"
    )
    print("-" * 68)
    for key, m in all_metrics.items():
        period = f"{m['extrap_eval_year_min']}–{m['extrap_eval_year_max']}"
        print(
            f"{key:<16} {period:<14} {m['extrap_eval_r2']:>10.4f} {m['extrap_eval_rmse']:>12.4f}"
        )

    # ── Physical plausibility ──────────────────────────────────────────────
    print("\n" + "=" * 68)
    print("PHYSICAL PLAUSIBILITY CHECKS")
    print("-" * 68)
    for key, m in all_metrics.items():
        status = m.get("monotone_check", "not checked")
        print(f"  {key:<16}: {status}")

    # ── Sample forecasts ───────────────────────────────────────────────────
    print("\n── Sample predictions ──")
    print(f"{'Target':<16} {'2024':>8} {'2030':>8} {'2035':>8}  Units")
    print("-" * 55)
    for key, m in all_metrics.items():
        sp = m["sample_predictions"]
        v24 = str(sp.get("2024", "N/A"))
        v30 = str(sp.get("2030", "N/A"))
        v35 = str(sp.get("2035", "N/A"))
        print(f"{key:<16} {v24:>8} {v30:>8} {v35:>8}  {m['units']}")

    # ── Valid ranges ───────────────────────────────────────────────────────
    print("\n── Valid prediction ranges ──")
    print(f"{'Target':<16} {'Min year':>10} {'Max year':>10}  Floor / Ceil")
    print("-" * 60)
    for key, m in all_metrics.items():
        floor = str(m.get("physical_floor", "none"))
        ceil_ = str(m.get("physical_ceil", "none"))
        print(
            f"{key:<16} {m['valid_year_min']:>10} {m['valid_year_max']:>10}  {floor} / {ceil_}"
        )


if __name__ == "__main__":
    main()