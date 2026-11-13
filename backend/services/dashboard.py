from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from backend.config import settings
from backend.models import Course, StudySession


def _local_date(value: datetime, local_timezone: ZoneInfo) -> date:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(local_timezone).date()


def _streak_metrics(
    sessions: list[StudySession], today: date, local_timezone: ZoneInfo
) -> tuple[int, int]:
    scheduled_days = {
        _local_date(session.start_time, local_timezone)
        for session in sessions
        if session.status in {"planned", "completed", "missed"}
    }
    completed_days = {
        _local_date(session.start_time, local_timezone)
        for session in sessions
        if session.status == "completed"
    }
    effective_days = sorted(
        day
        for day in scheduled_days
        if day < today or (day == today and day in completed_days)
    )
    if not effective_days:
        return 0, 0

    current_streak = 0
    for day in reversed(effective_days):
        if day not in completed_days:
            break
        current_streak += 1

    longest_streak = 0
    run = 0
    for day in effective_days:
        if day in completed_days:
            run += 1
            longest_streak = max(longest_streak, run)
        else:
            run = 0

    return current_streak, longest_streak


def build_student_dashboard(
    courses: list[Course],
    sessions: list[StudySession],
    now: datetime | None = None,
) -> dict:
    current_time = now or datetime.utcnow()
    if current_time.tzinfo is not None:
        current_time = current_time.astimezone(timezone.utc).replace(tzinfo=None)
    local_timezone = ZoneInfo(settings.TIMEZONE)
    today_local = _local_date(current_time, local_timezone)
    active_courses = [course for course in courses if not course.is_archived]
    active_course_ids = {course.id for course in active_courses}
    active_sessions = [session for session in sessions if session.course_id in active_course_ids]
    completed_sessions = [session for session in sessions if session.status == "completed"]
    active_completed_sessions = [
        session for session in active_sessions if session.status == "completed"
    ]
    current_streak, longest_streak = _streak_metrics(
        sessions, today_local, local_timezone
    )

    completed_minutes_by_course: dict[int, int] = defaultdict(int)
    for session in active_completed_sessions:
        minutes = max(0, int((session.end_time - session.start_time).total_seconds() // 60))
        completed_minutes_by_course[session.course_id] += minutes

    target_minutes = sum(max(0, course.total_workload_hours) * 60 for course in active_courses)
    completed_minutes = sum(completed_minutes_by_course.values())
    course_progress = []
    for course in active_courses:
        target = max(0, course.total_workload_hours) * 60
        course_completed = completed_minutes_by_course[course.id]
        course_progress.append({
            "course_id": course.id,
            "course_name": course.name,
            "completed_minutes": course_completed,
            "target_minutes": target,
            "progress_percent": min(100, round(course_completed / target * 100)) if target else 0,
            "exam_date": course.exam_date,
        })

    week_start = current_time - timedelta(days=7)
    week_minutes = sum(
        max(0, int((session.end_time - session.start_time).total_seconds() // 60))
        for session in completed_sessions
        if session.completed_at and week_start <= session.completed_at <= current_time
    )
    upcoming = sorted(
        (
            session for session in active_sessions
            if session.status == "planned" and session.start_time >= current_time
        ),
        key=lambda session: session.start_time,
    )[:5]
    course_names = {course.id: course.name for course in active_courses}

    return {
        "course_count": len(active_courses),
        "completed_sessions": len(completed_sessions),
        "planned_sessions": sum(session.status == "planned" for session in active_sessions),
        "current_streak_days": current_streak,
        "longest_streak_days": longest_streak,
        "missed_sessions": sum(
            session.status == "missed" for session in active_sessions
        ),
        "study_minutes_this_week": week_minutes,
        "progress_percent": min(100, round(completed_minutes / target_minutes * 100)) if target_minutes else 0,
        "course_progress": course_progress,
        "upcoming_sessions": [
            {
                "id": session.id,
                "course_id": session.course_id,
                "course_name": course_names[session.course_id],
                "start_time": session.start_time,
                "end_time": session.end_time,
                "status": session.status,
            }
            for session in upcoming
        ],
    }
