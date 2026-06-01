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

# ========== АДМИНЫ (КТО МОЖЕТ УПРАВЛЯТЬ) ==========
ADMIN_IDS = [8199816124]           # Твой ID (если правильный)
ADMIN_USERNAMES = ["MJyr23", "lor_win", "lfobot777"]   # Твой username добавлен!

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

# ========== ПРОВЕРКА АДМИНА ==========
def is_admin(user_id, username):
    if user_id in ADMIN_IDS:
        return True
    if username and username in ADMIN_USERNAMES:
        return True
    return False

# ========== 1. УДАЛИТЬ УЧАСТНИКА ==========
@dp.message(Command("убрать"))
async def kick_user(message: types.Message):
    if not is_admin(message.from_user.id, message.from_user.username):
        await message.reply("❌ У тебя нет прав на эту команду!")
        return
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        name = message.reply_to_message.from_user.full_name
    else:
        args = message.text.split()
        if len(args) < 2:
            await message.reply("❗ Использование: /убрать @username (или ответь на сообщение)")
            return
        username = args[1].replace("@", "")
        try:
            chat_member = await bot.get_chat_member(message.chat.id, f"@{username}")
            user_id = chat_member.user.id
            name = chat_member.user.full_name
        except:
            await message.reply(f"❌ Не могу найти пользователя @{username}")
            return
    
    try:
        await bot.ban_chat_member(message.chat.id, user_id)
        await message.reply(f"✅ Пользователь {name} удалён из чата!")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}\nПроверь, есть ли у бота права администратора!")

# ========== 2. ЗАБАНИТЬ ==========
@dp.message(Command("бан"))
async def ban_user(message: types.Message):
    if not is_admin(message.from_user.id, message.from_user.username):
        await message.reply("❌ У тебя нет прав!")
        return
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        name = message.reply_to_message.from_user.full_name
    else:
        args = message.text.split()
        if len(args) < 2:
            await message.reply("❗ Использование: /бан @username")
            return
        username = args[1].replace("@", "")
        try:
            chat_member = await bot.get_chat_member(message.chat.id, f"@{username}")
            user_id = chat_member.user.id
            name = chat_member.user.full_name
        except:
            await message.reply(f"❌ Не могу найти @{username}")
            return
    
    try:
        await bot.ban_chat_member(message.chat.id, user_id)
        await message.reply(f"✅ {name} забанен!")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

