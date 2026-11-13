FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir --retries 10 --timeout 60 -r requirements.txt

COPY . .
RUN mkdir -p /app/storage/uploads \
    && addgroup --system studyplan \
    && adduser --system --ingroup studyplan --home /home/studyplan studyplan \
    && chown -R studyplan:studyplan /app /home/studyplan

USER studyplan

EXPOSE 8000 8501

CMD ["python", "-m", "backend.main"]
