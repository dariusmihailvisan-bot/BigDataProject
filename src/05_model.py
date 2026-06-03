"""
Stage 5 — PREDICTIVE MODEL
--------------------------
Predict next-hour temperature from the other features. We try two simple,
explainable models and pick by MAE/RMSE:

  1) Linear Regression  — fast, simple baseline, easy to explain.
  2) Random Forest      — non-linear, usually better, still interpretable
                          via feature importances.

We keep things student-level: train/test split is chronological (no leakage),
one model per call, metrics printed clearly.

Input : data/clean/spark_features.parquet   (from stage 4)
        Falls back to data/clean/weather_clean.csv if parquet missing.
Output: data/clean/model_predictions.csv    (for the dashboard)
"""

import os
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

CLEAN_DIR = os.path.join("data", "clean")
FEAT_PARQ = os.path.join(CLEAN_DIR, "spark_features.parquet")
FALLBACK  = os.path.join(CLEAN_DIR, "weather_clean.csv")
OUT_PREDS = os.path.join(CLEAN_DIR, "model_predictions.csv")


def load() -> pd.DataFrame:
    if os.path.isdir(FEAT_PARQ) or os.path.isfile(FEAT_PARQ):
        print(f"Reading {FEAT_PARQ} ...")
        return pd.read_parquet(FEAT_PARQ)
    print(f"Spark features not found, reading {FALLBACK}")
    df = pd.read_csv(FALLBACK, parse_dates=["time"])
    # Build the same lag features Spark did, so this script still runs alone.
    df = df.sort_values(["city", "time"])
    df["temp_lag_1h"]    = df.groupby("city")["temperature_2m"].shift(1)
    df["temp_lag_24h"]   = df.groupby("city")["temperature_2m"].shift(24)
    df["temp_roll_24h"]  = (df.groupby("city")["temperature_2m"]
                              .transform(lambda s: s.rolling(24, min_periods=1).mean()))
    df["precip_roll_24h"] = (df.groupby("city")["precipitation"]
                               .transform(lambda s: s.rolling(24, min_periods=1).sum()))
    return df.dropna(subset=["temp_lag_1h", "temp_lag_24h"])


def main():
    df = load()
    print(f"  shape: {df.shape}")

    # Target: temperature at the current hour.
    # Features: everything that doesn't leak the target.
    feature_cols = [
        "relative_humidity_2m", "dew_point_2m", "precipitation",
        "surface_pressure", "cloud_cover",
        "wind_speed_10m", "wind_direction_10m",
        "month", "hour", "day_of_year",
        "temp_lag_1h", "temp_lag_24h",
        "temp_roll_24h", "precip_roll_24h",
    ]
    feature_cols = [c for c in feature_cols if c in df.columns]
    # One-hot encode the city — small cardinality, easy to interpret.
    X = pd.get_dummies(df[feature_cols + ["city"]], columns=["city"], drop_first=True)
    y = df["temperature_2m"].astype(float)

    # Chronological split — train on older data, test on newer. No leakage.
    df_sorted = df.sort_values("time")
    cutoff = int(len(df_sorted) * 0.8)
    train_idx = df_sorted.index[:cutoff]
    test_idx  = df_sorted.index[cutoff:]

    X_train, X_test = X.loc[train_idx], X.loc[test_idx]
    y_train, y_test = y.loc[train_idx], y.loc[test_idx]
    print(f"  train: {len(X_train):,}   test: {len(X_test):,}")

    results = {}

    # 1) Linear regression baseline
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    pred_lr = lr.predict(X_test)
    results["LinearRegression"] = (pred_lr,
                                   mean_absolute_error(y_test, pred_lr),
                                   np.sqrt(mean_squared_error(y_test, pred_lr)))

    # 2) Random forest — fewer trees to keep it laptop-friendly.
    rf = RandomForestRegressor(n_estimators=60, max_depth=14,
                               n_jobs=-1, random_state=42)
    rf.fit(X_train, y_train)
    pred_rf = rf.predict(X_test)
    results["RandomForest"] = (pred_rf,
                               mean_absolute_error(y_test, pred_rf),
                               np.sqrt(mean_squared_error(y_test, pred_rf)))

    print("\nModel       MAE     RMSE")
    print("------------------------------")
    for name, (_, mae, rmse) in results.items():
        print(f"{name:14s} {mae:5.2f}   {rmse:5.2f}")

    # Pick the better one for the dashboard.
    best_name = min(results, key=lambda n: results[n][1])
    best_pred = results[best_name][0]
    print(f"\nBest model: {best_name}")

    # Random Forest gives feature importances we can show.
    if best_name == "RandomForest":
        imp = pd.Series(rf.feature_importances_, index=X.columns)
        print("\nTop features:")
        print(imp.sort_values(ascending=False).head(10).round(3))

    # Save predictions for the dashboard.
    out = df.loc[test_idx, ["time", "city", "temperature_2m"]].copy()
    out["prediction"] = best_pred
    out["model"] = best_name
    out["abs_error"] = (out["temperature_2m"] - out["prediction"]).abs()
    out.to_csv(OUT_PREDS, index=False)
    print(f"  saved {OUT_PREDS}")


if __name__ == "__main__":
    main()
