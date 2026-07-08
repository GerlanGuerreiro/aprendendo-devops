from datetime import datetime

from pydantic import BaseModel


class SensorReading(BaseModel):
    sensor_id: str
    temperature: float
    humidity: float
    timestamp: datetime
