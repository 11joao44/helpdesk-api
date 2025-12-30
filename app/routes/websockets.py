from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.providers.websocket import manager

router = APIRouter(tags=["WebSockets"])

@router.websocket("/ws/{deal_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, deal_id: str, user_id: str):
    await manager.connect(websocket, deal_id)
    try:
        while True:
            # Mantém a conexão viva e pode receber mensagens do cliente se necessário
            # Por enquanto, apenas o servidor envia updates (timeline)
            data = await websocket.receive_text()
            # Se quiser implementar "User Typing...", processaria aqui.
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, deal_id)
