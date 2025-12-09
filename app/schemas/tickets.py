from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class TicketCreateRequest(BaseModel):
    title: str
    description: str
    user_id: int
    resp_id: str
    assigneeDepartment: str
    email: EmailStr
    filial: str
    name: str
    phone: str
    priority: str
    matricula: str
    requesterDepartment: str
    serviceCategory: str
    systemType: str

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