# Hackathon Strategy — from "meets the brief" to "wins the room"

Companion to [`IDEA.md`](./IDEA.md), [`CONTRACT.md`](./CONTRACT.md) and [`PLAN.md`](./PLAN.md).
`PLAN.md` covers hardening after the hackathon. This doc covers what to build and demo **for the judges**.

---

## 0. Our unfair advantage: numbers from the fleet's own data

Computed on `data/` today. These go on the first slide.

| Finding | Number | Source |
|---|---|---|
| Seatbelt **unfastened** in log readings | **17.8%** (1 in 6) | `machine_operations_log.csv`, 595 rows |
| Readings where the existing system **raised an alert** | **0.34%** (2 readings) | same |
| Readings our rule engine flags (unbelted or idling > 45 min) | **201 (33.8%)** | same, via `backend/seed.py` backfill |
| Readings with idling above the 45-min threshold | 127 | same |
| Total idle time, 5 machines, 1 month | **~306 hours** | same |
| Human task estimates that **overran** | **87%**, off by 11.7 min on average | `task_time_data.csv`, 300 rows |
| Our ML model's error (5-fold cross-validated) | **3.5 min MAE, 70% better than humans** | RandomForest, same features |

The story writes itself: **seatbelt violations appear in 1 of every 6 readings, but the current tooling flagged only 1 in 300 readings. We close that gap, and we coach operators so the violations stop.**

> Caveat for Q&A: the dataset is synthetic/sample data. Say "on the provided dataset". Don't claim real-world results.

---

## 1. The WOW factor: three features that build on what already works

The backend already implements all 11 contract endpoints. Each feature below adds a layer on top of them. None of them requires a rewrite.

### A. Sentinel: a live safety twin with real-time streaming

**The pain point:** safety data today is a log you read *after* the incident.

- **Real-time telemetry stream.** A backend simulator replays `machine_operations_log.csv` at about 60× speed and adds synthetic proximity readings. It pushes over a **WebSocket** (`/ws/telemetry`), so the UI updates live and nobody refreshes the page.
- **Proximity radar.** A top-down view of the machine with concentric danger rings (2 m, 5 m, 10 m). Workers appear as moving blips. When a blip crosses a ring, the ring pulses red, the tablet vibrates (`navigator.vibrate`), and a chime plays.
  - *Stretch goal:* a 3D low-poly excavator built with React Three Fiber, with the same rings rendered on the ground plane.
- **Anomaly detection with ML.** Upgrade `/anomalies` from fixed thresholds to a per-machine **IsolationForest** over these features:
  - fuel per load cycle
  - idle ratio
  - seatbelt state
  - time of day

  Each anomaly carries a **reason**, for example: *"Fuel per cycle is 2.8× this machine's norm, while load cycles are low."* Judges reward ML they can understand.

### B. Hands-free voice Co-Pilot

**The pain point:** operators wear gloves in a loud, vibrating cab, so they can't fill in forms. This is why incidents go unreported.

- A big push-to-talk button. Speech-to-text runs in the browser (Web Speech API).
- **Claude with tool use** calls our existing endpoints as tools:
  - `get_today_tasks`, `update_task`
  - `log_incident`, `get_alerts`
  - `predict_task_time`, `get_training_modules`
- Example requests and what happens:
  - *"What's next?"* → The Co-Pilot reads out the next task and its ML time estimate.
  - *"I clipped the barrier by the east trench, nobody hurt."* → It builds a **structured incident** (description, severity=Medium, machine and operator from the session). It reads the incident back and waits for the operator to say "confirm" before saving.
  - *"How long will this trench take in this rain?"* → It calls the predictor and answers aloud.
- **Model choice:** `claude-haiku-4-5` for the fast conversational loop. `claude-sonnet-5` generates the end-of-shift report.
- **Security:** the API key stays on the backend (`/copilot/chat`) and never reaches the browser.
- **Offline fallback:** a keyword intent parser handles the five core commands if the network or API fails. The demo can't die on stage.

