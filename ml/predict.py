from pathlib import Path
import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.pkl"

_model = None


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


if __name__ == "__main__":
    # Test prediction with example from CONTRACT.md
    sample_res = predict(
        task_type="Trenching",
        weather="Rainy",
        operator_skill="Intermediate",
        machine_age_yrs=4,
    )
    print(f"Test prediction: {sample_res:.2f} minutes")
