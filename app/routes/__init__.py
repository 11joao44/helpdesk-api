from fastapi import FastAPI
from app.routes.users import router as router_users

def create_routes(app: FastAPI) -> None:
        
        @app.get('/')
        def home(): return {"details": "Olá, FastAPI está funcionando!"}
        app.include_router(router_users)
