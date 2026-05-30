import os
import re
import numpy as np
import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────────

RAW_DIR       = os.path.join("ml", "data", "raw")
PROCESSED_DIR = os.path.join("ml", "data", "processed")
OUTPUT_FILE   = os.path.join(PROCESSED_DIR, "terraecho_dataset.csv")
LOG_FILE      = os.path.join(PROCESSED_DIR, "preprocessing_log.md")

os.makedirs(PROCESSED_DIR, exist_ok=True)

YEAR_START = 1900
YEAR_END   = 2024

# ── Logging ────────────────────────────────────────────────────────────────────

log_lines = []

def log(msg):
    print(msg)
    log_lines.append(str(msg))


# ══════════════════════════════════════════════════════════════════════════════
# 1. CO2
# ══════════════════════════════════════════════════════════════════════════════
#
# Two source files:
#
#   co2_historical_reconstruction.txt
#     Fixed-width layout, 4 paired (year, ppm) columns per row.
#     Contains a "Future Scenarios" block — excluded via stop-keyword guard.
#     Years 1850–2011 present; we use 1900–1958 from this source.
#     Data type: "reconstructed" (ice core + firn air, Etheridge et al. 1996)
#
#   co2_modern_mauna_loa.csv
#     NOAA GML annual mean. Comment lines start with #.
#     Columns: year, mean, unc.
#     Years 1959–2025 present; we use 1959–YEAR_END.
#     Data type: "observed" (direct atmospheric measurement)
#
#   Merge: historical 1900–1958 + modern 1959–YEAR_END.
#   Modern observations take strict priority — no overlap allowed.
#
# NOTE: The two sources have very different measurement uncertainties.
#   Ice core reconstruction: ±1–2 ppm.
#   Mauna Loa direct measurement: ±0.1 ppm.
#   We preserve the co2_type column in the merged dataset so downstream
#   models and the frontend can distinguish these if needed.
#   The training pipeline uses a data_source flag feature to account for
#   this difference rather than treating all rows identically.

DATA_ROW_PATTERN = re.compile(
    r'\b(1[89]\d{2}|20[012]\d)\s+(2[5-9]\d\.\d+|3\d{2}\.\d+|4[0-4]\d\.\d+)\b'
)

def load_co2():
    log("\n## CO2")

    # ── Historical reconstruction 1900–1958 ───────────────────────────────
    hist_path = os.path.join(RAW_DIR, "co2_historical_reconstruction.txt")
    log(f"  Loading: {hist_path}")

    hist_pairs = {}
    stop_keywords = ["future scenario", "alternative scenario", "2 degree", "references"]
    collecting = True

    with open(hist_path, "r", encoding="utf-8", errors="replace") as f:
        for raw_line in f:
            line_lower = raw_line.lower()

            if any(kw in line_lower for kw in stop_keywords):
                log(f"  Stopped at line: {raw_line.strip()[:60]}")
                collecting = False

            if not collecting:
                continue

            matches = DATA_ROW_PATTERN.findall(raw_line)
            for year_str, ppm_str in matches:
                year = int(year_str)
                ppm  = float(ppm_str)
                if YEAR_START <= year <= 1958:
                    hist_pairs[year] = ppm

    if not hist_pairs:
        raise ValueError(
            "No CO2 historical pairs extracted. "
            "Check file format or regex pattern."
        )

    df_hist = pd.DataFrame(
        sorted(hist_pairs.items()), columns=["year", "co2"]
    )
    df_hist["co2_type"] = "reconstructed"
    log(f"  Historical: {len(df_hist)} rows ({df_hist['year'].min()}–{df_hist['year'].max()})")
    log(f"  Uncertainty: ±1–2 ppm (ice core / firn air reconstruction)")

    # ── Modern Mauna Loa 1959–YEAR_END ────────────────────────────────────
    modern_path = os.path.join(RAW_DIR, "co2_modern_mauna_loa.csv")
    log(f"  Loading: {modern_path}")

    df_modern = pd.read_csv(
        modern_path,
        comment="#",
        header=None,
        names=["year", "co2", "unc"],
        skipinitialspace=True,
    )
    df_modern = df_modern[pd.to_numeric(df_modern["year"], errors="coerce").notna()].copy()
    df_modern["year"] = df_modern["year"].astype(int)
    df_modern["co2"]  = pd.to_numeric(df_modern["co2"], errors="coerce")
    df_modern = df_modern[df_modern["co2"] > 0].copy()
    # Strict range: only take 1959–YEAR_END, so 2025+ rows are excluded
    df_modern = df_modern[
        (df_modern["year"] >= 1959) & (df_modern["year"] <= YEAR_END)
    ].copy()
    df_modern["co2_type"] = "observed"
    log(f"  Modern: {len(df_modern)} rows ({df_modern['year'].min()}–{df_modern['year'].max()})")
    log(f"  Uncertainty: ±0.1 ppm (NOAA GML direct measurement)")

    # ── Merge: historical then modern, no overlap ──────────────────────────
    # Modern rows are filtered to >= 1959 above, historical to <= 1958,
    # so the concat is clean — no year appears in both sources.
    df_co2 = pd.concat(
        [df_hist[["year", "co2", "co2_type"]],
         df_modern[["year", "co2", "co2_type"]]],
        ignore_index=True
    ).sort_values("year").reset_index(drop=True)

    # Verify no duplicate years (would indicate a source boundary problem)
    dupes = df_co2[df_co2.duplicated("year")]
    if not dupes.empty:
        raise ValueError(f"Duplicate CO2 years after merge: {dupes['year'].tolist()}")

    log(f"  Final: {len(df_co2)} rows ({df_co2['year'].min()}–{df_co2['year'].max()})")
    log(f"  Source boundary: reconstructed ≤ 1958, observed ≥ 1959")
    return df_co2


