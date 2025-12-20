
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from models import Base
import os
import logging
from pathlib import Path
from logging_config import setup_sqlalchemy_logging

# Настройка логирования SQLAlchemy
setup_sqlalchemy_logging(logging.DEBUG)
logger = logging.getLogger(__name__)

# Создаем директорию для базы данных если её нет
DB_DIR = Path(__file__).parent / "data"
DB_DIR.mkdir(exist_ok=True)

# Путь к файлу базы данных SQLite
DB_PATH = DB_DIR / "shop.db"

# Строка подключения для SQLite
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite+aiosqlite:///{DB_PATH}")

# Создаем асинхронный движок для SQLite
# echo=True для SQLAlchemy логирования (будет перехвачено нашим логгером)
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Логирование SQL запросов через SQLAlchemy
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    """Инициализация базы данных с созданием всех таблиц"""
    async with engine.begin() as conn:
        logger.info("Создание таблиц в базе данных...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Все таблицы успешно созданы")
        logger.info(f"База данных находится в: {DB_PATH}")

async def get_db():
    """Генератор сессий для зависимостей"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()