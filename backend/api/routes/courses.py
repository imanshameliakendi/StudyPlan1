from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models import Chapter, Course, StudySession, User
from backend.schemas import ChapterCreate, ChapterOut, CourseCreate, CourseOut, CourseUpdate, PlanResponse, PlanSession
from backend.security import get_current_user, get_db
from backend.services.file_processing import delete_private_file
from planner.engine import generate_plan

router = APIRouter(tags=["courses"])


@router.get("/courses", response_model=list[CourseOut])
def list_courses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Course).filter(Course.user_id == current_user.id, Course.is_archived.is_(False)).order_by(Course.created_at.desc()).all()


@router.post("/courses", response_model=CourseOut)
def create_course(payload: CourseCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = Course(user_id=current_user.id, **payload.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.get("/courses/{course_id}", response_model=CourseOut)
def get_course(course_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.put("/courses/{course_id}", response_model=CourseOut)
def update_course(course_id: int, payload: CourseUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    for field, value in payload.model_dump().items():
        setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return course


@router.delete("/courses/{course_id}")
def delete_course(course_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    file_path = course.file_path
    course.is_archived = True
    course.file_name = None
    course.file_path = None
    course.file_type = None
    db.query(StudySession).filter(StudySession.course_id == course_id, StudySession.status == "planned").delete()
    db.commit()
    delete_private_file(file_path)
    return {"ok": True}


@router.get("/courses/{course_id}/chapters", response_model=list[ChapterOut])
def list_chapters(course_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return db.query(Chapter).filter(Chapter.course_id == course_id).order_by(Chapter.display_order).all()


@router.post("/courses/{course_id}/chapters", response_model=ChapterOut)
def create_chapter(course_id: int, payload: ChapterCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    chapter = Chapter(course_id=course_id, **payload.model_dump())
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter


@router.put("/courses/{course_id}/chapters/{chapter_id}", response_model=ChapterOut)
def update_chapter(course_id: int, chapter_id: int, payload: ChapterCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id, Chapter.course_id == course_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    for field, value in payload.model_dump().items():
        setattr(chapter, field, value)
    db.commit()
    db.refresh(chapter)
    return chapter


@router.delete("/courses/{course_id}/chapters/{chapter_id}")
def delete_chapter(course_id: int, chapter_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id, Chapter.course_id == course_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    db.delete(chapter)
    db.commit()
    return {"ok": True}


@router.get("/plan", response_model=PlanResponse)
def get_plan(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    courses = db.query(Course).filter(Course.user_id == current_user.id, Course.is_archived.is_(False)).all()
    chapters = db.query(Chapter).join(Course).filter(Course.user_id == current_user.id, Course.is_archived.is_(False)).all()
    sessions = db.query(StudySession).filter(StudySession.user_id == current_user.id).all()
    plan = generate_plan(courses, chapters, sessions)
    return PlanResponse(sessions=[PlanSession(**entry) for entry in plan["sessions"]], warnings=plan.get("warnings", []), status=plan.get("status", "ok"))
