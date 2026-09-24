import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.pkl"
REGISTRY_PATH = BASE_DIR / "models" / "registry.json"

RANGE_PERCENTILES = (10, 90)
# Smaller counterfactual deltas are forest noise (e.g. an older machine "saving" a minute).
MIN_DRIVER_MINUTES = 2
# Best-case reference for each condition; a driver is how many minutes the actual value adds or saves against it.
DRIVER_BASELINES = {
    "weather": ("Sunny", "sunny"),
    "operator_skill": ("Expert", "expert"),
    "machine_age_yrs": (1, "1-year-old machine"),
}
DRIVER_LABELS = {
    "weather": "{} weather",
    "operator_skill": "{} operator",
    "machine_age_yrs": "{}-year-old machine",
}

_model = None
_residual_band = None
_metadata = None


def get_model_metadata() -> dict:
    global _metadata
    if _metadata is None:
        if REGISTRY_PATH.exists():
            try:
                with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    active_ver = data.get("active_version")
                    for m in data.get("models", []):
                        if m.get("version") == active_ver:
                            _metadata = m
                            break
                    if _metadata is None and data.get("models"):
                        _metadata = data["models"][0]
            except Exception:
                pass
        if _metadata is None:
            _metadata = {"version": "v1.0.0", "metrics": {}}
    return _metadata


def get_model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model file not found at {MODEL_PATH}. Run 'python train.py' first to train and save the model."
            )
        _model = joblib.load(MODEL_PATH)
    return _model


def predict(task_type: str, weather: str, operator_skill: str, machine_age_yrs: int) -> float:
    """Predict actual task completion time in minutes given task parameters.

    Args:
        task_type: e.g. "Earth Excavation", "Trenching", "Material Loading", "Grading", "Demolition"
        weather: e.g. "Sunny", "Rainy", "Cloudy", "Windy"
        operator_skill: e.g. "Beginner", "Intermediate", "Expert"
        machine_age_yrs: machine age in years (integer)

    Returns:
        predicted task time in minutes (float)
    """
    model = get_model()
    input_df = pd.DataFrame(
        [
            {
                "task_type": task_type,
                "weather": weather,
                "operator_skill": operator_skill,
                "machine_age_yrs": machine_age_yrs,
            }
        ]
    )
    prediction = model.predict(input_df)[0]
    return float(prediction)


def get_residual_band() -> tuple[float, float]:
    """P10/P90 of out-of-fold prediction errors on the training data.

    Loaded directly from model registry if trained, or computed via 5-fold cross-validation.
    """
    global _residual_band
    if _residual_band is None:
        meta = get_model_metadata()
        if "residual_band" in meta and len(meta["residual_band"]) == 2:
            _residual_band = (float(meta["residual_band"][0]), float(meta["residual_band"][1]))
            return _residual_band

        from sklearn.model_selection import cross_val_predict

        from ml.train import CATEGORICAL_FEATURES, NUMERIC_FEATURES, TARGET, build_pipeline, load_dataset

        df = load_dataset()
        out_of_fold = cross_val_predict(build_pipeline(), df[CATEGORICAL_FEATURES + NUMERIC_FEATURES], df[TARGET], cv=5)
        low, high = np.percentile(df[TARGET] - out_of_fold, RANGE_PERCENTILES)
        _residual_band = (float(low), float(high))
    return _residual_band


def explain(task_type: str, weather: str, operator_skill: str, machine_age_yrs: int) -> dict:
    """Prediction with a likely range, what drives it, and model version metadata."""
    inputs = {
        "task_type": task_type,
        "weather": weather,
        "operator_skill": operator_skill,
        "machine_age_yrs": machine_age_yrs,
    }
    rows = [inputs] + [{**inputs, feature: baseline} for feature, (baseline, _) in DRIVER_BASELINES.items()]
    predictions = get_model().predict(pd.DataFrame(rows))
    minutes = float(predictions[0])
    low, high = get_residual_band()

    drivers = []
    for (feature, (baseline, compared_to)), counterfactual in zip(DRIVER_BASELINES.items(), predictions[1:]):
        delta = round(minutes - float(counterfactual))
        if inputs[feature] != baseline and abs(delta) >= MIN_DRIVER_MINUTES:
            drivers.append(
                {
                    "factor": feature,
                    "label": DRIVER_LABELS[feature].format(inputs[feature]),
                    "compared_to": compared_to,
                    "minutes": delta,
                }
            )

    meta = get_model_metadata()
    return {
        "minutes": minutes,
        "p10": max(1.0, minutes + low),
        "p90": minutes + high,
        "drivers": sorted(drivers, key=lambda d: -abs(d["minutes"])),
        "model_version": meta.get("version", "v1.0.0"),
    }


if __name__ == "__main__":
    # Test prediction with example from CONTRACT.md
    sample_res = predict(
        task_type="Trenching",
        weather="Rainy",
        operator_skill="Intermediate",
        machine_age_yrs=4,
    )
    exp = explain(
        task_type="Trenching",
        weather="Rainy",
        operator_skill="Intermediate",
        machine_age_yrs=4,
    )
    print(f"Test prediction: {sample_res:.2f} minutes, Version: {exp['model_version']}")

