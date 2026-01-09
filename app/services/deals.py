from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.deals import DealModel
from app.providers.bitrix import BitrixProvider
from app.providers.storage import StorageProvider
from app.repositories.deals import DealRepository
from app.schemas.tickets import TicketCloseRequest, TicketCreateRequest, TicketSendEmail


class DealService:
    def __init__(self, session: AsyncSession):
        # Instanciamos o provider aqui ou recebemos via injeção
        self.repo = DealRepository(session)
        self.bitrix = BitrixProvider()
        self.storage = StorageProvider()

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


    async def add_comment(self, deal_id: int, message: str, attachments: list = []) -> bool:
        """Adiciona um comentário ao Deal via Bitrix."""
        comment_id = await self.bitrix.add_comment(deal_id, message, attachments)
        if comment_id:
            # --- Real-time Broadcast ---
            try:
                from app.providers.websocket import manager
                from app.schemas.activity import ActivitySchema, ActivityFileSchema

                # Busca Deal para ter o ID interno
                deal = await self.repo.get_by_deal_id(deal_id)
                
                # --- Preparar Arquivos para Preview Imediato ---
                temp_files = []
                if attachments:
                    for idx, att in enumerate(attachments):
                        b64_content = att.get("content", "")
                        filename = att.get("name", f"file_{idx}")
                                
                        # Detectar mime type básico
                        mime = "application/octet-stream"
                        if filename.lower().endswith(".png"): mime = "image/png"
                        elif filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg"): mime = "image/jpeg"
                        elif filename.lower().endswith(".pdf"): mime = "application/pdf"
                                
                        data_uri = f"data:{mime};base64,{b64_content}"
                                
                        temp_file = ActivityFileSchema(
                            id=0,
                            bitrix_file_id=0,
                            file_url=data_uri,
                            filename=filename,
                            created_at=datetime.now(timezone.utc)
                        )
                        temp_files.append(temp_file)

                activity_payload = ActivitySchema(
                    id=deal.id,
                    activity_id=comment_id,
                    deal_id=deal.deal_id,
                    owner_type_id="2",
                    type_id="COMM",          # Front deve saber lidar ou exibir genérico
                    provider_id="CRM_COMMENT", 
                    provider_type_id="COMMENT",
                    direction="2", # Outgoing
                    description=message,
                    body_html=message,
                    description_type="3", # HTML
                    completed="Y",
                    priority="2",
                    created_at=datetime.now(timezone.utc),
                    files=temp_files,
                    # Campos Opcionais obrigatórios pelo Schema (se não tiver default)
                    responsible_id=str(deal.created_by_id) if deal else None,
                    responsible_name=None,
                    responsible_email=None,
                    sender_email=None,
                    to_email=None,
                    from_email=None,
                    receiver_email=None,
                    author_id=None,
                    editor_id=None,
                    read_confirmed=None,
                    file_id=None,
                    file_url=None,
                    created_at_bitrix=datetime.now(timezone.utc)
                )

                # Broadcast unificado (ID Bitrix)
                
                # Broadcast externo (ID Bitrix)
                await manager.broadcast(
                    message={"type": "NEW_ACTIVITY", "payload": activity_payload.model_dump(mode='json')},
                    deal_id=str(deal_id)
                )
                
                # --- Persistir no Banco de Dados ---
                if not deal.deal_id:
                     print(f"⚠️ [AddComment] Deal {deal_id} não encontrado localmente. Pulusando persistência.")
                     return True

                from app.repositories.activity import ActivityRepository
                act_repo = ActivityRepository(self.repo.session)
                
                db_activity_data = {
                    "deal_id": deal.id,
                    "activity_id": comment_id,
                    "owner_type_id": "2",
                    "type_id": "COMM",
                    "provider_id": "CRM_COMMENT",
                    "provider_type_id": "COMMENT",
                    "direction": "2",
                    "subject": "",
                    "description": message,
                    "body_html": message,
                    "description_type": "3",
                    "created_at_bitrix": datetime.now(timezone.utc)
                }

                print(f"💾 [AddComment] Tentando salvar atividade: {db_activity_data}")
                
                await act_repo.upsert_activity(db_activity_data)
                await self.repo.session.commit()
                print(f"✅ [AddComment] Atividade {comment_id} salva com sucesso.")

            except Exception as e:
                import traceback
                print(f"⚠️ Erro ao processar pós-comentário (AddComment): {e}")
                traceback.print_exc()

        return comment_id is not None

    async def create_ticket(self, data: TicketCreateRequest) -> DealModel:
        deal_id, file_id = await self.bitrix.create_deal(data)
        
        print(f"🛠️ [DealService] create_ticket: deal_id={deal_id}, file_id={file_id}")

        if not deal_id:
            raise Exception("Falha de comunicação com Bitrix24")

        # --- Busca Detalhes Ricos do Deal no Bitrix (Responsible, etc) ---
        bitrix_deal_data = await self.bitrix.get_deal(deal_id)
        
        responsible_name = "N/A"
        responsible_email = None
        
        if bitrix_deal_data:
            assigned_id = bitrix_deal_data.get("ASSIGNED_BY_ID")
            if assigned_id:
                user_data = await self.bitrix.get_user(assigned_id)
                if user_data:
                    responsible_name = f"{user_data.get('NAME', '')} {user_data.get('LAST_NAME', '')}".strip()
                    responsible_email = user_data.get("EMAIL")
        
        # --- Tratamento de Anexos (MinIO + Bitrix) ---
        # file_id já veio do bitrix.create_deal (que fez upload pro Disk)
        # file_url agora será o caminho no MinIO para consistência com Activities
        
        file_url = None
        
        # Se tiver anexos, faz upload pro MinIO também
        if data.attachments:
            print(f"📤 [DealService] Iniciando upload para MinIO...")
            for att in data.attachments:
                try:
                    name = att.get("name", f"file_{deal_id}.bin")
                    content_b64 = att.get("content", "")
                    
                    if content_b64:
                        import base64
                        file_bytes = base64.b64decode(content_b64)
                        
                        # Usa o StorageProvider para upload
                        # Ele retorna o object_name (ex: attachments/arquivo.pdf)
                        # Vamos prefixar com deal_{deal_id}_ para organizar melhor ou evitar colisão se o nome for genérico
                        # O provider já cuida de colisão básica? Vamos checar. O provider do user não usa UUID se passarmos nome.
                        # Vamos garantir nome único.
                        import uuid
                        ext = ""
                        if "." in name:
                            ext = f".{name.split('.')[-1]}"
                        unique_name = f"{uuid.uuid4()}{ext}"
                        
                        object_name = self.storage.upload_file(file_bytes, unique_name)
                        
                        if object_name:
                            file_url = object_name
                            print(f"✅ [DealService] Upload MinIO sucesso: {file_url}")
                            # Salvamos apenas o primeiro por enquanto, conforme schema single-column
                            break 
                except Exception as e:
                    print(f"❌ [DealService] Erro no upload MinIO: {e}")

        # --- Persistência no Banco Local (Com tratamento de Race Condition) ---
        saved_deal = None
        
        # 1. Tenta buscar primeiro para evitar erro se o webhook já criou
        existing_deal = await self.repo.get_by_deal_id(deal_id)
        if existing_deal:
            saved_deal = existing_deal
            # Atualiza TODOS os campos, pois o webhook cria 'seco'
            saved_deal.user_id = data.user_id
            saved_deal.created_by_id = data.resp_id
            saved_deal.matricula = data.matricula
            saved_deal.requester_department = data.requester_department
            saved_deal.assignee_department = data.assignee_department
            saved_deal.service_category = data.service_category
            saved_deal.system_type = data.system_type
            saved_deal.priority = data.priority
            saved_deal.requester_email = data.email
            saved_deal.description = data.description 
            
            # Atualiza Responsible e File Info
            if responsible_name != "N/A":
                saved_deal.responsible = responsible_name
            if responsible_email:
                saved_deal.responsible_email = responsible_email
            
            if file_id:
                saved_deal.file_id = file_id
            if file_url:
                saved_deal.file_url = file_url
                
            await self.repo.session.commit()
            await self.repo.session.refresh(saved_deal)
        else:
            # 2. Tenta criar novo
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
                file_id=file_id,
                file_url=file_url,
                responsible=responsible_name,
                responsible_email=responsible_email
            )

            try:
                self.repo.session.add(new_deal)
                await self.repo.session.commit()
                await self.repo.session.refresh(new_deal)
                saved_deal = new_deal
            except IntegrityError:
                # Race condition: Webhook criou o deal milissegundos antes
                await self.repo.session.rollback()
                existing_deal = await self.repo.get_by_deal_id(deal_id)
                if existing_deal:
                    saved_deal = existing_deal
                    # Atualiza TODOS os campos novamente
                    saved_deal.user_id = data.user_id
                    saved_deal.created_by_id = data.resp_id
                    saved_deal.matricula = data.matricula
                    saved_deal.requester_department = data.requester_department
                    saved_deal.assignee_department = data.assignee_department
                    saved_deal.service_category = data.service_category
                    saved_deal.system_type = data.system_type
                    saved_deal.priority = data.priority
                    saved_deal.requester_email = data.email
                    saved_deal.description = data.description
                    
                    if responsible_name != "N/A":
                        saved_deal.responsible = responsible_name
                    if responsible_email:
                        saved_deal.responsible_email = responsible_email
                    
                    if file_id:
                        saved_deal.file_id = file_id
                    if file_url:
                        saved_deal.file_url = file_url
                        
                    await self.repo.session.commit()
                    await self.repo.session.refresh(saved_deal)
                else:
                     raise

        # --- Pós-Criação: Adicionar Comentário com Anexos ---
        # Só chamamos agora que o Deal JÁ EXISTE no banco local.
        if data.attachments:
            # O add_comment vai buscar o deal no banco para criar a Activity e fazer broadcast
            if saved_deal:
                await self.add_comment(
                    deal_id=deal_id, 
                    message="Anexos.", 
                    attachments=data.attachments
                )
            
        return saved_deal
