
"""
Админ-панель для управления товарами, брендами и категориями через Telegram бота
"""
import os
import logging
from pathlib import Path
from functools import wraps
from typing import Union, List, Any, Callable
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from models import Brand, Category, Product
from database import AsyncSessionLocal
from sqlalchemy.orm import joinedload
from logging_config import setup_logger

logger = setup_logger(__name__, "admin", logging.DEBUG)

router = Router()

ADMINS = [6326719341, 790410251, 6388614116, 8188457128, 859330334]

# Настройки пагинации
PAGINATION_BRANDS_PER_PAGE = 10
PAGINATION_CATEGORIES_PER_PAGE = 8
PAGINATION_PRODUCTS_PER_PAGE = 20

# Путь к статическим файлам
BACKEND_DIR = Path(__file__).parent
STATIC_ROOT = Path(os.environ.get("STATIC_ROOT", BACKEND_DIR / "static"))
STATIC_ROOT.mkdir(parents=True, exist_ok=True)

# ========================
# FSM STATES
# ========================

class BrandStates(StatesGroup):
    add_name = State()
    edit_select = State()
    edit_name = State()
    delete_select = State()
    delete_confirm = State()

class CategoryStates(StatesGroup):
    add_name = State()
    edit_select = State()
    edit_name = State()
    delete_select = State()
    delete_confirm = State()

class ProductStates(StatesGroup):
    add_brand = State()
    add_category = State()
    add_name = State()
    add_price = State()
    add_photo = State()
    add_description = State()
    edit_select = State()
    edit_field = State()
    delete_select = State()
    delete_confirm = State()

# ========================
# UTILITY FUNCTIONS
# ========================

async def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id in ADMINS

def admin_required(func):
    """Декоратор для проверки прав администратора"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        update = None
        for arg in args:
            if isinstance(arg, (Message, CallbackQuery)):
                update = arg
                break

        if not update:
            logger.error("Не удалось определить объект update")
            return

        if not await is_admin(update.from_user.id):
            logger.warning(f"Попытка несанкционированного доступа: {update.from_user.id}")
            if isinstance(update, CallbackQuery):
                await update.answer("🚫 Доступ запрещён", show_alert=True)
            else:
                await update.answer("🚫 Доступ запрещён")
            return

        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Ошибка в обработчике {func.__name__}: {e}", exc_info=True)
            if isinstance(update, CallbackQuery):
                await update.answer("❌ Произошла ошибка", show_alert=True)
            else:
                await update.answer("❌ Произошла ошибка")

    return wrapper

async def save_photo_from_telegram(bot: Bot, file_id: str, subdir: str = "products") -> str:
    """Сохраняет фото из Telegram в статическую директорию"""
    try:
        target_dir = STATIC_ROOT / subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Получаем файл из Telegram
        file = await bot.get_file(file_id)
        
        # Генерируем уникальное имя файла
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        filename = f"{file_id}_{timestamp}.jpg"
        file_path = target_dir / filename
        
        # Скачиваем файл
        await bot.download_file(file.file_path, file_path)
        
        # Возвращаем путь относительно static
        return f"{subdir}/{filename}"
    except Exception as e:
        logger.error(f"Ошибка сохранения фото: {e}")
        raise

async def delete_photo(photo_url: str):
    """Удаляет фото из статической директории"""
    if not photo_url:
        return
    try:
        file_path = STATIC_ROOT / photo_url
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Фото удалено: {photo_url}")
    except Exception as e:
        logger.error(f"Ошибка удаления фото: {e}")

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
    total_items = len(items)
    if total_items == 0:
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
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
        await callback.message.answer(
            text=message_text,
            reply_markup=builder.as_markup(),
            parse_mode=parse_mode
        )
    finally:
        await callback.answer()

# ========================
# ADMIN PANEL
# ========================

async def admin_panel(update: Union[Message, CallbackQuery]):
    """Главное меню админ-панели"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📦 Товары", callback_data="products_menu"),
        InlineKeyboardButton(text="🏷️ Бренды", callback_data="brands_menu"),
        InlineKeyboardButton(text="📂 Категории", callback_data="categories_menu")
    )

    if isinstance(update, CallbackQuery):
        try:
            await update.message.edit_text(
                "👨‍💻 <b>Админ-панель:</b>",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка редактирования сообщения: {e}")
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

@router.message(Command("admin"))
@admin_required
async def admin_command(message: Message):
    await admin_panel(message)

@router.callback_query(F.data == "admin_back")
@admin_required
async def back_to_admin(callback: CallbackQuery):
    try:
        await admin_panel(callback)
    except Exception as e:
        logger.error(f"Ошибка в обработчике назад: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)
    finally:
        await callback.answer()

# ========================
# BRANDS MANAGEMENT
# ========================

@router.callback_query(F.data == "brands_menu")
@admin_required
async def brands_menu(callback: CallbackQuery):
    """Меню управления брендами"""
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
    except Exception as e:
        logger.error(f"Ошибка в brands_menu: {e}")
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
    try:
        data = await state.get_data()
        current_page = data.get('brands_page', 0)

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Brand).order_by(Brand.name))
            brands = result.scalars().all()

            def format_brand(brand: Brand, idx: int) -> str:
                # Подсчитываем количество товаров
                products_count = len(brand.products) if hasattr(brand, 'products') else 0
                return f"{idx}. <b>{brand.name}</b> (ID: {brand.id}, товаров: {products_count})"

            await send_paginated_message(
                callback=callback,
                items=brands,
                title="🏷️ <b>Список брендов:</b>",
                item_format=format_brand,
                items_per_page=PAGINATION_BRANDS_PER_PAGE,
                current_page=current_page,
                menu_callback="brands_menu",
                parse_mode="HTML"
            )
            await state.update_data(brands_page=current_page)
    except Exception as e:
        logger.error(f"Ошибка при получении брендов: {e}", exc_info=True)
        await callback.message.answer("❌ Ошибка при загрузке списка брендов")
        await callback.answer()

