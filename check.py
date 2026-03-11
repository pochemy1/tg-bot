from dotenv import load_dotenv
import os

load_dotenv()

tg_key = os.getenv("TG_BOT_TOKEN")
openai_key = os.getenv("OPENAI_API_KEY")

print(f"Telegram токен: {'Найден' if tg_key else 'НЕ НАЙДЕН'}")
print(f"OpenAI ключ: {'Найден' if openai_key else 'НЕ НАЙДЕН'}")

if openai_key:
    print(f"Начало ключа: {openai_key[:10]}...")