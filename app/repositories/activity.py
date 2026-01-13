from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from app.models import ActivityModel

class ActivityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


    async def get_by_activity_id(self, b_id: int) -> ActivityModel | None:
        from sqlalchemy.orm import selectinload
        result = await self.session.execute(
            select(ActivityModel)
            .options(selectinload(ActivityModel.files), selectinload(ActivityModel.deal))
            .where(ActivityModel.activity_id == b_id)
        )
        return result.scalar_one_or_none()


    async def get_activity_internal_id(self, activity_id: int) -> int | None:
        """Busca o ID interno (PK) baseado no ID do Bitrix"""
        activity = await self.get_by_activity_id(activity_id)
        return activity.id if activity else None


    async def upsert_ticket(self, data: dict) -> ActivityModel:
        ticket = await self.get_by_activity_id(data["activity_id"])
        if ticket:
            for key, value in data.items():
                if hasattr(ticket, key): setattr(ticket, key, value)
        else:
            ticket = ActivityModel(**data)
            self.session.add(ticket)
        await self.session.flush()
        return ticket


    async def upsert_activity(self, data: dict) -> ActivityModel:
        stmt = select(ActivityModel).where(ActivityModel.activity_id == data["activity_id"])
        result = await self.session.execute(stmt)
        activity = result.scalar_one_or_none()
        
        if activity:
            for key, value in data.items():
                if hasattr(activity, key):
                    setattr(activity, key, value)
        else:
            activity = ActivityModel(**data)
            self.session.add(activity)
            
            try:
                await self.session.flush()
            except IntegrityError:
                await self.session.rollback()
                result = await self.session.execute(stmt)
                activity = result.scalar_one() # Agora TEM que existir
                
                for key, value in data.items():
                    if hasattr(activity, key):
                        setattr(activity, key, value)
                        
        return activity
        
    async def sync_files(self, activity_id: int, files_data: list[dict]):
        """Sincroniza os arquivos de uma atividade (Remove antigos e insere novos - simples)"""
        if not files_data: return

        # Para simplificar, vamos inserir apenas os novos. 
        # Numa lógica mais robusta, verificaria se já existe pelo 'bitrix_file_id'.
        
        # Importação aqui para evitar erros de ciclo se não tiver no topo
        from app.models.activity_files import ActivityFileModel

        # Opcional: Limpar arquivos anteriores dessa activity? 
        # await self.session.execute(delete(ActivityFileModel).where(ActivityFileModel.activity_id == activity_id))
        
        for f in files_data:
            # Verifica duplicidade
            stmt = select(ActivityFileModel).where(ActivityFileModel.activity_id == activity_id)
            
            b_id = f.get("bitrix_file_id")
            f_url = f.get("file_url")

            if b_id and b_id != 0:
                stmt = stmt.where(ActivityFileModel.bitrix_file_id == b_id)
            elif f_url:
                stmt = stmt.where(ActivityFileModel.file_url == f_url)
            else:
                # Se não tem ID nem URL, pula
                continue

            existing = await self.session.execute(stmt)
            if existing.scalar_one_or_none():
                continue

            new_file = ActivityFileModel(**f)
            self.session.add(new_file)
            
        await self.session.flush()
