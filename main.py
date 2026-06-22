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

# ========== ХРАНИЛИЩЕ ДЛЯ ШИППЕРИНГА И СВАДЕБ ==========
shipped_couples = []  # Список шиппов
married_couples = []  # Список женатых пар

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

# ========== ДИАГНОСТИКА ==========
@dp.message(Command("myid"))
async def show_my_id(message: types.Message):
    user_id = message.from_user.id
    is_admin = await is_chat_admin(user_id, message.chat.id)
    await message.reply(
        f"👤 ТВОЙ ID: {user_id}\n"
        f"🔑 АДМИН? {is_admin}\n"
        f"📋 REAL_ADMIN_ID: {REAL_ADMIN_ID}\n"
        f"✅ СОВПАДАЕТ? {user_id == REAL_ADMIN_ID}\n"
        f"🤖 БОТ ВКЛЮЧЁН? {bot_enabled}"
    )

# ========== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ ПОЛЬЗОВАТЕЛЯ ==========
async def get_user_by_username(chat_id: int, username: str):
    """Получает пользователя по username"""
    try:
        # Убираем @ если есть
        username = username.replace("@", "")
        # Пробуем получить через get_chat_member
        try:
            member = await bot.get_chat_member(chat_id, f"@{username}")
            return member.user
        except:
            # Если не работает, пробуем через get_chat
            chat = await bot.get_chat(f"@{username}")
            return chat
    except Exception as e:
        raise Exception(f"Не могу найти пользователя @{username}")

# ========== КОМАНДЫ ШИППЕРИНГА (РАНДОМНЫЕ) ==========
@dp.message(Command("шиперить"))
async def ship_random(message: types.Message):
    """Рандомно шиперит двух пользователей из чата"""
    try:
        # Получаем список участников чата (исправленный способ)
        chat_members = []
        offset = 0
        limit = 100
        
        while True:
            try:
                # Используем правильный метод get_chat_members
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
                    
            except Exception as e:
                print(f"Ошибка получения участников: {e}")
                break
        
        # Если мало участников, используем администраторов
        if len(chat_members) < 3:
            admins = await bot.get_chat_administrators(message.chat.id)
            for admin in admins:
                if not admin.user.is_bot and admin.user not in chat_members:
                    chat_members.append(admin.user)
        
        if len(chat_members) < 2:
            await message.reply("😅 В чате太少 людей для шипперинга! Нужно минимум 2 человека.")
            return
        
        # Выбираем двух случайных разных пользователей
        user1, user2 = random.sample(chat_members, 2)
        
        # Проверяем, не являются ли они уже шиппом
        for ship in shipped_couples:
            if (ship["user1_id"] == user1.id and ship["user2_id"] == user2.id) or \
               (ship["user1_id"] == user2.id and ship["user2_id"] == user1.id):
                await message.reply(f"😏 {user1.full_name} и {user2.full_name} уже шипп! 🔥")
                return
        
        # Создаём шипп
        ship_names = [
            f"{user1.first_name}💕{user2.first_name}",
            f"{user1.first_name}❤️{user2.first_name}",
            f"{user1.first_name}🔥{user2.first_name}",
            f"{user1.first_name}⭐{user2.first_name}",
            f"{user1.first_name}🌈{user2.first_name}",
            f"{user1.first_name}💘{user2.first_name}",
            f"{user1.first_name}✨{user2.first_name}"
        ]
        ship_name = random.choice(ship_names)
        
        # Сохраняем шипп
        shipped_couples.append({
            "ship_name": ship_name,
            "user1_id": user1.id,
            "user1_name": user1.full_name,
            "user2_id": user2.id,
            "user2_name": user2.full_name,
            "date": datetime.now().strftime("%d.%m.%Y")
        })
        
        # Красивое сообщение
        messages = [
            f"🐍 ЗМЕЙ ШИППЕРИТ РАНДОМНО! 🎲\n\n💕 {user1.full_name} и {user2.full_name} - ИДЕАЛЬНАЯ ПАРА! 💕\n\nОни созданы друг для друга! 🔥\n\n💞 Название шиппа: {ship_name}",
            f"🎲 СЛУЧАЙНЫЙ ШИПП ОТ ЗМЕЯ! 🐍\n\n💞 {user1.full_name} + {user2.full_name} = ЛЮБОВЬ! 💞\n\nЭто судьба! 🌟\n\n🔥 Шипп: {ship_name}",
            f"🐍 ЗМЕЙ ВИДИТ ИСКРЫ МЕЖДУ:\n\n💗 {user1.full_name} 💗 {user2.full_name} 💗\n\nМежду ними определённо что-то есть! 😏\n\n{ship_name} - навсегда!",
            f"🎯 РАНДОМНЫЙ ШИПП! 🎯\n\n💖 {user1.full_name} 💖 {user2.full_name} 💖\n\nОни будут вместе! Так сказал Змей! 👑\n\n{ship_name} FOREVER!"
        ]
        
        await message.reply(random.choice(messages))
        
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

