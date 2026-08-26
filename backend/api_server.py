from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import Brand, Category, Product, Order, OrderItem as OrderItemModel, OrderStatus, OrderActionLog
from database import AsyncSessionLocal, init_db
import uvicorn
from typing import List, Optional
from pydantic import BaseModel
import os
from datetime import datetime
import logging
from telegram_notifications import send_order_notification
from logging_config import setup_logger, setup_sqlalchemy_logging

# Настройка логирования с уровнем DEBUG
setup_sqlalchemy_logging(logging.DEBUG)
logger = setup_logger(__name__, "api_server", logging.DEBUG)

app = FastAPI(title="TG Shop API", version="1.0.0")

# CORS middleware для локальной разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "https://rshop1.ru",
        "*"  # Разрешаем все источники для Cloudflare Tunnel
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем статические файлы (будет настроено после инициализации STATIC_ROOT)
# app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")

# Pydantic модели для API
class BrandResponse(BaseModel):
    id: int
    name: str
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

class CategoryResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    photo_url: Optional[str] = None
    description: Optional[str] = None
    category_id: int

    class Config:
        from_attributes = True

class OrderItemCreate(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    price: float

class OrderCreate(BaseModel):
    user_id: int
    user_name: str
    username: Optional[str] = None  # Username пользователя в Telegram
    phone: str
    address: str
    comment: Optional[str] = None
    items: List[OrderItemCreate]
    total: float

class OrderResponse(BaseModel):
    success: bool
    order_id: str
    message: str

class OrderStatusResponse(BaseModel):
    status: str

class OrderItemResponse(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    price: float

    class Config:
        from_attributes = True

class OrderDetailResponse(BaseModel):
    id: int
    order_id: str
    user_id: int
    user_name: str
    phone: str
    address: str
    comment: Optional[str]
    total: float
    status: str
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True

class UserStatsResponse(BaseModel):
    user_id: int
    orders_count: int
    total_spent: float

class BankDetails(BaseModel):
    accountNumber: str
    bankName: str
    recipientName: str

class PaymentDetailsResponse(BaseModel):
    orderId: str
    amount: float
    paymentInfo: str
    bankDetails: Optional[BankDetails] = None

class PaymentConfirmRequest(BaseModel):
    orderId: str

class PaymentCancelRequest(BaseModel):
    orderId: str

class AdminDataResponse(BaseModel):
    brands: List[BrandResponse]
    categories: List[CategoryResponse]

# Dependency для получения сессии БД
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

# Директория для сохранения статических файлов
from pathlib import Path

BACKEND_DIR = Path(__file__).parent
STATIC_ROOT = Path(os.environ.get("STATIC_ROOT", BACKEND_DIR / "static"))
STATIC_ROOT.mkdir(exist_ok=True)

def _ensure_static_dir(subdir: str = "products") -> Path:
    target_dir = STATIC_ROOT / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir

async def _save_upload_to_static(upload: UploadFile, subdir: str = "products") -> str:
    """Сохраняет файл в STATIC_ROOT/subdir и возвращает web-путь '/static/subdir/filename'."""
    target_dir = _ensure_static_dir(subdir)
    base_name = os.path.basename(upload.filename or "file")
    name, ext = os.path.splitext(base_name)
    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
    safe_name = f"{name}_{ts}{ext or ''}"
    disk_path = target_dir / safe_name

    try:
        contents = await upload.read()
        with open(disk_path, "wb") as f:
            f.write(contents)
    finally:
        await upload.close()

    return f"/static/{subdir}/{safe_name}"

# Health check endpoint
@app.get("/")
async def root():
    return {"status": "ok", "message": "TG Shop API is running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Brands endpoints
@app.get("/api/brands", response_model=List[BrandResponse])
async def get_brands(db: AsyncSession = Depends(get_db)):
    """Получить список всех брендов"""
    try:
        result = await db.execute(select(Brand).order_by(Brand.name))
        brands = result.scalars().all()
        logger.info(f"Found {len(brands)} brands")
        return brands
    except Exception as e:
        logger.error(f"Error fetching brands: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching brands: {str(e)}")

@app.get("/api/brands/{category_id}", response_model=List[BrandResponse])
async def get_brands_by_category(category_id: int, db: AsyncSession = Depends(get_db)):
    """Получить бренды для конкретной категории (через продукты)"""
    try:
        # Проверяем существование категории
        category_result = await db.execute(select(Category).where(Category.id == category_id))
        category = category_result.scalar_one_or_none()
        
        if not category:
            raise HTTPException(status_code=404, detail=f"Category with id {category_id} not found")
        
        # Получаем уникальные бренды через продукты этой категории
        result = await db.execute(
            select(Brand)
            .join(Product, Brand.id == Product.brand_id)
            .where(Product.category_id == category_id)
            .distinct()
        )
        brands = result.scalars().all()
        
        logger.info(f"Found {len(brands)} brands for category {category_id}")
        return brands
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching brands for category: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching brands for category: {str(e)}")

# Categories endpoints
@app.get("/api/categories", response_model=List[CategoryResponse])
async def get_all_categories(db: AsyncSession = Depends(get_db)):
    """Получить список всех категорий"""
    try:
        result = await db.execute(select(Category).order_by(Category.name))
        categories = result.scalars().all()
        logger.info(f"Found {len(categories)} categories")
        return categories
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")

@app.get("/api/categories/{brand_id}", response_model=List[CategoryResponse])
async def get_categories_by_brand(brand_id: int, db: AsyncSession = Depends(get_db)):
    """Получить категории для конкретного бренда (через продукты)"""
    try:
        # Проверяем существование бренда
        brand_result = await db.execute(select(Brand).where(Brand.id == brand_id))
        brand = brand_result.scalar_one_or_none()
        
        if not brand:
            raise HTTPException(status_code=404, detail=f"Brand with id {brand_id} not found")
        
        # Получаем уникальные категории через продукты этого бренда
        result = await db.execute(
            select(Category)
            .join(Product, Category.id == Product.category_id)
            .where(Product.brand_id == brand_id)
            .distinct()
            .order_by(Category.name)
        )
        categories = result.scalars().all()
        logger.info(f"Found {len(categories)} categories for brand {brand_id}")
        return categories
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")

# Products endpoints
@app.get("/api/products", response_model=List[ProductResponse])
async def get_all_products(db: AsyncSession = Depends(get_db)):
    """Получить список всех товаров"""
    try:
        result = await db.execute(select(Product).order_by(Product.name))
        products = result.scalars().all()
        logger.info(f"Found {len(products)} products")
        return products
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

@app.get("/api/products/{category_id}", response_model=List[ProductResponse])
async def get_products(category_id: int, db: AsyncSession = Depends(get_db)):
    """Получить товары для конкретной категории"""
    try:
        # Проверяем существование категории
        category_result = await db.execute(select(Category).where(Category.id == category_id))
        category = category_result.scalar_one_or_none()
        
        if not category:
            raise HTTPException(status_code=404, detail=f"Category with id {category_id} not found")
        
        # Получаем товары
        result = await db.execute(
            select(Product)
            .where(Product.category_id == category_id)
            .order_by(Product.name)
        )
        products = result.scalars().all()
        logger.info(f"Found {len(products)} products for category {category_id}")
        return products
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

# Orders endpoints
@app.post("/api/orders/create", response_model=OrderResponse)
async def create_order(order: OrderCreate, db: AsyncSession = Depends(get_db)):
    """Создать новый заказ"""
    try:
        # Валидация входных данных
        if not order.user_id or order.user_id <= 0:
            logger.warning(f"Invalid user_id: {order.user_id}")
            raise HTTPException(status_code=400, detail="Invalid user_id")
        
        if not order.items or len(order.items) == 0:
            logger.warning("Order has no items")
            raise HTTPException(status_code=400, detail="Order must have at least one item")
        
        if order.total <= 0:
            logger.warning(f"Invalid total: {order.total}")
            raise HTTPException(status_code=400, detail="Order total must be greater than 0")
        
        # Генерируем уникальный ID заказа: ORD-ДДММ-ХХ-YYY
        # Где ДДММ - день и месяц, ХХ - номер заказа за день, YYY - последние 3 цифры user_id
        now = datetime.now()
        date_str = now.strftime('%d%m')
        
        # Подсчитываем количество заказов этого пользователя за сегодня для уникальности
        today_start = datetime(now.year, now.month, now.day)
        orders_today_result = await db.execute(
            select(func.count(Order.id)).where(
                Order.created_at >= today_start
            )
        )
        orders_today = orders_today_result.scalar() or 0

        user_suffix = str(order.user_id)[-3:].zfill(3)
        attempt = 0
        order_id = ""

        while True:
            order_num = str(orders_today + 1 + attempt).zfill(2)
            order_id = f"ORD-{date_str}-{order_num}-{user_suffix}"
            existing = await db.execute(select(Order.id).where(Order.order_id == order_id))
            if not existing.scalar_one_or_none():
                break
            attempt += 1
        
        logger.info(f"Creating order: {order_id} for user {order.user_name} (id: {order.user_id})")
        logger.info(f"Order details: {len(order.items)} items, total: {order.total}")
        
        # Создаем заказ в БД
        new_order = Order(
            order_id=order_id,
            user_id=order.user_id,
            user_name=order.user_name,
            phone=order.phone,
            address=order.address,
            comment=order.comment,
            total=order.total,
            status=OrderStatus.PENDING.value
        )
        
        db.add(new_order)
        await db.flush()  # Получаем ID заказа
        
        # Добавляем товары заказа
        for item in order.items:
            if not item.product_id or item.quantity <= 0 or item.price <= 0:
                logger.warning(f"Invalid item: {item}")
                raise HTTPException(status_code=400, detail=f"Invalid item data: product_id={item.product_id}, quantity={item.quantity}, price={item.price}")
            
            order_item = OrderItemModel(
                order_id=new_order.id,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                price=item.price
            )
            db.add(order_item)
        
        await db.commit()
        await db.refresh(new_order)
        
        logger.info(f"Order {order_id} saved to database with ID {new_order.id}")
        
        # Подготавливаем данные для уведомления
        order_data = {
            "order_id": order_id,
            "user_id": order.user_id,
            "user_name": order.user_name,
            "username": order.username,  # Username пользователя в Telegram
            "phone": order.phone,
            "address": order.address,
            "comment": order.comment,
            "total": order.total,
            "items": [
                {
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "price": item.price
                }
                for item in order.items
            ]
        }
        
        # Отправляем уведомления администраторам
        try:
            notification_results = await send_order_notification(order_data)
            logger.info(f"Notifications sent: {len([r for r in notification_results if r.get('success')])} successful")
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
            # Не прерываем создание заказа, если уведомления не отправились
        
        return OrderResponse(
            success=True,
            order_id=order_id,
            message="Заказ успешно создан и отправлен в обработку"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating order: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")

@app.get("/api/orders/{order_id}/status", response_model=OrderStatusResponse)
async def get_order_status(order_id: str, db: AsyncSession = Depends(get_db)):
    """Получить статус заказа"""
    try:
        result = await db.execute(
            select(Order).where(Order.order_id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return OrderStatusResponse(status=order.status)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order status: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching order status: {str(e)}")

@app.get("/api/orders/{order_id}", response_model=OrderDetailResponse)
async def get_order_detail(order_id: str, db: AsyncSession = Depends(get_db)):
    """Получить детальную информацию о заказе"""
    try:
        result = await db.execute(
            select(Order).where(Order.order_id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Получаем товары заказа
        items_result = await db.execute(
            select(OrderItemModel).where(OrderItemModel.order_id == order.id)
        )
        items = items_result.scalars().all()
        
        return OrderDetailResponse(
            id=order.id,
            order_id=order.order_id,
            user_id=order.user_id,
            user_name=order.user_name,
            phone=order.phone,
            address=order.address,
            comment=order.comment,
            total=order.total,
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at,
            items=[
                OrderItemResponse(
                    product_id=item.product_id,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    price=item.price
                )
                for item in items
            ]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order detail: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching order detail: {str(e)}")

@app.get("/api/orders/user/{user_id}", response_model=List[OrderDetailResponse])
async def get_user_orders(user_id: int, db: AsyncSession = Depends(get_db)):
    """Получить историю заказов пользователя"""
    try:
        result = await db.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )
        orders = result.scalars().all()
        
        orders_with_items = []
        for order in orders:
            # Получаем товары для каждого заказа
            items_result = await db.execute(
                select(OrderItemModel).where(OrderItemModel.order_id == order.id)
            )
            items = items_result.scalars().all()
            
            orders_with_items.append(
                OrderDetailResponse(
                    id=order.id,
                    order_id=order.order_id,
                    user_id=order.user_id,
                    user_name=order.user_name,
                    phone=order.phone,
                    address=order.address,
                    comment=order.comment,
                    total=order.total,
                    status=order.status,
                    created_at=order.created_at,
                    updated_at=order.updated_at,
                    items=[
                        OrderItemResponse(
                            product_id=item.product_id,
                            product_name=item.product_name,
                            quantity=item.quantity,
                            price=item.price
                        )
                        for item in items
                    ]
                )
            )
        
        return orders_with_items
    except Exception as e:
        logger.error(f"Error fetching user orders: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching user orders: {str(e)}")

@app.get("/api/user/{user_id}/stats", response_model=UserStatsResponse)
async def get_user_stats(user_id: int, db: AsyncSession = Depends(get_db)):
    """Получить статистику пользователя (количество заказов, общая сумма)"""
    try:
        # Считаем статистику только по подтвержденным заказам.
        # Отклоненные и ожидающие заказы не должны попадать в "Потрачено".
        result = await db.execute(
            select(
                func.count(Order.id).label('orders_count'),
                func.coalesce(func.sum(Order.total), 0).label('total_spent')
            ).where(
                Order.user_id == user_id,
                Order.status == OrderStatus.CONFIRMED.value
            )
        )
        stats = result.first()
        
        return UserStatsResponse(
            user_id=user_id,
            orders_count=stats.orders_count or 0,
            total_spent=float(stats.total_spent or 0)
        )
    except Exception as e:
        logger.error(f"Error fetching user stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching user stats: {str(e)}")

# Admin endpoints
@app.get("/api/admin/data", response_model=AdminDataResponse)
async def get_admin_data(db: AsyncSession = Depends(get_db)):
    """Получить данные для админ-панели"""
    try:
        # Получаем бренды
        brands_result = await db.execute(select(Brand).order_by(Brand.name))
        brands = brands_result.scalars().all()
        
        # Получаем категории
        categories_result = await db.execute(select(Category).order_by(Category.name))
        categories = categories_result.scalars().all()
        
        logger.info(f"Admin data: {len(brands)} brands, {len(categories)} categories")
        
        return AdminDataResponse(
            brands=brands,
            categories=categories
        )
    except Exception as e:
        logger.error(f"Error fetching admin data: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching admin data: {str(e)}")

@app.post("/api/admin/add_product")
async def add_product(
    name: str = Form(...),
    price: float = Form(...),
    description: str = Form(None),
    category_id: int = Form(...),
    brand_id: int = Form(...),  # Теперь brand_id обязателен
    photo: UploadFile = File(None),
    db: AsyncSession = Depends(get_db)
):
    """Добавить новый товар"""
    try:
        # Проверяем существование категории
        category_result = await db.execute(select(Category).where(Category.id == category_id))
        category = category_result.scalar_one_or_none()
        
        if not category:
            raise HTTPException(status_code=404, detail=f"Category with id {category_id} not found")
        
        # Обрабатываем фото если есть
        photo_url = None
        if photo:
            try:
                photo_url = await _save_upload_to_static(photo, subdir="products")
                logger.info(f"Photo saved to {photo_url}")
            except Exception as e:
                logger.error(f"Error saving photo: {e}")
                raise HTTPException(status_code=500, detail="Error saving uploaded photo")
        
        # Проверяем существование бренда
        brand_result = await db.execute(select(Brand).where(Brand.id == brand_id))
        brand = brand_result.scalar_one_or_none()
        
        if not brand:
            raise HTTPException(status_code=404, detail=f"Brand with id {brand_id} not found")
        
        # Создаем новый товар
        new_product = Product(
            name=name,
            price=price,
            description=description,
            category_id=category_id,
            brand_id=brand_id,
            photo_url=photo_url
        )
        
        db.add(new_product)
        await db.commit()
        await db.refresh(new_product)
        
        logger.info(f"Product added: {new_product.id} - {new_product.name}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Товар '{name}' успешно добавлен",
                "product_id": new_product.id,
                "photo_url": new_product.photo_url
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding product: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding product: {str(e)}")

# ========================
# Admin: Доп. эндпоинты
# ========================

@app.post("/api/admin/add_brand")
async def add_brand(name: str = Form(...), db: AsyncSession = Depends(get_db)):
    try:
        existing = await db.execute(select(Brand).where(Brand.name.ilike(name)))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Бренд '{name}' уже существует")

        brand = Brand(name=name)
        db.add(brand)
        await db.commit()
        await db.refresh(brand)
        return {"success": True, "message": "Бренд добавлен", "brand_id": brand.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding brand: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при добавлении бренда")


@app.post("/api/admin/add_category")
async def add_category(name: str = Form(...), db: AsyncSession = Depends(get_db)):
    try:
        # Проверяем, существует ли категория с таким именем
        existing = await db.execute(
            select(Category).where(Category.name.ilike(name))
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Категория с таким названием уже существует")

        category = Category(name=name)
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return {"success": True, "message": "Категория добавлена", "category_id": category.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding category: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при добавлении категории")


@app.post("/api/admin/edit_product")
async def edit_product(
    product_id: int = Form(...),
    name: str = Form(None),
    price: float = Form(None),
    description: str = Form(None),
    category_id: int = Form(None),
    photo: UploadFile = File(None),
    db: AsyncSession = Depends(get_db)
):
    try:
        product = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")

        if category_id is not None:
            category = (await db.execute(select(Category).where(Category.id == category_id))).scalar_one_or_none()
            if not category:
                raise HTTPException(status_code=404, detail="Категория не найдена")
            product.category_id = category_id

        if name is not None:
            product.name = name
        if price is not None:
            product.price = price
        if description is not None:
            product.description = description

        if photo is not None:
            try:
                new_photo_url = await _save_upload_to_static(photo, subdir="products")
                product.photo_url = new_photo_url
            except Exception as e:
                logger.error(f"Error saving new photo: {e}")
                raise HTTPException(status_code=500, detail="Ошибка сохранения фото")

        await db.commit()
        await db.refresh(product)
        return {"success": True, "message": "Товар обновлен", "product_id": product.id, "photo_url": product.photo_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error editing product: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при редактировании товара")


@app.post("/api/admin/delete_product")
async def delete_product(product_id: int = Form(...), db: AsyncSession = Depends(get_db)):
    try:
        product = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")

        await db.delete(product)
        await db.commit()
        return {"success": True, "message": "Товар удален", "product_id": product_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при удалении товара")

# Payment endpoints
@app.get("/api/payment/details", response_model=PaymentDetailsResponse)
async def get_payment_details(orderId: str, db: AsyncSession = Depends(get_db)):
    """Получить данные для оплаты заказа"""
    try:
        logger.info(f"Fetching payment details for orderId: {orderId}")
        
        result = await db.execute(
            select(Order).where(Order.order_id == orderId)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            logger.warning(f"Order not found: {orderId}")
            raise HTTPException(status_code=404, detail=f"Order not found: {orderId}")
        
        logger.info(f"Found order {order.order_id} with total {order.total}")
        
        # Генерируем данные для оплаты
        # В реальном приложении здесь должна быть интеграция с платежной системой
        payment_info = f"Оплата заказа {order.order_id}\nСумма: {order.total} ₽\n\nПосле оплаты пришлите скриншот в поддержку."
        
        # Опционально можно добавить банковские реквизиты
        bank_details = BankDetails(
            accountNumber="40817810099910004312",
            bankName="Тинькофф Банк",
            recipientName="ИП Иванов Иван Иванович"
        )
        
        return PaymentDetailsResponse(
            orderId=order.order_id,
            amount=order.total,
            paymentInfo=payment_info,
            bankDetails=bank_details
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching payment details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching payment details: {str(e)}")

@app.post("/api/payment/confirm")
async def confirm_payment(request: PaymentConfirmRequest, db: AsyncSession = Depends(get_db)):
    """Подтвердить оплату заказа (используется только админами через бота)"""
    try:
        result = await db.execute(
            select(Order).where(Order.order_id == request.orderId)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Эта функция используется только админами для подтверждения заказа
        # При нажатии "Я оплатил" пользователем заказ создается со статусом PENDING
        # и подтверждается позже админом в чате
        order.status = OrderStatus.CONFIRMED.value
        await db.commit()
        
        logger.info(f"Payment confirmed for order {request.orderId} by admin")
        return {"success": True, "message": "Payment confirmed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming payment: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error confirming payment: {str(e)}")

@app.post("/api/payment/cancel")
async def cancel_order(request: PaymentCancelRequest, db: AsyncSession = Depends(get_db)):
    """Отменить заказ"""
    try:
        result = await db.execute(
            select(Order).where(Order.order_id == request.orderId)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Отменяем заказ
        order.status = OrderStatus.REJECTED.value
        await db.commit()
        
        logger.info(f"Order {request.orderId} cancelled")
        return {"success": True, "message": "Order cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error cancelling order: {str(e)}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    logger.info("Starting TG Shop API server...")
    try:
        # Монтируем статические файлы
        app.mount("/static", StaticFiles(directory=str(STATIC_ROOT)), name="static")
        logger.info(f"Static files mounted from: {STATIC_ROOT}")
        
        # Инициализируем базу данных
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
