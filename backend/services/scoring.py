from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import case, func
from sqlalchemy.orm import Session

import models
from services.rules import IDLE_THRESHOLD_MIN

# Behaviour factors use each operator's whole logged history; event factors use a recent window,
# otherwise simulator alerts accumulate until every operator sits at the cap.
PROXIMITY_WINDOW = timedelta(hours=1)
SHIFT_WINDOW = timedelta(hours=8)

SEATBELT_PTS_PER_PCT, SEATBELT_MAX = 1.0, 40
IDLE_PTS_PER_PCT, IDLE_MAX = 0.5, 25
PROXIMITY_PTS_EACH, PROXIMITY_MAX = 3, 15
INCIDENT_PTS = {"High": 10, "Medium": 5, "Low": 2}
INCIDENT_MAX = 20

# A factor assigns its module once its penalty reaches this many points.
ASSIGN_AT = {"seatbelt": 15, "idling": 10, "proximity": 6, "incidents": 5}
MODULE_FOR = {
    "seatbelt": "Seatbelt & Safe Cab Entry",
    "idling": "Reducing Idle Time & Fuel Conservation",
    "proximity": "Proximity Awareness & Site Safety",
    "incidents": "Safe Excavation Basics",
}

# Reference modules the coaching loop relies on; inserted at startup if a database predates them.
CATALOG = [
    {"title": "Seatbelt & Safe Cab Entry", "format": "Video", "duration_min": 4},
]


@dataclass
class Factor:
    factor: str
    penalty: int
    detail: str


@dataclass
class OperatorScore:
    operator_id: str
    score: int
    band: str
    readings: int
    factors: list[Factor] = field(default_factory=list)
    recommended_modules: list[dict] = field(default_factory=list)


def ensure_training_catalog(db: Session) -> None:
    existing = {title for (title,) in db.query(models.TrainingModule.title)}
    missing = [models.TrainingModule(**module, completed=0) for module in CATALOG if module["title"] not in existing]
    if missing:
        db.add_all(missing)
        db.commit()


def _band(score: int) -> str:
    if score >= 80:
        return "Good"
    if score >= 60:
        return "Watch"
    return "At risk"


def _since(window: timedelta, now: datetime) -> str:
    # Stored timestamps are naive local ISO strings (see schemas.Timestamp), so string comparison is ordering.
    return (now - window).isoformat(timespec="seconds")


def operator_scores(db: Session, operator_id: Optional[str] = None, now: Optional[datetime] = None) -> list[OperatorScore]:
    now = now or datetime.now()
    log = models.OperationLog

    readings_q = db.query(
        log.operator_id,
        func.count(),
        func.sum(case((log.seatbelt_status == "Unfastened", 1), else_=0)),
        func.sum(case((log.idling_time_min > IDLE_THRESHOLD_MIN, 1), else_=0)),
    ).group_by(log.operator_id)
    proximity_q = (
        db.query(models.Alert.operator_id, func.count())
        .filter(models.Alert.type == "Proximity", models.Alert.timestamp >= _since(PROXIMITY_WINDOW, now))
        .group_by(models.Alert.operator_id)
    )
    incidents_q = (
        db.query(models.Incident.operator_id, models.Incident.severity, func.count())
        .filter(models.Incident.timestamp >= _since(SHIFT_WINDOW, now))
        .group_by(models.Incident.operator_id, models.Incident.severity)
    )
    if operator_id:
        readings_q = readings_q.filter(log.operator_id == operator_id)
        proximity_q = proximity_q.filter(models.Alert.operator_id == operator_id)
        incidents_q = incidents_q.filter(models.Incident.operator_id == operator_id)

    readings = {op: (n, unbelted or 0, idle or 0) for op, n, unbelted, idle in readings_q}
    proximity = dict(proximity_q.all())
    incidents: dict[str, dict[str, int]] = {}
    for op, severity, count in incidents_q:
        incidents.setdefault(op, {})[severity or "Low"] = count

    operators = (set(readings) | set(proximity) | set(incidents)) - {"SYSTEM"}
    modules = {m.title: m for m in db.query(models.TrainingModule)}

    results = []
    for op in operators:
        n, unbelted, idle = readings.get(op, (0, 0, 0))
        factors = []
        if n:
            unbelted_pct, idle_pct = 100 * unbelted / n, 100 * idle / n
            factors.append(
                Factor("seatbelt", min(SEATBELT_MAX, round(unbelted_pct * SEATBELT_PTS_PER_PCT)), f"Unbelted in {unbelted_pct:.0f}% of logged readings")
            )
            factors.append(
                Factor("idling", min(IDLE_MAX, round(idle_pct * IDLE_PTS_PER_PCT)), f"Idled over {IDLE_THRESHOLD_MIN} min in {idle_pct:.0f}% of readings")
            )
        breaches = proximity.get(op, 0)
        factors.append(
            Factor("proximity", min(PROXIMITY_MAX, breaches * PROXIMITY_PTS_EACH), f"{breaches} proximity breach{'es' if breaches != 1 else ''} in the last hour")
        )
        by_severity = incidents.get(op, {})
        incident_count = sum(by_severity.values())
        factors.append(
            Factor(
                "incidents",
                min(INCIDENT_MAX, sum(INCIDENT_PTS.get(sev, 2) * count for sev, count in by_severity.items())),
                f"{incident_count} incident{'s' if incident_count != 1 else ''} reported this shift",
            )
        )

        score = max(0, 100 - sum(f.penalty for f in factors))
        recommended = []
        for f in sorted(factors, key=lambda f: -f.penalty):
            module = modules.get(MODULE_FOR[f.factor])
            if module and f.penalty >= ASSIGN_AT[f.factor]:
                recommended.append(
                    {
                        "id": module.id,
                        "title": module.title,
                        "format": module.format,
                        "duration_min": module.duration_min,
                        "completed": module.completed or 0,
                        "reason": f.detail,
                    }
                )
        results.append(OperatorScore(op, score, _band(score), n, factors, recommended))

    return sorted(results, key=lambda s: (s.score, s.operator_id))
