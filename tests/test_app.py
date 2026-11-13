import os
from datetime import datetime, timedelta

os.environ.setdefault("DATABASE_URL", "sqlite:///./storage/test_studyplan.db")
os.environ.setdefault("UPLOAD_DIR", "./storage/test_uploads")

from fastapi.testclient import TestClient

from backend.config import settings
from backend.main import app

client = TestClient(app)


def test_register_login_and_admin_seed():
    email = "student@example.com"
    register = client.post("/api/register", json={"email": email, "password": "Secret123!"})
    assert register.status_code == 200, register.text
    login = client.post("/api/login", json={"email": email, "password": "Secret123!"})
    assert login.status_code == 200, login.text
    data = login.json()
    assert "access_token" in data

    admin_login = client.post(
        "/api/login",
        json={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
    )
    assert admin_login.status_code == 200, admin_login.text


def test_course_and_plan_endpoints():
    email = "courseuser@example.com"
    register = client.post("/api/register", json={"email": email, "password": "Secret123!"})
    token = client.post("/api/login", json={"email": email, "password": "Secret123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create = client.post(
        "/api/courses",
        json={"name": "Algorithms", "importance": 4, "exam_date": (datetime.utcnow() + timedelta(days=10)).isoformat(), "description": "Prep", "total_workload_hours": 12},
        headers=headers,
    )
    assert create.status_code == 200, create.text
    course_id = create.json()["id"]

    plan = client.get("/api/plan", headers=headers)
    assert plan.status_code == 200, plan.text
    assert "sessions" in plan.json()

    course_list = client.get("/api/courses", headers=headers)
    assert course_list.status_code == 200, course_list.text
    assert any(item["id"] == course_id for item in course_list.json())


def test_admin_user_list_and_delete_restrictions():
    email = "admincheck@example.com"
    client.post("/api/register", json={"email": email, "password": "Secret123!"})
    admin_token = client.post(
        "/api/login",
        json={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
    ).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    users = client.get("/api/admin/users", headers=admin_headers)
    assert users.status_code == 200, users.text
    assert len(users.json()) >= 1

    student_token = client.post("/api/login", json={"email": email, "password": "Secret123!"}).json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}
    blocked = client.get("/api/admin/users", headers=student_headers)
    assert blocked.status_code == 403
