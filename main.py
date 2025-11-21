import asyncio

from fastapi import FastAPI
from db import Base, engine

from api.ws.tick_manager import tick_manager

from models.session import GameSession  # noqa: F401

# ROUTES
from api.routers.session import router as session_router
from api.routers.ws import router as ws_router
from api.routers.topics import router as topics_router


app = FastAPI(title="Game API", version="1.0.0")


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


app.include_router(session_router, tags=["Session"])
app.include_router(ws_router, tags=["WS"])
app.include_router(topics_router)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(tick_manager.start())
@app.get("/")
def root():
    return {"message": "OK"}