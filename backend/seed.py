import argparse
import csv
import logging
import sys
from pathlib import Path
from typing import Optional

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database import SessionLocal, engine
from migrations import apply_migrations
from models import Alert, Incident, OperationLog, Task, TaskTimeData, TrainingModule
from services.rules import summarize_log_reading

logger = logging.getLogger("seed")


# Canonical reference modules required by coaching and scoring
REFERENCE_MODULES = [
    {
        "title": "Safe Excavation Basics",
        "format": "Video",
        "duration_min": 12,
        "completed": 0,
    },
    {
        "title": "Proximity Awareness & Site Safety",
        "format": "Simulation",
        "duration_min": 25,
        "completed": 0,
    },
    {
        "title": "Reducing Idle Time & Fuel Conservation",
        "format": "Instructor",
        "duration_min": 45,
        "completed": 1,
    },
    {
        "title": "Seatbelt & Safe Cab Entry",
        "format": "Video",
        "duration_min": 4,
        "completed": 0,
    },
]

DEMO_DAILY_TASKS = [
    {
        "machine_id": "EXC001",
        "operator_id": "OP1001",
        "task_type": "Earth Excavation",
        "status": "Completed",
        "scheduled_time": "2025-05-01T07:00:00",
        "estimated_time_min": 60,
        "actual_time_min": 58,
    },
    {
        "machine_id": "EXC002",
        "operator_id": "OP1005",
        "task_type": "Trenching",
        "status": "Completed",
        "scheduled_time": "2025-05-01T08:00:00",
        "estimated_time_min": 45,
        "actual_time_min": 52,
    },
    {
        "machine_id": "EXC003",
        "operator_id": "OP1003",
        "task_type": "Material Loading",
        "status": "Completed",
        "scheduled_time": "2025-05-01T08:30:00",
        "estimated_time_min": 30,
        "actual_time_min": 28,
    },
    {
        "machine_id": "EXC004",
        "operator_id": "OP1004",
        "task_type": "Grading",
        "status": "In Progress",
        "scheduled_time": "2025-05-01T09:30:00",
        "estimated_time_min": 35,
        "actual_time_min": None,
    },
    {
        "machine_id": "EXC005",
        "operator_id": "OP1006",
        "task_type": "Demolition",
        "status": "In Progress",
        "scheduled_time": "2025-05-01T10:00:00",
        "estimated_time_min": 90,
        "actual_time_min": None,
    },
    {
        "machine_id": "EXC001",
        "operator_id": "OP1008",
        "task_type": "Trenching",
        "status": "In Progress",
        "scheduled_time": "2025-05-01T10:15:00",
        "estimated_time_min": 45,
        "actual_time_min": None,
    },
    {
        "machine_id": "EXC002",
        "operator_id": "OP1009",
        "task_type": "Material Loading",
        "status": "Pending",
        "scheduled_time": "2025-05-01T11:00:00",
        "estimated_time_min": 30,
        "actual_time_min": None,
    },
    {
        "machine_id": "EXC003",
        "operator_id": "OP1005",
        "task_type": "Earth Excavation",
        "status": "Pending",
        "scheduled_time": "2025-05-01T11:30:00",
        "estimated_time_min": 60,
        "actual_time_min": None,
    },
    {
        "machine_id": "EXC004",
        "operator_id": "OP1002",
        "task_type": "Grading",
        "status": "Pending",
        "scheduled_time": "2025-05-01T13:00:00",
        "estimated_time_min": 35,
        "actual_time_min": None,
    },
    {
        "machine_id": "EXC005",
        "operator_id": "OP1007",
        "task_type": "Earth Excavation",
        "status": "Pending",
        "scheduled_time": "2025-05-01T14:00:00",
        "estimated_time_min": 60,
        "actual_time_min": None,
    },
    {
        "machine_id": "EXC001",
        "operator_id": "OP1002",
        "task_type": "Material Loading",
        "status": "Pending",
        "scheduled_time": "2025-05-01T14:30:00",
        "estimated_time_min": 30,
        "actual_time_min": None,
    },
    {
        "machine_id": "EXC002",
        "operator_id": "OP1010",
        "task_type": "Trenching",
        "status": "Pending",
        "scheduled_time": "2025-05-01T15:30:00",
        "estimated_time_min": 45,
        "actual_time_min": None,
    },
    {
        "machine_id": "EXC003",
        "operator_id": "OP1009",
        "task_type": "Demolition",
        "status": "Pending",
        "scheduled_time": "2025-05-01T16:00:00",
        "estimated_time_min": 90,
        "actual_time_min": None,
    },
    {
        "machine_id": "EXC004",
        "operator_id": "OP1007",
        "task_type": "Grading",
        "status": "Pending",
        "scheduled_time": "2025-05-01T16:30:00",
        "estimated_time_min": 35,
        "actual_time_min": None,
    },
]


def normalize_iso_timestamp(ts: str) -> str:
    ts = ts.strip()
    if " " in ts and "T" not in ts:
        return ts.replace(" ", "T")
    return ts


def parse_float(val: Optional[str]) -> Optional[float]:
    val = val.strip() if val else ""
    return float(val) if val else None


def parse_int(val: Optional[str]) -> Optional[int]:
    val = val.strip() if val else ""
    return int(float(val)) if val else None


def parse_alert_flag(val: Optional[str]) -> int:
    val = val.strip().lower() if val else ""
    return 1 if val in ("1", "yes", "true") else 0


