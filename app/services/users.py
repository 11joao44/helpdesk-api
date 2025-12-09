from typing import Any, Dict
from fastapi import HTTPException, status
from app.core.security import create_reset_token
from app.repositories.users import UserRepository
from app.models import UserModel
from app.schemas.users import ChackAvailability, ForgotPasswordRequest, ResetPasswordRequest, UserLogin, UserOut, UserRegister
from app.core.config import settings
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from bcrypt import gensalt, hashpw, checkpw


from app.services.send_email import send_reset_password_email
from app.utils import not_found

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        
    async def get_by_id(self, id: int) -> UserModel:
        user = await self.user_repo.get_by_id(id)
        not_found(user, UserModel, id)
        return user
    
    async def create(self, data: UserRegister) -> UserModel:
        if await self.user_repo.get_by_cpf(data.cpf):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CPF já cadastrado.")
            
        if await self.user_repo.get_by_email(data.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado.")
        
        if await self.user_repo.get_by_matricula(data.matricula):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Matricula já cadastrada.")
        
        user = UserModel(
            full_name = data.full_name,
            email = data.email,
            hashed_password = self.hash_password(data.password),
            department = data.department,
            filial = data.filial,
            cpf = data.cpf,
            matricula = data.matricula
        )
         
        return await self.user_repo.create(user)

    async def update(self, id: int, data: UserRegister) -> UserModel:
        user = await self.user_repo.get_by_id(id)
        not_found(user, UserModel, id)
        return await self.user_repo.update(user, data)

    async def delete(self, id: int) -> None:
        user = await self.user_repo.get_by_id(id)
        not_found(user, UserModel, id)
        await self.user_repo.delete(user)

    def hash_password(self, password: str) -> str:
        return hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')

    def verify_password(self,  plain_password: str, hashed_password: str) -> bool:
        return checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    async def login(self, data: UserLogin) -> Dict[str, Any]:
        user = await self.user_repo.get_by_matricula(data.matricula)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matricula não encontrado")

        if not self.verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas.")
            
        return {
            "token": {
                "access_token": self.create_access_token({"sub": user.id}),
                "refresh_token": self.create_refresh_token({"sub": user.id}),
                "token_type": "bearer",
            },
            "user": UserOut.model_validate(user)
        }

    async def refresh_token(self, refresh_token: str) -> str:
        try:
            payload = jwt.decode(refresh_token, settings['SECRET_KEY'], settings['ALGORITHM'])

            if payload.get("type") != "refresh":
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de refresh inválido ou expirado.")

            user_id = payload.get("sub")

            if not user_id:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de refresh inválido ou expirado.")

            if not await self.user_repo.get_by_id(int(user_id)):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não existe ou está desativado.")

            return self.create_access_token({"sub": user_id})

        except JWTError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de refresh inválido ou expirado." )
        
    def create_access_token(self, data: dict, expire_delta: int = 30) -> str:
        to_encode = data.copy()
        to_encode["sub"] = str(to_encode.get("sub"))

        now = datetime.now(timezone.utc)
        to_encode.update({"exp": now + timedelta(minutes=expire_delta), "iat": now, "nbf": now})

        return jwt.encode(to_encode, settings['SECRET_KEY'], settings['ALGORITHM'])

    def create_refresh_token(self, data: dict, expire_delta: int = 7 * 24 * 60) -> str:
        to_encode = data.copy()
        to_encode["sub"] = str(to_encode.get("sub"))

        now = datetime.now(timezone.utc)
        to_encode.update({"exp": now + timedelta(minutes=expire_delta), "type": "refresh", "iat": now, "nbf": now})

        return jwt.encode(to_encode, settings['SECRET_KEY'], settings['ALGORITHM'])
    
    async def forgot_password(self, data: ForgotPasswordRequest):
        user = await self.user_repo.get_by_email(data.email)
        if not user: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="E-mail não encontrado")
        token = create_reset_token(user.email)
        await self.user_repo.set_reset_token(user, token)
        send_reset_password_email(user.email, token)
        return {"detail": "E-mail de recuperação enviado."}

    async def reset_password(self, data: ResetPasswordRequest):
            try:
                payload = jwt.decode(data.token, settings['SECRET_KEY'], algorithms=[settings['ALGORITHM']])
                email = payload.get("sub")
                if email is None or payload.get("type") != "reset":
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido")
            except JWTError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido ou expirado")

            user = await self.user_repo.get_by_email(email)
            if not user:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")

            if user.password_reset_token != data.token:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este link de recuperação já foi utilizado ou é inválido.")

            await self.user_repo.update_password(user, self.hash_password(data.new_password))
            return {"detail": "Senha atualizada com sucesso!"}
    
    async def chack_availability(self, data: ChackAvailability):
        if data.field == "cpf":
            if await self.user_repo.get_by_cpf(data.value):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CPF já cadastrado.")
            
        if data.field == "email":
            if await self.user_repo.get_by_email(data.value):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado.")
            
        if data.field == "matricula":
            if await self.user_repo.get_by_matricula(data.value):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Matricula já cadastrada.")
        
