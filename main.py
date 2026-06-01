import asyncio
import os
import random
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TELEGRAM_TOKEN = "8313357893:AAGNbxBUBc2CzwRvp7BKyptWcomgKq1ii9k"

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# ========== РАЗРЕШАЕМ ВСЕ КОМАНДЫ ДЛЯ ТЕБЯ (ВРЕМЕННО, ДЛЯ ТЕСТА) ==========
# Потом заменишь на проверку по ID
ALLOWED_USER_IDS = [8199816124]  # ТВОЙ ID

def is_allowed(user_id):
    return user_id in ALLOWED_USER_IDS

# ========== ВЕБ-СЕРВЕР ДЛЯ RENDER ==========
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Zmei bot is alive!")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# ========== СТАТУС БОТА ==========
bot_enabled = True

# ========== 1. УДАЛИТЬ УЧАСТНИКА ==========
@dp.message(Command("убрать"))
async def kick_user(message: types.Message):
    if not is_allowed(message.from_user.id):
        await message.reply("❌ У тебя нет прав!")
        return
    
    # Если ответили на сообщение
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        name = message.reply_to_message.from_user.full_name
        try:
            await bot.ban_chat_member(message.chat.id, user_id)
            await message.reply(f"✅ {name} удалён из чата!")
            return
        except Exception as e:
            await message.reply(f"❌ Ошибка: {e}")
            return
    
    # Если указали username
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❗ Использование: /убрать @username ИЛИ ответь на сообщение")
        return
    
    username = args[1].replace("@", "")
    try:
        # Получаем информацию о пользователе
        chat_member = await bot.get_chat_member(message.chat.id, f"@{username}")
        user_id = chat_member.user.id
        name = chat_member.user.full_name
        await bot.ban_chat_member(message.chat.id, user_id)
        await message.reply(f"✅ {name} удалён из чата!")
    except Exception as e:
        await message.reply(f"❌ Не могу найти @{username} или ошибка: {e}")

# ========== 2. ЗАБАНИТЬ ==========
@dp.message(Command("бан"))
async def ban_user(message: types.Message):
    if not is_allowed(message.from_user.id):
        await message.reply("❌ У тебя нет прав!")
        return
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        name = message.reply_to_message.from_user.full_name
        try:
            await bot.ban_chat_member(message.chat.id, user_id)
            await message.reply(f"✅ {name} забанен!")
            return
        except Exception as e:
            await message.reply(f"❌ Ошибка: {e}")
            return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❗ Использование: /бан @username")
        return
    
    username = args[1].replace("@", "")
    try:
        chat_member = await bot.get_chat_member(message.chat.id, f"@{username}")
        user_id = chat_member.user.id
        name = chat_member.user.full_name
        await bot.ban_chat_member(message.chat.id, user_id)
        await message.reply(f"✅ {name} забанен!")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

