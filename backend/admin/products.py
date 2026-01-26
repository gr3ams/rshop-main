
"""
Управление товарами в админ-панели
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from models import Product, Brand, Category
from database import AsyncSessionLocal
from .config import PAGINATION_PRODUCTS_PER_PAGE, STATIC_ROOT
from .states import ProductStates
from .utils import admin_required, send_paginated_message, delete_photo, save_photo_from_telegram, get_brands, get_categories, get_products_with_details
from .main_menu import admin_panel
from logging_config import setup_logger

logger = setup_logger(__name__, "admin", logging.DEBUG)

router = Router()

@router.callback_query(F.data == "products_menu")
@admin_required
async def products_menu(callback: CallbackQuery):
    """Меню управления товарами"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Открытие меню управления товарами: user_id={user_id}")
    
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
        logger.debug(f"Меню товаров отображено: user_id={user_id}")
    except Exception as e:
        logger.error(f"Ошибка в products_menu: {e}", exc_info=True)
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
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Просмотр списка товаров: user_id={user_id}")
    
    try:
        data = await state.get_data()
        current_page = data.get('products_page', 0)
        logger.debug(f"Текущая страница: {current_page}, user_id={user_id}")

        async with AsyncSessionLocal() as session:
            products = await get_products_with_details(session)

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
                parse_mode="HTML",
                page_prefix="page_products"
            )
            await state.update_data(products_page=current_page)
            logger.info(f"Список товаров отображен: user_id={user_id}, total={len(products)}, page={current_page}")
    except Exception as e:
        logger.error(f"Ошибка при получении товаров: user_id={user_id}, error={str(e)}", exc_info=True)
        await callback.message.answer("❌ Ошибка при загрузке списка товаров")
        await callback.answer()

@router.callback_query(F.data == "add_product_start")
@admin_required
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления товара"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Начало добавления товара: user_id={user_id}")
    
    try:
        async with AsyncSessionLocal() as session:
            brands = await get_brands(session)

            if not brands:
                logger.warning(f"Нет брендов для добавления товара: user_id={user_id}")
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
            logger.debug(f"Список брендов для выбора отображен: user_id={user_id}, brands_count={len(brands)}")
    except Exception as e:
        logger.error(f"Ошибка при запуске добавления товара: user_id={user_id}, error={str(e)}", exc_info=True)
        await callback.message.answer("❌ Ошибка при загрузке брендов")
    finally:
        await callback.answer()

@router.callback_query(ProductStates.add_brand, F.data.startswith("add_prod_brand_"))
@admin_required
async def select_product_brand(callback: CallbackQuery, state: FSMContext):
    """Выбор бренда для товара"""
    user_id = callback.from_user.id if callback.from_user else None
    try:
        brand_id = int(callback.data.split("_")[3])
        logger.info(f"Выбор бренда для товара: user_id={user_id}, brand_id={brand_id}")
        await state.update_data(brand_id=brand_id)

        async with AsyncSessionLocal() as session:
            categories = await get_categories(session)

            if not categories:
                logger.warning(f"Нет категорий для добавления товара: user_id={user_id}")
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
            logger.debug(f"Список категорий для выбора отображен: user_id={user_id}, categories_count={len(categories)}")
    except Exception as e:
        logger.error(f"Ошибка при выборе бренда: user_id={user_id}, error={str(e)}", exc_info=True)
        await callback.message.answer("❌ Ошибка при выборе бренда")
        await state.clear()
    finally:
        await callback.answer()

@router.callback_query(ProductStates.add_category, F.data.startswith("add_prod_cat_"))
@admin_required
async def select_product_category(callback: CallbackQuery, state: FSMContext):
    """Выбор категории для товара"""
    user_id = callback.from_user.id if callback.from_user else None
    try:
        category_id = int(callback.data.split("_")[3])
        logger.info(f"Выбор категории для товара: user_id={user_id}, category_id={category_id}")
        await state.update_data(category_id=category_id)
        await callback.message.answer("✏️ Введите название товара:")
        await state.set_state(ProductStates.add_name)
    except Exception as e:
        logger.error(f"Ошибка при выборе категории: user_id={user_id}, error={str(e)}", exc_info=True)
        await callback.message.answer("❌ Ошибка при выборе категории")
        await state.clear()
    finally:
        await callback.answer()

