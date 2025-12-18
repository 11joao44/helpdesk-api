from fastapi import Request
from datetime import datetime, timezone
from pydantic import ValidationError

from app.repositories.activity import ActivityRepository
from app.repositories.deals import DealRepository
from app.providers.bitrix import BitrixProvider
from app.schemas.bitrix import BitrixWebhookSchema
from app.core.constants import BitrixFields

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
        }

        await self.deal_repo.upsert_deal(deal_data)


    async def _sync_activity(self, activity_id: int):
        raw = await self.bitrix.get_activity(activity_id)
        if not raw: return

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

        # 4. Extração de Dados
        files = raw.get("FILES", {}) or {}
        settings = raw.get("SETTINGS", {}) or {}
        email_meta = settings.get("EMAIL_META", {}) or {}
        
        email_from = email_meta.get("from")
        email_to = email_meta.get("to")

        # 5. Montagem do Objeto
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
            
            "description": str(raw.get("DESCRIPTION")).replace('<br/><br/>Enviado por <a href="http://www.bitrix24.com" target="_blank" >bitrix24.com</a>', ""),
            "body_html": raw.get("DESCRIPTION"),
            "description_type": str(raw.get("DESCRIPTION_TYPE")),
            
            "from_email": email_from,
            "sender_email": email_from,
            "to_email": email_to,
            "receiver_email": email_to,
            
            "author_id": raw.get("AUTHOR_ID"),
            "editor_id": raw.get("EDITOR_ID"),
            
            "file_id": files.get("id"), 
            "file_url": files.get("url"), 

            "read_confirmed": 1 if raw.get("STATUS") == '2' else 0,
            "created_at_bitrix": self._parse_date(raw.get("CREATED"))
        }

        await self.activity_repo.upsert_activity(activity_data)
        print(f"📧 Atividade {activity_id} processada.")


    def _parse_date(self, date_str: str):
        if not date_str: return None
        try:
            return datetime.fromisoformat(date_str).astimezone(timezone.utc)
        except ValueError:
            return None