import httpx
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.constants import BitrixFields
from app.schemas.tickets import TicketCreateRequest

class BitrixProvider:
    def __init__(self):
        # Garanta que no seu config.py/env a URL termina sem a barra, ex: .../rest/1/token
        self.webhook_url = settings['BITRIX_INBOUND_URL'] 

    async def create_deal(self, data: TicketCreateRequest) -> int | None:
        """Cria um Negócio (Deal) no CRM. Doc: https://apidocs.bitrix24.com/api-reference/crm/deals/crm-deal-add.html"""
        payload = {
            "fields": {
                # Campos Padrão (Obrigatórios/Sistema)
                "TITLE": data.title,
                "TYPE_ID": "SALE",
                "STAGE_ID": "C25:NEW",
                "CATEGORY_ID": 25,
                "CURRENCY_ID": "BRL",
                "OPENED": "Y",
                "ASSIGNED_BY_ID": 5807,
                "SOURCE_ID": "SELF",
                BitrixFields.DESCRIPTION: data.description,
            }
        }

        # Para criar (WRITE), usamos POST para segurança dos dados
        result = await self._call_bitrix("crm.deal.add", json_body=payload, method="POST")

        if result:
            print(f"✅ [Provider] Deal criado com sucesso! ID: {result}")
            return int(result)
        return None

    async def get_deal(self, deal_id: int) -> Optional[Dict[str, Any]]:
        print(f"📡 [Provider] Buscando Deal {deal_id}...")
        return await self._call_bitrix("crm.deal.get", params={"id": deal_id})

    async def get_activity(self, activity_id: int) -> Optional[Dict[str, Any]]:
        print(f"📡 [Provider] Buscando Atividade {activity_id}...")
        return await self._call_bitrix("crm.activity.get", params={"id": activity_id})

    async def _call_bitrix(
        self, 
        endpoint: str, 
        params: Dict = None, 
        json_body: Dict = None, 
        method: str = "GET"
    ) -> Optional[Any]:
        """
        Método genérico inteligente.
        - GET: Usa 'params' (Query String) -> Bom para leituras.
        - POST: Usa 'json_body' (Corpo) -> Bom para criações/updates.
        """
        url = f"{self.webhook_url}/{endpoint}.json"
        
        async with httpx.AsyncClient() as client:
            try:
                if method == "GET":
                    response = await client.get(url, params=params, timeout=15.0)
                else:
                    response = await client.post(url, json=json_body, timeout=15.0)
                
                response.raise_for_status() # Lança erro se for 400/500
                data = response.json()
                print("Retorno da api bitrix criar ticket: ", data)
                
                if "result" in data:
                    return data["result"]
                
                print(f"⚠️ [Provider] Bitrix retornou sucesso mas sem resultado: {data}")
                return None
                
            except Exception as e:
                print(f"❌ [Provider] Erro na chamada {endpoint}: {e}")
                return None