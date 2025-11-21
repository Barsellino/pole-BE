import os
from typing import List

class Settings:
    def __init__(self):
        self.database_url: str = os.getenv("DATABASE_URL", "")
        self.debug: bool = os.getenv("DEBUG", "False").lower() == "true"
        self.cors_origins: List[str] = [
            "http://localhost:4200",
            "https://pole-fe.vercel.app"
        ]

settings = Settings()