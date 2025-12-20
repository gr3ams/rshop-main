
"""
Конфигурация логирования для всех сервисов
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Создаем директорию для логов
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Формат логов
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(
    name: str,
    log_file: str = None,
    level: int = logging.DEBUG,
    console_output: bool = True,
    file_output: bool = True
) -> logging.Logger:
    """
    Настройка логгера с выводом в консоль и файл
    
    Args:
        name: Имя логгера (обычно __name__)
        log_file: Имя файла для логов (без расширения)
        level: Уровень логирования
        console_output: Выводить ли в консоль
        file_output: Записывать ли в файл
        
    Returns:
        Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Убираем дублирование логов (если логгер уже настроен)
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # Обработчик для консоли
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Обработчик для файла
    if file_output and log_file:
        log_path = LOGS_DIR / f"{log_file}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Настройка логирования для SQLAlchemy
def setup_sqlalchemy_logging(level: int = logging.DEBUG):
    """Настройка логирования SQLAlchemy"""
    sqlalchemy_logger = setup_logger("sqlalchemy.engine", "sqlalchemy", level)
    sqlalchemy_logger.setLevel(level)
    
    # Логируем все SQL запросы
    logging.getLogger("sqlalchemy.engine").setLevel(level)
    logging.getLogger("sqlalchemy.pool").setLevel(level)
    logging.getLogger("sqlalchemy.dialects").setLevel(level)

# Настройка логирования для Uvicorn
def setup_uvicorn_logging(level: int = logging.DEBUG):
    """Настройка логирования Uvicorn"""
    uvicorn_logger = setup_logger("uvicorn", "uvicorn", level)
    uvicorn_access = setup_logger("uvicorn.access", "uvicorn_access", level)
    uvicorn_error = setup_logger("uvicorn.error", "uvicorn_error", level)

# Настройка логирования для aiogram
def setup_aiogram_logging(level: int = logging.DEBUG):
    """Настройка логирования aiogram"""
    aiogram_logger = setup_logger("aiogram", "aiogram", level)
    aiogram_logger.setLevel(level)

# Настройка логирования для httpx (для Telegram API запросов)
def setup_httpx_logging(level: int = logging.DEBUG):
    """Настройка логирования httpx"""
    httpx_logger = setup_logger("httpx", "httpx", level)
    httpx_logger.setLevel(level)
