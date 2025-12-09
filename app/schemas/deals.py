from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.schemas.activity import ActivitySchema

class DealCardSchema(BaseModel):
    id: int
    deal_id: int
    title: Optional[str]
    clean_title: Optional[str]
    description: Optional[str]
    stage_id: Optional[str]
    opened: Optional[str]
    closed: Optional[str]
    created_by_id: Optional[str]
    modify_by_id: Optional[str]
    moved_by_id: Optional[str]
    last_activity_by_id: Optional[str]
    last_communication_time: Optional[str]
    close_date: Optional[datetime]
    begin_date: Optional[datetime]
    activities: List[ActivitySchema] = []

    class Config: from_attributes = True
