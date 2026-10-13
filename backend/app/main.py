"""FastAPI entry point: creates the app, wires middleware, health checks, metrics and routers."""
import logging
import time

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .routers import appointments, dashboard, doctors, patients

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("clinic")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Clinic Management System: patients, doctors and appointments.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exposes /metrics in Prometheus format (request count, latency histogram, in-progress requests).
Instrumentator(excluded_handlers=["/metrics"]).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.middleware("http")
async def access_log(request: Request, call_next):
    """One log line per request, which `kubectl logs` / `docker compose logs` will show."""
    start = time.perf_counter()
    response = await call_next(request)
    if request.url.path not in ("/health", "/ready", "/metrics"):
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info("%s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code, duration_ms)
    return response


@app.get("/", tags=["system"])
def root():
    return {"service": settings.app_name, "version": settings.app_version, "env": settings.app_env, "docs": "/docs"}


@app.get("/health", tags=["system"])
def health():
    """Liveness: the process is up. Does NOT touch the database."""
    return {"status": "UP"}


@app.get("/ready", tags=["system"])
def ready(db: Session = Depends(get_db)):
    """Readiness: the app can serve traffic, i.e. the database is reachable."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - any DB error means "not ready"
        logger.exception("Readiness check failed: database unreachable")
        return JSONResponse(status_code=503, content={"status": "NOT_READY", "database": "DOWN"})
    return {"status": "READY", "database": "UP"}


app.include_router(dashboard.router)
app.include_router(patients.router)
app.include_router(doctors.router)
app.include_router(appointments.router)
