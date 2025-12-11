import httpx
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.constants import BitrixFields, BitrixValues
from app.schemas.tickets import TicketCreateRequest

class BitrixProvider:
    def __init__(self):
        # Garanta que no seu config.py/env a URL termina sem a barra, ex: .../rest/1/token
        self.webhook_url = settings['BITRIX_INBOUND_URL'] 

    async def get_or_create_contact(self, name: str, email: str, phone: str = None) -> str:
        """
        Lógica inteligente: 
        1. Busca se o contato já existe pelo E-mail.
        2. Se existir, retorna o ID dele.
        3. Se não existir, cria e retorna o novo ID.
        """
        # 1. Busca
        search_payload = {
            "filter": {"EMAIL": email},
            "select": ["ID"]
        }
        search_result = await self._call_bitrix("crm.contact.list", json_body=search_payload, method="POST")
        
        if search_result and len(search_result) > 0:
            existing_id = search_result[0]['ID']
            print(f"✅ [Bitrix] Contato encontrado: {email} (ID: {existing_id})")
            return existing_id

        # 2. Criação (se não achou)
        print(f"🆕 [Bitrix] Criando novo contato para: {email}")
        create_payload = {
            "fields": {
                "NAME": name.split()[0], # Primeiro nome
                "LAST_NAME": " ".join(name.split()[1:]) if " " in name else "", # Resto do nome
                "OPENED": "Y",
                "EMAIL": [{"VALUE": email, "VALUE_TYPE": "WORK"}],
                "PHONE": [{"VALUE": phone, "VALUE_TYPE": "WORK"}] if phone else []
            }
        }
        create_result = await self._call_bitrix("crm.contact.add", json_body=create_payload, method="POST")
        return str(create_result) if create_result else None

    async def create_deal(self, data: TicketCreateRequest) -> int | None:
        """Cria o Negócio traduzindo os campos do Front para o Bitrix"""
        
        # 1. Busca ou Cria o Contato (Pessoa Física)
        # Usamos full_name e email para garantir unicidade
        contact_id = await self.get_or_create_contact(data.full_name, data.email, data.phone)
        
        # 2. Tradução dos Campos (Mapeamento)
        # O Front manda "TI", o Bitrix quer "1385"
        # O Front manda "Cuiabá", o Bitrix quer "1619"
        
        # IMPORTANTE: Usamos o assignee_department (Para quem é o chamado) para classificar
        dept_id_bitrix = BitrixValues.get_id(BitrixValues.DEPARTAMENTOS, data.assignee_department)
        
        filial_id   = BitrixValues.get_id(BitrixValues.FILIAIS, data.filial)
        prioridade_id = BitrixValues.get_id(BitrixValues.PRIORIDADE, data.priority)
        sistema_id  = BitrixValues.get_id(BitrixValues.SISTEMAS, data.system_type)
        categoria_id = BitrixValues.get_id(BitrixValues.CATEGORIA, data.service_category)

        # 3. Enriquecendo a Descrição
        # Como o Bitrix nativo não tem "Departamento de Origem", colocamos no texto
        descricao_completa = (
            f"{data.description}\n\n"
            f"# Detalhes Adicionais\n"
            f"Solicitante: {data.full_name} (Matrícula: {data.matricula})\n"
            f"Departamento de Origem: {data.requester_department}\n"
            f"Telefone Informado: {data.phone}"
        )

        # 4. Montando o Payload
        payload = {
            "fields": {
                "TITLE": data.title,
                "TYPE_ID": "SALE",
                "STAGE_ID": "C25:NEW", # ID da etapa "Novo" no seu funil
                "OPENED": "Y",         # Aberto para todos
                "CATEGORY_ID": 25,
                "CURRENCY_ID": "BRL",
                "SOURCE_ID": "SELF",
                
                # --- Vínculos ---
                "CONTACT_ID": contact_id,
                # Define o responsável. Se vier vazio do front, usa um padrão (ex: 6185)
                "ASSIGNED_BY_ID": data.resp_id if data.resp_id else "6185",
                
                # --- Campos de Texto Simples ---
                "COMMENTS": descricao_completa, # Descrição vai na timeline
                BitrixFields.DESCRIPTION: data.description, # Se tiver um campo custom de texto só para o problema
                BitrixFields.CLIENT_PHONE: data.phone,
                BitrixFields.PROTOCOL_NUMBER: data.matricula, # Mapeamos matricula naquele campo de texto
                
                # --- Campos de Lista (IDs Mapeados) ---
                BitrixFields.DEPARTAMENTO: dept_id_bitrix, # TI, Manutenção, etc.
                BitrixFields.FILIAL: filial_id,
                BitrixFields.PRIORIDADE: prioridade_id,
                BitrixFields.CATEGORIA: categoria_id,
                
                # BitrixFields.SISTEMA: sistema_id,
                # Campos Booleanos/Flags (Opcional, se precisar resetar)
                # "UF_CRM_1711044027933": "0", 
            }
        }

        # Limpeza: Remove chaves vazias (exceto arrays vazios se necessário)
        # Isso evita que o Bitrix reclame de IDs vazios em campos de lista
        payload["fields"] = {k: v for k, v in payload["fields"].items() if v}

        print(f"🚀 [Bitrix] Criando Deal '{data.title}' para Depto ID: {dept_id_bitrix}")
        
        result = await self._call_bitrix("crm.deal.add", json_body=payload, method="POST")

        if result:
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
   
