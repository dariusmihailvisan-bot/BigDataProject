# Git Plan — 12 incremental commits

This file lists 12 small, self-contained commits so you can build the
repo over 2 days and push to GitHub as you go. Do **not** backdate
anything — commit as you actually finish each stage.

---

## One-time setup (run once, at the very beginning)

```bash
# from the project root
cd D:\facultate\BigDataProject\BigDataProject

# initialize the local repo
git init -b main

# identify yourself (only needed once per machine)
git config user.name  "Darius Visan"
git config user.email "dariusmihail.visan@ulbsibiu.ro"

# ----- create an empty repo on github.com first -----
# Then connect it as the remote:
git remote add origin https://github.com/<your-user>/<repo>.git
```

After each stage below, the commands are the same shape:

```bash
git add <files for this stage>
git commit -m "<message>"
git push -u origin main      # the -u is only needed on the first push
```

(After the first push, just `git push`.)

---

## Stage 1 — scaffolding & gitignore

**Files**

```
.gitignore
README.md
requirements.txt
data/raw/.gitkeep
data/clean/.gitkeep
```

**Commit**

```bash
git add .gitignore README.md requirements.txt data/raw/.gitkeep data/clean/.gitkeep
git commit -m "chore: scaffold project structure, README, .gitignore"
```

---

## Stage 2 — data acquisition script

**Files**

```
src/01_data_acquisition.py
```

**Commit**

```bash
git add src/01_data_acquisition.py
git commit -m "feat(data): pull hourly weather for 10 cities from Open-Meteo"
```

---

## Stage 3 — Pandas preprocessing

**Files**

```
src/02_preprocessing.py
```

**Commit**

```bash
git add src/02_preprocessing.py
git commit -m "feat(clean): pandas preprocessing — dedupe, fill NaNs, types"
```

---

## Stage 4 — EDA notebook

**Files**

```
notebooks/03_eda.ipynb
```

**Commit**

```bash
git add notebooks/03_eda.ipynb
git commit -m "feat(eda): notebook with seasonality, city comparison, correlations"
```

---

## Stage 5 — PySpark processing

**Files**

```
src/04_spark_processing.py
```

**Commit**

```bash
git add src/04_spark_processing.py
git commit -m "feat(spark): aggregations + lag/rolling features via PySpark"
```

---

## Stage 6 — ML model

**Files**

```
src/05_model.py
```

**Commit**

```bash
git add src/05_model.py
git commit -m "feat(model): linear regression + random forest, MAE/RMSE report"
```

---

## Stage 7 — dashboard export script

**Files**

```
src/06_dashboard_export.py
```

**Commit**

```bash
git add src/06_dashboard_export.py
git commit -m "feat(dashboard): daily-aggregated CSV + Plotly HTML export"
```

---

## Stage 8 — dashboard guide

**Files**

```
dashboard/DASHBOARD_GUIDE.md
```

**Commit**

```bash
git add dashboard/DASHBOARD_GUIDE.md
git commit -m "docs(dashboard): Tableau Public & Power BI step-by-step guide"
```

---

## Stage 9 — flesh out README

(After you've run the pipeline once and have real numbers to put in.)

**Files**

```
README.md
```

**Commit**

```bash
git add README.md
git commit -m "docs(readme): add architecture, usage, key findings"
```

---

## Stage 10 — git plan

**Files**

```
GIT_PLAN.md
```

**Commit**

```bash
git add GIT_PLAN.md
git commit -m "docs: add 12-stage git commit plan"
```

---

## Stage 11 — bug-fix / polish pass

(Anything that came up while running the pipeline — e.g. tweaks to
column names, a smarter median fill, fixing a chart label.)

**Commit**

```bash
git add -A
git commit -m "fix: small polish pass after end-to-end run"
```

---

## Stage 12 — final demo screenshots

Take 2–3 screenshots of your dashboard / charts, save them under
`docs/screenshots/` (create the folder), reference them at the bottom of
the README, and commit.

**Files**

```
docs/screenshots/*.png
README.md
```

**Commit**

```bash
git add docs/screenshots README.md
git commit -m "docs: add dashboard screenshots and demo references"
git push
```

---

## Cheat sheet

```bash
git status                    # what's changed
git diff                      # what's changed, with content
git log --oneline             # commit history
git push                      # push current branch to GitHub
git pull                      # pull latest from GitHub
```

That's it — push after each stage and you'll have a clean, presentable
GitHub history showing the project evolving stage by stage.
