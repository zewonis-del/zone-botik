from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.helpers import escape_markdown
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

# Конфигурация
BOT_TOKEN = "8549279597:AAGordI_CNDWXbczNxBHi06urY5hVKtg_fI"
CHANNEL_ID = -1003209253138
OPERATOR_USERNAME = "@ВАШ_ОПЕРАТОР"  # Замените на username оператора

# Хранение данных пользователей
user_data = {}


# Клавиатуры
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🛒 Купить", callback_data="buy")],
        [
            InlineKeyboardButton("👨‍💼 Оператор", url=f"https://t.me/{OPERATOR_USERNAME.replace('@', '')}"),
            InlineKeyboardButton("📖 Инструкция", callback_data="instruction")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def catalog_keyboard():
    keyboard = [
        [InlineKeyboardButton("🍺 Пиво", callback_data="product_1"),
        InlineKeyboardButton("🍸 Водка", callback_data="product_2")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def quantity_keyboard(user_id):
    quantity = user_data.get(user_id, {}).get('quantity', 1)
    product_name = user_data.get(user_id, {}).get('product_name', 'Товар')

    keyboard = [
        [
            InlineKeyboardButton("➖", callback_data="decrease"),
            InlineKeyboardButton(f"{quantity} шт.", callback_data="show_quantity"),
            InlineKeyboardButton("➕", callback_data="increase")
        ],
        [InlineKeyboardButton("✅ Подтвердить заказ", callback_data="confirm_order")],
        [InlineKeyboardButton("🔙 Назад к каталогу", callback_data="back_to_catalog")]
    ]
    return InlineKeyboardMarkup(keyboard)


def back_only_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


# Обработчики
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data:
        user_data[user_id] = {'quantity': 1}

    await update.message.reply_text(
        "🌟 Добро пожаловать в наш магазин!\n\n"
        "Тут будет красивый текст про ваш магазин и товары!",
        reply_markup=main_menu_keyboard()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    data = query.data

    await query.answer()

    # Инициализация данных пользователя если нужно
    if user_id not in user_data:
        user_data[user_id] = {'quantity': 1}

    if data == "buy":
        await query.edit_message_text(
            "🛍️ *Каталог товаров*\n\n"
            "Выберите товар из списка:",
            reply_markup=catalog_keyboard(),
            parse_mode='Markdown'
        )

    elif data == "instruction":
        await query.edit_message_text(
            "📖 *Инструкция по покупке*\n\n"
            "1. Выберите товар из каталога\n"
            "2. Укажите необходимое количество\n"
            "3. Подтвердите заказ\n"
            "4. Ожидайте связи с оператором\n\n"
            "💰 *Способ оплаты:*\n"
            "Наличка\n\n"
            "🚚 *Доставка:*\n"
            "• По области\n",
            reply_markup=back_only_keyboard(),
            parse_mode='Markdown'
        )

    elif data.startswith("product_"):
        product_id = data.split("_")[1]
        product_names = {
            "1": "Пиво",
            "2": "Водка"
        }

        user_data[user_id]['product_name'] = product_names[product_id]
        user_data[user_id]['quantity'] = 1  # Сбрасываем количество при выборе нового товара

        await query.edit_message_text(
            f"🎁 *{product_names[product_id]}*\n\n"
            "Описание товара и его характеристики...\n\n"
            "Выберите количество:",
            reply_markup=quantity_keyboard(user_id),
            parse_mode='Markdown'
        )

    elif data in ["increase", "decrease"]:
        current_quantity = user_data[user_id].get('quantity', 1)
        product_name = user_data[user_id].get('product_name', 'Товар')

        if data == "increase":
            user_data[user_id]['quantity'] = current_quantity + 1
        elif data == "decrease" and current_quantity > 1:
            user_data[user_id]['quantity'] = current_quantity - 1

        await query.edit_message_text(
            f"🎁 *{product_name}*\n\n"
            "Выберите количество:",
            reply_markup=quantity_keyboard(user_id),
            parse_mode='Markdown'
        )


    elif data == "confirm_order":
        quantity = user_data[user_id].get('quantity', 1)
        product_name = user_data[user_id].get('product_name', 'Товар')
        username = f"@{update.effective_user.username}" if update.effective_user.username else "Не указан"
        # Экранируем все поля, которые могут содержать разметку

        escaped_username = escape_markdown(username, version=2)
        escaped_operator_username = escape_markdown(OPERATOR_USERNAME, version=2)
        escaped_product_name = escape_markdown(product_name, version=2)
        order_text = (
            "🛍️ *НОВЫЙ ЗАКАЗ*\n\n"
            f"👤 *Пользователь:* {escaped_username}\n"
            f"🆔 *ID:* {user_id}\n"
            f"📦 *Товар:* {escaped_product_name}\n"
            f"🔢 *Количество:* {quantity} шт\.\n"
            f"⏰ *Время:* {update.effective_message.date.strftime('%d\\.%m\\.%Y %H:%M')}\n\n"
            "⚡ *Статус:* Ожидает обработки"
        )
        try:
            # Пытаемся отправить заказ в канал

            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=order_text,
                parse_mode='MarkdownV2'  # ← ИЗМЕНИЛИ НА MarkdownV2
            )

            # ВМЕСТО РЕДАКТИРОВАНИЯ СООБЩЕНИЯ ОТПРАВЛЯЕМ НОВОЕ
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="✅ *Ваш заказ подтвержден*\n\n"
                     f"📦 Товар: {escaped_product_name}\n"
                     f"🔢 Количество: {quantity} шт\.\n\n"
                     "📋 Заказ отправлен на обработку\.\n"
                     f"👨‍💼 Для связи с оператором: {escaped_operator_username}\n\n"
                     "⏳ Мы свяжемся с вами в ближайшее время",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🛒 Сделать новый заказ", callback_data="back_to_main")],
                    [InlineKeyboardButton("👨‍💼 Связаться с оператором",
                                          url=f"https://t.me/{escaped_operator_username.replace('@', '')}")]
                ]),
                parse_mode='MarkdownV2'
            )

        except Exception as e:
            # Выводим ошибку в консоль для отладки
            print(f"Ошибка при отправке в канал: {e}")  # ← ДОБАВИЛИ ВЫВОД ОШИБКИ
            await query.edit_message_text(
                f"❌ Произошла ошибка при отправке заказа\n\n"
                "Пожалуйста, попробуйте позже или свяжитесь с оператором.",
                reply_markup=back_only_keyboard()
            )

    elif data == "back_to_catalog":
        await query.edit_message_text(
            "🛍️ *Каталог товаров*\n\n"
            "Выберите товар из списка:",
            reply_markup=catalog_keyboard(),
            parse_mode='Markdown'
        )

    elif data == "back_to_main":
        # ВМЕСТО РЕДАКТИРОВАНИЯ СООБЩЕНИЯ ОТПРАВЛЯЕМ НОВОЕ
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🌟 Главное меню\n\n"
                 "Тут будет красивый текст про ваш магазин и товары!",
            reply_markup=main_menu_keyboard()
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    await update.message.reply_text(
        "Пожалуйста, используйте кнопки меню для навигации:",
        reply_markup=main_menu_keyboard()
    )


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    app.run_polling()