from datetime import datetime

from backend.services.file_processing import estimate_chapters
from planner.engine import generate_plan


def test_chapter_estimate_uses_word_count_instead_of_line_count():
    text = "# Cell Biology\n" + "cell " * 1000

    chapters = estimate_chapters(text)

    assert chapters == [{
        "title": "Cell Biology",
        "workload_hours": 1,
        "study_minutes": 60,
    }]


def test_planner_uses_precise_chapter_estimate():
    now = datetime(2026, 1, 1, 8, 0)
    course = {
        "id": 1,
        "importance": 5,
        "exam_date": datetime(2026, 1, 1, 12, 0),
        "total_workload_hours": 2,
        "is_archived": False,
    }
    chapter = {
        "id": 1,
        "course_id": 1,
        "workload_hours": 2,
        "study_minutes": 90,
    }

    plan = generate_plan(
        [course],
        [chapter],
        [],
        [{"day_of_week": 3, "start_time": "09:00", "end_time": "12:00"}],
        now=now,
    )

    assert sum(item["duration_minutes"] for item in plan["sessions"]) == 90


def test_planner_schedules_on_exam_day_only_before_exam_time():
    now = datetime(2026, 1, 1, 8, 0)
    course = {
        "id": 1,
        "importance": 5,
        "exam_date": datetime(2026, 1, 1, 10, 0),
        "total_workload_hours": 2,
        "is_archived": False,
    }

    plan = generate_plan(
        [course],
        [],
        [],
        [{"day_of_week": 3, "start_time": "09:00", "end_time": "12:00"}],
        now=now,
    )

    assert sum(item["duration_minutes"] for item in plan["sessions"]) == 60
    assert all(item["end_time"] <= course["exam_date"] for item in plan["sessions"])


def test_plan_uses_weekly_availability_and_splits_long_work_with_breaks():
    now = datetime(2026, 1, 1, 8, 0)
    course = {
        "id": 1,
        "name": "Biology",
        "importance": 5,
        "exam_date": datetime(2026, 1, 2),
        "total_workload_hours": 3,
        "is_archived": False,
    }
    plan = generate_plan(
        [course],
        [],
        [],
        [{"day_of_week": 3, "start_time": "09:00", "end_time": "12:30"}],
        now=now,
    )

    sessions = plan["sessions"]
    assert len(sessions) == 2
    assert sessions[0]["start_time"] == datetime(2026, 1, 1, 9, 0)
    assert sessions[0]["duration_minutes"] == 120
    assert sessions[1]["start_time"] == datetime(2026, 1, 1, 11, 15)
    assert all(item["end_time"] <= datetime(2026, 1, 1, 12, 30) for item in sessions)


def test_plan_respects_offline_exception_and_warns_when_capacity_is_short():
    now = datetime(2026, 1, 1, 8, 0)
    course = {
        "id": 1,
        "importance": 5,
        "exam_date": datetime(2026, 1, 2),
        "total_workload_hours": 3,
        "is_archived": False,
    }
    plan = generate_plan(
        [course],
        [],
        [],
        [{"day_of_week": 3, "start_time": "09:00", "end_time": "12:00"}],
        [
            {
                "offline_date": datetime(2026, 1, 1),
                "start_time": "10:00",
                "end_time": "11:00",
            }
        ],
        now,
    )

    assert plan["sessions"]
    assert plan["warnings"]
    assert all(
        item["end_time"] <= datetime(2026, 1, 1, 10, 0)
        or item["start_time"] >= datetime(2026, 1, 1, 11, 0)
        for item in plan["sessions"]
    )