# ══════════════════════════════════════════════════════════════════════════════
# 2. TEMPERATURE ANOMALY
# ══════════════════════════════════════════════════════════════════════════════
#
# File: temperature_anomaly_global.csv
# Source: NASA GISTEMP v4
#
#   Row 0: title "Land-Ocean: Global Means" — skip with skiprows=1
#   Columns: Year, Jan..Dec, J-D (annual mean), D-N, DJF, MAM, JJA, SON
#   Values in °C — confirmed: 1880 = -0.18, 2024 ≈ 1.29
#   No divide-by-100 needed (newer GISTEMP format)
#   "***" marks missing seasonal values — treated as NaN
#   Baseline: GISTEMP 1951–1980
#
#   We use J-D (annual mean) only.
#   2025 and 2026 rows exist in the file:
#     2025: complete annual mean available
#     2026: partial year only (J-D = "***")
#   We include 2025 if it falls within YEAR_END, otherwise exclude cleanly.
#   Rows with NaN in J-D are dropped rather than imputed.
#
#   data_type: "observed" (GISTEMP direct measurement + analysis)

def load_temperature():
    log("\n## Temperature Anomaly")

    path = os.path.join(RAW_DIR, "temperature_anomaly_global.csv")
    log(f"  Loading: {path}")

    df = pd.read_csv(
        path,
        skiprows=1,
        na_values=["***", ""],
    )

    df = df.rename(columns={"Year": "year", "J-D": "temp_anomaly"})
    df["year"]         = pd.to_numeric(df["year"], errors="coerce")
    df["temp_anomaly"] = pd.to_numeric(df["temp_anomaly"], errors="coerce")

    # Drop rows where either year or the annual mean is missing
    # (this handles the partial 2026 row cleanly without special-casing)
    df = df[df["year"].notna() & df["temp_anomaly"].notna()].copy()
    df["year"] = df["year"].astype(int)

    df = df[(df["year"] >= YEAR_START) & (df["year"] <= YEAR_END)].copy()
    df["temp_type"] = "observed"

    log(f"  Rows: {len(df)} ({df['year'].min()}–{df['year'].max()})")
    log(f"  Baseline: GISTEMP 1951–1980 (values in °C, not divided by 100)")
    log(f"  Range: {df['temp_anomaly'].min():.3f}°C – {df['temp_anomaly'].max():.3f}°C")
    log(f"  Partial-year rows (e.g. 2026 with incomplete months) excluded via NaN drop")

    return df[["year", "temp_anomaly", "temp_type"]]


