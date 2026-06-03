"""
Stage 2 — PREPROCESSING & CLEANING (Pandas)
-------------------------------------------
Reads the raw CSV from data/raw/, cleans it, and writes the cleaned
result to data/clean/.

Cleaning steps (explained inline so you can present them):
  1. Parse the "time" column as a proper datetime.
  2. Drop full duplicates (just in case the API returned overlap).
  3. Drop rows that have a missing temperature — temperature is our target
     for the model and a missing target is useless.
  4. Fill the remaining numeric NaNs with the per-city median. Median is
     robust to outliers (e.g. one freak storm reading won't shift it).
  5. Coerce types: numeric columns -> float32 to save memory; "city" -> category.
  6. Add convenience time columns (year, month, day, hour, day_of_year).
"""

import os
import pandas as pd

RAW_PATH   = os.path.join("data", "raw",   "weather_raw.csv")
CLEAN_DIR  = os.path.join("data", "clean")
CLEAN_CSV  = os.path.join(CLEAN_DIR, "weather_clean.csv")
CLEAN_PARQ = os.path.join(CLEAN_DIR, "weather_clean.parquet")

NUMERIC_COLS = [
    "temperature_2m", "relative_humidity_2m", "dew_point_2m",
    "precipitation", "rain", "snowfall",
    "surface_pressure", "cloud_cover",
    "wind_speed_10m", "wind_direction_10m",
]


def main():
    os.makedirs(CLEAN_DIR, exist_ok=True)
    print(f"Reading {RAW_PATH} ...")
    df = pd.read_csv(RAW_PATH)
    print(f"  raw shape: {df.shape}")

    # 1) Proper datetime parsing — string timestamps are useless for time math.
    df["time"] = pd.to_datetime(df["time"], utc=True)

    # 2) Exact duplicates can sneak in if the API is called twice.
    before = len(df)
    df = df.drop_duplicates()
    print(f"  dropped {before - len(df)} duplicate rows")

    # 3) Missing target = unusable row for our prediction problem.
    before = len(df)
    df = df.dropna(subset=["temperature_2m"])
    print(f"  dropped {before - len(df)} rows missing temperature")

    # 4) Fill remaining numeric NaNs with the per-city median.
    #    Per-city because Paris in January and Tokyo in January are very different.
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = df.groupby("city")[col].transform(
                lambda s: s.fillna(s.median())
            )

    # 5) Tighten types — float32 halves memory vs default float64.
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("float32")
    df["city"] = df["city"].astype("category")

    # 6) Time features that EDA / the model / the dashboard will all want.
    df["year"]        = df["time"].dt.year.astype("int16")
    df["month"]       = df["time"].dt.month.astype("int8")
    df["day"]         = df["time"].dt.day.astype("int8")
    df["hour"]        = df["time"].dt.hour.astype("int8")
    df["day_of_year"] = df["time"].dt.dayofyear.astype("int16")

    print(f"  clean shape: {df.shape}")
    print(df.dtypes)

    df.to_csv(CLEAN_CSV, index=False)
    print(f"  saved {CLEAN_CSV}")
    try:
        df.to_parquet(CLEAN_PARQ, index=False)
        print(f"  saved {CLEAN_PARQ}")
    except Exception as e:
        print(f"  (skipped parquet: {e})")


if __name__ == "__main__":
    main()