@router.callback_query(F.data == "add_brand_start")
@admin_required
async def add_brand_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления бренда"""
    await callback.message.answer("✏️ Введите название нового бренда:")
    await state.set_state(BrandStates.add_name)
    await callback.answer()

@router.message(BrandStates.add_name)
@admin_required
async def add_brand_finish(message: Message, state: FSMContext):
    """Завершение добавления бренда"""
    brand_name = message.text.strip()
    if not brand_name:
        await message.answer("❌ Название бренда не может быть пустым. Попробуйте снова:")
        return

    try:
        async with AsyncSessionLocal() as session:
            # Проверяем на дубликат
            existing = await session.scalar(
                select(Brand).where(func.lower(Brand.name) == func.lower(brand_name))
            )
            if existing:
                await message.answer(f"❌ Бренд '{brand_name}' уже существует!")
                await state.clear()
                return await admin_panel(message)

            # Создаем новый бренд
            new_brand = Brand(name=brand_name)
            session.add(new_brand)
            await session.commit()
            await session.refresh(new_brand)

            await message.answer(f"✅ Бренд <b>{brand_name}</b> успешно добавлен! (ID: {new_brand.id})", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при добавлении бренда: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при добавлении бренда")
    finally:
        await state.clear()
        await admin_panel(message)

@router.callback_query(F.data == "edit_brand_start")
@admin_required
async def edit_brand_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования бренда"""
    await callback.message.answer("🔍 Введите название бренда для редактирования:")
    await state.set_state(BrandStates.edit_select)
    await callback.answer()

@router.message(BrandStates.edit_select)
@admin_required
async def find_brand_to_edit(message: Message, state: FSMContext):
    """Поиск бренда для редактирования"""
    search_text = message.text.strip().lower()
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
                await message.answer("❌ Бренд не найден. Проверьте название.")
                await state.clear()
                return

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
        logger.error(f"Ошибка при поиске бренда: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при поиске бренда")
        await state.clear()

@router.message(BrandStates.edit_name)
@admin_required
async def save_brand_edit(message: Message, state: FSMContext):
    """Сохранение изменений бренда"""
    new_name = message.text.strip()
    if not new_name:
        await message.answer("❌ Название не может быть пустым. Введите снова:")
        return

    try:
        data = await state.get_data()
        brand_id = data.get('brand_id')

        async with AsyncSessionLocal() as session:
            brand = await session.get(Brand, brand_id)
            if not brand:
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
                await message.answer(f"❌ Бренд с названием '{new_name}' уже существует!")
                return

            old_name = brand.name
            brand.name = new_name
            await session.commit()

            await message.answer(
                f"✅ Бренд успешно обновлен!\n"
                f"Было: {old_name}\n"
                f"Стало: {new_name}"
            )
    except Exception as e:
        logger.error(f"Ошибка при сохранении бренда: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при сохранении изменений")
    finally:
        await state.clear()
        await admin_panel(message)

@router.callback_query(F.data == "delete_brand_start")
@admin_required
async def delete_brand_start(callback: CallbackQuery, state: FSMContext):
    """Начало удаления бренда"""
    await callback.message.answer("🔍 Введите название бренда для удаления:")
    await state.set_state(BrandStates.delete_select)
    await callback.answer()

@router.message(BrandStates.delete_select)
@admin_required
async def find_brand_to_delete(message: Message, state: FSMContext):
    """Поиск бренда для удаления"""
    search_text = message.text.strip().lower()
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
                await message.answer("❌ Бренд не найден. Проверьте название.")
                await state.clear()
                return

            # Подсчитываем количество товаров
            products_count = await session.scalar(
                select(func.count(Product.id)).where(Product.brand_id == brand.id)
            )

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
        logger.error(f"Ошибка при поиске бренда: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при поиске бренда")
        await state.clear()

