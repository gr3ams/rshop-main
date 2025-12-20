
"""
Обработчики для работы с заказами через Telegram бота
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select
from database import AsyncSessionLocal
from models import Order, OrderStatus, OrderActionLog
from telegram_notifications import edit_order_message, send_user_notification
from logging_config import setup_logger

logger = setup_logger(__name__, "order_handlers", logging.DEBUG)

# Создаем роутер для обработки заказов
order_router = Router()

@order_router.callback_query(F.data.startswith("order_"))
async def handle_order_callback(callback: CallbackQuery):
    """
    Обработчик callback-запросов для кнопок Подтвердить/Отклонить
    """
    try:
        # Парсим callback_data
        # Формат: "order_confirm_ORDER_20231201120000_123" или "order_reject_ORDER_20231201120000_123"
        data_parts = callback.data.split("_")
        if len(data_parts) < 3:
            await callback.answer("Ошибка: некорректные данные", show_alert=True)
            return
        
        action = data_parts[1]  # "confirm" или "reject"
        order_id = "_".join(data_parts[2:])  # Остальная часть - это order_id
        
        if action not in ["confirm", "reject"]:
            await callback.answer("Ошибка: неизвестное действие", show_alert=True)
            return
        
        # Получаем информацию об администраторе
        admin_id = callback.from_user.id
        admin_name = callback.from_user.full_name or callback.from_user.username or "Unknown"
        
        # Работаем с базой данных
        async with AsyncSessionLocal() as db:
            # Находим заказ
            result = await db.execute(
                select(Order).where(Order.order_id == order_id)
            )
            order = result.scalar_one_or_none()
            
            if not order:
                await callback.answer("Заказ не найден", show_alert=True)
                return
            
            # Проверяем, не обработан ли уже заказ
            if order.status != OrderStatus.PENDING.value:
                status_text = "подтвержден" if order.status == OrderStatus.CONFIRMED.value else "отклонен"
                await callback.answer(f"Заказ уже {status_text}", show_alert=True)
                return
            
            # Обновляем статус заказа
            if action == "confirm":
                order.status = OrderStatus.CONFIRMED.value
                status_text = "✅ ПОДТВЕРЖДЕН"
                action_text = "подтвержден"
            else:
                order.status = OrderStatus.REJECTED.value
                status_text = "❌ ОТКЛОНЕН"
                action_text = "отклонен"
            
            # Сохраняем изменение
            await db.commit()
            await db.refresh(order)
            
            # Логируем действие администратора
            action_log = OrderActionLog(
                order_id=order.id,
                admin_id=admin_id,
                admin_name=admin_name,
                action=action
            )
            db.add(action_log)
            await db.commit()
            
            logger.info(
                f"Order {order_id} {action_text} by admin {admin_name} (ID: {admin_id})"
            )
        
        # Обновляем сообщение в Telegram
        from datetime import datetime
        current_time = datetime.now().strftime('%d.%m.%Y %H:%M')
        
        new_message_text = f"""🛒 <b>ЗАКАЗ ОБРАБОТАН</b>

📋 <b>Номер заказа:</b> {order_id}
👤 <b>Клиент:</b> {order.user_name}
📞 <b>Телефон:</b> {order.phone}
📍 <b>Адрес:</b> {order.address}
💰 <b>Сумма:</b> {order.total:.2f} ₽

<b>Статус:</b> {status_text}
👨‍💼 <b>Обработал:</b> {admin_name}
⏰ <b>Время:</b> {current_time}

<i>Заказ обработан администратором</i>"""
        
        # Обновляем сообщение в чате
        chat_id = callback.message.chat.id if callback.message else None
        message_id = callback.message.message_id if callback.message else None
        
        if chat_id and message_id:
            success = await edit_order_message(chat_id, message_id, new_message_text, order_id)
            if success:
                logger.info(f"Message updated in chat {chat_id}")
            else:
                logger.warning(f"Failed to update message in chat {chat_id}")
        
        # Отправляем подтверждение администратору
        await callback.answer(f"Заказ {action_text} администратором {admin_name}", show_alert=False)
        
        # Отправляем уведомление пользователю о статусе заказа
        try:
            # Преобразуем action в статус для уведомления
            status_for_notification = "confirmed" if action == "confirm" else "rejected"
            user_notification_sent = await send_user_notification(
                user_id=order.user_id,
                order_id=order_id,
                status=status_for_notification,
                order_total=order.total
            )
            if user_notification_sent:
                logger.info(f"User notification sent to user {order.user_id} for order {order_id}")
            else:
                logger.warning(f"Failed to send notification to user {order.user_id} for order {order_id}")
        except Exception as e:
            logger.error(f"Error sending user notification: {e}", exc_info=True)
            # Не прерываем обработку, если уведомление не отправилось
        
    except Exception as e:
        logger.error(f"Error handling order callback: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при обработке заказа", show_alert=True)

