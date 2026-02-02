from fastapi import UploadFile, HTTPException
from app.providers.storage import StorageProvider
from app.schemas.upload import UploadResponse
import uuid

class UploadService:
    def __init__(self):
        self.storage = StorageProvider()

    async def upload_file(self, file: UploadFile) -> UploadResponse:
        try:
            # Ler o conteúdo do arquivo
            content = await file.read()
            
            # Gerar nome único para evitar colisão
            # Mantém a extensão original se possível
            ext = ""
            if file.filename and "." in file.filename:
                ext = f".{file.filename.split('.')[-1]}"
            
            unique_filename = f"{uuid.uuid4()}{ext}"
            
            # Fazer upload para o MinIO
            # O StorageProvider.upload_file retorna o object_name (path no bucket)
            # Vamos salvar numa pasta 'uploads' para separar dos anexos de email se quiser, 
            # mas o provider atual já prefixa com 'attachments/'. 
            # Vamos passar apenas o nome do arquivo e deixar o provider gerenciar, 
            # ou podemos gerenciar o prefixo se alterarmos o provider.
            # O provider atual faz: object_name = f"attachments/{filename}"
            # Então passamos unique_filename.
            
            object_name = self.storage.upload_file(content, unique_filename)
            
            if not object_name:
                raise HTTPException(status_code=500, detail="Failed to upload file to storage")

            # Gerar URL assinada (ou pública se configurado)
            # Como solicitado, retornamos uma URL acessível.
            # O StorageProvider.get_presigned_url gera link temporário. 
            # Para uso em editor (img src), o link precisa durar.
            # Vamos colocar 7 dias (168h) que é um maximo comum para signed urls v4.
            # Se precisar de mais, o bucket deve ser público.
            url = self.storage.get_presigned_url(object_name, expiration_hours=168)
            
            if not url:
                raise HTTPException(status_code=500, detail="Failed to generate file URL")

            return UploadResponse(
                url=url,
                filename=file.filename or unique_filename,
                content_type=file.content_type
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
