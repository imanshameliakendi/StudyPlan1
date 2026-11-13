from __future__ import annotations

from datetime import datetime

from icalendar import Calendar, Event


def build_ics(events):
    calendar = Calendar()
    calendar.add("prodid", "-//StudyPlan//")
    calendar.add("version", "2.0")
    for entry in events:
        event = Event()
        event.add("uid", f"studyplan-{entry['course_id']}-{entry['session_id']}@studyplan")
        event.add("dtstamp", datetime.utcnow())
        event.add("summary", entry.get("title", "Study Session"))
        event.add("dtstart", entry["start_time"])
        event.add("dtend", entry["end_time"])
        calendar.add_component(event)
    return calendar.to_ical().decode("utf-8")
