from html import escape
from datetime import datetime, timedelta

import requests
import streamlit as st

from api_config import get_backend_url

BACKEND_URL = get_backend_url()
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

st.set_page_config(page_title="StudyPlan", page_icon="📚", layout="wide")


def apply_theme():
    st.markdown(
        """
        <style>
        :root {
            --sp-ink: #172a26;
            --sp-muted: #63736d;
            --sp-green: #176b55;
            --sp-green-dark: #10513f;
            --sp-mint: #e7f2ec;
            --sp-canvas: #f5f7f4;
            --sp-line: #e2e9e3;
            --sp-card: #ffffff;
        }
        .stApp { background: var(--sp-canvas); color: var(--sp-ink); }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] { background: #102c25; }
        [data-testid="stSidebar"] * { color: #eef6f1; }
        [data-testid="stSidebar"] [data-testid="stRadio"] label {
            border-radius: 10px; padding: 8px 10px; margin: 2px 0;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
            background: rgba(255,255,255,.09);
        }
        .block-container { max-width: 1240px; padding-top: 2.4rem; padding-bottom: 4rem; }
        h1, h2, h3 { color: var(--sp-ink); letter-spacing: -.025em; }
        h1 { font-weight: 720; }
        [data-testid="stMetric"] {
            background: var(--sp-card); border: 1px solid var(--sp-line);
            padding: 18px 20px; border-radius: 14px;
            box-shadow: 0 2px 8px rgba(20, 45, 35, .035);
        }
        [data-testid="stMetricLabel"] { color: var(--sp-muted); }
        [data-testid="stMetricValue"] { color: var(--sp-ink); }
        [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] {
            scroll-margin-top: 24px;
        }
        .stButton > button, .stFormSubmitButton > button {
            border-radius: 9px; min-height: 2.55rem; font-weight: 600;
            border: 1px solid #d5e0d8;
        }
        .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
            background: var(--sp-green); border-color: var(--sp-green); color: white;
        }
        .stButton > button[kind="primary"]:hover,
        .stFormSubmitButton > button[kind="primary"]:hover {
            background: var(--sp-green-dark); border-color: var(--sp-green-dark); color: white;
        }
        input, textarea, [data-baseweb="select"] > div {
            border-radius: 9px !important;
        }
        [data-testid="stExpander"] {
            background: var(--sp-card); border: 1px solid var(--sp-line);
            border-radius: 12px; overflow: hidden;
        }
        [data-testid="stDataFrame"] { border: 1px solid var(--sp-line); border-radius: 12px; }
        .sp-brand { font-size: 1.35rem; font-weight: 750; letter-spacing: -.04em; }
        .sp-eyebrow { color: var(--sp-green); font-size: .76rem; font-weight: 750;
            letter-spacing: .12em; text-transform: uppercase; margin-bottom: .35rem; }
        .sp-subtitle { color: var(--sp-muted); font-size: 1rem; margin-top: -.25rem; }
        .sp-hero {
            background: linear-gradient(120deg, #123f34, #176b55);
            color: white; border-radius: 18px; padding: 26px 30px;
            margin: 0 0 20px; box-shadow: 0 10px 24px rgba(16, 81, 63, .14);
        }
        .sp-hero h2 { color: white; margin: 0 0 6px; font-size: 1.7rem; }
        .sp-hero p { color: #deeee6; margin: 0; }
        .sp-card {
            background: var(--sp-card); border: 1px solid var(--sp-line);
            border-radius: 14px; padding: 18px 20px; margin-bottom: 12px;
        }
        .sp-card-title { color: var(--sp-ink); font-size: 1.03rem; font-weight: 700; }
        .sp-muted { color: var(--sp-muted); font-size: .9rem; }
        .sp-pill { display: inline-block; border-radius: 999px; padding: 3px 9px;
            background: var(--sp-mint); color: var(--sp-green-dark);
            font-size: .78rem; font-weight: 650; }
        .sp-day {
            background: white; border: 1px solid var(--sp-line);
            border-radius: 12px; padding: 12px; min-height: 120px;
        }
        .sp-day-today { border: 1px solid var(--sp-green); box-shadow: 0 0 0 2px #dceee5; }
        .sp-day-name { color: var(--sp-muted); font-size: .75rem; font-weight: 700;
            letter-spacing: .06em; text-transform: uppercase; }
        .sp-day-date { font-size: 1.15rem; font-weight: 750; margin: 3px 0 10px; }
        .sp-event { background: var(--sp-mint); border-left: 3px solid var(--sp-green);
            border-radius: 5px; padding: 6px 7px; font-size: .78rem; margin: 5px 0; }
        @media (max-width: 720px) {
            .block-container { padding: 1.2rem 1rem 3rem; }
            .sp-hero { padding: 22px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_heading(eyebrow: str, title: str, subtitle: str):
    st.markdown(
        f'<div class="sp-eyebrow">{escape(eyebrow)}</div>'
        f'<h1 style="margin-top:0">{escape(title)}</h1>'
        f'<p class="sp-subtitle">{escape(subtitle)}</p>',
        unsafe_allow_html=True,
    )


def api_request(method, path, **kwargs):
    try:
        return requests.request(
            method,
            f"{BACKEND_URL}/api/{path}",
            timeout=15,
            **kwargs,
        )
    except (requests.ConnectionError, requests.Timeout):
        st.error("StudyPlan can't connect right now. Please try again in a moment.")
        return None


def report_error(response, fallback):
    if response is None:
        return True
    if response.ok:
        return False
    try:
        detail = response.json().get("detail", fallback)
        if isinstance(detail, list):
            detail = "; ".join(item.get("msg", str(item)) for item in detail)
    except ValueError:
        detail = fallback
    st.error(str(detail))
    return True


def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


def render_auth():
    left, right = st.columns([1.1, 1], gap="large")
    with left:
        st.markdown(
            """
            <div class="sp-hero" style="margin-top:3rem;padding:38px">
                <div class="sp-eyebrow" style="color:#a8ddc1">A calmer way to study</div>
                <h2 style="font-size:2.2rem;margin:10px 0">Make progress,<br>one session at a time.</h2>
                <p>Bring your courses, exam dates and real availability together
                in a study plan you can actually follow.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("#### Built for your semester")
        st.write("✓  Keep your courses and materials in one place")
        st.write("✓  Plan around your availability and exam dates")
        st.write("✓  Track completed study and see your progress")
    with right:
        st.markdown('<div class="sp-brand">📚 StudyPlan</div>', unsafe_allow_html=True)
        st.caption("Your semester, with a little more structure.")
        login_tab, register_tab = st.tabs(["Log in", "Create account"])
        with login_tab:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@university.edu")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Log in", type="primary", use_container_width=True)
            if submitted:
                response = api_request("POST", "login", json={"email": email, "password": password})
                if not report_error(response, "Login failed"):
                    st.session_state.token = response.json()["access_token"]
                    st.rerun()

        with register_tab:
            with st.form("register_form"):
                email = st.text_input("Email", placeholder="you@university.edu", key="register_email")
                password = st.text_input(
                    "Password", type="password", key="register_password",
                    help="Use at least 8 characters.",
                )
                submitted = st.form_submit_button(
                    "Create account", type="primary", use_container_width=True
                )
            if submitted:
                response = api_request("POST", "register", json={"email": email, "password": password})
                if not report_error(response, "Registration failed"):
                    st.success("Account created. You can now log in.")


