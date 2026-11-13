from datetime import datetime

from backend.config import settings
from backend.database import SessionLocal
from backend.models import User
from backend.security import hash_password


def ensure_admin_exists() -> User | None:
    db = SessionLocal()
    try:
        if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
            if not settings.ADMIN_EMAIL and not settings.ADMIN_PASSWORD:
                legacy_admin = (
                    db.query(User)
                    .filter(
                        User.role == "admin",
                        User.email == "admin@studyplan.local",
                    )
                    .first()
                )
                if legacy_admin:
                    legacy_admin.role = "student"
                    legacy_admin.session_token = None
                    legacy_admin.session_expires_at = None
                    db.commit()
                existing = db.query(User).filter(User.role == "admin").first()
                if existing:
                    return existing
                return None
            raise RuntimeError(
                "Set both ADMIN_EMAIL and ADMIN_PASSWORD to provision the initial admin."
            )

        legacy_admin = (
            db.query(User)
            .filter(User.role == "admin", User.email == "admin@studyplan.local")
            .first()
        )
        if legacy_admin and settings.ADMIN_EMAIL != legacy_admin.email:
            legacy_admin.role = "student"
            legacy_admin.session_token = None
            legacy_admin.session_expires_at = None
            db.commit()
        elif legacy_admin:
            legacy_admin.password_hash = hash_password(settings.ADMIN_PASSWORD)
            db.commit()
            return legacy_admin

        existing = db.query(User).filter(User.role == "admin").first()
        if existing:
            return existing
        admin = User(
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role="admin",
            created_at=datetime.utcnow(),
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
    finally:
        db.close()
