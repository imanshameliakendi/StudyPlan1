# StudyPlan MVP Specification

## 1. Product overview
StudyPlan is a student-focused academic planning application that helps students manage courses, estimate study effort, define time availability, and generate realistic study plans before examinations.

## 2. Product objectives
- Manage personal student accounts and admin accounts.
- Manage courses and study materials.
- Extract chapter and workload information from uploaded files.
- Define weekly and exception availability.
- Generate deterministic study schedules based on exam dates and course weight.
- Track study progress and study streaks.
- Export study sessions as ICS calendar files.
- Show simple recommendations for study priorities.

## 3. Target users
- University students.
- Administrative staff managing user accounts.

## 4. Roles
- Student: can manage personal courses, files, availability, sessions, and dashboard.
- Admin: can list users, search for accounts, and delete users after confirmation.

## 5. MVP scope
The MVP includes user auth, course CRUD, upload processing for PDF/Markdown/PPTX, chapter management, availability management, planner generation, progress tracking, dashboard summaries, admin dashboard, calendar export, and automated tests.

## 6. Core business rules
- Completed sessions are immutable.
- Active plans exclude archived courses.
- Student data stays isolated to the owning account.
- Admin endpoints require explicit admin privilege checks.
- The planner must never create overlapping sessions or impossible capacity.
- Uploaded chapter estimates are based on extracted word counts at approximately 1,000 words per study hour, with a 30-minute minimum; scheduling uses the resulting minute-level estimate.
- Study sessions must end by the course's exam timestamp, including when the exam is on the current planning day.
- Missed sessions remain historical records and are eligible for replanning; completed sessions are immutable.
- A streak advances only on a scheduled day with at least one completed session. Unscheduled days do not break the streak, and future dates are ignored.
- The deployment `TIMEZONE` setting defines local streak-day boundaries; per-student timezone preferences are outside the current MVP implementation.
- Uploaded files are private, type-checked, size-limited, and stored beneath the configured upload directory. Archiving removes the file but retains completed study history.
- Administrator credentials are provisioned only from environment settings. The app does not ship a default administrator password.

## 7. Database design
The application uses SQLite with SQLAlchemy. Core entities include User, Course, Chapter, WeeklyAvailability, AvailabilityException, StudySession, AdminAuditLog, and supporting relations for ownership and file metadata.

`User` stores the role and opaque expiring session token. `Course` owns ordered chapters and retains archived course history. `StudySession` records planned, completed, and missed work. Account deletion removes the user's uploads and related database records; administrator audit entries do not contain the deleted user's email.

## 8. API contract
The backend exposes APIs under `/api` for auth, courses, chapters, availability, planning, study sessions, dashboards/progress, calendar export, uploads, and admin management. Student resources are ownership-checked.

- `GET /dashboard` and `GET /progress` return overall and per-course completion, completed-session counts, study time in the previous seven days, and current/longest streaks.
- `POST /plan/generate` persists a new plan without deleting completed sessions. Plans use the student's weekly availability and offline exceptions.
- `GET /sessions` lists owned sessions; `POST /sessions/{id}/complete` records completion. Completed sessions cannot be modified.
- `POST /courses/{id}/upload` validates and privately stores supported files, extracts chapters, and adds them to the course.
- `GET /calendar.ics` exports the authenticated student's planned sessions.
- Admin-only `GET /admin/dashboard` and `/admin/users` provide account/usage summaries and user search; destructive actions are audited.
- `POST /sessions/{id}/miss` records an ended session as missed.
- `GET /plan.ics` exports planned sessions; `/calendar.ics` remains as a compatibility alias.

## 9. Technical architecture
- Frontend: Streamlit
- Backend: FastAPI
- Planner: independent pure Python engine
- Database: SQLite + SQLAlchemy
- File processing: pypdf, python-pptx, Markdown parsing
- Calendar export: icalendar
- Security: Argon2id hashing, env-based secrets, private uploads, ownership checks
- Containerization: Docker Compose with persistent database and upload storage

## 10. Security requirements
- Passwords stored as Argon2id hashes.
- Admin accounts initialized from environment variables.
- File validation for extension, size, content type, and safe storage.
- SQLite foreign keys enabled.
- No direct exposure of uploaded private content.

## 11. Testing strategy
Automated tests cover auth, user management, course CRUD, availability handling, planner output, dashboard calculations, calendar export, and permissions.

Additional focused tests cover word-based estimates, same-day exam cutoffs, course replanning, local-time streak rules, private-file cleanup, and historical-session preservation.

## 12. Acceptance criteria
The application is considered complete when the implemented MVP supports registration, login, course management, file upload and extraction, availability setup, planning, dashboard progress display, admin actions, and secure API behavior with working tests.

### Current implementation status
- Implemented: student/admin authentication and authorization, course CRUD and archive, private material uploads, editable chapter data, weekly availability and offline exceptions, deterministic plan generation, manual completion/missed states, progress and streak summaries, dashboard calendar, ICS export, admin user search/deletion, and automated tests.
- Partial: timezone handling uses one deployment-wide timezone rather than a per-user IANA preference; recurring scheduling is not fully DST-aware. Chapter nesting and drag-and-drop ordering are not exposed in the UI. Pomodoro and user-defined break preferences are not implemented. Account deletion removes historical records as well as active data for privacy.
- Operations: database initialization uses `create_all` and does not provide schema migrations for existing installations.

## 13. Future improvements
- More advanced drag-and-drop scheduling.
- Real collaborative features.
- School-wide cohort analytics.
- AI-assisted study guidance.

## 14. Out of scope for the MVP
- Multiple examinations per course.
- Assignment management.
- Native mobile app.
- External AI/ML integration.
