from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.services.websocket import manager
from app.core.security import get_current_user_ws
from app.models import UserModel
from app.core.config import logger

router = APIRouter(tags=["WebSockets"])

@router.websocket("/ws/{deal_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, deal_id: str, user_id: str):
    # TODO: Validar se user_id bate com o token se quisermos segurança aqui também
    # Por enquanto, mantendo compatibilidade com o que já existia (user_id na URL)
    await manager.connect(websocket, deal_id, user=None) 
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast(data, deal_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, deal_id)

@router.websocket("/ws/notifications")
async def notifications_endpoint(websocket: WebSocket, user: UserModel = Depends(get_current_user_ws)):
    """
    Endpoint global para notificações (Dashboard).
    Conecta na sala 'dashboard' onde todas as atividades são publicadas.
    Exige autenticação via Cookie (HttpOnly).
    """
    if not user:
        # Se não autenticar, fecha com código de política de violação ou normal
        await websocket.close(code=1008, reason="Authentication Failed")
        return

    logger.info(f"👤 Usuário Autenticado no WebSocket: {user.full_name}")

    await manager.connect(websocket, "dashboard", user=user)
    try:
        while True:
            await websocket.receive_text()  # Dashboard apenas recebe
    except WebSocketDisconnect:
        manager.disconnect(websocket, "dashboard")
