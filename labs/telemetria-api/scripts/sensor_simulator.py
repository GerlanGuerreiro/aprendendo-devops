import logging
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.logging_config import setup_logging
from app.models.sensor_reading import SensorReading

SENSOR_IDS = ["sensor-01", "sensor-02", "sensor-03"]
INTERVAL_SECONDS = 5
TEMPERATURE_RANGE = (15.0, 40.0)
HUMIDITY_RANGE = (20.0, 90.0)

setup_logging()
logger = logging.getLogger("sensor_simulator")


def generate_reading() -> SensorReading:
    return SensorReading(
        sensor_id=random.choice(SENSOR_IDS),
        temperature=round(random.uniform(*TEMPERATURE_RANGE), 2),
        humidity=round(random.uniform(*HUMIDITY_RANGE), 2),
        timestamp=datetime.now(timezone.utc),
    )


def main() -> None:
    logger.info("simulador_iniciado", extra={"interval_seconds": INTERVAL_SECONDS})
    try:
        while True:
            reading = generate_reading()
            reading_data = reading.model_dump(mode="json")
            reading_data["reading_timestamp"] = reading_data.pop("timestamp")
            logger.info("sensor_reading_received", extra=reading_data)
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logger.info("simulador_finalizado")


if __name__ == "__main__":
    main()
