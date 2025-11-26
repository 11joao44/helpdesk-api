from sys import stderr
from loguru import logger
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict

logger.remove()
logger.add(stderr, level="DEBUG", colorize=True, format="<green>{time:HH:mm:ss}</green> [<level>{level}</level>][<blue>{name}</blue>]<green>{function}</green>><green>{line}</green>: <level>{message}</level>")



# class Settings(BaseSettings):
#     BITRIX_WEBHOOK_URL: str
#     ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
#     TIMEOUT_REQUEST: int = 15.0
#     PG_CARVALIMA_HELPDESK_DBNAME: str
#     PG_BOTAPP_PASSWORD: str
#     PG_BOTAPP_HOST: str
#     PG_BOTAPP_USER: str
#     PG_BOTAPP_PORT: str

#     model_config = SettingsConfigDict(env_file=None, env_file_encoding="utf-8")

try:
    settings =  {
        "BITRIX_WEBHOOK_URL": getenv("BITRIX_WEBHOOK_URL"),
        "ALGORITHM": "HS256",
        "TIMEOUT_REQUEST" : 15.0,
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        "PG_CARVALIMA_HELPDESK_DBNAME": getenv("PG_CARVALIMA_HELPDESK_DBNAME"),
        "PG_BOTAPP_HOST": getenv("PG_BOTAPP_HOST"),
        "PG_BOTAPP_PASSWORD": getenv("PG_BOTAPP_PASSWORD"),
        "PG_BOTAPP_PORT": getenv("PG_BOTAPP_PORT"),
        "PG_BOTAPP_USER": getenv("PG_BOTAPP_USER"),
    }

    DATABASE_URL = f"postgresql+asyncpg://{settings.PG_BOTAPP_USER}:{quote_plus(settings.PG_BOTAPP_PASSWORD)}@{settings.PG_BOTAPP_HOST}:{settings.PG_BOTAPP_PORT}/{settings.PG_CARVALIMA_HELPDESK_DBNAME}"
except Exception as e:
    logger.error(f"Erro carregando Settings (Variável de ambiente faltando?): {e}")
    raise