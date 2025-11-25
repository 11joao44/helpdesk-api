from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

# DTOs (Data Transfer Objects) para padronizar a comunicação

class TicketCreateRequest(BaseModel):
    title: str
    description: str
    requester_id: int
    priority: int  # 0=Low, 1=Medium, 2=High

class TicketResponse(BaseModel):
    external_id: str  # ID no sistema externo (ex: 754 no Bitrix)
    status: str
    link: Optional[str] = None

class ITicketProvider(ABC):
    """
    Interface Abstrata.
    O Service só vai enxergar isso aqui.
    """
    
    @abstractmethod
    async def create_ticket(self, data: TicketCreateRequest) -> TicketResponse:
        pass

    @abstractmethod
    async def update_status(self, external_id: str, status: str) -> bool:
        pass

    @abstractmethod
    async def add_comment(self, external_id: str, message: str, author_id: int) -> bool:
        pass