# ══════════════════════════════════════════════════════════════════════════════
# 3. ARCTIC SEA ICE
# ══════════════════════════════════════════════════════════════════════════════
#
# Two source files:
#
#   arctic_ice_satellite_1979_present.csv (NSIDC)
#     Columns: year, mo, source_dataset, region, extent, area
#     Already September-only (mo=9), Northern Hemisphere (region=N)
#     extent in million km² — use directly
#     Covers 1980–2025 (1979 is absent from this file)
#     Source identifiers: NSIDC-0051 (main), NSIDC-0803 (2025 only)
#     data_type: "observed"
#
#   arctic_ice_reconstruction_1850_1978.csv (Walsh et al. G10010)
#     IMPORTANT: Despite the filename implying coverage to 1978,
#     this file actually extends to 2017. The filename is misleading.
#     Row 0: dataset title
#     Row 1: column headers (YYYYDDD, Northern_Hemisphere, ...)
#     Row 2: RegnArea metadata row
#     Row 3+: data rows
#     YYYYDDD format: first 4 chars = year, last 3 = day-of-year
#     Northern_Hemisphere values in km² → divide by 1,000,000
#     September = DOY 244–273
#     Per year: take September minimum (consistent with NSIDC methodology)
#     data_type: "reconstructed"
#
#   Merge strategy:
#     - Satellite (observed) is preferred wherever it exists (1980–2025)
#     - Walsh reconstruction fills:
#         (a) pre-satellite years 1900–1979, and
#         (b) the single year 1979 that is absent from the satellite file
#     - In the overlap zone (1980–2017) satellite always wins — Walsh
#       reconstruction values for those years are discarded
#     - This is a deliberate, documented choice: satellite data has
#       directly-measured uncertainty; reconstruction uncertainty is higher
#       and the two sources show non-trivial differences in absolute values
#       for overlapping years (e.g. Walsh 1980: ~8.28 vs satellite 1980: 7.67)
#
#   WHY NOT BLEND THE OVERLAP?
#     Blending reconstruction and satellite in the training window would
#     introduce a systematic offset (reconstruction tends to read higher).
#     Since we label each row with ice_type, the training pipeline can
#     add a binary "is_reconstructed" feature to partially account for this.

