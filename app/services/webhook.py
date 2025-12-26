from fastapi import Request
from datetime import datetime, timezone
from pydantic import ValidationError

from app.repositories.activity import ActivityRepository
from app.repositories.deals import DealRepository
from app.providers.bitrix import BitrixProvider
from app.schemas.bitrix import BitrixWebhookSchema
from app.core.constants import BitrixFields
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
        # --- 1. Validação e Parse do Payload ---
        try:
            form_data = await request.form()
            data = BitrixWebhookSchema(**dict(form_data))
        except ValidationError as e:
            print(f"⚠️ Payload inválido recebido do Bitrix: {e}")
            return 

        event = data.event
        object_id = data.data_fields_id

        if not object_id:
            return

        # --- 2. Roteamento do Evento ---
        try:
            print(f"🔄 Recebido: {event} | ID: {object_id}")

            # Rota de NEGÓCIOS
            if event in ["ONCRMDEALADD", "ONCRMDEALUPDATE"]:
                await self._sync_deal(object_id)
                await self.deal_repo.session.commit() # Confirma transação do Deal
            
            # Rota de ATIVIDADES
            elif event in ["ONCRMACTIVITYADD", "ONCRMACTIVITYUPDATE"]:
                await self._sync_activity(object_id)
                await self.activity_repo.session.commit() # Confirma transação da Activity

            print(f"✅ Sucesso: {event} | ID: {object_id}")

        except Exception as e:
            # Em caso de erro, faz rollback na sessão correta
            if "DEAL" in event:
                await self.deal_repo.session.rollback()
            else:
                await self.activity_repo.session.rollback()
            
            print(f"❌ Erro crítico no processamento do Webhook: {e}")


    async def _sync_deal(self, deal_id: int):
        raw = await self.bitrix.get_deal(deal_id)
        if not raw: return
        responsible = await self.bitrix.get_responsible(raw.get("ASSIGNED_BY_ID"))
        print("="*50)
        print(responsible['responsible'])
        print(responsible['email'])
        print("="*50)

        deal_data = {
            "deal_id": int(raw["ID"]),          
            "title": raw.get("TITLE"),
            "stage_id": raw.get("STAGE_ID"),
            "description": raw.get(BitrixFields.DESCRIPTION),
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
        }

        await self.deal_repo.upsert_deal(deal_data)


    async def _sync_activity(self, activity_id: int):
        raw = await self.bitrix.get_activity(activity_id)
        if not raw: return

        print(f"DEBUG BITRIX ACTIVITY {activity_id}: {raw}")
        print(f"SETTINGS keys: {raw.get('SETTINGS', {}).keys()}")


        # 1. Valida se é Deal (Type 2)
        if str(raw.get("OWNER_TYPE_ID")) != "2": 
            return 
            
        bitrix_deal_id = int(raw.get("OWNER_ID"))
        
        # 2. Busca o ID interno usando o repositório de DEALS (Correção de responsabilidade)
        internal_deal_id = await self.deal_repo.get_deal_internal_id(bitrix_deal_id)

        # 3. Lógica de "Auto-Healing" (Se não achar o pai, cria ele)
        if not internal_deal_id:
            print(f"⚠️ Pai não encontrado. Sincronizando Deal {bitrix_deal_id}...")
            await self._sync_deal(bitrix_deal_id)
            # Tenta buscar de novo
            internal_deal_id = await self.deal_repo.get_deal_internal_id(bitrix_deal_id)
            
            if not internal_deal_id: 
                print(f"❌ Falha: Não foi possível criar o Deal pai {bitrix_deal_id}.")
                return

        # 4. Extração de Dados (Arquivos)
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

            print(f"DEBUG COMMUNICATIONS ({type(communications)}): {comm_list}")

            # Pega o primeiro que for do tipo EMAIL
            for comm in comm_list:
                # Bitrix pode retornar TYPE="EMAIL" ou type="EMAIL"
                c_type = comm.get("TYPE") or comm.get("type")
                if c_type and str(c_type).upper() == "EMAIL":
                    email_to = comm.get("VALUE")
                    break
        
        # Buscando o responsável antes de montar o objeto
        responsible_info = await self.bitrix.get_responsible(raw.get("RESPONSIBLE_ID")) or {}

        # 5. Montagem do Objeto (Activity)
        activity_data = {
            "deal_id": internal_deal_id,       # ID Interno (FK)
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

             print(f"📎 Processando anexo ID {file_id}...")
             
             # Agora retorna tupla (url, filename_correto)
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