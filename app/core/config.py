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
        "SECRET_KEY": getenv("HELPDESK_SECRET_KEY"),
        "TIMEOUT_REQUEST": 15.0,
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        "HELPDESK_DB_DBNAME_1": getenv("HELPDESK_DB_DBNAME_1"),
        "HELPDESK_DB_HOST_1": getenv("HELPDESK_DB_HOST_1"),
        "HELPDESK_DB_USER_1": getenv("HELPDESK_DB_USER_1"),
        "HELPDESK_DB_PASSWORD_1": getenv("HELPDESK_DB_PASS_1"),
        "HELPDESK_DB_PORT_1": getenv("HELPDESK_DB_PORT_1"),

        "HELPDESK_DB_DBNAME_2": getenv("HELPDESK_DB_DBNAME_2"),
        "HELPDESK_DB_HOST_2": getenv("HELPDESK_DB_HOST_2"),
        "HELPDESK_DB_USER_2": getenv("HELPDESK_DB_USER_2"),
        "HELPDESK_DB_PASSWORD_2": getenv("HELPDESK_DB_PASS_2"),
        "HELPDESK_DB_PORT_2": getenv("HELPDESK_DB_PORT_2"),

        "HELPDESK_DB_DBNAME_3": getenv("HELPDESK_DB_DBNAME_3"),
        "HELPDESK_DB_HOST_3": getenv("HELPDESK_DB_HOST_3"),
        "HELPDESK_DB_USER_3": getenv("HELPDESK_DB_USER_3"),
        "HELPDESK_DB_PASSWORD_3": getenv("HELPDESK_DB_PASS_3"),
        "HELPDESK_DB_PORT_3": getenv("HELPDESK_DB_PORT_3"),

        "WEBMAIL_USUARIO": getenv("WEBMAIL_USUARIO"),
        "WEBMAIL_SENHA": getenv("WEBMAIL_SENHA"),
        "BITRIX_INBOUND_URL": getenv("BITRIX_INBOUND_URL"),
        "MINIO_ENDPOINT": getenv("IP_SERVIDOR_NFS"),
        "MINIO_ACCESS_KEY": getenv("MINIO_USER"),
        "MINIO_SECRET_KEY": getenv("MINIO_SENHA"),
    }
    
    DATABASE_CONFIGS = []
    for i in range(1, 4):
        if settings.get(f"HELPDESK_DB_HOST_{i}"):
            DATABASE_CONFIGS.append({
                "user": settings[f"HELPDESK_DB_USER_{i}"],
                "password": settings[f"HELPDESK_DB_PASSWORD_{i}"],
                "host": settings[f"HELPDESK_DB_HOST_{i}"],
                "port": settings[f"HELPDESK_DB_PORT_{i}"],
                "dbname": settings[f"HELPDESK_DB_DBNAME_{i}"],
            })
except Exception as e:
    logger.error(f"Erro carregando Settings (Variável de ambiente faltando?): {e}")
    raise
