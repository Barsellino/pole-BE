from copy import deepcopy
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from models.session import GameSession  # імпорт твоєї моделі, назва може відрізнятись


Player = str  # 'A' або 'B'


DEFAULT_STATE: Dict[str, Any] = {
    "topic": None,            # { id, name, imageUrl?, images? } або null
    "activePlayer": "A",      # 'A' | 'B'
    "timeA": 60,
    "timeB": 60,
    "perPlayerTotalSec": 60,
    "running": False,
    "images": [],             # [{ src, alt }]
    "imageIndex": 0
}

# api/services/game_state.py (продовження)

class GameStateService:
    """
    Порт твого фронтового GameStateService на бекенд.
    Працює з однією GameSession (однією сесією гри).
    """

    def __init__(self, db: Session, session: GameSession):
        self.db = db
        self.session = session

        # Якщо state не dict АБО порожній dict → створюємо новий
        if not isinstance(self.session.state, dict) or not self.session.state:
            self.session.state = deepcopy(DEFAULT_STATE)
            self._save()
        else:
            # доповнюємо відсутні ключі дефолтами
            for k, v in DEFAULT_STATE.items():
                if k not in self.session.state:
                    self.session.state[k] = deepcopy(v)
            self._save()

    # ---- базові хелпери ----

    @property
    def state(self) -> Dict[str, Any]:
        return self.session.state

    def _save(self) -> None:
        self.db.add(self.session)
        self.db.commit()
        self.db.refresh(self.session)

    def _patch(self, **patch: Any) -> Dict[str, Any]:
        self.state.update(patch)
        self._save()
        return self.state

    # ---- API, аналогічне твоєму TS-сервісу ----

    def set_topic(self, topic: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        topic: { id, name, imageUrl?, images? } або None
        """
        # формуємо images як у твому setTopic()
        imgs = []
        if topic and isinstance(topic.get("images"), list) and topic["images"]:
            imgs = topic["images"]
        elif topic and topic.get("imageUrl"):
            imgs = [{
                "src": topic["imageUrl"],
                "alt": topic.get("name") or "Тема"
            }]

        s = self.state
        per_player = s.get("perPlayerTotalSec", DEFAULT_STATE["perPlayerTotalSec"])

        # скидаємо таймери, зупиняємо гру, як у TS
        self.state["topic"] = topic
        self.state["images"] = imgs
        self.state["imageIndex"] = 0
        self.state["timeA"] = per_player
        self.state["timeB"] = per_player
        self.state["running"] = False
        self.state["activePlayer"] = "A"

        self._save()
        return self.state

    def set_per_player_time(self, sec: int) -> Dict[str, Any]:
        """аналог setPerPlayerTime(sec)"""
        s = max(5, int(sec))
        self.state["perPlayerTotalSec"] = s
        self.state["timeA"] = s
        self.state["timeB"] = s
        self.state["running"] = False
        self._save()
        return self.state

    def reset_times(self) -> Dict[str, Any]:
        """аналог resetTimes()"""
        s = int(self.state.get("perPlayerTotalSec", DEFAULT_STATE["perPlayerTotalSec"]))
        self.state["timeA"] = s
        self.state["timeB"] = s
        self.state["running"] = False
        self.state["imageIndex"] = 0
        self._save()
        return self.state

    def _next_image_index(self) -> int:
        imgs = self.state.get("images") or []
        image_index = int(self.state.get("imageIndex", 0))
        if imgs:
            return (image_index + 1) % len(imgs)
        return 0

    def start_turn(self, player: Player) -> Dict[str, Any]:
        """аналог startTurn(p: Player)"""
        next_idx = self._next_image_index()

        self.state["activePlayer"] = player
        self.state["running"] = True
        self.state["imageIndex"] = next_idx

        self._save()
        return self.state

    def pause_all(self) -> Dict[str, Any]:
        """аналог pauseAll()"""
        self.state["running"] = False
        self._save()
        return self.state

    def correct(self) -> Dict[str, Any]:
        """
        аналог correct():
        - змінити активного гравця
        - якщо в нього ще є час → startTurn(next)
        - інакше pauseAll()
        """
        active = self.state.get("activePlayer", "A")
        next_player: Player = "B" if active == "A" else "A"

        timeA = int(self.state.get("timeA", 0))
        timeB = int(self.state.get("timeB", 0))

        can_run = timeA > 0 if next_player == "A" else timeB > 0

        if can_run:
            return self.start_turn(next_player)
        else:
            return self.pause_all()

    def pass_or_wrong(self) -> Dict[str, Any]:
        """
        аналог passOrWrong():
        - штраф -3 сек активному
        - переключаємо картинку
        - якщо час у активного закінчився → pauseAll()
        """
        penalty = 3
        active = self.state.get("activePlayer", "A")
        timeA = int(self.state.get("timeA", 0))
        timeB = int(self.state.get("timeB", 0))

        # новий індекс картинки (як у TS)
        next_idx = self._next_image_index()

        if active == "A":
            nextA = max(0, timeA - penalty)
            self.state["timeA"] = nextA
            self.state["imageIndex"] = next_idx
            if nextA == 0:
                self.state["running"] = False
        else:
            nextB = max(0, timeB - penalty)
            self.state["timeB"] = nextB
            self.state["imageIndex"] = next_idx
            if nextB == 0:
                self.state["running"] = False

        self._save()
        return self.state

    def tick_once(self) -> Dict[str, Any]:
        """
        Тікає 1 секунда:
        - якщо гра не активна → нічого не робить
        - якщо у активного гравця стає 0 → гра зупиняється (без переключення)
        """

        if not self.state.get("running"):
            return self.state

        active = self.state.get("activePlayer", "A")
        timeA = int(self.state.get("timeA", 0))
        timeB = int(self.state.get("timeB", 0))

        # --- Тікає активний гравець ---
        if active == "A":
            nextA = max(0, timeA - 1)
            self.state["timeA"] = nextA

            # Якщо час закінчився → гра зупиняється
            if nextA == 0:
                self.state["running"] = False

        else:
            nextB = max(0, timeB - 1)
            self.state["timeB"] = nextB

            if nextB == 0:
                self.state["running"] = False

        self._save()
        return self.state
