
"""
Утилиты для админ-панели
"""
import logging
from functools import wraps
from typing import Union, List, Any, Callable
from pathlib import Path
from datetime import datetime
from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Brand, Category, Product
from database import AsyncSessionLocal
from .config import ADMINS, STATIC_ROOT
from logging_config import setup_logger

logger = setup_logger(__name__, "admin", logging.DEBUG)

# ========================
# AUTH UTILITIES
# ========================

async def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    result = user_id in ADMINS
    if not result:
        logger.warning(f"Попытка доступа неадминистратора: user_id={user_id}")
    return result

def admin_required(func):
    """Декоратор для проверки прав администратора"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        update = None
        user_id = None
        
        for arg in args:
            if isinstance(arg, (Message, CallbackQuery)):
                update = arg
                user_id = arg.from_user.id if arg.from_user else None
                break

        if not update:
            logger.error("Не удалось определить объект update в admin_required")
            return

        if not user_id:
            logger.error("Не удалось определить user_id из update")
            return

        if not await is_admin(user_id):
            logger.warning(f"Попытка несанкционированного доступа: user_id={user_id}, handler={func.__name__}")
            if isinstance(update, CallbackQuery):
                await update.answer("🚫 Доступ запрещён", show_alert=True)
            else:
                await update.answer("🚫 Доступ запрещён")
            return

        # Логируем начало операции
        logger.info(f"Начало операции: handler={func.__name__}, user_id={user_id}")
        
        try:
            result = await func(*args, **kwargs)
            logger.info(f"Успешное завершение операции: handler={func.__name__}, user_id={user_id}")
            return result
        except Exception as e:
            logger.error(
                f"Ошибка в обработчике {func.__name__}: user_id={user_id}, error={str(e)}",
                exc_info=True
            )
            if isinstance(update, CallbackQuery):
                await update.answer("❌ Произошла ошибка", show_alert=True)
            else:
                await update.answer("❌ Произошла ошибка")

    return wrapper

# ========================
# PHOTO UTILITIES
# ========================

async def save_photo_from_telegram(bot: Bot, file_id: str, subdir: str = "products") -> str:
    """Сохраняет фото из Telegram в статическую директорию"""
    logger.info(f"Начало сохранения фото: file_id={file_id}, subdir={subdir}")
    try:
        target_dir = STATIC_ROOT / subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Получаем файл из Telegram
        file = await bot.get_file(file_id)
        
        # Генерируем уникальное имя файла
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        filename = f"{file_id}_{timestamp}.jpg"
        file_path = target_dir / filename
        
        # Скачиваем файл
        await bot.download_file(file.file_path, file_path)
        
        photo_url = f"{subdir}/{filename}"
        logger.info(f"Фото успешно сохранено: photo_url={photo_url}")
        return photo_url
    except Exception as e:
        logger.error(f"Ошибка сохранения фото: file_id={file_id}, error={str(e)}", exc_info=True)
        raise

async def delete_photo(photo_url: str):
    """Удаляет фото из статической директории"""
    if not photo_url:
        return
    try:
        file_path = STATIC_ROOT / photo_url
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Фото удалено: photo_url={photo_url}")
        else:
            logger.warning(f"Фото не найдено для удаления: photo_url={photo_url}")
    except Exception as e:
        logger.error(f"Ошибка удаления фото: photo_url={photo_url}, error={str(e)}", exc_info=True)

# ========================
# PAGINATION UTILITIES
# ========================

async def send_paginated_message(
    callback: CallbackQuery,
    items: List[Any],
    title: str,
    item_format: Callable[[Any, int], str],
    items_per_page: int = 10,
    current_page: int = 0,
    back_callback: str = "admin_back",
    menu_callback: str = None,
    parse_mode: str = "HTML"
):
    """Отправка сообщения с пагинацией"""
    logger.debug(f"Отправка пагинированного сообщения: title={title}, items={len(items)}, page={current_page}")
    
    total_items = len(items)
    if total_items == 0:
        logger.info(f"Список пуст для пагинации: title={title}")
        await callback.message.edit_text(f"{title}\n\nСписок пуст", parse_mode=parse_mode)
        await callback.answer()
        return

    total_pages = (total_items + items_per_page - 1) // items_per_page
    start_idx = current_page * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)

    message_text = f"{title}\n\n"
    for i, item in enumerate(items[start_idx:end_idx], start_idx + 1):
        message_text += f"{item_format(item, i)}\n"

    if total_pages > 1:
        message_text += f"\n📄 Страница {current_page + 1} из {total_pages}"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()

    if current_page > 0:
        builder.button(text="⬅️ Назад", callback_data=f"page_{current_page - 1}")
    if current_page < total_pages - 1:
        builder.button(text="Вперёд ➡️", callback_data=f"page_{current_page + 1}")

    if menu_callback:
        builder.button(text="🔙 В меню", callback_data=menu_callback)
    else:
        builder.button(text="🔙 Назад", callback_data=back_callback)

    builder.adjust(2)

    try:
        await callback.message.edit_text(
            text=message_text,
            reply_markup=builder.as_markup(),
            parse_mode=parse_mode
        )
        logger.debug(f"Пагинированное сообщение отправлено: title={title}, page={current_page}")
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}", exc_info=True)
        await callback.message.answer(
            text=message_text,
            reply_markup=builder.as_markup(),
            parse_mode=parse_mode
        )
    finally:
        await callback.answer()

# ========================
# DATABASE UTILITIES
# ========================

async def get_brands(session: AsyncSession) -> List[Brand]:
    """Получить список брендов"""
    logger.debug("Получение списка брендов")
    result = await session.execute(select(Brand).order_by(Brand.name))
    brands = result.scalars().all()
    logger.debug(f"Получено брендов: {len(brands)}")
    return brands

async def get_categories(session: AsyncSession) -> List[Category]:
    """Получить список категорий"""
    logger.debug("Получение списка категорий")
    result = await session.execute(select(Category).order_by(Category.name))
    categories = result.scalars().all()
    logger.debug(f"Получено категорий: {len(categories)}")
    return categories

async def get_products_with_details(session: AsyncSession) -> List[Product]:
    """Получить список товаров с деталями"""
    logger.debug("Получение списка товаров с деталями")
    from sqlalchemy.orm import joinedload
    
    result = await session.execute(
        select(Product)
        .options(joinedload(Product.category), joinedload(Product.brand))
        .order_by(Product.name)
    )
    products = result.unique().scalars().all()
    logger.debug(f"Получено товаров: {len(products)}")
    return products

