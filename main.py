import asyncio
import os
import random
import threading
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TELEGRAM_TOKEN = "8313357893:AAGNbxBUBc2CzwRvp7BKyptWcomgKq1ii9k"

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# ========== ТВОЙ РЕАЛЬНЫЙ ID ==========
REAL_ADMIN_ID = 8199816124

# ========== ЦЕЛЕВОЙ ПОЛЬЗОВАТЕЛЬ ДЛЯ КОНТРОЛЯ ==========
TARGET_USER_ID = None  # Будет заполнено при первом обнаружении
TARGET_USERNAME = "Zakuback"
TARGET_FIRST_NAME = "тяви"

# ========== ПРОВЕРКА ПРАВ ==========
async def is_chat_admin(user_id: int, chat_id: int) -> bool:
    if user_id == REAL_ADMIN_ID:
        return True
    try:
        chat_member = await bot.get_chat_member(chat_id, user_id)
        return chat_member.status in ["creator", "administrator"]
    except:
        return False

# ========== ПРОВЕРКА ЯВЛЯЕТСЯ ЛИ ПОЛЬЗОВАТЕЛЬ ЦЕЛЕВЫМ ==========
def is_target_user(user_id: int, username: str = None, first_name: str = None) -> bool:
    global TARGET_USER_ID
    if TARGET_USER_ID and user_id == TARGET_USER_ID:
        return True
    if username and username.lower() == TARGET_USERNAME.lower():
        return True
    if first_name and first_name.lower() == TARGET_FIRST_NAME.lower():
        return True
    return False

# ========== ХРАНИЛИЩЕ ЗАПРЕЩЁННЫХ СЛОВ ==========
banned_words = []

# ========== ХРАНИЛИЩЕ ЗАМУЧЕННЫХ ПОЛЬЗОВАТЕЛЕЙ ==========
muted_users = {}

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

