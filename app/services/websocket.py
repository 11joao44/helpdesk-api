from typing import List, Dict
from fastapi import WebSocket
from app.core.config import logger

class WebSocketManager:
    def __init__(self):
        self.users: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, deal_id: str):
        await websocket.accept()
        if deal_id not in self.users: self.users[deal_id] = []
        logger.info(f"🔌 WebSocket lista de usuários conectados: {self.users[deal_id]}")
        logger.info(f"🔌 WebSocket lista de usuários conectados: {self.users}")
        self.users[deal_id].append(websocket)
        logger.info(f"🔌 WebSocket conectado na sala {deal_id}. Total: {len(self.users[deal_id])}")

    def disconnect(self, websocket: WebSocket, deal_id: str):
        if deal_id in self.users:
            if websocket in self.users[deal_id]:
                self.users[deal_id].remove(websocket)
                logger.info(f"🔌 WebSocket desconectado do Deal {deal_id}.")
            
            if not self.users[deal_id]: del self.users[deal_id]

    async def broadcast(self, message: dict, deal_id: str):
        if deal_id in self.users:
            for connection in self.users[deal_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"❌ Erro ao enviar mensagem WS: {e}")
                    self.disconnect(connection, deal_id)
        else:
            logger.warning(f"⚠️ Nenhuma conexão ativa encontrada para o Deal {deal_id}. Broadcast ignorado.")

manager = WebSocketManager()