def load_arctic_ice():
    log("\n## Arctic Sea Ice")

    # ── Satellite data (primary, 1980–YEAR_END) ───────────────────────────
    sat_path = os.path.join(RAW_DIR, "arctic_ice_satellite_1979_present.csv")
    log(f"  Loading satellite: {sat_path}")

    df_sat = pd.read_csv(
        sat_path,
        skiprows=2,
        header=None,
        names=["year", "mo", "source_dataset", "region", "extent", "area"],
    )
    df_sat["year"]   = pd.to_numeric(df_sat["year"].astype(str).str.strip(), errors="coerce")
    df_sat["extent"] = pd.to_numeric(df_sat["extent"], errors="coerce")
    df_sat = df_sat[df_sat["year"].notna() & df_sat["extent"].notna()].copy()
    df_sat = df_sat[df_sat["extent"] > 0].copy()
    df_sat["year"] = df_sat["year"].astype(int)
    # Hard cap at YEAR_END so future rows (e.g. 2025) don't leak in
    df_sat = df_sat[(df_sat["year"] >= 1979) & (df_sat["year"] <= YEAR_END)].copy()
    df_sat = df_sat[["year", "extent"]].rename(columns={"extent": "arctic_ice"})
    df_sat["ice_type"] = "observed"

    log(f"  Satellite: {len(df_sat)} rows ({df_sat['year'].min()}–{df_sat['year'].max()})")
    if 1979 not in df_sat["year"].values:
        log(f"  NOTE: 1979 absent from satellite file — will be filled from reconstruction")

    # ── Walsh reconstruction (secondary, used for pre-satellite years) ────
    walsh_path = os.path.join(RAW_DIR, "arctic_ice_reconstruction_1850_1978.csv")
    log(f"  Loading reconstruction: {walsh_path}")

    df_raw = pd.read_csv(walsh_path, header=None)

    # Row 1 = column headers, Row 2 = RegnArea metadata, Row 3+ = data
    headers = df_raw.iloc[1].tolist()
    df_data = df_raw.iloc[3:].copy()
    df_data.columns = headers
    df_data = df_data.reset_index(drop=True)

    # Parse YYYYDDD
    df_data["yyyyddd_str"] = df_data["YYYYDDD"].astype(str).str.strip()
    df_data["year_raw"] = pd.to_numeric(
        df_data["yyyyddd_str"].str[:4], errors="coerce"
    )
    df_data["doy"] = pd.to_numeric(
        df_data["yyyyddd_str"].str[4:], errors="coerce"
    )
    df_data = df_data[df_data["year_raw"].notna() & df_data["doy"].notna()].copy()
    df_data["year_raw"] = df_data["year_raw"].astype(int)
    df_data["doy"]      = df_data["doy"].astype(int)

    # September = DOY 244–273
    df_sept = df_data[
        (df_data["doy"] >= 244) & (df_data["doy"] <= 273)
    ].copy()

    df_sept = df_sept.copy()
    df_sept["arctic_ice"] = (
        pd.to_numeric(df_sept["Northern_Hemisphere"], errors="coerce") / 1_000_000
    )
    df_sept = df_sept[df_sept["arctic_ice"].notna() & (df_sept["arctic_ice"] > 0)].copy()

    # Per year: September minimum (consistent with NSIDC methodology)
    df_walsh_full = (
        df_sept.groupby("year_raw")["arctic_ice"]
        .min()
        .reset_index()
        .rename(columns={"year_raw": "year"})
    )

    # Keep only years NOT covered by satellite: 1900–1979
    # This includes the 1979 gap in the satellite file.
    # Satellite data takes priority for all years where it exists.
    sat_years = set(df_sat["year"].tolist())
    df_walsh = df_walsh_full[
        (df_walsh_full["year"] >= YEAR_START) &
        (df_walsh_full["year"] <= YEAR_END) &
        (~df_walsh_full["year"].isin(sat_years))
    ].copy()
    df_walsh["ice_type"] = "reconstructed"

    log(f"  Walsh (reconstruction, used for years not in satellite): "
        f"{len(df_walsh)} rows ({df_walsh['year'].min()}–{df_walsh['year'].max()})")
    log(f"  Walsh file actual year range: "
        f"{int(df_walsh_full['year'].min())}–{int(df_walsh_full['year'].max())} "
        f"(filename 'reconstruction_1850_1978' is misleading — file extends further)")
    log(f"  Overlap resolution: satellite wins for all years present in both sources")

    # ── Merge: Walsh (pre-satellite) + satellite (1980+) ──────────────────
    df_ice = pd.concat(
        [df_walsh[["year", "arctic_ice", "ice_type"]],
         df_sat[["year",   "arctic_ice", "ice_type"]]],
        ignore_index=True
    ).sort_values("year").reset_index(drop=True)

    # Verify no duplicate years (satellite priority logic above should prevent this)
    dupes = df_ice[df_ice.duplicated("year")]
    if not dupes.empty:
        raise ValueError(f"Duplicate arctic ice years after merge: {dupes['year'].tolist()}")

    log(f"  Final: {len(df_ice)} rows ({df_ice['year'].min()}–{df_ice['year'].max()})")
    log(f"  Reconstructed rows: {(df_ice['ice_type']=='reconstructed').sum()}, "
        f"Observed rows: {(df_ice['ice_type']=='observed').sum()}")
    return df_ice


