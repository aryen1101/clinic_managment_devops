"""Pydantic schemas: what the API accepts (Create/Update) and returns (Out)."""
from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Gender = Literal["MALE", "FEMALE", "OTHER"]
BloodGroup = Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
AppointmentStatus = Literal["SCHEDULED", "COMPLETED", "CANCELLED"]

PHONE = r"^\+?[0-9 \-]{7,20}$"
EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


# ---------- Doctors ----------
class DoctorBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    specialization: str = Field(min_length=2, max_length=80)
    phone: str = Field(pattern=PHONE)
    email: str = Field(pattern=EMAIL, max_length=120)
    consultation_fee: int = Field(default=500, ge=0, le=100000)
    is_available: bool = True


class DoctorCreate(DoctorBase):
    pass


class DoctorUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    specialization: str | None = Field(default=None, min_length=2, max_length=80)
    phone: str | None = Field(default=None, pattern=PHONE)
    email: str | None = Field(default=None, pattern=EMAIL, max_length=120)
    consultation_fee: int | None = Field(default=None, ge=0, le=100000)
    is_available: bool | None = None


class DoctorOut(DoctorBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DoctorBrief(BaseModel):
    id: int
    full_name: str
    specialization: str
    model_config = ConfigDict(from_attributes=True)


# ---------- Patients ----------
class PatientBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    date_of_birth: date
    gender: Gender
    phone: str = Field(pattern=PHONE)
    email: str | None = Field(default=None, pattern=EMAIL, max_length=120)
    blood_group: BloodGroup | None = None
    address: str = ""

    @field_validator("date_of_birth")
    @classmethod
    def dob_not_in_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return value


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    date_of_birth: date | None = None
    gender: Gender | None = None
    phone: str | None = Field(default=None, pattern=PHONE)
    email: str | None = Field(default=None, pattern=EMAIL, max_length=120)
    blood_group: BloodGroup | None = None
    address: str | None = None

    @field_validator("date_of_birth")
    @classmethod
    def dob_not_in_future(cls, value: date | None) -> date | None:
        if value and value > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return value


class PatientOut(PatientBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PatientBrief(BaseModel):
    id: int
    full_name: str
    phone: str
    model_config = ConfigDict(from_attributes=True)


# ---------- Appointments ----------
class AppointmentCreate(BaseModel):
    patient_id: int = Field(gt=0)
    doctor_id: int = Field(gt=0)
    appointment_date: date
    appointment_time: time
    reason: str = Field(default="", max_length=500)
    status: AppointmentStatus = "SCHEDULED"
    notes: str = ""


class AppointmentUpdate(BaseModel):
    patient_id: int | None = Field(default=None, gt=0)
    doctor_id: int | None = Field(default=None, gt=0)
    appointment_date: date | None = None
    appointment_time: time | None = None
    reason: str | None = Field(default=None, max_length=500)
    status: AppointmentStatus | None = None
    notes: str | None = None


class AppointmentOut(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    appointment_date: date
    appointment_time: time
    reason: str
    status: AppointmentStatus
    notes: str
    created_at: datetime
    patient: PatientBrief
    doctor: DoctorBrief
    model_config = ConfigDict(from_attributes=True)


# ---------- Dashboard ----------
class StatsOut(BaseModel):
    total_patients: int
    total_doctors: int
    available_doctors: int
    appointments_today: int
    scheduled: int
    completed: int
    cancelled: int