@router.callback_query(BrandStates.delete_confirm, F.data == "confirm_brand_delete")
@admin_required
async def execute_brand_delete(callback: CallbackQuery, state: FSMContext):
    """Удаление бренда"""
    try:
        data = await state.get_data()
        brand_id = data.get('brand_id')

        if not brand_id:
            await callback.message.answer("❌ Бренд не выбран")
            await state.clear()
            return

        async with AsyncSessionLocal() as session:
            brand = await session.get(Brand, brand_id)
            if not brand:
                await callback.message.answer("❌ Бренд не найден")
                await state.clear()
                return

            # Удаляем все фото товаров этого бренда
            products = await session.execute(
                select(Product).where(Product.brand_id == brand_id)
            )
            for product in products.scalars().all():
                if product.photo_url:
                    await delete_photo(product.photo_url)

            brand_name = brand.name
            await session.delete(brand)
            await session.commit()

            await callback.message.answer(
                f"✅ Бренд успешно удалён:\n"
                f"Название: {brand_name}\n"
                f"ID: {brand_id}"
            )
    except Exception as e:
        logger.error(f"Ошибка при удалении бренда: {e}", exc_info=True)
        await callback.message.answer("❌ Произошла ошибка при удалении бренда")
    finally:
        await state.clear()
        await admin_panel(callback.message)
        await callback.answer()

@router.callback_query(BrandStates.delete_confirm, F.data == "cancel_brand_delete")
@admin_required
async def cancel_brand_delete(callback: CallbackQuery, state: FSMContext):
    """Отмена удаления бренда"""
    await state.clear()
    await callback.message.answer("❌ Удаление бренда отменено")
    await admin_panel(callback.message)
    await callback.answer()

# ========================
# CATEGORIES MANAGEMENT
# ========================

@router.callback_query(F.data == "categories_menu")
@admin_required
async def categories_menu(callback: CallbackQuery):
    """Меню управления категориями"""
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
    except Exception as e:
        logger.error(f"Ошибка в categories_menu: {e}")
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
    try:
        data = await state.get_data()
        current_page = data.get('categories_page', 0)

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Category).order_by(Category.name))
            categories = result.scalars().all()

            def format_category(category: Category, idx: int) -> str:
                # Подсчитываем количество товаров
                products_count = len(category.products) if hasattr(category, 'products') else 0
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
    except Exception as e:
        logger.error(f"Ошибка при получении категорий: {e}", exc_info=True)
        await callback.message.answer("❌ Ошибка при загрузке списка категорий")
        await callback.answer()

@router.callback_query(F.data == "add_category_start")
@admin_required
async def add_category_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления категории"""
    await callback.message.answer("✏️ Введите название новой категории:")
    await state.set_state(CategoryStates.add_name)
    await callback.answer()

@router.message(CategoryStates.add_name)
@admin_required
async def add_category_finish(message: Message, state: FSMContext):
    """Завершение добавления категории"""
    category_name = message.text.strip()
    if not category_name:
        await message.answer("❌ Название категории не может быть пустым. Попробуйте снова:")
        return

    try:
        async with AsyncSessionLocal() as session:
            # Проверяем на дубликат
            existing = await session.scalar(
                select(Category).where(func.lower(Category.name) == func.lower(category_name))
            )
            if existing:
                await message.answer(f"❌ Категория '{category_name}' уже существует!")
                await state.clear()
                return await admin_panel(message)

            # Создаем новую категорию
            new_category = Category(name=category_name)
            session.add(new_category)
            await session.commit()
            await session.refresh(new_category)

            await message.answer(f"✅ Категория <b>{category_name}</b> успешно добавлена! (ID: {new_category.id})", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при добавлении категории: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при добавлении категории")
    finally:
        await state.clear()
        await admin_panel(message)

@router.callback_query(F.data == "edit_category_start")
@admin_required
async def edit_category_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования категории"""
    await callback.message.answer("🔍 Введите название категории для редактирования:")
    await state.set_state(CategoryStates.edit_select)
    await callback.answer()

@router.message(CategoryStates.edit_select)
@admin_required
async def find_category_to_edit(message: Message, state: FSMContext):
    """Поиск категории для редактирования"""
    search_text = message.text.strip().lower()
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
                await message.answer("❌ Категория не найдена. Проверьте название.")
                await state.clear()
                return

            await state.update_data(category_id=category.id, category_name=category.name)
            await message.answer(
                f"📂 <b>Найдена категория:</b>\n"
                f"Название: {category.name}\n"
                f"ID: {category.id}\n\n"
                f"Введите новое название:",
                parse_mode="HTML"
            )
            await state.set_state(CategoryStates.edit_name)
    except Exception as e:
        logger.error(f"Ошибка при поиске категории: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при поиске категории")
        await state.clear()

