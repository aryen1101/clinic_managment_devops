from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Appointment, Doctor, Patient
from ..schemas import StatsOut

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)):
    status_counts = select(Appointment.status, func.count(Appointment.id)).group_by(Appointment.status)
    by_status = dict(db.execute(status_counts).all())
    return StatsOut(
        total_patients=db.scalar(select(func.count(Patient.id))) or 0,
        total_doctors=db.scalar(select(func.count(Doctor.id))) or 0,
        available_doctors=db.scalar(select(func.count(Doctor.id)).where(Doctor.is_available.is_(True))) or 0,
        appointments_today=db.scalar(
            select(func.count(Appointment.id)).where(Appointment.appointment_date == date.today())
        )
        or 0,
        scheduled=by_status.get("SCHEDULED", 0),
        completed=by_status.get("COMPLETED", 0),
        cancelled=by_status.get("CANCELLED", 0),
    )
