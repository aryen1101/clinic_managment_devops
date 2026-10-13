def test_create_patient(client, patient):
    assert patient["id"] > 0
    assert patient["full_name"] == "Test Patient"
    assert patient["blood_group"] == "O+"


def test_create_patient_rejects_invalid_data(client):
    response = client.post("/api/patients", json={
        "full_name": "X",                 # too short
        "date_of_birth": "2999-01-01",    # in the future
        "gender": "UNKNOWN",              # not an allowed value
        "phone": "abc",                   # not a phone number
    })
    assert response.status_code == 422


def test_list_and_search_patients(client, patient):
    client.post("/api/patients", json={
        "full_name": "Another Person", "date_of_birth": "1980-01-01", "gender": "MALE", "phone": "+91 91111 11111",
    })
    assert len(client.get("/api/patients").json()) == 2
    results = client.get("/api/patients", params={"search": "test"}).json()
    assert [p["full_name"] for p in results] == ["Test Patient"]


def test_get_patient_not_found(client):
    response = client.get("/api/patients/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Patient not found"


def test_update_patient(client, patient):
    response = client.put(f"/api/patients/{patient['id']}", json={"address": "New Address", "blood_group": "A-"})
    assert response.status_code == 200
    body = response.json()
    assert body["address"] == "New Address"
    assert body["blood_group"] == "A-"
    assert body["full_name"] == "Test Patient"  # untouched fields stay the same


def test_delete_patient_also_deletes_appointments(client, patient, doctor):
    appt = client.post("/api/appointments", json={
        "patient_id": patient["id"], "doctor_id": doctor["id"],
        "appointment_date": "2030-01-10", "appointment_time": "10:00:00",
    }).json()
    assert client.delete(f"/api/patients/{patient['id']}").status_code == 204
    assert client.get(f"/api/patients/{patient['id']}").status_code == 404
    assert client.get(f"/api/appointments/{appt['id']}").status_code == 404
