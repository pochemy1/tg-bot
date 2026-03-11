import os
import pathlib
import logging
from dotenv import load_dotenv
from telegram import Update
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
    print("Проверьте, что файл .env содержит:")
    print("  TG_BOT_TOKEN=ваш_токен")
    print("  GROQ_API_KEY=gsk_ваш_ключ")
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

# Инициализация клиента Groq
client = Groq(api_key=GROQ_KEY)

# =============================================================================
# 3. НАСТРОЙКИ БОТА
# =============================================================================

# Хранилище истории: {user_id: [messages]}
user_histories = {}
MAX_HISTORY = 10  # Сколько пар сообщений помнить

# Системный промпт — "личность" бота
SYSTEM_PROMPT = "Ты — остроумный, отвечаешь с сарказмом. Отвечай на русском языке. В конце всегда пиши лошара рил 👻"

# =============================================================================
# 4. ОБРАБОТЧИКИ КОМАНД
# =============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "Здарова, я никита нейромелочкин. я не особо умный, но если че пиши. Вот тут команды есть /help"
    )

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /clear"""
    user_id = update.effective_user.id
    if user_id in user_histories:
        del user_histories[user_id]
    await update.message.reply_text("🗑️ История диалога очищена!")
    
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "📚 **Доступные команды:**\n\n"
        "/start — запустить бота\n"
        "/clear — очистить историю диалога\n"
        "/help — сходить нахуй ну ты уже тут\n\n"
        "Не пиши мне больше пожалуйста",
        reply_markup=get_menu_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    user_id = update.effective_user.id
    user_message = update.message.text

    logger.info(f"Пользователь {user_id}: {user_message[:50]}...")

    # Инициализация истории для нового пользователя
    if user_id not in user_histories:
        user_histories[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Добавляем сообщение пользователя
    user_histories[user_id].append({"role": "user", "content": user_message})

    # Ограничиваем длину истории (чтобы не тратить лишние токены)
    if len(user_histories[user_id]) > MAX_HISTORY * 2 + 1:
        user_histories[user_id] = [user_histories[user_id][0]] + user_histories[user_id][-MAX_HISTORY*2:]

    try:
        # Показываем статус "печатает..."
        await update.message.chat.send_action(action="typing")

        # Запрос к Groq API
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # ✅ Стабильная модель
            messages=user_histories[user_id],
            temperature=0.7,
            max_tokens=500
        )

        ai_response = response.choices[0].message.content

        # Добавляем ответ бота в историю
        user_histories[user_id].append({"role": "assistant", "content": ai_response})

        # Отправляем ответ пользователю
        await update.message.reply_text(ai_response)
        logger.info(f"Ответ отправлен пользователю {user_id}")

    except Exception as e:
        logger.error(f"Ошибка Groq: {e}")
        await update.message.reply_text(
            "😔 Ошибка при обработке запроса.\n"
            "Возможно, закончились лимиты Groq или проблема с ключом."
        )
        # Удаляем последнее сообщение пользователя при ошибке
        if user_histories[user_id] and user_histories[user_id][-1]["role"] == "user":
            user_histories[user_id].pop()

# =============================================================================
# 5. ЗАПУСК
# =============================================================================

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear_history_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен! Ожидание сообщений...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()