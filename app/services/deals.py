from datetime import datetime, timezone
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
            deal_id=data.deal_id, rating=data.rating, comment=data.comment
        )

        if not bitrix_success:
            return {"status": "error", "message": "Falha ao atualizar no Bitrix"}

        return {"status": "success", "message": "Chamado encerrado com sucesso"}

    async def send_email(self, data: TicketSendEmail):
        # 1. Envia para o Bitrix
        activity_id = await self.bitrix.send_email(
            deal_id=data.deal_id,
            subject=data.subject,
            message=data.message,
            to_email=data.to_email,
            from_email=data.from_email,
            attachments=data.attachments,
        )

        # 2. Se enviou com sucesso, salva no banco local imediatamente
        if activity_id:
            from app.repositories.activity import ActivityRepository
            
            # Precisamos do ID interno do Deal
            deal = await self.repo.get_by_deal_id(data.deal_id)
            if deal:
                act_repo = ActivityRepository(self.repo.session)
                
                activity_data = {
                    "deal_id": deal.id,
                    "activity_id": activity_id,
                    "owner_type_id": "2", # Deal
                    "type_id": "4",       # Email
                    "provider_id": "CRM_EMAIL",
                    "provider_type_id": "EMAIL",
                    "direction": "2",     # Outgoing
                    "subject": data.subject,
                    "description": data.message,
                    "body_html": data.message,
                    "description_type": "3", # HTML
                    "from_email": data.from_email,
                    "to_email": data.to_email,
                    "sender_email": data.from_email,
                    "receiver_email": data.to_email,
                    "created_at_bitrix": datetime.now(timezone.utc)
                }
                
                await act_repo.upsert_activity(activity_data)
                await self.repo.session.commit()

                # --- Real-time Broadcast ---
                try:
                    from app.providers.websocket import manager
                    # Buscamos do banco para garantir que venha com relacionamentos carregados (eager load)
                    # O método get_by_activity_id agora faz selectinload de files
                    saved_activity = await act_repo.get_by_activity_id(activity_id)
                    
                    if saved_activity:
                        from app.schemas.activity import ActivitySchema
                        activity_schema = ActivitySchema.model_validate(saved_activity)
                        
                        print(f"📡 Tentando broadcasting (SendEmail) para Deal {deal.id} (Internal) e {data.deal_id} (Bitrix)...")
                        
                        # Broadcast interno
                        await manager.broadcast(
                            message={"type": "NEW_ACTIVITY", "payload": activity_schema.model_dump(mode='json')},
                            deal_id=str(deal.id)
                        )
                        
                        # Broadcast externo (Bitrix ID)
                        await manager.broadcast(
                            message={"type": "NEW_ACTIVITY", "payload": activity_schema.model_dump(mode='json')},
                            deal_id=str(data.deal_id)
                        )
                        
                        print("✅ Broadcast (SendEmail) executado com sucesso.")
                except Exception as e:
                    print(f"⚠️ Erro ao transmitir WebSocket (SendEmail): {e}")

        return activity_id

    async def create_ticket(self, data: TicketCreateRequest) -> DealModel:
        deal_id = await self.bitrix.create_deal(data)

        if not deal_id:
            raise Exception("Falha de comunicação com Bitrix24")

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