@dp.message(Command("шипнуть"))
async def ship_specific(message: types.Message):
    """Шиперит конкретных пользователей"""
    args = message.text.split()
    if len(args) < 3:
        await message.reply("❗ Использование: /шипнуть @ник1 @ник2\nПример: /шипнуть @Змей @Зайчик")
        return
    
    user1_name = args[1].replace("@", "")
    user2_name = args[2].replace("@", "")
    
    try:
        # Получаем пользователей
        user1 = await get_user_by_username(message.chat.id, user1_name)
        user2 = await get_user_by_username(message.chat.id, user2_name)
        
        # Проверяем существующий шипп
        for ship in shipped_couples:
            if (ship["user1_id"] == user1.id and ship["user2_id"] == user2.id) or \
               (ship["user1_id"] == user2.id and ship["user2_id"] == user1.id):
                await message.reply(f"😏 {user1.full_name} и {user2.full_name} уже шипп! 🔥")
                return
        
        ship_names = [
            f"{user1.full_name}💕{user2.full_name}",
            f"{user1.full_name}❤️{user2.full_name}",
            f"{user1.full_name}🔥{user2.full_name}",
            f"{user1.full_name}⭐{user2.full_name}",
            f"{user1.full_name}🌈{user2.full_name}"
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
            f"🐍 ЗМЕЙ ШИППНУЛ! 🐍\n\n"
            f"💕 {user1.full_name} и {user2.full_name} - ТЕПЕРЬ ШИПП! 💕\n\n"
            f"🔥 Название: {ship_name}"
        )
        
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

@dp.message(Command("шиппы"))
async def show_ships(message: types.Message):
    """Показывает все шиппы"""
    if not shipped_couples:
        await message.reply("😔 Пока нет ни одного шиппа!\n\nСоздай командой:\n/шиперить - рандомный шипп\n/шипнуть @ник1 @ник2 - конкретный шипп")
        return
    
    ships_list = "🐍 ВСЕ ШИППЫ ЗМЕЯ:\n\n"
    for i, ship in enumerate(shipped_couples, 1):
        ships_list += f"{i}. {ship['ship_name']} 💕\n"
        ships_list += f"   👤 {ship['user1_name']} + {ship['user2_name']}\n"
        ships_list += f"   📅 {ship['date']}\n\n"
    
    await message.reply(ships_list)

