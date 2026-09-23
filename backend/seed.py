import argparse
import csv
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
sys.path.insert(0, str(BASE_DIR))

from database import Base, SessionLocal, engine
from models import Alert, Incident, OperationLog, Task, TaskTimeData, TrainingModule


def normalize_iso_timestamp(ts: str) -> str:
    ts = ts.strip()
    if " " in ts and "T" not in ts:
        return ts.replace(" ", "T")
    return ts


def parse_float(val: str):
    val = val.strip() if val else ""
    return float(val) if val else None


def parse_int(val: str):
    val = val.strip() if val else ""
    return int(float(val)) if val else None


def parse_alert_flag(val: str) -> int:
    val = val.strip().lower() if val else ""
    return 1 if val in ("1", "yes", "true") else 0


def seed_database(reset: bool = True):
    print("=" * 60)
    print("Starting database seed process...")
    print("=" * 60)

    # Ensure tables are created
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if reset:
            print("Resetting existing records in tables...")
            db.query(OperationLog).delete()
            db.query(TaskTimeData).delete()
            db.query(Task).delete()
            db.query(Incident).delete()
            db.query(Alert).delete()
            db.query(TrainingModule).delete()
            db.commit()

        # 1. Seed operation_log from machine_operations_log.csv
        csv_ops_path = PROJECT_ROOT / "data" / "machine_operations_log.csv"
        if not csv_ops_path.exists():
            print(f"Warning: CSV file not found at {csv_ops_path}")
        else:
            print(f"Loading operation logs from: {csv_ops_path}")
            ops_records = []
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
            print(f"Seeded {len(ops_records)} rows into 'operation_log'.")

        # 2. Seed task_time_data from task_time_data.csv
        csv_task_path = PROJECT_ROOT / "data" / "task_time_data.csv"
        if not csv_task_path.exists():
            print(f"Warning: CSV file not found at {csv_task_path}")
        else:
            print(f"Loading task time data from: {csv_task_path}")
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
            print(f"Seeded {len(task_records)} rows into 'task_time_data'.")

        # 3. Seed starter tasks for dashboard if empty
        if db.query(Task).count() == 0:
            sample_tasks = [
                Task(
                    machine_id="EXC001",
                    operator_id="OP1001",
                    task_type="Earth Excavation",
                    status="Pending",
                    scheduled_time="2025-05-01T08:00:00",
                    estimated_time_min=60,
                    actual_time_min=None,
                ),
                Task(
                    machine_id="EXC002",
                    operator_id="OP1005",
                    task_type="Trenching",
                    status="In Progress",
                    scheduled_time="2025-05-01T10:00:00",
                    estimated_time_min=45,
                    actual_time_min=None,
                ),
                Task(
                    machine_id="EXC003",
                    operator_id="OP1003",
                    task_type="Material Loading",
                    status="Completed",
                    scheduled_time="2025-05-01T06:00:00",
                    estimated_time_min=30,
                    actual_time_min=28,
                ),
                Task(
                    machine_id="EXC004",
                    operator_id="OP1004",
                    task_type="Grading",
                    status="Pending",
                    scheduled_time="2025-05-01T13:00:00",
                    estimated_time_min=35,
                    actual_time_min=None,
                ),
            ]
            db.add_all(sample_tasks)
            db.commit()
            print(f"Seeded {len(sample_tasks)} demo rows into 'tasks'.")

        # 4. Seed starter alerts if empty
        if db.query(Alert).count() == 0:
            sample_alerts = [
                Alert(
                    machine_id="EXC001",
                    operator_id="OP1001",
                    type="Seatbelt",
                    severity="High",
                    message="Seatbelt unfastened during operation",
                    timestamp="2025-05-01T10:00:00",
                ),
                Alert(
                    machine_id="EXC001",
                    operator_id="OP1001",
                    type="Idling",
                    severity="Medium",
                    message="Idling time 55min exceeds threshold (45min)",
                    timestamp="2025-05-01T10:00:00",
                ),
                Alert(
                    machine_id="EXC002",
                    operator_id="OP1009",
                    type="Seatbelt",
                    severity="High",
                    message="Seatbelt unfastened during operation",
                    timestamp="2025-05-01T15:59:13",
                ),
            ]
            db.add_all(sample_alerts)
            db.commit()
            print(f"Seeded {len(sample_alerts)} demo rows into 'alerts'.")

        # 5. Seed starter training modules if empty
        if db.query(TrainingModule).count() == 0:
            sample_modules = [
                TrainingModule(
                    title="Safe Excavation Basics",
                    format="Video",
                    duration_min=12,
                    completed=0,
                ),
                TrainingModule(
                    title="Proximity Awareness & Site Safety",
                    format="Simulation",
                    duration_min=25,
                    completed=0,
                ),
                TrainingModule(
                    title="Reducing Idle Time & Fuel Conservation",
                    format="Instructor",
                    duration_min=45,
                    completed=1,
                ),
            ]
            db.add_all(sample_modules)
            db.commit()
            print(f"Seeded {len(sample_modules)} demo rows into 'training_modules'.")

        print("=" * 60)
        print("Database seed completed successfully!")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the CAT Operator Assistant SQLite database.")
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Append records without clearing existing data.",
    )
    args = parser.parse_args()
    seed_database(reset=not args.no_reset)
