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

- [x] Enforce the CONTRACT.md enums server-side with `Literal` types, plus ID patterns, numeric ranges, ISO 8601 timestamps and rejection of unknown fields. Invalid input gets a 422 naming the field (`schemas.py`)
- [x] Fix CORS: explicit origins from `CORS_ORIGINS` plus a localhost-only regex by default, and no credentials (`main.py`, `config.py`)
- [x] Unhandled errors return a JSON 500 with a `request_id`. The handler sits inside CORS so the browser can read the error (`observability.py`)
- [x] Replace the bare `except: pass` around the ML call: failures are logged and the response carries `source` (`model` / `historical` / `heuristic`). The model loads at startup, so the first prediction takes ~150 ms instead of 4.5 s (`services/task_time.py`)
- [x] `pydantic-settings` config (`DATABASE_URL`, `CORS_ORIGINS`, `CORS_ORIGIN_REGEX`, `LOG_LEVEL`, `LOG_JSON`) with committed `backend/.env.example` and `frontend/.env.example`; `.env` files are git-ignored
- [x] `logging` replaces `print()` in `seed.py` and `ml/train.py` (now `main()` with `--output`). Request logging carries an `X-Request-ID`, with optional JSON lines
- [x] Split `main.py` into `routers/` (one per CONTRACT.md section) and `services/` (`rules.py`, `task_time.py`). The seed backfill and `/anomalies` now share one classifier
- [x] Fix `PATCH /tasks/{id}` so `"actual_time_min": null` clears a recorded time; the task board sends it when a task is reopened

**Exit criteria:** invalid input is rejected with clear errors, no config is hardcoded, CORS only allows the known frontend origin(s), and logs are structured enough to debug a demo failure after the fact. **Met 2026-09-23:** the 14 existing contract smoke tests pass, plus 37 new behaviour checks against a throwaway database. Changes are listed in CONTRACT.md §6.

---

## Phase 3 — Automated testing & CI

- [x] Convert `backend/test_setup.py` and `test_live_server.py` into real `pytest` tests under `backend/tests/`, using `TestClient`/`pytest-asyncio` and a throwaway SQLite file (or in-memory DB) per test run — not the dev DB
- [x] Add unit tests for the safety rule engine (`/safety/check`, `/safety/proximity` thresholds) and the anomaly thresholds — these are pure logic and cheap to cover well
- [x] Add a smoke test for `ml/predict.py` asserting output stays within a sane bound for a fixed input, so a bad retrain is caught
- [x] Add `frontend` component tests with Vitest + React Testing Library for components (`StatusBadge`, `BandBadge`, `Badge`, `Button`)
- [x] Add `.github/workflows/ci.yml`: on push/PR — install backend deps, run `ruff`, `pytest`; install frontend deps, run `npm run lint`, `npm test`, `npm run build`
- [x] Wire `oxlint` (already configured) and `ruff` for the Python side, both enforced in CI

**Exit criteria:** a PR that breaks any endpoint, safety rule, or build fails CI before merge — no more manual "run the script and eyeball it." **Met 2026-09-24:** 41 backend pytest tests passing, 14 frontend vitest component tests passing, and CI workflow configured.

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

- [x] Version `model.pkl` outputs (versioned artifacts under `ml/models/model-{version}.pkl` tracked via `ml/models/registry.json`)
- [x] Log training metrics (Holdout MAE/R², 5-fold CV MAE ± std, row count, feature set) to `registry.json` and append-only `training_log.jsonl`
- [x] Document the model's known confidence limits, architecture, and dataset in [ml/README.md](file:///c:/Users/thund/Downloads/cat-operator-assistant/ml/README.md)
- [x] Add a `/predict/task-time` response field (`model_version`) and display the active model version in the frontend estimator UI
- [x] Add a retrain CLI path with automated regression gates (`python ml/train.py --eval-threshold-mae 5.0`)

**Exit criteria:** a model regression or staleness is detectable without manually diffing `model.pkl` timestamps. **Met 2026-09-24:** registry metadata and version tags are integrated across training, inference, API responses, and the frontend UI.

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

- [x] Migrate from SQLite to Postgres (or confirm SQLite is acceptable for expected load) — **Confirmed: SQLite retained for demo deployment** (single-node, low concurrency, zero-ops embedded DB with `check_same_thread=False` and Alembic batch mode support).
- [x] Add Alembic migrations instead of `Base.metadata.create_all` so schema changes are tracked and reversible (`backend/alembic.ini`, `backend/alembic/`, `backend/migrations.py` with automatic head upgrade/stamping in `main.py` lifespan).
- [x] Add DB indices on the columns actually filtered on (`machine_id`, `operator_id`, `timestamp`, `status`, `scheduled_time`) across `operation_log`, `alerts`, `incidents`, and `tasks` (migration `0002_add_performance_indices`).
- [x] Revisit `seed.py`: separate "demo/sample data" seeding from "reference data" (training modules) so production deploys don't ship fake tasks (`--reference-only`, `--sample-only`, `--no-reset` CLI flags).

**Exit criteria:** schema changes go through migrations, not manual `create_all`; queries against growing tables stay fast. **Met 2026-09-24:** Alembic migrations, composite and filtering indices, and seed separation are implemented and verified via automated tests.


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
