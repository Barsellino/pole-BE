import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Завантажуємо змінні з .env
load_dotenv()

# Отримуємо URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL не знайдено в .env файлі")

# Створюємо двигун (engine)
# echo=True буде виводити SQL запити в консоль (для налагодження)
engine = create_engine(DATABASE_URL, echo=True)

# Створюємо базовий клас для моделей
Base = declarative_base()

# Фабрика сесій
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependency для FastAPI: отримаємо сесію та закриємо її після запиту.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print("✅ Успішне підключення!")
            print(f"Версія бази даних: {version}")
    except Exception as e:
        print("❌ Помилка підключення:")
        print(e)

if __name__ == "__main__":
    test_connection()