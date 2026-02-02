from typing import Any, Dict
from fastapi import HTTPException, status, UploadFile
from app.core.security import create_reset_token
from app.repositories.users import UserRepository
from app.models import UserModel
from app.models import UserModel
from app.schemas.users import ChackAvailability, ForgotPasswordRequest, ResetPasswordRequest, UserLogin, UserOut, UserRegister, UserSchema
from app.core.config import settings
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from bcrypt import gensalt, hashpw, checkpw


from app.services.send_email import send_reset_password_email
from app.utils import not_found
from app.providers.storage import StorageProvider

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self.storage = StorageProvider()
        
    async def get_by_id(self, id: int) -> UserOut:
        user = await self.user_repo.get_by_id(id)
        not_found(user, UserModel, id)
        
        # Populate avatar URL
        user_out = UserOut.model_validate(user)
        if user.profile_picture:
             user_out.profile_picture_url = self.storage.get_presigned_url(user.profile_picture)
             
        return user_out
    
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
        
    async def update_phone(self, user_id: int, phone_number: str) -> UserOut:
        
        existing_user = await self.user_repo.get_by_phone_number(phone_number)
        if existing_user and existing_user.id != user_id:
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Telefone já cadastrado por outro usuário.")
        
        # 2. Update user
        user = await self.user_repo.get_by_id(user_id)
        not_found(user, UserModel, user_id)
        
        user.phone_number = phone_number
        
        # Save changes (repo.create adds and commits, acting as save/merge for attached objects)
        await self.user_repo.create(user)
        
        return self._prepare_user_out(user)

    def hash_password(self, password: str) -> str:
        return hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')

    def verify_password(self,  plain_password: str, hashed_password: str) -> bool:
        return checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    async def login(self, data: UserLogin) -> Dict[str, Any]:
        login = data.login

        if len(login) == 11:
            user = await self.user_repo.get_by_cpf(login)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CPF não encontrado")
        else:
            user = await self.user_repo.get_by_matricula(login)
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
            "user": self._prepare_user_out(user)
        }
        
    def _prepare_user_out(self, user: UserModel) -> UserOut:
        user_out = UserOut.model_validate(user)
        if user.profile_picture:
            # 7 dias = 168 horas
            user_out.profile_picture_url = self.storage.get_presigned_url(user.profile_picture, expiration_hours=168)
        return user_out

    async def upload_profile_picture(self, user_id: int, file: UploadFile) -> UserOut:
        user = await self.user_repo.get_by_id(user_id)
        not_found(user, UserModel, user_id)

        # 1. Prepare filename
        # Use simple extension extraction
        filename = file.filename or ""
        ext = filename.split(".")[-1] if "." in filename else "jpg"
        object_name_candidate = f"users/{user_id}/profile.{ext}"

        # 2. Upload
        content = await file.read()
        saved_object_name = self.storage.upload_file(content, object_name_candidate)
        
        if not saved_object_name:
             raise HTTPException(status_code=500, detail="Falha ao salvar imagem no storage.")

        # 3. Save to DB
        await self.user_repo.update_profile_picture(user, saved_object_name)
        
        # 4. Return updated user with URL
        return self._prepare_user_out(user)

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
        
    def create_access_token(self, data: dict, expire_delta: int = 10080) -> str:
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
        
        if data.field == "phone_number":
            if await self.user_repo.get_by_phone_number(data.value):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Telefone já cadastrado.")
            
        if data.field == "email":
            if await self.user_repo.get_by_email(data.value):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado.")
            
        if data.field == "matricula":
            if await self.user_repo.get_by_matricula(data.value):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Matricula já cadastrada.")
        
