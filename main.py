import asyncio
import logging
import sqlite3
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

TOKEN = "8670073050:AAHb2D2WZ-q5dfIoH78jCqjCGzdT90dgFbo"

bot = Bot(token=TOKEN)
dp = Dispatcher()

def init_db():
    conn = sqlite3.connect("asham_games.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            balance REAL DEFAULT 0.0
        )
    ''')
    conn.commit()
    conn.close()

def register_user(user_id, username, full_name):
    conn = sqlite3.connect("asham_games.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, balance FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute(
            "INSERT INTO users (user_id, username, full_name, balance) VALUES (?, ?, ?, ?)",
            (user_id, username, full_name, 10.0)
        )
        conn.commit()
        conn.close()
        return 10.0
    
    conn.close()
    return 0.0

def get_user_balance(user_id):
    conn = sqlite3.connect("asham_games.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0.0

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="💰 ሒሳቤ (Balance)")
    builder.button(text="💳 ገንዘብ ገቢ ማድረግ")
    builder.button(text="🎮 ጨዋታዎች")
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    full_name = message.from_user.full_name
    
    bonus_given = register_user(user_id, username, full_name)
    balance = get_user_balance(user_id)
    
    if bonus_given > 0:
        welcome_text = (
            f"ሰላም ዮሐንስ! ወደ **Asham Games** በደህና መጡ። 🎮\n\n"
            f"እንኳን ደስ አለዎት! ለአዲስ ተመዝጋቢዎች የተዘጋጀው የ **10 ብር መጫወቻ ቦነስ** አካውንትዎ ላይ ተጭኗል። 🎁\n\n"
            f"አሁን ያለዎት ቀሪ ሂሳብ: **{balance} ብር**"
        )
    else:
        welcome_text = (
            f"እንኳን ደህና መጡ ዮሐንስ! ወደ **Asham Games** ተመልሰዋል። 🎮\n\n"
            f"አሁን ያለዎት ቀሪ ሂሳብ: **{balance} ብር**"
        )
    
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())

@dp.message(lambda message: message.text == "💰 ሒሳቤ (Balance)")
async def check_balance(message: types.Message):
    user_id = message.from_user.id
    balance = get_user_balance(user_id)
    await message.answer(f"💰 አሁን ያለዎት ቀሪ ሂሳብ: **{balance} ብር**", parse_mode="Markdown")

@dp.message(lambda message: message.text == "💳 ገንዘብ ገቢ ማድረግ")
async def deposit_handler(message: types.Message):
    await message.answer("💳 ገንዘብ ገቢ ለማድረግ እባክዎ በቴሌብር (Telebirr) ወይም በባንክ አካውንታችን ይጠቀሙ።", parse_mode="Markdown")

@dp.message(F.text == "🎮 ጨዋታዎች")
async def games_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Cash Games ጫወት (Play)", 
                    url="https://dash5.bet/en/casino?game=%2Fkeno5526&returnUrl=casino"
                )
            ]
        ]
    )
    await message.answer(
        "እንኳን ወደ **Asham Games** በደህና መጡ! 🚀\n\nከታች ያለውን አዝራር በመጫን ጨዋታዎቹን መጫወት መጀመር ይችላሉ፦",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def handle(request):
    return web.Response(text="Asham Games Bot is alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    init_db()
    logging.basicConfig(level=logging.INFO)
    print("Asham_games_bot በስኬት እየሰራ ነው...")
    
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
