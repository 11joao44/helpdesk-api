from fastapi import FastAPI
from app.routes.users import router as router_users
from app.routes.webhook import router as router_webhooks
from app.routes.tickets import router as router_tickets
from app.routes.websocket import router as router_websocket
from app.routes.uploads import router as router_uploads

def create_routes(app: FastAPI) -> None:
        
        @app.get('/')
        def home(): return {"detail": "Olá, FastAPI está funcionando!"}
        app.include_router(router_users)
        app.include_router(router_webhooks)
        app.include_router(router_tickets)
        app.include_router(router_websocket)
        app.include_router(router_uploads)
