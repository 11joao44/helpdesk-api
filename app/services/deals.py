from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
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
                        from app.schemas.activity import ActivitySchema, ActivityFileSchema
                        activity_schema = ActivitySchema.model_validate(saved_activity)
                        
                        # --- 1. Injetar Imagens de Perfil (Responsável e Solicitante) ---
                        from app.providers.storage import StorageProvider
                        storage = StorageProvider()
                        
                        # Foto do Responsável pelo Deal
                        if deal.responsible_user_rel and deal.responsible_user_rel.profile_picture:
                             activity_schema.responsible_profile_picture_url = storage.get_presigned_url(
                                 deal.responsible_user_rel.profile_picture, 
                                 expiration_hours=168
                             )

                        # --- 2. Injetar Anexos (Base64 para Data URI) ---
                        # O saved_activity ainda não tem arquivos (pois o webhook não rodou).
                        # Vamos injetar manualmente para o front ter feedback imediato.
                        if data.attachments:
                            temp_files = []
                            for idx, att in enumerate(data.attachments):
                                # att = {"name": "foo.png", "content": "base64String..."}
                                b64_content = att.get("content", "")
                                filename = att.get("name", f"file_{idx}")
                                
                                # Detectar mime type básico (opcional, ou genérico)
                                mime = "application/octet-stream"
                                if filename.lower().endswith(".png"): mime = "image/png"
                                elif filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg"): mime = "image/jpeg"
                                elif filename.lower().endswith(".pdf"): mime = "application/pdf"
                                
                                # Montar Data URI
                                data_uri = f"data:{mime};base64,{b64_content}"
                                
                                temp_file = ActivityFileSchema(
                                    id=0, # ID temporário
                                    bitrix_file_id=0,
                                    file_url=data_uri,
                                    filename=filename,
                                    created_at=datetime.now(timezone.utc)
                                )
                                temp_files.append(temp_file)
                            
                            activity_schema.files = temp_files

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
                except Exception as e:
                    print(f"⚠️ Erro ao transmitir WebSocket (SendEmail): {e}")

        return activity_id


    async def create_ticket(self, data: TicketCreateRequest) -> DealModel:
        deal_id = await self.bitrix.create_deal(data)

        if not deal_id:
            raise Exception("Falha de comunicação com Bitrix24")
        
        # Tenta buscar primeiro para evitar erro se o webhook já criou
        existing_deal = await self.repo.get_by_deal_id(deal_id)
        if existing_deal:
            # Atualiza campos importantes que o webhook pode não ter setado (ex: user_id)
            existing_deal.user_id = data.user_id
            existing_deal.created_by_id = data.resp_id
            existing_deal.matricula = data.matricula
            await self.repo.session.commit()
            await self.repo.session.refresh(existing_deal)
            return existing_deal
            
        new_deal = DealModel(
            deal_id=deal_id,
            user_id=data.user_id,
            title=f"[{datetime.now().strftime('%Y%m%d')}{deal_id}] {data.title}",
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
            requester_email=data.email, 
        )

        try:
            self.repo.session.add(new_deal)
            await self.repo.session.commit()
            await self.repo.session.refresh(new_deal)
            return new_deal
        except IntegrityError:
            # Race condition: Webhook criou o deal milissegundos antes
            await self.repo.session.rollback()
            existing_deal = await self.repo.get_by_deal_id(deal_id)
            if existing_deal:
                existing_deal.user_id = data.user_id
                existing_deal.created_by_id = data.resp_id
                existing_deal.matricula = data.matricula
                await self.repo.session.commit()
                await self.repo.session.refresh(existing_deal)
                return existing_deal
            else:
                # Se falhou por outro motivo que não duplicate (pouco provável para deal_id)
                raise
