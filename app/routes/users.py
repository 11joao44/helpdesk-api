from fastapi import APIRouter, HTTPException, Depends, status, Response, Request
from app.models.users import UserModel
from app.repositories.users import UserRepository
from app.services.users import UserService
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import session_db
from app.core.security import  require_admin, get_current_user_from_cookie
from app.schemas.users import (ChackAvailability, ForgotPasswordRequest, LoginResponse, ResetPasswordRequest, UserRegister, UserOut, UserLogin)

router = APIRouter(prefix="/auth", tags=["users"])

def get_service(db: AsyncSession = Depends(session_db)) -> UserService:
    return UserService(UserRepository(db))


@router.get('/users', status_code=status.HTTP_200_OK)
async def get(): 
    return {"data": "Rota /users em funcionamento!"}


@router.get('/users/{user_id}', status_code=status.HTTP_200_OK, response_model=UserOut)
async def list(user_id: int, service: UserService = Depends(get_service),  admin: UserModel = Depends(require_admin)):
    return await service.list(user_id)


@router.post('/users', status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def create(data: UserRegister, service: UserService = Depends(get_service)):
    return await service.create(data)


@router.put('/users/{user_id}', status_code=status.HTTP_200_OK, response_model=UserOut)
async def update(user_id: int, service: UserService = Depends(get_service), admin: UserModel = Depends(require_admin)):
    return await service.update(user_id)


@router.delete('/users/{user_id}', status_code=status.HTTP_200_OK, response_model=UserOut)
async def delete(user_id: int, service: UserService = Depends(get_service), admin: UserModel = Depends(require_admin)):
    return await service.delete(user_id)


# --- ÁREA ALTERADA: LOGIN COM COOKIES ---
@router.post('/login', status_code=status.HTTP_200_OK, response_model=LoginResponse)
async def login(user: UserLogin, response: Response, service: UserService = Depends(get_service)):
    login_data = await service.login(user)
    cookie_params = {
        "httponly": True,
        "secure": True,      # Obrigatório quando samesite="None"
        "samesite": "None",  # Permite Cross-Site
    }


    response.set_cookie(
        key="access_token", 
        value=login_data['token']['access_token'],
        max_age=1800, # 30 min
        **cookie_params
    )

    # 2. Refresh Token
    response.set_cookie(
        key="refresh_token",
        value=login_data['token']['refresh_token'],
        max_age=604800, # 7 dias
        **cookie_params
    )

    return login_data


@router.get("/me")
async def read_users_me(current_user = Depends(get_current_user_from_cookie)):
    return current_user


@router.post('/logout', status_code=status.HTTP_200_OK)
async def logout(response: Response):
    cookie_params = {
        "httponly": True,
        "secure": True,
        "samesite": "None",
    }
    response.delete_cookie(key="access_token", **cookie_params)
    response.delete_cookie(key="refresh_token", **cookie_params)
    return {"message": "Logout realizado com sucesso"}

# --- REFRESH TOKEN (Atualizado para ler Cookie) ---
@router.post('/refresh-token', status_code=status.HTTP_200_OK)
async def refresh_token(request: Request, response: Response, service: UserService = Depends(get_service)):
    refresh_token_str = request.cookies.get("refresh_token")

    if not refresh_token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Refresh token não encontrado nos cookies."
        )
    
    new_tokens = await service.refresh_token(refresh_token_str)

    if not new_tokens:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    new_access_token = new_tokens # ou new_tokens['access_token'] dependendo do retorno

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        max_age=1800,
        httponly=True,
        secure=True,
        samesite="None"
    )
    
    return {"message": "Token atualizado"}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(data: ForgotPasswordRequest, service: UserService = Depends(get_service)):
    return await service.forgot_password(data)


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(data: ResetPasswordRequest, service: UserService = Depends(get_service)):
    return await service.reset_password(data)

@router.get("/check-availability", status_code=status.HTTP_200_OK)
async def chack_availability(data: ChackAvailability = Depends(), service: UserService = Depends(get_service)):
    return await service.chack_availability(data)