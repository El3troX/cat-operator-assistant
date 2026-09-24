# Machine Learning: Task-Time Duration Estimator

This module implements the task-time prediction pipeline for the CAT Smart Operator Assistant. It estimates machine task durations (in minutes) based on operating conditions, provides a P10–P90 confidence range, and attributes the factors driving the duration up or down.

---

## 1. Problem & Performance Summary

- **Human Estimation Baseline**: Human planners on the fleet overrun on **87% of tasks**, with an average error of **11.7 minutes**.
- **Our ML Model Performance**:
  - **Holdout MAE**: **~3.5 minutes** (~70% error reduction compared to humans).
  - **Holdout $R^2$**: **~0.96** (explains 96% of task variance).
  - **5-Fold Cross-Validation MAE**: **3.46 ± 0.34 minutes**.
  - **Confidence Interval**: P10–P90 quantile band based on out-of-fold residuals (covers ~76% of actual job times).

---

## 2. Model Architecture

The model is built as an end-to-end `sklearn.pipeline.Pipeline`:

1. **Preprocessing (`ColumnTransformer`)**:
   - **Categoricals**: `OneHotEncoder(handle_unknown="ignore", sparse_output=False)`
     - `task_type`: `"Earth Excavation"`, `"Trenching"`, `"Material Loading"`, `"Grading"`, `"Demolition"`
     - `weather`: `"Sunny"`, `"Rainy"`, `"Cloudy"`, `"Windy"`
     - `operator_skill`: `"Beginner"`, `"Intermediate"`, `"Expert"`
   - **Numeric**: Passthrough
     - `machine_age_yrs`: integer machine age in years (1–10)
2. **Estimator**:
   - `RandomForestRegressor(n_estimators=100, random_state=42)`

---

## 3. Explainability & Counterfactual Attribution

Rather than a single opaque estimate, `explain()` in `predict.py` returns:
1. `minutes`: Predicted time in minutes.
2. `p10` / `p90`: Lower and upper bounds representing the likely duration spread.
3. `drivers`: Condition deltas relative to optimal baseline conditions:
   - Baseline: `Sunny` weather, `Expert` operator, `1-year-old` machine.
   - Example: *"Rainy weather adds +9 min · Beginner operator adds +12 min"*.
4. `model_version`: Active model tag (e.g. `v2026.09.24`).

---

## 4. Model Versioning & Registry

Outputs are versioned under `ml/models/` rather than overwritten in place:

- **Artifacts**: `ml/models/model-{version}.pkl` (active copy linked to `ml/model.pkl`).
- **Registry (`ml/models/registry.json`)**:
  Tracks `active_version`, timestamp, git commit SHA, row count, CV metrics, and residual quantile bands.
- **Ledger (`ml/models/training_log.jsonl`)**: Append-only log recording every training run.

---

## 5. Dataset & Confidence Limits

- **Data Source**: `data/task_time_data.csv` (300 records).
- **Data Caveat**: The dataset is synthetic / sample hackathon data.
- **Extrapolation Bounds**:
  - Machines aged > 10 years are capped by tree leaf boundaries.
  - Novel weather or task combinations fall back to the global intercept with uncertainty reflected in the wider driver spreads.

---

## 6. How to Retrain the Model

Run the training pipeline with optional version tagging and automated regression thresholds:

```bash
# Standard training run (auto-generates version timestamp)
python ml/train.py

# Tagged training run with automated regression gate (fails if MAE > 5.0 min)
python ml/train.py --version v2026.09.24 --eval-threshold-mae 5.0
```

If holdout MAE exceeds `--eval-threshold-mae`, the command exits with code 1 to block deployment of regressed models in CI.