# ========== 1. ВКЛЮЧИТЬ/ОТКЛЮЧИТЬ БОТА ==========
@dp.message(Command("включить"))
async def enable_bot(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ У тебя нет прав!")
        return
    global bot_enabled
    bot_enabled = True
    await message.reply("🟢 Бот ВКЛЮЧЁН!")

@dp.message(Command("отключить"))
async def disable_bot(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ У тебя нет прав!")
        return
    global bot_enabled
    bot_enabled = False
    await message.reply("🔴 Бот ОТКЛЮЧЁН!")

# ========== 2. УДАЛИТЬ УЧАСТНИКА ==========
@dp.message(Command("убрать"))
async def kick_user(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ У тебя нет прав!")
        return
    
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
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❗ Использование: /убрать @username")
        return
    
    username = args[1].replace("@", "")
    try:
        chat_member = await bot.get_chat_member(message.chat.id, f"@{username}")
        user_id = chat_member.user.id
        name = chat_member.user.full_name
        await bot.ban_chat_member(message.chat.id, user_id)
        await message.reply(f"✅ {name} удалён из чата!")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

# ========== 3. ЗАБАНИТЬ ==========
@dp.message(Command("бан"))
async def ban_user(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
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

# ========== 4. ОЧИСТИТЬ ЧАТ ==========
@dp.message(Command("очистить"))
async def clear_chat(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
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
        for i in range(1, count + 1):
            try:
                msg_id = message.message_id - i
                if msg_id > 0:
                    await bot.delete_message(message.chat.id, msg_id)
                    deleted += 1
                    await asyncio.sleep(0.1)
            except:
                pass
        
        report_msg = await message.answer(f"✅ Удалено {deleted} сообщений!")
        await asyncio.sleep(3)
        try:
            await report_msg.delete()
        except:
            pass
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# ========== 5. ПРЕДУПРЕЖДЕНИЕ ==========
@dp.message(Command("варн"))
async def warn_user(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ У тебя нет прав!")
        return
    
    if not message.reply_to_message:
        await message.reply("❗ Ответь на сообщение пользователя!")
        return
    
    user = message.reply_to_message.from_user
    await message.reply(f"⚠️ ПРЕДУПРЕЖДЕНИЕ {user.full_name}!\nСоблюдай правила чата!")

# ========== 6. МУТ ==========
@dp.message(Command("мут"))
async def mute_user(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ У тебя нет прав!")
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.reply("❗ Использование: /мут @username 10м (м - минуты, ч - часы, д - дни)")
        return
    
    username = args[1].replace("@", "")
    time_str = args[2]
    
    # Парсим время
    if time_str.endswith("м"):
        minutes = int(time_str[:-1])
        seconds = minutes * 60
        text_time = f"{minutes} минут"
    elif time_str.endswith("ч"):
        hours = int(time_str[:-1])
        seconds = hours * 3600
        text_time = f"{hours} часов"
    elif time_str.endswith("д"):
        days = int(time_str[:-1])
        seconds = days * 86400
        text_time = f"{days} дней"
    else:
        await message.reply("❗ Неверный формат. Примеры: 10м, 2ч, 1д")
        return
    
    try:
        chat_member = await bot.get_chat_member(message.chat.id, f"@{username}")
        user_id = chat_member.user.id
        name = chat_member.user.full_name
        
        muted_users[user_id] = datetime.now() + timedelta(seconds=seconds)
        
        # Ограничиваем права (не может писать)
        await bot.restrict_chat_member(
            message.chat.id, user_id,
            permissions=types.ChatPermissions(can_send_messages=False)
        )
        
        await message.reply(f"🔇 {name} замучен на {text_time}!")
        
        # Авто-размут через время
        await asyncio.sleep(seconds)
        if user_id in muted_users and muted_users[user_id] <= datetime.now():
            await bot.restrict_chat_member(
                message.chat.id, user_id,
                permissions=types.ChatPermissions(can_send_messages=True)
            )
            await message.answer(f"🔊 {name} размучен автоматически.")
            del muted_users[user_id]
            
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

# ========== 7. РАЗМУТ ==========
@dp.message(Command("размут"))
async def unmute_user(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ У тебя нет прав!")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❗ Использование: /размут @username")
        return
    
    username = args[1].replace("@", "")
    try:
        chat_member = await bot.get_chat_member(message.chat.id, f"@{username}")
        user_id = chat_member.user.id
        name = chat_member.user.full_name
        
        if user_id in muted_users:
            del muted_users[user_id]
        
        await bot.restrict_chat_member(
            message.chat.id, user_id,
            permissions=types.ChatPermissions(can_send_messages=True)
        )
        await message.reply(f"🔊 {name} размучен!")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

# ========== 8. ПИНГ ==========
@dp.message(Command("пинг"))
async def ping(message: types.Message):
    start = datetime.now()
    msg = await message.answer("🏓 Понг...")
    end = datetime.now()
    latency = (end - start).total_seconds() * 1000
    await msg.edit_text(f"🏓 Понг! Задержка: {int(latency)}мс")

# ========== 9. ИНФО О ПОЛЬЗОВАТЕЛЕ ==========
@dp.message(Command("инфо"))
async def user_info(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ У тебя нет прав!")
        return
    
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    else:
        args = message.text.split()
        if len(args) < 2:
            await message.reply("❗ Использование: /инфо @username или ответь на сообщение")
            return
        username = args[1].replace("@", "")
        try:
            chat_member = await bot.get_chat_member(message.chat.id, f"@{username}")
            user = chat_member.user
        except:
            await message.reply(f"❌ Не могу найти @{username}")
            return
    
    info = (
        f"📝 ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ:\n\n"
        f"👤 Имя: {user.full_name}\n"
        f"🆔 ID: {user.id}\n"
        f"📛 Username: @{user.username if user.username else 'нет'}\n"
    )
    await message.reply(info)

# ========== 10. ЗАПРЕТИТЬ СЛОВО ==========
@dp.message(Command("запрет"))
async def ban_word(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ У тебя нет прав!")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❗ Использование: /запрет слово")
        return
    
    word = args[1].lower()
    if word not in banned_words:
        banned_words.append(word)
        await message.reply(f"✅ Слово '{word}' добавлено в чёрный список!")
    else:
        await message.reply(f"⚠️ Слово '{word}' уже в чёрном списке!")

# ========== 11. РАЗРЕШИТЬ СЛОВО ==========
@dp.message(Command("разрешить"))
async def unban_word(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ У тебя нет прав!")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❗ Использование: /разрешить слово")
        return
    
    word = args[1].lower()
    if word in banned_words:
        banned_words.remove(word)
        await message.reply(f"✅ Слово '{word}' удалено из чёрного списка!")
    else:
        await message.reply(f"⚠️ Слово '{word}' не найдено в чёрном списке!")

# ========== 12. ПРАВИЛА ==========
@dp.message(Command("правила"))
async def rules(message: types.Message):
    await message.reply(
        "📜 ПРАВИЛА ЧАТА:\n\n"
        "1️⃣ Без оскорблений\n"
        "2️⃣ Без спама\n"
        "3️⃣ Без рекламы\n"
        "4️⃣ Уважайте друг друга\n"
        "5️⃣ Слушайтесь админов\n\n"
        "Нарушители будут наказаны!"
    )

# ========== 13. HELP ==========
@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.reply(
        "🐍 КОМАНДЫ ЗМЕЯ:\n\n"
        "👑 АДМИНИСТРИРОВАНИЕ:\n"
        "/включить - Включить бота\n"
        "/отключить - Выключить бота\n"
        "/убрать @ник - Кикнуть\n"
        "/бан @ник - Забанить\n"
        "/очистить N - Очистить N сообщений\n"
        "/варн - Предупреждение\n"
        "/мут @ник время - Замутить (10м, 2ч, 1д)\n"
        "/размут @ник - Снять мут\n"
        "/запрет слово - Запретить слово\n"
        "/разрешить слово - Разрешить слово\n"
        "/инфо @ник - Инфо о пользователе\n\n"
        "📊 ИНФОРМАЦИЯ:\n"
        "/mods - Все моды\n"
        "/stats - Статистика\n"
        "/creator - О создателе\n"
        "/ping - Проверить бота\n\n"
        "💬 ПРОСТО НАПИШИ:\n"
        "Привет, как дела, пока, спасибо, люблю тебя, название мода"
    )

# ========== 14. МОДЫ, СТАТС, КРИЭЙТОР ==========
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
    await message.answer(
        f"📊 СТАТИСТИКА:\n"
        f"🐍 Модов: {len(MODS)}\n"
        f"🔞 Запрещённых слов: {len(banned_words)}\n"
        f"🔇 Замученных: {len(muted_users)}\n"
        f"💬 Статус: 🟢 РАБОТАЮ"
    )

@dp.message(Command("creator"))
async def creator_cmd(message: types.Message):
    await message.answer("👑 СОЗДАТЕЛЬ - ЛЕГЕНДА! 🔥")

# ========== 15. ПРИВЕТСТВИЕ НОВИЧКОВ ==========
@dp.message()
async def welcome_new_member(message: types.Message):
    if message.new_chat_members:
        for member in message.new_chat_members:
            if member.id != bot.id:
                await message.reply(f"🐍 Добро пожаловать, {member.full_name}!")

# ========== 16. ПРОВЕРКА НА ЗАПРЕЩЁННЫЕ СЛОВА ==========
@dp.message()
async def check_banned_words(message: types.Message):
    if not bot_enabled:
        return
    
    text = message.text.lower() if message.text else ""
    for word in banned_words:
        if word in text:
            await message.delete()
            await message.answer(f"⚠️ {message.from_user.full_name}, слово '{word}' запрещено!")
            return

# ========== 17. ПРОВЕРКА НА МУТ ==========
@dp.message()
async def check_muted(message: types.Message):
    if not bot_enabled:
        return
    
    user_id = message.from_user.id
    if user_id in muted_users:
        if muted_users[user_id] > datetime.now():
            await message.delete()
            await message.answer(f"🔇 {message.from_user.full_name}, вы замучены и не можете писать!")
        else:
            del muted_users[user_id]

# ========== 18. ОБЫЧНЫЕ ОТВЕТЫ ==========
BASIC_ANSWERS = {
    "привет": ["Привет, зайка! 🐍", "Здарова, пушистый! 👋", "Приветик! 😊"],
    "как дела": ["Норм, а у тебя?", "Отлично, рассказывай!", "Хорошо, сам как?"],
    "пока": ["Пока, зайка! 👋", "До встречи!", "Пока-пока!"],
    "спасибо": ["Пожалуйста! 😊", "Не за что!", "Всегда рад помочь!"],
    "люблю": ["И я тебя люблю! 💖", "Ой, спасибо!"],
}

EXTRA_ANSWERS = [
    "Интересно! Продолжай!",
    "Я слушаю тебя! 👂",
    "Ну и что дальше?",
    "Расскажи подробнее!",
    "Змей внимает тебе!"
]

# ========== 19. КОНТРОЛЬ НАД ВИТЕЙ (ЗАМЕНЯЕМ СООБЩЕНИЯ) ==========
TARGET_RESPONSES = [
    "Витя, не пиши ерунду! 😠",
    "тяви, прекрати! 👀",
    "@Zakuback, ты меня бесишь! 🤬",
    "Витя, иди учи уроки! 📚",
    "тяви, молчи уже! 🤐",
    "@Zakuback, заткнись! 🔇",
    "Витя, ты вообще адекватный? 🤔",
    "тяви, прекрати позориться! 😤",
    "@Zakuback, будь человеком! 🧑",
    "Витя, тебе заняться нечем? 💀",
]

TARGET_SPECIAL_RESPONSES = {
    "привет": ["Витя, иди нафиг! 👋", "тяви, не приветствуй меня!"],
    "как дела": ["Витя, а мне похер!", "тяви, не твое дело!"],
    "пока": ["Вали, Витя! 🚪", "иди нафиг, @Zakuback!"],
}

@dp.message()
async def control_target_user(message: types.Message):
    global bot_enabled, TARGET_USER_ID
    
    if not bot_enabled:
        return
    
    # Проверяем, является ли пользователь целевым
    user = message.from_user
    
    # Сохраняем ID цели при первом обнаружении
    if is_target_user(user.id, user.username, user.first_name):
        TARGET_USER_ID = user.id
        
        # Отвечаем на сообщение Вити
        text = message.text.lower().strip() if message.text else ""
        
        # Специальные ответы на ключевые слова
        for key in TARGET_SPECIAL_RESPONSES:
            if key in text:
                await message.reply(random.choice(TARGET_SPECIAL_RESPONSES[key]))
                return
        
        # Случайные ответы
        await message.reply(random.choice(TARGET_RESPONSES))

# ========== 20. ОБЫЧНЫЕ ОТВЕТЫ (перемещены в конец, чтобы не конфликтовать с контролем) ==========
@dp.message()
async def snake_reply(message: types.Message):
    global bot_enabled
    if not bot_enabled:
        return
    
    # Пропускаем, если это целевой пользователь (он уже обработан)
    if is_target_user(message.from_user.id, message.from_user.username, message.from_user.first_name):
        return
    
    text = message.text.lower().strip() if message.text else ""
    if not text:
        return
    
    # Проверка на моды
    for mod in MODS:
        if mod.lower() in text:
            await message.answer(f"О, {mod}! Классный мод! 🔥")
            return
    
    # Проверка на ключевые слова
    for key in BASIC_ANSWERS:
        if key in text:
            await message.answer(random.choice(BASIC_ANSWERS[key]))
            return
    
    # Если ничего не подошло
    await message.answer(random.choice(EXTRA_ANSWERS))

# ========== ЗАПУСК ==========
async def main():
    print("=" * 60)
    print("🐍 ЗМЕЙ ЗАПУЩЕН! ВСЕ КОМАНДЫ АКТИВНЫ!")
    print("👑 Админ: Олег")
    print("🎯 Целевой пользователь: Витя (@Zakuback, тяви)")
    print("📋 Команды: /help - список всех команд")
    print("=" * 60)
    await dp.start_polling(bot)

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    asyncio.run(main())
