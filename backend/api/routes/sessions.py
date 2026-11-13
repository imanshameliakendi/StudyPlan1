from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.models import StudySession, User
from backend.schemas import SessionComplete, StudySessionOut
from backend.security import get_current_user, get_db

router = APIRouter(tags=["sessions"])


def _session_response(session: StudySession) -> dict:
    return {
        "id": session.id,
        "course_id": session.course_id,
        "course_name": session.course.name,
        "chapter_id": session.chapter_id,
        "start_time": session.start_time,
        "end_time": session.end_time,
        "status": session.status,
        "completion_note": session.completion_note,
        "completed_at": session.completed_at,
    }


@router.get("/sessions", response_model=list[StudySessionOut])
def list_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = (
        db.query(StudySession)
        .options(joinedload(StudySession.course))
        .filter(StudySession.user_id == current_user.id)
        .order_by(StudySession.start_time)
        .all()
    )
    return [_session_response(session) for session in sessions]


@router.post("/sessions/{session_id}/complete", response_model=StudySessionOut)
def complete_session(
    session_id: int,
    payload: SessionComplete,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(StudySession)
        .options(joinedload(StudySession.course))
        .filter(StudySession.id == session_id, StudySession.user_id == current_user.id)
        .first()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Study session not found")
    if session.status == "completed":
        raise HTTPException(status_code=409, detail="Completed sessions cannot be changed")
    if session.status != "planned":
        raise HTTPException(status_code=409, detail="Only planned sessions can be completed")

    session.status = "completed"
    session.completion_note = payload.completion_note
    session.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return _session_response(session)


@router.post("/sessions/{session_id}/miss", response_model=StudySessionOut)
def mark_session_missed(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(StudySession)
        .options(joinedload(StudySession.course))
        .filter(StudySession.id == session_id, StudySession.user_id == current_user.id)
        .first()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Study session not found")
    if session.status != "planned":
        raise HTTPException(status_code=409, detail="Only planned sessions can be marked missed")
    if session.end_time >= datetime.utcnow():
        raise HTTPException(status_code=409, detail="A session can be marked missed after it ends")

    session.status = "missed"
    db.commit()
    db.refresh(session)
    return _session_response(session)
