from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SensorReadingCreate(BaseModel):
    sensor_id: str
    temperature: float
    humidity: float
    timestamp: datetime


class SensorReadingOut(SensorReadingCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