@router.message(CategoryStates.edit_name)
@admin_required
async def save_category_edit(message: Message, state: FSMContext):
    """Сохранение изменений категории"""
    new_name = message.text.strip()
    if not new_name:
        await message.answer("❌ Название не может быть пустым. Введите снова:")
        return

    try:
        data = await state.get_data()
        category_id = data.get('category_id')

        async with AsyncSessionLocal() as session:
            category = await session.get(Category, category_id)
            if not category:
                await message.answer("❌ Категория не найдена")
                await state.clear()
                return

            # Проверяем на дубликат
            existing = await session.scalar(
                select(Category).where(
                    and_(
                        func.lower(Category.name) == func.lower(new_name),
                        Category.id != category_id
                    )
                )
            )
            if existing:
                await message.answer(f"❌ Категория с названием '{new_name}' уже существует!")
                return

            old_name = category.name
            category.name = new_name
            await session.commit()

            await message.answer(
                f"✅ Категория успешно обновлена!\n"
                f"Было: {old_name}\n"
                f"Стало: {new_name}"
            )
    except Exception as e:
        logger.error(f"Ошибка при сохранении категории: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при сохранении изменений")
    finally:
        await state.clear()
        await admin_panel(message)

@router.callback_query(F.data == "delete_category_start")
@admin_required
async def delete_category_start(callback: CallbackQuery, state: FSMContext):
    """Начало удаления категории"""
    await callback.message.answer("🔍 Введите название категории для удаления:")
    await state.set_state(CategoryStates.delete_select)
    await callback.answer()

@router.message(CategoryStates.delete_select)
@admin_required
async def find_category_to_delete(message: Message, state: FSMContext):
    """Поиск категории для удаления"""
    search_text = message.text.strip().lower()
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
                await message.answer("❌ Категория не найдена. Проверьте название.")
                await state.clear()
                return

            # Подсчитываем количество товаров
            products_count = await session.scalar(
                select(func.count(Product.id)).where(Product.category_id == category.id)
            )

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
        logger.error(f"Ошибка при поиске категории: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при поиске категории")
        await state.clear()

@router.callback_query(CategoryStates.delete_confirm, F.data == "confirm_category_delete")
@admin_required
async def execute_category_delete(callback: CallbackQuery, state: FSMContext):
    """Удаление категории"""
    try:
        data = await state.get_data()
        category_id = data.get('category_id')

        if not category_id:
            await callback.message.answer("❌ Категория не выбрана")
            await state.clear()
            return

        async with AsyncSessionLocal() as session:
            category = await session.get(Category, category_id)
            if not category:
                await callback.message.answer("❌ Категория не найдена")
                await state.clear()
                return

            # Удаляем все фото товаров этой категории
            products = await session.execute(
                select(Product).where(Product.category_id == category_id)
            )
            for product in products.scalars().all():
                if product.photo_url:
                    await delete_photo(product.photo_url)

            category_name = category.name
            await session.delete(category)
            await session.commit()

            await callback.message.answer(
                f"✅ Категория успешно удалена:\n"
                f"Название: {category_name}\n"
                f"ID: {category_id}"
            )
    except Exception as e:
        logger.error(f"Ошибка при удалении категории: {e}", exc_info=True)
        await callback.message.answer("❌ Произошла ошибка при удалении категории")
    finally:
        await state.clear()
        await admin_panel(callback.message)
        await callback.answer()

@router.callback_query(CategoryStates.delete_confirm, F.data == "cancel_category_delete")
@admin_required
async def cancel_category_delete(callback: CallbackQuery, state: FSMContext):
    """Отмена удаления категории"""
    await state.clear()
    await callback.message.answer("❌ Удаление категории отменено")
    await admin_panel(callback.message)
    await callback.answer()

# ========================
# PRODUCTS MANAGEMENT
# ========================

