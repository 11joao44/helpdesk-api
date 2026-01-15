from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from app.core.config import settings, DATABASE_CONFIGS, quote_plus
import socket
from loguru import logger

Base = declarative_base()

def get_active_database_url():
    for config in DATABASE_CONFIGS:
        host = config["host"]
        port = int(config["port"])
        try:
            with socket.create_connection((host, port), timeout=2):
                logger.info(f"Conectado ao banco de dados: {host}:{port}")
                return f"postgresql+asyncpg://{config['user']}:{quote_plus(config['password'])}@{config['host']}:{config['port']}/{config['dbname']}"
        except (socket.timeout, socket.error):
            logger.warning(f"Falha ao conectar no banco: {host}:{port}")
            continue
    raise Exception("Nenhum banco de dados disponível.")

DATABASE_URL = get_active_database_url()

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

async_session_maker = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def session_db():
    async with async_session_maker() as session:
        yield session