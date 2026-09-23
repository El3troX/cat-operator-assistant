import asyncio
import logging
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import models
from database import SessionLocal
from schemas import AlertResponse
from services.events import TELEMETRY, bus, publish_event
from services.rules import PROXIMITY_ALERT_M, evaluate_proximity

logger = logging.getLogger(__name__)

WORKERS_PER_MACHINE = 2
READING_EVERY_TICKS = 5  # cab readings change more slowly than people walk around
ALERT_COOLDOWN_TICKS = 15
MAX_DISTANCE_M = 12.0
WORKING_DISTANCE_M = 7.0
# Tuned so the fleet sees roughly one breach every 2-3 minutes at a 2 s tick.
WALK_NOISE_M = 0.8


@dataclass
class Worker:
    id: str
    distance_m: float
    bearing_deg: float


@dataclass(frozen=True)
class Breach:
    machine_id: str
    operator_id: str
    distance_m: float


class FleetSimulator:
    """Replays the operation log as live telemetry and walks simulated ground workers around each machine."""

    def __init__(self, readings_by_machine: dict[str, list[dict]], seed: int) -> None:
        self._rng = random.Random(seed)
        self._readings = readings_by_machine
        self._tick = 0
        self._cursor = {machine: 0 for machine in readings_by_machine}
        self._cooldown = {machine: 0 for machine in readings_by_machine}
        self._workers = {
            machine: [
                Worker(f"{machine}-W{i + 1}", self._rng.uniform(5, MAX_DISTANCE_M), self._rng.uniform(0, 360))
                for i in range(WORKERS_PER_MACHINE)
            ]
            for machine in readings_by_machine
        }
        self.latest: Optional[dict] = None

    def tick(self) -> tuple[dict, list[Breach]]:
        self._tick += 1
        advance_reading = self._tick % READING_EVERY_TICKS == 0
        machines, breaches = [], []

        for machine_id, readings in self._readings.items():
            if advance_reading:
                self._cursor[machine_id] = (self._cursor[machine_id] + 1) % len(readings)
            reading = readings[self._cursor[machine_id]]

            workers = self._workers[machine_id]
            nearest_before = min(w.distance_m for w in workers)
            for worker in workers:
                self._walk(worker)
            nearest = min(workers, key=lambda w: w.distance_m)

            self._cooldown[machine_id] = max(0, self._cooldown[machine_id] - 1)
            entered_danger = nearest.distance_m <= PROXIMITY_ALERT_M < nearest_before
            if entered_danger and not self._cooldown[machine_id]:
                self._cooldown[machine_id] = ALERT_COOLDOWN_TICKS
                breaches.append(Breach(machine_id, reading["operator_id"], nearest.distance_m))

            machines.append(
                {
                    **reading,
                    "machine_id": machine_id,
                    "nearest_m": round(nearest.distance_m, 1),
                    "workers": [
                        {"id": w.id, "distance_m": round(w.distance_m, 2), "bearing_deg": round(w.bearing_deg)}
                        for w in workers
                    ],
                }
            )

        self.latest = {"ts": datetime.now().isoformat(timespec="seconds"), "machines": machines}
        return self.latest, breaches

    def _walk(self, worker: Worker) -> None:
        # Mean-reverting walk: workers hover around a working distance and now and then cut close.
        worker.distance_m += 0.1 * (WORKING_DISTANCE_M - worker.distance_m) + self._rng.gauss(0, WALK_NOISE_M)
        worker.distance_m = min(max(worker.distance_m, 0.4), MAX_DISTANCE_M)
        worker.bearing_deg = (worker.bearing_deg + self._rng.gauss(0, 10)) % 360


current: Optional[FleetSimulator] = None


def load_readings() -> dict[str, list[dict]]:
    with SessionLocal() as db:
        rows = db.query(models.OperationLog).order_by(models.OperationLog.timestamp, models.OperationLog.id).all()
    by_machine: dict[str, list[dict]] = {}
    for row in rows:
        by_machine.setdefault(row.machine_id, []).append(
            {
                "operator_id": row.operator_id,
                "seatbelt_status": row.seatbelt_status,
                "idling_time_min": row.idling_time_min,
                "fuel_used_l": row.fuel_used_l,
                "load_cycles": row.load_cycles,
                "reading_ts": row.timestamp,
            }
        )
    return dict(sorted(by_machine.items()))


def _raise_proximity_alert(breach: Breach) -> None:
    violation = evaluate_proximity(breach.distance_m)
    with SessionLocal() as db:
        alert = models.Alert(
            machine_id=breach.machine_id,
            operator_id=breach.operator_id,
            type=violation.type,
            severity=violation.severity,
            message=violation.message,
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        publish_event("alert.created", AlertResponse.model_validate(alert))
    logger.info("Simulated proximity breach on %s: worker at %.1f m", breach.machine_id, breach.distance_m)


async def run_simulator(interval_s: float, seed: int) -> None:
    global current
    readings = await asyncio.to_thread(load_readings)
    if not readings:
        logger.warning("Fleet simulator idle: operation_log is empty (run seed.py)")
        return

    current = FleetSimulator(readings, seed)
    logger.info("Fleet simulator streaming %d machines every %.1f s", len(readings), interval_s)
    while True:
        try:
            frame, breaches = current.tick()
            bus.publish(TELEMETRY, frame)
            for breach in breaches:
                await asyncio.to_thread(_raise_proximity_alert, breach)
        except Exception:
            # A transient DB error must not end live telemetry for the rest of a demo.
            logger.exception("Fleet simulator tick failed")
        await asyncio.sleep(interval_s)
