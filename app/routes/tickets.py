from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import session_db
from app.repositories.deals import DealRepository
from app.schemas.deals import DealCardCreateSchema, DealCardSchema
from app.services.deals import DealService
from app.schemas.tickets import TicketCloseRequest, TicketCreateRequest, TicketSendEmail, TicketAddCommentRequest
from app.providers.storage import StorageProvider

router = APIRouter(tags=["Tickets"])


def get_service(session: AsyncSession = Depends(session_db)):
    return DealService(session)

def get_storage():
    return StorageProvider()

def _sign_deals(deals: List, storage: StorageProvider):
    """Percorre os deals e gera links assinados para os anexos"""
    for deal in deals:
        # --- Deal Responsible Avatar ---
        if hasattr(deal, "responsible_user_rel") and deal.responsible_user_rel and deal.responsible_user_rel.profile_picture:
             deal.responsible_profile_picture_url = storage.get_presigned_url(deal.responsible_user_rel.profile_picture, expiration_hours=168)
        
        # --- Deal Requester Avatar ---
        # Assumindo que deal.user é o solicitante/dono interno
        if hasattr(deal, "user") and deal.user and deal.user.profile_picture:
             deal.requester_profile_picture_url = storage.get_presigned_url(deal.user.profile_picture, expiration_hours=168)

        for activity in deal.activities:
            # --- Activity Responsible Avatar ---
            if hasattr(activity, "responsible_user") and activity.responsible_user and activity.responsible_user.profile_picture:
                 activity.responsible_profile_picture_url = storage.get_presigned_url(activity.responsible_user.profile_picture, expiration_hours=168)

            # 1. Tratamento para campo legado (file_url)
            if activity.file_url and not activity.file_url.startswith("http"):
                # Se não começa com http, é uma key do MinIO
                signed_url = storage.get_presigned_url(activity.file_url)
                if signed_url:
                    activity.file_url = signed_url
            
            # 2. Tratamento para lista de arquivos (files)
            if activity.files:
                for f in activity.files:
                    if f.file_url and not f.file_url.startswith("http"):
                        signed_f_url = storage.get_presigned_url(f.file_url)
                        if signed_f_url:
                            f.file_url = signed_f_url
    return deals


@router.post("/send-email")
async def send_email_route(payload: TicketSendEmail, service: DealService = Depends(get_service)):
    """Cria um ticket no Bitrix e salva no banco local."""
    return await service.send_email(payload)


@router.post(
    "/ticket", response_model=DealCardCreateSchema, status_code=status.HTTP_201_CREATED
)
async def create_ticket_endpoint(
    data: TicketCreateRequest, service: DealService = Depends(get_service)
):
    """Cria um ticket no Bitrix e salva no banco local."""
    return await service.create_ticket(data)


@router.post("/close-ticket")
async def close_ticket_route(
    payload: TicketCloseRequest, service: DealService = Depends(get_service)
):
    """Encerra um ticket, move para etapa 'Ganho' no Bitrix e salva avaliação."""
    return await service.close_ticket(payload)


@router.post("/ticket/comment")
async def add_ticket_comment(payload: TicketAddCommentRequest, service: DealService = Depends(get_service)):
    """Adiciona um comentário (texto e/ou anexos) a um ticket no Bitrix."""
    success = await service.add_comment(
        deal_id=payload.deal_id,
        message=payload.message,
        attachments=payload.attachments
    )
    
    if success:
        return {"status": "success", "message": "Comentário adicionado com sucesso"}
    
    return {"status": "error", "message": "Falha ao adicionar comentário no Bitrix"}


@router.get("/tickets/{user_id}", response_model=List[DealCardSchema])
async def tickets(user_id: int, session: AsyncSession = Depends(session_db), storage: StorageProvider = Depends(get_storage)):
    repo = DealRepository(session)
    deals = await repo.get_deals_by_user_id(user_id)
    return _sign_deals(deals, storage)


@router.get("/tickets-opens/{user_id}", response_model=List[DealCardSchema])
async def tickets(user_id: int, session: AsyncSession = Depends(session_db), storage: StorageProvider = Depends(get_storage)):
    repo = DealRepository(session)
    deals = await repo.get_deals_by_user_id_open(user_id)
    return _sign_deals(deals, storage)


@router.get("/tickets-responsible/{user_id}", response_model=List[DealCardSchema])
async def tickets_responsible(user_id: int, session: AsyncSession = Depends(session_db), storage: StorageProvider = Depends(get_storage)):
    repo = DealRepository(session)
    deals = await repo.get_deals_by_responsible_id(user_id)
    print("deals: ", deals)
    return _sign_deals(deals, storage)


@router.get("/deal/{deal_id}/{user_id}", response_model=List[DealCardSchema])
async def deal(deal_id: int, user_id: int, session: AsyncSession = Depends(session_db), storage: StorageProvider = Depends(get_storage)):
    repo = DealRepository(session)
    deals = await repo.get_deal_by_id(user_id, deal_id)
    return _sign_deals(deals, storage)
