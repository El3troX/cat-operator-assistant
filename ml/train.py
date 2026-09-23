import argparse
import logging
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DEFAULT_OUTPUT = BASE_DIR / "model.pkl"
CSV_CANDIDATES = [BASE_DIR / "task_time_data.csv", PROJECT_ROOT / "data" / "task_time_data.csv"]

CATEGORICAL_FEATURES = ["task_type", "weather", "operator_skill"]
NUMERIC_FEATURES = ["machine_age_yrs"]
TARGET = "actual_time_min"

logger = logging.getLogger("ml.train")


def load_dataset() -> pd.DataFrame:
    csv_file = next((path for path in CSV_CANDIDATES if path.exists()), None)
    if csv_file is None:
        raise FileNotFoundError(f"Could not find task_time_data.csv in {[str(p) for p in CSV_CANDIDATES]}")

    logger.info("Loading data from: %s", csv_file)
    df = pd.read_csv(csv_file)
    df.columns = [
        col.strip().lower().replace(" ", "_").replace("(", "").replace(")", "") for col in df.columns
    ]
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


def main(output: Path) -> None:
    df = load_dataset()
    features = df[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
    X_train, X_test, y_train, y_test = train_test_split(features, df[TARGET], test_size=0.2, random_state=42)

    pipeline = build_pipeline()
    logger.info("Training RandomForestRegressor pipeline...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    logger.info("Holdout MAE: %.2f minutes | R2: %.4f (%.1f%% variance explained)", mae, r2, r2 * 100)

    joblib.dump(pipeline, output)
    logger.info("Model saved to: %s", output)

    sample = pd.DataFrame(
        [{"task_type": "Trenching", "weather": "Rainy", "operator_skill": "Intermediate", "machine_age_yrs": 4}]
    )
    logger.info("Sample prediction [Trenching, Rainy, Intermediate, 4 yrs]: %.1f minutes", pipeline.predict(sample)[0])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the task-time regression model.")
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT, help=f"where to write the fitted pipeline (default: {DEFAULT_OUTPUT})"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main(args.output)
