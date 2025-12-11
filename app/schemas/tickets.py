from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class TicketCreateRequest(BaseModel):
    full_name: str
    title: str
    description: str
    user_id: int
    resp_id: str
    assignee_department: str
    email: EmailStr
    filial: str
    phone: str
    priority: str
    matricula: str
    requester_department: str
    service_category: str
    system_type: str

# --- O QUE RECEBEMOS (Input) ---
class TicketCreate(BaseModel):
    title: str
    description: str
    stage_id: Optional[str] = "NEW"
    value: float = 0.0
    responsible_id: int = 1

# --- O QUE DEVOLVEMOS (Output) ---
# Usamos apenas o ID para ser simples e direto na criação
class TicketCreatedResponse(BaseModel):
    id: int
    deal_id: int
    message: str = "Ticket criado com sucesso"
    data: TicketCreateRequest