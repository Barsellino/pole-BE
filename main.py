import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import Base, engine
from core.config import settings
from core.logging import logger
from api.ws.tick_manager import tick_manager
from models.session import GameSession  # noqa: F401

# ROUTES
from api.routers.session import router as session_router
from api.routers.ws import router as ws_router
from api.routers.topics import router as topics_router


app = FastAPI(title="Game API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up application...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    logger.info("Starting tick manager...")
    asyncio.create_task(tick_manager.start())


app.include_router(session_router, tags=["Session"])
app.include_router(ws_router, tags=["WS"])
app.include_router(topics_router)


@app.get("/")
def root():
    logger.info("Health check requested")
    return {"message": "OK", "status": "healthy"}