# ========== 3. ОЧИСТИТЬ ЧАТ ==========
@dp.message(Command("очистить"))
async def clear_chat(message: types.Message):
    if not is_allowed(message.from_user.id):
        await message.reply("❌ У тебя нет прав!")
        return
    
    args = message.text.split()
    count = 5
    if len(args) > 1:
        try:
            count = int(args[1])
            if count > 100:
                count = 100
        except:
            pass
    
    try:
        # Удаляем команду
        await message.delete()
        deleted = 0
        async for msg in bot.get_chat_history(message.chat.id, limit=count):
            try:
                await bot.delete_message(message.chat.id, msg.message_id)
                deleted += 1
                await asyncio.sleep(0.2)
            except:
                pass
        await message.answer(f"✅ Удалено {deleted} сообщений!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# ========== 4. ПРЕДУПРЕЖДЕНИЕ ==========
@dp.message(Command("варн"))
async def warn_user(message: types.Message):
    if not is_allowed(message.from_user.id):
        await message.reply("❌ У тебя нет прав!")
        return
    
    if not message.reply_to_message:
        await message.reply("❗ Ответь на сообщение пользователя, которого хочешь предупредить!")
        return
    
    user = message.reply_to_message.from_user
    await message.reply(f"⚠️ ПРЕДУПРЕЖДЕНИЕ {user.full_name}!\nСоблюдай правила чата!")

# ========== 5. ВКЛ/ВЫКЛ БОТА ==========
@dp.message(Command("отключить"))
async def disable_bot(message: types.Message):
    if not is_allowed(message.from_user.id):
        await message.reply("❌ У тебя нет прав!")
        return
    global bot_enabled
    bot_enabled = False
    await message.reply("🔴 Бот ОТКЛЮЧЁН!")

@dp.message(Command("включить"))
async def enable_bot(message: types.Message):
    if not is_allowed(message.from_user.id):
        await message.reply("❌ У тебя нет прав!")
        return
    global bot_enabled
    bot_enabled = True
    await message.reply("🟢 Бот ВКЛЮЧЁН!")

# ========== 6. ПРИВЕТСТВИЕ НОВИЧКОВ ==========
@dp.message()
async def welcome_new_member(message: types.Message):
    if message.new_chat_members:
        for member in message.new_chat_members:
            if member.id != bot.id:
                await message.reply(f"🐍 Добро пожаловать, {member.full_name}!")

# ========== 7. КОМАНДЫ /mods, /stats, /creator ==========
MODS = [
    "Зайчик", "Другая История", "Зайчик История Алисы",
    "Зайчик Зов Лесного Кошмара", "Зайчик Зазеркалье", "Зайчик Оковы Тьмы",
    "Зайчик Осколки Души", "Зайчик Мелодия Любви", "Зайчик Змей",
    "Зайчик Я не изгой", "Зайчик Направление Сердца", "Зайчик Овечья Шкура",
    "Зайчик Иной Финал", "Зайчик Равновесие", "Зайчик Путь Истины",
    "Зайчик Невысказанное", "Зайчик в Тумане", "Зайчик Лето"
]

@dp.message(Command("mods"))
async def mods_cmd(message: types.Message):
    mods_list = "\n".join([f"• {m}" for m in MODS])
    await message.answer(f"📚 МОДЫ:\n\n{mods_list}")

@dp.message(Command("stats"))
async def stats_cmd(message: types.Message):
    await message.answer(f"📊 СТАТИСТИКА:\n🐍 Модов: {len(MODS)}\n💬 Статус: 🟢 РАБОТАЮ")

@dp.message(Command("creator"))
async def creator_cmd(message: types.Message):
    await message.answer("👑 СОЗДАТЕЛЬ - ЛЕГЕНДА! 🔥")

# ========== 8. ОБЫЧНЫЕ ОТВЕТЫ ==========
BASIC_ANSWERS = {
    "привет": ["Привет, зайка! 🐍", "Здарова!", "Приветик! 😊"],
    "как дела": ["Норм, а у тебя?", "Отлично!", "Хорошо!"],
    "пока": ["Пока, зайка! 👋", "До встречи!", "Пока-пока!"],
    "спасибо": ["Пожалуйста! 😊", "Не за что!", "Всегда рад помочь!"],
}

EXTRA_ANSWERS = ["Интересно!", "Расскажи подробнее!", "Змей внимает тебе!"]

@dp.message()
async def snake_reply(message: types.Message):
    global bot_enabled
    if not bot_enabled:
        return
    
    text = message.text.lower().strip() if message.text else ""
    if not text:
        return
    
    # Приветствие новичков уже обработано выше
    
    # Проверка на моды
    for mod in MODS:
        if mod.lower() in text:
            await message.answer(f"О, {mod}! Классный мод! 🔥")
            return
    
    for key in BASIC_ANSWERS:
        if key in text:
            await message.answer(random.choice(BASIC_ANSWERS[key]))
            return
    
    await message.answer(random.choice(EXTRA_ANSWERS))

# ========== ЗАПУСК ==========
async def main():
    print("=" * 50)
    print("🐍 ЗМЕЙ ЗАПУЩЕН!")
    print("Команды: /убрать, /бан, /очистить, /варн, /отключить, /включить")
    print("=" * 50)
    await dp.start_polling(bot)

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    asyncio.run(main())
