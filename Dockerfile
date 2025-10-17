From python:3.11-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml .
COPY uv.lock .

RUN uv sync

COPY . .

CMD ["uv", "run", "python3", "-m", "src.main"]

