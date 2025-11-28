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

    # app/main.py (ou similar)

    origins = [
        "http://localhost:5173",      # Seu Frontend Local (Vite)
        "http://127.0.0.1:5173",      # Alternativa local
        "https://carvalima-helpdesk.carvalima-teste.duckdns.org:8086/" # Produção (quando subir)
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app