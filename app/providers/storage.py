import io
import mimetypes
from urllib.parse import urlparse
from datetime import timedelta
from minio import Minio
from minio.error import S3Error
from app.core.config import settings

from urllib3 import PoolManager

class StorageProvider:
    def __init__(self):
        # Remove protocolo caso venha na variável de ambiente (SDK espera host:port)
        raw_endpoint = settings["MINIO_ENDPOINT"]
        endpoint = raw_endpoint.replace("http://", "").replace("https://", "") if raw_endpoint else ""

        # FALLBACK: Se o endpoint for o do usuário e não tiver porta, adiciona 8086
        if "carvalima-teste.duckdns.org" in endpoint and ":" not in endpoint:
            endpoint = f"{endpoint}:8086"
            print(f"⚠️ [MinIO] Porta ausente no .env. Forçando :8086 para compatibilidade.")

        if not endpoint:
            # Se não houver endpoint, o MinIO gera URLs quebradas tipo https:///bucket...
            # Verifica se foi uma falha de configuração
            if not raw_endpoint:
                 error_msg = "❌ [MinIO] A variável de ambiente IP_SERVIDOR_NFS (ou MINIO_ENDPOINT) não está definida ou está vazia."
                 print(error_msg)
                 # Podemos levantar erro ou usar um fallback seguro (mas o fallback ideal depende do ambiente)
                 # Vamos levantar erro para forçar correção
                 raise ValueError(error_msg)
        

        self.endpoint = endpoint
        print(f"🔌 [MinIO] Endpoint Configurado: '{endpoint}' (Secure=True)")

        self.client = Minio(
            endpoint=endpoint,
            access_key=settings["MINIO_ACCESS_KEY"],
            secret_key=settings["MINIO_SECRET_KEY"],
            secure=True,
            http_client=PoolManager(
                timeout=120.0,
                retries=3,
                maxsize=10
            )
        )
        self.bucket_name = "anexos-email-bitrix"
        
        try:
            self._ensure_bucket()
        except Exception as e:
            print(f"⚠️ [MinIO] Não foi possível conectar ao Storage na inicialização: {e}")

    def _ensure_bucket(self):
        """Garante que o bucket existe ao iniciar."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"📦 [MinIO] Bucket '{self.bucket_name}' criado.")
        except Exception as err:
             print(f"⚠️ [MinIO] Erro ao verificar bucket: {err}")

    def upload_file(self, file_data: bytes, filename: str) -> str | None:
        """Faz upload de bytes para o MinIO. Retorna o 'Object Name' (Key) salvo."""
        try:
            content_type, _ = mimetypes.guess_type(filename)
            if not content_type:
                content_type = "application/octet-stream"

            data_stream = io.BytesIO(file_data)
            object_name = f"attachments/{filename}"

            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=data_stream,
                length=len(file_data),
                content_type=content_type
            )
            
            print(f"✅ [MinIO] Upload Sucesso: {object_name}")
            return object_name

        except Exception as e:
            print(f"❌ [MinIO] Erro no upload: {e}")
            return None

    def get_presigned_url(self, object_name: str, expiration_hours: int = 2) -> str | None:
        """Gera uma URL temporária (GET) para acessar o arquivo."""
        if not object_name: return None
        
        # Se for URL completa, tenta extrair a chave (path) relativa
        if object_name.startswith("http"):
             # Extrai componentes da URL
             parsed = urlparse(object_name)
             path_parts = parsed.path.lstrip('/').split('/', 1)
             
             # Verifica se identificamos nosso bucket na URL (Host ou Path)
             # Casos:
             # 1. Host da URL bate com o Endpoint configurado (self.endpoint)
             # 2. Caminho da URL começa com o nome do bucket (self.bucket_name) - útil se host for diferente (IP vs Domain)
             is_my_bucket = False
             
             if self.endpoint in object_name:
                 is_my_bucket = True
             elif len(path_parts) > 1 and path_parts[0] == self.bucket_name:
                 is_my_bucket = True
                 
             if is_my_bucket:
                 # Se confirmou ser nosso bucket, tenta extrair o object_name real
                 if len(path_parts) > 1 and path_parts[0] == self.bucket_name:
                     object_name = path_parts[1] # folder/file.jpg
                 else:
                     # Fallback estranho (host bateu, mas path não tem bucket?), retorna original
                     return object_name
             else:
                 # Se for URL externa (ex: google user photo) e não bateu bucket/host, retorna como está
                 return object_name

        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=timedelta(hours=expiration_hours)
            )
            return url
        except Exception as e:
            print(f"❌ [MinIO] Erro ao gerar presigned url: {e}")
            return None