# ══════════════════════════════════════════════════════════════════════════════
# 4. SEA LEVEL
# ══════════════════════════════════════════════════════════════════════════════
#
# File: sea_level_global.csv
# Source: EPA (CSIRO + NOAA combined)
#
#   Columns: Year, CSIRO Adjusted Sea Level, Lower Error Bound,
#            Upper Error Bound, NOAA Adjusted Sea Level
#   CSIRO: 1880–2013 (tide-gauge reconstruction, EOF-based)
#   NOAA:  2010–2023 (satellite altimetry)
#   UNITS: inches (EPA source documentation) → convert × 25.4 to mm
#
#   Stitch strategy:
#     - Use CSIRO for 1880–2013
#     - Use NOAA for 2014–2023 (CSIRO ends at 2013)
#     - In the 2010–2013 overlap CSIRO takes priority (consistent series)
#
#   Rebaseline: subtract 1900 value so sea_level = 0 mm at 1900
#
#   IMPORTANT — no forward-fill for 2024:
#     The original code forward-filled the missing 2024 value with the 2023
#     NOAA reading. This creates a fabricated training point. We do NOT do
#     this. The sea level series ends at 2023 naturally. The 2024 NaN is left
#     as NaN in the merged dataset and excluded from sea level model training.
#
#   data_type:
#     CSIRO rows: "reconstructed" (sparse tide-gauge EOF reconstruction)
#     NOAA-only rows (2014+): "observed" (satellite altimetry)

INCHES_TO_MM = 25.4

def load_sea_level():
    log("\n## Sea Level")

    path = os.path.join(RAW_DIR, "sea_level_global.csv")
    log(f"  Loading: {path}")

    df = pd.read_csv(path)
    df = df.rename(columns={
        "Year":                     "year",
        "CSIRO Adjusted Sea Level": "csiro_in",
        "NOAA Adjusted Sea Level":  "noaa_in",
    })
    df["year"] = df["year"].astype(int)

    # Convert to mm
    df["csiro_mm"] = pd.to_numeric(df["csiro_in"], errors="coerce") * INCHES_TO_MM
    df["noaa_mm"]  = pd.to_numeric(df["noaa_in"],  errors="coerce") * INCHES_TO_MM

    # Stitch: CSIRO first, NOAA fills where CSIRO is absent
    df["sea_level_raw"] = df["csiro_mm"].combine_first(df["noaa_mm"])

    # Assign type per row
    df["sl_type"] = df.apply(
        lambda row: (
            "observed"
            if pd.isna(row["csiro_in"]) and pd.notna(row["noaa_in"])
            else "reconstructed"
        ),
        axis=1,
    )

    # Filter to our year range; keep only rows with actual data
    df = df[(df["year"] >= YEAR_START) & (df["year"] <= YEAR_END)].copy()
    df = df[df["sea_level_raw"].notna()].copy()

    # Rebaseline to 1900 = 0 mm
    rows_1900 = df[df["year"] == 1900]
    if rows_1900.empty:
        baseline = df["sea_level_raw"].iloc[0]
        log(f"  WARNING: no 1900 row found — using first available year as baseline")
    else:
        baseline = rows_1900["sea_level_raw"].iloc[0]

    df["sea_level"] = (df["sea_level_raw"] - baseline).round(1)

    log(f"  Unit conversion: × {INCHES_TO_MM} → mm")
    log(f"  Baseline (1900 value pre-rebase): {baseline:.2f} mm")
    log(f"  Rows: {len(df)} ({df['year'].min()}–{df['year'].max()})")
    log(f"  Range: {df['sea_level'].min():.1f} – {df['sea_level'].max():.1f} mm")
    log(f"  NOTE: 2024 sea level is absent (no source data). "
        f"No forward-fill applied. 2024 will be NaN in the merged dataset "
        f"and excluded from model training automatically.")
    log(f"  Reconstructed rows: {(df['sl_type']=='reconstructed').sum()}, "
        f"Observed rows: {(df['sl_type']=='observed').sum()}")

    return df[["year", "sea_level", "sl_type"]]


# ══════════════════════════════════════════════════════════════════════════════
# 5. FOREST COVER
# ══════════════════════════════════════════════════════════════════════════════
#
# File: forest_cover_global.csv
# Source: Our World in Data (FAO FRA)
#
#   Columns: Entity, Code, Year,
#            'Share of land covered by forest',
#            'Share of land covered by forest (Annotations)'
#   Coverage: 1990–2025 (FAO FRA data)
#   data_type: "observed" for 1990+
#
# Strategy:
#   1. Filter to Entity == "World"
#   2. If "World" does not exist, aggregate all countries by mean per year
#      and log clearly as a data limitation
#   3. Pre-1990: leave as NaN — do NOT fabricate values
#      Forest cover before 1990 has no reliable global series.
#      The polynomial model MUST NOT be asked to predict values before 1990.
#      Invalid-range protection is enforced in train.py, not here.
#   4. data_type: "observed" for all FAO FRA rows

