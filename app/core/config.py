from sys import stderr
from loguru import logger
from urllib.parse import quote_plus
from dotenv import load_dotenv
from os import getenv

load_dotenv()

logger.remove()
logger.add(
    stderr,
    level="DEBUG",
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> [<level>{level}</level>][<blue>{name}</blue>]<green>{function}</green>><green>{line}</green>: <level>{message}</level>",
)

try:
    settings = {
        "ALGORITHM": "HS256",
        "SECRET_KEY": "564546897789879asd",
        "TIMEOUT_REQUEST": 15.0,
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        "PG_CARVALIMA_HELPDESK_DBNAME": getenv("PG_CARVALIMA_HELPDESK_DBNAME"),
        "PG_BOTAPP_HOST": getenv("PG_BOTAPP_HOST"),
        "PG_BOTAPP_PASSWORD": getenv("PG_BOTAPP_PASSWORD"),
        "PG_BOTAPP_PORT": getenv("PG_BOTAPP_PORT"),
        "PG_BOTAPP_USER": getenv("PG_BOTAPP_USER"),
        "WEBMAIL_USUARIO": getenv("WEBMAIL_USUARIO"),
        "WEBMAIL_SENHA": getenv("WEBMAIL_SENHA"),
        "BITRIX_INBOUND_URL": getenv("BITRIX_INBOUND_URL"),
    }
    DATABASE_URL = f"postgresql+asyncpg://{settings["PG_BOTAPP_USER"]}:{quote_plus(settings["PG_BOTAPP_PASSWORD"])}@{settings["PG_BOTAPP_HOST"]}:{settings["PG_BOTAPP_PORT"]}/{settings["PG_CARVALIMA_HELPDESK_DBNAME"]}"
except Exception as e:
    logger.error(f"Erro carregando Settings (Variável de ambiente faltando?): {e}")
    raise
