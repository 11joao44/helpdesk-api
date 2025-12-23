from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.deals import DealModel
from app.models import ActivityModel

class DealRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_deals_for_kanban(self):
        stmt = (
            select(DealModel)
            .options(selectinload(DealModel.activities).selectinload(ActivityModel.files))
            .order_by(DealModel.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().all()


    async def get_by_deal_id(self, deal_id: int) -> DealModel | None:
        result = await self.session.execute(select(DealModel).where(DealModel.deal_id == deal_id))
        return result.scalar_one_or_none()
    
    async def get_deal_by_id(self, user_id: int, deal_id: int) -> Sequence[DealModel]:
        query = (
            select(DealModel)
            .where(DealModel.user_id == user_id)
            .where(DealModel.deal_id == deal_id)
            .options(selectinload(DealModel.activities).selectinload(ActivityModel.files))
            .order_by(DealModel.created_at.desc())
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_deals_by_user_id(self, user_id: int) -> Sequence[DealModel]:
        query = (
            select(DealModel)
            .where(DealModel.user_id == user_id)
            .options(selectinload(DealModel.activities).selectinload(ActivityModel.files))
            .order_by(DealModel.created_at.desc())
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_deals_by_user_id_open(self, user_id: int) -> Sequence[DealModel]:
        query = (
            select(DealModel)
            .where(DealModel.closed != "Y")
            .where(DealModel.user_id == user_id)
            .options(selectinload(DealModel.activities).selectinload(ActivityModel.files))
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
        
        if deal:
            # Atualiza campos existentes dinamicamente
            for key, value in data.items():
                if hasattr(deal, key):
                    setattr(deal, key, value)
        else:
            # Cria novo
            deal = DealModel(**data)
            self.session.add(deal)
            
        await self.session.flush() # Gera o ID sem fechar a transação
        return deal

