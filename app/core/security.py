from fastapi import Depends, HTTPException, status, Request
from jose import jwt, JWTError
from app.core.config import settings
from app.models.users import UserModel
from app.core.database import session_db 
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.users import UserRepository

async def get_current_user_from_cookie(request: Request,  db_session: AsyncSession = Depends(session_db)):
    token = request.cookies.get("access_token") 

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado (Token ausente)")

    try:
        payload = jwt.decode(token, settings['SECRET_KEY'], algorithms=[settings['ALGORITHM']])
        token_user_id: str = payload.get("sub") 
        
        if token_user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido (sem sub)")
            
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    
    user = await UserRepository(db_session).get_by_id(int(token_user_id))

    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
    return user

# Dependência de Admin (Reutiliza a anterior)
async def require_admin(user: UserModel = Depends(get_current_user_from_cookie)):
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Ação restrita a administradores."
        )
    return user