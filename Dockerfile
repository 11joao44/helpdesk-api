# syntax=docker/dockerfile:1

########################################
# Etapa 1: Builder (Compilação e Dependências)
########################################
# Recomendo usar 3.12 pois 3.14 ainda é instável/alpha para muitas libs
FROM python:3.12-slim AS builder

# Instala o uv (método oficial mais rápido)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /code

# Variáveis de ambiente para o build
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Dependências de sistema para compilar (se necessário para libs C)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia arquivos de dependência
COPY pyproject.toml uv.lock ./

# Instala dependências no ambiente virtual (.venv é criado automaticamente pelo uv)
# --no-install-project: Não instala o seu código ainda, só as libs (melhora cache)
RUN uv sync --frozen --no-dev --no-install-project

########################################
# Etapa 2: Runtime (Imagem Final Leve)
########################################
FROM python:3.12-slim AS runtime

WORKDIR /code

# Instala apenas deps de runtime (curl para healthcheck, libpq para postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Cria usuário não-root
RUN useradd -m appuser

# Copia o ambiente virtual criado na etapa anterior
COPY --from=builder /code/.venv /code/.venv

# Copia o código da aplicação
COPY . .

# Ajusta permissões
RUN chown -R appuser:appuser /code

# Define o usuário para execução
USER appuser

# Adiciona o venv ao PATH (Isso "ativa" o ambiente virtual automaticamente)
ENV PATH="/code/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    UVICORN_WORKERS=4 \
    PORT=8024

# Porta exposta
EXPOSE 8024

# Healthcheck (Verifica se a API está respondendo)
# HEALTHCHECK --interval=30s --timeout=5s --start-period=5s \
#     CMD curl -f http://localhost:8024/ || exit 1

# Comando de execução
# Como seu main.py está na raiz, usamos "main:app"
ENTRYPOINT ["sh", "-c"]
CMD ["uvicorn main:app --host 0.0.0.0 --port 8024 --workers $UVICORN_WORKERS --proxy-headers"]