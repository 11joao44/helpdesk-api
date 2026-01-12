from fastapi import Request
from datetime import datetime, timezone
from pydantic import ValidationError

from app.repositories.activity import ActivityRepository
from app.repositories.deals import DealRepository
from app.providers.bitrix import BitrixProvider
from app.schemas.bitrix import BitrixWebhookSchema
from app.core.constants import BitrixFields, BitrixValues
from app.providers.storage import StorageProvider

class WebhookService:
    def __init__(
        self, 
        deal_repo: DealRepository, 
        activity_repo: ActivityRepository, 
        provider: BitrixProvider
    ):
        self.deal_repo = deal_repo          # Corrigido: deaL_repo -> deal_repo
        self.activity_repo = activity_repo
        self.bitrix = provider
        self.storage = StorageProvider()

    async def process_webhook(self, request: Request):
        try:
            form_data = await request.form()
            data = BitrixWebhookSchema(**dict(form_data))
        except ValidationError as e:
            print(f"⚠️ Payload inválido recebido do Bitrix: {e}")
            return 

        event = data.event
        object_id = data.data_fields_id

        if not object_id: return

        try:
            if event in ["ONCRMDEALADD", "ONCRMDEALUPDATE"]: # Rota de NEGÓCIOS
                await self._sync_deal(object_id)
            
            elif event in ["ONCRMACTIVITYADD", "ONCRMACTIVITYUPDATE"]: # Rota de ATIVIDADES
                await self._sync_activity(object_id)
        except Exception as e:
            if "DEAL" in event: # Em caso de erro, faz rollback na sessão correta
                await self.deal_repo.session.rollback()
            else:
                await self.activity_repo.session.rollback()
            print(f"❌ Erro crítico no processamento do Webhook: {e}")


    async def _sync_deal(self, deal_id: int):
        raw = await self.bitrix.get_deal(deal_id)
        if raw.get("ID") != "8029": return # PARA AMBIENTE LOCAL DE TESTE
        if not raw: return
        print("Data Prazo: ", raw.get(BitrixFields.PRAZO))
        responsible = await self.bitrix.get_responsible(raw.get("ASSIGNED_BY_ID"))
        deal_data = {
            "deal_id": int(raw["ID"]),          
            "title": raw.get("TITLE"),
            "stage_id": raw.get("STAGE_ID"),
            "opened": raw.get("OPENED"),
            "closed": raw.get("CLOSED"),
            "created_by_id": raw.get("CREATED_BY_ID"),
            "modify_by_id": raw.get("MODIFY_BY_ID"),
            "moved_by_id": raw.get("MOVED_BY_ID"),
            "begin_date": self._parse_date(raw.get("BEGINDATE")),
            "close_date": self._parse_date(raw.get("CLOSEDATE")),
            "created_at": self._parse_date(raw.get("DATE_CREATE")),
            "last_activity_by_id": raw.get("LAST_ACTIVITY_BY"),
            "last_communication_time": raw.get("LAST_COMMUNICATION_TIME"),
            "responsible": responsible['responsible'],
            "responsible_email": responsible['email'],
            "service_category": BitrixValues.get_label(BitrixValues.CATEGORIA, raw.get(BitrixFields.CATEGORIA)),
            "system_type": BitrixValues.get_label(BitrixValues.SISTEMAS, raw.get(BitrixFields.SISTEMA)),
            "priority": BitrixValues.get_label(BitrixValues.PRIORIDADE, raw.get(BitrixFields.PRIORIDADE)),
            "date_deadline": self._parse_date(raw.get(BitrixFields.PRAZO)),
        }

        print(f"Deal atualizado: {deal_data}")
        await self.deal_repo.upsert_deal(deal_data)
        await self.deal_repo.session.commit()
        
        # Sincroniza comentários da linha do tempo
        # await self._sync_timeline_for_deal(deal_id)


    async def _sync_timeline_for_deal(self, bitrix_deal_id: int):
        """Busca comentários da timeline e sincroniza com base local."""
        # print(f"🔄 Sincronizando timeline do Deal {bitrix_deal_id}...")
        
        # 1. Busca comentários no Bitrix
        comments_list = await self.bitrix.list_timeline_comments(bitrix_deal_id)
        print(f"🔎 [SyncTimeline] Deal {bitrix_deal_id} retornou {len(comments_list)} comentários.")

        # Para cada comentário, tenta salvar como Activity
        for comm in comments_list:
            # comm ex: {'ID': '177369', 'CREATED': '2026-01-07T21:40:05+03:00', 'AUTHOR_ID': '36', 'COMMENT': 'Lorem ipsum', 'FILES': {...}}
            
            comm_id_int = int(comm["ID"])
            existing = await self.activity_repo.get_by_activity_id(comm_id_int)
            
            if existing:
                print(f"⏭️ [SyncTimeline] Comentário {comm_id_int} já existe. Pulando.")
                continue # Já temos, pula (ou poderia atualizar se quisesse editar)
                
            print(f"📥 Importando novo comentário {comm_id_int} do Bitrix...")
            
            # Busca ID interno do Deal
            deal_id = await self.deal_repo.get_deal_internal_id(bitrix_deal_id)
            if not deal_id:
                print(f"⚠️ Deal {bitrix_deal_id} sem ID interno. Pulando comentário.")
                continue

            # Extração de Author/User
            author_id = comm.get("AUTHOR_ID")
            # Tenta pegar info do user se não tivermos
            responsible_info = {}
            if author_id:
                responsible_info = await self.bitrix.get_responsible(author_id) or {}

            # Extração de Arquivos
            files_data = comm.get("FILES") or []
            files_list = []
            if isinstance(files_data, dict):
                 files_list = list(files_data.values())
            elif isinstance(files_data, list):
                 files_list = files_data
            
            # Monta payload da Activity
            activity_data = {
                "deal_id": deal_id,
                "activity_id": comm_id_int,
                "owner_type_id": "2",
                "type_id": "COMM",             # Mapeia para nosso tipo curto
                "provider_id": "CRM_COMMENT",
                "provider_type_id": "COMMENT",
                "direction": "2",              # Entrada/Saída não se aplica bem, mas 2=Saída é ok
                "subject": "Comentário via Bitrix",
                "description": comm.get("COMMENT"),
                "body_html": comm.get("COMMENT"),
                "description_type": "1",       # 1=Texto simples (geralmente), Bitrix manda HTML as vezes
                "responsible_id": author_id,
                "responsible_name": responsible_info.get("responsible"),
                "responsible_email": responsible_info.get("email"),
                "author_id": author_id,
                "created_at_bitrix": self._parse_date(comm.get("CREATED"))
            }
            
            # Salva
            new_activity = await self.activity_repo.upsert_activity(activity_data)
            
            # Processa Arquivos
            processed_files = []
            for f in files_list:
                # f ex: {'id': 123, 'url': ...}
                file_id = f.get("id")
                if not file_id: continue
                
                res = await self._process_attachment(f)
                if res:
                    url_minio, fname = res
                    processed_files.append({
                         "activity_id": new_activity.id,
                         "bitrix_file_id": file_id,
                         "file_url": url_minio,
                         "filename": fname
                    })
            
            if processed_files:
                await self.activity_repo.sync_files(new_activity.id, processed_files)
                new_activity.file_url = processed_files[0]["file_url"]
                self.activity_repo.session.add(new_activity)

            # Commit ANTES do Broadcast para evitar Race Condition no Front
            await self.activity_repo.session.commit()

            # Broadcast WebSocket
            await self._broadcast_new_activity(new_activity, deal_id, bitrix_deal_id)

    async def _broadcast_new_activity(self, activity, deal_id, bitrix_deal_id):
        try:
            from app.providers.websocket import manager
            from app.schemas.activity import ActivitySchema
            
            # Recarrega do banco para pegar relacionamentos novos
            saved = await self.activity_repo.get_by_activity_id(activity.activity_id)
            print("🚀 Activity salva:", saved)
            if not saved: return # Safety check
            
            schema = ActivitySchema.model_validate(saved)
            
            payload = schema.model_dump(mode='json')
            
            # Injeta ID do Bitrix no payload para o Front reconhecer
            payload["bitrix_deal_id"] = bitrix_deal_id
            print("🚀 Payload:", payload)
            print("🚀 Deal ID:", deal_id)
            print("🚀 Bitrix Deal ID:", bitrix_deal_id)

            await manager.broadcast(
                message={"type": "NEW_ACTIVITY", "payload": payload},
                deal_id=str(bitrix_deal_id)
            )

        except Exception as e:
            print(f"⚠️ Erro Broadcast Webhook: {e}")

    async def _sync_activity(self, activity_id: int):
        raw = await self.bitrix.get_activity(activity_id)
        if raw.get("OWNER_ID") != "8029": return # PARA AMBIENTE LOCAL DE TESTE

        print("Retorno WEBWOOK Activity: ", raw)

        if not raw: return
        if str(raw.get("OWNER_TYPE_ID")) != "2": return # OWNER_TYPE_ID é "2" (que representa "Deal/Negócio" no Bitrix).
            
        bitrix_deal_id = int(raw.get("OWNER_ID"))
        await self._sync_deal(bitrix_deal_id) # Sincronizando Deal

        deal_id = await self.deal_repo.get_deal_internal_id(bitrix_deal_id)
        
        if not deal_id: 
            print(f"❌ Falha: Deal pai {bitrix_deal_id} não encontrado após sincronização.")
            return

        files_data = raw.get("FILES") or []
        files_list = []

        if isinstance(files_data, list):
            files_list = files_data
        elif isinstance(files_data, dict):
            # Bitrix as vezes retorna dict com chaves numéricas
            files_list = list(files_data.values())

        settings = raw.get("SETTINGS", {}) or {}
        email_meta = settings.get("EMAIL_META", {}) or {}
        
        # Tenta pegar de EMAIL_META (padrão de e-mails recebidos/imap)
        email_from = email_meta.get("from")
        email_to = email_meta.get("to")

        # Se não achou, tenta pegar de MESSAGE_FROM (padrão de e-mails enviados via API)
        if not email_from:
            email_from = settings.get("MESSAGE_FROM")

        # Se não achou TO, tenta pegar de COMMUNICATIONS
        if not email_to:
            communications = raw.get("COMMUNICATIONS", [])
            comm_list = []
            
            if isinstance(communications, list):
                comm_list = communications
            elif isinstance(communications, dict):
                comm_list = list(communications.values())
            
            for comm in comm_list:
                c_type = comm.get("TYPE") or comm.get("type")
                if c_type and str(c_type).upper() == "EMAIL":
                    email_to = comm.get("VALUE")
                    break
        
        # Buscando o responsável antes de montar o objeto
        responsible_info = await self.bitrix.get_responsible(raw.get("RESPONSIBLE_ID")) or {}

        # 5. Montagem do Objeto (Activity)
        activity_data = {
            "deal_id": deal_id,       # ID Interno (FK)
            "activity_id": int(raw["ID"]),     # ID Bitrix
            
            "owner_type_id": str(raw.get("OWNER_TYPE_ID")),
            "type_id": str(raw.get("TYPE_ID")),
            "provider_id": raw.get("PROVIDER_ID"),
            "provider_type_id": raw.get("PROVIDER_TYPE_ID"),
            
            "direction": str(raw.get("DIRECTION")),
            "subject": raw.get("SUBJECT"),
            "priority": str(raw.get("PRIORITY")),
            "responsible_id": raw.get("RESPONSIBLE_ID"),
            
            # Buscando detalhes do responsável
            "responsible_name": responsible_info.get('responsible'),
            "responsible_email": responsible_info.get('email'),

            "description": str(raw.get("DESCRIPTION")).replace('<br/><br/>Enviado por <a href="http://www.bitrix24.com" target="_blank" >bitrix24.com</a>', ""),
            "body_html": raw.get("DESCRIPTION"),
            "description_type": str(raw.get("DESCRIPTION_TYPE")),
            
            "from_email": email_from,
            "sender_email": email_from,
            "to_email": email_to,
            "receiver_email": email_to,
            
            "author_id": raw.get("AUTHOR_ID"),
            "editor_id": raw.get("EDITOR_ID"),
             
            # Mantendo retrocompatibilidade (pega o primeiro se existir)
            "file_id": files_list[0].get("id") if files_list else None,
            "file_url": None, # Será atualizado depois

            "read_confirmed": 1 if raw.get("STATUS") == '2' else 0,
            "created_at_bitrix": self._parse_date(raw.get("CREATED"))
        }

        # Verifica se já existe atividade para não sobrescrever e-mails
        existing_activity = await self.activity_repo.get_by_activity_id(activity_data["activity_id"])
        
        if existing_activity:
            # Preserva campos locais se vierem nulos do Bitrix
            if not activity_data.get("to_email") and existing_activity.to_email:
                activity_data["to_email"] = existing_activity.to_email
                activity_data["receiver_email"] = existing_activity.receiver_email
                
            if not activity_data.get("from_email") and existing_activity.from_email:
                activity_data["from_email"] = existing_activity.from_email
                activity_data["sender_email"] = existing_activity.sender_email

        # Salva a atividade primeiro para ter o ID
        activity = await self.activity_repo.upsert_activity(activity_data)
        
        # 6. Processamento dos Arquivos (Multiplos)
        processed_files = []
        for f in files_list:
             if not isinstance(f, dict): continue
             
             file_id = f.get("id")
             if not file_id: continue
             
             result_process = await self._process_attachment(f)
             
             if result_process:
                 minio_url, real_filename = result_process
                 
                 processed_files.append({
                     "activity_id": activity.id,
                     "bitrix_file_id": file_id,
                     "file_url": minio_url,
                     "filename": real_filename or f.get("name")
                 })


        # Atualiza tabela de arquivos
        if processed_files:
             await self.activity_repo.sync_files(activity.id, processed_files)
             # Atualiza o file_url retrocompativel com o primeiro arquivo
             activity.file_url = processed_files[0]["file_url"]
             self.activity_repo.session.add(activity)

        print(f"📧 Atividade {activity_id} processada com {len(processed_files)} anexos.")

        # Commit ANTES do Broadcast para evitar Race Condition no Front
        await self.activity_repo.session.commit()

        # --- 7. Real-time Broadcast ---
        await self._broadcast_new_activity(activity, deal_id, bitrix_deal_id)


    async def _process_attachment(self, file_data: dict) ->  tuple[str, str] | None:
        """
        Baixa anexo do Bitrix e sobe no MinIO.
        Retorna (URL MinIO, Filename Original).
        """
        # file_data ex: {'id': 971599, 'url': '...'}
        file_id = file_data.get("id")
        if not file_id:
            return None

        # 1. Download via API Autenticada (Disk)
        # Retorna: (filename, bytes)
        result = await self.bitrix.download_disk_file(file_id)
        
        if not result:
            print(f"❌ Falha ao baixar anexo {file_id} do Bitrix.")
            return None

        filename, file_bytes = result
        
        # 2. Upload para MinIO usando o nome original
        # O storage provider vai detectar o mimetype pelo filename
        uploaded_key = self.storage.upload_file(file_bytes, filename)
        
        if uploaded_key:
            return uploaded_key, filename
            
        return None


    def _parse_date(self, date_str: str):
        if not date_str: return None
        try:
            return datetime.fromisoformat(date_str).astimezone(timezone.utc)
        except ValueError:
            return None