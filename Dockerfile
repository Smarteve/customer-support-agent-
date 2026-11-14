FROM ghcr.io/astral-sh/uv:0.13.0 AS uv
FROM python:3.12-slim AS base
COPY --from=uv /uv /uvx /bin/
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev && useradd --create-home --uid 10001 app
ENV PATH="/app/.venv/bin:$PATH"

FROM base AS runtime
USER app
CMD ["python", "-m", "support_engine.simulator"]

FROM base AS test
RUN uv sync --frozen
COPY tests ./tests
USER app
CMD ["pytest", "-q"]
