"""
Управление брендами в админ-панели
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from models import Brand, Product
from database import AsyncSessionLocal
from .config import PAGINATION_BRANDS_PER_PAGE
from .states import BrandStates
from .utils import admin_required, send_paginated_message, delete_photo, get_brands
from .main_menu import admin_panel
from logging_config import setup_logger

logger = setup_logger(__name__, "admin", logging.DEBUG)

router = Router()

@router.callback_query(F.data == "brands_menu")
@admin_required
async def brands_menu(callback: CallbackQuery):
    """Меню управления брендами"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Открытие меню управления брендами: user_id={user_id}")
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 Список", callback_data="view_brands"),
        InlineKeyboardButton(text="➕ Добавить", callback_data="add_brand_start")
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_brand_start"),
        InlineKeyboardButton(text="🗑️ Удалить", callback_data="delete_brand_start")
    )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back"))

    try:
        await callback.message.edit_text(
            "🏷️ <b>Управление брендами:</b>",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        logger.debug(f"Меню брендов отображено: user_id={user_id}")
    except Exception as e:
        logger.error(f"Ошибка в brands_menu: {e}", exc_info=True)
        await callback.message.answer(
            "🏷️ <b>Управление брендами:</b>",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    finally:
        await callback.answer()

@router.callback_query(F.data == "view_brands")
@admin_required
async def view_brands(callback: CallbackQuery, state: FSMContext):
    """Просмотр списка брендов"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Просмотр списка брендов: user_id={user_id}")
    
    try:
        data = await state.get_data()
        current_page = data.get('brands_page', 0)
        logger.debug(f"Текущая страница: {current_page}, user_id={user_id}")

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Brand, func.count(Product.id).label("products_count"))
                .outerjoin(Product, Product.brand_id == Brand.id)
                .group_by(Brand.id)
                .order_by(Brand.name)
            )
            brand_rows = result.all()

            def format_brand(row: tuple[Brand, int], idx: int) -> str:
                brand, products_count = row
                return f"{idx}. <b>{brand.name}</b> (ID: {brand.id}, товаров: {products_count or 0})"

            await send_paginated_message(
                callback=callback,
                items=brand_rows,
                title="🏷️ <b>Список брендов:</b>",
                item_format=format_brand,
                items_per_page=PAGINATION_BRANDS_PER_PAGE,
                current_page=current_page,
                menu_callback="brands_menu",
                parse_mode="HTML",
                page_prefix="page_brands"
            )
            await state.update_data(brands_page=current_page)
            logger.info(f"Список брендов отображен: user_id={user_id}, total={len(brand_rows)}, page={current_page}")
    except Exception as e:
        logger.error(f"Ошибка при получении брендов: user_id={user_id}, error={str(e)}", exc_info=True)
        await callback.message.answer("❌ Ошибка при загрузке списка брендов")
        await callback.answer()

@router.callback_query(F.data == "add_brand_start")
@admin_required
async def add_brand_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления бренда"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Начало добавления бренда: user_id={user_id}")
    
    await callback.message.answer("✏️ Введите название нового бренда:")
    await state.set_state(BrandStates.add_name)
    await callback.answer()

@router.message(BrandStates.add_name)
@admin_required
async def add_brand_finish(message: Message, state: FSMContext):
    """Завершение добавления бренда"""
    user_id = message.from_user.id if message.from_user else None
    brand_name = message.text.strip()
    
    logger.info(f"Попытка добавления бренда: user_id={user_id}, name={brand_name}")
    
    if not brand_name:
        logger.warning(f"Пустое название бренда: user_id={user_id}")
        await message.answer("❌ Название бренда не может быть пустым. Попробуйте снова:")
        return

    try:
        async with AsyncSessionLocal() as session:
            # Проверяем на дубликат
            from sqlalchemy import func
            existing = await session.scalar(
                select(Brand).where(func.lower(Brand.name) == func.lower(brand_name))
            )
            if existing:
                logger.warning(f"Попытка добавить существующий бренд: user_id={user_id}, name={brand_name}, existing_id={existing.id}")
                await message.answer(f"❌ Бренд '{brand_name}' уже существует!")
                await state.clear()
                return await admin_panel(message)

            # Создаем новый бренд
            new_brand = Brand(name=brand_name)
            session.add(new_brand)
            await session.commit()
            await session.refresh(new_brand)

            logger.info(f"Бренд успешно добавлен: user_id={user_id}, brand_id={new_brand.id}, name={brand_name}")
            await message.answer(f"✅ Бренд <b>{brand_name}</b> успешно добавлен! (ID: {new_brand.id})", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при добавлении бренда: user_id={user_id}, name={brand_name}, error={str(e)}", exc_info=True)
        await message.answer("❌ Произошла ошибка при добавлении бренда")
    finally:
        await state.clear()
        await admin_panel(message)

@router.callback_query(F.data == "edit_brand_start")
@admin_required
async def edit_brand_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования бренда"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Начало редактирования бренда: user_id={user_id}")
    
    await callback.message.answer("🔍 Введите название бренда для редактирования:")
    await state.set_state(BrandStates.edit_select)
    await callback.answer()

@router.message(BrandStates.edit_select)
@admin_required
async def find_brand_to_edit(message: Message, state: FSMContext):
    """Поиск бренда для редактирования"""
    user_id = message.from_user.id if message.from_user else None
    search_text = message.text.strip().lower()
    
    logger.info(f"Поиск бренда для редактирования: user_id={user_id}, search={search_text}")
    
    if not search_text:
        await message.answer("❌ Введите название бренда:")
        return

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Brand).where(func.lower(Brand.name) == search_text)
            )
            brand = result.scalar_one_or_none()

            if not brand:
                logger.warning(f"Бренд не найден для редактирования: user_id={user_id}, search={search_text}")
                await message.answer("❌ Бренд не найден. Проверьте название.")
                await state.clear()
                return

            logger.info(f"Бренд найден для редактирования: user_id={user_id}, brand_id={brand.id}, name={brand.name}")
            await state.update_data(brand_id=brand.id, brand_name=brand.name)
            await message.answer(
                f"🏷️ <b>Найден бренд:</b>\n"
                f"Название: {brand.name}\n"
                f"ID: {brand.id}\n\n"
                f"Введите новое название:",
                parse_mode="HTML"
            )
            await state.set_state(BrandStates.edit_name)
    except Exception as e:
        logger.error(f"Ошибка при поиске бренда: user_id={user_id}, search={search_text}, error={str(e)}", exc_info=True)
        await message.answer("❌ Произошла ошибка при поиске бренда")
        await state.clear()

@router.message(BrandStates.edit_name)
@admin_required
async def save_brand_edit(message: Message, state: FSMContext):
    """Сохранение изменений бренда"""
    user_id = message.from_user.id if message.from_user else None
    new_name = message.text.strip()
    
    logger.info(f"Сохранение изменений бренда: user_id={user_id}, new_name={new_name}")
    
    if not new_name:
        await message.answer("❌ Название не может быть пустым. Введите снова:")
        return

    try:
        data = await state.get_data()
        brand_id = data.get('brand_id')
        old_name = data.get('brand_name')

        if not brand_id:
            logger.error(f"brand_id не найден в state: user_id={user_id}")
            await message.answer("❌ Ошибка: ID бренда не найден")
            await state.clear()
            return

        async with AsyncSessionLocal() as session:
            brand = await session.get(Brand, brand_id)
            if not brand:
                logger.error(f"Бренд не найден в БД: user_id={user_id}, brand_id={brand_id}")
                await message.answer("❌ Бренд не найден")
                await state.clear()
                return

            # Проверяем на дубликат
            existing = await session.scalar(
                select(Brand).where(
                    and_(
                        func.lower(Brand.name) == func.lower(new_name),
                        Brand.id != brand_id
                    )
                )
            )
            if existing:
                logger.warning(f"Попытка переименовать в существующий бренд: user_id={user_id}, brand_id={brand_id}, new_name={new_name}, existing_id={existing.id}")
                await message.answer(f"❌ Бренд с названием '{new_name}' уже существует!")
                return

            old_name_db = brand.name
            brand.name = new_name
            await session.commit()

            logger.info(f"Бренд успешно обновлен: user_id={user_id}, brand_id={brand_id}, old_name={old_name_db}, new_name={new_name}")
            await message.answer(
                f"✅ Бренд успешно обновлен!\n"
                f"Было: {old_name_db}\n"
                f"Стало: {new_name}"
            )
    except Exception as e:
        logger.error(f"Ошибка при сохранении бренда: user_id={user_id}, error={str(e)}", exc_info=True)
        await message.answer("❌ Произошла ошибка при сохранении изменений")
    finally:
        await state.clear()
        await admin_panel(message)

@router.callback_query(F.data == "delete_brand_start")
@admin_required
async def delete_brand_start(callback: CallbackQuery, state: FSMContext):
    """Начало удаления бренда"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Начало удаления бренда: user_id={user_id}")
    
    await callback.message.answer("🔍 Введите название бренда для удаления:")
    await state.set_state(BrandStates.delete_select)
    await callback.answer()

@router.message(BrandStates.delete_select)
@admin_required
async def find_brand_to_delete(message: Message, state: FSMContext):
    """Поиск бренда для удаления"""
    user_id = message.from_user.id if message.from_user else None
    search_text = message.text.strip().lower()
    
    logger.info(f"Поиск бренда для удаления: user_id={user_id}, search={search_text}")
    
    if not search_text:
        await message.answer("❌ Введите название бренда:")
        return

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Brand).where(func.lower(Brand.name) == search_text)
            )
            brand = result.scalar_one_or_none()

            if not brand:
                logger.warning(f"Бренд не найден для удаления: user_id={user_id}, search={search_text}")
                await message.answer("❌ Бренд не найден. Проверьте название.")
                await state.clear()
                return

            # Подсчитываем количество товаров
            products_count = await session.scalar(
                select(func.count(Product.id)).where(Product.brand_id == brand.id)
            )

            logger.info(f"Бренд найден для удаления: user_id={user_id}, brand_id={brand.id}, name={brand.name}, products_count={products_count}")

            warning = ""
            if products_count > 0:
                warning = f"\n\n⚠️ Внимание! У этого бренда {products_count} товаров, они тоже будут удалены!"

            await state.update_data(brand_id=brand.id)

            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="✅ Да, удалить", callback_data="confirm_brand_delete"),
                InlineKeyboardButton(text="❌ Нет, отмена", callback_data="cancel_brand_delete")
            )

            await message.answer(
                f"Вы уверены, что хотите удалить бренд?\n"
                f"Название: {brand.name}\n"
                f"ID: {brand.id}{warning}",
                reply_markup=builder.as_markup()
            )
            await state.set_state(BrandStates.delete_confirm)
    except Exception as e:
        logger.error(f"Ошибка при поиске бренда: user_id={user_id}, search={search_text}, error={str(e)}", exc_info=True)
        await message.answer("❌ Произошла ошибка при поиске бренда")
        await state.clear()

