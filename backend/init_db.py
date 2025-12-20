
"""
Скрипт для инициализации базы данных и заполнения тестовыми данными
"""
import asyncio
from sqlalchemy import select
from database import init_db, AsyncSessionLocal
from models import Brand, Category, Product


async def clear_database():
    """Очистка всех данных из базы данных"""
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
            print("+ Database cleared")
        except Exception as e:
            await session.rollback()
            print(f"- Error clearing database: {e}")
            raise


async def seed_test_data():
    """Заполнение базы данных тестовыми данными"""
    async with AsyncSessionLocal() as session:
        try:
            # Создаем бренды
            brands_data = [
                "Nike",
                "Adidas",
                "Puma",
                "Reebok",
                "New Balance",
                "Under Armour"
            ]
            
            brands = {}
            for brand_name in brands_data:
                brand = Brand(name=brand_name)
                session.add(brand)
                await session.flush()
                brands[brand_name] = brand
                print(f"+ Created brand: {brand_name} (ID: {brand.id})")
            
            # Создаем категории (теперь независимые, уникальные по имени)
            all_category_names = set()
            categories_data = {
                "Nike": ["Кроссовки", "Одежда", "Аксессуары"],
                "Adidas": ["Обувь", "Спортивная одежда", "Сумки"],
                "Puma": ["Кроссовки", "Футболки", "Куртки"],
                "Reebok": ["Беговые кроссовки", "Фитнес одежда"],
                "New Balance": ["Кроссовки", "Одежда"],
                "Under Armour": ["Спортивная обувь", "Компрессионная одежда"]
            }
            
            # Собираем все уникальные названия категорий
            for cats in categories_data.values():
                all_category_names.update(cats)
            
            # Создаем категории (уникальные по имени)
            categories_map = {}
            for cat_name in sorted(all_category_names):
                category = Category(name=cat_name)
                session.add(category)
                await session.flush()
                categories_map[cat_name] = category
                print(f"  + Created category: {cat_name} (ID: {category.id})")
            
            # Создаем маппинг для обратной совместимости со старым кодом
            categories = {}
            for brand_name, cats in categories_data.items():
                categories[brand_name] = {}
                for cat_name in cats:
                    categories[brand_name][cat_name] = categories_map[cat_name]
            
            # Создаем товары
            products_data = [
                # Nike
                ("Nike", "Кроссовки", "Nike Air Max 90", 12999, "Классические кроссовки Nike Air Max 90 с воздушной подушкой", "https://cdn-icons-png.flaticon.com/512/2331/2331966.png"),
                ("Nike", "Кроссовки", "Nike React Infinity", 14999, "Беговые кроссовки с технологией React", "https://cdn-icons-png.flaticon.com/512/2331/2331966.png"),
                ("Nike", "Одежда", "Nike Pro Top", 3499, "Компрессионная футболка Nike Pro", "https://cdn-icons-png.flaticon.com/512/892/892458.png"),
                ("Nike", "Одежда", "Nike Sportswear Hoodie", 5999, "Толстовка с капюшоном", "https://cdn-icons-png.flaticon.com/512/2755/2755043.png"),
                ("Nike", "Аксессуары", "Nike Gym Bag", 2999, "Спортивная сумка", "https://cdn-icons-png.flaticon.com/512/2153/2153788.png"),
                
                # Adidas
                ("Adidas", "Обувь", "Adidas Ultraboost 22", 16999, "Премиальные беговые кроссовки", "https://cdn-icons-png.flaticon.com/512/2331/2331966.png"),
                ("Adidas", "Обувь", "Adidas Stan Smith", 8999, "Классические кроссовки Stan Smith", "https://cdn-icons-png.flaticon.com/512/2331/2331966.png"),
                ("Adidas", "Спортивная одежда", "Adidas Training Tee", 2999, "Тренировочная футболка", "https://cdn-icons-png.flaticon.com/512/892/892458.png"),
                ("Adidas", "Спортивная одежда", "Adidas Track Pants", 4999, "Спортивные брюки", "https://cdn-icons-png.flaticon.com/512/3429/3429557.png"),
                ("Adidas", "Сумки", "Adidas Duffel Bag", 3499, "Спортивная сумка-дафл", "https://cdn-icons-png.flaticon.com/512/2153/2153788.png"),
                
                # Puma
                ("Puma", "Кроссовки", "Puma RS-X", 9999, "Ретро кроссовки RS-X", "https://cdn-icons-png.flaticon.com/512/2331/2331966.png"),
                ("Puma", "Футболки", "Puma Essential Tee", 1999, "Базовая футболка", "https://cdn-icons-png.flaticon.com/512/892/892458.png"),
                ("Puma", "Куртки", "Puma Windbreaker", 6999, "Ветровка с капюшоном", "https://cdn-icons-png.flaticon.com/512/3429/3429557.png"),
                
                # Reebok
                ("Reebok", "Беговые кроссовки", "Reebok Floatride", 11999, "Легкие беговые кроссовки", "https://cdn-icons-png.flaticon.com/512/2331/2331966.png"),
                ("Reebok", "Фитнес одежда", "Reebok Workout Top", 3299, "Топ для тренировок", "https://cdn-icons-png.flaticon.com/512/892/892458.png"),
                
                # New Balance
                ("New Balance", "Кроссовки", "New Balance 574", 8499, "Классика New Balance 574", "https://cdn-icons-png.flaticon.com/512/2331/2331966.png"),
                ("New Balance", "Кроссовки", "New Balance Fresh Foam", 13499, "Кроссовки с технологией Fresh Foam", "https://cdn-icons-png.flaticon.com/512/2331/2331966.png"),
                ("New Balance", "Одежда", "New Balance Athletics Tee", 2799, "Спортивная футболка", "https://cdn-icons-png.flaticon.com/512/892/892458.png"),
                
                # Under Armour
                ("Under Armour", "Спортивная обувь", "UA HOVR Phantom", 14999, "Кроссовки с технологией HOVR", "https://cdn-icons-png.flaticon.com/512/2331/2331966.png"),
                ("Under Armour", "Компрессионная одежда", "UA HeatGear Compression", 3999, "Компрессионная футболка HeatGear", "https://cdn-icons-png.flaticon.com/512/892/892458.png"),
            ]
            
            for brand_name, cat_name, prod_name, price, desc, photo in products_data:
                category = categories[brand_name][cat_name]
                brand = brands[brand_name]
                product = Product(
                    name=prod_name,
                    price=price,
                    description=desc,
                    photo_url=photo,
                    category_id=category.id,
                    brand_id=brand.id
                )
                session.add(product)
                await session.flush()
                print(f"    + Created product: {prod_name} (ID: {product.id}) - {price} RUB")
            
            await session.commit()
            print("\n+ All test data successfully added!")
            
        except Exception as e:
            await session.rollback()
            print(f"\n- Error seeding data: {e}")
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
        
        print("\n" + "="*50)
        print("DATABASE STATISTICS")
        print("="*50)
        print(f"Брендов: {brands_count}")
        print(f"Категорий: {categories_count}")
        print(f"Товаров: {products_count}")
        print("="*50 + "\n")


async def main():
    """Главная функция"""
    print("\n" + "="*50)
    print("INITIALIZATION OF DATABASE")
    print("="*50 + "\n")
    
    # Инициализируем базу данных (создаем таблицы)
    print("Creating tables...")
    await init_db()
    print()
    
    # Очищаем существующие данные
    print("Clearing existing data...")
    await clear_database()
    print()
    
    # Заполняем тестовыми данными
    print("Seeding test data...")
    await seed_test_data()
    
    # Показываем статистику
    await show_stats()


if __name__ == "__main__":
    asyncio.run(main())