### C. Closed-loop coaching: detect → alert → coach → improve

**The pain point:** alerts without follow-up just become noise.

- **Shift Safety Score** (0–100) per operator. It combines seatbelt compliance, proximity breaches, idle ratio and incidents. It gets a hero spot in the UI with an animated gauge.
- **Automatic training assignment.** Each behaviour pattern maps to a training module. For example:
  - repeated unfastened seatbelt → "Seatbelt & Egress, 4-min video"
  - chronic idling → "Fuel-Smart Operation"
  - proximity breaches → "Blind-Spot Awareness simulation"

  The Training Hub is no longer a static list. **It's personalized from the operator's own behaviour.**
- **Idle cost counter.** Idle hours × an idle burn rate show fuel, CO₂ and money wasted, per operator and per fleet.
  - Calibrate the burn rate by regressing `Fuel Used` on idle minutes and load cycles in our own log. That way the number is *learned from the fleet* rather than assumed.
- **Estimator with confidence.** `/predict/task-time` also returns a P10–P90 range, taken from the spread of the random forest's trees. It also returns its top drivers, for example: *"Rain +9 min · Beginner +12 min."*

### Bonus (stretch): offline-first PWA

Job sites have dead zones. Add a `vite-plugin-pwa` service worker and an IndexedDB outbox for incidents and task updates. In the demo, turn Wi-Fi off, log an incident, turn Wi-Fi on, and watch it sync. Build this only if tiers 1 and 2 are done.

---

## 2. Premium UI/UX on a hackathon budget

### Two personas, two modes

| | **Cab Mode** (operator, tablet) | **Command Center** (supervisor, laptop) |
|---|---|---|
| Layout | One task at a time, huge touch targets (≥ 64 px, glove-friendly) | Dense grid: fleet table, live alert feed, per-operator scores |
| Theme | Dark, high contrast, readable in sunlight | Same tokens, denser type scale |
| Hero | Next task + Co-Pilot button + Safety Score | Live radar + streaming anomaly feed + idle cost counter |

**Demo tip:** run both modes side by side on two screens. An action in the cab shows up live in the command center. This is the core of the mic-drop moment (see section 4).

### Design system

- **shadcn/ui** (Radix primitives with Tailwind v4, which is already installed). The components are accessible and we own the code.
- **Palette:** near-black surfaces (`#0B0D10`) and one industrial safety-yellow accent. Severity colors are green, amber and red, **always paired with an icon and label**, because safety states must never depend on color alone.
  - Don't use Caterpillar logos or trademarks. An industrial yellow palette is fine.
- **Type:** Inter or Geist for UI, with tabular numerals for every metric.
- **Icons:** `lucide-react`.

### Micro-interactions that make it feel alive

- **`motion`** (formerly Framer Motion):
  - alerts slide in and stack
  - layout animations when tasks change status
  - shared-element transitions from a task card to its detail view
- **Number tickers** for the Safety Score, idle cost and ETA, which roll to their new value.
- **Pulse rings** on the radar and the live-data indicator.
- **`sonner`** toasts for confirmations. A high-severity alert gets a full-width banner plus haptic feedback plus a chime.
- **Skeleton loaders**, never spinners. Optimistic updates through TanStack Query, so task status flips instantly.
- **`cmdk` command palette** (Ctrl+K) in the Command Center. Power-user polish that judges notice.
- **Co-Pilot voice orb:** an animated waveform while it listens, and streamed text plus speech synthesis while it answers.

---

## 3. Architecture and scaffolding

### Stack decision: evolve the current stack, don't replace it

The current stack works and has all contract endpoints. A move to Next.js or Supabase would burn hours and gain nothing on stage.

