import logging

from fastapi import FastAPI

from app.core.database import Base, engine
from app.core.logging_config import setup_logging
from app.routers import readings

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="API de Telemetria/Clima")
app.include_router(readings.router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    logger.info("api_startup", extra={"event": "startup"})


@app.get("/health")
def health() -> dict:
    logger.info("health_check", extra={"event": "health_check"})
    return {"status": "ok"}
