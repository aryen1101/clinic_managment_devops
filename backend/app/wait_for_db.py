"""Block until the database accepts connections (max ~60s), then exit 0.

Runs before `alembic upgrade head` in the container start command. In Kubernetes
the backend and Postgres pods start at the same time; without this wait the
backend would crash once or twice (CrashLoopBackOff) until Postgres is up.
"""
import logging
import sys
import time

from sqlalchemy import create_engine, text

from .config import settings

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s wait_for_db %(message)s")
log = logging.getLogger(__name__)


def wait(timeout_seconds: int = 60, interval_seconds: float = 2.0) -> bool:
    engine = create_engine(settings.sqlalchemy_url, pool_pre_ping=True)
    deadline = time.monotonic() + timeout_seconds
    attempt = 0
    while True:
        attempt += 1
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            log.info("Database is ready (attempt %d)", attempt)
            return True
        except Exception as exc:  # noqa: BLE001
            reason = str(exc).strip().splitlines()[0] if str(exc).strip() else exc.__class__.__name__
            if time.monotonic() >= deadline:
                log.error("Database still unreachable after %ss: %s", timeout_seconds, reason)
                return False
            log.info("Waiting for database (attempt %d): %s", attempt, reason)
            time.sleep(interval_seconds)
        finally:
            engine.dispose()


if __name__ == "__main__":
    sys.exit(0 if wait() else 1)