# ========== КОМАНДЫ СВАДЬБЫ (ПО ДВУМ НИКАМ) ==========
@dp.message(Command("женится"))
async def marry_users(message: types.Message):
    """Женит двух пользователей по никам"""
    args = message.text.split()
    if len(args) < 3:
        await message.reply("❗ Использование: /женится @ник1 @ник2\nПример: /женится @Змей @Зайчик")
        return
    
    user1_name = args[1].replace("@", "")
    user2_name = args[2].replace("@", "")
    
    try:
        # Получаем пользователей
        user1 = await get_user_by_username(message.chat.id, user1_name)
        user2 = await get_user_by_username(message.chat.id, user2_name)
        
        # Проверяем, не женаты ли уже
        for couple in married_couples:
            if (couple["user1_id"] == user1.id and couple["user2_id"] == user2.id) or \
               (couple["user1_id"] == user2.id and couple["user2_id"] == user1.id):
                await message.reply(f"😅 {user1.full_name} и {user2.full_name} уже женаты!")
                return
        
        # Сохраняем брак
        married_couples.append({
            "user1": user1_name,
            "user1_id": user1.id,
            "user1_full": user1.full_name,
            "user2": user2_name,
            "user2_id": user2.id,
            "user2_full": user2.full_name,
            "date": datetime.now().strftime("%d.%m.%Y")
        })
        
        # Поздравления
        congrats = [
            f"💍 СВАДЬБА! 💍\n\n{user1.full_name} и {user2.full_name} теперь МУЖ И ЖЕНА! 💑\n\nЗмей благословляет этот брак! 🐍✨\n\nЛюбви и счастья! ❤️",
            f"💞 СВЕРШИЛОСЬ! 💞\n\n{user1.full_name} и {user2.full_name} теперь СЕМЬЯ! 🏠\n\nЗмей рад за вас! 🐍\n\nСовет да любовь! ❤️",
            f"🎊 ЕЩЁ ОДНА СВАДЬБА! 🎊\n\n{user1.full_name} 💍 {user2.full_name}\n\nТеперь они вместе навсегда! 💕\n\nТак сказал Змей! 👑"
        ]
        
        await message.reply(random.choice(congrats))
        
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

@dp.message(Command("развод"))
async def divorce_users(message: types.Message):
    """Разводит двух пользователей"""
    args = message.text.split()
    if len(args) < 3:
        await message.reply("❗ Использование: /развод @ник1 @ник2\nПример: /развод @Змей @Зайчик")
        return
    
    user1_name = args[1].replace("@", "")
    user2_name = args[2].replace("@", "")
    
    # Ищем брак
    found = False
    for couple in married_couples:
        if (couple["user1"] == user1_name and couple["user2"] == user2_name) or \
           (couple["user1"] == user2_name and couple["user2"] == user1_name):
            married_couples.remove(couple)
            found = True
            break
    
    if not found:
        await message.reply(f"😅 {user1_name} и {user2_name} не состоят в браке!")
        return
    
    divorce_msgs = [
        f"💔 {user1_name} и {user2_name} развелись!\n\nЗмей грустит... но это их выбор! 🐍",
        f"😔 Брак {user1_name} и {user2_name} расторгнут!\n\nЗмей надеется, что вы найдёте счастье! 🌟",
        f"💀 {user1_name} и {user2_name} развелись!\n\nЗмей не судит! ❤️"
    ]
    
    await message.reply(random.choice(divorce_msgs))

@dp.message(Command("женатые"))
async def show_married(message: types.Message):
    """Показывает все браки"""
    if not married_couples:
        await message.reply("😔 Пока нет ни одной свадьбы! Создайте первую командой:\n/женится @ник1 @ник2")
        return
    
    married_list = "💍 ВСЕ БРАКИ ЗМЕЯ:\n\n"
    for i, couple in enumerate(married_couples, 1):
        married_list += f"{i}. {couple['user1_full']} 💍 {couple['user2_full']}\n"
        married_list += f"   📅 {couple['date']}\n\n"
    
    await message.reply(married_list)

# ========== КОМАНДЫ АДМИНИСТРИРОВАНИЯ ==========
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