@router.message(ProductStates.add_name)
@admin_required
async def set_product_name(message: Message, state: FSMContext):
    """Установка названия товара"""
    user_id = message.from_user.id if message.from_user else None
    product_name = message.text.strip()
    logger.debug(f"Установка названия товара: user_id={user_id}, name={product_name}")
    
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
    user_id = message.from_user.id if message.from_user else None
    try:
        price = float(message.text.replace(',', '.'))
        logger.debug(f"Установка цены товара: user_id={user_id}, price={price}")
        
        if price <= 0:
            await message.answer("❌ Цена должна быть больше нуля. Введите снова:")
            return

        await state.update_data(price=price)
        await message.answer("📸 Отправьте фото товара:")
        await state.set_state(ProductStates.add_photo)
    except ValueError:
        logger.warning(f"Некорректная цена: user_id={user_id}, input={message.text}")
        await message.answer("❌ Введите корректную цену (число):")

@router.message(ProductStates.add_photo, F.photo)
@admin_required
async def set_product_photo(message: Message, state: FSMContext, bot: Bot):
    """Установка фото товара"""
    user_id = message.from_user.id if message.from_user else None
    logger.info(f"Сохранение фото товара: user_id={user_id}")
    
    try:
        photo = message.photo[-1]
        photo_url = await save_photo_from_telegram(bot, photo.file_id)
        await state.update_data(photo_url=photo_url)
        logger.info(f"Фото товара сохранено: user_id={user_id}, photo_url={photo_url}")
        await message.answer("📝 Введите описание товара (или '-' чтобы пропустить):")
        await state.set_state(ProductStates.add_description)
    except Exception as e:
        logger.error(f"Ошибка сохранения фото: user_id={user_id}, error={str(e)}", exc_info=True)
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
    user_id = message.from_user.id if message.from_user else None
    description = message.text.strip() if message.text.strip() != "-" else None
    logger.info(f"Завершение добавления товара: user_id={user_id}, description_length={len(description) if description else 0}")

    try:
        data = await state.get_data()
        brand_id = data.get('brand_id')
        category_id = data.get('category_id')
        name = data.get('name')
        price = data.get('price')
        photo_url = data.get('photo_url')

        # Проверяем обязательные поля (photo_url может быть None)
        if not all([brand_id, category_id, name, price]):
            logger.error(f"Не все обязательные данные заполнены: user_id={user_id}, brand_id={brand_id}, category_id={category_id}, name={name}, price={price}, photo_url={photo_url}")
            await message.answer("❌ Ошибка: не все данные заполнены. Начните заново.")
            await state.clear()
            return await admin_panel(message)

        async with AsyncSessionLocal() as session:
            brand = await session.get(Brand, brand_id)
            category = await session.get(Category, category_id)

            if not brand:
                logger.error(f"Бренд не найден: user_id={user_id}, brand_id={brand_id}")
                await message.answer("❌ Бренд не найден")
                await state.clear()
                return await admin_panel(message)

            if not category:
                logger.error(f"Категория не найдена: user_id={user_id}, category_id={category_id}")
                await message.answer("❌ Категория не найдена")
                await state.clear()
                return await admin_panel(message)

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

            logger.info(f"Товар успешно добавлен: user_id={user_id}, product_id={product.id}, name={name}, brand_id={brand_id}, category_id={category_id}, price={price}")
            await message.answer(
                f"✅ Товар успешно добавлен!\n"
                f"Название: {product.name}\n"
                f"Бренд: {brand.name}\n"
                f"Категория: {category.name}\n"
                f"Цена: {product.price:.2f} ₽\n"
                f"ID: {product.id}"
            )
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара: user_id={user_id}, error={str(e)}", exc_info=True)
        await message.answer("❌ Произошла ошибка при добавлении товара")
    finally:
        await state.clear()
        await admin_panel(message)

