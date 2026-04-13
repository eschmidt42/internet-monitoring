# https://hub.docker.com/r/astral/uv
FROM astral/uv:python3.12-bookworm-slim@sha256:f41363eb4bf05a63a61c8a7bc50ab1c5437f4f945ee7de3b0d40f97f2ab7eb12

WORKDIR /app

COPY pyproject.toml .
COPY .python-version .
COPY uv.lock .
RUN uv sync --frozen --no-dev

COPY bridge.py .

EXPOSE 5000

CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "30", "bridge:app"]
