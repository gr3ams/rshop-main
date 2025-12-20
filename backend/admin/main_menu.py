
"""
Главное меню админ-панели
"""
import logging
from typing import Union
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from .utils import admin_required
from logging_config import setup_logger

logger = setup_logger(__name__, "admin", logging.DEBUG)

router = Router()

async def admin_panel(update: Union[Message, CallbackQuery]):
    """Главное меню админ-панели"""
    user_id = update.from_user.id if update.from_user else None
    logger.info(f"Открытие главного меню админ-панели: user_id={user_id}")
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📦 Товары", callback_data="products_menu"),
        InlineKeyboardButton(text="🏷️ Бренды", callback_data="brands_menu"),
        InlineKeyboardButton(text="📂 Категории", callback_data="categories_menu")
    )

    try:
        if isinstance(update, CallbackQuery):
            await update.message.edit_text(
                "👨‍💻 <b>Админ-панель:</b>",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
            logger.debug(f"Главное меню отредактировано: user_id={user_id}")
        else:
            await update.answer(
                "👨‍💻 <b>Админ-панель:</b>",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
            logger.debug(f"Главное меню отправлено: user_id={user_id}")
    except Exception as e:
        logger.error(f"Ошибка при отображении главного меню: {e}", exc_info=True)
        if isinstance(update, CallbackQuery):
            await update.message.answer(
                "👨‍💻 <b>Админ-панель:</b>",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
        else:
            await update.answer(
                "👨‍💻 <b>Админ-панель:</b>",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )

@router.callback_query(F.data == "admin_back")
@admin_required
async def back_to_admin(callback: CallbackQuery):
    """Возврат в главное меню"""
    try:
        await admin_panel(callback)
    except Exception as e:
        logger.error(f"Ошибка в обработчике назад: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка", show_alert=True)
    finally:
        await callback.answer()

