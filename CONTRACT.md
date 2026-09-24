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

Both fields are optional. Omit a field to leave it unchanged; send `"actual_time_min": null` to clear a recorded time (e.g. when a completed task is reopened).

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

Each flagged log reading appears once, typed by its most severe violation (`Seatbelt` before `Idling`); `detail` lists every rule it broke. A reading the machine flagged without breaking a rule is typed `Anomaly`. Returns at most the 100 most recent readings.

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
{
  "predicted_minutes": 54, "source": "model", "p10": 48, "p90": 59,
  "model_version": "v2026.09.24",
  "drivers": [
    { "factor": "weather", "label": "Rainy weather", "compared_to": "sunny", "minutes": 8 },
    { "factor": "operator_skill", "label": "Intermediate operator", "compared_to": "expert", "minutes": 4 }
  ]
}
```
`model_version` is the active model tag from the registry (omitted when `source` isn't `"model"`).
`p10`–`p90` is the likely range, from the model's out-of-fold errors on past jobs (it held about 76% of held-out actual times). Each driver is the predicted change against a best-case baseline (Sunny, Expert, 1-year-old machine); drivers under 2 minutes are omitted. Both are `null` / `[]` when `source` isn't `"model"`.
`source` is `"model"` for the trained regressor, or `"historical"` / `"heuristic"` when the model is unavailable and the API falls back to past-job averages or rule-of-thumb multipliers.

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

### Coaching

**GET `/scores/operators?operator_id=OP1001`** (operator_id optional). Lowest score first.
```json
[
  {
    "operator_id": "OP1001", "score": 72, "band": "Watch", "readings": 69,
    "factors": [
      { "factor": "seatbelt", "penalty": 10, "detail": "Unbelted in 10% of logged readings" },
      { "factor": "idling", "penalty": 7, "detail": "Idled over 45 min in 13% of readings" },
      { "factor": "proximity", "penalty": 6, "detail": "2 proximity breaches in the last hour" },
      { "factor": "incidents", "penalty": 5, "detail": "1 incident reported this shift" }
    ],
    "recommended_modules": [
      { "id": 1, "title": "Safe Excavation Basics", "format": "Video", "duration_min": 12, "completed": 0, "reason": "1 incident reported this shift" }
    ]
  }
]
```
Score = 100 − penalties. Seatbelt: 1 pt per % of the operator's logged readings unbelted (max 40). Idling: 0.5 pt per % over 45 min (max 25). Proximity: 3 per breach in the last hour (max 15). Incidents this 8-hour shift: High 10 / Medium 5 / Low 2 (max 20). Bands: `Good` ≥ 80, `Watch` 60–79, `At risk` < 60. A factor assigns its training module at 15 / 10 / 6 / 5 points respectively. `completed` is the module's global flag (§2 simplification).

---

### Co-pilot

**POST `/copilot/chat`**: one conversational turn. The client keeps the text history and sends up to the last 20 turns, starting and ending with a `user` turn.
```json
{
  "operator_id": "OP1001", "machine_id": "EXC001",
  "messages": [{ "role": "user", "content": "Log it: I clipped the barrier by the east trench, nobody hurt" }]
}
```
Response:
```json
{
  "reply": "I've drafted a medium severity incident: ... Please confirm it on screen.",
  "source": "claude",
  "draft_incident": { "machine_id": "EXC001", "operator_id": "OP1001", "description": "...", "severity": "Medium" },
  "actions": [{ "tool": "draft_incident", "summary": "Medium incident drafted, awaiting confirmation" }]
}
```
Gemini answers with tools scoped to the request's operator and machine: tasks, task status, incident draft, time estimate, safety status, training. `source` is `"offline"` when no `GEMINI_API_KEY` is configured or Gemini is unreachable; a keyword parser then handles the same core commands. **Incidents are never saved by the co-pilot**: `draft_incident` is shown to the operator, and the client saves it with `POST /incidents` once they confirm. Task status changes made by the co-pilot are saved immediately and emit `task.updated`.

---

### Live (WebSocket)

Browsers must connect from an allowed origin (same rule as CORS); others are refused with 403. Clients only receive; nothing needs to be sent.

**WS `/ws/events`**: one message each time data changes through the API (or the simulator raises an alert). `data` has the same shape as the matching REST response.
```json
{ "type": "alert.created", "data": { "id": 212, "machine_id": "EXC003", "operator_id": "OP1003", "type": "Proximity", "severity": "High", "message": "Object within 2m of machine", "timestamp": "2026-09-23T22:37:22" } }
```
Types: `alert.created`, `incident.created`, `task.updated`, `training.updated`.

**WS `/ws/telemetry`**: one frame every `SIM_INTERVAL_S` (default 2 s), plus the latest frame immediately on connect. Cab readings are replayed from `operation_log` (advancing every 5 frames); ground workers are simulated. A worker entering 2 m raises a Proximity alert (with the machine's current operator) and emits `alert.created`.
```json
{
  "ts": "2026-09-23T22:30:14",
  "machines": [
    {
      "machine_id": "EXC001", "operator_id": "OP1001", "seatbelt_status": "Unfastened",
      "idling_time_min": 55, "fuel_used_l": 3.8, "load_cycles": 2, "reading_ts": "2025-05-01T10:00:00",
      "nearest_m": 7.7,
      "workers": [{ "id": "EXC001-W1", "distance_m": 7.71, "bearing_deg": 92 }]
    }
  ]
}
```
`bearing_deg` is clockwise from the machine's front.

---

## 4. Build Order Reminder

- Frontend can build against these exact JSON shapes as **mock data** before the backend is live — don't wait.
- Backend should stand up `/tasks/today` and `/safety/alerts` first (dashboard + safety are the highest demo-impact, lowest-effort features).
- ML should get `/predict/task-time` logic working as a standalone function first, then either expose it directly as a FastAPI route or hand it to Person 2 to wire in.

## 5. If You Need to Change a Shape

Ping the other two before changing anything in this file. Update it here, then
everyone re-pastes the updated section into their AI tool's context before their
next prompt — don't let sessions drift on stale shapes.

## 6. Changelog

### 2026-09-24: voice co-pilot (Gemini)

- Added **POST `/copilot/chat`** (see §3 "Co-pilot").
- Settings: `GEMINI_API_KEY`, `COPILOT_MODEL` (default `gemini-2.5-flash`), `COPILOT_TIMEOUT_S`. Dependency: `google-genai`.

### 2026-09-23: estimate ranges

- `POST /predict/task-time` adds `p10`, `p90` and `drivers` (see §3). Existing fields are unchanged.

### 2026-09-23: coaching

- Added **GET `/scores/operators`** (see §3 "Coaching").
- New training module "Seatbelt & Safe Cab Entry" (Video, 4 min). The API inserts it at startup if missing, so existing databases get it without a reseed.

### 2026-09-23: live updates

- Added **WS `/ws/events`** and **WS `/ws/telemetry`** (see §3 "Live"). No REST shape changed.
- Mutating endpoints now also publish an event after saving.
- New settings: `SIM_ENABLED`, `SIM_INTERVAL_S`, `SIM_SEED` (see `backend/.env.example`).

### 2026-09-23: backend hardening (PLAN.md Phase 2)

Existing request and response shapes are unchanged; clients that follow this contract keep working.

- **Requests are validated.** Enum fields must use the exact §1 strings (case-sensitive). `machine_id` / `operator_id` must match `[A-Za-z0-9_-]{1,32}`. Minutes are 0–1440, `distance_m` is 0–1000, `machine_age_yrs` is 0–60, an incident `description` is 5–2000 characters and `completed` is `0` or `1`. Unknown fields are rejected. Violations return **422** with FastAPI's standard body: `{"detail": [{"loc": ["body", "field"], "msg": "...", "type": "..."}]}`.
- **Timestamps** must be ISO 8601. They are stored as naive local time, `YYYY-MM-DDTHH:MM:SS`: fractions are dropped and UTC/offset times are converted to server-local time.
- **`POST /predict/task-time`** adds `source` (see §3).
- **`PATCH /tasks/{id}`** accepts `"actual_time_min": null` to clear a recorded time.
- **`GET /anomalies`** labels a reading that breaks both rules as `Seatbelt` (previously `Idling`). A flag-only reading is typed `Anomaly` (previously `Safety`, which wasn't a §1 `AlertType`).
- **Errors:** every response carries an `X-Request-ID` header (a valid incoming one is echoed). Unexpected failures return **500** `{"detail": "Internal server error", "request_id": "..."}`.
- **CORS** allows only configured origins: any localhost port by default, plus `CORS_ORIGINS` (see `backend/.env.example`). It no longer sends `Access-Control-Allow-Credentials`.
