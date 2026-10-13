def test_create_doctor(client, doctor):
    assert doctor["specialization"] == "Cardiology"
    assert doctor["is_available"] is True


def test_duplicate_doctor_email_is_rejected(client, doctor):
    response = client.post("/api/doctors", json={
        "full_name": "Dr. Copy", "specialization": "Dermatology",
        "phone": "+91 98100 99999", "email": doctor["email"],
    })
    assert response.status_code == 409


def test_filter_doctors_by_specialization(client, doctor):
    client.post("/api/doctors", json={
        "full_name": "Dr. Bones", "specialization": "Orthopedics",
        "phone": "+91 98100 12345", "email": "bones@clinic.local",
    })
    results = client.get("/api/doctors", params={"specialization": "ortho"}).json()
    assert [d["full_name"] for d in results] == ["Dr. Bones"]


def test_update_and_delete_doctor(client, doctor):
    response = client.put(f"/api/doctors/{doctor['id']}", json={"is_available": False, "consultation_fee": 1000})
    assert response.status_code == 200
    assert response.json()["is_available"] is False
    assert response.json()["consultation_fee"] == 1000

    assert client.delete(f"/api/doctors/{doctor['id']}").status_code == 204
    assert client.get(f"/api/doctors/{doctor['id']}").status_code == 404
