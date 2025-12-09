from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from app.models import ActivityModel

class ActivityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


    async def get_by_activity_id(self, b_id: int) -> ActivityModel | None:
        result = await self.session.execute(select(ActivityModel).where(ActivityModel.activity_id == b_id))
        return result.scalar_one_or_none()


    async def get_activity_internal_id(self, activity_id: int) -> int | None:
        """Busca o ID interno (PK) baseado no ID do Bitrix"""
        activity = await self.get_by_activity_id(activity_id)
        return activity.id if activity else None


    async def upsert_ticket(self, data: dict) -> ActivityModel:
        ticket = await self.get_by_activity_id(data["activity_id"])
        if ticket:
            for key, value in data.items():
                if hasattr(ticket, key): setattr(ticket, key, value)
        else:
            ticket = ActivityModel(**data)
            self.session.add(ticket)
        await self.session.flush()
        return ticket


    async def upsert_activity(self, data: dict) -> ActivityModel:
        stmt = select(ActivityModel).where(ActivityModel.activity_id == data["activity_id"])
        result = await self.session.execute(stmt)
        activity = result.scalar_one_or_none()
        
        if activity:
            for key, value in data.items():
                if hasattr(activity, key):
                    setattr(activity, key, value)
        else:
            activity = ActivityModel(**data)
            self.session.add(activity)
            
            try:
                await self.session.flush()
            except IntegrityError:
                await self.session.rollback()
                result = await self.session.execute(stmt)
                activity = result.scalar_one() # Agora TEM que existir
                
                for key, value in data.items():
                    if hasattr(activity, key):
                        setattr(activity, key, value)
                        
        return activity
