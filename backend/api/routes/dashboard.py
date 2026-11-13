from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.models import Course, StudySession, User
from backend.security import get_current_user, get_db
from backend.services.dashboard import build_student_dashboard

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
@router.get("/progress")
def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    courses = db.query(Course).filter(Course.user_id == current_user.id).all()
    sessions = db.query(StudySession).filter(StudySession.user_id == current_user.id).all()
    return build_student_dashboard(courses, sessions)
