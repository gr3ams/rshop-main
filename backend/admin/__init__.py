
"""
Главный модуль админ-панели
Объединяет все роутеры для управления брендами, категориями и товарами
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from .main_menu import router as main_menu_router, admin_panel
from .brands import router as brands_router
from .categories import router as categories_router
from .products import router as products_router
from .utils import admin_required
from logging_config import setup_logger

logger = setup_logger(__name__, "admin", logging.DEBUG)

# Создаем главный роутер
router = Router()

# Подключаем все роутеры
router.include_router(main_menu_router)
router.include_router(brands_router)
router.include_router(categories_router)
router.include_router(products_router)

# Обработчик команды /admin
@router.message(Command("admin"))
@admin_required
async def admin_command(message: Message):
    """Обработчик команды /admin"""
    user_id = message.from_user.id if message.from_user else None
    logger.info(f"Команда /admin вызвана: user_id={user_id}")
    await admin_panel(message)

# Обработчик пагинации (общий для всех модулей)

@router.callback_query(F.data.startswith("page_"))
@admin_required
async def handle_pagination(callback: CallbackQuery, state: FSMContext):
    """Обработка пагинации"""
    user_id = callback.from_user.id if callback.from_user else None
    try:
        parts = callback.data.split("_")
        if len(parts) < 3:
            await callback.answer("Неизвестный контекст пагинации")
            return

        context = parts[1]
        page = int(parts[2])

        logger.debug(f"Обработка пагинации: user_id={user_id}, page={page}, context={context}")

        from .brands import view_brands
        from .categories import view_categories
        from .products import view_products

        if context == "products":
            await state.update_data(products_page=page)
            await view_products(callback, state)
        elif context == "brands":
            await state.update_data(brands_page=page)
            await view_brands(callback, state)
        elif context == "categories":
            await state.update_data(categories_page=page)
            await view_categories(callback, state)
        else:
            logger.warning(f"Неизвестный контекст пагинации: user_id={user_id}, context={context}")
            await callback.answer("Неизвестный контекст пагинации")
    except Exception as e:
        logger.error(f"Ошибка обработки пагинации: user_id={user_id}, error={str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка при переключении страницы")
