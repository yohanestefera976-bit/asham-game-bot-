import asyncio
import logging
import sqlite3
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8670073050:AAHb2D2WZ-q5dfIoH78jCqjCGzdT90dgFbo"
ADMIN_ID = 888546281  # አድሚን (ዮሐንስ) ቴሌግራም ID

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class DepositStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_tx_id = State()

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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            tx_id TEXT,
            status TEXT DEFAULT 'PENDING'
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

def update_user_balance(user_id, amount):
    conn = sqlite3.connect("asham_games.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="💰 ሒሳቤ (Balance)")
    builder.button(text="💳 ገንዘብ ገቢ ማድረግ")
    builder.button(text="🎮 ጨዋታዎች")
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
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

@dp.message(F.text == "💰 ሒሳቤ (Balance)")
async def check_balance(message: types.Message):
    user_id = message.from_user.id
    balance = get_user_balance(user_id)
    await message.answer(f"💰 አሁን ያለዎት ቀሪ ሂሳብ: **{balance} ብር**", parse_mode="Markdown")

@dp.message(F.text == "💳 ገንዘብ ገቢ ማድረግ")
async def deposit_handler(message: types.Message, state: FSMContext):
    await state.set_state(DepositStates.waiting_for_amount)
    await message.answer(
        "💳 **ገንዘብ ገቢ ማድረግ**\n\n"
        "ወደ አካውንትዎ ማስገባት የሚፈልጉትን የብር መጠን ይጻፉ (ለምሳሌ: 100):",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )

@dp.message(DepositStates.waiting_for_amount)
async def process_deposit_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ እባክዎ ትክክለኛ ቁጥር ብቻ ይጻፉ (ለምሳሌ: 100):")
        return
    
    await state.update_data(amount=float(message.text))
    await state.set_state(DepositStates.waiting_for_tx_id)
    
    deposit_info = (
        "💳 **የክፍያ መዋቢያዎች (Payment Details)**\n\n"
        "እባክዎ ከታች ባለው አካውንት ገንዘቡን ያስተላልፉ፦\n"
        "• **ቴሌብር (Telebirr):** `0993727789` (በዮሐንስ)\n\n"
        "ገንዘቡን ካስተላለፉ በኋላ የትራንዛክሽን ቁጥሩን (Transaction ID / UTR) በዚህ ቦት ላይ ይጻፉልን:"
    )
    await message.answer(deposit_info, parse_mode="Markdown")

@dp.message(DepositStates.waiting_for_tx_id)
async def process_deposit_tx(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    amount = user_data.get("amount")
    tx_id = message.text
    user = message.from_user
    
    conn = sqlite3.connect("asham_games.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO deposits (user_id, amount, tx_id, status) VALUES (?, ?, ?, ?)",
        (user.id, amount, tx_id, 'PENDING')
    )
    dep_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    await state.clear()
    await message.answer(
        "✅ **ጥያቄዎ ለአድሚን ተልኳል!**\n\n"
        "ክፍያዎ በአጭር ጊዜ ውስጥ ተረጋግጦ ሂሳብዎ ላይ ይጨመራል። እናመሰግናለን!",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )
    
    # ለአድሚን (ለዮሐንስ) ማሳወቂያ መላክ
    admin_text = (
        "🔔 **አዲስ የገንዘብ ገቢ ጥያቄ መጥቷል!**\n\n"
        f"👤 ተጠቃሚ: {user.full_name} (@{user.username or 'የሌለው'})\n"
        f"🆔 ID: `{user.id}`\n"
        f"💵 መጠን: **{amount} ብር**\n"
        f"🧾 <b>ትራንዛክሽን ቁጥር:</b> <code>{tx_id}</code>"
    )
    
    admin_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ አረጋግጥ (Approve)", callback_data=f"approve_{dep_id}_{user.id}_{amount}"),
                InlineKeyboardButton(text="❌ ውድቅ አድርግ (Reject)", callback_data=f"reject_{dep_id}")
            ]
        ]
    )
    
    try:
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML", reply_markup=admin_kb)
    except Exception as e:
        logging.error(f"Error sending admin notification: {e}")

# --- የአድሚን ማረጋገጫ (Callback Query Handler) ---
@dp.callback_query(F.data.startswith("approve_"))
async def approve_deposit(callback: types.CallbackData):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("ይህንን ትዕዛዝ ለመፈጸም ፈቃድ አለዎት!", show_alert=True)
        return
    
    parts = callback.data.split("_")
    dep_id = parts[1]
    target_user_id = int(parts[2])
    amount = float(parts[3])
    
    # ዳታቤዝ ማሻሻል
    conn = sqlite3.connect("asham_games.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE deposits SET status = 'APPROVED' WHERE id = ?", (dep_id,))
    conn.commit()
    conn.close()
    
    # የተጠቃሚውን ሂሳብ መጨመር
    update_user_balance(target_user_id, amount)
    new_balance = get_user_balance(target_user_id)
    
    # ለአድሚን ማሳወቅ
    await callback.message.edit_text(f"{callback.message.text}\n\n✅ **ሁኔታ:** ጸድቋል (Approved)")
    await callback.answer("ክፍያው በትክክል ጸድቋል!")
    
    # ለተጠቃሚው ማሳወቅ
    try:
        await bot.send_message(
            target_user_id,
            f"🎉 **መልካም ዜና!**\n\n"
            f"የላኩት የ {amount} ብር ክፍያ በአድሚን ጸድቋል!\n"
            f"💰 አዲስ ቀሪ ሂሳብዎ: **{new_balance} ብር**\n\n"
            f"አሁን ጨዋታውን መጫወት ይችላሉ!",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Error notifying user: {e}")

@dp.callback_query(F.data.startswith("reject_"))
async def reject_deposit(callback: types.CallbackData):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("ፈቃድ የለዎትም!", show_alert=True)
        return
    
    dep_id = callback.data.split("_")[1]
    
    conn = sqlite3.connect("asham_games.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE deposits SET status = 'REJECTED' WHERE id = ?", (dep_id,))
    conn.commit()
    conn.close()
    
    await callback.message.edit_text(f"{callback.message.text}\n\n❌ **ሁኔታ:** ውድቅ ተደርጓል (Rejected)")
    await callback.answer("ጥያቄው ውድቅ ተደርጓል።")

@dp.message(F.text == "🎮 ጨዋታዎች")
async def games_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Cash Games ጫወት (Play)", 
                    web_app=types.WebAppInfo(url="https://dash5.bet/en/casino?game=%2Fkeno5526&returnUrl=casino")
                )
            ]
        ]
    )
    await message.answer(
        "እንኳን ወደ **Asham Games** በደህና መጡ! 🚀\n\nከታች ያለውን አዝራር በመጫን ጨዋታዎቹን በቀጥታ በቦታችን ውስጥ መጫወት መጀመር ይችላሉ፦",
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
  
