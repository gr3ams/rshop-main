
"""
Конфигурация админ-панели
"""
from pathlib import Path
import os

# Список администраторов
ADMINS = [6326719341, 790410251, 6388614116, 8188457128, 859330334]

# Настройки пагинации
PAGINATION_BRANDS_PER_PAGE = 10
PAGINATION_CATEGORIES_PER_PAGE = 8
PAGINATION_PRODUCTS_PER_PAGE = 20

# Путь к статическим файлам
BACKEND_DIR = Path(__file__).parent.parent
STATIC_ROOT = Path(os.environ.get("STATIC_ROOT", BACKEND_DIR / "static"))
STATIC_ROOT.mkdir(parents=True, exist_ok=True)

