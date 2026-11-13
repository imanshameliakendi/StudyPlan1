from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Iterable

SESSION_MAX_MINUTES = 120
SESSION_MIN_MINUTES = 30
BREAK_MINUTES = 15
PLANNING_HORIZON_DAYS = 90


def _value(item: Any, name: str, default: Any = None) -> Any:
    return item.get(name, default) if isinstance(item, dict) else getattr(item, name, default)


def _time(value: str) -> time:
    return time.fromisoformat(value)


def _overlaps(start: datetime, end: datetime, other_start: datetime, other_end: datetime) -> bool:
    return start < other_end and other_start < end


def _available_segments(
    window_start: datetime,
    window_end: datetime,
    exceptions: Iterable[Any],
    current_date: date,
) -> list[tuple[datetime, datetime]]:
    segments = [(window_start, window_end)]
    for exception in exceptions:
        exception_date = _value(exception, "offline_date")
        if exception_date.date() != current_date:
            continue
        blocked_start = datetime.combine(current_date, _time(_value(exception, "start_time")))
        blocked_end = datetime.combine(current_date, _time(_value(exception, "end_time")))
        remaining = []
        for start, end in segments:
            if not _overlaps(start, end, blocked_start, blocked_end):
                remaining.append((start, end))
                continue
            if start < blocked_start:
                remaining.append((start, blocked_start))
            if blocked_end < end:
                remaining.append((blocked_end, end))
        segments = remaining
    return segments


def _build_tasks(courses: list[Any], chapters: list[Any], sessions: list[Any]) -> list[dict]:
    completed_by_chapter: dict[int, int] = {}
    completed_chapter_by_course: dict[int, int] = {}
    completed_by_course: dict[int, int] = {}
    for session in sessions:
        if _value(session, "status") != "completed":
            continue
        duration = max(
            0,
            int(
                (
                    _value(session, "end_time") - _value(session, "start_time")
                ).total_seconds()
                // 60
            ),
        )
        course_id = _value(session, "course_id")
        completed_by_course[course_id] = completed_by_course.get(course_id, 0) + duration
        chapter_id = _value(session, "chapter_id")
        if chapter_id is not None:
            completed_by_chapter[chapter_id] = completed_by_chapter.get(chapter_id, 0) + duration
            completed_chapter_by_course[course_id] = (
                completed_chapter_by_course.get(course_id, 0) + duration
            )

    chapters_by_course: dict[int, list[Any]] = {}
    for chapter in chapters:
        chapters_by_course.setdefault(_value(chapter, "course_id"), []).append(chapter)

    tasks = []
    for course in courses:
        if _value(course, "is_archived", False):
            continue
        course_id = _value(course, "id")
        exam_date = _value(course, "exam_date")
        deadline = exam_date
        if deadline is not None and deadline.tzinfo is not None:
            deadline = deadline.astimezone(timezone.utc).replace(tzinfo=None)
        importance = max(1, int(_value(course, "importance", 1)))
        course_chapters = chapters_by_course.get(course_id, [])
        chapter_minutes = 0

        for chapter in course_chapters:
            study_minutes = max(0, int(_value(chapter, "study_minutes", 0)))
            workload_minutes = max(0, int(_value(chapter, "workload_hours", 0))) * 60
            target = study_minutes or workload_minutes
            chapter_minutes += max(study_minutes, workload_minutes)
            remaining = max(0, target - completed_by_chapter.get(_value(chapter, "id"), 0))
            if remaining:
                tasks.append({
                    "course_id": course_id,
                    "chapter_id": _value(chapter, "id"),
                    "remaining_minutes": remaining,
                    "deadline": deadline,
                    "importance": importance,
                })

        course_target = max(0, int(_value(course, "total_workload_hours", 0))) * 60
        unassigned_target = max(0, course_target - chapter_minutes)
        if not course_chapters:
            unassigned_target = course_target
        unassigned_completed = max(
            0,
            completed_by_course.get(course_id, 0)
            - completed_chapter_by_course.get(course_id, 0),
        )
        remaining = max(0, unassigned_target - unassigned_completed)
        if remaining:
            tasks.append({
                "course_id": course_id,
                "chapter_id": None,
                "remaining_minutes": remaining,
                "deadline": deadline,
                "importance": importance,
            })
    return tasks


