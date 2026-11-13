from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session, joinedload

from backend.models import StudySession, User
from backend.security import get_current_user, get_db
from backend.services.calendar_service import build_ics

router = APIRouter(tags=["calendar"])


@router.get("/calendar.ics")
@router.get("/plan.ics")
def export_calendar(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = (
        db.query(StudySession)
        .options(joinedload(StudySession.course))
        .filter(StudySession.user_id == current_user.id, StudySession.status == "planned")
        .order_by(StudySession.start_time)
        .all()
    )
    events = [
        {
            "session_id": session.id,
            "course_id": session.course_id,
            "title": f"Study: {session.course.name}",
            "start_time": session.start_time,
            "end_time": session.end_time,
        }
        for session in sessions
    ]
    return Response(
        content=build_ics(events),
        media_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="studyplan.ics"'},
    )