| Layer | Keep | Add |
|---|---|---|
| Frontend | React 19, Vite 8, Tailwind 4 | `react-router`, `@tanstack/react-query`, `zustand` (live telemetry store), shadcn/ui, `motion`, `lucide-react`, `sonner`, `recharts`, `cmdk`. *Stretch:* `@react-three/fiber` + `drei`, `vite-plugin-pwa` |
| Backend | FastAPI, SQLAlchemy, SQLite | WebSockets (native in FastAPI), `anthropic` SDK, `pydantic-settings`, split into routers |
| ML | scikit-learn, pandas, joblib | `IsolationForest` anomaly model, quantile range from the tree ensemble, a fuel/idle regression |
| Ops | none today | `docker-compose.yml`, `.env.example`, a GitHub Actions workflow that runs the smoke tests |

**Keep SQLite for the hackathon.** Moving to Postgres is in `PLAN.md` Phase 7, after the event.

### Target folder tree

```
cat-operator-assistant/
├── docker-compose.yml
├── .env.example                  # ANTHROPIC_API_KEY, CORS_ORIGINS, SIM_SPEED
├── backend/
│   ├── app/
│   │   ├── main.py               # app factory, CORS from settings, router mounts
│   │   ├── config.py             # pydantic-settings
│   │   ├── db.py  models.py  schemas.py   # schemas use Literal enums from CONTRACT §1
│   │   ├── routers/
│   │   │   ├── tasks.py  safety.py  incidents.py  anomalies.py
│   │   │   ├── predict.py  training.py
│   │   │   ├── copilot.py        # POST /copilot/chat (Claude tool-use loop)
│   │   │   ├── scores.py         # GET /scores/operators, /scores/fleet-cost
│   │   │   └── ws.py             # WS /ws/telemetry, WS /ws/events
│   │   ├── services/
│   │   │   ├── simulator.py      # CSV replay + synthetic proximity blips
│   │   │   ├── rules.py          # seatbelt / idling / proximity rule engine
│   │   │   ├── scoring.py        # Safety Score + training recommendation map
│   │   │   ├── event_bus.py      # in-process pub/sub → WebSocket broadcast
│   │   │   └── copilot_tools.py  # tool schemas → call the services above
│   │   └── seed.py
│   └── tests/                    # pytest, ported from test_setup.py
├── ml/
│   ├── train_task_time.py        # adds P10/P90 + feature drivers
│   ├── train_anomaly.py          # IsolationForest per machine
│   ├── train_fuel.py             # idle burn-rate regression
│   ├── predict.py
│   └── models/                   # versioned *.pkl
├── frontend/src/
│   ├── app/                      # router, providers (QueryClient, theme, toaster)
│   ├── routes/
│   │   ├── cab/                  # Cab Mode (operator)
│   │   └── command/              # Command Center (supervisor)
│   ├── features/
│   │   ├── tasks/  safety/  incidents/  training/  anomalies/
│   │   ├── radar/                # proximity radar (SVG + motion; R3F stretch)
│   │   ├── copilot/              # voice orb, STT/TTS hooks, chat stream
│   │   └── scores/               # Safety Score gauge, idle cost counter
│   ├── components/ui/            # shadcn components
│   ├── lib/  api.ts  ws.ts       # typed client + WebSocket hook
│   └── stores/telemetry.ts       # zustand live store
└── data/
```

### Contract additions

Add these endpoints to `CONTRACT.md` before building. All existing shapes stay unchanged; only new optional fields are added.

- `WS /ws/telemetry` streams `{machine_id, operator_id, ts, seatbelt, idle_min, fuel_l, load_cycles, proximity: [{id, x, y, distance_m}]}`.
- `WS /ws/events` streams alerts, incidents and score changes in the same shapes the REST endpoints return.
- `POST /copilot/chat` takes `{messages, operator_id, machine_id}` and returns a streamed reply plus a list of executed tool calls.
- `GET /scores/operators` returns `[{operator_id, score, breakdown, recommended_module_ids}]`.
- `GET /scores/fleet-cost` returns `{idle_hours, fuel_l, co2_kg, cost}`.
- `POST /predict/task-time` gains **new optional fields** `p10`, `p90`, `drivers[]` and `source`. The existing `predicted_minutes` is unchanged.

