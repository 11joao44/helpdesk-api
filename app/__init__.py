from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings, logger
from app.routes import create_routes
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    logger.info("🚀 Subindo aplicação Helpdesk...")
    # Aqui você pode inicializar conexões de banco, Redis, ou carregar ML models
    yield
    # --- SHUTDOWN ---
    logger.info("🛑 Desligando aplicação...")

def create_app() -> FastAPI:
    """
    Application Factory: Cria e configura a instância do FastAPI.
    """
    app = FastAPI(
        title="Carvalima Helpdesk API",
        description="API de chamados integrada ao Bitrix24",
        version="1.0.0",
        # openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan
    )

    create_routes(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # Em produção trocar pelo domínio do React
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app