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

TOKEN = "8670073050:AAHb2D2WZ-q5dfIoH78jCqjCGzdT90dgFbo"
ADMIN_ID = 7131094446  # የዮሐንስ አድሚን ID

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- ዳታቤዝ ማዋቀር (Database Setup) ---
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
            f"ለመመዝገብ እና የ 10 ብር ቦነስዎን ለመቀበል እባክዎ ከታች ያለውን አዝራር በመጫን ስልክ ቁጥርዎን ያጋሩ:",
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
        "✅ <b>ምዝገባ ተጠናቋል!</b>\n\n"
        "እንኳን ደስ አለዎት! ለአዲስ ተመዝጋቢዎች የተዘጋጀው የ <b>10 ብር</b> ጨዋታ ቦነስ አካውንትዎ ላይ ተጨምሯል። 🎁\n\n"
        "ከታች ካሉት አማራጮች የሚፈልጉትን ይምረጡ:",
        parse_mode="HTML",
        reply_markup=get_main_menu(),
    )

# --- የሜኑ ትዕዛዞች ---
@dp.message(F.text == "💰 ሐሳብ (Balance)")
async def menu_balance(message: types.Message):
    user_data = get_user_balance(message.from_user.id)
    balance = user_data[0] if user_data else 10.0
    await message.answer(f"💰 አሁን ያለዎት ቀሪ ሒሳብ: <b>{balance} ብር</b>", parse_mode="HTML")

@dp.message(F.text == "💳 ገንዘብ ገቢ ማድረግ")
async def menu_deposit(message: types.Message):
    await message.answer("💳 <b>ገንዘብ ገቢ ለማድረግ:</b> እባክዎ በአስተዳዳሪው በኩል በባንክ ወይም በቴሌብር ያስተላልፉ።", parse_mode="HTML")

@dp.message(F.text == "💸 ገንዘብ ማውጣት (Withdraw)")
async def menu_withdraw(message: types.Message):
    await message.answer("💸 <b>ገንዘብ ማውጣት:</b> ማውጣት የሚፈልጉትን መጠን ለአድሚን ያሳውቁ።", parse_mode="HTML")

@dp.message(F.text == "🎮 ጨዋታዎች")
async def menu_games(message: types.Message):
    # እዚህ ጋር የራሰህን የ Render ሊንክ ታስገባለህ (ምሳሌ: https://your-app-name.onrender.com/keno)
    server_url = "https://YOUR-RENDER-APP-URL.onrender.com/keno"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 የኬኖ ጨዋታውን ክፈት", web_app=WebAppInfo(url=server_url))]
        ]
    )
    await message.answer("🎮 ከታች ያለውን ቁልፍ በመጫን የኬኖ ጨዋታውን በቀጥታ መጫወት ይችላሉ፦", reply_markup=keyboard)

@dp.message(F.text == "🛠️ ቴክለማ ሳፖርት (Support)")
async def menu_support(message: types.Message):
    await message.answer("🛠️ ማንኛውም ጥያቄ ካለዎት እዚህ ጋር ማግኘት ይችላሉ።")

# --- አድሚን ብሮድካስት ---
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

# --- የውስጥ ዌብ ሰርቨር እና የኬኖ ሚኒ አፕ (Internal Mini App Server) ---
async def handle_home(request):
    return web.Response(text="Bot is running!")

async def handle_keno_game(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="am">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Asham Keno Mini App</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #0f172a;
                color: #ffffff;
                text-align: center;
                padding: 20px;
                margin: 0;
            }
            h1 { color: #f59e0b; margin-bottom: 5px; }
            .balance-box {
                background: #1e293b;
                padding: 10px 20px;
                border-radius: 10px;
                display: inline-block;
                margin: 15px 0;
                font-size: 18px;
                border: 1px solid #334155;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(8, 1fr);
                gap: 8px;
                max-width: 400px;
                margin: 20px auto;
            }
            .number-btn {
                background-color: #334155;
                color: white;
                border: none;
                padding: 12px 0;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                cursor: pointer;
                transition: 0.2s;
            }
            .number-btn.selected {
                background-color: #f59e0b;
                color: #0f172a;
            }
            .play-btn {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
                cursor: pointer;
                margin-top: 20px;
                width: 100%;
                max-width: 400px;
            }
            .play-btn:hover { background-color: #059669; }
        </style>
    </head>
    <body>
        <h1>🎲 Asham Keno</h1>
        <p>ቁጥሮችዎን ይምረጡ እና ዕድልዎን ይሞክሩ!</p>
        
        <div class="balance-box">
            ቀሪ ሒሳብ: <span id="user-balance">10.0</span> ብር
        </div>

        <div class="grid" id="keno-grid"></div>

        <button class="play-btn" onclick="playGame()">ጨዋታውን ጀምር (Bet)</button>

        <script>
            let tg = window.Telegram.WebApp;
            tg.expand();

            let selectedNumbers = [];
            const grid = document.getElementById('keno-grid');

            for (let i = 1; i <= 80; i++) {
                let btn = document.createElement('button');
                btn.className = 'number-btn';
                btn.innerText = i;
                btn.onclick = () => toggleNumber(i, btn);
                grid.appendChild(btn);
            }

            function toggleNumber(num, btn) {
                if (selectedNumbers.includes(num)) {
                    selectedNumbers = selectedNumbers.filter(n => n !== num);
                    btn.classList.remove('selected');
                } else {
                    if (selectedNumbers.length >= 10) {
                        alert('ከ 10 በላይ ቁጥሮች መምረጥ አይችሉም!');
                        return;
                    }
                    selectedNumbers.push(num);
                    btn.classList.add('selected');
                }
            }

            function playGame() {
                if (selectedNumbers.length === 0) {
                    alert('እባክዎ ቢያንስ አንድ ቁጥር ይምረጡ!');
                    return;
                }
                alert('ዕጣ እየተወጣ ነው... መልካም ዕድል!');
            }
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type="text/html")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle_home)
    app.router.add_get("/keno", handle_keno_game)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

async def main():
    asyncio.create_task(web_server())
    app_task = asyncio.create_task(dp.start_polling(bot))
    await app_task

if __name__ == "__main__":
    asyncio.run(main())
                               
