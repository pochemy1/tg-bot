import os
import pathlib
from dotenv import load_dotenv

# Показываем путь
print(f"📁 Путь к файлу: {pathlib.Path(__file__).parent}")

# Загружаем .env
dotenv_path = pathlib.Path(__file__).parent / ".env"
print(f"📄 Путь к .env: {dotenv_path}")
print(f"✅ .env существует: {dotenv_path.exists()}")

load_dotenv(dotenv_path=dotenv_path)

# Проверяем ключи
TOKEN = os.getenv("TG_BOT_TOKEN")
KEY = os.getenv("OPENAI_API_KEY")

print(f"\n🔑 TG токен: {TOKEN[:10]}..." if TOKEN else "🔑 TG токен: НЕ НАЙДЕН")
print(f"🔑 OpenAI ключ: {KEY[:10]}..." if KEY else "🔑 OpenAI ключ: НЕ НАЙДЕН")

if TOKEN and KEY:
    print("\n✅ ВСЁ РАБОТАЕТ! Запускайте bot.py")
else:
    print("\n❌ ПРОБЛЕМА С ЧТЕНИЕМ .env")