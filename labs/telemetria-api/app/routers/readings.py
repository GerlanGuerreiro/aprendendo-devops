import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.sensor_reading import SensorReading
from app.schemas.sensor_reading import SensorReadingCreate, SensorReadingOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/readings", tags=["readings"])


@router.post("", response_model=SensorReadingOut, status_code=201)
def create_reading(reading: SensorReadingCreate, db: Session = Depends(get_db)) -> SensorReading:
    db_reading = SensorReading(**reading.model_dump())
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    logger.info(
        "reading_persisted",
        extra={"sensor_id": db_reading.sensor_id, "reading_id": db_reading.id},
    )
    return db_reading


@router.get("", response_model=list[SensorReadingOut])
def list_readings(limit: int = 50, db: Session = Depends(get_db)) -> list[SensorReading]:
    return (
        db.query(SensorReading)
        .order_by(SensorReading.timestamp.desc())
        .limit(limit)
        .all()
    )
