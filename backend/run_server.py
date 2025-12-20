
"""
Скрипт для запуска API сервера
"""
import uvicorn
import sys
import io
import logging
from logging_config import setup_logger, setup_uvicorn_logging

# Настройка логирования
setup_uvicorn_logging(logging.DEBUG)
logger = setup_logger(__name__, "run_server", logging.DEBUG)

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == "__main__":
    logger.info("="*50)
    logger.info("ЗАПУСК API СЕРВЕРА")
    logger.info("="*50)
    logger.info("Сервер будет доступен по адресу:")
    logger.info("  • http://localhost:8000")
    logger.info("  • http://127.0.0.1:8000")
    logger.info("API эндпоинты:")
    logger.info("  • GET  /api/brands - получить все бренды")
    logger.info("  • GET  /api/categories/{brand_id} - категории бренда")
    logger.info("  • GET  /api/products/{category_id} - товары категории")
    logger.info("  • GET  /api/admin/data - данные для админки")
    logger.info("  • POST /api/admin/add_product - добавить товар")
    logger.info("Для остановки сервера нажмите Ctrl+C")
    logger.info("="*50)
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"  # Изменено на debug
    )

