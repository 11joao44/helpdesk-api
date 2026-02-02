from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.deals import DealModel
from app.models.users import UserModel
from app.models import ActivityModel

class DealRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_deals_for_kanban(self):
        stmt = (
            select(DealModel)
            .options(
                selectinload(DealModel.activities).selectinload(ActivityModel.files),
                selectinload(DealModel.files)
            )
            .order_by(DealModel.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().all()


    async def get_by_deal_id(self, deal_id: int) -> DealModel | None:
        result = await self.session.execute(
            select(DealModel)
            .where(DealModel.deal_id == deal_id)
            .options(
                selectinload(DealModel.user),
                selectinload(DealModel.responsible_user_rel),
                selectinload(DealModel.files)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_deal_by_id(self, user_id: int, deal_id: int) -> Sequence[DealModel]:
        query = (
            select(DealModel)
            .where(DealModel.user_id == user_id)
            .where(DealModel.deal_id == deal_id)
            .options(
                selectinload(DealModel.user),
                selectinload(DealModel.responsible_user_rel),
                selectinload(DealModel.activities).selectinload(ActivityModel.files),
                selectinload(DealModel.activities).selectinload(ActivityModel.responsible_user),
                selectinload(DealModel.activities).selectinload(ActivityModel.deal),
                selectinload(DealModel.files)
            )
            .order_by(DealModel.created_at.desc())
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_deals_by_user_id(self, user_id: int) -> Sequence[DealModel]:
        query = (
            select(DealModel)
            .where(DealModel.user_id == user_id)
            .options(
                selectinload(DealModel.user),
                selectinload(DealModel.responsible_user_rel),
                selectinload(DealModel.activities).selectinload(ActivityModel.files),
                selectinload(DealModel.activities).selectinload(ActivityModel.responsible_user),
                selectinload(DealModel.activities).selectinload(ActivityModel.deal),
                selectinload(DealModel.files)
            )
            .order_by(DealModel.created_at.desc())
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_deals_by_user_id_open(self, user_id: int) -> Sequence[DealModel]:
        query = (
            select(DealModel)
            .where(DealModel.closed != "Y")
            .where(DealModel.user_id == user_id)
            .options(
                selectinload(DealModel.user),
                selectinload(DealModel.responsible_user_rel),
                selectinload(DealModel.activities).selectinload(ActivityModel.files),
                selectinload(DealModel.activities).selectinload(ActivityModel.responsible_user),
                selectinload(DealModel.activities).selectinload(ActivityModel.deal),
                selectinload(DealModel.files)
            )
            .order_by(DealModel.created_at.desc())
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()


    async def get_deal_internal_id(self, deal_id: int) -> int | None:
        """Busca o ID interno (PK) baseado no ID do Bitrix"""
        deal = await self.get_by_deal_id(deal_id)
        return deal.id if deal else None


    async def upsert_deal(self, data: dict) -> DealModel:
        deal = await self.get_by_deal_id(data["deal_id"])

        responsible_email = data.get("responsible_email")
        responsible_id = None
        
        if responsible_email:
            # Busca o usuário pelo e-mail para pegar o ID
            result = await self.session.execute(select(UserModel).where(UserModel.email == responsible_email))
            user = result.scalar_one_or_none()
            if user:
                responsible_id = user.id

        if deal:
            # Atualiza campos existentes dinamicamente
            for key, value in data.items():
                if hasattr(deal, key):
                    setattr(deal, key, value)
            
            # Atualiza o responsible_id se encontrado
            if responsible_id:
                deal.responsible_id = responsible_id

        else:
            # Cria novo
            if responsible_id:
                data["responsible_id"] = responsible_id
            
            deal = DealModel(**data)
            self.session.add(deal)
            
        await self.session.flush() # Gera o ID sem fechar a transação
        return deal

    async def get_deals_by_responsible_id(self, user_id: int) -> Sequence[DealModel]:
        query = (
            select(DealModel)
            .where(DealModel.responsible_id == user_id)
            .where(DealModel.closed != "Y")
            .options(
                selectinload(DealModel.user),
                selectinload(DealModel.responsible_user_rel),
                selectinload(DealModel.activities).selectinload(ActivityModel.files),
                selectinload(DealModel.activities).selectinload(ActivityModel.responsible_user),
                selectinload(DealModel.activities).selectinload(ActivityModel.deal),
                selectinload(DealModel.files)
            )
            .order_by(DealModel.created_at.desc())
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def add_files(self, deal_internal_id: int, files_data: list[dict]):
        """Adiciona arquivos a um Deal (ID Interno)"""
        if not files_data: return

        from app.models.deal_files import DealFileModel

        for f in files_data:
            # Garante que o deal_id interno está correto
            f["deal_id"] = deal_internal_id
            
            # Verifica duplicidade simples (pelo bitrix_file_id ou URL)
            stmt = select(DealFileModel).where(DealFileModel.deal_id == deal_internal_id)
            
            if f.get("bitrix_file_id"):
                stmt = stmt.where(DealFileModel.bitrix_file_id == f["bitrix_file_id"])
            elif f.get("file_url"):
                 stmt = stmt.where(DealFileModel.file_url == f["file_url"])
            else:
                # Se não tem nem ID nem URL, pula
                continue

            existing = await self.session.execute(stmt)
            if existing.scalar_one_or_none():
                continue

            new_file = DealFileModel(**f)
            self.session.add(new_file)
            
        await self.session.flush()


    async def mark_as_unread(self, deal_internal_id: int):
        """Marca o Deal como NÃO LIDO (possui novas atividades)."""
        stmt = (
            select(DealModel).where(DealModel.id == deal_internal_id)
        )
        result = await self.session.execute(stmt)
        deal = result.scalar_one_or_none()
        if deal:
            deal.is_unread = True
            await self.session.commit()

    async def mark_as_read(self, deal_internal_id: int):
        """Marca o Deal como LIDO (usuário visualizou)."""
        stmt = (
            select(DealModel).where(DealModel.id == deal_internal_id)
        )
        result = await self.session.execute(stmt)
        deal = result.scalar_one_or_none()
        if deal:
            deal.is_unread = False
            await self.session.commit()
            await self.session.refresh(deal)

