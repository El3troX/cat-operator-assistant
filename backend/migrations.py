import logging
from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config
from database import engine
from sqlalchemy import create_engine, inspect

logger = logging.getLogger(__name__)
BACKEND_DIR = Path(__file__).resolve().parent
ALEMBIC_INI = BACKEND_DIR / "alembic.ini"
ALEMBIC_DIR = BACKEND_DIR / "alembic"


def get_alembic_config(database_url: Optional[str] = None) -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(ALEMBIC_DIR))
    if database_url:
        cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


def apply_migrations(database_url: Optional[str] = None) -> None:
    """Apply Alembic migrations to bring the database schema to 'head'.

    Handles legacy unversioned databases automatically by stamping the baseline
    revision before upgrading.
    """
    cfg = get_alembic_config(database_url)
    target_engine = create_engine(database_url) if database_url else engine
    insp = inspect(target_engine)
    existing_tables = set(insp.get_table_names())
    if database_url:
        target_engine.dispose()


    if "alembic_version" not in existing_tables:
        core_tables = {"operation_log", "tasks", "alerts", "incidents", "task_time_data", "training_modules"}
        if existing_tables & core_tables:
            logger.info("Existing database schema detected without alembic_version; stamping '0001_initial_schema'...")
            command.stamp(cfg, "0001_initial_schema")

    logger.info("Applying Alembic migrations to head...")
    command.upgrade(cfg, "head")
    logger.info("Alembic migrations applied successfully.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    apply_migrations()
