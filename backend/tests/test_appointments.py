from datetime import date


def book(client, patient, doctor, **overrides):
    payload = {
        "patient_id": patient["id"],
        "doctor_id": doctor["id"],
        "appointment_date": "2030-01-10",
        "appointment_time": "10:00:00",
        "reason": "Routine check-up",
    }
    payload.update(overrides)
    return client.post("/api/appointments", json=payload)


def test_book_appointment(client, patient, doctor):
    response = book(client, patient, doctor)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "SCHEDULED"
    assert body["patient"]["full_name"] == "Test Patient"
    assert body["doctor"]["full_name"] == "Dr. Test Doctor"


def test_booking_with_unknown_patient_returns_404(client, doctor):
    response = book(client, {"id": 9999}, doctor)
    assert response.status_code == 404
    assert response.json()["detail"] == "Patient not found"


def test_double_booking_same_doctor_slot_is_rejected(client, patient, doctor):
    assert book(client, patient, doctor).status_code == 201
    response = book(client, patient, doctor)
    assert response.status_code == 409


def test_cancelled_slot_can_be_rebooked(client, patient, doctor):
    first = book(client, patient, doctor).json()
    client.put(f"/api/appointments/{first['id']}", json={"status": "CANCELLED"})
    assert book(client, patient, doctor).status_code == 201


def test_unavailable_doctor_cannot_be_booked(client, patient, doctor):
    client.put(f"/api/doctors/{doctor['id']}", json={"is_available": False})
    response = book(client, patient, doctor)
    assert response.status_code == 400


def test_update_appointment_status_and_notes(client, patient, doctor):
    appt = book(client, patient, doctor).json()
    response = client.put(f"/api/appointments/{appt['id']}", json={"status": "COMPLETED", "notes": "All good"})
    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"
    assert response.json()["notes"] == "All good"


def test_filter_appointments_by_status(client, patient, doctor):
    book(client, patient, doctor)
    second = book(client, patient, doctor, appointment_time="11:00:00").json()
    client.put(f"/api/appointments/{second['id']}", json={"status": "COMPLETED"})
    completed = client.get("/api/appointments", params={"status": "COMPLETED"}).json()
    assert [a["id"] for a in completed] == [second["id"]]


def test_patient_history(client, patient, doctor):
    book(client, patient, doctor)
    book(client, patient, doctor, appointment_time="12:00:00")
    history = client.get(f"/api/patients/{patient['id']}/appointments").json()
    assert len(history) == 2


def test_delete_appointment(client, patient, doctor):
    appt = book(client, patient, doctor).json()
    assert client.delete(f"/api/appointments/{appt['id']}").status_code == 204
    assert client.get(f"/api/appointments/{appt['id']}").status_code == 404


def test_dashboard_stats(client, patient, doctor):
    book(client, patient, doctor, appointment_date=date.today().isoformat())
    cancelled = book(client, patient, doctor, appointment_time="16:00:00").json()
    client.put(f"/api/appointments/{cancelled['id']}", json={"status": "CANCELLED"})

    stats = client.get("/api/stats").json()
    assert stats == {
        "total_patients": 1,
        "total_doctors": 1,
        "available_doctors": 1,
        "appointments_today": 1,
        "scheduled": 1,
        "completed": 0,
        "cancelled": 1,
    }
