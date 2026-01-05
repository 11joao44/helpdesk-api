from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.providers.websocket import manager

router = APIRouter(tags=["WebSockets"])

@router.websocket("/ws/{deal_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, deal_id: str, user_id: str):
    await manager.connect(websocket, deal_id)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, deal_id)
