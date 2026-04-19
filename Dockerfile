FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/opt/poetry_cache

RUN pip install --no-cache-dir poetry

WORKDIR /app

COPY backend/pyproject.toml backend/poetry.lock* ./

RUN poetry install --no-root --no-interaction --no-ansi || true

RUN poetry run pip install --no-cache-dir \
    numpy==1.26.4 \
    paddlepaddle==2.6.2 \
    paddleocr==2.8.1

ENV PATH="/app/.venv/bin:$PATH"

COPY backend/ .

COPY entrypoint.py .

EXPOSE 8000

CMD ["python", "entrypoint.py"]