@router.callback_query(F.data == "edit_product_start")
@admin_required
async def edit_product_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования товара"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Начало редактирования товара: user_id={user_id}")
    
    await callback.message.answer("🔍 Введите название товара для редактирования:")
    await state.set_state(ProductStates.edit_select)
    await callback.answer()

@router.message(ProductStates.edit_select)
@admin_required
async def find_product_to_edit(message: Message, state: FSMContext):
    """Поиск товара для редактирования"""
    user_id = message.from_user.id if message.from_user else None
    search_text = message.text.strip().lower()
    logger.info(f"Поиск товара для редактирования: user_id={user_id}, search={search_text}")
    
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
                logger.warning(f"Товар не найден для редактирования: user_id={user_id}, search={search_text}")
                await message.answer("❌ Товар не найден. Проверьте название.")
                await state.clear()
                return

            if len(products) == 1:
                product = products[0]
                logger.info(f"Товар найден для редактирования: user_id={user_id}, product_id={product.id}")
                await show_product_edit_menu(message, state, product)
            else:
                logger.info(f"Найдено несколько товаров: user_id={user_id}, count={len(products)}")
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
        logger.error(f"Ошибка при поиске товара: user_id={user_id}, search={search_text}, error={str(e)}", exc_info=True)
        await message.answer("❌ Произошла ошибка при поиске товара")
        await state.clear()

