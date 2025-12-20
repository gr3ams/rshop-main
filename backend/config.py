
"""
Конфигурационный файл для настроек приложения
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ID чата администраторов (можно указать несколько через запятую в .env)
# Формат в .env: ADMIN_CHAT_IDS=-1234567890,-9876543210
# Или один ID: ADMIN_CHAT_IDS=-1234567890
ADMIN_CHAT_IDS_STR = os.getenv("ADMIN_CHAT_IDS", "")
ADMIN_CHAT_IDS = [int(chat_id.strip()) for chat_id in ADMIN_CHAT_IDS_STR.split(",") if chat_id.strip()] if ADMIN_CHAT_IDS_STR else []

# Если не указаны в .env, можно задать здесь напрямую (для разработки)
if not ADMIN_CHAT_IDS:
    # Пример: ADMIN_CHAT_IDS = [-1234567890]  # Замените на реальный ID чата
    ADMIN_CHAT_IDS = []

def get_admin_chat_ids():
    """Получить список ID чатов администраторов"""
    if not ADMIN_CHAT_IDS:
        raise ValueError(
            "ADMIN_CHAT_IDS не настроен. Укажите ID чата администраторов в .env файле "
            "или в config.py. Пример: ADMIN_CHAT_IDS=-1234567890"
        )
    return ADMIN_CHAT_IDS

