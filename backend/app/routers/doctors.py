from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Doctor
from ..schemas import DoctorCreate, DoctorOut, DoctorUpdate
from .common import get_or_404

router = APIRouter(prefix="/api/doctors", tags=["doctors"])


def _ensure_unique_email(db: Session, email: str, exclude_id: int | None = None) -> None:
    query = select(Doctor).where(Doctor.email == email)
    if exclude_id is not None:
        query = query.where(Doctor.id != exclude_id)
    if db.scalars(query).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A doctor with this email already exists")


@router.get("", response_model=list[DoctorOut])
def list_doctors(
    specialization: str | None = Query(default=None, description="Filter by specialization"),
    available: bool | None = Query(default=None, description="Only available / unavailable doctors"),
    db: Session = Depends(get_db),
):
    query = select(Doctor).order_by(Doctor.full_name)
    if specialization:
        query = query.where(Doctor.specialization.ilike(f"%{specialization}%"))
    if available is not None:
        query = query.where(Doctor.is_available == available)
    return list(db.scalars(query))


@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Doctor, doctor_id, "Doctor")


@router.post("", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor(payload: DoctorCreate, db: Session = Depends(get_db)):
    _ensure_unique_email(db, payload.email)
    doctor = Doctor(**payload.model_dump())
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@router.put("/{doctor_id}", response_model=DoctorOut)
def update_doctor(doctor_id: int, payload: DoctorUpdate, db: Session = Depends(get_db)):
    doctor = get_or_404(db, Doctor, doctor_id, "Doctor")
    changes = payload.model_dump(exclude_unset=True)
    if "email" in changes:
        _ensure_unique_email(db, changes["email"], exclude_id=doctor_id)
    for key, value in changes.items():
        setattr(doctor, key, value)
    db.commit()
    db.refresh(doctor)
    return doctor


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = get_or_404(db, Doctor, doctor_id, "Doctor")
    db.delete(doctor)
    db.commit()
