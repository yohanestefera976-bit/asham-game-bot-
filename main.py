import logging
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
import asyncio
from aiohttp import web

# ሎጊንግ ማስተካከል
logging.basicConfig(level=logging.INFO)

# የዮሐንስ ቦት ቶከን
TOKEN = "8670073050:AAHb2D2WZ-q5dfIoH78jCqjCGzdT90dgFbo"
ADMIN_ID = 7131094446  # የዮሐንስ አድሚን ID
WEB_APP_URL = "https://dash5.bet/en/casino?game=%2Fkeno5526&returnUrl=casino"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- ዳልቤዝ ማዋቀር (Database Setup) ---
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            phone_number TEXT,
            balance REAL DEFAULT 10.0,
            referred_by INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

def add_user_initial(user_id: int, username: str, referred_by: int = None):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    existing = cursor.fetchone()
    if not existing:
        cursor.execute(
            "INSERT INTO users (user_id, username, balance, referred_by) VALUES (?, ?, 10.0, ?)",
            (user_id, username, referred_by),
        )
        conn.commit()
    conn.close()

def update_user_phone(user_id: int, phone: str):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET phone_number = ? WHERE user_id = ?", (phone, user_id))
    conn.commit()
    conn.close()

def get_user_balance(user_id: int):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance, phone_number FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_total_users():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_all_user_ids():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

# --- ቋሚ ምናሌዎች (Reply Keyboards) ---
def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💰 ሐሳብ (Balance)"),
                KeyboardButton(text="💳 ገንዘብ ገቢ ማድረግ"),
            ],
            [
                KeyboardButton(text="💸 ገንዘብ ማውጣት (Withdraw)"),
                KeyboardButton(text="🎮 ጨዋታዎች"),
            ],
            [
                KeyboardButton(text="🛠️ ቴክለማ ሳፖርት (Support)"),
            ],
        ],
        resize_keyboard=True,
    )

# --- የ /start ትዕዛዝ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    args = message.text.split()
    
    referred_by = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            ref_id = int(args[1].replace("ref_", ""))
            if ref_id != user_id:
                referred_by = ref_id
        except ValueError:
            pass

    add_user_initial(user_id, username, referred_by)

    user_data = get_user_balance(user_id)
    if user_data and user_data[1]:
        await message.answer(
            f"ሰላም <b>{message.from_user.first_name}</b>! እንደገና እንኳን ደህና መጡ። 🎮",
            parse_mode="HTML",
            reply_markup=get_main_menu(),
        )
    else:
        phone_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 ስልክ ቁጥር አጋራ (Share Contact)", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await message.answer(
            f"ሰላም <b>{message.from_user.first_name}</b>! ወደ Asham Games በደህና መጡ። 🎮\n\n"
            f"ለመመዝገብ እና ሽልማቱን ሙሉ በሙሉ ለመጠቀም እባክዎ ከታች ያለውን አዝራር በመጫጭ ስልክ ቁጥርዎን ያጋሩ:",
            parse_mode="HTML",
            reply_markup=phone_keyboard,
        )

# --- ስልክ ቁጥር መቀበል ---
@dp.message(F.contact)
async def handle_contact(message: types.Message):
    user_id = message.from_user.id
    phone = message.contact.phone_number
    update_user_phone(user_id, phone)

    await message.answer(
        "✅ <b>ምዝገባም ተጠናቀዋል!</b>\n\n"
        "እንዳን ደስ አለዎት! ለአዲስ ተመዝጋቢዎች የተዘጋጀው የ <b>10 ብር</b> ጨዋታ ቦነስ አካውንትዎ ላይ ተጨምሯል። 🎁\n\n"
        "ከታች ካሉት አማራጮች የሚፈልጉትን ይምረጡ:",
        parse_mode="HTML",
        reply_markup=get_main_menu(),
    )

# --- የሜኑ አዝራሮች ትዕዛዞች ---
@dp.message(F.text == "💰 ሐሳብ (Balance)")
async def menu_balance(message: types.Message):
    user_data = get_user_balance(message.from_user.id)
    balance = user_data[0] if user_data else 10.0
    await message.answer(f"💰 አሁን ያለዎት ቀሪ ሒሳብ: <b>{balance} ብር</b>", parse_mode="HTML")

@dp.message(F.text == "💳 ገንዘብ ገቢ ማድረግ")
async def menu_deposit(message: types.Message):
    await message.answer(
        "💳 <b>ገንዘብ ገቢ ለማድረግ:</b>\n\n"
        "እባክዎ በቴሌግራም ሚኒ አፕ (Mini App) ውስጥ በመግባት በባንክ ወይም በቴሌብር (Telebirr) ገቢ ያድርጉ።",
        parse_mode="HTML",
    )

@dp.message(F.text == "💸 ገንዘብ ማውጣት (Withdraw)")
async def menu_withdraw(message: types.Message):
    await message.answer(
        "💸 <b>ገንዘብ ማውጣት:</b>\n\n"
        "እባክዎ ማውጣት የሚፈልጉትን መጠን እና የባንክ/የቴሌብር አካውንት መረጃዎን ለአስተዳዳሪው (Support) ያጋሩ።",
        parse_mode="HTML",
    )

@dp.message(F.text == "🎮 ጨዋታዎች")
async def menu_games(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 ኬኖ ጨዋታውን ክፈት", web_app=WebAppInfo(url=WEB_APP_URL))]
        ]
    )
    await message.answer("🎮 ከታች ያለውን በመጫን በቀጥታ የኬኖ ጨዋታውን መጫወት ይችላሉ፦", reply_markup=keyboard)

@dp.message(F.text == "🛠️ ቴክለማ ሳፖርት (Support)")
async def menu_support(message: types.Message):
    await message.answer("🛠️ ማንኛውም ጥያቄ ወይም እገዛ ከፈለጉ በዚሁ ቦት በኩል ማግኘት ይችላሉ። አድሚናችን ፈጣን ምላሽ ይሰጣሉ።")

# --- አድሚን ብሮድካስት (Broadcast) ---
@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    text_to_broadcast = message.text.replace("/broadcast", "").strip()
    if not text_to_broadcast:
        await message.answer("እባክዎ መላክ የሚፈልጉትን መልእክት አብረው ይጻፉ!")
        return

    users = get_all_user_ids()
    success = 0
    status_msg = await message.answer(f"📢 መልእክቱ ለ {len(users)} ተጠቃሚዎች እየተላለፈ ነው...")

    for uid in users:
        try:
            await bot.send_message(uid, text_to_broadcast)
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await status_msg.edit_text(f"✅ ብሮድካስት ተጠናቋል። የተሳካ: {success}")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    total = get_total_users()
    await message.answer(f"📊 አጠቃላይ የተመዝጋቢዎች ብዛት: <b>{total}</b>", parse_mode="HTML")

# --- ዌብ ሰርቨር (Render እንዲቆይ) ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

async def main():
    asyncio.create_task(web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
