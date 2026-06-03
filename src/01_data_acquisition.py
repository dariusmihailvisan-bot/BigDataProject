"""
Stage 1 — DATA ACQUISITION
--------------------------
Pulls historical HOURLY weather data from the free Open-Meteo Archive API
(https://open-meteo.com — no API key needed) for ~10 cities and ~3 years.

Why this API:
  - Free and public, no key required.
  - Returns clean JSON, hourly granularity.
  - Easy to hit a "big-ish" dataset (a few hundred thousand rows) so that
    using PySpark later is genuinely justified.

Output:
  data/raw/weather_raw.csv      <- one big CSV
  data/raw/weather_raw.parquet  <- same data in Parquet (smaller + faster)
"""

import os
import time
import requests
import pandas as pd

# -----------------------------------------------------------------------------
# Config — change here if you want more/fewer cities or a different time range.
# -----------------------------------------------------------------------------

# 10 cities spread across Europe + a couple outside, with their coordinates.
CITIES = {
    "Bucharest":   (44.4268, 26.1025),
    "Sibiu":       (45.7983, 24.1256),
    "Cluj-Napoca": (46.7712, 23.6236),
    "Berlin":      (52.5200, 13.4050),
    "Paris":       (48.8566,  2.3522),
    "Madrid":      (40.4168, -3.7038),
    "Rome":        (41.9028, 12.4964),
    "London":      (51.5072, -0.1276),
    "New York":    (40.7128, -74.0060),
    "Tokyo":       (35.6762, 139.6503),
}

# 3 full years of hourly data => ~26.000 rows per city => ~260.000 rows total.
START_DATE = "2022-01-01"
END_DATE   = "2024-12-31"

# Hourly variables we ask the API for.
HOURLY_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "precipitation",
    "rain",
    "snowfall",
    "surface_pressure",
    "cloud_cover",
    "wind_speed_10m",
    "wind_direction_10m",
]

API_URL = "https://archive-api.open-meteo.com/v1/archive"

# Paths relative to project root (we assume you run scripts from the repo root).
RAW_DIR = os.path.join("data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)


def fetch_city(city: str, lat: float, lon: float) -> pd.DataFrame:
    """Hit the API for one city and return a tidy DataFrame."""
    params = {
        "latitude":   lat,
        "longitude":  lon,
        "start_date": START_DATE,
        "end_date":   END_DATE,
        "hourly":     ",".join(HOURLY_VARS),
        "timezone":   "UTC",
    }
    # Simple retry loop in case the API hiccups.
    for attempt in range(3):
        try:
            r = requests.get(API_URL, params=params, timeout=60)
            r.raise_for_status()
            data = r.json()
            break
        except Exception as e:
            print(f"  ! {city} attempt {attempt+1} failed: {e}")
            time.sleep(3)
    else:
        raise RuntimeError(f"Failed to fetch {city} after 3 attempts")

    hourly = data["hourly"]
    df = pd.DataFrame(hourly)
    df["city"] = city
    df["latitude"]  = lat
    df["longitude"] = lon
    return df


def main():
    print(f"Pulling {len(CITIES)} cities, {START_DATE} -> {END_DATE} ...")
    all_frames = []
    for city, (lat, lon) in CITIES.items():
        print(f"  - {city}")
        df = fetch_city(city, lat, lon)
        all_frames.append(df)
        # Be polite to the free API.
        time.sleep(1)

    big = pd.concat(all_frames, ignore_index=True)
    print(f"Total rows pulled: {len(big):,}")

    csv_path     = os.path.join(RAW_DIR, "weather_raw.csv")
    parquet_path = os.path.join(RAW_DIR, "weather_raw.parquet")

    big.to_csv(csv_path, index=False)
    print(f"  saved {csv_path}")
    try:
        big.to_parquet(parquet_path, index=False)
        print(f"  saved {parquet_path}")
    except Exception as e:
        # Parquet needs pyarrow/fastparquet; not critical if missing.
        print(f"  (skipped parquet: {e})")


if __name__ == "__main__":
    main()
