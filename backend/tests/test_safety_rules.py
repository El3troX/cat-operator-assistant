from services.rules import (
    IDLE_THRESHOLD_MIN,
    PROXIMITY_ALERT_M,
    evaluate_cab_reading,
    evaluate_proximity,
    summarize_log_reading,
)


def test_evaluate_cab_reading_compliant():
    """A safe reading with seatbelt fastened and idle time within threshold raises no violations."""
    violations = evaluate_cab_reading(seatbelt_status="Fastened", idling_time_min=20)
    assert violations == []


def test_evaluate_cab_reading_seatbelt_violation():
    """Unfastened seatbelt raises a High severity violation."""
    violations = evaluate_cab_reading(seatbelt_status="Unfastened", idling_time_min=10)
    assert len(violations) == 1
    assert violations[0].type == "Seatbelt"
    assert violations[0].severity == "High"
    assert "Seatbelt unfastened" in violations[0].message


def test_evaluate_cab_reading_idling_violation():
    """Idling above 45 min threshold raises a Medium severity violation."""
    violations = evaluate_cab_reading(seatbelt_status="Fastened", idling_time_min=46)
    assert len(violations) == 1
    assert violations[0].type == "Idling"
    assert violations[0].severity == "Medium"
    assert f"exceeds threshold ({IDLE_THRESHOLD_MIN}min)" in violations[0].message


def test_evaluate_cab_reading_idling_boundary():
    """Exactly at threshold (45 min) should not violate."""
    violations = evaluate_cab_reading(seatbelt_status="Fastened", idling_time_min=IDLE_THRESHOLD_MIN)
    assert violations == []


def test_evaluate_cab_reading_multiple_violations():
    """Both unfastened seatbelt and excessive idling generate two distinct violations."""
    violations = evaluate_cab_reading(seatbelt_status="Unfastened", idling_time_min=55)
    assert len(violations) == 2
    types = [v.type for v in violations]
    assert "Seatbelt" in types
    assert "Idling" in types


def test_evaluate_cab_reading_none_values():
    """Gracefully handles None values for optional parameters."""
    violations = evaluate_cab_reading(seatbelt_status=None, idling_time_min=None)
    assert violations == []


def test_evaluate_proximity_hazard():
    """Distance <= PROXIMITY_ALERT_M (2.0m) triggers a High severity violation."""
    v_close = evaluate_proximity(1.2)
    assert v_close is not None
    assert v_close.type == "Proximity"
    assert v_close.severity == "High"
    assert f"within {PROXIMITY_ALERT_M:g}m" in v_close.message

    v_boundary = evaluate_proximity(2.0)
    assert v_boundary is not None
    assert v_boundary.severity == "High"


def test_evaluate_proximity_safe():
    """Distance > 2.0m is considered safe and returns None."""
    assert evaluate_proximity(2.01) is None
    assert evaluate_proximity(5.0) is None
    assert evaluate_proximity(15.0) is None


def test_summarize_log_reading_prefers_highest_severity():
    """When both Seatbelt (High) and Idling (Medium) trigger, the primary type is Seatbelt."""
    summary = summarize_log_reading(seatbelt_status="Unfastened", idling_time_min=60, alert_flag=False)
    assert summary is not None
    assert summary.type == "Seatbelt"
    assert summary.severity == "High"
    # Detail message should document both issues
    assert "Seatbelt unfastened" in summary.message
    assert "Idling time" in summary.message


def test_summarize_log_reading_flag_only():
    """When no cab rules triggered but safety_alert_triggered was flagged in data, typed as Anomaly."""
    summary = summarize_log_reading(seatbelt_status="Fastened", idling_time_min=10, alert_flag=True)
    assert summary is not None
    assert summary.type == "Anomaly"
    assert summary.severity == "Medium"
    assert "Safety alert triggered" in summary.message


def test_summarize_log_reading_clean():
    """Clean reading with no flag returns None."""
    assert summarize_log_reading(seatbelt_status="Fastened", idling_time_min=10, alert_flag=False) is None
