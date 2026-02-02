from pydantic import BaseModel, EmailStr, field_validator
from re import sub as re_sub
from typing import Optional, List, Dict


class TicketCreateRequest(BaseModel):
    full_name: str
    title: str
    description: str
    subject: str
    user_id: int
    resp_id: str
    assignee_department: str
    email: EmailStr
    filial: str
    phone: str
    cpf: str
    priority: Optional[str] = "Médio/Normal"
    matricula: str
    requester_department: str
    service_category: str
    system_type: str
    attachments: Optional[List[Dict[str, str]]] = []

    @field_validator("phone")
    def validate_phone(cls, v):
        nums = re_sub(r"\D", "", v)

        if len(nums) in [10, 11]:
            return f"55{nums}"

        return nums


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


class TicketSendEmail(BaseModel):
    deal_id: int
    from_email: str
    to_email: str
    subject: str
    message: str
    attachments: Optional[List[Dict[str, str]]] = []


class TicketCloseRequest(BaseModel):
    deal_id: int
    rating: Optional[int] = None
    comment: Optional[str] = None


class TicketAddCommentRequest(BaseModel):
    deal_id: int
    message: str
    email: Optional[str] = None
    user_id: Optional[int] = None
    attachments: Optional[List[Dict[str, str]]] = []