---

## 4. The winning pitch: 3 minutes

| Time | Beat | On screen |
|---|---|---|
| 0:00–0:25 | **Hook with the fleet's own data.** "In this fleet's own logs, seatbelts were off in **1 of every 6** readings. The current tooling flagged **1 in 300**." | Big numbers only, on black |
| 0:25–0:50 | **Meet the operator.** Cab Mode on the tablet: today's tasks, and "Next: Trenching, 52 min (47–58)". Tap *why* to see "Rain +9 · Machine age +4". | Cab Mode |
| 0:50–1:40 | **The mic drop** (below). | Cab + Command Center side by side |
| 1:40–2:15 | **Sentinel.** Drag a worker blip toward the machine: rings turn red, the tablet buzzes, the Co-Pilot says *"Stop. Person 1.5 metres, rear left."* Then an ML anomaly appears with its reason: "Fuel per cycle 2.8× normal." | Radar + anomaly feed |
| 2:15–2:40 | **The business case.** Idle cost counter: *306 idle hours this month*, converted to fuel, CO₂ and money. ML estimates **70% more accurate** than humans. | Command Center |
| 2:40–3:00 | **Close.** "Detect, alert, coach, improve. Built on data the machines already produce, with no new hardware." | Loop diagram + team |

### The mic-drop moment: 20 seconds, voice only, no touch

1. The presenter holds the Co-Pilot button: *"Log it. I clipped the barrier by the east trench, nobody hurt."*
2. The Co-Pilot reads back a structured incident (Medium severity, EXC001, OP1001, timestamp). The presenter says *"Confirm."*
3. **On the supervisor screen, live:**
   - the incident slides into the feed
   - OP1001's Safety Score rolls down from 92 to 84
   - the Training Hub auto-assigns **"Blind-Spot Awareness"**, with a pulse
4. Line: *"The operator never touched the screen, and the supervisor never refreshed. The system saw it, logged it and started coaching."*

### Demo insurance (do not skip)

- **Record a full backup video** of the demo the night before.
- Add a **`DEMO_MODE`** flag with a deterministic simulator seed, so the same blips and anomalies appear every run.
- Use the Co-Pilot's offline intent parser if venue Wi-Fi or the API fails. Test the demo once with Wi-Fi off.
- Pre-warm the API: send one Co-Pilot request before walking on stage.
- Use a **wired or headset mic** for speech-to-text. Venue noise breaks laptop mics.

---

## 5. Build order for a 3-person team (tiered, so it scales to any time budget)

| Tier | Frontend (P1) | Backend (P2) | ML / AI (P3) |
|---|---|---|---|
| **1: must ship** | router + shadcn + Cab/Command layouts; Incident, Training, Anomaly and Proximity panels (`PLAN.md` Phase 1) | Split into routers, CORS from settings, `Literal` enums, `/ws/telemetry` + simulator, `/ws/events` bus | Estimator P10/P90 + drivers; Safety Score + training recommendation map |
| **2: the wow** | Radar (SVG + motion); live feeds; Safety Score gauge; number tickers | `/copilot/chat` with a Claude tool-use loop + offline intent fallback; `/scores/*` | IsolationForest anomalies with reasons; fuel/idle regression for cost |
| **3: stretch** | 3D R3F excavator; cmdk palette; PWA offline outbox | End-of-shift report (`claude-sonnet-5`); docker-compose | Versioned models; model card in `ml/README.md` |

**Integration checkpoints:**
- After tier 1, freeze the contract additions.
- Run a full demo rehearsal after tier 2.
- Stop feature work with at least 20% of the time left, then rehearse and record the backup video.
