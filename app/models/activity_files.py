# app/models/activity_files.py
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class ActivityFileModel(Base):
    __tablename__ = 'activity_files'

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Relacionamento com Activity
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)
    
    # ID do arquivo no Bitrix (para referência)
    bitrix_file_id: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Caminho/URL no MinIO ou Storage
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Nome original do arquivo
    filename: Mapped[str] = mapped_column(String(255), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relacionamento reverso
    activity = relationship("ActivityModel", back_populates="files")

# Query para criação da tabela 
"""
CREATE TABLE activity_files (
    id SERIAL PRIMARY KEY,
    activity_id INTEGER NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
    bitrix_file_id INTEGER,
    file_url TEXT NOT NULL,
    filename VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_activity_files_activity_id ON activity_files (activity_id);
"""