async def show_product_edit_menu(message: Message, state: FSMContext, product: Product):
    """Показать меню редактирования товара"""
    user_id = message.from_user.id if message.from_user else None
    logger.debug(f"Показ меню редактирования товара: user_id={user_id}, product_id={product.id}")
    
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
                logger.warning(f"Фото товара не найдено: user_id={user_id}, product_id={product.id}, photo_url={product.photo_url}")
                await message.answer(info_text, reply_markup=builder.as_markup(), parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка отправки фото: user_id={user_id}, error={str(e)}", exc_info=True)
            await message.answer(info_text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        await message.answer(info_text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("select_product_"))
@admin_required
async def handle_product_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора товара из списка"""
    user_id = callback.from_user.id if callback.from_user else None
    try:
        product_id = int(callback.data.split("_")[2])
        logger.info(f"Выбор товара из списка: user_id={user_id}, product_id={product_id}")

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
                logger.error(f"Товар не найден: user_id={user_id}, product_id={product_id}")
                await callback.answer("❌ Товар не найден", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка выбора товара: user_id={user_id}, error={str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка при выборе товара", show_alert=True)
    finally:
        await callback.answer()

@router.callback_query(F.data == "edit_field_name")
@admin_required
async def edit_product_name(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования названия"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.debug(f"Начало редактирования названия товара: user_id={user_id}")
    
    await callback.message.answer("✏️ Введите новое название:")
    await state.update_data(field="name")
    await state.set_state(ProductStates.edit_field)
    await callback.answer()

@router.callback_query(F.data == "edit_field_price")
@admin_required
async def edit_product_price(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования цены"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.debug(f"Начало редактирования цены товара: user_id={user_id}")
    
    await callback.message.answer("💰 Введите новую цену:")
    await state.update_data(field="price")
    await state.set_state(ProductStates.edit_field)
    await callback.answer()

@router.callback_query(F.data == "edit_field_desc")
@admin_required
async def edit_product_desc(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования описания"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.debug(f"Начало редактирования описания товара: user_id={user_id}")
    
    await callback.message.answer("📝 Введите новое описание (или '-' чтобы удалить):")
    await state.update_data(field="description")
    await state.set_state(ProductStates.edit_field)
    await callback.answer()

@router.callback_query(F.data == "edit_field_photo")
@admin_required
async def edit_product_photo(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования фото"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.debug(f"Начало редактирования фото товара: user_id={user_id}")
    
    await callback.message.answer("📸 Отправьте новое фото:")
    await state.update_data(field="photo_url")
    await state.set_state(ProductStates.edit_field)
    await callback.answer()

@router.message(ProductStates.edit_field, F.photo)
@admin_required
async def save_product_photo_edit(message: Message, state: FSMContext, bot: Bot):
    """Сохранение нового фото товара"""
    user_id = message.from_user.id if message.from_user else None
    logger.info(f"Сохранение нового фото товара: user_id={user_id}")
    
    try:
        data = await state.get_data()
        product_id = data.get('product_id')
        field = data.get('field')

        if field != "photo_url":
            return

        async with AsyncSessionLocal() as session:
            product = await session.get(Product, product_id)
            if not product:
                logger.error(f"Товар не найден: user_id={user_id}, product_id={product_id}")
                await message.answer("❌ Товар не найден")
                await state.clear()
                return

            if product.photo_url:
                await delete_photo(product.photo_url)
                logger.debug(f"Старое фото удалено: user_id={user_id}, old_photo_url={product.photo_url}")

            photo = message.photo[-1]
            new_photo_url = await save_photo_from_telegram(bot, photo.file_id)
            product.photo_url = new_photo_url
            await session.commit()

            logger.info(f"Фото товара успешно обновлено: user_id={user_id}, product_id={product_id}, new_photo_url={new_photo_url}")
            await message.answer("✅ Фото успешно обновлено!")
            await state.clear()
            await admin_panel(message)
    except Exception as e:
        logger.error(f"Ошибка при обновлении фото: user_id={user_id}, error={str(e)}", exc_info=True)
        await message.answer(f"❌ Ошибка обновления фото: {str(e)}")

@router.message(ProductStates.edit_field)
@admin_required
async def save_product_changes(message: Message, state: FSMContext):
    """Сохранение изменений товара"""
    user_id = message.from_user.id if message.from_user else None
    try:
        data = await state.get_data()
        product_id = data.get('product_id')
        field = data.get('field')
        value = message.text.strip()

        logger.info(f"Сохранение изменений товара: user_id={user_id}, product_id={product_id}, field={field}")

        if not product_id or not field:
            logger.error(f"Данные не найдены: user_id={user_id}, product_id={product_id}, field={field}")
            await message.answer("❌ Ошибка: данные не найдены")
            await state.clear()
            return

        async with AsyncSessionLocal() as session:
            product = await session.get(Product, product_id)
            if not product:
                logger.error(f"Товар не найден: user_id={user_id}, product_id={product_id}")
                await message.answer("❌ Товар не найден")
                await state.clear()
                return

            old_value = getattr(product, field, None)
            
            if field == "description" and value == "-":
                value = None
            elif field == "price":
                try:
                    value = float(value.replace(',', '.'))
                    if value <= 0:
                        await message.answer("❌ Цена должна быть больше нуля. Введите снова:")
                        return
                except ValueError:
                    logger.warning(f"Некорректная цена: user_id={user_id}, input={value}")
                    await message.answer("❌ Введите корректную цену (число):")
                    return
            elif field == "name":
                if not value:
                    await message.answer("❌ Название не может быть пустым. Введите снова:")
                    return

            setattr(product, field, value)
            await session.commit()

            logger.info(f"Поле товара успешно обновлено: user_id={user_id}, product_id={product_id}, field={field}, old_value={old_value}, new_value={value}")
            await message.answer(f"✅ {field.capitalize()} успешно обновлено!")
    except Exception as e:
        logger.error(f"Ошибка при сохранении изменений: user_id={user_id}, error={str(e)}", exc_info=True)
        await message.answer("❌ Произошла ошибка при сохранении изменений")
    finally:
        await state.clear()
        await admin_panel(message)

@router.callback_query(F.data == "delete_product_start")
@admin_required
async def delete_product_start(callback: CallbackQuery, state: FSMContext):
    """Начало удаления товара"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Начало удаления товара: user_id={user_id}")
    
    await callback.message.answer("🔍 Введите название товара для удаления:")
    await state.set_state(ProductStates.delete_select)
    await callback.answer()

@router.message(ProductStates.delete_select)
@admin_required
async def find_product_to_delete(message: Message, state: FSMContext):
    """Поиск товара для удаления"""
    user_id = message.from_user.id if message.from_user else None
    search_text = message.text.strip().lower()
    logger.info(f"Поиск товара для удаления: user_id={user_id}, search={search_text}")
    
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
                logger.warning(f"Товар не найден для удаления: user_id={user_id}, search={search_text}")
                await message.answer("❌ Товар не найден. Проверьте название.")
                await state.clear()
                return

            if len(products) == 1:
                product = products[0]
                logger.info(f"Товар найден для удаления: user_id={user_id}, product_id={product.id}")
                await show_product_delete_confirmation(message, state, product)
            else:
                logger.info(f"Найдено несколько товаров: user_id={user_id}, count={len(products)}")
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
        logger.error(f"Ошибка при поиске товара: user_id={user_id}, search={search_text}, error={str(e)}", exc_info=True)
        await message.answer("❌ Произошла ошибка при поиске товара")
        await state.clear()

@router.callback_query(F.data.startswith("select_product_delete_"))
@admin_required
async def handle_product_delete_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора товара для удаления"""
    user_id = callback.from_user.id if callback.from_user else None
    try:
        product_id = int(callback.data.split("_")[3])
        logger.info(f"Выбор товара для удаления: user_id={user_id}, product_id={product_id}")

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
                logger.error(f"Товар не найден: user_id={user_id}, product_id={product_id}")
                await callback.answer("❌ Товар не найден", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка выбора товара: user_id={user_id}, error={str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка при выборе товара", show_alert=True)
    finally:
        await callback.answer()

async def show_product_delete_confirmation(message: Message, state: FSMContext, product: Product):
    """Показать подтверждение удаления товара"""
    user_id = message.from_user.id if message.from_user else None
    logger.debug(f"Показ подтверждения удаления товара: user_id={user_id}, product_id={product.id}")
    
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
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Подтверждение удаления товара: user_id={user_id}")
    
    try:
        data = await state.get_data()
        product_id = data.get('product_id')

        if not product_id:
            logger.error(f"product_id не найден в state: user_id={user_id}")
            await callback.message.answer("❌ Товар не выбран")
            await state.clear()
            return

        async with AsyncSessionLocal() as session:
            product = await session.get(Product, product_id)
            if not product:
                logger.error(f"Товар не найден в БД: user_id={user_id}, product_id={product_id}")
                await callback.message.answer("❌ Товар не найден")
                await state.clear()
                return

            product_name = product.name
            photo_deleted = False
            
            if product.photo_url:
                await delete_photo(product.photo_url)
                photo_deleted = True
                logger.debug(f"Фото товара удалено: user_id={user_id}, photo_url={product.photo_url}")

            await session.delete(product)
            await session.commit()

            logger.info(f"Товар успешно удален: user_id={user_id}, product_id={product_id}, name={product_name}, photo_deleted={photo_deleted}")
            await callback.message.answer(
                f"✅ Товар успешно удалён:\n"
                f"Название: {product_name}\n"
                f"ID: {product_id}"
            )
    except Exception as e:
        logger.error(f"Ошибка при удалении товара: user_id={user_id}, error={str(e)}", exc_info=True)
        await callback.message.answer("❌ Произошла ошибка при удалении товара")
    finally:
        await state.clear()
        await admin_panel(callback.message)
        await callback.answer()

@router.callback_query(ProductStates.delete_confirm, F.data == "cancel_product_delete")
@admin_required
async def cancel_product_delete(callback: CallbackQuery, state: FSMContext):
    """Отмена удаления товара"""
    user_id = callback.from_user.id if callback.from_user else None
    logger.info(f"Отмена удаления товара: user_id={user_id}")
    
    await state.clear()
    await callback.message.answer("❌ Удаление товара отменено")
    await admin_panel(callback.message)
    await callback.answer()
