
"""
Конфигурация админ-панели
"""
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

def _parse_admin_ids(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]

# Список администраторов (user_id из Telegram)
DEFAULT_ADMINS = [6326719341, 790410251, 6388614116, 8188457128, 859330334]

ADMIN_USER_IDS = os.getenv("ADMIN_USER_IDS", "")
ADMIN_CHAT_IDS = os.getenv("ADMIN_CHAT_IDS", "")

if ADMIN_USER_IDS:
    ADMINS = _parse_admin_ids(ADMIN_USER_IDS)
elif ADMIN_CHAT_IDS:
    ADMINS = _parse_admin_ids(ADMIN_CHAT_IDS)
else:
    ADMINS = DEFAULT_ADMINS

# Настройки пагинации
PAGINATION_BRANDS_PER_PAGE = 10
PAGINATION_CATEGORIES_PER_PAGE = 8
PAGINATION_PRODUCTS_PER_PAGE = 20

# Путь к статическим файлам
BACKEND_DIR = Path(__file__).parent.parent
STATIC_ROOT = Path(os.environ.get("STATIC_ROOT", BACKEND_DIR / "static"))
STATIC_ROOT.mkdir(parents=True, exist_ok=True)
