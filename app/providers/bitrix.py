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


    async def upload_disk_file(self, filename: str, content: str) -> Optional[int]:
        """Faz upload de um arquivo para o Bitrix Disk (Pasta Raiz do Storage Padrão)"""
        
        print(f"📤 [Bitrix] Uploading file {filename} to Disk...")
        
        # 1. Obter Storage Padrão para pegar a Pasta Raiz
        storage_list = await self._call_bitrix("disk.storage.getlist")
        root_folder_id = None
        
        if storage_list and isinstance(storage_list, list) and len(storage_list) > 0:
            # Pega o primeiro storage (geralmente Arquivos Carregados ou o Drive da Empresa)
            storage = storage_list[0]
            # O campo ROOT_OBJECT_ID é a pasta raiz
            root_folder_id = storage.get("ROOT_OBJECT_ID")
            print(f"📂 [Bitrix] Storage encontrado. ID: {storage.get('ID')}, Root: {root_folder_id}")
        else:
             print(f"⚠️ [Bitrix] Nenhum storage encontrado. Lista: {storage_list}")
        
        if not root_folder_id:
            # Fallback: Tenta um get no storage default explicito se getlist falhar no index 0
            # Mas vamos assumir que falhou geral
            print("❌ [Bitrix] Não foi possível encontrar a Pasta Raiz para upload.")
            return None

        # 2. Upload para a Pasta (disk.folder.uploadfile)
        # O disk.folder.uploadfile exige 'id' da pasta.
        # DICA: Para evitar erro 400 em multipart, passamos o ID na Query String.
        
        try:
            file_bytes = base64.b64decode(content)
        except Exception as e:
            print(f"❌ [Bitrix] Erro ao decodificar base64 do arquivo: {e}")
            return None

        # Preparar Multipart
        files = {'file': (filename, file_bytes)}
        
        # URL com Parametros (mais seguro para Bitrix + Multipart)
        url = f"{self.webhook_url}/disk.folder.uploadfile.json"
        params = {"id": root_folder_id, "generateUniqueName": "Y"}
        
        async with httpx.AsyncClient() as client:
            try:
                # Nota: Passamos params para o httpx anexar na URL
                response = await client.post(
                    url, 
                    params=params, 
                    data={"generateUniqueName": "Y"}, # Redundante mas seguro
                    files=files, 
                    timeout=60.0
                )
                
                if response.status_code != 200:
                     print(f"❌ [Bitrix] Erro HTTP {response.status_code}: {response.text}")
                     return None

                result = response.json()
                
                # Caso 1: Upload Direto (retornou ID)
                if "result" in result and "ID" in result["result"]:
                    file_id = result["result"]["ID"]
                    print(f"✅ [Bitrix] Arquivo salvo no Disk com ID: {file_id}")
                    return int(file_id)
                # Caso 2: Upload com Redirecionamento (retornou uploadUrl)
                elif "result" in result and "uploadUrl" in result["result"]:
                    upload_url = result["result"]["uploadUrl"]
                    print(f"🔄 [Bitrix] Recebida uploadUrl. Redirecionando upload para: {upload_url}...")
                    
                    # Precisamos reenviar o arquivo para a nova URL
                    # Recriamos o files pointer
                    files_retry = {'file': (filename, file_bytes)}
                    
                    response_upload = await client.post(
                        upload_url,
                        files=files_retry,
                        timeout=60.0
                    )
                    
                    if response_upload.status_code != 200:
                        print(f"❌ [Bitrix] Erro HTTP no Redirecionamento {response_upload.status_code}: {response_upload.text}")
                        return None
                        
                    result_upload = response_upload.json()
                    if "result" in result_upload and "ID" in result_upload["result"]:
                        file_id = result_upload["result"]["ID"]
                        print(f"✅ [Bitrix] Arquivo salvo (após redirect) com ID: {file_id}")
                        return int(file_id)
                    else:
                         print(f"⚠️ [Bitrix] Falha no upload secundário: {result_upload}")
                         return None

                else:
                    print(f"⚠️ [Bitrix] Upload retornou sucesso mas sem ID nem uploadUrl: {result}")
                    return None
                    
            except Exception as e:
                print(f"❌ [Bitrix] Erro no upload para disk: {e}")
                return None


    async def download_disk_file(self, file_id: int) -> Optional[tuple[str, bytes]]:
        """
        Baixa um arquivo do Bitrix Disk.
        Retorna: (filename, content_bytes)
        """
        # 1. Obter metadados e URL de download
        file_info = await self._call_bitrix("disk.file.get", params={"id": file_id})
        
        if not file_info or "DOWNLOAD_URL" not in file_info:
            print(f"❌ [Bitrix] Falha ao obter info do arquivo DISK {file_id}")
            return None
            
        download_url = file_info["DOWNLOAD_URL"]
        filename = file_info.get("NAME", f"downloaded_file_{file_id}")
        
        # 2. Baixar Conteúdo
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(download_url, timeout=60.0)
                if resp.status_code == 200:
                    return filename, resp.content
                else:
                    print(f"❌ [Bitrix] Erro HTTP ao baixar arquivo {file_id}: {resp.status_code}")
                    return None
            except Exception as e:
                print(f"❌ [Bitrix] Erro de conexão ao baixar arquivo {file_id}: {e}")
                return None


    async def create_deal(self, data: TicketCreateRequest) -> int | None:
        """
        Cria o Negócio traduzindo os campos do Front para o Bitrix.
        Retorna deal_id.
        """

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

        # Processar Anexos
        uploaded_file_ids = []
        if data.attachments:
            print(f"📎 [Bitrix] Processando {len(data.attachments)} anexos para o Deal...")
            for att in data.attachments:
                file_id = await self.upload_disk_file(att.get("name"), att.get("content"))
                if file_id:
                    uploaded_file_ids.append(file_id)

        payload = {
            "fields": {
                "TITLE": data.title,
                "TYPE_ID": "SALE",
                "STAGE_ID": "C25:NEW",
                "OPENED": "Y",
                "CATEGORY_ID": 25,
                "CURRENCY_ID": "BRL",
                "SOURCE_ID": "5",
                "CONTACT_ID": contact_id,
                "ASSIGNED_BY_ID": data.resp_id if data.resp_id else "6185",
                "COMMENTS": ("Chamado vindo do Portal HelpDesk"),
                
                # Campos Mapeados com Constantes
                BitrixFields.AREA_SOLICITANTE: data.requester_department,
                BitrixFields.FORMA_CRIACAO: BitrixValues.FORMA_CRIACAO["Automática"],
                BitrixFields.DESCRIPTION: data.description,
                BitrixFields.PORTAL: "1981", # Portal
                BitrixFields.CLIENT_PHONE: data.phone,
                BitrixFields.PROTOCOL_NUMBER: data.matricula,
                BitrixFields.DEPARTAMENTO: dept_id_bitrix,
                BitrixFields.FILIAIS_MATRIZ: filial_id,
                BitrixFields.PRIORIDADE: prioridade_id,
                BitrixFields.CATEGORIA: categoria_id,
                BitrixFields.TIPO_SISTEMA: sistema_id,
                BitrixFields.ASSUNTO_MAP.get(sistema_id): BitrixValues.get_subject_id(
                    data.system_type, data.subject
                ),
                
                # Novo Campo CPF
                BitrixFields.CPF: data.cpf,

                # Campo de Prazo (SLA) Calculado
                BitrixFields.PRAZO: self._calculate_sla_deadline(prioridade_id),
            }
        }

        # Vincular Arquivos ao Campo de Arquivo do Bitrix (se houver)
        if uploaded_file_ids:
             payload["fields"][BitrixFields.ARQUIVO] = uploaded_file_ids

        payload["fields"] = {k: v for k, v in payload["fields"].items() if v}

        print(f"🚀 [Bitrix] Criando Deal '{data.title}' para Depto ID: {dept_id_bitrix}")

        result = await self._call_bitrix("crm.deal.add", json_body=payload, method="POST")

        if result: 
            deal_id = int(result)
            print(f"✅ [Bitrix] Deal criado: {deal_id}")
            return deal_id

        return None


    def _calculate_sla_deadline(self, priority_id: str) -> str:
        """
        Calcula o prazo limite (deadline) baseado na Prioridade do Bitrix.
        Retorna string ISO 8601.
        
        Regras:
        - 1557 (Crítico): +1 Hora
        - 1559 (Alto): +4 Horas
        - 1561 (Médio): +1 Dia
        - 1563 (Baixo): +3 Dias
        """
        if not priority_id:
            return ""

        from datetime import datetime, timedelta
        import pytz

        # Define timezone Brasil/Cuiabá (ou o que o servidor usar)
        # O Bitrix espera ISO 8601. Vamos usar UTC ou local com offset.
        tz = pytz.timezone("America/Cuiaba") 
        now = datetime.now(tz)
        
        deadline = now # fallback

        if priority_id == "1557": # Crítico
            deadline = now + timedelta(hours=1)
        elif priority_id == "1559": # Alto
            deadline = now + timedelta(hours=4)
        elif priority_id == "1561": # Médio
            deadline = now + timedelta(days=1)
        elif priority_id == "1563": # Baixo
            deadline = now + timedelta(days=3)
        else:
            return "" # Se não for nenhum ID conhecido, não manda prazo.

        return deadline.isoformat()


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
        # print(f"📡 [Provider] Buscando Deal {deal_id}...")
        return await self._call_bitrix("crm.deal.get", params={"id": deal_id})


    async def get_responsible(self, ASSIGNED_BY_ID: int) -> Optional[Dict[str, Any]]:
        # print(f"📡 [Provider] Buscando Responsável ID {ASSIGNED_BY_ID}...")
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
        # print(f"📡 [Provider] Buscando Atividade {activity_id}...")
        return await self._call_bitrix("crm.activity.get", params={"id": activity_id})


    async def list_timeline_comments(self, deal_id: int) -> list:
        """Lista os comentários da timeline de um Deal."""
        # crm.timeline.comment.list não é um método padrão documentado tão claramente quanto crm.activity.list
        # Mas vamos tentar filtrar activities do type COMMENT ou usar o método apropriado se existir.
        # Na verdade, comentários de timeline costumam ser atividades com provider ID específico ou método próprio.
        # Porém, a API oficial sugere crm.timeline.comment.list
        
        # print(f"📡 [Provider] Listando comentários da timeline do Deal {deal_id}...")
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


    async def get_timeline_comment(self, comment_id: int) -> Optional[Dict[str, Any]]:
        """Busca um comentário específico da timeline pelo ID."""
        # print(f"📡 [Provider] Buscando Comentário {comment_id}...")
        result = await self._call_bitrix(
            "crm.timeline.comment.get",
            params={"id": comment_id},
            method="GET" # get usa params
        )
        return result


    async def list_activities(self, deal_id: int) -> list:
        """Lista todas as atividades de um Deal."""
        # print(f"📡 [Provider] Listando atividades do Deal {deal_id}...")
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
    

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Busca dados de um usuário Bitrix pelo ID"""
        # print(f"📡 [Provider] Buscando Usuário ID {user_id}...")
        users_list = await self._call_bitrix("user.get", params={"ID": user_id})

        if users_list and isinstance(users_list, list) and len(users_list) > 0:
            return users_list[0]
            
        return None


    async def get_file_url(self, file_id: int) -> Optional[str]:
        """Tenta obter uma URL de visualização/download para o arquivo no Disk"""
        meta = await self.get_disk_file(file_id)
        if meta:
            # Bitrix Disk File object tem DETAIL_URL, DOWNLOAD_URL, etc.
            # O DOWNLOAD_URL é autenticado, mas o DETAIL_URL é a pagina de visualização interna.
            # Para download autenticado sem sessão de usuário, precisaríamos proxy ou token.
            # Vamos salvar o DOWNLOAD_URL que vem na API, que geralmente contém um token temporário ou exige auth.
            # No entanto, para o uso no front, talvez seja melhor o DETAIL_URL que abre no bitrix.
            # Mas o usuário pediu File URL. Vamos tentar o DOWNLOAD_URL.
            return meta.get("DOWNLOAD_URL")
        return None