def generate_plan(
    courses: list[Any],
    chapters: list[Any],
    sessions: list[Any],
    availability: list[Any] | None = None,
    exceptions: list[Any] | None = None,
    now: datetime | None = None,
) -> dict:
    current_time = now or datetime.now(timezone.utc).replace(tzinfo=None)
    warnings = []
    tasks = _build_tasks(courses, chapters, sessions)
    if not tasks:
        return {
            "sessions": [],
            "warnings": ["No remaining workload to schedule."],
            "status": "empty",
        }

    if not availability:
        return {
            "sessions": [],
            "warnings": ["Add weekly availability before generating your study plan."],
            "status": "empty",
        }

    weekly_windows = {}
    for item in availability:
        day = int(_value(item, "day_of_week"))
        start = _time(_value(item, "start_time"))
        end = _time(_value(item, "end_time"))
        if start < end:
            weekly_windows.setdefault(day, []).append((start, end))
    if not weekly_windows:
        return {
            "sessions": [],
            "warnings": ["No valid weekly availability windows were found."],
            "status": "empty",
        }

    completed_sessions = [
        session for session in sessions if _value(session, "status") == "completed"
    ]
    occupied_sessions = list(completed_sessions)
    offline_periods = exceptions or []
    generated = []
    last_day = current_time.date() + timedelta(days=PLANNING_HORIZON_DAYS)

    for day_offset in range((last_day - current_time.date()).days + 1):
        current_date = current_time.date() + timedelta(days=day_offset)
        for window_start, window_end in weekly_windows.get(current_date.weekday(), []):
            start = datetime.combine(current_date, window_start)
            end = datetime.combine(current_date, window_end)
            if current_date == current_time.date():
                start = max(start, current_time.replace(second=0, microsecond=0))
            if start >= end:
                continue

            for segment_start, segment_end in _available_segments(
                start, end, offline_periods, current_date
            ):
                slot_start = segment_start
                while tasks and slot_start + timedelta(minutes=SESSION_MIN_MINUTES) <= segment_end:
                    slot_minutes = min(
                        SESSION_MAX_MINUTES,
                        int((segment_end - slot_start).total_seconds() // 60),
                    )
                    eligible = [
                        task
                        for task in tasks
                        if task["deadline"] is None
                        or slot_start + timedelta(minutes=SESSION_MIN_MINUTES)
                        <= task["deadline"]
                    ]
                    if not eligible:
                        break
                    eligible.sort(
                        key=lambda task: (
                            -task["importance"] / max(
                                1,
                                (
                                    (task["deadline"].date() if task["deadline"] else last_day)
                                    - current_date
                                ).days,
                            ),
                            task["deadline"] or datetime.combine(last_day, time.max),
                            task["course_id"],
                            task["chapter_id"] or 0,
                        )
                    )
                    task = eligible[0]
                    if task["deadline"] is not None:
                        minutes_until_deadline = int(
                            (task["deadline"] - slot_start).total_seconds() // 60
                        )
                        slot_minutes = min(slot_minutes, minutes_until_deadline)
                    duration = min(slot_minutes, task["remaining_minutes"])
                    if duration < SESSION_MIN_MINUTES:
                        duration = min(SESSION_MIN_MINUTES, slot_minutes)

                    slot_end = slot_start + timedelta(minutes=duration)
                    if any(
                        _overlaps(
                            slot_start,
                            slot_end,
                            _value(session, "start_time"),
                            _value(session, "end_time"),
                        )
                        for session in occupied_sessions
                    ):
                        slot_start += timedelta(minutes=SESSION_MAX_MINUTES + BREAK_MINUTES)
                        continue

                    entry = {
                        "course_id": task["course_id"],
                        "chapter_id": task["chapter_id"],
                        "start_time": slot_start,
                        "end_time": slot_end,
                        "duration_minutes": duration,
                        "status": "planned",
                    }
                    generated.append(entry)
                    occupied_sessions.append(entry)
                    task["remaining_minutes"] -= duration
                    if task["remaining_minutes"] <= 0:
                        tasks.remove(task)
                    slot_start = slot_end + timedelta(minutes=BREAK_MINUTES)

    if tasks:
        warnings.append(
            "Some workload could not be scheduled within your availability and exam dates."
        )
    return {
        "sessions": generated,
        "warnings": warnings,
        "status": "ok" if generated else "empty",
    }
