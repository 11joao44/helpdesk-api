from sqlalchemy import ForeignKey, Integer, String, DateTime, Text, Boolean, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING: from app.models.activity import ActivityModel
if TYPE_CHECKING: from app.models.users import UserModel

class DealModel(Base):
    __tablename__ = 'deals'

    id: Mapped[int] = mapped_column(primary_key=True)
    deal_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    stage_id: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    opened: Mapped[Optional[str]] = mapped_column(String(1), index=True)
    closed: Mapped[Optional[str]] = mapped_column(String(1), index=True)
    created_by_id: Mapped[Optional[str]] = mapped_column(String(10), index=True)
    modify_by_id: Mapped[Optional[str]] = mapped_column(String(10))
    moved_by_id: Mapped[Optional[str]] = mapped_column(String(10))
    last_activity_by_id: Mapped[Optional[str]] = mapped_column(String(10))
    last_communication_time: Mapped[Optional[str]] = mapped_column(String(19))
    close_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    date_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    begin_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    requester_department: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    assignee_department: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    service_category: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    system_type: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    priority: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    matricula: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    responsible: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    responsible_email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    requester_email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    
    # New Foreign Key
    responsible_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    # Attachments
    file_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Notifications
    is_unread: Mapped[bool] = mapped_column(Boolean, default=False, server_default='false')

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now() 
    )

    activities: Mapped[List["ActivityModel"]] = relationship(
        "ActivityModel", 
        back_populates="deal",
        cascade="all, delete-orphan" 
    )

    files: Mapped[List["DealFileModel"]] = relationship(
        "DealFileModel", 
        back_populates="deal",
        cascade="all, delete-orphan" 
    )

    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    user: Mapped[Optional["UserModel"]] = relationship("app.models.users.UserModel", back_populates="deals", foreign_keys=[user_id])

    # Relacionamento FK Real
    responsible_user_rel: Mapped[Optional["UserModel"]] = relationship(
        "UserModel",
        foreign_keys=[responsible_id],
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Deal(id={self.id}, title='{self.title}')>"


# CREATE TABLE deals (
#     id SERIAL PRIMARY KEY,
#     deal_id INTEGER NOT NULL UNIQUE,
#     title VARCHAR(255),
#     description TEXT,
#     stage_id VARCHAR(15),
#     opened VARCHAR(1),
#     closed VARCHAR(1),
#     created_by_id VARCHAR(10),
#     modify_by_id VARCHAR(10),
#     moved_by_id VARCHAR(10),
#     responsible VARCHAR(30),
#     status_img TEXT,
#     last_activity_by_id VARCHAR(10),
# 	last_communication_time VARCHAR(19),
#     close_date TIMESTAMP WITH TIME ZONE,
#     begin_date TIMESTAMP WITH TIME ZONE,
#     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
#     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
#     requester_email VARCHAR(255),
# );
