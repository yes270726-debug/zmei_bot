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

# ========== АДМИНЫ (кто может использовать команды) ==========
ADMIN_IDS = [8199816124]  # Твой ID
ADMIN_USERNAMES = ["MJyr23", "lor_win"]  # Username админов

# ========== ВЕБ-СЕРВЕР ==========
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
    return user_id in ADMIN_IDS or username in ADMIN_USERNAMES

# ========== КОМАНДЫ УПРАВЛЕНИЯ ЧАТОМ ==========

# 1. УДАЛИТЬ УЧАСТНИКА
@dp.message(Command("убрать"))
async def kick_user(message: types.Message):
    if not is_admin(message.from_user.id, message.from_user.username):
        await message.reply("❌ У тебя нет прав на эту команду!")
        return
    
    # Парсим username или reply
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
            # Пытаемся найти пользователя
            chat_member = await bot.get_chat_member(message.chat.id, f"@{username}")
            user_id = chat_member.user.id
            name = chat_member.user.full_name
        except:
            await message.reply(f"❌ Не могу найти пользователя @{username}")
            return
    
    try:
        await bot.ban_chat_member(message.chat.id, user_id)
        await message.reply(f"✅ Пользователь {name} удалён из чата!")
        # Опционально: разбанить сразу (чтобы мог вернуться по ссылке)
        # await bot.unban_chat_member(message.chat.id, user_id)
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}\nПроверь, есть ли у бота права администратора!")

# 2. ЗАБАНИТЬ (с разбаном)
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

# 3. РАЗБАНИТЬ
@dp.message(Command("разбан"))
async def unban_user(message: types.Message):
    if not is_admin(message.from_user.id, message.from_user.username):
        await message.reply("❌ У тебя нет прав!")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❗ Использование: /разбан @username")
        return
    
    username = args[1].replace("@", "")
    try:
        # Нужно получить user_id по username (сложно, проще через ID)
        # Для простоты просим ID
        await message.reply("⚠️ Укажи ID пользователя: /разбан 123456789")
        return
    except:
        pass

# 4. ОЧИСТИТЬ ЧАТ (удалить последние N сообщений)
@dp.message(Command("очистить"))
async def clear_chat(message: types.Message):
    if not is_admin(message.from_user.id, message.from_user.username):
        await message.reply("❌ У тебя нет прав!")
        return
    
    args = message.text.split()
    count = 5  # по умолчанию 5
    if len(args) > 1:
        try:
            count = int(args[1])
            if count > 100:
                count = 100
        except:
            pass
    
    try:
        # Удаляем команду .очистить
        await message.delete()
        
        # Собираем сообщения для удаления
        deleted = 0
        async for msg in bot.get_chat_history(message.chat.id, limit=count):
            if msg.message_id != message.message_id:
                try:
                    await bot.delete_message(message.chat.id, msg.message_id)
                    deleted += 1
                    await asyncio.sleep(0.3)  # пауза чтобы не банило
                except:
                    pass
        
        await message.answer(f"✅ Удалено {deleted} сообщений!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}\nНужны права на удаление сообщений!")

# 5. ПРЕДУПРЕЖДЕНИЕ (варн)
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

# 6. ПРИВЕТСТВИЕ НОВИЧКОВ
@dp.message()
async def welcome_new_member(message: types.Message):
    if message.new_chat_members:
        for member in message.new_chat_members:
            if member.id != bot.id:
                await message.reply(
                    f"🐍 Добро пожаловать, {member.full_name}! Приятно познакомиться!\n"
                    f"Я Змей, хранитель этого чата. Будь вежлив и уважай других!"
                )

# ========== ОБЫЧНЫЕ ОТВЕТЫ (ОСТАЛИСЬ БЕЗ ИЗМЕНЕНИЙ) ==========
MODS = [
    "Зайчик", "Другая История", "Зайчик История Алисы",
    "Зайчик Зов Лесного Кошмара", "Зайчик Зазеркалье", "Зайчик Оковы Тьмы",
    "Зайчик Осколки Души", "Зайчик Мелодия Любви", "Зайчик Змей",
    "Зайчик Я не изгой", "Зайчик Направление Сердца", "Зайчик Овечья Шкура",
    "Зайчик Иной Финал", "Зайчик Равновесие", "Зайчик Путь Истины",
    "Зайчик Невысказанное", "Зайчик в Тумане", "Зайчик Лето"
]

MOD_ANSWERS = {
    "Зайчик": ["🐰 Зайчик - это классика! Самый душевный мод!", "Обожаю Зайчика! Это мод с которым всё началось!"],
    "Зайчик Змей": ["О, это мод про меня! Змеи рулят! 🐍", "Змей - мод про хитрость и мудрость!"],
    "Зайчик Лето": ["Лето - самый тёплый мод! Столько солнца и радости! ☀️"],
}

BASIC_ANSWERS = {
    "привет": ["Привет, зайка! 🐍", "Здарова, пушистый! 👋"],
    "как дела": ["Норм, а у тебя?", "Отлично, рассказывай!"],
    "пока": ["Пока, зайка! Заходи ещё! 👋", "До встречи, пушистый!"],
    "спасибо": ["Пожалуйста! 😊", "Не за что!"],
}

EXTRA_ANSWERS = ["Интересно!", "Расскажи подробнее!", "Змей внимает тебе!"]

# ========== ОБРАБОТЧИК ОБЫЧНЫХ СООБЩЕНИЙ ==========
@dp.message()
async def snake_reply(message: types.Message):
    global bot_enabled
    if not bot_enabled:
        return
    
    text = message.text.lower().strip() if message.text else ""
    if not text:
        return
    
    # Проверка на моды
    for mod in MODS:
        if mod.lower() in text:
            await message.answer(random.choice(MOD_ANSWERS.get(mod, ["Классный мод!"])))
            return
    
    for key in BASIC_ANSWERS:
        if key in text:
            await message.answer(random.choice(BASIC_ANSWERS[key]))
            return
    
    await message.answer(random.choice(EXTRA_ANSWERS))

# ========== ЗАПУСК ==========
async def main():
    print("=" * 50)
    print("🐍 ЗМЕЙ ЗАПУЩЕН! РАБОТАЮТ АДМИН-КОМАНДЫ!")
    print("Команды: /убрать, /бан, /очистить, /варн")
    print("=" * 50)
    await dp.start_polling(bot)

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    asyncio.run(main())
