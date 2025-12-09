from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import session_db
from app.services.deals import DealService
from app.schemas.tickets import TicketCreateRequest, TicketCreatedResponse

router = APIRouter(tags=['Tickets'])

def get_service(session: AsyncSession = Depends(session_db)):
    return DealService(session)

@router.post("/ticket", response_model=TicketCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket_endpoint(data: TicketCreateRequest, service: DealService = Depends(get_service)):
    """Cria um ticket no Bitrix e salva no banco local."""
    print(f"📝 Request do data: {data}")
    return await service.create_ticket(data)