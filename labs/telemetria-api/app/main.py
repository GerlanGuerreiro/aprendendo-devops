import logging

from fastapi import FastAPI

from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="API de Telemetria/Clima")


@app.on_event("startup")
def on_startup() -> None:
    logger.info("api_startup", extra={"event": "startup"})


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
