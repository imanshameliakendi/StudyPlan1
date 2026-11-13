from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.models import (
    AvailabilityException,
    Chapter,
    Course,
    StudySession,
    User,
    WeeklyAvailability,
)
from backend.schemas import PlanResponse, PlanSession
from backend.security import get_current_user, get_db
from planner.engine import generate_plan

router = APIRouter(tags=["planner"])


def _generate_user_plan(current_user: User, db: Session) -> dict:
    courses = db.query(Course).filter(Course.user_id == current_user.id, Course.is_archived.is_(False)).all()
    chapters = db.query(Chapter).join(Course).filter(Course.user_id == current_user.id, Course.is_archived.is_(False)).all()
    sessions = db.query(StudySession).filter(StudySession.user_id == current_user.id).all()
    availability = db.query(WeeklyAvailability).filter(
        WeeklyAvailability.user_id == current_user.id
    ).all()
    exceptions = db.query(AvailabilityException).filter(
        AvailabilityException.user_id == current_user.id
    ).all()
    return generate_plan(courses, chapters, sessions, availability, exceptions)


def _plan_response(plan: dict) -> PlanResponse:
    return PlanResponse(sessions=[PlanSession(**entry) for entry in plan["sessions"]], warnings=plan.get("warnings", []), status=plan.get("status", "ok"))


@router.get("/plan/generate", response_model=PlanResponse)
def preview_user_plan(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _plan_response(_generate_user_plan(current_user, db))


@router.post("/plan/generate", response_model=PlanResponse)
def generate_user_plan(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    plan = _generate_user_plan(current_user, db)
    current_time = datetime.utcnow()
    db.query(StudySession).filter(
        StudySession.user_id == current_user.id,
        StudySession.status == "planned",
        StudySession.end_time < current_time,
    ).update({"status": "missed"}, synchronize_session=False)
    db.query(StudySession).filter(
        StudySession.user_id == current_user.id,
        StudySession.status == "planned",
        StudySession.end_time >= current_time,
    ).delete(synchronize_session=False)
    db.add_all(
        StudySession(
            user_id=current_user.id,
            course_id=item["course_id"],
            chapter_id=item["chapter_id"],
            start_time=item["start_time"],
            end_time=item["end_time"],
            status="planned",
        )
        for item in plan["sessions"]
    )
    db.commit()
    return _plan_response(plan)
