
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

# Импорты из вашего проекта
from admin import router as admin_router  # Модульный admin из admin/
from order_handlers import order_router
from database import init_db
from logging_config import setup_logger, setup_aiogram_logging

# Настройка логирования
setup_aiogram_logging(logging.DEBUG)
logger = setup_logger(__name__, "telegram_bot", logging.DEBUG)

load_dotenv()

async def on_startup():
    """Действия при запуске бота"""
    logger.info("Запуск инициализации базы данных...")
    await init_db()
    logger.info("База данных готова к работе")

async def main():
    # Инициализация бота
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher()
    
    # Включаем роутеры
    dp.include_router(admin_router)
    dp.include_router(order_router)
    
    # Обработчик команды /start
    @dp.message(Command("start"))
    async def start(message: types.Message):
        user = message.from_user
        username = user.username if user else None
        
        # Проверяем наличие username
        if not username:
            # Если username нет, просим его поставить
            no_username_text = """
🖤 *RShop — премиальная брендовая одежда*

Для доступа к магазину необходимо установить username в Telegram.

📝 *Как установить username:*
1. Откройте настройки Telegram
2. Перейдите в "Имя пользователя" (Username)
3. Установите ваш username
4. После этого отправьте команду /start снова

После установки username вы сможете открыть каталог товаров.
            """
            await message.answer(
                no_username_text,
                parse_mode="Markdown"
            )
            return
        
        # Если username есть, отправляем ссылку на мини-приложение
        mini_app_url = "https://code-filter-header-oral.trycloudflare.com"

        welcome_text = f"""
🖤 *RShop — премиальная брендовая одежда*

Добро пожаловать в мир элегантности и стиля. 

В нашем каталоге только отборные коллекции ведущих брендов.

Откройте мини-приложение через кнопку, которую вы настроили в BotFather,
или перейдите по ссылке: [🌟 ОТКРЫТЬ КАТАЛОГ]({mini_app_url})
        """
    
        await message.answer(
            welcome_text,
            parse_mode="Markdown"
        )
    
    # Запускаем бота
    await on_startup()
    logger.info("Бот готов к работе, запускаем polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Остановка бота...")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)