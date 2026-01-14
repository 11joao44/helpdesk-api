from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket import manager

router = APIRouter(tags=["WebSockets"])

@router.websocket("/ws/{deal_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, deal_id: str, user_id: str):
    await manager.connect(websocket, deal_id)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast(data, deal_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, deal_id)

@router.websocket("/ws/notifications")
async def notifications_endpoint(websocket: WebSocket):
    """
    Endpoint global para notificações (Dashboard).
    Conecta na sala 'dashboard' onde todas as atividades são publicadas.
    """
    await manager.connect(websocket, "dashboard")
    try:
        while True:
            await websocket.receive_text()  # Dashboard apenas recebe, não envia nada por enquanto 
    except WebSocketDisconnect:
        manager.disconnect(websocket, "dashboard")
