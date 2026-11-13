# StudyPlan

StudyPlan helps students organize courses, estimate workload, and build study schedules around exam dates and weekly availability. The Streamlit frontend communicates with a FastAPI REST backend; planning logic is kept in the framework-independent `planner` package.

## Features

- Create and manage courses, exam dates, and workload.
- Generate or refresh a study plan based on course deadlines and availability.
- Track completed study sessions, progress, and study history.
- Upload course materials and edit the chapters extracted from them.
- Download planned sessions as an iCalendar (`.ics`) file.

Workload estimates from uploaded text are approximate: the estimator uses word count, at about 1,000 words per study hour, with a 30-minute minimum per chapter.

## Run locally (Windows)

Use Python 3.11 or newer. From the project root, create a virtual environment and install dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Set `ADMIN_EMAIL` and `ADMIN_PASSWORD` in the local `.env` file before starting the backend if you need an administrator account. There are no default admin credentials. Keep `.env` private and do not commit it.

Start the backend in one PowerShell window:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Start the frontend in a second window:

```powershell
$env:BACKEND_BASE_URL = "http://127.0.0.1:8000"
.\.venv\Scripts\python.exe -m streamlit run frontend\app.py --server.address 127.0.0.1 --server.port 8501
```

Open [http://localhost:8501](http://localhost:8501). The backend health endpoint is [http://localhost:8000/health](http://localhost:8000/health).

Alternatively, run both services with Docker Compose:

```powershell
docker compose up --build
```

## Upload course materials

1. Open **Courses**, create or select a course, and use **Upload course material**.
2. Upload a PDF, Markdown (`.md`), or PowerPoint (`.pptx`) file.
3. Choose **Upload and extract chapters**. The backend validates and processes the file, then adds extracted chapters to the selected course.
4. Expand the course to edit chapter titles, workload, study minutes, order, and notes, or add and remove chapters.

The backend upload limit is controlled by `MAX_UPLOAD_SIZE_MB` (20 MB in the provided Docker Compose configuration). Files are stored in the configured private upload directory; the default is `storage/uploads`.

## Tests

Run the automated test suite from the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