# ========== 3. ОЧИСТИТЬ ЧАТ ==========
@dp.message(Command("очистить"))
async def clear_chat(message: types.Message):
    if not is_admin(message.from_user.id, message.from_user.username):
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
        await message.delete()
        deleted = 0
        async for msg in bot.get_chat_history(message.chat.id, limit=count):
            try:
                await bot.delete_message(message.chat.id, msg.message_id)
                deleted += 1
                await asyncio.sleep(0.3)
            except:
                pass
        await message.answer(f"✅ Удалено {deleted} сообщений!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# ========== 4. ПРЕДУПРЕЖДЕНИЕ ==========
@dp.message(Command("варн"))
async def warn_user(message: types.Message):
    if not is_admin(message.from_user.id, message.from_user.username):
        await message.reply("❌ У тебя нет прав!")
        return
    
    if not message.reply_to_message:
        await message.reply("❗ Ответь на сообщение пользователя, которого хочешь предупредить!")
        return
    
    user = message.reply_to_message.from_user
    await message.reply(f"⚠️ ПРЕДУПРЕЖДЕНИЕ {user.full_name}!\nПожалуйста, соблюдай правила чата!")

# ========== 5. ПРИВЕТСТВИЕ НОВИЧКОВ ==========
@dp.message()
async def welcome_new_member(message: types.Message):
    if message.new_chat_members:
        for member in message.new_chat_members:
            if member.id != bot.id:
                await message.reply(
                    f"🐍 Добро пожаловать, {member.full_name}! Приятно познакомиться!\n"
                    f"Я Змей, хранитель этого чата. Будь вежлив и уважай других!"
                )

# ========== 6. ВКЛ/ВЫКЛ БОТА ==========
@dp.message(Command("отключить"))
async def disable_bot(message: types.Message):
    if not is_admin(message.from_user.id, message.from_user.username):
        await message.reply("❌ У тебя нет прав!")
        return
    global bot_enabled
    bot_enabled = False
    await message.reply("🔴 Бот ОТКЛЮЧЁН! Админы могут включить командой /включить")

@dp.message(Command("включить"))
async def enable_bot(message: types.Message):
    if not is_admin(message.from_user.id, message.from_user.username):
        await message.reply("❌ У тебя нет прав!")
        return
    global bot_enabled
    bot_enabled = True
    await message.reply("🟢 Бот ВКЛЮЧЁН!")

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
    await message.answer(f"📚 МОДЫ:\n\n{mods_list}\n\nНапиши название любого мода, я расскажу!")

@dp.message(Command("stats"))
async def stats_cmd(message: types.Message):
    await message.answer(
        f"📊 СТАТИСТИКА:\n\n"
        f"🐍 Ответов: 5000+\n"
        f"🎮 Модов: {len(MODS)}\n"
        f"👑 Админы: @MJyr23, @lor_win, @lfobot777\n"
        f"💬 Статус: 🟢 РАБОТАЮ"
    )

@dp.message(Command("creator"))
async def creator_cmd(message: types.Message):
    await message.answer("👑 СОЗДАТЕЛЬ - ЛЕГЕНДА! 🔥\n\nОн создал все эти крутые моды и меня самого!\nЯ его обожаю и уважаю больше всех! ❤️")

# ========== 8. ОБЫЧНЫЕ ОТВЕТЫ ==========
BASIC_ANSWERS = {
    "привет": ["Привет, зайка! 🐍", "Здарова, пушистый! 👋", "Приветик! Как сам? 😊"],
    "как дела": ["Норм, греюсь на солнышке! А у тебя?", "Отлично, рассказывай давай!", "Хорошо, сам как?"],
    "пока": ["Пока, зайка! Заходи ещё! 👋", "До встречи, пушистый!", "Пока-пока, буду ждать!"],
    "спасибо": ["Пожалуйста! 😊", "Не за что, обращайся!", "Всегда рад помочь!"],
    "люблю": ["И я тебя люблю, зайка! 💖", "Ой, спасибо! Я тоже тебя!"],
    "создатель": ["👑 СОЗДАТЕЛЬ - ЛЕГЕНДА! Обожаю его!", "Мой создатель красавчик, гений!"],
    "чат": ["Vitalem - лучший чат! 💬", "Наш чат топ, остальные мимо!"],
}

EXTRA_ANSWERS = [
    "Интересно ты говоришь, зайка! Продолжай!",
    "Я тебя слушаю, любимый! 👂",
    "Ну и что дальше, сладкий?",
    "Змей внимает тебе! Давай-давай!",
    "Расскажи подробнее, пушистый!"
]

@dp.message()
async def snake_reply(message: types.Message):
    global bot_enabled
    if not bot_enabled:
        return
    
    text = message.text.lower().strip() if message.text else ""
    if not text:
        return
    
    # Приветствие новичков (уже обработано выше через message.new_chat_members)
    
    # Проверка на моды
    for mod in MODS:
        if mod.lower() in text:
            await message.answer(f"О, {mod}! Классный мод! Я его очень ценю! 🔥")
            return
    
    # Поиск ответа
    for key in BASIC_ANSWERS:
        if key in text:
            await message.answer(random.choice(BASIC_ANSWERS[key]))
            return
    
    await message.answer(random.choice(EXTRA_ANSWERS))

# ========== ЗАПУСК ==========
async def main():
    print("=" * 50)
    print("🐍 ЗМЕЙ ЗАПУЩЕН! АДМИН-КОМАНДЫ РАБОТАЮТ!")
    print("Админы: @MJyr23, @lor_win, @lfobot777")
    print("Команды: /убрать, /бан, /очистить, /варн, /отключить, /включить")
    print("=" * 50)
    await dp.start_polling(bot)

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    asyncio.run(main())
