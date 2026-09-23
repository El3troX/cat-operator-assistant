import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import Base, SessionLocal, engine
from observability import RequestContextMiddleware, configure_logging
from routers import anomalies, copilot, incidents, live, predict, safety, scores, system, tasks, training
from services.events import bus
from services.scoring import ensure_training_catalog
from services.simulator import run_simulator
from services.task_time import warm_up

settings = get_settings()
configure_logging(settings.log_level, settings.log_json)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_training_catalog(db)
    warm_up()
    bus.bind(asyncio.get_running_loop())
    simulator_task = (
        asyncio.create_task(run_simulator(settings.sim_interval_s, settings.sim_seed)) if settings.sim_enabled else None
    )
    logger.info(
        "API ready: database=%s cors_origins=%s cors_origin_regex=%s",
        engine.url.render_as_string(hide_password=True),
        settings.cors_origin_list or "-",
        settings.cors_origin_regex or "-",
    )
    yield
    if simulator_task:
        simulator_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await simulator_task


app = FastAPI(
    title="Smart Operator Assistant for CAT Machinery",
    description="Backend API for CAT Machinery Smart Operator Assistant",
    version="1.1.0",
    lifespan=lifespan,
)

# The last middleware added is the outermost: CORS must wrap RequestContextMiddleware
# so the JSON 500s it produces still carry CORS headers the browser can read.
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)


@app.exception_handler(RequestValidationError)
async def log_validation_error(request: Request, exc: RequestValidationError):
    problems = "; ".join(
        f"{'.'.join(str(part) for part in error['loc'][1:]) or 'body'}: {error['msg']}" for error in exc.errors()
    )
    logger.info("Rejected %s %s: %s", request.method, request.url.path, problems)
    return await request_validation_exception_handler(request, exc)


for module in (system, tasks, safety, incidents, anomalies, predict, training, scores, copilot, live):
    app.include_router(module.router)