def seed_reference_data(db) -> int:
    """Seed reference metadata (TrainingModule catalog).

    Guarantees that canonical training modules exist for the coaching loop,
    without overwriting or modifying completed user state.
    """
    existing_titles = {title for (title,) in db.query(TrainingModule.title)}
    new_modules = []
    for item in REFERENCE_MODULES:
        if item["title"] not in existing_titles:
            new_modules.append(TrainingModule(**item))

    if new_modules:
        db.add_all(new_modules)
        db.commit()
        logger.info("Seeded %d reference training module(s).", len(new_modules))
    else:
        logger.info("Reference training modules already up-to-date (%d existing).", len(existing_titles))
    return len(new_modules)


def seed_sample_data(db, reset: bool = True) -> dict[str, int]:
    """Seed demo/sample operational logs, task time training data, alerts, and daily tasks."""
    if reset:
        logger.info("Resetting demo/sample data tables (leaving reference catalog intact)...")
        db.query(Alert).delete()
        db.query(Incident).delete()
        db.query(Task).delete()
        db.query(TaskTimeData).delete()
        db.query(OperationLog).delete()
        db.commit()

    counts = {"operation_log": 0, "task_time_data": 0, "alerts": 0, "tasks": 0}

    # 1. Seed operation_log from machine_operations_log.csv
    csv_ops_path = PROJECT_ROOT / "data" / "machine_operations_log.csv"
    ops_records = []
    if not csv_ops_path.exists():
        logger.warning("CSV file not found at %s", csv_ops_path)
    else:
        logger.info("Loading operation logs from: %s", csv_ops_path)
        with open(csv_ops_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ops_records.append(
                    OperationLog(
                        timestamp=normalize_iso_timestamp(row.get("Timestamp", "")),
                        machine_id=row.get("Machine ID", "").strip(),
                        operator_id=row.get("Operator ID", "").strip(),
                        engine_hours=parse_float(row.get("Engine Hours")),
                        fuel_used_l=parse_float(row.get("Fuel Used (L)")),
                        load_cycles=parse_int(row.get("Load Cycles")),
                        idling_time_min=parse_int(row.get("Idling Time (min)")),
                        seatbelt_status=row.get("Seatbelt Status", "").strip(),
                        safety_alert_triggered=parse_alert_flag(row.get("Safety Alert Triggered", "0")),
                    )
                )
        db.bulk_save_objects(ops_records)
        db.commit()
        counts["operation_log"] = len(ops_records)
        logger.info("Seeded %d rows into 'operation_log'.", len(ops_records))

    # 2. Seed task_time_data from task_time_data.csv
    csv_task_path = PROJECT_ROOT / "data" / "task_time_data.csv"
    if not csv_task_path.exists():
        logger.warning("CSV file not found at %s", csv_task_path)
    else:
        logger.info("Loading task time data from: %s", csv_task_path)
        task_records = []
        with open(csv_task_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                task_records.append(
                    TaskTimeData(
                        task_id=row.get("Task ID", "").strip(),
                        task_type=row.get("Task Type", "").strip(),
                        weather=row.get("Weather", "").strip(),
                        operator_skill=row.get("Operator Skill", "").strip(),
                        machine_age_yrs=parse_int(row.get("Machine Age (yrs)")),
                        estimated_time_min=parse_int(row.get("Estimated Time (min)")),
                        actual_time_min=parse_int(row.get("Actual Time (min)")),
                    )
                )
        db.bulk_save_objects(task_records)
        db.commit()
        counts["task_time_data"] = len(task_records)
        logger.info("Seeded %d rows into 'task_time_data'.", len(task_records))

    # 3. Backfill one alert per flagged operation_log reading
    alert_records = []
    for op in ops_records:
        if op.safety_alert_triggered != 1:
            continue
        violation = summarize_log_reading(op.seatbelt_status, op.idling_time_min, alert_flag=True)
        alert_records.append(
            Alert(
                machine_id=op.machine_id,
                operator_id=op.operator_id,
                type=violation.type,
                severity=violation.severity,
                message=violation.message,
                timestamp=op.timestamp,
            )
        )
    if alert_records:
        db.bulk_save_objects(alert_records)
        db.commit()
        counts["alerts"] = len(alert_records)
        logger.info("Backfilled %d historical safety alerts into 'alerts'.", len(alert_records))

    # 4. Seed realistic daily demo tasks
    task_objs = [Task(**task_data) for task_data in DEMO_DAILY_TASKS]
    db.add_all(task_objs)
    db.commit()
    counts["tasks"] = len(task_objs)
    logger.info("Seeded %d daily tasks into 'tasks'.", len(task_objs))

    return counts


def seed_database(
    reference_only: bool = False,
    sample_only: bool = False,
    reset_sample: bool = True,
) -> None:
    logger.info("Applying Alembic migrations before seeding %s...", engine.url.render_as_string(hide_password=True))
    apply_migrations()

    db = SessionLocal()
    try:
        if not sample_only:
            seed_reference_data(db)
        if not reference_only:
            seed_sample_data(db, reset=reset_sample)
        logger.info("Database seeding completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the CAT Operator Assistant SQLite database.")
    parser.add_argument(
        "--reference-only",
        action="store_true",
        help="Only seed reference data (training module catalog).",
    )
    parser.add_argument(
        "--sample-only",
        action="store_true",
        help="Only seed demo/sample data (operations logs, tasks, alerts).",
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Append sample data without truncating existing rows.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    seed_database(
        reference_only=args.reference_only,
        sample_only=args.sample_only,
        reset_sample=not args.no_reset,
    )