def load_forest_cover():
    log("\n## Forest Cover")

    path = os.path.join(RAW_DIR, "forest_cover_global.csv")
    log(f"  Loading: {path}")

    df_raw = pd.read_csv(path)

    # Identify the forest cover value column
    forest_col = None
    for col in df_raw.columns:
        if "forest" in col.lower() and "share" in col.lower() and "annotation" not in col.lower():
            forest_col = col
            break
    if forest_col is None:
        raise ValueError(
            f"Cannot find forest cover column. Columns: {df_raw.columns.tolist()}"
        )
    log(f"  Value column: '{forest_col}'")

    # Try World entity first
    df_world = df_raw[df_raw["Entity"] == "World"].copy()

    if len(df_world) == 0:
        log("  WARNING: 'World' entity not found. Aggregating all countries by year mean.")
        log("  This is a fallback — results will be less accurate than a true global figure.")
        df_world = (
            df_raw.groupby("Year")[forest_col]
            .mean()
            .reset_index()
        )
        df_world["Entity"] = "aggregated_mean"
    else:
        log(f"  'World' entity found: {len(df_world)} rows")

    df_forest = df_world[["Year", forest_col]].rename(
        columns={"Year": "year", forest_col: "forest_cover"}
    ).copy()
    df_forest["year"] = df_forest["year"].astype(int)
    df_forest["forest_cover"] = pd.to_numeric(df_forest["forest_cover"], errors="coerce")
    df_forest = df_forest[df_forest["forest_cover"].notna()].copy()
    df_forest = df_forest[
        (df_forest["year"] >= YEAR_START) & (df_forest["year"] <= YEAR_END)
    ].copy()
    df_forest["forest_type"] = "observed"
    df_forest = df_forest.sort_values("year").reset_index(drop=True)

    log(f"  Rows after filter: {len(df_forest)} "
        f"({df_forest['year'].min()}–{df_forest['year'].max()})")
    log(f"  NOTE: Pre-1990 forest cover is absent — not fabricated.")
    log(f"  The merged dataset will have NaN for forest_cover before 1990.")
    log(f"  train.py enforces a minimum valid prediction year of 1990 for this target.")

    return df_forest[["year", "forest_cover", "forest_type"]]


# ══════════════════════════════════════════════════════════════════════════════
# 6. MERGE
# ══════════════════════════════════════════════════════════════════════════════
#
# Outer join all five datasets on a full year spine (YEAR_START–YEAR_END).
# Assign unified data_type column.
# Interpolate ONLY interior gaps for metrics with dense coverage.
# Forest cover pre-1990 gap is intentionally left as NaN.
# Log all imputation decisions explicitly.
#
# IMPORTANT: The is_reconstructed column is preserved in the output.
# This binary flag (1 = at least one source is reconstructed, 0 = all observed)
# is passed to train.py as a feature for models that span both source eras.
# Using it as a feature partially accounts for the different measurement
# characteristics of reconstruction vs direct observation without discarding
# the reconstruction-era data.

