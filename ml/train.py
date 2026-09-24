import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import cross_val_predict, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
MODELS_DIR = BASE_DIR / "models"
REGISTRY_PATH = MODELS_DIR / "registry.json"
TRAINING_LOG_PATH = MODELS_DIR / "training_log.jsonl"
DEFAULT_OUTPUT = BASE_DIR / "model.pkl"
CSV_CANDIDATES = [BASE_DIR / "task_time_data.csv", PROJECT_ROOT / "data" / "task_time_data.csv"]

CATEGORICAL_FEATURES = ["task_type", "weather", "operator_skill"]
NUMERIC_FEATURES = ["machine_age_yrs"]
TARGET = "actual_time_min"
RANGE_PERCENTILES = (10, 90)

logger = logging.getLogger("ml.train")


def get_git_commit() -> str:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(PROJECT_ROOT),
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        return commit
    except Exception:
        return "unknown"


def load_dataset() -> pd.DataFrame:
    csv_file = next((path for path in CSV_CANDIDATES if path.exists()), None)
    if csv_file is None:
        raise FileNotFoundError(f"Could not find task_time_data.csv in {[str(p) for p in CSV_CANDIDATES]}")

    logger.info("Loading data from: %s", csv_file)
    df = pd.read_csv(csv_file)
    df.columns = [col.strip().lower().replace(" ", "_").replace("(", "").replace(")", "") for col in df.columns]
    logger.info("Dataset shape: %s, columns: %s", df.shape, list(df.columns))
    return df


def build_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
            ("num", "passthrough", NUMERIC_FEATURES),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", RandomForestRegressor(n_estimators=100, random_state=42)),
        ]
    )


def update_registry(entry: dict) -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    registry = {"active_version": entry["version"], "models": []}
    if REGISTRY_PATH.exists():
        try:
            with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
                registry["models"] = existing.get("models", [])
        except Exception as exc:
            logger.warning("Could not read existing registry, creating fresh: %s", exc)

    # Filter out duplicate version entries
    registry["models"] = [m for m in registry["models"] if m.get("version") != entry["version"]]
    registry["models"].insert(0, entry)
    registry["active_version"] = entry["version"]

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)
    logger.info("Registry updated at: %s", REGISTRY_PATH)

    with open(TRAINING_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def train_model(version: str | None = None, eval_threshold_mae: float | None = None) -> dict:
    df = load_dataset()
    features = df[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
    y = df[TARGET]

    # Version identifier
    now = datetime.now(timezone.utc)
    version_tag = version or f"v{now.strftime('%Y%m%d_%H%M%S')}"
    git_sha = get_git_commit()

    # 1. 5-fold cross-validation on full dataset
    logger.info("Running 5-fold cross-validation...")
    cv_pipeline = build_pipeline()
    cv_scores = -cross_val_score(cv_pipeline, features, y, cv=5, scoring="neg_mean_absolute_error")
    cv_mae_mean = float(np.mean(cv_scores))
    cv_mae_std = float(np.std(cv_scores))
    logger.info("5-Fold CV MAE: %.2f ± %.2f minutes", cv_mae_mean, cv_mae_std)

    # Out-of-fold residuals for P10/P90 interval estimation
    oof_predictions = cross_val_predict(build_pipeline(), features, y, cv=5)
    residuals = y - oof_predictions
    p10_offset, p90_offset = np.percentile(residuals, RANGE_PERCENTILES)
    logger.info("Residual quantile band: P10 %+.2f min, P90 %+.2f min", p10_offset, p90_offset)

    # 2. Holdout test evaluation (80/20 train/test split)
    X_train, X_test, y_train, y_test = train_test_split(features, y, test_size=0.2, random_state=42)
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    holdout_mae = float(mean_absolute_error(y_test, y_pred))
    holdout_r2 = float(r2_score(y_test, y_pred))
    logger.info("Holdout Test MAE: %.2f minutes | R2: %.4f (%.1f%% variance explained)", holdout_mae, holdout_r2, holdout_r2 * 100)

    # Regression gate check
    if eval_threshold_mae is not None and holdout_mae > eval_threshold_mae:
        error_msg = f"Holdout MAE {holdout_mae:.2f} min exceeds regression threshold of {eval_threshold_mae:.2f} min!"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # 3. Train final model on entire dataset for production deployment
    final_pipeline = build_pipeline()
    final_pipeline.fit(features, y)

    # Save versioned artifact
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    versioned_filename = f"model-{version_tag}.pkl"
    versioned_path = MODELS_DIR / versioned_filename
    joblib.dump(final_pipeline, versioned_path)
    logger.info("Versioned artifact saved: %s", versioned_path)

    # Also update active model.pkl
    joblib.dump(final_pipeline, DEFAULT_OUTPUT)
    logger.info("Active model updated: %s", DEFAULT_OUTPUT)

    entry = {
        "version": version_tag,
        "created_at": now.isoformat(),
        "git_commit": git_sha,
        "dataset_rows": len(df),
        "features": {
            "categorical": CATEGORICAL_FEATURES,
            "numeric": NUMERIC_FEATURES,
            "target": TARGET,
        },
        "metrics": {
            "holdout_mae": round(holdout_mae, 4),
            "holdout_r2": round(holdout_r2, 4),
            "cv_mae_mean": round(cv_mae_mean, 4),
            "cv_mae_std": round(cv_mae_std, 4),
        },
        "residual_band": [round(float(p10_offset), 2), round(float(p90_offset), 2)],
        "artifact_file": versioned_filename,
    }

    update_registry(entry)

    # Sample inference check
    sample = pd.DataFrame(
        [{"task_type": "Trenching", "weather": "Rainy", "operator_skill": "Intermediate", "machine_age_yrs": 4}]
    )
    predicted_sample = final_pipeline.predict(sample)[0]
    logger.info("Sanity prediction [Trenching, Rainy, Intermediate, 4 yrs]: %.1f minutes", predicted_sample)

    return entry


def main():
    parser = argparse.ArgumentParser(description="Train and version the task-time regression pipeline.")
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="custom version tag (e.g. v2026.09.24); defaults to timestamp",
    )
    parser.add_argument(
        "--eval-threshold-mae",
        type=float,
        default=5.0,
        help="maximum acceptable holdout MAE in minutes (regression gate, default 5.0 min)",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    try:
        train_model(version=args.version, eval_threshold_mae=args.eval_threshold_mae)
    except Exception as exc:
        logger.error("Training failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