def render_dashboard():
    now = datetime.now()
    greeting = "Good morning" if now.hour < 12 else "Good afternoon" if now.hour < 18 else "Good evening"
    page_heading("Your semester at a glance", f"{greeting}", "Small, consistent sessions add up. Here's where you are today.")
    response = api_request("GET", "dashboard", headers=auth_headers())
    if report_error(response, "Could not load your dashboard"):
        return
    data = response.json()

    sessions_response = api_request("GET", "sessions", headers=auth_headers())
    if report_error(sessions_response, "Could not load your study sessions"):
        return
    sessions = sessions_response.json()
    courses_response = api_request("GET", "courses", headers=auth_headers())
    if report_error(courses_response, "Could not load your courses"):
        return
    courses = courses_response.json()

    st.markdown(
        '<div class="sp-hero"><h2>One focused session at a time.</h2>'
        '<p>Keep your plan realistic, and adjust it whenever your week changes.</p></div>',
        unsafe_allow_html=True,
    )
    metrics = st.columns(4)
    metrics[0].metric("Active courses", data["course_count"])
    metrics[1].metric("Course progress", f'{data["progress_percent"]}%')
    metrics[2].metric("Study streak", f'{data["current_streak_days"]} days')
    metrics[3].metric(
        "Study time · 7 days",
        f'{data["study_minutes_this_week"] // 60}h {data["study_minutes_this_week"] % 60:02d}m',
    )

    today = now.date()
    week_start = today - timedelta(days=today.weekday())
    week_days = [week_start + timedelta(days=offset) for offset in range(7)]
    sessions_by_day: dict[object, list[dict]] = {}
    for session in sessions:
        start = datetime.fromisoformat(session["start_time"].replace("Z", "+00:00"))
        sessions_by_day.setdefault(start.date(), []).append(session)

    st.subheader("This week")
    st.caption("Your planned and completed study sessions, Monday through Sunday.")
    day_columns = st.columns(7)
    for day, column in zip(week_days, day_columns):
        events = sessions_by_day.get(day, [])
        today_class = " sp-day-today" if day == today else ""
        event_html = "".join(
            '<div class="sp-event">'
            f'<strong>{escape(item["course_name"])}</strong><br>'
            f'{datetime.fromisoformat(item["start_time"].replace("Z", "+00:00")).strftime("%H:%M")} '
            f'· {item["status"].title()}</div>'
            for item in events[:3]
        )
        if len(events) > 3:
            event_html += f'<div class="sp-muted">+{len(events) - 3} more</div>'
        column.markdown(
            f'<div class="sp-day{today_class}"><div class="sp-day-name">'
            f'{day.strftime("%a")}</div><div class="sp-day-date">{day.day}</div>'
            f'{event_html or "<div class=sp-muted>No sessions</div>"}</div>',
            unsafe_allow_html=True,
        )

    left, right = st.columns([1.25, 1], gap="large")
    with left:
        st.subheader("Today's focus")
        todays_sessions = [
            item for item in sessions_by_day.get(today, [])
            if item["status"] == "planned"
        ]
        if todays_sessions:
            for item in todays_sessions:
                start = datetime.fromisoformat(item["start_time"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(item["end_time"].replace("Z", "+00:00"))
                st.markdown(
                    f'<div class="sp-card"><div class="sp-card-title">'
                    f'{escape(item["course_name"])}</div><div class="sp-muted">'
                    f'{start.strftime("%H:%M")}–{end.strftime("%H:%M")} · '
                    f'{int((end - start).total_seconds() // 60)} min</div></div>',
                    unsafe_allow_html=True,
                )
                if st.button("Mark complete", key=f'dashboard_complete_{item["id"]}'):
                    _complete_session(item["id"])
        else:
            st.info("Nothing scheduled today. Take a break or build a plan for the week.")
            if st.button("Generate a study plan", type="primary"):
                st.session_state["active_page"] = "Study plan"
                st.rerun()

    with right:
        st.subheader("Coming up")
        upcoming_exams = []
        for course in courses:
            if course.get("exam_date"):
                exam = datetime.fromisoformat(course["exam_date"].replace("Z", "+00:00")).date()
                days_left = (exam - today).days
                if days_left >= 0:
                    upcoming_exams.append((days_left, course["name"], exam))
        for days_left, name, exam in sorted(upcoming_exams)[:4]:
            countdown = "Today" if days_left == 0 else "Tomorrow" if days_left == 1 else f"In {days_left} days"
            st.markdown(
                f'<div class="sp-card"><div class="sp-card-title">{escape(name)}</div>'
                f'<div class="sp-muted">{exam.strftime("%b %d")} · {countdown}</div></div>',
                unsafe_allow_html=True,
            )
        if not upcoming_exams:
            st.info("Add an exam date to a course to see your upcoming exams here.")

        st.subheader("A useful next step")
        course_progress = {
            item["course_id"]: item for item in data["course_progress"]
        }
        near_deadlines = []
        for course in courses:
            if not course.get("exam_date"):
                continue
            exam = datetime.fromisoformat(
                course["exam_date"].replace("Z", "+00:00")
            ).date()
            days_left = (exam - today).days
            progress = course_progress.get(course["id"], {}).get("progress_percent", 0)
            if 0 <= days_left <= 7 and progress < 75:
                near_deadlines.append((days_left, course["name"], progress))
        if near_deadlines:
            days_left, name, progress = min(near_deadlines)
            timing = "today" if days_left == 0 else f"in {days_left} days"
            st.info(
                f"{name} has an exam {timing} and {progress}% progress. "
                "Consider reviewing its remaining chapters."
            )
        elif not courses:
            st.info("Add your first course to get a helpful study recommendation.")
        else:
            st.info("Your plan is up to date. A short review session can help reinforce recent learning.")

        st.subheader("Course progress")
        if data["course_progress"]:
            for course in data["course_progress"][:5]:
                st.progress(
                    course["progress_percent"] / 100,
                    text=f'{course["course_name"]} · {course["progress_percent"]}%',
                )
        else:
            st.info("Add a course to start tracking your progress.")


def _complete_session(session_id: int):
    response = api_request(
        "POST",
        f"sessions/{session_id}/complete",
        headers=auth_headers(),
        json={},
    )
    if not report_error(response, "Could not complete the session"):
        st.success("Progress saved.")
        st.rerun()


def _miss_session(session_id: int):
    response = api_request(
        "POST",
        f"sessions/{session_id}/miss",
        headers=auth_headers(),
    )
    if not report_error(response, "Could not update the session"):
        st.info("Session marked as missed. It can be rescheduled when you refresh your plan.")
        st.rerun()


def render_courses():
    page_heading("Build your semester", "Courses", "Keep exam dates, workload and course materials organized.")
    with st.expander("Add a course", expanded=False):
        with st.form("course_form"):
            name = st.text_input("Course name")
            importance = st.slider("Importance", min_value=1, max_value=10, value=5)
            has_exam_date = st.checkbox("I know the exam date", value=True)
            exam_date = st.date_input(
                "Exam date",
                value=datetime.now().date() + timedelta(days=14),
                disabled=not has_exam_date,
            )
            workload = st.number_input("Estimated workload (hours)", min_value=0, value=10, step=1)
            description = st.text_area("Description")
            submitted = st.form_submit_button(
                "Add course", type="primary", use_container_width=True
            )
        if submitted:
            payload = {
                "name": name,
                "importance": importance,
                "exam_date": f"{exam_date}T23:59:00" if has_exam_date else None,
                "description": description,
                "total_workload_hours": int(workload),
            }
            response = api_request("POST", "courses", json=payload, headers=auth_headers())
            if not report_error(response, "Could not create course"):
                st.success("Course added.")
                st.rerun()

    response = api_request("GET", "courses", headers=auth_headers())
    if report_error(response, "Could not load courses"):
        return
    courses = response.json()
    if not courses:
        st.info("You haven't added any courses yet. Add your first course above to get started.")
        return

    for course in courses:
        with st.expander(f'{course["name"]}  ·  {course["total_workload_hours"]}h'):
            course_date = (
                datetime.fromisoformat(course["exam_date"].replace("Z", "+00:00")).date()
                if course.get("exam_date") else datetime.now().date() + timedelta(days=14)
            )
            with st.form(f'edit_course_{course["id"]}'):
                edited_name = st.text_input(
                    "Course name", value=course["name"], key=f'course_name_{course["id"]}'
                )
                col1, col2 = st.columns(2)
                edited_importance = col1.slider(
                    "Importance", 1, 10, value=course["importance"],
                    key=f'course_importance_{course["id"]}',
                )
                has_exam_date = col2.checkbox(
                    "Exam date set", value=course.get("exam_date") is not None,
                    key=f'has_exam_{course["id"]}',
                )
                edited_exam_date = st.date_input(
                    "Exam date", value=course_date, disabled=not has_exam_date,
                    key=f'course_exam_{course["id"]}',
                )
                edited_workload = st.number_input(
                    "Estimated workload (hours)", min_value=0,
                    value=course["total_workload_hours"],
                    key=f'course_workload_{course["id"]}',
                )
                edited_description = st.text_area(
                    "Description", value=course.get("description") or "",
                    key=f'course_description_{course["id"]}',
                )
                save_course = st.form_submit_button("Save course details")
            if save_course:
                updated = api_request(
                    "PUT",
                    f'courses/{course["id"]}',
                    headers=auth_headers(),
                    json={
                        "name": edited_name,
                        "importance": edited_importance,
                        "exam_date": f"{edited_exam_date}T23:59:00" if has_exam_date else None,
                        "description": edited_description or None,
                        "total_workload_hours": int(edited_workload),
                    },
                )
                if not report_error(updated, "Could not update course"):
                    st.success("Course details saved.")
                    st.rerun()

            if course.get("file_name"):
                st.caption(f'📎 Current material: {course["file_name"]}')
            chapters_response = api_request(
                "GET", f'courses/{course["id"]}/chapters', headers=auth_headers()
            )
            if report_error(chapters_response, "Could not load course chapters"):
                continue
            chapters = chapters_response.json()
            st.markdown("#### Chapters")
            if chapters:
                for chapter in chapters:
                    with st.container(border=True):
                        st.markdown(
                            f'##### {chapter["display_order"] + 1}. {chapter["title"]}'
                        )
                        with st.form(f'edit_chapter_{chapter["id"]}'):
                            chapter_title = st.text_input(
                                "Title", value=chapter["title"],
                                key=f'chapter_title_{chapter["id"]}',
                            )
                            c1, c2, c3 = st.columns(3)
                            chapter_hours = c1.number_input(
                                "Workload (hours)", min_value=0,
                                value=chapter["workload_hours"],
                                key=f'chapter_hours_{chapter["id"]}',
                            )
                            chapter_minutes = c2.number_input(
                                "Study minutes", min_value=0,
                                value=chapter["study_minutes"],
                                key=f'chapter_minutes_{chapter["id"]}',
                            )
                            chapter_order = c3.number_input(
                                "Order", min_value=1,
                                value=chapter["display_order"] + 1,
                                key=f'chapter_order_{chapter["id"]}',
                            )
                            chapter_description = st.text_area(
                                "Notes", value=chapter.get("description") or "",
                                key=f'chapter_description_{chapter["id"]}',
                            )
                            save_chapter = st.form_submit_button("Save chapter")
                        if save_chapter:
                            updated = api_request(
                                "PUT",
                                f'courses/{course["id"]}/chapters/{chapter["id"]}',
                                headers=auth_headers(),
                                json={
                                    "title": chapter_title,
                                    "description": chapter_description or None,
                                    "workload_hours": int(chapter_hours),
                                    "study_minutes": int(chapter_minutes),
                                    "display_order": int(chapter_order) - 1,
                                    "parent_id": chapter.get("parent_id"),
                                },
                            )
                            if not report_error(updated, "Could not update chapter"):
                                st.success("Chapter saved.")
                                st.rerun()
                        with st.form(f'delete_chapter_{chapter["id"]}'):
                            confirm_delete = st.checkbox(
                                "Confirm chapter deletion",
                                key=f'confirm_chapter_{chapter["id"]}',
                            )
                            delete_chapter = st.form_submit_button("Delete chapter")
                        if delete_chapter:
                            if not confirm_delete:
                                st.error("Confirm deletion before continuing.")
                            else:
                                deleted = api_request(
                                    "DELETE",
                                    f'courses/{course["id"]}/chapters/{chapter["id"]}',
                                    headers=auth_headers(),
                                )
                                if not report_error(deleted, "Could not delete chapter"):
                                    st.rerun()
            else:
                st.caption("No chapters yet. Upload material or add a chapter below.")

            with st.form(f'add_chapter_{course["id"]}'):
                st.markdown("##### Add a chapter")
                new_chapter_title = st.text_input(
                    "Chapter title", key=f'new_chapter_title_{course["id"]}'
                )
                new_chapter_col1, new_chapter_col2 = st.columns(2)
                new_chapter_hours = new_chapter_col1.number_input(
                    "Workload (hours)", min_value=0, value=1,
                    key=f'new_chapter_hours_{course["id"]}',
                )
                new_chapter_minutes = new_chapter_col2.number_input(
                    "Study minutes", min_value=0, value=60,
                    key=f'new_chapter_minutes_{course["id"]}',
                )
                add_chapter = st.form_submit_button("Add chapter")
            if add_chapter:
                created = api_request(
                    "POST",
                    f'courses/{course["id"]}/chapters',
                    headers=auth_headers(),
                    json={
                        "title": new_chapter_title,
                        "workload_hours": int(new_chapter_hours),
                        "study_minutes": int(new_chapter_minutes),
                        "display_order": len(chapters),
                    },
                )
                if not report_error(created, "Could not add chapter"):
                    st.success("Chapter added.")
                    st.rerun()

            with st.form(f'archive_course_{course["id"]}'):
                confirm_archive = st.checkbox(
                    "I understand this removes the course from my active plan.",
                    key=f'confirm_archive_{course["id"]}',
                )
                archive_course = st.form_submit_button("Archive course")
            if archive_course:
                if not confirm_archive:
                    st.error("Confirm archiving before continuing.")
                else:
                    archived = api_request(
                        "DELETE", f'courses/{course["id"]}', headers=auth_headers()
                    )
                    if not report_error(archived, "Could not archive course"):
                        st.success("Course archived.")
                        st.rerun()

    st.subheader("Upload course material")
    st.caption("PDF, Markdown (.md), and PowerPoint (.pptx), up to the configured size limit.")
    course_options = {f'{course["name"]} · #{course["id"]}': course["id"] for course in courses}
    selected_name = st.selectbox("Course", list(course_options), key="upload_course")
    uploaded_file = st.file_uploader("Choose a course file", type=["pdf", "md", "pptx"])
    if st.button("Upload and extract chapters", disabled=uploaded_file is None):
        response = api_request(
            "POST",
            f'courses/{course_options[selected_name]}/upload',
            headers=auth_headers(),
            files={
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type or "application/octet-stream",
                )
            },
        )
        if not report_error(response, "Could not process the uploaded file"):
            uploaded = response.json()
            if uploaded["chapters"]:
                st.success(
                    f'Uploaded {uploaded["file_name"]}; '
                    f'{len(uploaded["chapters"])} chapter(s) were added.'
                )
            else:
                st.warning(
                    f'Uploaded {uploaded["file_name"]}, but no new chapters were added. '
                    "The file may not contain selectable text, or its chapters may already exist."
                )
            st.rerun()


def render_study_plan():
    page_heading(
        "Make time for what matters",
        "Study plan",
        "Your schedule is built around your weekly availability and course deadlines.",
    )
    action_col, help_col = st.columns([1, 2], vertical_alignment="center")
    if action_col.button("Generate or refresh plan", type="primary", use_container_width=True):
        generated = api_request("POST", "plan/generate", headers=auth_headers())
        if not report_error(generated, "Could not generate a plan"):
            plan = generated.json()
            if plan["sessions"]:
                st.success(f'{len(plan["sessions"])} study sessions are ready.')
            else:
                st.info("No sessions could be scheduled. Review your workload, exam dates and availability.")
            for warning in plan.get("warnings", []):
                st.warning(warning)
    help_col.caption("Change a course or availability window, then refresh your plan whenever your week changes.")

    response = api_request("GET", "sessions", headers=auth_headers())
    if report_error(response, "Could not load study sessions"):
        return
    sessions = response.json()
    if not sessions:
        st.info("Your plan is empty. Add a course and set your availability to get started.")
    else:
        grouped_sessions: dict[str, list[dict]] = {}
        for item in sessions:
            start = datetime.fromisoformat(item["start_time"].replace("Z", "+00:00"))
            grouped_sessions.setdefault(start.date().isoformat(), []).append(item)

        st.subheader("Upcoming sessions")
        upcoming_days = [
            day for day in sorted(grouped_sessions)
            if any(item["status"] == "planned" for item in grouped_sessions[day])
        ]
        if not upcoming_days:
            st.info("No planned sessions remain. Generate a new plan when your workload changes.")
        for day in upcoming_days[:14]:
            with st.expander(datetime.fromisoformat(day).strftime("%A, %B %d")):
                for item in grouped_sessions[day]:
                    start = datetime.fromisoformat(item["start_time"].replace("Z", "+00:00"))
                    end = datetime.fromisoformat(item["end_time"].replace("Z", "+00:00"))
                    status_label = item["status"].title()
                    st.markdown(
                        f'<div class="sp-card"><div class="sp-card-title">'
                        f'{escape(item["course_name"])}</div><div class="sp-muted">'
                        f'{start.strftime("%H:%M")}–{end.strftime("%H:%M")} · '
                        f'{int((end - start).total_seconds() // 60)} min · '
                        f'{escape(status_label)}</div></div>',
                        unsafe_allow_html=True,
                    )
                    if item["status"] == "planned":
                        if end < datetime.utcnow():
                            if st.button("Mark missed", key=f'missed_{item["id"]}'):
                                _miss_session(item["id"])
                        elif st.button("Mark complete", key=f'complete_{item["id"]}'):
                            _complete_session(item["id"])
        with st.expander("Show completed and historical sessions"):
            history = [item for item in sessions if item["status"] != "planned"]
            if history:
                st.dataframe(
                    [
                        {
                            "Course": item["course_name"],
                            "Date": item["start_time"][:10],
                            "Start": item["start_time"][11:16],
                            "Status": item["status"].title(),
                        }
                        for item in history
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.caption("Completed sessions will appear here.")

    calendar = api_request("GET", "plan.ics", headers=auth_headers())
    if calendar is not None and calendar.ok:
        st.download_button(
            "Download planned sessions (.ics)",
            data=calendar.content,
            file_name="studyplan.ics",
            mime="text/calendar",
        )


def render_progress():
    page_heading("Consistency over cramming", "Progress", "A clear picture of the work you've already put in.")
    response = api_request("GET", "progress", headers=auth_headers())
    if report_error(response, "Could not load your progress"):
        return
    data = response.json()
    metrics = st.columns(4)
    metrics[0].metric("Overall progress", f'{data["progress_percent"]}%')
    metrics[1].metric("Current streak", f'{data["current_streak_days"]} days')
    metrics[2].metric("Longest streak", f'{data["longest_streak_days"]} days')
    metrics[3].metric("Completed sessions", data["completed_sessions"])
    st.caption(
        f'{data["completed_sessions"]} completed sessions · '
        f'{data["study_minutes_this_week"] // 60}h '
        f'{data["study_minutes_this_week"] % 60:02d}m studied in the last 7 days'
    )
    st.subheader("Course progress")
    if not data["course_progress"]:
        st.info("Your course progress will appear here after you add courses.")
    for course in data["course_progress"]:
        col1, col2 = st.columns([3, 1])
        col1.markdown(f'**{course["course_name"]}**')
        col2.markdown(f'{course["progress_percent"]}%')
        st.progress(course["progress_percent"] / 100)
        st.caption(
            f'{course["completed_minutes"] // 60}h {course["completed_minutes"] % 60:02d}m '
            f'of {course["target_minutes"] // 60}h planned workload'
        )
    sessions_response = api_request("GET", "sessions", headers=auth_headers())
    if not report_error(sessions_response, "Could not load study history"):
        history = [
            item for item in sessions_response.json()
            if item["status"] in {"completed", "missed"}
        ]
        st.subheader("Study history")
        if history:
            st.dataframe(
                [
                    {
                        "Course": item["course_name"],
                        "Date": item["start_time"][:10],
                        "Start": item["start_time"][11:16],
                        "Status": item["status"].title(),
                    }
                    for item in reversed(history[-20:])
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("Completed and missed sessions will appear here.")


def render_availability():
    page_heading(
        "Plan around real life",
        "Availability",
        "Set recurring study windows and one-off blocks. The planner will work around them.",
    )
    with st.form("availability_form"):
        day = st.selectbox("Day", DAYS)
        start = st.time_input("Available from")
        end = st.time_input("Available until")
        submitted = st.form_submit_button("Add availability")
    if submitted:
        if end <= start:
            st.error("End time must be later than start time.")
        else:
            response = api_request(
                "POST",
                "availability",
                headers=auth_headers(),
                json={
                    "day_of_week": DAYS.index(day),
                    "start_time": start.strftime("%H:%M"),
                    "end_time": end.strftime("%H:%M"),
                },
            )
            if not report_error(response, "Could not save availability"):
                st.success("Availability saved.")
                st.rerun()

    response = api_request("GET", "availability", headers=auth_headers())
    if report_error(response, "Could not load availability"):
        return
    availability = response.json()
    if not availability:
        st.info("No weekly availability set.")
    for item in availability:
        col1, col2 = st.columns([4, 1])
        col1.write(
            f'{DAYS[item["day_of_week"]]} · {item["start_time"]}–{item["end_time"]}'
        )
        if col2.button("Remove", key=f'availability_{item["id"]}'):
            deleted = api_request(
                "DELETE", f'availability/{item["id"]}', headers=auth_headers()
            )
            if not report_error(deleted, "Could not remove availability"):
                st.rerun()

    with st.expander("Add a one-time offline period"):
        with st.form("offline_exception_form"):
            offline_date = st.date_input("Date", key="offline_date")
            offline_start = st.time_input("Unavailable from", key="offline_start")
            offline_end = st.time_input("Unavailable until", key="offline_end")
            reason = st.text_input("Reason (optional)")
            submitted = st.form_submit_button("Save offline period")
        if submitted:
            if offline_end <= offline_start:
                st.error("End time must be later than start time.")
            else:
                response = api_request(
                    "POST",
                    "availability/exceptions",
                    headers=auth_headers(),
                    json={
                        "offline_date": datetime.combine(offline_date, offline_start).isoformat(),
                        "start_time": offline_start.strftime("%H:%M"),
                        "end_time": offline_end.strftime("%H:%M"),
                        "reason": reason or None,
                    },
                )
                if not report_error(response, "Could not save offline period"):
                    st.success("Offline period saved.")
                    st.rerun()

    exceptions_response = api_request(
        "GET", "availability/exceptions", headers=auth_headers()
    )
    if not report_error(exceptions_response, "Could not load offline periods"):
        exceptions = exceptions_response.json()
        if exceptions:
            st.subheader("One-time offline periods")
            for item in exceptions:
                col1, col2 = st.columns([4, 1])
                col1.write(
                    f'{item["offline_date"][:10]} · {item["start_time"]}–'
                    f'{item["end_time"]} {item.get("reason") or ""}'
                )
                if col2.button("Remove", key=f'exception_{item["id"]}'):
                    deleted = api_request(
                        "DELETE",
                        f'availability/exceptions/{item["id"]}',
                        headers=auth_headers(),
                    )
                    if not report_error(deleted, "Could not remove offline period"):
                        st.rerun()


def render_admin():
    page_heading(
        "Administration",
        "Admin dashboard",
        "Manage accounts and review recent administrative activity.",
    )
    dashboard = api_request("GET", "admin/dashboard", headers=auth_headers())
    if report_error(dashboard, "Could not load the admin dashboard"):
        return
    data = dashboard.json()
    metrics = st.columns(5)
    metrics[0].metric("Users", data["user_count"])
    metrics[1].metric("Students", data["student_count"])
    metrics[2].metric("Admins", data["admin_count"])
    metrics[3].metric("Active courses", data["course_count"])
    metrics[4].metric("Completed sessions", data["completed_sessions"])

    st.subheader("User management")
    search = st.text_input("Search users by email")
    users_response = api_request(
        "GET",
        "admin/users",
        headers=auth_headers(),
        params={"search": search} if search else None,
    )
    if report_error(users_response, "Could not load users"):
        return
    users = users_response.json()
    if users:
        st.dataframe(
            [
                {
                    "ID": item["id"],
                    "Email": item["email"],
                    "Role": item["role"],
                    "Joined": item["created_at"],
                }
                for item in users
            ],
            use_container_width=True,
            hide_index=True,
        )
        deletable = [item for item in users if item["id"] != st.session_state.user["id"]]
        if deletable:
            user_options = {
                f'{item["email"]} (ID {item["id"]})': item["id"] for item in deletable
            }
            with st.form("delete_user_form"):
                selected_user = st.selectbox("Select a user to delete", list(user_options))
                confirm = st.checkbox("I understand this permanently deletes the selected account and its data.")
                submitted = st.form_submit_button("Delete user", type="primary")
            if submitted:
                if not confirm:
                    st.error("Confirm the deletion before continuing.")
                else:
                    deleted = api_request(
                        "DELETE",
                        f'admin/users/{user_options[selected_user]}',
                        headers=auth_headers(),
                    )
                    if not report_error(deleted, "Could not delete the user"):
                        st.success("User deleted.")
                        st.rerun()
    else:
        st.info("No users matched your search.")

    st.subheader("Recent admin activity")
    activity = data["recent_activity"]
    if activity:
        st.dataframe(
            [
                {
                    "Action": item["action"],
                    "Details": item["detail"],
                    "Time": item["created_at"],
                }
                for item in activity
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No admin actions recorded yet.")


apply_theme()

if "token" not in st.session_state:
    st.session_state.token = None

if not st.session_state.token:
    render_auth()
else:
    me_response = api_request("GET", "me", headers=auth_headers())
    if me_response is None:
        st.stop()
    if me_response.status_code == 401:
        st.warning("Your session has expired. Please log in again.")
        st.session_state.token = None
        st.rerun()
    if report_error(me_response, "Could not load your account"):
        st.stop()
    st.session_state.user = me_response.json()

    with st.sidebar:
        st.markdown(
            '<div class="sp-brand">📚 StudyPlan</div>'
            '<div class="sp-muted" style="color:#b9ccc3;margin:4px 0 18px">'
            'A calmer semester starts here.</div>',
            unsafe_allow_html=True,
        )
        st.caption(st.session_state.user["email"])
        pages = ["Overview", "Courses", "Study plan", "Progress", "Availability"]
        if st.session_state.user["role"] == "admin":
            pages.append("Admin dashboard")
        if st.session_state.get("active_page") not in pages:
            st.session_state.active_page = pages[0]
        page = st.radio(
            "Workspace", pages, key="active_page", label_visibility="collapsed"
        )
        if st.button("Log out"):
            logout_response = api_request(
                "POST", "logout", headers=auth_headers()
            )
            if logout_response is None or not logout_response.ok:
                st.warning("Signed out on this device. Your API session could not be revoked.")
            st.session_state.token = None
            st.rerun()

    if page == "Overview":
        render_dashboard()
    elif page == "Courses":
        render_courses()
    elif page == "Study plan":
        render_study_plan()
    elif page == "Progress":
        render_progress()
    elif page == "Availability":
        render_availability()
    elif page == "Admin dashboard":
        render_admin()
