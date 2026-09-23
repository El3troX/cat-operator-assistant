# Project Plan — Smart Operator Assistant, Production Readiness

Source docs: [`IDEA.md`](./IDEA.md) (original brief) and [`CONTRACT.md`](./CONTRACT.md) (locked API/DB contract).

## Current state (audited 2026-09-23)

The backend implements **all 11 endpoints** in `CONTRACT.md` §3 against a schema that matches §2 field-for-field, and the ML task-time predictor (`ml/train.py` → `ml/predict.py`, RandomForest in an sklearn `Pipeline`) is wired end-to-end with a heuristic fallback if the model fails to load. That's the good news — this was a solid hackathon build.

What's missing, mapped to `IDEA.md`'s five "Expected Outcomes":

| Outcome | Backend | Frontend | End-to-end? |
|---|---|---|---|
| Daily task dashboard | done | done | **Working** |
| Task time estimation | done | done | **Working** |
| Safety — seatbelt compliance | done | partial (alerts list only) | Partial |
| Safety — proximity hazards | done | **none** | Missing |
| Safety — incident logging | done | **none** | Missing |
| Operator training hub | done | **none** | Missing |
| Anomaly / unusual-behavior detection | done | **none** | Missing |

Plus, for anything beyond a hackathon demo: no auth anywhere, no tests in CI, no Docker, no env/secrets config, CORS is misconfigured (`allow_origins=["*"]` + `allow_credentials=True`), request bodies accept any string instead of enforcing the CONTRACT.md enums, no logging (only `print()`), no model versioning, and the root README is a one-line stub.

This plan is ordered so each phase ships something demoable, and later phases don't block on earlier ones being "perfect" — just done enough to build on.

---

## Phase 1 — Close the frontend gap (highest impact, no backend changes)

The fastest way to make four "done" backend features actually visible.

- [x] Incident logging: form to POST `/incidents` and a live list for GET `/incidents?machine_id=` (`features/incidents/IncidentForm.jsx`, `IncidentList.jsx`)
- [x] Proximity: an interactive radar that POSTs `/safety/proximity` on release and shows `triggered`/`severity`/`message` (`features/safety/ProximityRadar.jsx`)
- [x] Training hub: GET `/training/modules` with mark-complete and undo via PATCH (`features/training/TrainingHub.jsx`)
- [x] Anomalies: GET `/anomalies?machine_id=` with type and machine filters, plus operator/machine hotspots (`features/anomalies/AnomalyPanel.jsx`)
- [x] Live `POST /safety/check` with seatbelt and idling inputs (`features/safety/SafetyCheck.jsx`); the alert feed polls every 5 s (`AlertFeed.jsx`)
- [x] `react-router` with two modes: Command Center `/command/*` and Cab Mode `/cab/*` (`app/router.jsx`, `layouts/`)
- [x] Typed-shape API client for all 11 contract endpoints (`lib/api.js`) with TanStack Query hooks (`lib/queries.js`)

**Exit criteria:** every endpoint in CONTRACT.md §3 has a corresponding UI action; a demo walkthrough can touch all 5 IDEA.md outcome areas without opening a REST client. **Met 2026-09-23:** verified in the browser against the live backend at desktop, tablet and 375 px widths.

---

## Phase 2 — Backend correctness & hardening

- [ ] Enforce the CONTRACT.md enums server-side: switch `schemas.py` request models from `str` to `Literal[...]`/`Enum` for `task_type`, `weather`, `operator_skill`, `status`, `severity`, `type` — reject invalid values with 422 instead of silently accepting them
- [ ] Fix CORS: replace `allow_origins=["*"]` + `allow_credentials=True` with an explicit allow-list driven by env config (see below) — the current combination is invalid per the CORS spec and a real misconfiguration
- [ ] Add a global exception handler (FastAPI `@app.exception_handler`) returning consistent JSON error shapes instead of raw 500s
- [ ] Remove the bare `except Exception: pass` around the ML call in `/predict/task-time`; log the failure and surface a `"source": "fallback"` field in the response so the frontend/demo can tell when it's degraded to the heuristic
- [ ] Introduce `pydantic-settings` for config (DB path, CORS origins, log level) backed by a `.env` file; commit `.env.example`
- [ ] Replace `print()` calls in `seed.py`/`train.py` with the `logging` module; add basic request logging middleware in `main.py`
- [ ] Split `main.py` into routers (`routers/tasks.py`, `routers/safety.py`, `routers/incidents.py`, `routers/anomalies.py`, `routers/predict.py`, `routers/training.py`) — one file per CONTRACT.md section, mounted via `APIRouter`

**Exit criteria:** invalid input is rejected with clear errors, no config is hardcoded, CORS only allows the known frontend origin(s), and logs are structured enough to debug a demo failure after the fact.

---

## Phase 3 — Automated testing & CI

