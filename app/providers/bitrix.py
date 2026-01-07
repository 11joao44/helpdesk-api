import httpx
import re
import base64
from datetime import datetime
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.constants import BitrixFields, BitrixValues
from app.schemas.tickets import TicketCreateRequest


class BitrixProvider:
    def __init__(self):
        self.webhook_url = settings.get("BITRIX_INBOUND_URL")

    async def get_or_create_contact(self, name: str, email: str, service_category: str, phone: str = None) -> Optional[str]:
        """
        1. Busca se o contato já existe pelo E-mail.
        2. Se existir, retorna o ID dele.
        3. Se não existir, cria e retorna o novo ID.
        """
        contacts = await self._call_bitrix(
            "crm.contact.list",
            json_body={"filter": {"EMAIL": email}, "select": ["ID"]},
            method="POST",
        )

        # Se houve erro na API (None) ou retorno inválido, não tenta processar e retorna None
        if contacts is None or not isinstance(contacts, list):
            print(
                f"⚠️ [Bitrix] Falha ao buscar contato {email}. Retorno inválido ou erro na API: {type(contacts)}"
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

        if not contact_id:
            print(f"❌ [Bitrix] Falha ao obter Contact ID para {data.email}. Abortando criação do Deal.")
            return None

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
        return await self.add_comment(deal_id, "Arquivos enviados durante a abertura do chamado.", attachments)

    async def add_comment(self, deal_id: int, message: str, attachments: list = []) -> int | None:
        """Adiciona um comentário (com ou sem anexos) na timeline do Deal."""
        print(f"💬 [Bitrix] Adicionando comentário ao Deal {deal_id}...")

        files_payload = []
        
        # 1. Processar anexos explícitos (se existirem)
        if attachments:
            for att in attachments:
                files_payload.append([att.get("name"), att.get("content")])

        # 2. Processar imagens embutidas no HTML (tags <img>) e limpar HTML
        # Ex: <img src="http://..."> -> remove tag e adiciona imagem como anexo
        img_tags = re.findall(r'<img[^>]+src="([^">]+)"', message)
        
        if img_tags:
            async with httpx.AsyncClient() as client:
                for idx, img_url in enumerate(img_tags):
                    try:
                        # Decodifica HTML entities na URL (&amp; -> &) se houver
                        img_url_clean = img_url.replace("&amp;", "&")
                        
                        resp = await client.get(img_url_clean, timeout=30.0)
                        if resp.status_code == 200:
                            # Converte para base64
                            b64_content = base64.b64encode(resp.content).decode("utf-8")
                            
                            # Tenta adivinhar nome/extensão
                            filename = f"image_embedded_{idx}.png"
                            # Se a URL tiver path, tenta extrair o nome
                            url_match = re.search(r'/([^/?#]+\.(?:png|jpg|jpeg|gif|pdf))', img_url_clean, re.IGNORECASE)
                            if url_match:
                                filename = url_match.group(1)

                            files_payload.append([filename, b64_content])
                        else:
                            print(f"⚠️ [Bitrix] Falha ao baixar imagem {idx}: {resp.status_code}")
                    except Exception as e:
                        print(f"❌ [Bitrix] Erro ao processar imagem embutida {idx}: {e}")

            # Remove as tags de imagem do corpo da mensagem
            message = re.sub(r'<img[^>]+>', '', message)

        # Limpeza extra pedida pelo usuário: remover tags <p>
        clean_message = message.replace("<p>", "").replace("</p>", "").strip()

        payload = {
            "fields": {
                "ENTITY_ID": deal_id,
                "ENTITY_TYPE": "deal",
                "COMMENT": clean_message,
                "FILES": files_payload,
            }
        }

        # Remove FILES key if empty to be safe (though empty list might be fine)
        if not files_payload:
            payload["fields"].pop("FILES")

        result = await self._call_bitrix(
            "crm.timeline.comment.add", json_body=payload, method="POST"
        )
        
        return int(result) if result else None

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

    async def list_timeline_comments(self, deal_id: int) -> list:
        """Lista os comentários da timeline de um Deal."""
        # crm.timeline.comment.list não é um método padrão documentado tão claramente quanto crm.activity.list
        # Mas vamos tentar filtrar activities do type COMMENT ou usar o método apropriado se existir.
        # Na verdade, comentários de timeline costumam ser atividades com provider ID específico ou método próprio.
        # Porém, a API oficial sugere crm.timeline.comment.list
        
        print(f"📡 [Provider] Listando comentários da timeline do Deal {deal_id}...")
        results = await self._call_bitrix(
            "crm.timeline.comment.list",
            json_body={
                "filter": {
                    "ENTITY_ID": deal_id,
                    "ENTITY_TYPE": "deal"
                },
                "select": ["ID", "CREATED", "AUTHOR_ID", "COMMENT", "FILES"],
                "order": {"CREATED": "DESC"}
            },
            method="POST"
        )
        return results if isinstance(results, list) else []

    async def list_activities(self, deal_id: int) -> list:
        """Lista todas as atividades de um Deal."""
        print(f"📡 [Provider] Listando atividades do Deal {deal_id}...")
        results = await self._call_bitrix(
            "crm.activity.list",
            json_body={
                "filter": {
                    "OWNER_ID": deal_id,
                    "OWNER_TYPE_ID": 2 # Deal
                },
                "select": ["*"], # Pega tudo
                "order": {"CREATED": "DESC"}
            },
            method="POST"
        )
        return results if isinstance(results, list) else []

    async def _call_bitrix(self, endpoint: str, params: Dict = None, json_body: Dict = None, method: str = "GET") -> Optional[Any]:
        """
        - GET: Usa 'params' (Query String) -> Bom para leituras.
        - POST: Usa 'json_body' (Corpo) -> Bom para criações/updates.
        """
        if not self.webhook_url:
            print(
                f"❌ [Bitrix] Falha na chamada {endpoint}: BITRIX_INBOUND_URL não configurada."
            )
            return None

        url = f"{self.webhook_url}/{endpoint}.json"

        async with httpx.AsyncClient() as client:
            try:
                if method == "GET":
                    response = await client.get(url, params=params, timeout=15.0)
                else:
                    response = await client.post(url, json=json_body, timeout=15.0)

                response.raise_for_status()  # Lança erro se for 400/500
                data = response.json()
                # print("Retorno da api bitrix criar ticket: ", data)

                if "result" in data:
                    return data["result"]

                print(f"⚠️ [Provider] Bitrix retornou sucesso mas sem resultado: {data}")
                return None

            except Exception as e:
                print(f"❌ [Provider] Erro na chamada {endpoint}: {e}")
                return None

    async def send_email(self, deal_id: int, subject: str, message: str, to_email: str, from_email: str = None, attachments: list = []) -> int | None:
        """Envia um e-mail vinculado ao Deal (Ticket) para o cliente."""
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

    async def close_deal(self, deal_id: int, rating: int = None, comment: str = None) -> bool:
        """Encerra o chamado movendo para a etapa de sucesso e salvando a avaliação."""

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

    async def get_disk_file(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Busca metadados de um arquivo no Bitrix Drive (Disk)"""
        return await self._call_bitrix("disk.file.get", params={"id": file_id})
    
    async def download_disk_file(self, file_id: int) -> Optional[tuple[str, bytes]]:
        """Baixa um arquivo do Bitrix Disk usando as credenciais do Webhook."""
        meta = await self.get_disk_file(file_id)
        
        if not meta:
            print(f"⚠️ [Bitrix] Metadados não achados para {file_id}. Cancelando download.")
            return None

        download_url = meta.get("DOWNLOAD_URL")
        encoded_filename = meta.get("NAME", f"{file_id}.bin")
        
        async with httpx.AsyncClient() as client:
            try:
                print(f"📥 [Bitrix] Baixando conteúdo do arquivo ID: {file_id}...")
                response = await client.get(download_url, timeout=60.0)
                
                if response.status_code != 200:
                    print(f"❌ [Bitrix] Falha download ID {file_id}: {response.status_code} - {response.text[:200]}")
                    return None
                
                return encoded_filename, response.content
                
            except Exception as e:
                print(f"❌ [Bitrix] Erro no download disk: {e}")
                return None
