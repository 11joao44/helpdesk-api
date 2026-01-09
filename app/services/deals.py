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
                
                # --- Preparar Arquivos para Preview Imediato (Websocket) ---
                temp_files = []
                if attachments:
                    print(f"📤 [DealService.add_comment] Processando {len(attachments)} anexos para WebSocket...")
                    for idx, att in enumerate(attachments):
                        b64_content = att.get("content", "")
                        filename = att.get("name", f"file_{idx}_{deal_id}")
                        
                        file_url = None
                        
                        if b64_content:
                            try:
                                import base64
                                import uuid
                                file_bytes = base64.b64decode(b64_content)
                                
                                # Upload MinIO
                                ext = ""
                                if "." in filename:
                                    ext = f".{filename.split('.')[-1]}"
                                unique_name = f"{uuid.uuid4()}{ext}"
                                
                                object_name = self.storage.upload_file(file_bytes, unique_name)
                                
                                if object_name:
                                    # Gera link assinado para o front conseguir abrir imediatamente
                                    signed_url = self.storage.get_presigned_url(object_name)
                                    file_url = signed_url
                                    print(f"✅ [DealService.add_comment] Upload WS sucesso: {object_name}")
                                    
                            except Exception as e:
                                print(f"❌ [DealService.add_comment] Erro Upload MinIO: {e}")
                                # Fallback para data URI se der erro? Melhor não, fica pesado.
                                # Deixa sem URL ou tenta recuperar na próxima leitura.
                        
                        temp_file = ActivityFileSchema(
                            id=0,
                            bitrix_file_id=0,
                            file_url=file_url if file_url else "",
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
        deal_id = await self.bitrix.create_deal(data)
        
        print(f"🛠️ [DealService] create_ticket: deal_id={deal_id}")

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
        files_to_save = []
        legacy_file_id = None # Para coluna antiga (compatibilidade)
        legacy_file_url = None # Para coluna antiga (compatibilidade)
        
        if data.attachments:
            print(f"📤 [DealService] Iniciando processamento de {len(data.attachments)} anexos...")
            for idx, att in enumerate(data.attachments):
                try:
                    name = att.get("name", f"file_{deal_id}_{idx}.bin")
                    content_b64 = att.get("content", "")
                    
                    minio_path = None
                    bitrix_fid = None
                    
                    if content_b64: # Apenas se tiver conteúdo
                         # 1. Upload MinIO
                        try:
                            import base64
                            import uuid
                            file_bytes = base64.b64decode(content_b64)
                            
                            ext = ""
                            if "." in name:
                                ext = f".{name.split('.')[-1]}"
                            unique_name = f"{uuid.uuid4()}{ext}"
                            
                            minio_path = self.storage.upload_file(file_bytes, unique_name)
                            if minio_path:
                                print(f"✅ [DealService] Upload MinIO: {minio_path}")
                        except Exception as e_minio:
                            print(f"❌ [DealService] Erro Upload MinIO ({name}): {e_minio}")

                        # 2. Upload Bitrix Disk (para ter ID oficial)
                        try:
                             # Requer nome e bytes (ja decodificados em file_bytes? ou passamos base64?)
                             # upload_disk_file espera string (conteudo) ou bytes? 
                             # O metodo original espera 'content' que geralmente vinha do payload JSON string?
                             # Vamos checar a assinatura do upload_disk_file...
                             # Se ele espera bytes:
                             bitrix_fid = await self.bitrix.upload_disk_file(name, file_bytes) 
                             # Se ele esperava string, o decode acima gera bytes. Vamos assumir que upload_disk_file foi ajustado ou aceita bytes.
                             if bitrix_fid:
                                 print(f"✅ [DealService] Upload Bitrix Disk: {bitrix_fid}")
                        except Exception as e_bx:
                            print(f"❌ [DealService] Erro Upload Bitrix ({name}): {e_bx}")

                        # 3. Prepara registro se pelo menos um subiu
                        if minio_path or bitrix_fid:
                             files_to_save.append({
                                 "file_url": minio_path if minio_path else "", # URL obrigatória no model?
                                 "bitrix_file_id": bitrix_fid,
                                 "filename": name
                             })
                             
                             # Se for o primeiro, guarda para legacy (prioriza o primeiro que funcionar)
                             if legacy_file_id is None and bitrix_fid:
                                 legacy_file_id = bitrix_fid
                             if legacy_file_url is None and minio_path:
                                 legacy_file_url = minio_path

                except Exception as e:
                    print(f"❌ [DealService] Erro genérico processando anexo {idx}: {e}")

        # --- Persistência no Banco Local ---
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
            
            # Legacy columns
            if legacy_file_id: saved_deal.file_id = legacy_file_id
            if legacy_file_url: saved_deal.file_url = legacy_file_url
            
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
                file_id=legacy_file_id,
                file_url=legacy_file_url,
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
                    
                    if legacy_file_id:
                        saved_deal.file_id = legacy_file_id
                    if legacy_file_url:
                        saved_deal.file_url = legacy_file_url
                        
                    await self.repo.session.commit()
                    await self.repo.session.refresh(saved_deal)

        # --- Persistência dos Multi-Arquivos (Tabela Nova) ---
        if saved_deal and files_to_save:
            # saved_deal.id é o ID da nossa tabela (PK), não o deal_id do Bitrix
            await self.repo.add_files(saved_deal.id, files_to_save)
            
            # --- Adiciona Comentário na Timeline (Visibilidade) ---
            # Vamos usar o método antigo add_comment que aceita a lista de attachments original
            # Isso garante que apareça na timeline (mesmo duplicando o storage interno do Bitrix Timeline vs Disk)
            # UX First: Usuário quer ver o arquivo lá.
            try:
                if saved_deal:
                     await self.add_comment(
                        deal_id=saved_deal.deal_id, 
                        message="Arquivos anexados na criação do ticket.", 
                        attachments=data.attachments
                    )
            except Exception as e_comm:
                print(f"⚠️ [DealService] Erro ao adicionar comentário de anexos: {e_comm}")

        return saved_deal