def merge_all(df_co2, df_temp, df_ice, df_sea, df_forest):
    log("\n## Merging")

    # Full year spine
    df = pd.DataFrame({"year": range(YEAR_START, YEAR_END + 1)})

    df = df.merge(df_co2[["year", "co2", "co2_type"]],            on="year", how="left")
    df = df.merge(df_temp[["year", "temp_anomaly", "temp_type"]], on="year", how="left")
    df = df.merge(df_ice[["year", "arctic_ice", "ice_type"]],     on="year", how="left")
    df = df.merge(df_sea[["year", "sea_level", "sl_type"]],       on="year", how="left")
    df = df.merge(df_forest[["year", "forest_cover", "forest_type"]], on="year", how="left")

    # Report NaN counts before interpolation
    log("  NaN counts before interpolation:")
    for col in ["co2", "temp_anomaly", "arctic_ice", "sea_level", "forest_cover"]:
        n = df[col].isna().sum()
        if n > 0:
            years = df[df[col].isna()]["year"].tolist()
            log(f"    {col}: {n} missing — years {years[:5]}{'...' if len(years) > 5 else ''}")

    # Interpolate interior gaps only for metrics with dense coverage.
    # "Interior" = gap is surrounded by known values on both sides.
    # This handles isolated missing years (e.g. instrument outages).
    # Forest cover pre-1990 is a leading gap — not interior — so it is
    # correctly left as NaN by limit_area="inside".
    # Sea level 2024 NaN is a trailing edge gap — also left as NaN.
    interp_cols = ["co2", "temp_anomaly", "arctic_ice", "sea_level"]
    for col in interp_cols:
        before = df[col].isna().sum()
        df[col] = df[col].interpolate(method="linear", limit_area="inside")
        after = df[col].isna().sum()
        if before != after:
            log(f"  Interpolated {before - after} interior gap(s) in '{col}'")

    # ── Unified data_type ──────────────────────────────────────────────────
    # A year is "observed" only if all available sources for that year are
    # directly measured. Any reconstructed source → "reconstructed".
    type_cols = ["co2_type", "temp_type", "ice_type", "sl_type", "forest_type"]

    def assign_type(row):
        types = [row[c] for c in type_cols if pd.notna(row[c])]
        if not types:
            return "unknown"
        if "reconstructed" in types:
            return "reconstructed"
        return "observed"

    df["data_type"] = df.apply(assign_type, axis=1)

    # ── is_reconstructed binary feature ───────────────────────────────────
    # 1 if data_type == "reconstructed" else 0.
    # Passed to train.py as a feature for models that span both source eras
    # (co2, arctic_ice). Helps the model partially distinguish measurement
    # regime without discarding early data.
    df["is_reconstructed"] = (df["data_type"] == "reconstructed").astype(int)

    # Drop individual type columns — they served their purpose
    df = df.drop(columns=type_cols)

    log(f"\n  Final shape: {df.shape}")
    log(f"  data_type distribution:\n{df['data_type'].value_counts().to_string()}")
    log(f"\n  NaN counts after interpolation:")
    for col in ["co2", "temp_anomaly", "arctic_ice", "sea_level", "forest_cover"]:
        n = df[col].isna().sum()
        log(f"    {col}: {n}")

    return df


# ══════════════════════════════════════════════════════════════════════════════
# 7. MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    log("# TerraEcho Preprocessing Log")
    log(f"Year range: {YEAR_START}–{YEAR_END}")
    log(f"Output: {OUTPUT_FILE}\n")

    df_co2    = load_co2()
    df_temp   = load_temperature()
    df_ice    = load_arctic_ice()
    df_sea    = load_sea_level()
    df_forest = load_forest_cover()

    df = merge_all(df_co2, df_temp, df_ice, df_sea, df_forest)

    # Round to sensible precision
    df["co2"]          = df["co2"].round(2)
    df["temp_anomaly"] = df["temp_anomaly"].round(3)
    df["arctic_ice"]   = df["arctic_ice"].round(3)
    df["sea_level"]    = df["sea_level"].round(1)
    df["forest_cover"] = df["forest_cover"].round(3)

    # Final column order — Phase 5B/5C contract preserved, is_reconstructed appended
    cols = [
        "year", "forest_cover", "arctic_ice", "co2",
        "temp_anomaly", "sea_level", "data_type", "is_reconstructed",
    ]
    df = df[cols]

    df.to_csv(OUTPUT_FILE, index=False)
    log(f"\n✓ Written: {OUTPUT_FILE}")

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    log(f"✓ Log: {LOG_FILE}")

    # Preview
    print("\n── Sample: milestone years ──")
    sample_years = [1900, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020, 2024]
    print(df[df["year"].isin(sample_years)].to_string(index=False))

    print("\n── Head ──")
    print(df.head(3).to_string(index=False))

    print("\n── Tail ──")
    print(df.tail(3).to_string(index=False))


if __name__ == "__main__":
    main()