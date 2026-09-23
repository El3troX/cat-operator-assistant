# CONTRACT.md — Smart Operator Assistant for CAT Machinery

This is the locked contract for the hackathon build. All three of us paste this
into our AI tool's first prompt and build against these exact shapes. If a shape
needs to change mid-build, call it out to the other two before changing it.

Stack: React + Vite + Tailwind (frontend) · FastAPI + SQLite (backend) · pandas + scikit-learn (ml)

---

## 1. Shared Enums / Constants

Use these exact strings everywhere — frontend, backend, and ML — so nothing has to
be re-mapped at integration time.

```
SeatbeltStatus   = "Fastened" | "Unfastened"
TaskType         = "Earth Excavation" | "Trenching" | "Material Loading" | "Grading" | "Demolition"
Weather          = "Sunny" | "Rainy" | "Cloudy" | "Windy"
OperatorSkill    = "Beginner" | "Intermediate" | "Expert"
TaskStatus       = "Pending" | "In Progress" | "Completed"
AlertType        = "Seatbelt" | "Proximity" | "Idling" | "Anomaly"
AlertSeverity    = "Low" | "Medium" | "High"
```

---

## 2. Database Schema (SQLite)

```sql
-- Machine operation log (from sample data)
CREATE TABLE operation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,          -- ISO 8601, e.g. "2025-05-01T08:00:00"
    machine_id TEXT NOT NULL,         -- e.g. "EXC001"
    operator_id TEXT NOT NULL,        -- e.g. "OP1001"
    engine_hours REAL,
    fuel_used_l REAL,
    load_cycles INTEGER,
    idling_time_min INTEGER,
    seatbelt_status TEXT,             -- SeatbeltStatus
    safety_alert_triggered INTEGER    -- 0 or 1
);

-- Task time reference data (from sample data, used to train the estimator)
CREATE TABLE task_time_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    task_type TEXT,                   -- TaskType
    weather TEXT,                     -- Weather
    operator_skill TEXT,              -- OperatorSkill
    machine_age_yrs INTEGER,
    estimated_time_min INTEGER,
    actual_time_min INTEGER
);

-- Daily tasks (dashboard-facing)
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id TEXT NOT NULL,
    operator_id TEXT NOT NULL,
    task_type TEXT NOT NULL,          -- TaskType
    status TEXT NOT NULL DEFAULT 'Pending',  -- TaskStatus
    scheduled_time TEXT,              -- ISO 8601
    estimated_time_min INTEGER,       -- from predictor
    actual_time_min INTEGER           -- filled in once completed
);

-- Incident log (operator/manual entries)
CREATE TABLE incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id TEXT NOT NULL,
    operator_id TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT,                    -- AlertSeverity
    timestamp TEXT NOT NULL           -- ISO 8601
);

-- Safety/anomaly alerts (system-generated)
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id TEXT NOT NULL,
    operator_id TEXT NOT NULL,
    type TEXT NOT NULL,               -- AlertType
    severity TEXT,                    -- AlertSeverity
    message TEXT,
    timestamp TEXT NOT NULL
);

-- Training modules (static-ish, seeded)
CREATE TABLE training_modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    format TEXT,                      -- "Video" | "Simulation" | "Instructor"
    duration_min INTEGER,
    completed INTEGER DEFAULT 0       -- per-operator completion, simplified to 0/1 for demo
);
```

---

## 3. API Endpoints

Base URL: `http://localhost:8000`

### Dashboard

**GET `/tasks/today`**
Response:
```json
[
  {
    "id": 1,
    "machine_id": "EXC001",
    "operator_id": "OP1001",
    "task_type": "Earth Excavation",
    "status": "Pending",
    "scheduled_time": "2025-05-01T08:00:00",
    "estimated_time_min": 60,
    "actual_time_min": null
  }
]
```

**PATCH `/tasks/{id}`** — update status/actual time
Request:
```json
{ "status": "Completed", "actual_time_min": 58 }
```
Response: updated task object (same shape as above)

---

### Safety

**GET `/safety/alerts?machine_id=EXC001`** (machine_id optional — omit for all)
Response:
```json
[
  {
    "id": 1,
    "machine_id": "EXC001",
    "operator_id": "OP1001",
    "type": "Seatbelt",
    "severity": "High",
    "message": "Seatbelt unfastened during operation",
    "timestamp": "2025-05-01T10:00:00"
  }
]
```

**POST `/safety/check`** — run rule engine against a new/latest log entry, returns any alerts it generated
Request:
```json
{
  "machine_id": "EXC001",
  "operator_id": "OP1001",
  "seatbelt_status": "Unfastened",
  "idling_time_min": 55,
  "timestamp": "2025-05-01T10:00:00"
}
```
Response: `[]` or array of alert objects (same shape as GET above)

**POST `/safety/proximity`** — simulated proximity feed pushes a reading, returns alert if triggered
Request:
```json
{ "machine_id": "EXC001", "distance_m": 1.2, "timestamp": "2025-05-01T10:00:00" }
```
Response:
```json
{ "triggered": true, "severity": "High", "message": "Object within 2m of machine" }
```

---

### Incidents

**POST `/incidents`**
Request:
```json
{
  "machine_id": "EXC001",
  "operator_id": "OP1001",
  "description": "Minor collision with barrier",
  "severity": "Medium",
  "timestamp": "2025-05-01T11:00:00"
}
```
Response: created incident object with `id`

**GET `/incidents?machine_id=EXC001`** (machine_id optional)
Response: array of incident objects

---

### Anomaly Detection

**GET `/anomalies?machine_id=EXC001`**
Response:
```json
[
  {
    "machine_id": "EXC001",
    "operator_id": "OP1001",
    "type": "Idling",
    "detail": "Idling time 60min exceeds threshold (45min)",
    "timestamp": "2025-05-02T09:00:00"
  }
]
```
(Threshold-based for the hackathon — no real ML needed here unless time allows.)

---

### Task Time Prediction

**POST `/predict/task-time`**
Request:
```json
{
  "task_type": "Trenching",
  "weather": "Rainy",
  "operator_skill": "Intermediate",
  "machine_age_yrs": 4
}
```
Response:
```json
{ "predicted_minutes": 51 }
```

---

### Training Hub

**GET `/training/modules`**
Response:
```json
[
  { "id": 1, "title": "Safe Excavation Basics", "format": "Video", "duration_min": 12, "completed": 0 }
]
```

**PATCH `/training/modules/{id}`**
Request: `{ "completed": 1 }`
Response: updated module object

---

## 4. Build Order Reminder

- Frontend can build against these exact JSON shapes as **mock data** before the backend is live — don't wait.
- Backend should stand up `/tasks/today` and `/safety/alerts` first (dashboard + safety are the highest demo-impact, lowest-effort features).
- ML should get `/predict/task-time` logic working as a standalone function first, then either expose it directly as a FastAPI route or hand it to Person 2 to wire in.

## 5. If You Need to Change a Shape

Ping the other two before changing anything in this file. Update it here, then
everyone re-pastes the updated section into their AI tool's context before their
next prompt — don't let sessions drift on stale shapes.
