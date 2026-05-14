# tests/test_students.py

def get_auth_token(client, username="student_tester", password="pass123"):
    """Helper: register a user and return their JWT token."""

    client.post(
        "/auth/register",
        json={"username": username, "password": password}
    )

    response = client.post(
        "/auth/login",
        json={"username": username, "password": password}
    )

    return response.json()["access_token"]


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_get_students_without_token(client):
    """Unauthenticated request must be rejected."""

    response = client.get("/students/")

    assert response.status_code in [401, 403]


def test_get_students_with_token(client):
    """Authenticated request must succeed and return a list."""

    token = get_auth_token(client, username="getter_user")

    response = client.get(
        "/students/",
        headers=auth_header(token)
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_student(client):
    """Creating a student returns 201 with the new student's data."""

    token = get_auth_token(client, username="creator_user")

    response = client.post(
        "/students/",
        json={
            "name": "Ravi Kumar",
            "age": 20,
            "email": "ravi@test.com",
            "city": "Kuppam"
        },
        headers=auth_header(token)
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Ravi Kumar"
    assert data["email"] == "ravi@test.com"
    assert "id" in data


def test_create_student_duplicate_email(client):
    """Duplicate email must return 400, not 500."""

    token = get_auth_token(client, username="dup_email_user")

    student_data = {
        "name": "Test",
        "age": 21,
        "email": "unique@test.com",
        "city": "Chennai"
    }

    client.post(
        "/students/",
        json=student_data,
        headers=auth_header(token)
    )

    response = client.post(
        "/students/",
        json=student_data,
        headers=auth_header(token)
    )

    assert response.status_code == 400


def test_update_student(client):
    """Updating a student should return updated data."""

    token = get_auth_token(client, username="update_user")

    # Create student first
    create_response = client.post(
        "/students/",
        json={
            "name": "Old Name",
            "age": 22,
            "email": "old@test.com",
            "city": "Delhi"
        },
        headers=auth_header(token)
    )

    student_id = create_response.json()["id"]

    # Update student
    update_response = client.put(
        f"/students/{student_id}",
        json={
            "name": "New Name",
            "age": 23,
            "email": "new@test.com",
            "city": "Mumbai"
        },
        headers=auth_header(token)
    )

    assert update_response.status_code == 200

    data = update_response.json()

    assert data["name"] == "New Name"
    assert data["email"] == "new@test.com"
    assert data["city"] == "Mumbai"


def test_delete_student(client):
    """Deleting a student should succeed."""

    token = get_auth_token(client, username="delete_user")

    # Create student first
    create_response = client.post(
        "/students/",
        json={
            "name": "Delete Me",
            "age": 24,
            "email": "delete@test.com",
            "city": "Bangalore"
        },
        headers=auth_header(token)
    )

    student_id = create_response.json()["id"]

    # Delete student
    delete_response = client.delete(
        f"/students/{student_id}",
        headers=auth_header(token)
    )

    assert delete_response.status_code == 200