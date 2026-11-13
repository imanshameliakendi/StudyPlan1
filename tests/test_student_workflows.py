from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from backend.config import settings
from backend.database import SessionLocal
from backend.main import app
from backend.models import Course, StudySession

client = TestClient(app)


def register_and_login(email: str) -> dict[str, str]:
    password = "Secret123!"
    registered = client.post(
        "/api/register",
        json={"email": email, "password": password},
    )
    assert registered.status_code == 200, registered.text
    login = client.post("/api/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return {"Authorization": f'Bearer {login.json()["access_token"]}'}


def create_course(headers: dict[str, str]) -> int:
    response = client.post(
        "/api/courses",
        headers=headers,
        json={
            "name": "Biology",
            "importance": 2,
            "exam_date": (datetime.utcnow() + timedelta(days=14)).isoformat(),
            "description": "Test course",
            "total_workload_hours": 4,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def test_regenerating_plan_includes_course_added_after_first_plan():
    headers = register_and_login("replan-workflow@example.com")
    tomorrow = datetime.now().date() + timedelta(days=1)
    availability = client.post(
        "/api/availability",
        headers=headers,
        json={
            "day_of_week": tomorrow.weekday(),
            "start_time": "09:00",
            "end_time": "17:00",
        },
    )
    assert availability.status_code == 200, availability.text

    first_course = client.post(
        "/api/courses",
        headers=headers,
        json={
            "name": "Biology",
            "importance": 5,
            "exam_date": (datetime.now() + timedelta(days=14)).isoformat(),
            "total_workload_hours": 1,
        },
    )
    assert first_course.status_code == 200, first_course.text
    first_plan = client.post("/api/plan/generate", headers=headers)
    assert first_plan.status_code == 200, first_plan.text
    assert first_plan.json()["sessions"]

    second_course = client.post(
        "/api/courses",
        headers=headers,
        json={
            "name": "Chemistry",
            "importance": 5,
            "exam_date": datetime.combine(tomorrow, datetime.max.time()).isoformat(),
            "total_workload_hours": 1,
        },
    )
    assert second_course.status_code == 200, second_course.text

    refreshed = client.post("/api/plan/generate", headers=headers)
    assert refreshed.status_code == 200, refreshed.text
    assert second_course.json()["id"] in {
        item["course_id"] for item in refreshed.json()["sessions"]
    }


def test_plan_completion_progress_streak_and_ownership():
    student_headers = register_and_login("workflow@example.com")
    course_id = create_course(student_headers)
    availability = client.post(
        "/api/availability",
        headers=student_headers,
        json={"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"},
    )
    assert availability.status_code == 200, availability.text

    generated = client.post("/api/plan/generate", headers=student_headers)
    assert generated.status_code == 200, generated.text
    assert generated.json()["sessions"]

    sessions = client.get("/api/sessions", headers=student_headers)
    assert sessions.status_code == 200, sessions.text
    first_session = sessions.json()[0]
    assert first_session["course_name"] == "Biology"

    other_student_headers = register_and_login("other-workflow@example.com")
    hidden_session = client.post(
        f'/api/sessions/{first_session["id"]}/complete',
        headers=other_student_headers,
        json={},
    )
    assert hidden_session.status_code == 404

    completed = client.post(
        f'/api/sessions/{first_session["id"]}/complete',
        headers=student_headers,
        json={"completion_note": "Reviewed chapter one"},
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "completed"
    assert completed.json()["completion_note"] == "Reviewed chapter one"

    repeated = client.post(
        f'/api/sessions/{first_session["id"]}/complete',
        headers=student_headers,
        json={},
    )
    assert repeated.status_code == 409

    dashboard = client.get("/api/dashboard", headers=student_headers)
    assert dashboard.status_code == 200, dashboard.text
    data = dashboard.json()
    assert data["course_count"] == 1
    assert data["completed_sessions"] == 1
    assert data["current_streak_days"] == 0
    assert data["progress_percent"] > 0
    assert data["course_progress"][0]["course_id"] == course_id

    calendar = client.get("/api/calendar.ics", headers=student_headers)
    assert calendar.status_code == 200
    assert "BEGIN:VCALENDAR" in calendar.text


def test_upload_adds_chapters_and_admin_dashboard(monkeypatch, tmp_path):
    student_headers = register_and_login("upload-workflow@example.com")
    course_id = create_course(student_headers)
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)

    upload = client.post(
        f"/api/courses/{course_id}/upload",
        headers=student_headers,
        files={
            "file": (
                "biology.md",
                (
                    " # Cell Structure\n"
                    "Cells contain organelles and maintain the internal organization required "
                    "for normal cellular function.\n"
                    "# Genetics\n"
                    "Genes encode traits and pass biological information between generations "
                    "through inherited material.\n"
                ).encode(),
                "text/markdown",
            )
        },
    )
    assert upload.status_code == 200, upload.text
    assert len(upload.json()["chapters"]) == 2

    chapters = client.get(
        f"/api/courses/{course_id}/chapters",
        headers=student_headers,
    )
    assert chapters.status_code == 200
    assert [chapter["title"] for chapter in chapters.json()] == [
        "Cell Structure",
        "Genetics",
    ]

    admin_login = client.post(
        "/api/login",
        json={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
    )
    assert admin_login.status_code == 200, admin_login.text
    admin_headers = {"Authorization": f'Bearer {admin_login.json()["access_token"]}'}
    dashboard = client.get("/api/admin/dashboard", headers=admin_headers)
    assert dashboard.status_code == 200, dashboard.text
    assert dashboard.json()["user_count"] >= 2

    blocked = client.get("/api/admin/dashboard", headers=student_headers)
    assert blocked.status_code == 403


def test_archiving_course_removes_private_file_but_keeps_completed_history(
    monkeypatch, tmp_path
):
    headers = register_and_login("archive-workflow@example.com")
    course_id = create_course(headers)
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)
    db = SessionLocal()
    try:
        course = db.query(Course).filter(Course.id == course_id).first()
        assert course is not None
        file_path = tmp_path / str(course.user_id) / str(course.id) / "material.md"
        file_path.parent.mkdir(parents=True)
        file_path.write_text("# Private notes\n")
        course.file_path = str(file_path)
        course.file_name = "material.md"
        course.file_type = ".md"
        db.add_all(
            [
                StudySession(
                    user_id=course.user_id,
                    course_id=course.id,
                    start_time=datetime.utcnow() - timedelta(days=2),
                    end_time=datetime.utcnow() - timedelta(days=2) + timedelta(hours=1),
                    status="completed",
                    completed_at=datetime.utcnow() - timedelta(days=2),
                ),
                StudySession(
                    user_id=course.user_id,
                    course_id=course.id,
                    start_time=datetime.utcnow() + timedelta(days=1),
                    end_time=datetime.utcnow() + timedelta(days=1, hours=1),
                    status="planned",
                ),
            ]
        )
        db.commit()
    finally:
        db.close()

    archived = client.delete(f"/api/courses/{course_id}", headers=headers)
    assert archived.status_code == 200, archived.text
    assert not file_path.exists()

    db = SessionLocal()
    try:
        course = db.query(Course).filter(Course.id == course_id).first()
        sessions = db.query(StudySession).filter(StudySession.course_id == course_id).all()
        assert course is not None and course.is_archived
        assert course.file_path is None
        assert [session.status for session in sessions] == ["completed"]
    finally:
        db.close()


def test_admin_account_deletion_removes_uploads_without_logging_email(
    monkeypatch, tmp_path
):
    headers = register_and_login("private-user@example.com")
    user = client.get("/api/me", headers=headers).json()
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)
    user_directory = tmp_path / str(user["id"])
    user_directory.mkdir()
    private_file = user_directory / "course.pdf"
    private_file.write_bytes(b"private")

    admin_login = client.post(
        "/api/login",
        json={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
    )
    assert admin_login.status_code == 200, admin_login.text
    admin_headers = {
        "Authorization": f'Bearer {admin_login.json()["access_token"]}'
    }

    deleted = client.delete(f'/api/admin/users/{user["id"]}', headers=admin_headers)
    assert deleted.status_code == 200, deleted.text
    assert not user_directory.exists()
    audit = client.get("/api/admin/audit", headers=admin_headers)
    assert audit.status_code == 200, audit.text
    assert "private-user@example.com" not in str(audit.json())


def test_upload_rejects_spoofed_file_content(monkeypatch, tmp_path):
    headers = register_and_login("spoof-upload@example.com")
    course_id = create_course(headers)
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)

    response = client.post(
        f"/api/courses/{course_id}/upload",
        headers=headers,
        files={"file": ("notes.pdf", b"this is not a PDF", "application/pdf")},
    )

    assert response.status_code == 400
    assert not list(tmp_path.rglob("*"))


def test_missed_session_is_preserved_when_plan_is_refreshed():
    headers = register_and_login("missed-session@example.com")
    course_id = create_course(headers)
    db = SessionLocal()
    try:
        course = db.query(Course).filter(Course.id == course_id).first()
        assert course is not None
        missed_session = StudySession(
            user_id=course.user_id,
            course_id=course.id,
            start_time=datetime.utcnow() - timedelta(hours=2),
            end_time=datetime.utcnow() - timedelta(hours=1),
            status="planned",
        )
        db.add(missed_session)
        db.commit()
        session_id = missed_session.id
    finally:
        db.close()

    refreshed = client.post("/api/plan/generate", headers=headers)
    assert refreshed.status_code == 200, refreshed.text

    db = SessionLocal()
    try:
        saved = db.query(StudySession).filter(StudySession.id == session_id).first()
        assert saved is not None
        assert saved.status == "missed"
    finally:
        db.close()