- [ ] Convert `backend/test_setup.py` and `test_live_server.py` into real `pytest` tests under `backend/tests/`, using `TestClient`/`pytest-asyncio` and a throwaway SQLite file (or in-memory DB) per test run — not the dev DB
- [ ] Add unit tests for the safety rule engine (`/safety/check`, `/safety/proximity` thresholds) and the anomaly thresholds — these are pure logic and cheap to cover well
- [ ] Add a smoke test for `ml/predict.py` asserting output stays within a sane bound for a fixed input, so a bad retrain is caught
- [ ] Add `frontend` component tests with Vitest + React Testing Library for the four new Phase 1 components plus the existing three
- [ ] Add `.github/workflows/ci.yml`: on PR — install backend deps, run `pytest`; install frontend deps, run `npm run lint`, `npm run build`, `npm test`
- [ ] Wire `oxlint` (already configured) and add `ruff`/`black` for the Python side, both enforced in CI

**Exit criteria:** a PR that breaks any endpoint, safety rule, or build fails CI before merge — no more manual "run the script and eyeball it."

---

## Phase 4 — Auth & access control

Currently anyone who can reach the API can read/write any machine's data — fine for a hackathon demo, not for anything real.

- [ ] Decide on an auth model appropriate to the actual deployment (recommend: simple JWT-based operator login, since this is a single-operator-facing app, not a public API) — confirm scope with stakeholders before building
- [ ] Add `operators` table + login endpoint; issue short-lived JWTs
- [ ] Protect all mutating endpoints (`PATCH /tasks/{id}`, `POST /incidents`, `PATCH /training/modules/{id}`, `POST /safety/*`) behind auth; scope reads to the operator's own `operator_id` where it makes sense (e.g. `/tasks/today`) vs. supervisor-level views (e.g. all machines)
- [ ] Add a minimal login screen to the frontend; store token in memory (not `localStorage`) and attach via `api.js`
- [ ] Add rate limiting on the auth endpoint (e.g. `slowapi`) to blunt brute-force attempts

**Exit criteria:** the API is no longer fully anonymous/open; a stolen link can't read or mutate another operator's data.

---

## Phase 5 — ML pipeline maturity

- [ ] Version `model.pkl` outputs (e.g. `model-<date>-<git-sha>.pkl` or MLflow-style registry) instead of overwriting in place on every `train.py` run
- [ ] Log training metrics (MAE/R², row count, feature set) to a file or lightweight tracker on every training run, not just stdout
- [ ] Expand training data: 300 rows is thin for a RandomForest with one-hot categoricals — either source more historical task data or document the model's known confidence limits in `ml/README.md`
- [ ] Add a `/predict/task-time` response field indicating model version/staleness so the frontend can flag predictions from an old model
- [ ] Add a scheduled or manually-triggered retrain path (script or CI job) once more data accumulates

**Exit criteria:** a model regression or staleness is detectable without manually diffing `model.pkl` timestamps.

---

## Phase 6 — Containerization & deployment

- [ ] `backend/Dockerfile` (slim Python base, non-root user, `uvicorn` entrypoint)
- [ ] `frontend/Dockerfile` (multi-stage: Vite build → static serve via nginx or similar)
- [ ] `docker-compose.yml` at repo root wiring backend + frontend (+ a named volume for the SQLite file, or plan the Phase 7 Postgres migration first if that's happening before launch)
- [ ] Root `README.md`: replace the one-line stub with real setup/run instructions (local dev, Docker, env vars, seeding)
- [ ] `ml/README.md`: how to retrain, what data it expects, current metrics
- [ ] Choose and document a deploy target (e.g. Fly.io/Render/Railway for backend, Vercel/Netlify for frontend, or a single VM via compose) and add the matching config file once decided

**Exit criteria:** `docker compose up` gives a working full-stack instance from a clean checkout; README lets a new contributor run it in under 10 minutes.

---

## Phase 7 — Data layer & scale readiness

- [ ] Migrate from SQLite to Postgres (or confirm SQLite is acceptable for expected load) — SQLite's single-writer model will bottleneck under concurrent operators/machines
- [ ] Add Alembic migrations instead of `Base.metadata.create_all` so schema changes are tracked and reversible
- [ ] Add DB indices on the columns actually filtered on (`machine_id`, `operator_id`, `timestamp`) across `operation_log`, `alerts`, `incidents`
- [ ] Revisit `seed.py`: separate "demo/sample data" seeding from "reference data" (training modules) so production deploys don't ship fake tasks

**Exit criteria:** schema changes go through migrations, not manual `create_all`; queries against growing tables stay fast.

---

## Phase 8 — Observability & production polish

- [ ] Structured logging (JSON) + request IDs, shippable to a log aggregator
- [ ] `/health` endpoint (exists) extended with DB connectivity + model-load checks for real readiness/liveness probes
- [ ] Basic error tracking (e.g. Sentry) on both frontend and backend
- [ ] Accessibility pass on the frontend (keyboard nav, ARIA labels on alert severities/icons, color-contrast check on severity colors — safety alerts must not rely on color alone)
- [ ] Load-test the dashboard/alerts endpoints at expected fleet size before launch
- [ ] Final end-to-end QA pass against every row of the Phase 1 exit criteria table

**Exit criteria:** the team can see what's happening in production, gets alerted on failures, and the app is usable by operators with accessibility needs.

---

## Suggested sequencing

Phases 1–3 are independent of each other and could run in parallel with separate owners (frontend / backend hardening / test infra). Phase 4 (auth) should land before any real deployment (Phase 6) since an open API in production is a hard blocker, not a nice-to-have. Phases 5, 7, and 8 can trail after the first production deploy as iterative hardening.