@dp.message(Command("статус"))
async def status_bot(message: types.Message):
    if not await is_chat_admin(message.from_user.id, message.chat.id):
        await message.reply("❌ У тебя нет прав!")
        return
    status = "🟢 ВКЛЮЧЁН" if bot_enabled else "🔴 ОТКЛЮЧЁН"
    await message.reply(f"📊 СТАТУС БОТА: {status}")

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
            await asyncio.sleep(1)
            await bot.unban_chat_member(message.chat.id, user_id)
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
        await asyncio.sleep(1)
        await bot.unban_chat_member(message.chat.id, user_id)
        await message.reply(f"✅ {name} удалён из чата!")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

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
        
        await bot.restrict_chat_member(
            message.chat.id, user_id,
            permissions=types.ChatPermissions(can_send_messages=False)
        )
        
        await message.reply(f"🔇 {name} замучен на {text_time}!")
        
        async def auto_unmute():
            await asyncio.sleep(seconds)
            if user_id in muted_users and muted_users[user_id] <= datetime.now():
                try:
                    await bot.restrict_chat_member(
                        message.chat.id, user_id,
                        permissions=types.ChatPermissions(can_send_messages=True)
                    )
                    await message.answer(f"🔊 {name} размучен автоматически.")
                    del muted_users[user_id]
                except:
                    pass
        
        asyncio.create_task(auto_unmute())
            
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

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

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.reply(
        "🐍 КОМАНДЫ ЗМЕЯ:\n\n"
        "💕 ШИППЕРИНГ И СВАДЬБЫ:\n"
        "/шиперить - Рандомный шипп из чата 🎲\n"
        "/шипнуть @ник1 @ник2 - Шиппнуть конкретных\n"
        "/шиппы - Все шиппы\n"
        "/женится @ник1 @ник2 - Поженить двух\n"
        "/развод @ник1 @ник2 - Развести\n"
        "/женатые - Все браки\n\n"
        "👑 АДМИНИСТРИРОВАНИЕ:\n"
        "/включить - Включить бота\n"
        "/отключить - Выключить бота\n"
        "/статус - Статус бота\n"
        "/myid - Твой ID\n"
        "/убрать @ник - Кикнуть\n"
        "/бан @ник - Забанить\n"
        "/очистить N - Очистить\n"
        "/варн - Предупреждение\n"
        "/мут @ник время - Замутить\n"
        "/размут @ник - Снять мут\n"
        "/запрет слово - Запретить слово\n"
        "/разрешить слово - Разрешить\n"
        "/инфо @ник - Инфо\n\n"
        "📊 ИНФОРМАЦИЯ:\n"
        "/mods - Моды\n"
        "/stats - Статистика\n"
        "/creator - Создатель\n"
        "/ping - Пинг"
    )

@dp.message(Command("ping"))
async def ping(message: types.Message):
    start = datetime.now()
    msg = await message.answer("🏓 Понг...")
    end = datetime.now()
    latency = (end - start).total_seconds() * 1000
    await msg.edit_text(f"🏓 Понг! Задержка: {int(latency)}мс")

@dp.message(Command("mods"))
async def mods_cmd(message: types.Message):
    MODS = [
        "Зайчик", "Другая История", "Зайчик История Алисы",
        "Зайчик Зов Лесного Кошмара", "Зайчик Зазеркалье", "Зайчик Оковы Тьмы",
        "Зайчик Осколки Души", "Зайчик Мелодия Любви", "Зайчик Змей",
        "Зайчик Я не изгой", "Зайчик Направление Сердца", "Зайчик Овечья Шкура",
        "Зайчик Иной Финал", "Зайчик Равновесие", "Зайчик Путь Истины",
        "Зайчик Невысказанное", "Зайчик в Тумане", "Зайчик Лето"
    ]
    mods_list = "\n".join([f"• {m}" for m in MODS])
    await message.answer(f"📚 МОДЫ:\n\n{mods_list}")

@dp.message(Command("stats"))
async def stats_cmd(message: types.Message):
    MODS = [
        "Зайчик", "Другая История", "Зайчик История Алисы",
        "Зайчик Зов Лесного Кошмара", "Зайчик Зазеркалье", "Зайчик Оковы Тьмы",
        "Зайчик Осколки Души", "Зайчик Мелодия Любви", "Зайчик Змей",
        "Зайчик Я не изгой", "Зайчик Направление Сердца", "Зайчик Овечья Шкура",
        "Зайчик Иной Финал", "Зайчик Равновесие", "Зайчик Путь Истины",
        "Зайчик Невысказанное", "Зайчик в Тумане", "Зайчик Лето"
    ]
    await message.answer(
        f"📊 СТАТИСТИКА:\n"
        f"🐍 Модов: {len(MODS)}\n"
        f"🔞 Запрещённых слов: {len(banned_words)}\n"
        f"🔇 Замученных: {len(muted_users)}\n"
        f"💕 Шиппов: {len(shipped_couples)}\n"
        f"💍 Браков: {len(married_couples)}\n"
        f"💬 Статус: {'🟢 РАБОТАЮ' if bot_enabled else '🔴 ОТКЛЮЧЁН'}"
    )

