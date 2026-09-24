from dataclasses import dataclass
from typing import Optional

IDLE_THRESHOLD_MIN = 45
PROXIMITY_ALERT_M = 2.0

SEVERITY_RANK = {"Low": 0, "Medium": 1, "High": 2}


@dataclass(frozen=True)
class Violation:
    type: str
    severity: str
    message: str


def evaluate_cab_reading(seatbelt_status: Optional[str], idling_time_min: Optional[int]) -> list[Violation]:
    """Every safety rule a single cab reading breaks."""
    violations = []
    if seatbelt_status == "Unfastened":
        violations.append(Violation("Seatbelt", "High", "Seatbelt unfastened during operation"))
    if idling_time_min is not None and idling_time_min > IDLE_THRESHOLD_MIN:
        violations.append(
            Violation(
                "Idling", "Medium", f"Idling time {idling_time_min}min exceeds threshold ({IDLE_THRESHOLD_MIN}min)"
            )
        )
    return violations


def evaluate_proximity(distance_m: float) -> Optional[Violation]:
    if distance_m <= PROXIMITY_ALERT_M:
        return Violation("Proximity", "High", f"Object within {PROXIMITY_ALERT_M:g}m of machine")
    return None


def summarize_log_reading(
    seatbelt_status: Optional[str], idling_time_min: Optional[int], alert_flag: bool
) -> Optional[Violation]:
    """One entry per flagged operation-log reading, typed by its most severe violation.

    Shared by the anomaly feed and the seed's alert backfill so both label a reading the same way.
    """
    violations = evaluate_cab_reading(seatbelt_status, idling_time_min)
    if violations:
        primary = max(violations, key=lambda v: SEVERITY_RANK[v.severity])
        return Violation(primary.type, primary.severity, "; ".join(v.message for v in violations))
    if alert_flag:
        return Violation("Anomaly", "Medium", "Safety alert triggered on machine")
    return None
