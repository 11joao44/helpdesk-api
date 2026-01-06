from fastapi import APIRouter, UploadFile, File, Depends
from app.services.upload import UploadService
from app.schemas.upload import UploadResponse

router = APIRouter(tags=["Uploads"])

def get_service():
    return UploadService()

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    service: UploadService = Depends(get_service)
):
    """
    Endpoint genérico para upload de arquivos (imagens para editor, etc).
    Retorna a URL do arquivo para ser usada no frontend.
    """
    return await service.upload_file(file)
