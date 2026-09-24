import pytest

from ml.predict import explain, get_model, get_model_metadata, get_residual_band, predict
from ml.train import train_model

TASK_TYPES = ["Earth Excavation", "Trenching", "Material Loading", "Grading", "Demolition"]
WEATHERS = ["Sunny", "Rainy", "Cloudy", "Windy"]
SKILLS = ["Beginner", "Intermediate", "Expert"]


def test_model_loads_successfully():
    """Verify that model artifact loads and is a trained estimator."""
    model = get_model()
    assert model is not None
    assert hasattr(model, "predict")


def test_model_registry_metadata():
    """Verify model metadata is loaded from registry and contains metrics."""
    meta = get_model_metadata()
    assert meta is not None
    assert "version" in meta
    assert meta["version"].startswith("v")


def test_residual_band_calculated():
    """Residual band should have negative lower bound and positive upper bound."""
    low, high = get_residual_band()
    assert isinstance(low, float)
    assert isinstance(high, float)
    assert low < 0
    assert high > 0


@pytest.mark.parametrize("task_type", TASK_TYPES)
def test_predict_sane_bounds_all_tasks(task_type):
    """Ensure predicted task time falls within plausible bounds (10 to 300 minutes)."""
    predicted = predict(
        task_type=task_type,
        weather="Sunny",
        operator_skill="Intermediate",
        machine_age_yrs=3,
    )
    assert isinstance(predicted, float)
    assert 10 <= predicted <= 300, f"Predicted time {predicted} outside sane bounds for {task_type}"


def test_predict_skill_impact():
    """Expert operators should take less or equal time than Beginners under identical conditions."""
    expert_time = predict("Trenching", "Sunny", "Expert", machine_age_yrs=2)
    beginner_time = predict("Trenching", "Sunny", "Beginner", machine_age_yrs=2)
    assert expert_time <= beginner_time, (
        f"Expert time ({expert_time}) was expected to be <= Beginner time ({beginner_time})"
    )


def test_explain_structure_and_intervals():
    """Explain should return minutes, p10, p90, drivers, and model_version."""
    res = explain(
        task_type="Trenching",
        weather="Rainy",
        operator_skill="Beginner",
        machine_age_yrs=5,
    )
    assert "minutes" in res
    assert "p10" in res
    assert "p90" in res
    assert "drivers" in res
    assert "model_version" in res
    assert res["model_version"] is not None

    minutes = res["minutes"]
    p10 = res["p10"]
    p90 = res["p90"]

    # Bounds check
    assert p10 >= 1.0
    assert p10 <= minutes <= p90

    # Drivers check
    drivers = res["drivers"]
    assert isinstance(drivers, list)
    for driver in drivers:
        assert "factor" in driver
        assert "label" in driver
        assert "compared_to" in driver
        assert "minutes" in driver
        assert isinstance(driver["minutes"], int)


def test_training_regression_gate_fails():
    """Regression gate raises ValueError when MAE threshold is unachievable."""
    with pytest.raises(ValueError, match="exceeds regression threshold"):
        train_model(version="vtest_fail", eval_threshold_mae=0.001)
