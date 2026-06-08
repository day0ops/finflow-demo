FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml .
RUN uv sync --no-dev --frozen 2>/dev/null || uv sync --no-dev

COPY . .

RUN mkdir -p /data

ENV PYTHONPATH=/app
ENV DB_PATH=/data/portfolio.db
EXPOSE 8000
CMD ["uv", "run", "python", "server.py"]
