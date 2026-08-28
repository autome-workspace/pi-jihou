FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY audio_agent ./audio_agent

# Standard library only; no pip install required.
EXPOSE 8031

CMD ["python", "-m", "audio_agent"]
