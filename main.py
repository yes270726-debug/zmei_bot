import asyncio
import os
import random
import threading
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

TELEGRAM_TOKEN = "8313357893:AAGNbxBUBc2CzwRvp7BKyptWcomgKq1ii9k"

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# ========== ТВОЙ РЕАЛЬНЫЙ ID ==========
REAL_ADMIN_ID = 8199816124

# ========== ЦЕЛЕВОЙ ПОЛЬЗОВАТЕЛЬ ДЛЯ КОНТРОЛЯ ==========
TARGET_USER_ID = None
TARGET_USERNAME = "Zakuback"
TARGET_FIRST_NAME = "тяви"

# ========== ХРАНИЛИЩА ==========
banned_words = []
muted_users = {}
bot_enabled = True
shipped_couples = []
married_couples = []

# ========== ПРОВЕРКА ПРАВ ==========
async def is_chat_admin(user_id: int, chat_id: int) -> bool:
    if user_id == REAL_ADMIN_ID:
        return True
    try:
        chat_member = await bot.get_chat_member(chat_id, user_id)
        return chat_member.status in ["creator", "administrator"]
    except:
        return False

# ========== ПРОВЕРКА ЦЕЛЕВОГО ПОЛЬЗОВАТЕЛЯ ==========
def is_target_user(user_id: int, username: str = None, first_name: str = None) -> bool:
    global TARGET_USER_ID
    if TARGET_USER_ID and user_id == TARGET_USER_ID:
        return True
    if username and username.lower() == TARGET_USERNAME.lower():
        return True
    if first_name and first_name.lower() == TARGET_FIRST_NAME.lower():
        return True
    return False

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

# ========== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ==========
async def get_user_by_username(chat_id: int, username: str):
    username = username.replace("@", "")
    try:
        member = await bot.get_chat_member(chat_id, f"@{username}")
        return member.user
    except:
        chat = await bot.get_chat(f"@{username}")
        return chat

# ========== ДИАГНОСТИКА ==========
@dp.message(Command("myid"))
async def show_my_id(message: types.Message):
    await message.reply(f"👤 ТВОЙ ID: {message.from_user.id}")

@dp.message(Command("ping"))
async def ping(message: types.Message):
    start = datetime.now()
    msg = await message.answer("🏓 Понг...")
    end = datetime.now()
    latency = (end - start).total_seconds() * 1000
    await msg.edit_text(f"🏓 Понг! Задержка: {int(latency)}мс")

# ========== КОМАНДЫ ШИППЕРИНГА ==========
@dp.message(Command("шиперить"))
async def ship_random(message: types.Message):
    try:
        chat_members = []
        offset = 0
        limit = 100
        
        while True:
            try:
                members = await bot.get_chat_members(
                    chat_id=message.chat.id,
                    offset=offset,
                    limit=limit
                )
                if not members:
                    break
                for member in members:
                    if not member.user.is_bot:
                        chat_members.append(member.user)
                offset += len(members)
                if len(members) < limit:
                    break
            except:
                break
        
        if len(chat_members) < 3:
            admins = await bot.get_chat_administrators(message.chat.id)
            for admin in admins:
                if not admin.user.is_bot and admin.user not in chat_members:
                    chat_members.append(admin.user)
        
        if len(chat_members) < 2:
            await message.reply("😅 Нужно минимум 2 человека!")
            return
        
        user1, user2 = random.sample(chat_members, 2)
        
        ship_names = [
            f"{user1.first_name}💕{user2.first_name}",
            f"{user1.first_name}❤️{user2.first_name}",
            f"{user1.first_name}🔥{user2.first_name}"
        ]
        ship_name = random.choice(ship_names)
        
        shipped_couples.append({
            "ship_name": ship_name,
            "user1_id": user1.id,
            "user1_name": user1.full_name,
            "user2_id": user2.id,
            "user2_name": user2.full_name,
            "date": datetime.now().strftime("%d.%m.%Y")
        })
        
        await message.reply(
            f"🐍 ЗМЕЙ ШИППЕРИТ! 🎲\n\n"
            f"💕 {user1.full_name} и {user2.full_name}\n\n"
            f"💞 Название: {ship_name}"
        )
        
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

@dp.message(Command("шипнуть"))
async def ship_specific(message: types.Message):
    args = message.text.split()
    if len(args) < 3:
        await message.reply("❗ /шипнуть @ник1 @ник2")
        return
    
    try:
        user1 = await get_user_by_username(message.chat.id, args[1])
        user2 = await get_user_by_username(message.chat.id, args[2])
        
        ship_names = [
            f"{user1.full_name}💕{user2.full_name}",
            f"{user1.full_name}❤️{user2.full_name}",
            f"{user1.full_name}🔥{user2.full_name}"
        ]
        ship_name = random.choice(ship_names)
        
        shipped_couples.append({
            "ship_name": ship_name,
            "user1_id": user1.id,
            "user1_name": user1.full_name,
            "user2_id": user2.id,
            "user2_name": user2.full_name,
            "date": datetime.now().strftime("%d.%m.%Y")
        })
        
        await message.reply(
            f"🐍 ШИППНУТО! 💕\n\n"
            f"{user1.full_name} + {user2.full_name}\n"
            f"Название: {ship_name}"
        )
        
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

