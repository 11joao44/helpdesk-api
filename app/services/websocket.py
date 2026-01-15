from typing import List, Dict
from fastapi import WebSocket
from app.core.config import logger

class WebSocketManager:
    def __init__(self):
        self.users: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, deal_id: str, user = None):
        await websocket.accept()
        if deal_id not in self.users: self.users[deal_id] = []
        
        # Armazena tupla (websocket, user) ou objeto customizado
        connection_info = {"ws": websocket, "user": user}
        self.users[deal_id].append(connection_info)
        
        user_name = user.full_name if user else "Anonimo"
        logger.info(f"🔌 WebSocket conectado na sala {deal_id}. User: {user_name}. Total: {len(self.users[deal_id])}")

    def disconnect(self, websocket: WebSocket, deal_id: str):
        if deal_id in self.users:
            # Filtra a lista removendo a conexão que bate com o websocket
            initial_len = len(self.users[deal_id])
            self.users[deal_id] = [conn for conn in self.users[deal_id] if conn["ws"] != websocket]
            
            if len(self.users[deal_id]) < initial_len:
                logger.info(f"🔌 WebSocket desconectado do Deal {deal_id}.")
            
            if not self.users[deal_id]: del self.users[deal_id]

    async def broadcast(self, message: dict, deal_id: str, target_users: List[int] = None):
        if deal_id in self.users:
            if deal_id == "dashboard":
                logger.info(f"📢 [WS Broadcast] Enviando notificação global para {len(self.users[deal_id])} clientes conectados.")

            for conn_info in self.users[deal_id]:
                connection = conn_info["ws"]
                user = conn_info["user"]
                
                # Filtragem de Usuários (Se target_users for informado)
                if target_users is not None:
                     if not user or user.id not in target_users:
                         # logger.debug(f"   🚫 User {user.id if user else 'Anon'} ignorado (Não está na lista de alvos).")
                         continue

                try:
                    if deal_id == "dashboard":
                        user_label = f"{user.full_name} (ID: {user.id})" if user else "Anonimo"
                        logger.info(f"   👉 Envio para: {user_label} - IP: {connection.client.host}")
                    
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"❌ Erro ao enviar mensagem WS: {e}")
                    self.disconnect(connection, deal_id)
        else:
            logger.warning(f"⚠️ Nenhuma conexão ativa encontrada para o Deal {deal_id}. Broadcast ignorado.")

manager = WebSocketManager()
