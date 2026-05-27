# ml/data/inspect_datasets.py

from pathlib import Path
import pandas as pd

RAW_DIR = Path("ml/data/raw")

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 80)


def divider(name):
    print("\n")
    print("=" * 100)
    print(name)
    print("=" * 100)


# =========================================================
# ARCTIC SATELLITE
# =========================================================

def inspect_arctic_satellite():

    divider("ARCTIC SATELLITE")

    try:

        df = pd.read_csv(
            RAW_DIR / "arctic_ice_satellite_1979_present.csv"
        )

        df.columns = df.columns.str.strip()

        print("\nColumns:")
        print(df.columns.tolist())

        print("\nShape:")
        print(df.shape)

        print("\nDtypes:")
        print(df.dtypes)

        print("\nMissing:")
        print(df.isnull().sum())

        print("\nHead:")
        print(df.head())

        print("\nTail:")
        print(df.tail())

    except Exception as e:

        print(e)


# =========================================================
# ARCTIC RECONSTRUCTION
# =========================================================

def inspect_arctic_reconstruction():

    divider("ARCTIC RECONSTRUCTION")

    try:

        df = pd.read_csv(
            RAW_DIR / "arctic_ice_reconstruction_1850_1978.csv",
            header=None
        )

        print("\nFirst 25 rows:")
        print(df.head(25))

        print("\nPotential header row:")
        print(df.iloc[1])

        print("\nPotential metadata row:")
        print(df.iloc[2])

    except Exception as e:

        print(e)


# =========================================================
# SEA LEVEL
# =========================================================

def inspect_sea_level():

    divider("SEA LEVEL")

    try:

        df = pd.read_csv(
            RAW_DIR / "sea_level_global.csv"
        )

        print("\nColumns:")
        print(df.columns.tolist())

        print("\nShape:")
        print(df.shape)

        print("\nDtypes:")
        print(df.dtypes)

        print("\nMissing:")
        print(df.isnull().sum())

        print("\nHead:")
        print(df.head())

        print("\nTail:")
        print(df.tail())

    except Exception as e:

        print(e)


# =========================================================
# TEMPERATURE
# =========================================================

def inspect_temperature():

    divider("TEMPERATURE")

    try:

        print("\nRAW FILE PREVIEW:\n")

        with open(
            RAW_DIR / "temperature_anomaly_global.csv",
            encoding="utf8"
        ) as f:

            for i in range(20):

                line = f.readline()

                print(f"{i}: {line.rstrip()}")

        print("\nTrying skiprows=1...\n")

        df = pd.read_csv(
            RAW_DIR / "temperature_anomaly_global.csv",
            skiprows=1
        )

        print("\nColumns:")
        print(df.columns.tolist())

        print("\nShape:")
        print(df.shape)

        print("\nHead:")
        print(df.head())

    except Exception as e:

        print(e)


# =========================================================
# CO2 MODERN
# =========================================================

def inspect_co2_modern():

    divider("CO2 MODERN")

    try:

        path = RAW_DIR / "co2_modern_mauna_loa.csv"

        print("\nRaw preview:\n")

        with open(
            path,
            encoding="utf8"
        ) as f:

            for i in range(30):

                print(
                    f"{i}: {f.readline().rstrip()}"
                )

        print(
            "\nLook for where actual data starts."
        )

    except Exception as e:

        print(e)


# =========================================================
# FOREST
# =========================================================

def inspect_forest():

    divider("FOREST")

    try:

        df = pd.read_csv(
            RAW_DIR / "forest_cover_global.csv"
        )

        print("\nColumns:")
        print(df.columns.tolist())

        print("\nShape:")
        print(df.shape)

        print("\nDtypes:")
        print(df.dtypes)

        print("\nEntities sample:")
        print(
            df["Entity"]
            .unique()[:20]
        )

        print("\nHead:")
        print(df.head())

        print("\nTail:")
        print(df.tail())

    except Exception as e:

        print(e)


# =========================================================
# CO2 HISTORICAL TXT
# =========================================================

def inspect_co2_txt():

    divider(
        "CO2 HISTORICAL RECONSTRUCTION"
    )

    try:

        with open(
            RAW_DIR /
            "co2_historical_reconstruction.txt",
            encoding="utf8"
        ) as f:

            text = f.read()

        print("\nLength:")
        print(len(text))

        print("\nFirst 8000 chars:\n")

        print(
            text[:8000]
        )

    except Exception as e:

        print(e)


# =========================================================

print("\nSTARTING INSPECTION")


inspect_arctic_satellite()

inspect_arctic_reconstruction()

inspect_sea_level()

inspect_temperature()

inspect_co2_modern()

inspect_forest()

inspect_co2_txt()


print("\nDONE")