@dp.message(Command("шиппы"))
async def show_ships(message: types.Message):
    if not shipped_couples:
        await message.reply("😔 Нет шиппов!")
        return
    
    text = "🐍 ВСЕ ШИППЫ:\n\n"
    for i, ship in enumerate(shipped_couples, 1):
        text += f"{i}. {ship['ship_name']}\n"
        text += f"   {ship['user1_name']} + {ship['user2_name']}\n\n"
    
    await message.reply(text)

# ========== КОМАНДЫ СВАДЬБЫ ==========
@dp.message(Command("женится"))
async def marry_users(message: types.Message):
    args = message.text.split()
    if len(args) < 3:
        await message.reply("❗ /женится @ник1 @ник2")
        return
    
    try:
        user1 = await get_user_by_username(message.chat.id, args[1])
        user2 = await get_user_by_username(message.chat.id, args[2])
        
        married_couples.append({
            "user1_id": user1.id,
            "user1_full": user1.full_name,
            "user2_id": user2.id,
            "user2_full": user2.full_name,
            "date": datetime.now().strftime("%d.%m.%Y")
        })
        
        congrats = [
            f"💍 СВАДЬБА! 💍\n\n{user1.full_name} и {user2.full_name} теперь МУЖ И ЖЕНА! 💑",
            f"💞 {user1.full_name} и {user2.full_name} теперь СЕМЬЯ! 🏠",
            f"🎊 {user1.full_name} 💍 {user2.full_name}\n\nТеперь они вместе! 💕"
        ]
        
        await message.reply(random.choice(congrats))
        
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

@dp.message(Command("развод"))
async def divorce_users(message: types.Message):
    args = message.text.split()
    if len(args) < 3:
        await message.reply("❗ /развод @ник1 @ник2")
        return
    
    user1_name = args[1].replace("@", "")
    user2_name = args[2].replace("@", "")
    
    found = False
    for couple in married_couples:
        if (couple["user1_full"].lower() == user1_name.lower() or 
            couple["user1_full"].lower() == user2_name.lower()) and \
           (couple["user2_full"].lower() == user1_name.lower() or 
            couple["user2_full"].lower() == user2_name.lower()):
            married_couples.remove(couple)
            found = True
            break
    
    if not found:
        await message.reply(f"😅 {user1_name} и {user2_name} не женаты!")
        return
    
    await message.reply(f"💔 {user1_name} и {user2_name} развелись!")

@dp.message(Command("женатые"))
async def show_married(message: types.Message):
    if not married_couples:
        await message.reply("😔 Нет браков!")
        return
    
    text = "💍 ВСЕ БРАКИ:\n\n"
    for i, couple in enumerate(married_couples, 1):
        text += f"{i}. {couple['user1_full']} 💍 {couple['user2_full']}\n"
        text += f"   📅 {couple['date']}\n\n"
    
    await message.reply(text)

