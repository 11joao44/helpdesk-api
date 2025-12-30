from typing import List, Dict
from fastapi import WebSocket
from app.core.config import logger

class ConnectionManager:
    def __init__(self):
        # Mapeia deal_id -> Lista de WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, deal_id: str):
        await websocket.accept()
        if deal_id not in self.active_connections:
            self.active_connections[deal_id] = []
        self.active_connections[deal_id].append(websocket)
        logger.info(f"🔌 WebSocket conectado no Deal {deal_id}. Total: {len(self.active_connections[deal_id])}")

    def disconnect(self, websocket: WebSocket, deal_id: str):
        if deal_id in self.active_connections:
            if websocket in self.active_connections[deal_id]:
                self.active_connections[deal_id].remove(websocket)
                logger.info(f"🔌 WebSocket desconectado do Deal {deal_id}.")
            
            if not self.active_connections[deal_id]:
                del self.active_connections[deal_id]

    async def broadcast(self, message: dict, deal_id: str):
        if deal_id in self.active_connections:
            logger.info(f"📢 Broadcasting mensagem para Deal {deal_id} ({len(self.active_connections[deal_id])} conexões)")
            for connection in self.active_connections[deal_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"❌ Erro ao enviar mensagem WS: {e}")
                    # Remove dead connections
                    self.disconnect(connection, deal_id)
        else:
            logger.warning(f"⚠️ Nenhuma conexão ativa encontrada para o Deal {deal_id}. Broadcast ignorado.")

# Singleton global manager
manager = ConnectionManager()
