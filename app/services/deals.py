from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.deals import DealModel
from app.providers.bitrix import BitrixProvider
from app.repositories.deals import DealRepository
from app.schemas.tickets import TicketCloseRequest, TicketCreateRequest, TicketSendEmail

class DealService:
    def __init__(self, session: AsyncSession):
        # Instanciamos o provider aqui ou recebemos via injeção
        self.repo = DealRepository(session)
        self.bitrix = BitrixProvider()

    async def close_ticket(self, data: TicketCloseRequest):
        provider = BitrixProvider()
        
        bitrix_success = await provider.close_deal(
            deal_id=data.deal_id, 
            rating=data.rating,
            comment=data.comment
        )

        if not bitrix_success:
             return {"status": "error", "message": "Falha ao atualizar no Bitrix"}
        
        return {"status": "success", "message": "Chamado encerrado com sucesso"}


    async def send_email(self, data: TicketSendEmail):
        return await self.bitrix.send_email(data.deal_id, data.subject, data.message, data.to_email, data.from_email)


    async def create_ticket(self, data: TicketCreateRequest) -> DealModel:
        deal_id = await self.bitrix.create_deal(data)
        
        if not deal_id: raise Exception("Falha de comunicação com Bitrix24")

        new_deal = DealModel(
            deal_id=deal_id,
            user_id=data.user_id,
            title=f"[{datetime.now().strftime("%Y%m%d")}{deal_id}] {data.title}",
            description=data.description, 
            stage_id="C25:NEW",
            opened="Y",
            closed="N",
            begin_date=datetime.now(),
            created_by_id=data.resp_id,
            requester_department=data.requester_department,
            assignee_department=data.assignee_department,
            service_category=data.service_category,
            system_type=data.system_type,
            priority=data.priority,
            matricula=data.matricula,
        )
        
        self.repo.session.add(new_deal)
        await self.repo.session.commit()
        await self.repo.session.refresh(new_deal)
        return new_deal
