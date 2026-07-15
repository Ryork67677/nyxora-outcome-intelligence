FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY sql ./sql
COPY artifacts ./artifacts

RUN python -m pip install --no-cache-dir .

EXPOSE 8000

ENV NYXORA_PROJECT_ROOT=/app

CMD ["sh", "-c", "nyxora-intel build --root /app --skip-dashboard-package && nyxora-intel serve --host 0.0.0.0 --port 8000"]
