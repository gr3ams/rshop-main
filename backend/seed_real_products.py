
"""
Скрипт для заполнения базы данных реальными товарами
с реальными названиями, ценами и изображениями
"""
import asyncio
import sys
import io
from sqlalchemy import select
from database import init_db, AsyncSessionLocal
from models import Brand, Category, Product

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


async def clear_existing_data():
    """Очистка существующих данных"""
    async with AsyncSessionLocal() as session:
        try:
            # Удаляем все товары
            products = await session.execute(select(Product))
            for product in products.scalars().all():
                await session.delete(product)
            
            # Удаляем все категории
            categories = await session.execute(select(Category))
            for category in categories.scalars().all():
                await session.delete(category)
            
            # Удаляем все бренды
            brands = await session.execute(select(Brand))
            for brand in brands.scalars().all():
                await session.delete(brand)
            
            await session.commit()
            print("[OK] База данных очищена")
        except Exception as e:
            await session.rollback()
            print(f"[ERROR] Ошибка при очистке: {e}")


async def seed_real_products():
    """Заполнение базы данных реальными товарами"""
    async with AsyncSessionLocal() as session:
        try:
            # Создаем бренды
            brands_data = {
                "Nike": {
                    "categories": {
                        "Кроссовки": [
                            {
                                "name": "Nike Air Max 90",
                                "price": 12999,
                                "description": "Классические кроссовки Nike Air Max 90 с видимой воздушной подушкой",
                                "photo_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "Nike Air Force 1 '07",
                                "price": 10999,
                                "description": "Легендарные белые кроссовки Nike Air Force 1 с классическим дизайном",
                                "photo_url": "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "Nike React Infinity Run Flyknit 3",
                                "price": 15999,
                                "description": "Беговые кроссовки с технологией React для максимальной амортизации",
                                "photo_url": "https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "Nike Dunk Low",
                                "price": 8999,
                                "description": "Баскетбольные кроссовки Nike Dunk Low в ретро стиле",
                                "photo_url": "https://images.unsplash.com/photo-1605348532760-6753d2c43329?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "Nike Zoom Pegasus 39",
                                "price": 13999,
                                "description": "Профессиональные беговые кроссовки для ежедневных тренировок",
                                "photo_url": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=800&h=800&fit=crop"
                            }
                        ],
                        "Одежда": [
                            {
                                "name": "Nike Dri-FIT ADV TechKnit Ultra",
                                "price": 5499,
                                "description": "Спортивная футболка с технологией Dri-FIT для отвода влаги",
                                "photo_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "Nike Sportswear Tech Fleece",
                                "price": 7999,
                                "description": "Толстовка Tech Fleece с современным дизайном и утеплителем",
                                "photo_url": "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "Nike Pro Hyperwarm",
                                "price": 4499,
                                "description": "Термобелье Nike Pro для тренировок в холодную погоду",
                                "photo_url": "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "Nike Windrunner Jacket",
                                "price": 8999,
                                "description": "Легкая ветровка Nike Windrunner с водоотталкивающим покрытием",
                                "photo_url": "https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=800&h=800&fit=crop"
                            }
                        ],
                        "Аксессуары": [
                            {
                                "name": "Nike Gym Sack",
                                "price": 2499,
                                "description": "Спортивная сумка Nike Gym Sack для тренировок",
                                "photo_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "Nike Swoosh Cap",
                                "price": 2999,
                                "description": "Бейсболка Nike с фирменным логотипом Swoosh",
                                "photo_url": "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?w=800&h=800&fit=crop"
                            }
                        ]
                    }
                },
                "Adidas": {
                    "categories": {
                        "Кроссовки": [
                            {
                                "name": "Adidas Ultraboost 22",
                                "price": 16999,
                                "description": "Премиальные беговые кроссовки с технологией Boost",
                                "photo_url": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "Adidas Originals Superstar",
                                "price": 9999,
                                "description": "Классические кроссовки Adidas Superstar с резиновым мыском",
                                "photo_url": "https://images.unsplash.com/photo-1589578527966-fdac0f44566c?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "Adidas NMD R1",
                                "price": 12999,
                                "description": "Стильные кроссовки Adidas NMD с технологией Boost",
                                "photo_url": "https://images.unsplash.com/photo-1605348532760-6753d2c43329?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "Adidas Yeezy Boost 350",
                                "price": 29999,
                                "description": "Легендарные кроссовки Yeezy Boost 350 в коллаборации с Kanye West",
                                "photo_url": "https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=800&h=800&fit=crop"
                            }
                        ],
                        "Одежда": [
                            {
                                "name": "Adidas Tiro 21",
                                "price": 3999,
                                "description": "Футбольные штаны Adidas Tiro 21 с классическими полосками",
                                "photo_url": "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "Adidas Essentials 3-Stripes Tee",
                                "price": 2999,
                                "description": "Базовая футболка Adidas с тремя полосками",
                                "photo_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "Adidas Originals Track Top",
                                "price": 6999,
                                "description": "Куртка Adidas Originals в ретро стиле",
                                "photo_url": "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=800&h=800&fit=crop"
                            }
                        ]
                    }
                },
                "Puma": {
                    "categories": {
                        "Кроссовки": [
                            {
                                "name": "Puma RS-X3",
                                "price": 10999,
                                "description": "Стильные кроссовки Puma RS-X3 с ретро дизайном",
                                "photo_url": "https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "Puma Suede Classic",
                                "price": 7999,
                                "description": "Классические кроссовки Puma Suede из натуральной замши",
                                "photo_url": "https://images.unsplash.com/photo-1605348532760-6753d2c43329?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "Puma Speedcat",
                                "price": 8499,
                                "description": "Беговые кроссовки Puma Speedcat для скоростных тренировок",
                                "photo_url": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=800&h=800&fit=crop"
                            }
                        ],
                        "Одежда": [
                            {
                                "name": "Puma Essentials Logo Tee",
                                "price": 2499,
                                "description": "Базовая футболка Puma с фирменным логотипом",
                                "photo_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "Puma Classics Hoodie",
                                "price": 5999,
                                "description": "Толстовка Puma Classics с капюшоном",
                                "photo_url": "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=800&h=800&fit=crop"
                            }
                        ]
                    }
                },
                "New Balance": {
                    "categories": {
                        "Кроссовки": [
                            {
                                "name": "New Balance 574",
                                "price": 8499,
                                "description": "Классические кроссовки New Balance 574 из натуральной замши",
                                "photo_url": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "New Balance 990v5",
                                "price": 18999,
                                "description": "Премиальные кроссовки New Balance 990v5 Made in USA",
                                "photo_url": "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "New Balance Fresh Foam 1080v12",
                                "price": 14999,
                                "description": "Беговые кроссовки с технологией Fresh Foam для максимального комфорта",
                                "photo_url": "https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=800&h=800&fit=crop"
                            }
                        ],
                        "Одежда": [
                            {
                                "name": "New Balance Athletics Tee",
                                "price": 2999,
                                "description": "Спортивная футболка New Balance для тренировок",
                                "photo_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800&h=800&fit=crop"
                            }
                        ]
                    }
                },
                "Reebok": {
                    "categories": {
                        "Кроссовки": [
                            {
                                "name": "Reebok Classic Leather",
                                "price": 7999,
                                "description": "Классические кроссовки Reebok Classic Leather из натуральной кожи",
                                "photo_url": "https://images.unsplash.com/photo-1605348532760-6753d2c43329?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "Reebok Nano X2",
                                "price": 11999,
                                "description": "Кроссовки Reebok Nano X2 для функциональных тренировок",
                                "photo_url": "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=800&h=800&fit=crop"
                            }
                        ],
                        "Одежда": [
                            {
                                "name": "Reebok Workout Ready Tee",
                                "price": 2799,
                                "description": "Футболка Reebok для интенсивных тренировок",
                                "photo_url": "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=800&h=800&fit=crop"
                            }
                        ]
                    }
                },
                "Under Armour": {
                    "categories": {
                        "Кроссовки": [
                            {
                                "name": "Under Armour HOVR Phantom 3",
                                "price": 14999,
                                "description": "Беговые кроссовки с технологией HOVR для оптимальной амортизации",
                                "photo_url": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "Under Armour Curry 9",
                                "price": 12999,
                                "description": "Баскетбольные кроссовки Under Armour Curry 9",
                                "photo_url": "https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=800&h=800&fit=crop"
                            }
                        ],
                        "Одежда": [
                            {
                                "name": "Under Armour HeatGear Compression",
                                "price": 3999,
                                "description": "Компрессионная футболка HeatGear для интенсивных тренировок",
                                "photo_url": "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=800&h=800&fit=crop"
                            },
                            {
                                "name": "Under Armour Rival Fleece Hoodie",
                                "price": 6499,
                                "description": "Толстовка Under Armour Rival Fleece для тренировок",
                                "photo_url": "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=800&h=800&fit=crop"
                            }
                        ]
                    }
                }
            }
            
            brands = {}
            total_products = 0
            
            # Создаем бренды
            for brand_name in brands_data.keys():
                brand = Brand(name=brand_name)
                session.add(brand)
                await session.flush()
                brands[brand_name] = brand
                print(f"[OK] Создан бренд: {brand_name}")
            
            # Создаем категории и товары
            for brand_name, brand_info in brands_data.items():
                brand = brands[brand_name]
                
                for category_name, products_list in brand_info["categories"].items():
                    # Создаем категорию
                    category = Category(name=category_name, brand_id=brand.id)
                    session.add(category)
                    await session.flush()
                    print(f"  [OK] Создана категория: {category_name} для {brand_name}")
                    
                    # Создаем товары в категории
                    for product_data in products_list:
                        product = Product(
                            name=product_data["name"],
                            price=product_data["price"],
                            description=product_data["description"],
                            photo_url=product_data["photo_url"],
                            category_id=category.id
                        )
                        session.add(product)
                        await session.flush()
                        total_products += 1
                        print(f"    [OK] Товар: {product_data['name']} - {product_data['price']} RUB")
            
            await session.commit()
            print(f"\n[SUCCESS] Успешно добавлено товаров: {total_products}")
            
        except Exception as e:
            await session.rollback()
            print(f"\n[ERROR] Ошибка при заполнении: {e}")
            import traceback
            traceback.print_exc()
            raise


