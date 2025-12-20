
"""
Управление категориями в админ-панели
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, and_, func
from models import Category, Product
from database import AsyncSessionLocal
from .config import PAGINATION_CATEGORIES_PER_PAGE
from .states import CategoryStates
from .utils import admin_required, send_paginated_message, delete_photo, get_categories
from .main_menu import admin_panel
from logging_config import setup_logger

logger = setup_logger(__name__, "admin", logging.DEBUG)

router = Router()

@router.callback_query(F.data == "categories_menu")
@admin_required
async def categories_menu(callback: CallbackQuery):
    """Меню управления категориями"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Открытие меню управления категориями: user_id={user_id}")
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 Список", callback_data="view_categories"),
        InlineKeyboardButton(text="➕ Добавить", callback_data="add_category_start")
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_category_start"),
        InlineKeyboardButton(text="🗑️ Удалить", callback_data="delete_category_start")
    )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back"))

    try:
        await callback.message.edit_text(
            "📂 <b>Управление категориями:</b>",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        logger.debug(f"Меню категорий отображено: user_id={user_id}")
    except Exception as e:
        logger.error(f"Ошибка в categories_menu: {e}", exc_info=True)
        await callback.message.answer(
            "📂 <b>Управление категориями:</b>",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    finally:
        await callback.answer()

@router.callback_query(F.data == "view_categories")
@admin_required
async def view_categories(callback: CallbackQuery, state: FSMContext):
    """Просмотр списка категорий"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Просмотр списка категорий: user_id={user_id}")
    
    try:
        data = await state.get_data()
        current_page = data.get('categories_page', 0)
        logger.debug(f"Текущая страница: {current_page}, user_id={user_id}")

        async with AsyncSessionLocal() as session:
            categories = await get_categories(session)

            # Подсчитываем товары для каждой категории
            category_products_count = {}
            for category in categories:
                products_count_result = await session.scalar(
                    select(func.count(Product.id)).where(Product.category_id == category.id)
                )
                category_products_count[category.id] = products_count_result or 0

            def format_category(category: Category, idx: int) -> str:
                products_count = category_products_count.get(category.id, 0)
                return f"{idx}. <b>{category.name}</b> (ID: {category.id}, товаров: {products_count})"

            await send_paginated_message(
                callback=callback,
                items=categories,
                title="📂 <b>Список категорий:</b>",
                item_format=format_category,
                items_per_page=PAGINATION_CATEGORIES_PER_PAGE,
                current_page=current_page,
                menu_callback="categories_menu",
                parse_mode="HTML"
            )
            await state.update_data(categories_page=current_page)
            logger.info(f"Список категорий отображен: user_id={user_id}, total={len(categories)}, page={current_page}")
    except Exception as e:
        logger.error(f"Ошибка при получении категорий: user_id={user_id}, error={str(e)}", exc_info=True)
        await callback.message.answer("❌ Ошибка при загрузке списка категорий")
        await callback.answer()

@router.callback_query(F.data == "add_category_start")
@admin_required
async def add_category_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления категории"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Начало добавления категории: user_id={user_id}")
    
    await callback.message.answer("✏️ Введите название новой категории:")
    await state.set_state(CategoryStates.add_name)
    await callback.answer()

@router.message(CategoryStates.add_name)
@admin_required
async def add_category_finish(message: Message, state: FSMContext):
    """Завершение добавления категории"""
    user_id = message.from_user.id if message.from_user else None
    category_name = message.text.strip()
    
    logger.info(f"Попытка добавления категории: user_id={user_id}, name={category_name}")
    
    if not category_name:
        logger.warning(f"Пустое название категории: user_id={user_id}")
        await message.answer("❌ Название категории не может быть пустым. Попробуйте снова:")
        return

    try:
        async with AsyncSessionLocal() as session:
            existing = await session.scalar(
                select(Category).where(func.lower(Category.name) == func.lower(category_name))
            )
            if existing:
                logger.warning(f"Попытка добавить существующую категорию: user_id={user_id}, name={category_name}, existing_id={existing.id}")
                await message.answer(f"❌ Категория '{category_name}' уже существует!")
                await state.clear()
                return await admin_panel(message)

            new_category = Category(name=category_name)
            session.add(new_category)
            await session.commit()
            await session.refresh(new_category)

            logger.info(f"Категория успешно добавлена: user_id={user_id}, category_id={new_category.id}, name={category_name}")
            await message.answer(f"✅ Категория <b>{category_name}</b> успешно добавлена! (ID: {new_category.id})", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при добавлении категории: user_id={user_id}, name={category_name}, error={str(e)}", exc_info=True)
        await message.answer("❌ Произошла ошибка при добавлении категории")
    finally:
        await state.clear()
        await admin_panel(message)

@router.callback_query(F.data == "edit_category_start")
@admin_required
async def edit_category_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования категории"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Начало редактирования категории: user_id={user_id}")
    
    # Очищаем состояние перед началом редактирования
    await state.clear()
    await callback.message.answer("🔍 Введите название категории для редактирования:")
    await state.set_state(CategoryStates.edit_select)
    await callback.answer()

@router.message(CategoryStates.edit_select)
@admin_required
async def find_category_to_edit(message: Message, state: FSMContext):
    """Поиск категории для редактирования"""
    user_id = message.from_user.id if message.from_user else None
    
    # Проверяем, что message.text существует
    if not message.text:
        logger.warning(f"Сообщение без текста: user_id={user_id}, message_type={type(message)}")
        await message.answer("❌ Введите текстовое название категории:")
        return
    
    search_text = message.text.strip().lower()
    
    logger.info(f"Поиск категории для редактирования: user_id={user_id}, search={search_text}, message_text='{message.text}'")
    
    if not search_text:
        await message.answer("❌ Введите название категории:")
        return

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Category).where(func.lower(Category.name) == search_text)
            )
            category = result.scalar_one_or_none()

            if not category:
                logger.warning(f"Категория не найдена для редактирования: user_id={user_id}, search={search_text}")
                await message.answer("❌ Категория не найдена. Проверьте название.")
                await state.clear()
                return

            logger.info(f"Категория найдена для редактирования: user_id={user_id}, category_id={category.id}, name={category.name}")
            
            # Сохраняем данные о категории
            await state.update_data(category_id=category.id, category_name=category.name)
            
            # Сначала отправляем сообщение пользователю
            try:
                await message.answer(
                    f"📂 <b>Найдена категория:</b>\n"
                    f"Название: {category.name}\n"
                    f"ID: {category.id}\n\n"
                    f"Введите новое название:",
                    parse_mode="HTML"
                )
                logger.debug(f"Сообщение о найденной категории отправлено: user_id={user_id}, category_id={category.id}")
            except Exception as send_error:
                logger.error(f"Ошибка при отправке сообщения: user_id={user_id}, error={send_error}", exc_info=True)
                raise
            
            # Только после отправки сообщения устанавливаем новое состояние
            await state.set_state(CategoryStates.edit_name)
            logger.debug(f"Состояние установлено в edit_name: user_id={user_id}, category_id={category.id}")
    except Exception as e:
        logger.error(f"Ошибка при поиске категории: user_id={user_id}, search={search_text}, error={str(e)}", exc_info=True)
        await message.answer("❌ Произошла ошибка при поиске категории")
        await state.clear()

@router.message(CategoryStates.edit_name)
@admin_required
async def save_category_edit(message: Message, state: FSMContext):
    """Сохранение изменений категории"""
    user_id = message.from_user.id if message.from_user else None
    new_name = message.text.strip()
    
    # Логируем текущее состояние для отладки
    current_state = await state.get_state()
    logger.info(f"Сохранение изменений категории: user_id={user_id}, new_name={new_name}, current_state={current_state}")
    
    if not new_name:
        logger.warning(f"Пустое название категории при редактировании: user_id={user_id}")
        await message.answer("❌ Название не может быть пустым. Введите снова:")
        return

    try:
        data = await state.get_data()
        category_id = data.get('category_id')
        old_name = data.get('category_name')
        
        logger.debug(f"Данные из state: user_id={user_id}, category_id={category_id}, old_name={old_name}, all_data={data}")

        if not category_id:
            logger.error(f"category_id не найден в state: user_id={user_id}, state_data={data}")
            await message.answer("❌ Ошибка: ID категории не найден. Попробуйте начать редактирование заново.")
            await state.clear()
            return

        async with AsyncSessionLocal() as session:
            category = await session.get(Category, category_id)
            if not category:
                logger.error(f"Категория не найдена в БД: user_id={user_id}, category_id={category_id}")
                await message.answer("❌ Категория не найдена")
                await state.clear()
                return

            existing = await session.scalar(
                select(Category).where(
                    and_(
                        func.lower(Category.name) == func.lower(new_name),
                        Category.id != category_id
                    )
                )
            )
            if existing:
                logger.warning(f"Попытка переименовать в существующую категорию: user_id={user_id}, category_id={category_id}, new_name={new_name}, existing_id={existing.id}")
                await message.answer(f"❌ Категория с названием '{new_name}' уже существует!")
                return

            old_name_db = category.name
            category.name = new_name
            await session.commit()

            logger.info(f"Категория успешно обновлена: user_id={user_id}, category_id={category_id}, old_name={old_name_db}, new_name={new_name}")
            await message.answer(
                f"✅ Категория успешно обновлена!\n"
                f"Было: {old_name_db}\n"
                f"Стало: {new_name}"
            )
    except Exception as e:
        logger.error(f"Ошибка при сохранении категории: user_id={user_id}, error={str(e)}", exc_info=True)
        await message.answer("❌ Произошла ошибка при сохранении изменений")
    finally:
        await state.clear()
        await admin_panel(message)

@router.callback_query(F.data == "delete_category_start")
@admin_required
async def delete_category_start(callback: CallbackQuery, state: FSMContext):
    """Начало удаления категории"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Начало удаления категории: user_id={user_id}")
    
    await callback.message.answer("🔍 Введите название категории для удаления:")
    await state.set_state(CategoryStates.delete_select)
    await callback.answer()

@router.message(CategoryStates.delete_select)
@admin_required
async def find_category_to_delete(message: Message, state: FSMContext):
    """Поиск категории для удаления"""
    user_id = message.from_user.id if message.from_user else None
    search_text = message.text.strip().lower()
    
    logger.info(f"Поиск категории для удаления: user_id={user_id}, search={search_text}")
    
    if not search_text:
        await message.answer("❌ Введите название категории:")
        return

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Category).where(func.lower(Category.name) == search_text)
            )
            category = result.scalar_one_or_none()

            if not category:
                logger.warning(f"Категория не найдена для удаления: user_id={user_id}, search={search_text}")
                await message.answer("❌ Категория не найдена. Проверьте название.")
                await state.clear()
                return

            products_count = await session.scalar(
                select(func.count(Product.id)).where(Product.category_id == category.id)
            )

            logger.info(f"Категория найдена для удаления: user_id={user_id}, category_id={category.id}, name={category.name}, products_count={products_count}")

            warning = ""
            if products_count > 0:
                warning = f"\n\n⚠️ Внимание! В этой категории {products_count} товаров, они тоже будут удалены!"

            await state.update_data(category_id=category.id)

            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="✅ Да, удалить", callback_data="confirm_category_delete"),
                InlineKeyboardButton(text="❌ Нет, отмена", callback_data="cancel_category_delete")
            )

            await message.answer(
                f"Вы уверены, что хотите удалить категорию?\n"
                f"Название: {category.name}\n"
                f"ID: {category.id}{warning}",
                reply_markup=builder.as_markup()
            )
            await state.set_state(CategoryStates.delete_confirm)
    except Exception as e:
        logger.error(f"Ошибка при поиске категории: user_id={user_id}, search={search_text}, error={str(e)}", exc_info=True)
        await message.answer("❌ Произошла ошибка при поиске категории")
        await state.clear()

