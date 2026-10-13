from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Appointment, Patient
from ..schemas import AppointmentOut, PatientCreate, PatientOut, PatientUpdate
from .common import get_or_404

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.get("", response_model=list[PatientOut])
def list_patients(
    search: str | None = Query(default=None, description="Search by name or phone"),
    db: Session = Depends(get_db),
):
    query = select(Patient).order_by(Patient.id.desc())
    if search:
        pattern = f"%{search}%"
        query = query.where(or_(Patient.full_name.ilike(pattern), Patient.phone.ilike(pattern)))
    return list(db.scalars(query))


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Patient, patient_id, "Patient")


@router.get("/{patient_id}/appointments", response_model=list[AppointmentOut])
def patient_history(patient_id: int, db: Session = Depends(get_db)):
    get_or_404(db, Patient, patient_id, "Patient")
    query = (
        select(Appointment)
        .where(Appointment.patient_id == patient_id)
        .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
    )
    return list(db.scalars(query).unique())


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    patient = Patient(**payload.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: int, payload: PatientUpdate, db: Session = Depends(get_db)):
    patient = get_or_404(db, Patient, patient_id, "Patient")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(patient, key, value)
    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = get_or_404(db, Patient, patient_id, "Patient")
    db.delete(patient)
    db.commit()
