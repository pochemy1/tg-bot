import os
import pathlib
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# =============================================================================
# 1. ЗАГРУЗКА КЛЮЧЕЙ
# =============================================================================

dotenv_path = pathlib.Path(__file__).parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

TOKEN = os.getenv("TG_BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")

if not TOKEN or not GROQ_KEY:
    print("❌ ОШИБКА: Не найдены ключи в файле .env!")
    exit(1)

print("✅ Ключи загружены успешно!")

# =============================================================================
# 2. НАСТРОЙКА ЛОГИРОВАНИЯ И КЛИЕНТОВ
# =============================================================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

client = Groq(api_key=GROQ_KEY)

# =============================================================================
# 3. НАСТРОЙКИ БОТА
# =============================================================================

user_histories = {}
MAX_HISTORY = 10
SYSTEM_PROMPT = "Ты — дружелюбный и полезный ИИ-ассистент в Telegram. Отвечай кратко, по делу и на русском языке."

# =============================================================================
# 4. КЛАВИАТУРА (эта функция БЫЛА пропущена!)
# =============================================================================

def get_menu_keyboard():
    """Возвращает клавиатуру с кнопками команд"""
    keyboard = [
        ["🧹 Очистить историю"],
        ["❓ Помощь"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# =============================================================================
# 5. ОБРАБОТЧИКИ КОМАНД
# =============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "👋 Привет! Я ИИ-бот на базе Groq (Llama 3.3).\n"
        "Напиши мне что-нибудь — я постараюсь помочь!",
        reply_markup=get_menu_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help — ТЕПЕРЬ РАБОТАЕТ!"""
    await update.message.reply_text(
        "📚 **Доступные команды:**\n\n"
        "/start — Запустить бота заново\n"
        "/clear — Очистить историю диалога\n"
        "/help — Показать эту справку\n\n"
        "Просто напиши мне что-нибудь — я отвечу!",
        reply_markup=get_menu_keyboard()  # <-- Теперь функция существует!
    )

async def clear_history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /clear"""
    user_id = update.effective_user.id
    if user_id in user_histories:
        del user_histories[user_id]
    await update.message.reply_text(
        "🗑️ История диалога очищена!",
        reply_markup=get_menu_keyboard()
    )

async def handle_button_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    user_message = update.message.text
    user_id = update.effective_user.id

    if user_message == "🧹 Очистить историю":
        if user_id in user_histories:
            del user_histories[user_id]
        await update.message.reply_text(
            "🗑️ История диалога очищена!",
            reply_markup=get_menu_keyboard()
        )
    elif user_message == "❓ Помощь":
        await help_command(update, context)  # <-- Переиспользуем help_command
        return  # Важно: выйти, чтобы не обрабатывать как обычное сообщение

    # Если это не наша кнопка — пропускаем
    if user_message in ["🧹 Очистить историю", "❓ Помощь"]:
        return

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    user_id = update.effective_user.id
    user_message = update.message.text

    # Пропускаем сообщения от кнопок (они уже обработаны)
    if user_message in ["🧹 Очистить историю", "❓ Помощь"]:
        return

    logger.info(f"Пользователь {user_id}: {user_message[:50]}...")

    if user_id not in user_histories:
        user_histories[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    user_histories[user_id].append({"role": "user", "content": user_message})

    if len(user_histories[user_id]) > MAX_HISTORY * 2 + 1:
        user_histories[user_id] = [user_histories[user_id][0]] + user_histories[user_id][-MAX_HISTORY*2:]

    try:
        await update.message.chat.send_action(action="typing")

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=user_histories[user_id],
            temperature=0.7,
            max_tokens=500
        )

        ai_response = response.choices[0].message.content
        user_histories[user_id].append({"role": "assistant", "content": ai_response})

        await update.message.reply_text(
            ai_response,
            reply_markup=get_menu_keyboard()
        )
        logger.info(f"Ответ отправлен пользователю {user_id}")

    except Exception as e:
        logger.error(f"Ошибка Groq: {e}")
        await update.message.reply_text(
            "😔 Ошибка при обработке запроса.",
            reply_markup=get_menu_keyboard()
        )
        if user_histories[user_id] and user_histories[user_id][-1]["role"] == "user":
            user_histories[user_id].pop()

# =============================================================================
# 6. ЗАПУСК
# =============================================================================

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_history_command))
    
    # Сначала кнопки, потом обычные сообщения
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button_text))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен! Ожидание сообщений...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()