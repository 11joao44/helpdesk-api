from pydantic import BaseModel
from datetime import datetime
from typing import Optional



class ActivityFileSchema(BaseModel):
    id: int
    bitrix_file_id: Optional[int]
    file_url: str
    filename: Optional[str]
    created_at: datetime

    class Config: from_attributes = True    


class ActivitySchema(BaseModel):
    id: int
    
    # ID do Bitrix
    activity_id: int
    
    # Chave Estrangeira
    deal_id: int

    # Campos de Tipo/Provedor
    owner_type_id: Optional[str] 
    type_id: Optional[str] 
    provider_id: Optional[str]
    provider_type_id: Optional[str]
    
    # Detalhes
    direction: Optional[str]
    subject: Optional[str] = None
    priority: Optional[str]
    responsible_id: Optional[str]
    
    # Conteúdo
    description: Optional[str]
    body_html: Optional[str]
    description_type: Optional[str]
    
    # E-mails
    sender_email: Optional[str]
    to_email: Optional[str]
    from_email: Optional[str]
    receiver_email: Optional[str]
    
    # Metadados
    author_id: Optional[str]
    editor_id: Optional[str]
    read_confirmed: Optional[int]
    
    # Arquivos (Legado)
    file_id: Optional[int]
    file_url: Optional[str]
    
    # Arquivos (Lista)
    files: list[ActivityFileSchema] = []

    # Datas
    created_at_bitrix: Optional[datetime]
    created_at: datetime

    class Config: from_attributes = True