@router.callback_query(CategoryStates.delete_confirm, F.data == "confirm_category_delete")
@admin_required
async def execute_category_delete(callback: CallbackQuery, state: FSMContext):
    """Удаление категории"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Подтверждение удаления категории: user_id={user_id}")
    
    try:
        data = await state.get_data()
        category_id = data.get('category_id')

        if not category_id:
            logger.error(f"category_id не найден в state: user_id={user_id}")
            await callback.message.answer("❌ Категория не выбрана")
            await state.clear()
            return

        async with AsyncSessionLocal() as session:
            category = await session.get(Category, category_id)
            if not category:
                logger.error(f"Категория не найдена в БД: user_id={user_id}, category_id={category_id}")
                await callback.message.answer("❌ Категория не найдена")
                await state.clear()
                return

            products_count = await session.scalar(
                select(func.count(Product.id)).where(Product.category_id == category_id)
            )
            
            products = await session.execute(
                select(Product).where(Product.category_id == category_id)
            )
            deleted_photos = 0
            for product in products.scalars().all():
                if product.photo_url:
                    await delete_photo(product.photo_url)
                    deleted_photos += 1

            category_name = category.name
            await session.delete(category)
            await session.commit()

            logger.info(f"Категория успешно удалена: user_id={user_id}, category_id={category_id}, name={category_name}, products_deleted={products_count}, photos_deleted={deleted_photos}")
            await callback.message.answer(
                f"✅ Категория успешно удалена:\n"
                f"Название: {category_name}\n"
                f"ID: {category_id}"
            )
    except Exception as e:
        logger.error(f"Ошибка при удалении категории: user_id={user_id}, error={str(e)}", exc_info=True)
        await callback.message.answer("❌ Произошла ошибка при удалении категории")
    finally:
        await state.clear()
        await admin_panel(callback.message)
        await callback.answer()

@router.callback_query(CategoryStates.delete_confirm, F.data == "cancel_category_delete")
@admin_required
async def cancel_category_delete(callback: CallbackQuery, state: FSMContext):
    """Отмена удаления категории"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Отмена удаления категории: user_id={user_id}")
    
    await state.clear()
    await callback.message.answer("❌ Удаление категории отменено")
    await admin_panel(callback.message)
    await callback.answer()

