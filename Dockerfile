FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT="/usr/local" \
    UV_COMPILE_BYTECODE=1

WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

# --frozen: Garante que usa versões exatas do uv.lock (Crucial para produção)
# --no-dev: Não instala pytest, black, etc. (Economiza espaço e segurança)
RUN uv sync --frozen --no-dev

COPY . .

RUN useradd -m appuser && chown -R appuser /code
USER appuser

EXPOSE 8024

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8024", "--proxy-headers"]