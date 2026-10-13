"""Insert demo data so the dashboard is not empty (useful for screenshots).

Run:  python -m app.seed            (locally)
      docker compose exec backend python -m app.seed
It does nothing if doctors already exist, so running it twice is safe.
"""
from datetime import date, time, timedelta

from sqlalchemy import func, select

from .db import SessionLocal
from .models import Appointment, Doctor, Patient


def seed() -> None:
    with SessionLocal() as db:
        if db.scalar(select(func.count(Doctor.id))):
            print("Seed skipped: data already present")
            return

        doctors = [
            Doctor(full_name="Dr. Ananya Sharma", specialization="Cardiology", phone="+91 98100 11111",
                   email="ananya.sharma@clinic.local", consultation_fee=900),
            Doctor(full_name="Dr. Rahul Mehta", specialization="Orthopedics", phone="+91 98100 22222",
                   email="rahul.mehta@clinic.local", consultation_fee=800),
            Doctor(full_name="Dr. Priya Nair", specialization="Pediatrics", phone="+91 98100 33333",
                   email="priya.nair@clinic.local", consultation_fee=600),
            Doctor(full_name="Dr. Vikram Singh", specialization="General Medicine", phone="+91 98100 44444",
                   email="vikram.singh@clinic.local", consultation_fee=500, is_available=False),
        ]
        patients = [
            Patient(full_name="Amit Kumar", date_of_birth=date(1988, 4, 12), gender="MALE",
                    phone="+91 90000 10001", blood_group="B+", address="Sector 21, Noida"),
            Patient(full_name="Sneha Verma", date_of_birth=date(1995, 9, 3), gender="FEMALE",
                    phone="+91 90000 10002", email="sneha@example.com", blood_group="O+",
                    address="Indiranagar, Bengaluru"),
            Patient(full_name="Rohan Das", date_of_birth=date(2016, 1, 22), gender="MALE",
                    phone="+91 90000 10003", blood_group="A+", address="Salt Lake, Kolkata"),
            Patient(full_name="Fatima Khan", date_of_birth=date(1972, 11, 30), gender="FEMALE",
                    phone="+91 90000 10004", blood_group="AB-", address="Bandra, Mumbai"),
        ]
        db.add_all(doctors + patients)
        db.flush()

        today = date.today()
        db.add_all([
            Appointment(patient_id=patients[0].id, doctor_id=doctors[0].id, appointment_date=today,
                        appointment_time=time(10, 0), reason="Chest pain follow-up"),
            Appointment(patient_id=patients[1].id, doctor_id=doctors[1].id, appointment_date=today,
                        appointment_time=time(11, 30), reason="Knee pain"),
            Appointment(patient_id=patients[2].id, doctor_id=doctors[2].id, appointment_date=today,
                        appointment_time=time(12, 0), reason="Vaccination"),
            Appointment(patient_id=patients[3].id, doctor_id=doctors[0].id, appointment_date=today - timedelta(days=2),
                        appointment_time=time(9, 30), reason="ECG review", status="COMPLETED",
                        notes="BP normal. Continue medication."),
            Appointment(patient_id=patients[0].id, doctor_id=doctors[2].id, appointment_date=today + timedelta(days=1),
                        appointment_time=time(15, 0), reason="Child check-up", status="CANCELLED"),
        ])
        db.commit()
        print("Seed complete: 4 doctors, 4 patients, 5 appointments")


if __name__ == "__main__":
    seed()
