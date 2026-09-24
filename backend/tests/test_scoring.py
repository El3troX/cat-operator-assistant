import models
from services.scoring import (
    CATALOG,
    _band,
    ensure_training_catalog,
    operator_scores,
)


def test_band_classification():
    assert _band(100) == "Good"
    assert _band(80) == "Good"
    assert _band(79) == "Watch"
    assert _band(60) == "Watch"
    assert _band(59) == "At risk"
    assert _band(0) == "At risk"


def test_ensure_training_catalog(db_session):
    """Catalog modules are inserted if missing, but not duplicated."""
    db_session.query(models.TrainingModule).delete()
    db_session.commit()

    ensure_training_catalog(db_session)
    count1 = db_session.query(models.TrainingModule).count()
    assert count1 >= len(CATALOG)

    # Calling again does not duplicate
    ensure_training_catalog(db_session)
    count2 = db_session.query(models.TrainingModule).count()
    assert count1 == count2


def test_operator_scores_computation(db_session, seed_test_data):
    """Operator scores are correctly calculated and reflect penalties."""
    scores = operator_scores(db_session)
    assert len(scores) > 0

    op1001 = next((s for s in scores if s.operator_id == "OP1001"), None)
    assert op1001 is not None
    # OP1001 had an unfastened reading and a 55 min idle reading
    assert op1001.score < 100
    assert op1001.band in ("Good", "Watch", "At risk")
    assert op1001.readings >= 2

    factor_names = [f.factor for f in op1001.factors]
    assert "seatbelt" in factor_names or "idling" in factor_names


def test_operator_scores_single_operator_filter(db_session, seed_test_data):
    """Querying by operator_id filters results to just that operator."""
    scores = operator_scores(db_session, operator_id="OP1002")
    assert len(scores) == 1
    assert scores[0].operator_id == "OP1002"
