import os
import secrets

os.environ.setdefault("DATABASE_URL", "sqlite:///./storage/test_studyplan.db")
os.environ.setdefault("UPLOAD_DIR", "./storage/test_uploads")
os.environ.setdefault("ADMIN_EMAIL", "test-admin@studyplan.local")
os.environ.setdefault("ADMIN_PASSWORD", secrets.token_urlsafe(24))

import pytest

from backend.database import SessionLocal
from backend.config import settings
from backend.models import (
    AdminAuditLog,
    AvailabilityException,
    Chapter,
    Course,
    StudySession,
    User,
    WeeklyAvailability,
)
from backend.security import hash_password


_test_db = SessionLocal()
try:
    _existing_admin = _test_db.query(User).filter(User.role == "admin").first()
    if _existing_admin:
        _existing_admin.email = settings.ADMIN_EMAIL
        _existing_admin.password_hash = hash_password(settings.ADMIN_PASSWORD)
        _test_db.commit()
finally:
    _test_db.close()


def _clear_students(db):
    db.query(StudySession).delete(synchronize_session=False)
    db.query(Chapter).delete(synchronize_session=False)
    db.query(Course).delete(synchronize_session=False)
    db.query(WeeklyAvailability).delete(synchronize_session=False)
    db.query(AvailabilityException).delete(synchronize_session=False)
    db.query(AdminAuditLog).delete(synchronize_session=False)
    db.query(User).filter(User.role != "admin").delete(synchronize_session=False)
    db.commit()


@pytest.fixture(autouse=True)
def reset_db():
    db = SessionLocal()
    try:
        _clear_students(db)
    finally:
        db.close()
    yield
    db = SessionLocal()
    try:
        _clear_students(db)
    finally:
        db.close()