# ========== КОМАНДЫ АДМИНИСТРИРОВАНИЯ ==========
@dp.message(Command("включить"))
async def enable_bot(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ Нет прав!")
        return
    global bot_enabled
    bot_enabled = True
    await message.reply("🟢 Бот ВКЛЮЧЁН!")

@dp.message(Command("отключить"))
async def disable_bot(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ Нет прав!")
        return
    global bot_enabled
    bot_enabled = False
    await message.reply("🔴 Бот ОТКЛЮЧЁН!")

@dp.message(Command("статус"))
async def status_bot(message: types.Message):
    status = "🟢 ВКЛЮЧЁН" if bot_enabled else "🔴 ОТКЛЮЧЁН"
    await message.reply(f"📊 СТАТУС: {status}")

@dp.message(Command("убрать"))
async def kick_user(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ Нет прав!")
        return
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        name = message.reply_to_message.from_user.full_name
        try:
            await bot.ban_chat_member(message.chat.id, user_id)
            await asyncio.sleep(1)
            await bot.unban_chat_member(message.chat.id, user_id)
            await message.reply(f"✅ {name} удалён!")
            return
        except Exception as e:
            await message.reply(f"❌ {e}")
            return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❗ /убрать @username")
        return
    
    try:
        member = await bot.get_chat_member(message.chat.id, args[1])
        await bot.ban_chat_member(message.chat.id, member.user.id)
        await asyncio.sleep(1)
        await bot.unban_chat_member(message.chat.id, member.user.id)
        await message.reply(f"✅ {member.user.full_name} удалён!")
    except Exception as e:
        await message.reply(f"❌ {e}")

@dp.message(Command("бан"))
async def ban_user(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ Нет прав!")
        return
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        name = message.reply_to_message.from_user.full_name
        try:
            await bot.ban_chat_member(message.chat.id, user_id)
            await message.reply(f"✅ {name} забанен!")
            return
        except Exception as e:
            await message.reply(f"❌ {e}")
            return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❗ /бан @username")
        return
    
    try:
        member = await bot.get_chat_member(message.chat.id, args[1])
        await bot.ban_chat_member(message.chat.id, member.user.id)
        await message.reply(f"✅ {member.user.full_name} забанен!")
    except Exception as e:
        await message.reply(f"❌ {e}")

@dp.message(Command("очистить"))
async def clear_chat(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ Нет прав!")
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
        
        msg = await message.answer(f"✅ Удалено {deleted} сообщений!")
        await asyncio.sleep(2)
        await msg.delete()
    except Exception as e:
        await message.answer(f"❌ {e}")

@dp.message(Command("варн"))
async def warn_user(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ Нет прав!")
        return
    
    if not message.reply_to_message:
        await message.reply("❗ Ответь на сообщение!")
        return
    
    user = message.reply_to_message.from_user
    await message.reply(f"⚠️ ПРЕДУПРЕЖДЕНИЕ {user.full_name}!")

@dp.message(Command("мут"))
async def mute_user(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ Нет прав!")
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.reply("❗ /мут @ник 10м (м,ч,д)")
        return
    
    try:
        member = await bot.get_chat_member(message.chat.id, args[1])
        time_str = args[2]
        
        if time_str.endswith("м"):
            seconds = int(time_str[:-1]) * 60
            text_time = f"{int(time_str[:-1])} минут"
        elif time_str.endswith("ч"):
            seconds = int(time_str[:-1]) * 3600
            text_time = f"{int(time_str[:-1])} часов"
        elif time_str.endswith("д"):
            seconds = int(time_str[:-1]) * 86400
            text_time = f"{int(time_str[:-1])} дней"
        else:
            await message.reply("❗ Формат: 10м, 2ч, 1д")
            return
        
        muted_users[member.user.id] = datetime.now() + timedelta(seconds=seconds)
        
        await bot.restrict_chat_member(
            message.chat.id, member.user.id,
            permissions=types.ChatPermissions(can_send_messages=False)
        )
        
        await message.reply(f"🔇 {member.user.full_name} замучен на {text_time}!")
        
    except Exception as e:
        await message.reply(f"❌ {e}")

@dp.message(Command("размут"))
async def unmute_user(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ Нет прав!")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❗ /размут @ник")
        return
    
    try:
        member = await bot.get_chat_member(message.chat.id, args[1])
        
        if member.user.id in muted_users:
            del muted_users[member.user.id]
        
        await bot.restrict_chat_member(
            message.chat.id, member.user.id,
            permissions=types.ChatPermissions(can_send_messages=True)
        )
        await message.reply(f"🔊 {member.user.full_name} размучен!")
    except Exception as e:
        await message.reply(f"❌ {e}")

@dp.message(Command("инфо"))
async def user_info(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ Нет прав!")
        return
    
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    else:
        args = message.text.split()
        if len(args) < 2:
            await message.reply("❗ /инфо @ник")
            return
        try:
            member = await bot.get_chat_member(message.chat.id, args[1])
            user = member.user
        except:
            await message.reply(f"❌ Не найден!")
            return
    
    await message.reply(
        f"📝 ИНФО:\n\n"
        f"👤 {user.full_name}\n"
        f"🆔 {user.id}\n"
        f"📛 @{user.username if user.username else 'нет'}"
    )

@dp.message(Command("запрет"))
async def ban_word(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ Нет прав!")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❗ /запрет слово")
        return
    
    word = args[1].lower()
    if word not in banned_words:
        banned_words.append(word)
        await message.reply(f"✅ Слово '{word}' запрещено!")
    else:
        await message.reply(f"⚠️ Уже запрещено!")

@dp.message(Command("разрешить"))
async def unban_word(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ Нет прав!")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❗ /разрешить слово")
        return
    
    word = args[1].lower()
    if word in banned_words:
        banned_words.remove(word)
        await message.reply(f"✅ Слово '{word}' разрешено!")
    else:
        await message.reply(f"⚠️ Не найдено!")

@dp.message(Command("mods"))
async def mods_cmd(message: types.Message):
    mods = ["Зайчик", "Другая История", "Зайчик Змей"]
    await message.answer("📚 МОДЫ:\n\n" + "\n".join([f"• {m}" for m in mods]))

@dp.message(Command("stats"))
async def stats_cmd(message: types.Message):
    await message.answer(
        f"📊 СТАТИСТИКА:\n"
        f"💕 Шиппов: {len(shipped_couples)}\n"
        f"💍 Браков: {len(married_couples)}\n"
        f"🔞 Слов в бане: {len(banned_words)}\n"
        f"🔇 Замученных: {len(muted_users)}\n"
        f"💬 Статус: {'🟢 РАБОТАЮ' if bot_enabled else '🔴 ОТКЛЮЧЁН'}"
    )

@dp.message(Command("creator"))
async def creator_cmd(message: types.Message):
    await message.answer("👑 СОЗДАТЕЛЬ - ЛЕГЕНДА! 🔥")

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.reply(
        "🐍 КОМАНДЫ ЗМЕЯ:\n\n"
        "💕 ЛЮБОВЬ:\n"
        "/шиперить - Рандомный шипп\n"
        "/шипнуть @ник1 @ник2 - Конкретный шипп\n"
        "/шиппы - Все шиппы\n"
        "/женится @ник1 @ник2 - Поженить\n"
        "/развод @ник1 @ник2 - Развести\n"
        "/женатые - Все браки\n\n"
        "👑 АДМИН:\n"
        "/включить, /отключить, /статус\n"
        "/убрать @ник, /бан @ник\n"
        "/очистить N, /варн\n"
        "/мут @ник 10м, /размут @ник\n"
        "/запрет слово, /разрешить слово\n"
        "/инфо @ник, /myid\n\n"
        "📊 ДРУГОЕ:\n"
        "/mods, /stats, /creator, /ping, /help"
    )

# ========== ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ ==========
@dp.message(F.text)
async def handle_all_messages(message: types.Message):
    global bot_enabled, TARGET_USER_ID
    
    # ПРОВЕРЯЕМ НОВЫХ УЧАСТНИКОВ
    if message.new_chat_members:
        for member in message.new_chat_members:
            if member.id != bot.id:
                await message.reply(f"🐍 Добро пожаловать, {member.full_name}!")
        return
    
    if not bot_enabled:
        return
    
    user = message.from_user
    text = message.text.lower().strip() if message.text else ""
    
    # КОНТРОЛЬ НАД ВИТЕЙ
    if is_target_user(user.id, user.username, user.first_name):
        TARGET_USER_ID = user.id
        
        responses = [
            "Витя, не пиши ерунду! 😠",
            "тяви, прекрати! 👀",
            "@Zakuback, ты меня бесишь! 🤬",
            "Витя, иди учи уроки! 📚",
            "тяви, молчи уже! 🤐",
            "@Zakuback, заткнись! 🔇"
        ]
        
        special = {
            "привет": ["Витя, иди нафиг! 👋"],
            "как дела": ["Витя, а мне похер!"],
            "пока": ["Вали, Витя! 🚪"]
        }
        
        for key in special:
            if key in text:
                await message.reply(random.choice(special[key]))
                return
        
        await message.reply(random.choice(responses))
        return
    
    # ПРОВЕРКА НА МУТ
    if user.id in muted_users:
        if muted_users[user.id] > datetime.now():
            await message.delete()
            await message.answer(f"🔇 {user.full_name}, вы замучены!")
            return
        else:
            del muted_users[user.id]
    
    # ПРОВЕРКА НА ЗАПРЕЩЁННЫЕ СЛОВА
    for word in banned_words:
        if word in text:
            await message.delete()
            await message.answer(f"⚠️ {user.full_name}, слово '{word}' запрещено!")
            return
    
    # ОБЫЧНЫЕ ОТВЕТЫ
    answers = {
        "привет": ["Привет, зайка! 🐍", "Здарова! 👋"],
        "как дела": ["Норм, а у тебя?", "Отлично!"],
        "пока": ["Пока! 👋", "До встречи!"],
        "спасибо": ["Пожалуйста! 😊", "Не за что!"],
        "люблю": ["И я тебя люблю! 💖", "❤️"]
    }
    
    for key in answers:
        if key in text:
            await message.answer(random.choice(answers[key]))
            return
    
    # СЛУЧАЙНЫЙ ОТВЕТ (30% шанс)
    if random.random() < 0.3:
        extra = ["Интересно!", "Продолжай!", "Я слушаю!"]
        await message.answer(random.choice(extra))

# ========== ЗАПУСК ==========
async def main():
    print("=" * 60)
    print("🐍 ЗМЕЙ ЗАПУЩЕН!")
    print(f"👑 Админ ID: {REAL_ADMIN_ID}")
    print("🎯 Цель: Витя (@Zakuback, тяви)")
    print("📋 Команды: /help")
    print("=" * 60)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    asyncio.run(main())
