from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime
from app.schemas.activity import ActivitySchema
from app.schemas.users import UserOut
from pydantic import Field, model_validator


class DealCardCreateSchema(BaseModel):
    id: int
    deal_id: int
    title: Optional[str]
    description: Optional[str]
    stage_id: Optional[str]
    opened: Optional[bool]
    closed: Optional[bool] = None
    created_by_id: Optional[str]
    requester_department: Optional[str] = None
    assignee_department: Optional[str] = None
    service_category: Optional[str] = None
    system_type: Optional[str] = None
    priority: Optional[str] = None
    matricula: Optional[str] = None

    @field_validator("opened", "closed", mode="before")
    def parse_boolean_fields(cls, v):
        if isinstance(v, str):
            return v.upper() == "Y"
        return v

    class Config:
        from_attributes = True


class DealCardSchema(DealCardCreateSchema):
    modify_by_id: Optional[str]
    moved_by_id: Optional[str]
    last_activity_by_id: Optional[str]
    last_communication_time: Optional[str]
    close_date: Optional[datetime]
    begin_date: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    # Campos que retornam para o front (mantendo contrato)
    # Campos que retornam para o front (mantendo contrato)
    responsible: Optional[str] = None
    responsible_email: Optional[str] = None
    requester_email: Optional[str] = None
    responsible_profile_picture_url: Optional[str] = None
    
    requester_name: Optional[str] = None
    requester_profile_picture_url: Optional[str] = None
    file_url: Optional[str] = None
    file_id: Optional[int] = None
    activities: List[ActivitySchema] = []

    # Campo oculto para carregar dados do relacionamento (não vai para o JSON final)
    responsible_user_rel: Optional[UserOut] = Field(default=None, exclude=True)
    user: Optional[UserOut] = Field(default=None, exclude=True)

    @model_validator(mode='after')
    def fill_computed_details(self):
        # 1. Preenche dados do responsável (Legacy Support)
        if not self.responsible and self.responsible_user_rel:
            self.responsible = self.responsible_user_rel.full_name
            
        if not self.responsible_email and self.responsible_user_rel:
            self.responsible_email = self.responsible_user_rel.email
            
        if not self.matricula and self.responsible_user_rel:
             self.matricula = self.responsible_user_rel.matricula

        # 2. Preenche nome do solicitante
        if not self.requester_name and self.user:
            self.requester_name = self.user.full_name
             
        return self

    class Config:
        from_attributes = True
