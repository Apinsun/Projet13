FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (Stockfish)
RUN apt-get update && apt-get install -y --no-install-recommends \
    stockfish \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==2.2.1

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies (no venv, directly in system)
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# Copy application
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
