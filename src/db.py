from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import TypeVar

from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import OperationalError

T = TypeVar("T")

def create_database_engine() -> Engine:
    """Create the PostgreSQL engine from DATABASE_URL."""
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://etl_user:etl_password@localhost:5432/etl_data_quality",
    )
    return create_engine(database_url, pool_pre_ping=True)


def run_with_retry[T](
    engine: Engine,
    operation: Callable[[Connection], T],
    attempts: int = 3,
    delay_seconds: float = 0.5,
) -> T:
    """Retry transient database operations with exponential backoff."""
    for attempt in range(attempts):
        try:
            with engine.connect() as connection:
                return operation(connection)
        except OperationalError:
            if attempt == attempts - 1:
                raise
            time.sleep(delay_seconds * (2**attempt))
    raise RuntimeError("Database operation did not complete")
