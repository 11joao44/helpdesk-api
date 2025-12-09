from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.models.deals import DealModel # ou TicketModel se já renomeou
from app.providers.bitrix import BitrixProvider
from app.repositories.deals import DealRepository
from app.schemas.tickets import TicketCreateRequest

class DealService:
    def __init__(self, session: AsyncSession):
        # Instanciamos o provider aqui ou recebemos via injeção
        self.repo = DealRepository(session)
        self.bitrix = BitrixProvider() 

    async def create_ticket(self, data: TicketCreateRequest) -> DealModel:
        deal_id = await self.bitrix.create_deal(data)
        
        if not deal_id: raise Exception("Falha de comunicação com Bitrix24")

        print("ID do novo ticket no bitrix: ", deal_id)

        new_deal = DealModel(
            deal_id=deal_id,
            user_id=data.user_id,
            title=data.title,
            description=data.description, 
            stage_id="C25:NEW",
        )
        
        self.repo.session.add(new_deal)
        await self.repo.session.commit()
        await self.repo.session.refresh(new_deal)
        
        return new_deal