@router.callback_query(F.data == "products_menu")
@admin_required
async def products_menu(callback: CallbackQuery):
    """Меню управления товарами"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 Список", callback_data="view_products"),
        InlineKeyboardButton(text="➕ Добавить", callback_data="add_product_start")
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_product_start"),
        InlineKeyboardButton(text="🗑️ Удалить", callback_data="delete_product_start")
    )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back"))

    try:
        await callback.message.edit_text(
            "📦 <b>Управление товарами:</b>",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка в products_menu: {e}")
        await callback.message.answer(
            "📦 <b>Управление товарами:</b>",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    finally:
        await callback.answer()

@router.callback_query(F.data == "view_products")
@admin_required
async def view_products(callback: CallbackQuery, state: FSMContext):
    """Просмотр списка товаров"""
    try:
        data = await state.get_data()
        current_page = data.get('products_page', 0)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Product)
                .options(joinedload(Product.category), joinedload(Product.brand))
                .order_by(Product.name)
            )
            products = result.unique().scalars().all()

            def format_product(product: Product, idx: int) -> str:
                brand_name = product.brand.name if product.brand else "N/A"
                category_name = product.category.name if product.category else "N/A"
                return (
                    f"{idx}. <b>{product.name}</b>\n"
                    f"   Бренд: {brand_name} | Категория: {category_name}\n"
                    f"   Цена: {product.price:.2f} ₽ | ID: {product.id}"
                )

            await send_paginated_message(
                callback=callback,
                items=products,
                title="📦 <b>Список товаров:</b>",
                item_format=format_product,
                items_per_page=PAGINATION_PRODUCTS_PER_PAGE,
                current_page=current_page,
                menu_callback="products_menu",
                parse_mode="HTML"
            )
            await state.update_data(products_page=current_page)
    except Exception as e:
        logger.error(f"Ошибка при получении товаров: {e}", exc_info=True)
        await callback.message.answer("❌ Ошибка при загрузке списка товаров")
        await callback.answer()

@router.callback_query(F.data == "add_product_start")
@admin_required
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления товара"""
    try:
        async with AsyncSessionLocal() as session:
            brands = await get_brands(session)

            if not brands:
                await callback.message.answer("❌ Сначала добавьте бренды!")
                await callback.answer()
                return

            builder = InlineKeyboardBuilder()
            for brand in brands:
                builder.button(text=brand.name, callback_data=f"add_prod_brand_{brand.id}")
            builder.adjust(2)
            builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="products_menu"))

            await callback.message.edit_text(
                "Выберите бренд для товара:",
                reply_markup=builder.as_markup()
            )
            await state.set_state(ProductStates.add_brand)
    except Exception as e:
        logger.error(f"Ошибка при запуске добавления товара: {e}", exc_info=True)
        await callback.message.answer("❌ Ошибка при загрузке брендов")
    finally:
        await callback.answer()

async def get_brands(session: AsyncSession):
    """Получить список брендов"""
    result = await session.execute(select(Brand).order_by(Brand.name))
    return result.scalars().all()

async def get_categories(session: AsyncSession):
    """Получить список категорий"""
    result = await session.execute(select(Category).order_by(Category.name))
    return result.scalars().all()

@router.callback_query(ProductStates.add_brand, F.data.startswith("add_prod_brand_"))
@admin_required
async def select_product_brand(callback: CallbackQuery, state: FSMContext):
    """Выбор бренда для товара"""
    try:
        brand_id = int(callback.data.split("_")[3])
        await state.update_data(brand_id=brand_id)

        async with AsyncSessionLocal() as session:
            categories = await get_categories(session)

            if not categories:
                await callback.message.answer("❌ Сначала добавьте категории!")
                await state.clear()
                return

            builder = InlineKeyboardBuilder()
            for category in categories:
                builder.button(text=category.name, callback_data=f"add_prod_cat_{category.id}")
            builder.adjust(2)
            builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="add_product_start"))

            await callback.message.edit_text(
                "Выберите категорию для товара:",
                reply_markup=builder.as_markup()
            )
            await state.set_state(ProductStates.add_category)
    except Exception as e:
        logger.error(f"Ошибка при выборе бренда: {e}", exc_info=True)
        await callback.message.answer("❌ Ошибка при выборе бренда")
        await state.clear()
    finally:
        await callback.answer()

@router.callback_query(ProductStates.add_category, F.data.startswith("add_prod_cat_"))
@admin_required
async def select_product_category(callback: CallbackQuery, state: FSMContext):
    """Выбор категории для товара"""
    try:
        category_id = int(callback.data.split("_")[3])
        await state.update_data(category_id=category_id)
        await callback.message.answer("✏️ Введите название товара:")
        await state.set_state(ProductStates.add_name)
    except Exception as e:
        logger.error(f"Ошибка при выборе категории: {e}", exc_info=True)
        await callback.message.answer("❌ Ошибка при выборе категории")
        await state.clear()
    finally:
        await callback.answer()

@router.message(ProductStates.add_name)
@admin_required
async def set_product_name(message: Message, state: FSMContext):
    """Установка названия товара"""
    product_name = message.text.strip()
    if not product_name:
        await message.answer("❌ Название товара не может быть пустым. Введите снова:")
        return

    await state.update_data(name=product_name)
    await message.answer("💰 Введите цену товара (число):")
    await state.set_state(ProductStates.add_price)

@router.message(ProductStates.add_price)
@admin_required
async def set_product_price(message: Message, state: FSMContext):
    """Установка цены товара"""
    try:
        price = float(message.text.replace(',', '.'))
        if price <= 0:
            await message.answer("❌ Цена должна быть больше нуля. Введите снова:")
            return

        await state.update_data(price=price)
        await message.answer("📸 Отправьте фото товара:")
        await state.set_state(ProductStates.add_photo)
    except ValueError:
        await message.answer("❌ Введите корректную цену (число):")

