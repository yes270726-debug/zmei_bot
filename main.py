import asyncio
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TELEGRAM_TOKEN = "8313357893:AAGNbxBUBc2CzwRvp7BKyptWcomgKq1ii9k"

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# ========== ВЕБ-СЕРВЕР ==========
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Zmei bot is alive!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# ========== КОМАНДЫ ==========
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Я Змей. Пиши: !змей привет")

@dp.message(lambda m: m.text and m.text.startswith("!змей"))
async def reply(message: types.Message):
    text = message.text[6:].strip().lower()
    if "привет" in text:
        await message.answer("Привет, зайка!")
    elif "как дела" in text:
        await message.answer("Норм, а у тебя?")
    else:
        await message.answer("Расскажи подробнее!")

# ========== ЗАПУСК ==========
async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    asyncio.run(main())
