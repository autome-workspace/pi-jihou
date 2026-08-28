FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
COPY audio_agent ./audio_agent

RUN pip install --no-cache-dir .

EXPOSE 8031

CMD ["uvicorn", "audio_agent.main:app", "--host", "0.0.0.0", "--port", "8031"]
