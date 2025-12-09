from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr
from sqlalchemy.future import select
from app.models import UserModel
from app.schemas.users import UserDetailsSchema

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


    async def get_by_id(self, id: int) -> UserModel | None:
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == id)
        )
        return result.scalar_one_or_none()


    async def get_by_matricula(self, matricula: str) -> UserModel | None:
        result = await self.session.execute(
            select(UserModel).where(UserModel.matricula == matricula)
        )
        return result.scalar_one_or_none()


    async def get_by_email(self, email: EmailStr) -> UserModel | None:
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        return result.scalar_one_or_none()


    async def get_by_cpf(self, cpf: str) -> UserModel | None:
        result = await self.session.execute(
            select(UserModel).where(UserModel.cpf == cpf)
        )
        return result.scalar_one_or_none()


    async def create(self, data: UserModel) -> UserModel:
        self.session.add(data)
        await self.session.commit()
        await self.session.refresh(data)
        return data


    async def update(self, base_data: UserModel, update_data: UserDetailsSchema) -> UserModel:
        for key, value in update_data.model_dump(exclude_unset=True).items():
            setattr(base_data, key, value)
        await self.session.commit()
        await self.session.refresh(base_data)
        return base_data


    async def update_password(self, user: UserModel, new_hash_password) -> None:
        user.hashed_password = new_hash_password
        user.password_reset_token = None
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)


    async def set_reset_token(self, user: UserModel, token: str) -> None:
        user.password_reset_token = token
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)


    async def delete(self, user: UserModel) -> None:
        await self.session.delete(user)
        await self.session.commit()