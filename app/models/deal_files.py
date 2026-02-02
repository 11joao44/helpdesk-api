from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class DealFileModel(Base):
    __tablename__ = 'deal_files'

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Relacionamento com Deal
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)
    
    # ID do arquivo no Bitrix (para referência)
    bitrix_file_id: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Caminho/URL no MinIO ou Storage
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Nome original do arquivo
    filename: Mapped[str] = mapped_column(String(255), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relacionamento reverso
    deal = relationship("DealModel", back_populates="files")
