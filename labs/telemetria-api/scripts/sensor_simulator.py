import logging
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.logging_config import setup_logging
from app.schemas.sensor_reading import SensorReadingCreate

SENSOR_IDS = ["sensor-01", "sensor-02", "sensor-03"]
INTERVAL_SECONDS = 5
TEMPERATURE_RANGE = (15.0, 40.0)
HUMIDITY_RANGE = (20.0, 90.0)
API_URL = os.environ.get("API_URL", "http://localhost:8000")

setup_logging()
logger = logging.getLogger("sensor_simulator")


def generate_reading() -> SensorReadingCreate:
    return SensorReadingCreate(
        sensor_id=random.choice(SENSOR_IDS),
        temperature=round(random.uniform(*TEMPERATURE_RANGE), 2),
        humidity=round(random.uniform(*HUMIDITY_RANGE), 2),
        timestamp=datetime.now(timezone.utc),
    )


def send_reading(reading: SensorReadingCreate) -> None:
    response = requests.post(
        f"{API_URL}/readings", json=reading.model_dump(mode="json"), timeout=5
    )
    response.raise_for_status()


def main() -> None:
    logger.info(
        "simulador_iniciado",
        extra={"interval_seconds": INTERVAL_SECONDS, "api_url": API_URL},
    )
    try:
        while True:
            reading = generate_reading()
            reading_data = reading.model_dump(mode="json")
            try:
                send_reading(reading)
                reading_data["reading_timestamp"] = reading_data.pop("timestamp")
                logger.info("sensor_reading_persisted", extra=reading_data)
            except requests.RequestException as exc:
                logger.error("sensor_reading_failed", extra={"error": str(exc)})
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logger.info("simulador_finalizado")


if __name__ == "__main__":
    main()
