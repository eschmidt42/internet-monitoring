# https://hub.docker.com/r/astral/uv
FROM astral/uv:python3.12-bookworm-slim@sha256:f41363eb4bf05a63a61c8a7bc50ab1c5437f4f945ee7de3b0d40f97f2ab7eb12 AS builder

WORKDIR /app

COPY pyproject.toml .python-version uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# https://hub.docker.com/layers/library/python/3.12-bookworm/images/sha256-b56f33e82a8b7ae179eb4210a5297062b60d8e7d9e2faa32a8d8347f236505b2
FROM python:3.12-slim-bookworm@sha256:771f3160ed1c1115f0ed16cc9992b52418a4b12aee65269a1a040767c554d541 AS runtime

RUN adduser --disabled-password --gecos "" appuser

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY bridge.py .

RUN chown -R appuser:appuser /app
USER appuser

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "30", "bridge:app"]