@router.message(ProductStates.add_photo, F.photo)
@admin_required
async def set_product_photo(message: Message, state: FSMContext, bot: Bot):
    """Установка фото товара"""
    try:
        photo = message.photo[-1]
        photo_url = await save_photo_from_telegram(bot, photo.file_id)
        await state.update_data(photo_url=photo_url)
        await message.answer("📝 Введите описание товара (или '-' чтобы пропустить):")
        await state.set_state(ProductStates.add_description)
    except Exception as e:
        logger.error(f"Ошибка сохранения фото: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка сохранения фото: {str(e)}")

@router.message(ProductStates.add_photo)
@admin_required
async def set_product_photo_error(message: Message):
    """Обработка ошибки при отправке фото"""
    await message.answer("❌ Отправьте фото товара (изображение):")

@router.message(ProductStates.add_description)
@admin_required
async def add_product_finish(message: Message, state: FSMContext):
    """Завершение добавления товара"""
    description = message.text.strip() if message.text.strip() != "-" else None

    try:
        data = await state.get_data()
        brand_id = data.get('brand_id')
        category_id = data.get('category_id')
        name = data.get('name')
        price = data.get('price')
        photo_url = data.get('photo_url')

        if not all([brand_id, category_id, name, price]):
            await message.answer("❌ Ошибка: не все данные заполнены. Начните заново.")
            await state.clear()
            return await admin_panel(message)

        async with AsyncSessionLocal() as session:
            # Проверяем существование бренда и категории
            brand = await session.get(Brand, brand_id)
            category = await session.get(Category, category_id)

            if not brand:
                await message.answer("❌ Бренд не найден")
                await state.clear()
                return await admin_panel(message)

            if not category:
                await message.answer("❌ Категория не найдена")
                await state.clear()
                return await admin_panel(message)

            # Создаем товар
            product = Product(
                name=name,
                price=price,
                photo_url=photo_url,
                description=description,
                category_id=category_id,
                brand_id=brand_id
            )
            session.add(product)
            await session.commit()
            await session.refresh(product)

            await message.answer(
                f"✅ Товар успешно добавлен!\n"
                f"Название: {product.name}\n"
                f"Бренд: {brand.name}\n"
                f"Категория: {category.name}\n"
                f"Цена: {product.price:.2f} ₽\n"
                f"ID: {product.id}"
            )
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при добавлении товара")
    finally:
        await state.clear()
        await admin_panel(message)