@router.callback_query(BrandStates.delete_confirm, F.data == "confirm_brand_delete")
@admin_required
async def execute_brand_delete(callback: CallbackQuery, state: FSMContext):
    """Удаление бренда"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Подтверждение удаления бренда: user_id={user_id}")
    
    try:
        data = await state.get_data()
        brand_id = data.get('brand_id')

        if not brand_id:
            logger.error(f"brand_id не найден в state: user_id={user_id}")
            await callback.message.answer("❌ Бренд не выбран")
            await state.clear()
            return

        async with AsyncSessionLocal() as session:
            brand = await session.get(Brand, brand_id)
            if not brand:
                logger.error(f"Бренд не найден в БД: user_id={user_id}, brand_id={brand_id}")
                await callback.message.answer("❌ Бренд не найден")
                await state.clear()
                return

            # Подсчитываем товары для логирования
            products_count = await session.scalar(
                select(func.count(Product.id)).where(Product.brand_id == brand_id)
            )
            
            # Удаляем все фото товаров этого бренда
            products = await session.execute(
                select(Product).where(Product.brand_id == brand_id)
            )
            deleted_photos = 0
            for product in products.scalars().all():
                if product.photo_url:
                    await delete_photo(product.photo_url)
                    deleted_photos += 1

            brand_name = brand.name
            await session.delete(brand)
            await session.commit()

            logger.info(f"Бренд успешно удален: user_id={user_id}, brand_id={brand_id}, name={brand_name}, products_deleted={products_count}, photos_deleted={deleted_photos}")
            await callback.message.answer(
                f"✅ Бренд успешно удалён:\n"
                f"Название: {brand_name}\n"
                f"ID: {brand_id}"
            )
    except Exception as e:
        logger.error(f"Ошибка при удалении бренда: user_id={user_id}, error={str(e)}", exc_info=True)
        await callback.message.answer("❌ Произошла ошибка при удалении бренда")
    finally:
        await state.clear()
        await admin_panel(callback.message)
        await callback.answer()

@router.callback_query(BrandStates.delete_confirm, F.data == "cancel_brand_delete")
@admin_required
async def cancel_brand_delete(callback: CallbackQuery, state: FSMContext):
    """Отмена удаления бренда"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Отмена удаления бренда: user_id={user_id}")
    
    await state.clear()
    await callback.message.answer("❌ Удаление бренда отменено")
    await admin_panel(callback.message)
    await callback.answer()
