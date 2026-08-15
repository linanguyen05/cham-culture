# Cham Culture — production image.
# Serves the FastAPI backend AND the frontend SPA from one origin.
# Build context = repo root (vhc/), so both backend/ and frontend/ are available.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# App code + the frontend it serves.
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# Run from backend/ so the `app` package is importable; serve ../frontend.
WORKDIR /app/backend
ENV FRONTEND_DIR=/app/frontend \
    ENVIRONMENT=production

EXPOSE 8000

# Platforms (Render/Railway/Fly) inject $PORT; default to 8000 locally.
# --loop asyncio pins the event loop that psycopg's async mode is validated with.
CMD ["sh", "-c", "uvicorn app:create_app --factory --host 0.0.0.0 --port ${PORT:-8000} --loop asyncio"]
