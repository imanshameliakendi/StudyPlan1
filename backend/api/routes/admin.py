from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.models import AdminAuditLog, Course, StudySession, User
from backend.schemas import AdminUserSummary, AuditLogOut
from backend.security import get_db, require_admin
from backend.services.file_processing import delete_user_uploads

router = APIRouter(tags=["admin"])


@router.get("/admin/users", response_model=list[AdminUserSummary])
def list_users(
    search: str | None = Query(default=None, max_length=255),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if search and search.strip():
        query = query.filter(User.email.ilike(f"%{search.strip()}%"))
    return query.order_by(User.created_at.desc()).all()


@router.get("/admin/dashboard")
def get_admin_dashboard(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User)
    return {
        "user_count": users.filter(User.is_archived.is_(False)).count(),
        "student_count": users.filter(User.role == "student", User.is_archived.is_(False)).count(),
        "admin_count": users.filter(User.role == "admin", User.is_archived.is_(False)).count(),
        "course_count": db.query(Course).filter(Course.is_archived.is_(False)).count(),
        "completed_sessions": db.query(StudySession).filter(StudySession.status == "completed").count(),
        "recent_activity": db.query(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).limit(10).all(),
    }


@router.get("/admin/audit", response_model=list[AuditLogOut])
def get_audit(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).all()


@router.delete("/admin/users/{user_id}")
def delete_user(user_id: int, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete the account you are currently using.",
        )
    if target.role == "admin" and db.query(User).filter(User.role == "admin").count() <= 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The last administrator account cannot be deleted.",
        )
    delete_user_uploads(target.id)
    db.add(
        AdminAuditLog(
            user_id=current_user.id,
            action="delete_user",
            detail="Removed a user account",
        )
    )
    db.delete(target)
    db.commit()
    return {"ok": True}
