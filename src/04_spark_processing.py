"""
Stage 4 — BIG DATA PROCESSING with PySpark
------------------------------------------
Why Spark here?
  Even though our dataset fits in RAM on a laptop, the *point* of using Spark
  is that the same code would work unchanged on 100x or 1000x more data
  (e.g. hourly weather for the whole world for 20 years).
  This script demonstrates:
    - reading a CSV/Parquet into a Spark DataFrame
    - aggregating at scale (monthly + daily summaries per city)
    - feature engineering (lag features, rolling means) with window functions
    - writing the results out as Parquet for downstream stages

Inputs : data/clean/weather_clean.csv  (or .parquet)
Outputs: data/clean/spark_monthly.parquet
         data/clean/spark_daily.parquet
         data/clean/spark_features.parquet   <- used by the model
"""

import os
from pyspark.sql import SparkSession, functions as F, Window

CLEAN_DIR = os.path.join("data", "clean")
IN_PATH   = os.path.join(CLEAN_DIR, "weather_clean.csv")

OUT_MONTHLY  = os.path.join(CLEAN_DIR, "spark_monthly.parquet")
OUT_DAILY    = os.path.join(CLEAN_DIR, "spark_daily.parquet")
OUT_FEATURES = os.path.join(CLEAN_DIR, "spark_features.parquet")


def build_spark() -> SparkSession:
    # Small local cluster — runs fine on a normal laptop.
    return (
        SparkSession.builder
        .appName("WeatherBigData")
        .master("local[*]")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.driver.memory", "2g")
        .getOrCreate()
    )


def main():
    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")

    print(f"Reading {IN_PATH} ...")
    df = (spark.read
          .option("header", True)
          .option("inferSchema", True)
          .csv(IN_PATH))

    # Spark reads "time" as string from CSV — cast it.
    df = df.withColumn("time", F.to_timestamp("time"))
    print(f"  rows: {df.count():,}")
    df.printSchema()

    # ---- Aggregation 1: monthly averages per city ---------------------------
    monthly = (df.groupBy("city", "year", "month")
                 .agg(
                     F.avg("temperature_2m").alias("avg_temp"),
                     F.min("temperature_2m").alias("min_temp"),
                     F.max("temperature_2m").alias("max_temp"),
                     F.avg("precipitation").alias("avg_precip"),
                     F.avg("wind_speed_10m").alias("avg_wind"),
                     F.count("*").alias("n_obs"),
                 )
                 .orderBy("city", "year", "month"))
    monthly.show(5)
    monthly.write.mode("overwrite").parquet(OUT_MONTHLY)

    # ---- Aggregation 2: daily averages per city -----------------------------
    daily = (df.groupBy("city", "year", "month", "day")
               .agg(
                   F.avg("temperature_2m").alias("avg_temp"),
                   F.min("temperature_2m").alias("min_temp"),
                   F.max("temperature_2m").alias("max_temp"),
                   F.sum("precipitation").alias("total_precip"),
               ))
    daily.write.mode("overwrite").parquet(OUT_DAILY)

    # ---- Feature engineering for the model ---------------------------------
    # Window: same city, ordered in time. Window functions are the killer
    # feature of Spark for time-series — they parallelize cleanly.
    w = Window.partitionBy("city").orderBy("time")

    feats = (df
             # 1-hour and 24-hour lag of temperature (yesterday-same-hour)
             .withColumn("temp_lag_1h",  F.lag("temperature_2m", 1).over(w))
             .withColumn("temp_lag_24h", F.lag("temperature_2m", 24).over(w))
             # 24h rolling mean of temperature (smooths out daily noise)
             .withColumn(
                 "temp_roll_24h",
                 F.avg("temperature_2m").over(w.rowsBetween(-23, 0))
             )
             # 24h rolling sum of precipitation
             .withColumn(
                 "precip_roll_24h",
                 F.sum("precipitation").over(w.rowsBetween(-23, 0))
             ))

    # Drop the first 24h per city — lag/rolling values are NULL there.
    feats = feats.dropna(subset=["temp_lag_1h", "temp_lag_24h", "temp_roll_24h"])

    print("  feature rows:", feats.count())
    feats.show(3)

    feats.write.mode("overwrite").parquet(OUT_FEATURES)
    print(f"  wrote {OUT_MONTHLY}, {OUT_DAILY}, {OUT_FEATURES}")

    spark.stop()


if __name__ == "__main__":
    main()
