import logging
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# ሎጊንግ ማስተካከል
logging.basicConfig(level=logging.INFO)

TOKEN = "8670073050:AAHb2D2WZ-q5dfIoH78jCqjCGzdT90dgFbo"
ADMIN_ID = 7131094446

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- ዳታቤዝ ማዋቀር ---
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            phone_number TEXT,
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
            "INSERT INTO users (user_id, username, referred_by) VALUES (?, ?, ?)",
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

def get_all_user_ids():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

# --- ቋሚ ምናሌዎች ---
def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💳 ገንዘብ ገቢ ማድረግ"),
                KeyboardButton(text="🛠️ ቴክለማ ሳፖርት (Support)"),
            ],
        ],
        resize_keyboard=True,
    )

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

    phone_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 ስልክ ቁጥር አጋራ (Share Contact)", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    
    await message.answer(
        f"ሰላም <b>{message.from_user.first_name}</b>!\n\n"
        f"እንኳን ወደ ክፍያ ማዕከል በደህና መጡ። 💳✨\n\n"
        f"አገልግሎቱን ለመጀመር እባክዎ ከታች ያለውን አዝራር በመጫን ስልክ ቁጥርዎን ያጋሩ:",
        parse_mode="HTML",
        reply_markup=phone_keyboard,
    )

@dp.message(F.contact)
async def handle_contact(message: types.Message):
    user_id = message.from_user.id
    phone = message.contact.phone_number
    update_user_phone(user_id, phone)

    await message.answer(
        "✅ <b>ምዝገባ ተጠናቋል!</b>\n\n"
        "💳 <b>ገንዘብ ገቢ ለማድረግ:</b>\n\n"
        "እባክዎ ከታች ባለው የቴሌብር ቁጥር ገንዘብ ያስተላልፉ:\n\n"
        "📱 <b>ቴሌብር:</b> <code>0998257988</code>\n"
        "👤 <b>ስም:</b> ዮሃንስ\n"
        "⚠️ <b>ዝቅተኛው ዲፖዚት መጠን:</b> 200 ብር\n\n"
        "ገንዘብ ካስተላለፉ በኋላ የደረሰኝ ስክሪንሾት (Screenshot) ለአድሚን በመላክ ማረጋገጥ ይችላሉ።",
        parse_mode="HTML",
        reply_markup=get_main_menu(),
    )

@dp.message(F.text == "💳 ገንዘብ ገቢ ማድረግ")
async def menu_deposit(message: types.Message):
    await message.answer(
        "💳 <b>ገንዘብ ገቢ ለማድረግ:</b>\n\n"
        "እባክዎ ከታች ባለው የቴሌብር ቁጥር ገንዘብ ያስተላልፉ:\n\n"
        "📱 <b>ቴሌብር:</b> <code>0998257988</code>\n"
        "👤 <b>ስም:</b> ዮሃንስ\n"
        "⚠️ <b>ዝቅተኛው ዲፖዚት መጠን:</b> 200 ብር\n\n"
        "ገንዘብ ካስተላለፉ በኋላ የደረሰኝ ስክሪንሾት (Screenshot) ለአድሚን በመላክ ማረጋገጥ ይችላሉ።",
        parse_mode="HTML"
    )

@dp.message(F.text == "🛠️ ቴክለማ ሳፖርት (Support)")
async def menu_support(message: types.Message):
    await message.answer("🛠️ ማንኛውም ጥያቄ ወይም እርዳታ ካለዎት ለአድሚን ማሳወቅ ይችላሉ።")

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

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
  
