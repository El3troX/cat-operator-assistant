from pathlib import Path
import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.pkl"

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
    """
    Predict actual task completion time in minutes given task parameters.
    
    Args:
        task_type: e.g. "Earth Excavation", "Trenching", "Material Loading", "Grading", "Demolition"
        weather: e.g. "Sunny", "Rainy", "Cloudy", "Windy"
        operator_skill: e.g. "Beginner", "Intermediate", "Expert"
        machine_age_yrs: machine age in years (integer)
        
    Returns:
        predicted task time in minutes (float)
    """
    model = get_model()
    input_df = pd.DataFrame([
        {
            "task_type": task_type,
            "weather": weather,
            "operator_skill": operator_skill,
            "machine_age_yrs": machine_age_yrs,
        }
    ])
    prediction = model.predict(input_df)[0]
    return float(prediction)


def get_residual_band() -> tuple[float, float]:
    """P10/P90 of out-of-fold prediction errors on the training data.

    The spread of the forest's individual trees covered only ~59% of held-out actual times
    for a nominal 80% range; these residual quantiles covered ~76%.
    """
    global _residual_band
    if _residual_band is None:
        from sklearn.model_selection import cross_val_predict

        from ml.train import CATEGORICAL_FEATURES, NUMERIC_FEATURES, TARGET, build_pipeline, load_dataset

        df = load_dataset()
        out_of_fold = cross_val_predict(build_pipeline(), df[CATEGORICAL_FEATURES + NUMERIC_FEATURES], df[TARGET], cv=5)
        low, high = np.percentile(df[TARGET] - out_of_fold, RANGE_PERCENTILES)
        _residual_band = (float(low), float(high))
    return _residual_band


def explain(task_type: str, weather: str, operator_skill: str, machine_age_yrs: int) -> dict:
    """Prediction with a likely range and the conditions pushing it up or down."""
    inputs = {"task_type": task_type, "weather": weather, "operator_skill": operator_skill, "machine_age_yrs": machine_age_yrs}
    rows = [inputs] + [{**inputs, feature: baseline} for feature, (baseline, _) in DRIVER_BASELINES.items()]
    predictions = get_model().predict(pd.DataFrame(rows))
    minutes = float(predictions[0])
    low, high = get_residual_band()

    drivers = []
    for (feature, (baseline, compared_to)), counterfactual in zip(DRIVER_BASELINES.items(), predictions[1:]):
        delta = round(minutes - float(counterfactual))
        if inputs[feature] != baseline and abs(delta) >= MIN_DRIVER_MINUTES:
            drivers.append(
                {"factor": feature, "label": DRIVER_LABELS[feature].format(inputs[feature]), "compared_to": compared_to, "minutes": delta}
            )

    return {
        "minutes": minutes,
        "p10": max(1.0, minutes + low),
        "p90": minutes + high,
        "drivers": sorted(drivers, key=lambda d: -abs(d["minutes"])),
    }


if __name__ == "__main__":
    # Test prediction with example from CONTRACT.md
    sample_res = predict(
        task_type="Trenching",
        weather="Rainy",
        operator_skill="Intermediate",
        machine_age_yrs=4,
    )
    print(f"Test prediction: {sample_res:.2f} minutes")