@dp.message(Command("creator"))
async def creator_cmd(message: types.Message):
    await message.answer("👑 СОЗДАТЕЛЬ - ЛЕГЕНДА! 🔥")

# ========== ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ ==========
@dp.message(F.text)
async def handle_all_messages(message: types.Message):
    global bot_enabled, TARGET_USER_ID
    
    if not bot_enabled:
        return
    
    if message.new_chat_members:
        for member in message.new_chat_members:
            if member.id != bot.id:
                await message.reply(f"🐍 Добро пожаловать, {member.full_name}!")
        return
    
    user = message.from_user
    text = message.text.lower().strip() if message.text else ""
    
    # Контроль над Витей
    if is_target_user(user.id, user.username, user.first_name):
        TARGET_USER_ID = user.id
        
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
            "Витя, тебе заняться нечем? 💀"
        ]
        
        TARGET_SPECIAL = {
            "привет": ["Витя, иди нафиг! 👋", "тяви, не приветствуй меня!"],
            "как дела": ["Витя, а мне похер!", "тяви, не твое дело!"],
            "пока": ["Вали, Витя! 🚪", "иди нафиг, @Zakuback!"],
        }
        
        for key in TARGET_SPECIAL:
            if key in text:
                await message.reply(random.choice(TARGET_SPECIAL[key]))
                return
        
        await message.reply(random.choice(TARGET_RESPONSES))
        return
    
    # Проверка на мут
    if user.id in muted_users:
        if muted_users[user.id] > datetime.now():
            await message.delete()
            await message.answer(f"🔇 {user.full_name}, вы замучены и не можете писать!")
            return
        else:
            del muted_users[user.id]
    
    # Проверка на запрещённые слова
    for word in banned_words:
        if word in text:
            await message.delete()
            await message.answer(f"⚠️ {user.full_name}, слово '{word}' запрещено!")
            return
    
    # Обычные ответы
    MODS = [
        "Зайчик", "Другая История", "Зайчик История Алисы",
        "Зайчик Зов Лесного Кошмара", "Зайчик Зазеркалье", "Зайчик Оковы Тьмы",
        "Зайчик Осколки Души", "Зайчик Мелодия Любви", "Зайчик Змей",
        "Зайчик Я не изгой", "Зайчик Направление Сердца", "Зайчик Овечья Шкура",
        "Зайчик Иной Финал", "Зайчик Равновесие", "Зайчик Путь Истины",
        "Зайчик Невысказанное", "Зайчик в Тумане", "Зайчик Лето"
    ]
    
    for mod in MODS:
        if mod.lower() in text:
            await message.answer(f"О, {mod}! Классный мод! 🔥")
            return
    
    BASIC_ANSWERS = {
        "привет": ["Привет, зайка! 🐍", "Здарова, пушистый! 👋", "Приветик! 😊"],
        "как дела": ["Норм, а у тебя?", "Отлично, рассказывай!", "Хорошо, сам как?"],
        "пока": ["Пока, зайка! 👋", "До встречи!", "Пока-пока!"],
        "спасибо": ["Пожалуйста! 😊", "Не за что!", "Всегда рад помочь!"],
        "люблю": ["И я тебя люблю! 💖", "Ой, спасибо!"],
    }
    
    for key in BASIC_ANSWERS:
        if key in text:
            await message.answer(random.choice(BASIC_ANSWERS[key]))
            return
    
    EXTRA = [
        "Интересно! Продолжай!",
        "Я слушаю тебя! 👂",
        "Ну и что дальше?",
        "Расскажи подробнее!",
        "Змей внимает тебе!"
    ]
    if random.random() < 0.3:
        await message.answer(random.choice(EXTRA))

# ========== ЗАПУСК ==========
async def main():
    print("=" * 60)
    print("🐍 ЗМЕЙ ЗАПУЩЕН!")
    print(f"👑 Админ ID: {REAL_ADMIN_ID}")
    print("🎯 Цель: Витя (@Zakuback, тяви)")
    print("💕 Шипперинг: рандомный и по никам")
    print("💍 Свадьбы: по двум никам")
    print("📋 Команды: /help")
    print("=" * 60)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    asyncio.run(main())
