from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import Request, HTTPException, status
from app.core.config import logger, settings

async def get_current_user_id(request: Request):
    logger.info("auth_required: Iniciando verificação de token")
    
    access_token = request.cookies.get("access_token")
    logger.debug(f"Token recebido: {access_token}")

    if not access_token:
        logger.warning("Token não fornecido.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido BACK-END"
        )

    try:
        payload = jwt.decode(access_token, settings["SECRET_KEY"], algorithms=["HS256"])
        logger.debug(f"Payload decodificado: {payload}")
        
        user_id = payload.get("user_id")
        
        if user_id is None:
            logger.error("Token não contém user_id")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: user_id ausente"
            )

        logger.info(f"auth_required: Token válido para user_id testand rota delete: {user_id}")
        return user_id

    except ExpiredSignatureError as e:
        logger.error(f"Token expirado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Token expirado", "details": str(e)}
        )
    except JWTError as e:
        logger.error(f"Token inválido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Token inválido", "details": str(e)}
        )
    except Exception as e:
        logger.exception("Erro desconhecido ao decodificar o token.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Erro desconhecido", "details": str(e)}
        )