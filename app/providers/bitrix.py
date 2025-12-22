import httpx
from datetime import datetime
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.constants import BitrixFields, BitrixValues
from app.schemas.tickets import TicketCreateRequest


class BitrixProvider:
    def __init__(self):
        # Garanta que no seu config.py/env a URL termina sem a barra, ex: .../rest/1/token
        self.webhook_url = settings["BITRIX_INBOUND_URL"]

        # Correção automática de protocolo se estiver faltando
        if self.webhook_url and not self.webhook_url.startswith(
            ("http://", "https://")
        ):
            self.webhook_url = f"https://{self.webhook_url}"

    async def get_or_create_contact(
        self, name: str, email: str, service_category: str, phone: str = None
    ) -> Optional[str]:
        """
        Lógica inteligente:
        1. Busca se o contato já existe pelo E-mail.
        2. Se existir, retorna o ID dele.
        3. Se não existir, cria e retorna o novo ID.
        """
        contacts = await self._call_bitrix(
            "crm.contact.list",
            json_body={"filter": {"EMAIL": email}, "select": ["ID"]},
            method="POST",
        )

        # Se houve erro na API (None), não tenta processar e retorna None
        if contacts is None:
            print(
                f"⚠️ [Bitrix] Falha ao buscar contato {email}. Verifique logs anteriores."
            )
            return None

        if len(contacts) == 0:
            print(f"🆕 [Bitrix] Criando novo contato para: {email}")
            create_payload = {
                "fields": {
                    "NAME": name.split()[0],  # Primeiro nome
                    "LAST_NAME": " ".join(name.split()[1:]) if " " in name else "",
                    "OPENED": "Y",
                    "COMPANY_ID": "2" if service_category == "Interno" else "",
                    "EMAIL": [{"VALUE": email, "VALUE_TYPE": "WORK"}],
                    "PHONE": [{"VALUE": phone, "VALUE_TYPE": "WORK"}] if phone else [],
                }
            }
            create_result = await self._call_bitrix(
                "crm.contact.add", json_body=create_payload, method="POST"
            )
            return str(create_result) if create_result else None

        return contacts[0]["ID"]

    async def create_deal(self, data: TicketCreateRequest) -> int | None:
        """Cria o Negócio traduzindo os campos do Front para o Bitrix"""

        contact_id = await self.get_or_create_contact(
            data.full_name, data.email, data.service_category, data.phone
        )
        dept_id_bitrix = BitrixValues.get_id(
            BitrixValues.DEPARTAMENTOS, data.assignee_department
        )
        filial_id = BitrixValues.get_id(BitrixValues.FILIAIS, data.filial)
        prioridade_id = BitrixValues.get_id(BitrixValues.PRIORIDADE, data.priority)
        sistema_id = BitrixValues.get_id(BitrixValues.SISTEMAS, data.system_type)
        categoria_id = BitrixValues.get_id(
            BitrixValues.CATEGORIA, data.service_category
        )

        descricao_completa = (
            f"{data.description}\n\n"
            f"# Detalhes Adicionais\n"
            f"Solicitante: {data.full_name} (Matrícula: {data.matricula})\n"
            f"Departamento de Origem: {data.requester_department}\n"
            f"Telefone Informado: {data.phone}"
        )

        payload = {
            "fields": {
                "TITLE": data.title,
                "TYPE_ID": "SALE",
                "STAGE_ID": "C25:NEW",  # ID da etapa "Novo" no seu funil
                "OPENED": "Y",
                "CATEGORY_ID": 25,
                "CURRENCY_ID": "BRL",
                "SOURCE_ID": "SELF",
                "CONTACT_ID": contact_id,
                "ASSIGNED_BY_ID": data.resp_id if data.resp_id else "6185",
                "COMMENTS": descricao_completa,  # Descrição vai na timeline
                "UF_CRM_6938495549C8A": data.requester_department,
                BitrixFields.DESCRIPTION: data.description,  # Se tiver um campo custom de texto só para o problema
                BitrixFields.CLIENT_PHONE: data.phone,
                BitrixFields.PROTOCOL_NUMBER: data.matricula,  # Mapeamos matricula naquele campo de texto
                # --- Campos de Lista (IDs Mapeados) ---
                BitrixFields.DEPARTAMENTO: dept_id_bitrix,  # TI, Manutenção, etc.
                BitrixFields.FILIAL: filial_id,
                BitrixFields.PRIORIDADE: prioridade_id,
                BitrixFields.CATEGORIA: categoria_id,
                BitrixFields.SISTEMA: sistema_id,
                BitrixFields.ASSUNTO_MAP.get(sistema_id): BitrixValues.get_subject_id(
                    data.system_type, data.subject
                ),
            }
        }

        payload["fields"] = {k: v for k, v in payload["fields"].items() if v}

        print(
            f"🚀 [Bitrix] Criando Deal '{data.title}' para Depto ID: {dept_id_bitrix}"
        )

        result = await self._call_bitrix(
            "crm.deal.add", json_body=payload, method="POST"
        )

        if result:
            deal_id = int(result)

            # Se houver anexos na abertura, cria um comentário com eles
            if data.attachments:
                await self._add_comment_with_files(deal_id, data.attachments)

            return deal_id
        return None

    async def _add_comment_with_files(self, deal_id: int, attachments: list):
        """Adiciona um comentário no Deal contendo os arquivos anexados"""
        print(
            f"📎 [Bitrix] Anexando {len(attachments)} arquivos ao Deal {deal_id} via Timeline..."
        )

        # Formato para crm.timeline.comment.add: [["nome.ext", "base64..."], ...]
        files_payload = []
        for att in attachments:
            files_payload.append([att.get("name"), att.get("content")])

        payload = {
            "fields": {
                "ENTITY_ID": deal_id,
                "ENTITY_TYPE": "deal",
                "COMMENT": "Arquivos enviados durante a abertura do chamado.",
                "FILES": files_payload,
            }
        }

        await self._call_bitrix(
            "crm.timeline.comment.add", json_body=payload, method="POST"
        )

    async def get_deal(self, deal_id: int) -> Optional[Dict[str, Any]]:
        print(f"📡 [Provider] Buscando Deal {deal_id}...")
        return await self._call_bitrix("crm.deal.get", params={"id": deal_id})

    async def get_responsible(self, ASSIGNED_BY_ID: int) -> Optional[Dict[str, Any]]:
        print(f"📡 [Provider] Buscando Responsável ID {ASSIGNED_BY_ID}...")
        users_list = await self._call_bitrix("user.get", params={"ID": ASSIGNED_BY_ID})

        # Segurança: Verifica se voltou algo
        if not users_list or len(users_list) == 0:
            return None

        user = users_list[0]

        return {
            "responsible_id": user["ID"],
            "email": user.get("EMAIL", ""),
            "responsible": f"{user.get('NAME', '')} {user.get('LAST_NAME', '')}".strip(),
        }

    async def get_activity(self, activity_id: int) -> Optional[Dict[str, Any]]:
        print(f"📡 [Provider] Buscando Atividade {activity_id}...")
        return await self._call_bitrix("crm.activity.get", params={"id": activity_id})

    async def _call_bitrix(
        self,
        endpoint: str,
        params: Dict = None,
        json_body: Dict = None,
        method: str = "GET",
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

                response.raise_for_status()  # Lança erro se for 400/500
                data = response.json()
                print("Retorno da api bitrix criar ticket: ", data)

                if "result" in data:
                    return data["result"]

                print(f"⚠️ [Provider] Bitrix retornou sucesso mas sem resultado: {data}")
                return None

            except Exception as e:
                print(f"❌ [Provider] Erro na chamada {endpoint}: {e}")
                return None

    async def send_email(
        self,
        deal_id: int,
        subject: str,
        message: str,
        to_email: str,
        from_email: str = None,
        attachments: list = [],
    ) -> int | None:
        """
        Envia um e-mail vinculado ao Deal (Ticket) para o cliente.
        endpoint: crm.activity.add
        """

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        payload = {
            "fields": {
                "OWNER_TYPE_ID": 2,  # 2 = Deal (Negócio)
                "OWNER_ID": deal_id,  # ID do Ticket/Deal
                "TYPE_ID": 4,  # 4 = E-mail
                "PROVIDER_ID": "CRM_EMAIL",
                "PROVIDER_TYPE_ID": "EMAIL",
                "SUBJECT": subject,
                "DESCRIPTION": message,
                "DESCRIPTION_TYPE": 3,  # 3 = HTML (permite formatação)
                "DIRECTION": 2,  # 2 = Saída (Outgoing)
                "START_TIME": now_str,
                "END_TIME": now_str,
                "COMPLETED": "Y",  # Marca como concluído/enviado
                "PRIORITY": 2,  # 2 = Normal
                "SETTINGS": {  # Configuração de Remetente e Destinatário
                    "MESSAGE_FROM": (
                        from_email if from_email else "qualidade.09@carvalima.com.br"
                    ),
                },
                "COMMUNICATIONS": [
                    {
                        "VALUE": to_email,
                        "ENTITY_TYPE_ID": 3,  # 3 = Contact (Contato)
                        "TYPE": "EMAIL",
                    }
                ],
            }
        }

        # 2. Anexar arquivos DIRETAMENTE (Direct Base64)
        # Formato testado e aprovado: "FILES": [{"fileData": ["nome.ext", "base64..."]}]
        if attachments:
            files_payload = []
            for att in attachments:
                # att = {"name": "fatura.pdf", "content": "base64..."}
                files_payload.append(
                    {"fileData": [att.get("name"), att.get("content")]}
                )

            payload["fields"]["FILES"] = files_payload

        print(f"📧 [Bitrix] Enviando e-mail para Deal {deal_id} ({to_email})...")

        result = await self._call_bitrix(
            "crm.activity.add", json_body=payload, method="POST"
        )

        if result:
            return int(result)

        return None

    async def close_deal(
        self, deal_id: int, rating: int = None, comment: str = None
    ) -> bool:
        """
        Encerra o chamado movendo para a etapa de sucesso e salvando a avaliação.
        Endpoint: crm.deal.update
        """

        fields = {
            "STAGE_ID": "C25:WON",
            "COMMENTS": (
                comment if comment else "Chamado encerrado pelo cliente via Portal."
            ),
        }

        if rating:
            fields["UF_CRM_CSAT_RATING"] = rating

        print(f"🏁 [Bitrix] Encerrando Deal {deal_id} com nota {rating}...")

        result = await self._call_bitrix(
            "crm.deal.update",
            json_body={"id": deal_id, "fields": fields},
            method="POST",
        )

        return bool(result)
