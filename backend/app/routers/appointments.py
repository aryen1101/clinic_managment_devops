from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from prometheus_client import Counter
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Appointment, Doctor, Patient
from ..schemas import AppointmentCreate, AppointmentOut, AppointmentStatus, AppointmentUpdate
from .common import get_or_404

router = APIRouter(prefix="/api/appointments", tags=["appointments"])

# Business metric, visible in Prometheus/Grafana next to the HTTP metrics.
APPOINTMENTS_BOOKED = Counter("clinic_appointments_booked_total", "Appointments booked", ["doctor_specialization"])


def _check_doctor_slot(db: Session, appt: Appointment) -> None:
    """A doctor cannot have two active (non-cancelled) appointments at the same date and time."""
    if appt.status == "CANCELLED":
        return
    query = select(Appointment.id).where(
        Appointment.doctor_id == appt.doctor_id,
        Appointment.appointment_date == appt.appointment_date,
        Appointment.appointment_time == appt.appointment_time,
        Appointment.status != "CANCELLED",
    )
    if appt.id is not None:
        query = query.where(Appointment.id != appt.id)
    if db.scalars(query).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Doctor already has an appointment at this time"
        )


@router.get("", response_model=list[AppointmentOut])
def list_appointments(
    status_filter: AppointmentStatus | None = Query(default=None, alias="status"),
    on_date: date | None = Query(default=None, alias="date"),
    doctor_id: int | None = None,
    patient_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = select(Appointment).order_by(Appointment.appointment_date.desc(), Appointment.appointment_time)
    if status_filter:
        query = query.where(Appointment.status == status_filter)
    if on_date:
        query = query.where(Appointment.appointment_date == on_date)
    if doctor_id:
        query = query.where(Appointment.doctor_id == doctor_id)
    if patient_id:
        query = query.where(Appointment.patient_id == patient_id)
    return list(db.scalars(query).unique())


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Appointment, appointment_id, "Appointment")


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    get_or_404(db, Patient, payload.patient_id, "Patient")
    doctor = get_or_404(db, Doctor, payload.doctor_id, "Doctor")
    if not doctor.is_available:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor is not available for appointments")

    appt = Appointment(**payload.model_dump())
    _check_doctor_slot(db, appt)
    db.add(appt)
    db.commit()
    db.refresh(appt)
    APPOINTMENTS_BOOKED.labels(doctor_specialization=doctor.specialization).inc()
    return appt


@router.put("/{appointment_id}", response_model=AppointmentOut)
def update_appointment(appointment_id: int, payload: AppointmentUpdate, db: Session = Depends(get_db)):
    appt = get_or_404(db, Appointment, appointment_id, "Appointment")
    changes = payload.model_dump(exclude_unset=True)
    if "patient_id" in changes:
        get_or_404(db, Patient, changes["patient_id"], "Patient")
    if "doctor_id" in changes:
        get_or_404(db, Doctor, changes["doctor_id"], "Doctor")
    for key, value in changes.items():
        setattr(appt, key, value)
    with db.no_autoflush:
        _check_doctor_slot(db, appt)
    db.commit()
    db.refresh(appt)
    return appt


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appt = get_or_404(db, Appointment, appointment_id, "Appointment")
    db.delete(appt)
    db.commit()
