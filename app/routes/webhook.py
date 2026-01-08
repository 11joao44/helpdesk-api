from fastapi import APIRouter, Request, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import session_db
from app.providers.bitrix import BitrixProvider
from app.services.deals import DealService
from app.services.webhook import WebhookService
from app.repositories.deals import DealRepository
from app.repositories.activity import ActivityRepository
from app.schemas.deals import DealCardSchema
from typing import List
from app.core.logger import logger

router = APIRouter(tags=["Webhook Bitrix24"])

async def debug_request(request: Request):
    form_data = await request.form()
    print("Evento recebido: ", form_data.get("event"))
    if form_data.get("data[FIELDS][ID]") != "837":
        return
    print("\n" + "="*50)
    print(f"📦 Quantidade de campos: {len(form_data)}")
    print(f"📦 form_data campos: {form_data}")
    for key, value in form_data.items():
        print(f"   👉 {key}: {value}")
    print("="*50 + "\n")

def get_webhook_service(db: AsyncSession = Depends(session_db)) -> WebhookService:
    return WebhookService(deal_repo=DealRepository(db), activity_repo=ActivityRepository(db), provider=BitrixProvider())

@router.post("/webhook-bitrix24", status_code=status.HTTP_200_OK)
async def handle_bitrix_webhook(request: Request,  service: WebhookService = Depends(get_webhook_service)):
    """Endpoint oficial de integração. Recebe o ID -> Busca Detalhes -> Salva no Banco."""
    # await debug_request(request)
    form_data = await request.form()
    logger.info("Evento recebido: ", form_data.get("event"))
    await service.process_webhook(request)
    return "OK"

@router.get("/kanban/cards", response_model=List[DealCardSchema])
async def get_kanban_cards(session: AsyncSession = Depends(session_db)):
    repo = DealRepository(session)
    deals = await repo.get_deals_for_kanban()
    return deals
