from __future__ import annotations

from pathlib import Path
from zipfile import BadZipFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pptx.exc import PackageNotFoundError
from pypdf.errors import PdfReadError
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import Chapter, Course, User
from backend.security import get_current_user, get_db
from backend.services.file_processing import (
    ALLOWED_EXTENSIONS,
    delete_private_file,
    estimate_chapters,
    extract_text_from_file,
    safe_filename,
    validate_file_content,
)

router = APIRouter(tags=["uploads"])


@router.post("/courses/{course_id}/upload")
def upload_course_file(course_id: int, file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    file_bytes = file.file.read(max_bytes + 1)
    if len(file_bytes) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large")
    try:
        validate_file_content(file.filename or "", file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    safe_name = safe_filename(file.filename or "course")
    destination = settings.UPLOAD_DIR / str(current_user.id) / str(course.id) / safe_name
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.stem}.upload{destination.suffix}")
    temporary.write_bytes(file_bytes)
    try:
        extracted = extract_text_from_file(temporary)
    except (BadZipFile, PackageNotFoundError, PdfReadError, UnicodeDecodeError, ValueError) as exc:
        temporary.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail="This file could not be read. Upload a valid PDF, Markdown, or PowerPoint file.",
        ) from exc
    parsed = estimate_chapters(extracted)
    if not parsed:
        temporary.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail="No readable text was found in this file. Text-based material is required.",
        )
    old_file_path = course.file_path
    temporary.replace(destination)
    course.file_name = file.filename
    course.file_path = str(destination)
    course.file_type = ext
    existing = db.query(Chapter).filter(Chapter.course_id == course.id).all()
    existing_titles = {chapter.title.casefold() for chapter in existing}
    next_order = max((chapter.display_order for chapter in existing), default=-1) + 1
    added_chapters = []
    for chapter_data in parsed:
        title = chapter_data["title"].strip()
        if title.casefold() in existing_titles:
            continue
        chapter = Chapter(
            course_id=course.id,
            title=title,
            workload_hours=chapter_data["workload_hours"],
            study_minutes=chapter_data["study_minutes"],
            display_order=next_order,
        )
        db.add(chapter)
        added_chapters.append(chapter_data)
        existing_titles.add(title.casefold())
        next_order += 1
    db.flush()
    course.total_workload_hours = sum(chapter.workload_hours for chapter in existing) + sum(
        item["workload_hours"] for item in added_chapters
    )
    db.commit()
    if old_file_path and Path(old_file_path).resolve() != destination.resolve():
        delete_private_file(old_file_path)
    return {"ok": True, "chapters": added_chapters, "file_name": file.filename}
