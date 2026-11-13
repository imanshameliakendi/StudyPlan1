from __future__ import annotations

import hashlib
import math
import re
import shutil
from io import BytesIO
from pathlib import Path
from typing import List
from zipfile import BadZipFile, ZipFile, is_zipfile

from pptx import Presentation
from pypdf import PdfReader

from backend.config import settings

ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".md": "text/markdown",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}
WORDS_PER_STUDY_HOUR = 1000
MIN_ESTIMATED_STUDY_MINUTES = 30
_CHAPTER_HEADING_RE = re.compile(r"^(chapter|unit|module|part)\s+\d+\b", re.IGNORECASE)
_WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)


def safe_filename(name: str) -> str:
    return hashlib.sha256(name.encode("utf-8")).hexdigest() + Path(name).suffix.lower()


def validate_file_content(filename: str, file_bytes: bytes) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type")
    if suffix == ".pdf" and not file_bytes.startswith(b"%PDF-"):
        raise ValueError("The file content does not match a PDF document")
    if suffix == ".md":
        try:
            text = file_bytes.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("Markdown files must use UTF-8 text encoding") from exc
        if "\x00" in text:
            raise ValueError("Markdown files must contain readable text")
    if suffix == ".pptx":
        if not is_zipfile(BytesIO(file_bytes)):
            raise ValueError("The file content does not match a PowerPoint presentation")
        try:
            with ZipFile(BytesIO(file_bytes)) as archive:
                names = set(archive.namelist())
        except BadZipFile as exc:
            raise ValueError("The PowerPoint file is corrupted") from exc
        if "[Content_Types].xml" not in names or "ppt/presentation.xml" not in names:
            raise ValueError("The file content does not match a PowerPoint presentation")


def extract_text_from_file(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix == ".md":
        return file_path.read_text(encoding="utf-8")
    if suffix == ".pptx":
        presentation = Presentation(str(file_path))
        chunks = []
        for slide in presentation.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text:
                    chunks.append(shape.text)
        return "\n".join(chunks)
    raise ValueError("Unsupported file format")


def delete_private_file(file_path: str | None) -> None:
    if not file_path:
        return
    root = settings.UPLOAD_DIR.resolve()
    path = Path(file_path).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("Refusing to delete a file outside private storage") from exc
    if path.is_file():
        path.unlink()


def delete_user_uploads(user_id: int) -> None:
    root = settings.UPLOAD_DIR.resolve()
    user_directory = (root / str(user_id)).resolve()
    try:
        user_directory.relative_to(root)
    except ValueError as exc:
        raise ValueError("Refusing to delete a directory outside private storage") from exc
    if user_directory.is_dir():
        shutil.rmtree(user_directory)


def estimate_chapters(text: str) -> List[dict]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    sections: list[tuple[str, list[str]]] = []
    title = "Chapter 1"
    content: list[str] = []

    for line in lines:
        is_heading = (
            line.startswith("#")
            or (line.isupper() and any(character.isalpha() for character in line))
            or _CHAPTER_HEADING_RE.match(line) is not None
        )
        if is_heading:
            if content:
                sections.append((title, content))
            title = line.lstrip("# ").rstrip("# ").strip()
            content = []
        else:
            content.append(line)

    if content:
        sections.append((title, content))

    chapters = []
    for title, section_lines in sections:
        word_count = len(_WORD_RE.findall(" ".join(section_lines)))
        if not word_count:
            continue
        study_minutes = max(
            MIN_ESTIMATED_STUDY_MINUTES,
            math.ceil(word_count * 60 / WORDS_PER_STUDY_HOUR),
        )
        chapters.append({
            "title": title,
            "workload_hours": math.ceil(study_minutes / 60),
            "study_minutes": study_minutes,
        })
    return chapters
