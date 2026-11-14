FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Зависимости — отдельным слоем, до копирования кода.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Код — последним, он меняется чаще всего
COPY README.md ./
COPY src/ ./src/
RUN uv sync --frozen --no-dev

# Процесс не должен работать от root
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8080

ARG APP_VERSION=0.0.0-dev
ENV APP_VERSION=$APP_VERSION

CMD ["python", "-m", "booking"]