@router.callback_query(F.data == "edit_product_start")
@admin_required
async def edit_product_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования товара"""
    await callback.message.answer("🔍 Введите название товара для редактирования:")
    await state.set_state(ProductStates.edit_select)
    await callback.answer()

@router.message(ProductStates.edit_select)
@admin_required
async def find_product_to_edit(message: Message, state: FSMContext):
    """Поиск товара для редактирования"""
    search_text = message.text.strip().lower()
    if not search_text:
        await message.answer("❌ Введите название товара:")
        return

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Product)
                .where(func.lower(Product.name) == search_text)
                .options(joinedload(Product.category), joinedload(Product.brand))
            )
            products = result.unique().scalars().all()

            if not products:
                await message.answer("❌ Товар не найден. Проверьте название.")
                await state.clear()
                return

            if len(products) == 1:
                product = products[0]
                await show_product_edit_menu(message, state, product)
            else:
                # Несколько товаров с таким названием
                builder = InlineKeyboardBuilder()
                for product in products:
                    brand_name = product.brand.name if product.brand else "N/A"
                    category_name = product.category.name if product.category else "N/A"
                    builder.button(
                        text=f"{product.name} ({brand_name}/{category_name})",
                        callback_data=f"select_product_{product.id}"
                    )
                builder.adjust(1)
                await message.answer(
                    f"Найдено {len(products)} товаров с таким названием. Выберите нужный:",
                    reply_markup=builder.as_markup()
                )
    except Exception as e:
        logger.error(f"Ошибка при поиске товара: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при поиске товара")
        await state.clear()

async def show_product_edit_menu(message: Message, state: FSMContext, product: Product):
    """Показать меню редактирования товара"""
    await state.update_data(product_id=product.id)

    brand_name = product.brand.name if product.brand else "N/A"
    category_name = product.category.name if product.category else "N/A"

    info_text = (
        f"📦 <b>Товар:</b> {product.name}\n"
        f"🏷️ Бренд: {brand_name}\n"
        f"📂 Категория: {category_name}\n"
        f"💰 Цена: {product.price:.2f} ₽\n"
        f"📝 Описание: {product.description or 'нет'}\n"
        f"🆔 ID: {product.id}"
    )

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Название", callback_data="edit_field_name"),
        InlineKeyboardButton(text="💰 Цена", callback_data="edit_field_price")
    )
    builder.row(
        InlineKeyboardButton(text="📝 Описание", callback_data="edit_field_desc"),
        InlineKeyboardButton(text="📸 Фото", callback_data="edit_field_photo")
    )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="products_menu"))

    if product.photo_url:
        try:
            photo_path = STATIC_ROOT / product.photo_url
            if photo_path.exists():
                photo = FSInputFile(photo_path)
                await message.answer_photo(photo, caption=info_text, reply_markup=builder.as_markup(), parse_mode="HTML")
            else:
                await message.answer(info_text, reply_markup=builder.as_markup(), parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка отправки фото: {e}")
            await message.answer(info_text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        await message.answer(info_text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("select_product_"))
@admin_required
async def handle_product_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора товара из списка"""
    try:
        product_id = int(callback.data.split("_")[2])

        async with AsyncSessionLocal() as session:
            product = await session.get(
                Product,
                product_id,
                options=[joinedload(Product.category), joinedload(Product.brand)]
            )

            if product:
                await callback.message.delete()
                await show_product_edit_menu(callback.message, state, product)
            else:
                await callback.answer("❌ Товар не найден", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка выбора товара: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при выборе товара", show_alert=True)
    finally:
        await callback.answer()

@router.callback_query(F.data == "edit_field_name")
@admin_required
async def edit_product_name(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования названия"""
    await callback.message.answer("✏️ Введите новое название:")
    await state.update_data(field="name")
    await state.set_state(ProductStates.edit_field)
    await callback.answer()

@router.callback_query(F.data == "edit_field_price")
@admin_required
async def edit_product_price(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования цены"""
    await callback.message.answer("💰 Введите новую цену:")
    await state.update_data(field="price")
    await state.set_state(ProductStates.edit_field)
    await callback.answer()

@router.callback_query(F.data == "edit_field_desc")
@admin_required
async def edit_product_desc(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования описания"""
    await callback.message.answer("📝 Введите новое описание (или '-' чтобы удалить):")
    await state.update_data(field="description")
    await state.set_state(ProductStates.edit_field)
    await callback.answer()

@router.callback_query(F.data == "edit_field_photo")
@admin_required
async def edit_product_photo(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования фото"""
    await callback.message.answer("📸 Отправьте новое фото:")
    await state.update_data(field="photo_url")
    await state.set_state(ProductStates.edit_field)
    await callback.answer()

@router.message(ProductStates.edit_field, F.photo)
@admin_required
async def save_product_photo_edit(message: Message, state: FSMContext, bot: Bot):
    """Сохранение нового фото товара"""
    try:
        data = await state.get_data()
        product_id = data.get('product_id')
        field = data.get('field')

        if field != "photo_url":
            return

        async with AsyncSessionLocal() as session:
            product = await session.get(Product, product_id)
            if not product:
                await message.answer("❌ Товар не найден")
                await state.clear()
                return

            # Удаляем старое фото
            if product.photo_url:
                await delete_photo(product.photo_url)

            # Сохраняем новое фото
            photo = message.photo[-1]
            new_photo_url = await save_photo_from_telegram(bot, photo.file_id)
            product.photo_url = new_photo_url
            await session.commit()

            await message.answer("✅ Фото успешно обновлено!")
            await state.clear()
            await admin_panel(message)
    except Exception as e:
        logger.error(f"Ошибка при обновлении фото: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка обновления фото: {str(e)}")

@router.message(ProductStates.edit_field)
@admin_required
async def save_product_changes(message: Message, state: FSMContext):
    """Сохранение изменений товара"""
    try:
        data = await state.get_data()
        product_id = data.get('product_id')
        field = data.get('field')
        value = message.text.strip()

        if not product_id or not field:
            await message.answer("❌ Ошибка: данные не найдены")
            await state.clear()
            return

        async with AsyncSessionLocal() as session:
            product = await session.get(Product, product_id)
            if not product:
                await message.answer("❌ Товар не найден")
                await state.clear()
                return

            # Обработка значений в зависимости от поля
            if field == "description" and value == "-":
                value = None
            elif field == "price":
                try:
                    value = float(value.replace(',', '.'))
                    if value <= 0:
                        await message.answer("❌ Цена должна быть больше нуля. Введите снова:")
                        return
                except ValueError:
                    await message.answer("❌ Введите корректную цену (число):")
                    return
            elif field == "name":
                if not value:
                    await message.answer("❌ Название не может быть пустым. Введите снова:")
                    return

            setattr(product, field, value)
            await session.commit()

            await message.answer(f"✅ {field.capitalize()} успешно обновлено!")
    except Exception as e:
        logger.error(f"Ошибка при сохранении изменений: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при сохранении изменений")
    finally:
        await state.clear()
        await admin_panel(message)

@router.callback_query(F.data == "delete_product_start")
@admin_required
async def delete_product_start(callback: CallbackQuery, state: FSMContext):
    """Начало удаления товара"""
    await callback.message.answer("🔍 Введите название товара для удаления:")
    await state.set_state(ProductStates.delete_select)
    await callback.answer()

@router.message(ProductStates.delete_select)
@admin_required
async def find_product_to_delete(message: Message, state: FSMContext):
    """Поиск товара для удаления"""
    search_text = message.text.strip().lower()
    if not search_text:
        await message.answer("❌ Введите название товара:")
        return

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Product)
                .where(func.lower(Product.name) == search_text)
                .options(joinedload(Product.category), joinedload(Product.brand))
            )
            products = result.unique().scalars().all()

            if not products:
                await message.answer("❌ Товар не найден. Проверьте название.")
                await state.clear()
                return

            if len(products) == 1:
                product = products[0]
                await show_product_delete_confirmation(message, state, product)
            else:
                # Несколько товаров
                builder = InlineKeyboardBuilder()
                for product in products:
                    brand_name = product.brand.name if product.brand else "N/A"
                    category_name = product.category.name if product.category else "N/A"
                    builder.button(
                        text=f"{product.name} ({brand_name}/{category_name})",
                        callback_data=f"select_product_delete_{product.id}"
                    )
                builder.adjust(1)
                await message.answer(
                    f"Найдено {len(products)} товаров. Выберите нужный:",
                    reply_markup=builder.as_markup()
                )
    except Exception as e:
        logger.error(f"Ошибка при поиске товара: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при поиске товара")
        await state.clear()

@router.callback_query(F.data.startswith("select_product_delete_"))
@admin_required
async def handle_product_delete_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора товара для удаления"""
    try:
        product_id = int(callback.data.split("_")[3])

        async with AsyncSessionLocal() as session:
            product = await session.get(
                Product,
                product_id,
                options=[joinedload(Product.category), joinedload(Product.brand)]
            )

            if product:
                await callback.message.delete()
                await show_product_delete_confirmation(callback.message, state, product)
            else:
                await callback.answer("❌ Товар не найден", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка выбора товара: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при выборе товара", show_alert=True)
    finally:
        await callback.answer()

async def show_product_delete_confirmation(message: Message, state: FSMContext, product: Product):
    """Показать подтверждение удаления товара"""
    await state.update_data(product_id=product.id)

    brand_name = product.brand.name if product.brand else "N/A"
    category_name = product.category.name if product.category else "N/A"

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да, удалить", callback_data="confirm_product_delete"),
        InlineKeyboardButton(text="❌ Нет, отмена", callback_data="cancel_product_delete")
    )

    await message.answer(
        f"Вы уверены, что хотите удалить товар?\n"
        f"Название: {product.name}\n"
        f"Бренд: {brand_name}\n"
        f"Категория: {category_name}\n"
        f"Цена: {product.price:.2f} ₽\n"
        f"ID: {product.id}",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductStates.delete_confirm)

@router.callback_query(ProductStates.delete_confirm, F.data == "confirm_product_delete")
@admin_required
async def execute_product_delete(callback: CallbackQuery, state: FSMContext):
    """Удаление товара"""
    try:
        data = await state.get_data()
        product_id = data.get('product_id')

        if not product_id:
            await callback.message.answer("❌ Товар не выбран")
            await state.clear()
            return

        async with AsyncSessionLocal() as session:
            product = await session.get(Product, product_id)
            if not product:
                await callback.message.answer("❌ Товар не найден")
                await state.clear()
                return

            # Удаляем фото
            if product.photo_url:
                await delete_photo(product.photo_url)

            product_name = product.name
            await session.delete(product)
            await session.commit()

            await callback.message.answer(
                f"✅ Товар успешно удалён:\n"
                f"Название: {product_name}\n"
                f"ID: {product_id}"
            )
    except Exception as e:
        logger.error(f"Ошибка при удалении товара: {e}", exc_info=True)
        await callback.message.answer("❌ Произошла ошибка при удалении товара")
    finally:
        await state.clear()
        await admin_panel(callback.message)
        await callback.answer()

@router.callback_query(ProductStates.delete_confirm, F.data == "cancel_product_delete")
@admin_required
async def cancel_product_delete(callback: CallbackQuery, state: FSMContext):
    """Отмена удаления товара"""
    await state.clear()
    await callback.message.answer("❌ Удаление товара отменено")
    await admin_panel(callback.message)
    await callback.answer()

# ========================
# PAGINATION HANDLER
# ========================

@router.callback_query(F.data.startswith("page_"))
@admin_required
async def handle_pagination(callback: CallbackQuery, state: FSMContext):
    """Обработка пагинации"""
    try:
        page = int(callback.data.split("_")[1])
        message_text = callback.message.text or ""

        # Определяем контекст по тексту сообщения
        if "товар" in message_text.lower():
            await state.update_data(products_page=page)
            await view_products(callback, state)
        elif "бренд" in message_text.lower():
            await state.update_data(brands_page=page)
            await view_brands(callback, state)
        elif "категори" in message_text.lower():
            await state.update_data(categories_page=page)
            await view_categories(callback, state)
        else:
            await callback.answer("Неизвестный контекст пагинации")
    except Exception as e:
        logger.error(f"Ошибка обработки пагинации: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при переключении страницы")
