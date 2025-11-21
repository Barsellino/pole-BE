import asyncio

from api.ws.manager import manager
from api.crud.session import get_all_sessions
from services.game_state import GameStateService
from db import SessionLocal


class TickManager:
    def __init__(self):
        self.running = False

    async def start(self):
        """Запускає глобальний тікер кожні 0.9 секунди"""
        if self.running:
            return

        self.running = True
        print("⏳ TickManager STARTED")

        TICK_INTERVAL = 0.9  # секунди між тиками

        while True:
            await asyncio.sleep(TICK_INTERVAL)
            await self.tick_all_sessions()

    async def tick_all_sessions(self):
        db = SessionLocal()
        try:
            sessions = get_all_sessions(db)
            for session in sessions:
                state = session.state
                if state and state.get("running"):
                    service = GameStateService(db, session)
                    new_state = service.tick_once()
                    await manager.broadcast_state(session.id, new_state)
        except Exception as e:
            print("Tick ERROR:", e)
        finally:
            db.close()


tick_manager = TickManager()