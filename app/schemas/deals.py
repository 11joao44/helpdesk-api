from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime
from app.schemas.activity import ActivitySchema


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
    responsible: Optional[str] = None
    responsible_email: Optional[str] = None
    activities: List[ActivitySchema] = []

    class Config:
        from_attributes = True
