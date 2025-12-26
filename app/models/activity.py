# app/models/activities.py
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.deals import DealModel
from app.models.activity_files import ActivityFileModel
if TYPE_CHECKING: from app.models.users import UserModel

class ActivityModel(Base):
    __tablename__ = 'activities' # Nome plural correto

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # ID do Bitrix
    activity_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    
    # Chave Estrangeira
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id"), nullable=False)

    # Campos de Tipo/Provedor
    owner_type_id: Mapped[Optional[str]] = mapped_column(String(5))
    type_id: Mapped[Optional[str]] = mapped_column(String(5))
    provider_id: Mapped[Optional[str]] = mapped_column(String(50))
    provider_type_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Detalhes
    direction: Mapped[Optional[str]] = mapped_column(String(10))
    subject: Mapped[Optional[str]] = mapped_column(String(255))
    priority: Mapped[Optional[str]] = mapped_column(String(5))
    responsible_id: Mapped[Optional[str]] = mapped_column(String(20))
    responsible_name: Mapped[Optional[str]] = mapped_column(String(255))
    responsible_email: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Conteúdo
    description: Mapped[Optional[str]] = mapped_column(Text)
    body_html: Mapped[Optional[str]] = mapped_column(Text)
    description_type: Mapped[Optional[str]] = mapped_column(String(5))
    
    # E-mails
    sender_email: Mapped[Optional[str]] = mapped_column(String(255))
    to_email: Mapped[Optional[str]] = mapped_column(String(255))
    from_email: Mapped[Optional[str]] = mapped_column(String(255))
    receiver_email: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Metadados
    author_id: Mapped[Optional[str]] = mapped_column(String(20))
    editor_id: Mapped[Optional[str]] = mapped_column(String(20))
    read_confirmed: Mapped[Optional[int]] = mapped_column(Integer) # Bitrix pode mandar '1' string, converteremos
    
    # Arquivos
    file_id: Mapped[Optional[int]] = mapped_column(Integer)
    file_url: Mapped[Optional[str]] = mapped_column(Text)

    # Datas
    created_at_bitrix: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relacionamento
    deal: Mapped["DealModel"] = relationship("DealModel", back_populates="activities")
    files: Mapped[list["ActivityFileModel"]] = relationship("ActivityFileModel", back_populates="activity", cascade="all, delete-orphan")

    # Relacionamento por e-mail para pegar foto do responsável
    responsible_user: Mapped[Optional["UserModel"]] = relationship(
        "UserModel",
        primaryjoin="foreign(ActivityModel.responsible_email) == UserModel.email",
        viewonly=True,
    )


# Query para criação da tabela 
"""
CREATE TABLE activities (
    id SERIAL PRIMARY KEY,
    
    -- IDs
    activity_id INTEGER NOT NULL UNIQUE,
    deal_id INTEGER NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
    
    -- Tipos
    owner_type_id VARCHAR(5),
    type_id VARCHAR(5),
    provider_id VARCHAR(50),
    provider_type_id VARCHAR(50),
    
    -- Detalhes (Mantive a primeira definição de 'direction')
    direction VARCHAR(10),    
    subject VARCHAR(255),
    priority VARCHAR(5),
    
    -- Conteúdo
    description TEXT,
    body_html TEXT,
    description_type VARCHAR(5),
    
    -- E-mails
    sender_email VARCHAR(255),
    from_email VARCHAR(255),
    to_email VARCHAR(255),    -- Aumentei para 255 (20 corta e-mails comuns)
    receiver_email VARCHAR(255),
    
    -- Metadados
    -- Metadados
    responsible_id VARCHAR(20),
    responsible_name VARCHAR(255),
    responsible_email VARCHAR(255),
    author_id VARCHAR(20),
    editor_id VARCHAR(20),
    read_confirmed INTEGER,   -- Verifique se aqui tinha vírgula no seu código anterior
    
    -- Arquivos
    file_id INTEGER,          -- O erro estava apontando aqui
    file_url TEXT,
    
    -- Datas
    created_at_bitrix TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices (Ajustados para a tabela 'activities')
CREATE INDEX ix_activities_deal_id ON activities (deal_id);
CREATE INDEX ix_activities_bitrix_id ON activities (activity_id);
"""
