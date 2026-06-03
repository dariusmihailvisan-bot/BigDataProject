"""
Stage 6 — DASHBOARD-READY EXPORT + Plotly backup
------------------------------------------------
Produces:
  dashboard/weather_dashboard.csv   <- tidy CSV for Tableau Public / Power BI
  dashboard/weather_dashboard.html  <- self-contained interactive dashboard
                                       (open in any browser)

Why a separate "dashboard CSV"?
  Tableau / Power BI love tidy, denormalized rows. We pre-aggregate to *daily*
  level so the BI tool stays snappy and so anyone can build the dashboard in
  about 10 minutes following the guide.
"""

import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

CLEAN_DIR = os.path.join("data", "clean")
DASH_DIR  = "dashboard"
os.makedirs(DASH_DIR, exist_ok=True)

CLEAN_CSV = os.path.join(CLEAN_DIR, "weather_clean.csv")
PREDS_CSV = os.path.join(CLEAN_DIR, "model_predictions.csv")

OUT_CSV  = os.path.join(DASH_DIR, "weather_dashboard.csv")
OUT_HTML = os.path.join(DASH_DIR, "weather_dashboard.html")


def main():
    print(f"Reading {CLEAN_CSV} ...")
    df = pd.read_csv(CLEAN_CSV, parse_dates=["time"])

    # Aggregate to daily — Tableau handles a few hundred thousand rows fine,
    # but daily is more than enough granularity for dashboard charts.
    daily = (df.groupby(["city", "year", "month", "day"], as_index=False)
               .agg(avg_temp=("temperature_2m", "mean"),
                    min_temp=("temperature_2m", "min"),
                    max_temp=("temperature_2m", "max"),
                    avg_humidity=("relative_humidity_2m", "mean"),
                    total_precip=("precipitation", "sum"),
                    avg_wind=("wind_speed_10m", "mean")))
    daily["date"] = pd.to_datetime(daily[["year", "month", "day"]])

    # Add latitude/longitude for map charts in Tableau/PBI.
    coords = (df.groupby("city", as_index=False)[["latitude", "longitude"]].first())
    daily = daily.merge(coords, on="city", how="left")

    # Optional: bring in model errors if the model script ran.
    if os.path.isfile(PREDS_CSV):
        preds = pd.read_csv(PREDS_CSV, parse_dates=["time"])
        # Strip timezone so it merges cleanly with our tz-naive daily["date"].
        preds["date"] = preds["time"].dt.tz_localize(None).dt.floor("D")
        err = (preds.groupby(["city", "date"], as_index=False)["abs_error"]
                    .mean()
                    .rename(columns={"abs_error": "model_mae"}))
        daily = daily.merge(err, on=["city", "date"], how="left")

    # Reorder + write tidy CSV.
    cols = ["date", "city", "latitude", "longitude",
            "avg_temp", "min_temp", "max_temp",
            "avg_humidity", "total_precip", "avg_wind"]
    if "model_mae" in daily.columns:
        cols.append("model_mae")
    daily = daily[cols].sort_values(["city", "date"])
    daily.to_csv(OUT_CSV, index=False)
    print(f"  saved {OUT_CSV}  ({len(daily):,} rows)")

    # ---- Plotly backup dashboard --------------------------------------------
    print("Building Plotly HTML dashboard ...")
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Daily average temperature per city",
            "Monthly seasonality",
            "City map (size = avg temp)",
            "Precipitation distribution",
        ),
        specs=[[{"type": "scatter"}, {"type": "scatter"}],
               [{"type": "scattergeo"}, {"type": "box"}]],
    )

    # 1) Temperature over time (line per city)
    for city, g in daily.groupby("city"):
        fig.add_trace(
            go.Scatter(x=g["date"], y=g["avg_temp"], mode="lines",
                       name=city, legendgroup=city),
            row=1, col=1,
        )

    # 2) Monthly seasonality
    monthly = (daily.assign(month=daily["date"].dt.month)
                    .groupby(["city", "month"], as_index=False)["avg_temp"].mean())
    for city, g in monthly.groupby("city"):
        fig.add_trace(
            go.Scatter(x=g["month"], y=g["avg_temp"], mode="lines+markers",
                       name=city, legendgroup=city, showlegend=False),
            row=1, col=2,
        )

    # 3) Map
    city_avg = (daily.groupby(["city", "latitude", "longitude"], as_index=False)["avg_temp"].mean())
    sizes = 8 + (city_avg["avg_temp"] - city_avg["avg_temp"].min()) * 2
    fig.add_trace(
        go.Scattergeo(
            lon=city_avg["longitude"], lat=city_avg["latitude"],
            text=city_avg["city"] + ": " + city_avg["avg_temp"].round(1).astype(str) + " C",
            marker=dict(size=sizes, color=city_avg["avg_temp"],
                        colorscale="RdYlBu_r", showscale=False,
                        line=dict(width=1, color="black")),
            showlegend=False,
        ),
        row=2, col=1,
    )

    # 4) Precipitation box plot per city
    for city, g in daily.groupby("city"):
        fig.add_trace(
            go.Box(y=g["total_precip"], name=city, legendgroup=city,
                   showlegend=False, boxpoints=False),
            row=2, col=2,
        )

    fig.update_layout(
        height=900,
        title_text="Historical Weather Trends - Interactive Dashboard",
        template="plotly_white",
    )
    fig.update_geos(showcountries=True, showcoastlines=True,
                    projection_type="natural earth")

    fig.write_html(OUT_HTML, include_plotlyjs="cdn")
    print(f"  saved {OUT_HTML}")


if __name__ == "__main__":
    main()
