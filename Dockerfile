# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /code

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

########################################
# Etapa 2: Runtime (Imagem Final Leve)
########################################
FROM python:3.12-slim AS runtime

WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m appuser

COPY --from=builder /code/.venv /code/.venv

COPY . .

RUN chown -R appuser:appuser /code

USER appuser

ENV PATH="/code/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    UVICORN_WORKERS=1 \
    PORT=8024

EXPOSE 8024

# Healthcheck (Verifica se a API está respondendo)
# HEALTHCHECK --interval=30s --timeout=5s --start-period=5s \
#     CMD curl -f http://localhost:8024/ || exit 1

ENTRYPOINT ["sh", "-c"]
CMD ["uvicorn main:app --host 0.0.0.0 --port 8024 --workers $UVICORN_WORKERS --proxy-headers"]