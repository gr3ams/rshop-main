
"""
Модуль для отправки уведомлений администраторам через Telegram
"""
import httpx
import logging
from typing import List, Dict, Any
from config import BOT_TOKEN, get_admin_chat_ids
from logging_config import setup_logger, setup_httpx_logging

# Настройка логирования
setup_httpx_logging(logging.DEBUG)
logger = setup_logger(__name__, "telegram_notifications", logging.DEBUG)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def format_order_message(order: Dict[str, Any]) -> str:
    """
    Форматирует сообщение о заказе для отправки администраторам
    
    Args:
        order: Словарь с данными заказа
        
    Returns:
        Отформатированное сообщение в формате HTML
    """
    order_id = order.get("order_id", "N/A")
    user_id = order.get("user_id", "N/A")
    user_name = order.get("user_name", "N/A")
    username = order.get("username")  # Username пользователя в Telegram
    phone = order.get("phone", "N/A")
    address = order.get("address", "N/A")
    comment = order.get("comment", "")
    total = order.get("total", 0)
    items = order.get("items", [])
    
    message = f"""🛒 <b>НОВЫЙ ЗАКАЗ</b>

📋 <b>Номер заказа:</b> {order_id}
👤 <b>Клиент:</b> {user_name}
🆔 <b>ID:</b> {user_id}"""
    
    # Добавляем username, если он есть
    if username:
        message += f"\n👤 <b>Username:</b> @{username}"
    
    message += f"\n📞 <b>Телефон:</b> {phone}\n📍 <b>Адрес:</b> {address}"
    
    if comment:
        message += f"\n💬 <b>Комментарий:</b> {comment}"
    
    message += f"\n\n<b>Состав заказа:</b>\n"
    
    for idx, item in enumerate(items, 1):
        product_name = item.get("product_name", "N/A")
        quantity = item.get("quantity", 0)
        price = item.get("price", 0)
        item_total = quantity * price
        message += f"{idx}. {product_name}\n   Количество: {quantity} × {price:.2f} ₽ = {item_total:.2f} ₽\n"
    
    message += f"\n💰 <b>Итого:</b> {total:.2f} ₽"
    
    return message

def create_order_keyboard(order_id: str) -> Dict[str, Any]:
    """
    Создает inline-клавиатуру с кнопками Подтвердить/Отклонить
    
    Args:
        order_id: ID заказа
        
    Returns:
        Словарь с клавиатурой для Telegram API
    """
    return {
        "inline_keyboard": [
            [
                {
                    "text": "✅ Подтвердить",
                    "callback_data": f"order_confirm_{order_id}"
                },
                {
                    "text": "❌ Отклонить",
                    "callback_data": f"order_reject_{order_id}"
                }
            ]
        ]
    }

async def send_order_notification(order: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Отправляет уведомление о новом заказе всем администраторам
    
    Args:
        order: Словарь с данными заказа
        
    Returns:
        Список результатов отправки (по одному для каждого чата)
    """
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не настроен. Уведомления не будут отправлены.")
        return []
    
    try:
        admin_chat_ids = get_admin_chat_ids()
    except ValueError as e:
        logger.error(str(e))
        return []
    
    if not admin_chat_ids:
        logger.warning("Список администраторов пуст. Уведомления не будут отправлены.")
        return []
    
    message_text = format_order_message(order)
    keyboard = create_order_keyboard(order.get("order_id", ""))
    
    results = []
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for chat_id in admin_chat_ids:
            try:
                response = await client.post(
                    f"{TELEGRAM_API_URL}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": message_text,
                        "parse_mode": "HTML",
                        "reply_markup": keyboard
                    }
                )
                response.raise_for_status()
                result = response.json()
                results.append({
                    "chat_id": chat_id,
                    "success": result.get("ok", False),
                    "message_id": result.get("result", {}).get("message_id") if result.get("ok") else None
                })
                logger.info(f"Уведомление отправлено в чат {chat_id}")
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления в чат {chat_id}: {e}")
                results.append({
                    "chat_id": chat_id,
                    "success": False,
                    "error": str(e)
                })
    
    return results

async def send_user_notification(user_id: int, order_id: str, status: str, order_total: float) -> bool:
    """
    Отправляет уведомление пользователю о статусе его заказа
    
    Args:
        user_id: ID пользователя в Telegram
        order_id: ID заказа
        status: Статус заказа ('confirmed' или 'rejected')
        order_total: Сумма заказа
        
    Returns:
        True если успешно, False в противном случае
    """
    if not BOT_TOKEN:
        logger.warning("BOT_TOKEN не настроен. Уведомление пользователю не будет отправлено.")
        return False
    
    try:
        if status == "confirmed":
            message_text = f"""✅ <b>Ваш заказ подтвержден!</b>

📋 <b>Номер заказа:</b> {order_id}
💰 <b>Сумма:</b> {order_total:.2f} ₽

Спасибо за заказ! Мы свяжемся с вами в ближайшее время для уточнения деталей доставки."""
        elif status == "rejected":
            message_text = f"""❌ <b>Ваш заказ отклонен</b>

📋 <b>Номер заказа:</b> {order_id}
💰 <b>Сумма:</b> {order_total:.2f} ₽

К сожалению, ваш заказ был отклонен. Если у вас есть вопросы, свяжитесь с поддержкой."""
        else:
            logger.warning(f"Unknown status for user notification: {status}")
            return False
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{TELEGRAM_API_URL}/sendMessage",
                json={
                    "chat_id": user_id,
                    "text": message_text,
                    "parse_mode": "HTML"
                }
            )
            response.raise_for_status()
            result = response.json()
            if result.get("ok", False):
                logger.info(f"User notification sent to user {user_id} for order {order_id}")
                return True
            else:
                logger.error(f"Failed to send user notification: {result}")
                return False
    except httpx.HTTPStatusError as e:
        # Если пользователь заблокировал бота или чат не найден
        if e.response.status_code == 403:
            logger.warning(f"User {user_id} blocked the bot or chat not found")
        else:
            logger.error(f"HTTP error sending user notification: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending user notification: {e}")
        return False

async def edit_order_message(chat_id: int, message_id: int, new_text: str, order_id: str) -> bool:
    """
    Обновляет сообщение о заказе после обработки администратором
    
    Args:
        chat_id: ID чата
        message_id: ID сообщения
        new_text: Новый текст сообщения
        order_id: ID заказа
        
    Returns:
        True если успешно, False в противном случае
    """
    if not BOT_TOKEN:
        return False
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{TELEGRAM_API_URL}/editMessageText",
                json={
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": new_text,
                    "parse_mode": "HTML"
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get("ok", False)
    except Exception as e:
        logger.error(f"Ошибка при обновлении сообщения: {e}")
        return False

