# Dashboard Guide — Tableau Public / Power BI

The file `dashboard/weather_dashboard.csv` is the input. It has one row
per (city, day) with columns:

| Column         | Meaning                                       |
|----------------|-----------------------------------------------|
| date           | Day (yyyy-mm-dd)                              |
| city           | City name                                     |
| latitude       | City latitude (for map charts)                |
| longitude      | City longitude (for map charts)               |
| avg_temp       | Daily average temperature (°C)                |
| min_temp       | Daily min temperature (°C)                    |
| max_temp       | Daily max temperature (°C)                    |
| avg_humidity   | Daily average relative humidity (%)           |
| total_precip   | Daily total precipitation (mm)                |
| avg_wind       | Daily average wind speed (m/s)                |
| model_mae      | Daily mean absolute error of the temp model   |

---

## Option A — Tableau Public (free)

1. Open Tableau Public Desktop.
2. **Connect → Text file → `weather_dashboard.csv`**.
3. Tableau auto-detects types. Make sure `date` is **Date**, `city` is
   **String**, `latitude`/`longitude` are **Number (decimal)** and set
   their geographic role to Latitude/Longitude.
4. Build these four sheets:

   **Sheet 1 — Temperature over time**
   - Columns: `date` (continuous, day)
   - Rows: `avg_temp` (avg)
   - Color: `city`
   - Mark type: Line

   **Sheet 2 — Seasonality heatmap**
   - Columns: `MONTH(date)`
   - Rows: `city`
   - Color: `avg_temp` (avg, red→blue diverging)
   - Mark type: Square

   **Sheet 3 — Map**
   - Drag `latitude` to Rows, `longitude` to Columns
   - Detail: `city`
   - Size & Color: `avg_temp` (avg)

   **Sheet 4 — Precipitation by city**
   - Columns: `city`
   - Rows: `total_precip` (sum)
   - Mark type: Bar

5. **Dashboard → New Dashboard.** Drag all 4 sheets in. Add a date-range
   filter applied to all sheets.
6. **File → Save to Tableau Public.** Get a shareable URL.

---

## Option B — Power BI Desktop (free)

1. **Home → Get Data → Text/CSV → `weather_dashboard.csv` → Load**.
2. In the model view, make sure `date` is **Date**, `latitude`/`longitude`
   are **Decimal**.
3. Build these visuals on a single report page:

   - **Line chart** — Axis: `date`, Values: `avg_temp`, Legend: `city`.
   - **Matrix / heatmap** — Rows: `city`, Columns: `Month` of `date`,
     Values: `avg_temp`, conditional formatting red→blue.
   - **Map** (built-in Map visual) — Location: `city`,
     Latitude: `latitude`, Longitude: `longitude`, Size: `avg_temp`.
   - **Bar chart** — Axis: `city`, Values: `total_precip` (sum).
   - **Card** — Value: `model_mae` (avg) → headline "Avg model error °C".

4. Add a **Slicer** on `date` and one on `city` — they will cross-filter
   every chart.
5. Save the `.pbix` next to this guide.

---

## Backup — Plotly HTML
If you don't want to install Tableau or Power BI, open
`dashboard/weather_dashboard.html` in any browser. It has the same four
charts (line, seasonality, map, distribution) and works offline. 