async def show_stats():
    """Показать статистику по базе данных"""
    async with AsyncSessionLocal() as session:
        brands_result = await session.execute(select(Brand))
        brands_count = len(brands_result.scalars().all())
        
        categories_result = await session.execute(select(Category))
        categories_count = len(categories_result.scalars().all())
        
        products_result = await session.execute(select(Product))
        products_count = len(products_result.scalars().all())
        
        print("\n" + "="*60)
        print("СТАТИСТИКА БАЗЫ ДАННЫХ")
        print("="*60)
        print(f"Брендов: {brands_count}")
        print(f"Категорий: {categories_count}")
        print(f"Товаров: {products_count}")
        print("="*60 + "\n")


async def main():
    """Главная функция"""
    print("\n" + "="*60)
    print("ЗАПОЛНЕНИЕ БАЗЫ ДАННЫХ РЕАЛЬНЫМИ ТОВАРАМИ")
    print("="*60 + "\n")
    
    # Инициализируем базу данных
    print("[INIT] Инициализация базы данных...")
    await init_db()
    print()
    
    # Очищаем существующие данные
    print("[CLEAN] Очистка существующих данных...")
    await clear_existing_data()
    print()
    
    # Заполняем реальными товарами
    print("[SEED] Заполнение реальными товарами...")
    await seed_real_products()
    print()
    
    # Показываем статистику
    await show_stats()


if __name__ == "__main__":
    asyncio.run(main())
