import pathlib
import os

# Показываем, что лежит в папке
folder = pathlib.Path(__file__).parent
print("📁 Файлы в папке:")
for f in folder.iterdir():
    print(f"  - {f.name}")

# Пробуем прочитать .env напрямую
env_file = folder / ".env"
print(f"\n📄 Файл .env существует: {env_file.exists()}")

if env_file.exists():
    print(f"📏 Размер файла: {env_file.stat().st_size} байт")
    print("\n📋 Содержимое файла:")
    with open(env_file, "r", encoding="utf-8") as f:
        content = f.read()
        print(repr(content))  # Показывает скрытые символы

# Пробуем загрузить через dotenv
from dotenv import load_dotenv
load_dotenv(dotenv_path=env_file)

print("\n🔑 Переменные окружения:")
print(f"  TG_BOT_TOKEN: {'✓' if os.getenv('TG_BOT_TOKEN') else '✗'}")
print(f"  OPENAI_API_KEY: {'✓' if os.getenv('OPENAI_API_KEY') else '✗'}")