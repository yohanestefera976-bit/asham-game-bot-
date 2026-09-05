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

# --- ዳታቤዝ ማዋቀር ---
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
    server_url = "https://asham-game-bot-3.onrender.com/"
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

# --- የውስጥ ዌብ ሰርቨር እና የፋስት ኬኖ ሚኒ አፕ (በቴሌግራም ዌብ አፕ የሚሰራ) ---
async def handle_keno_game(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="am">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Asham Fast Keno</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-900 text-white font-sans min-h-screen flex flex-col items-center justify-between p-3">

        <header class="w-full max-w-md flex justify-between items-center bg-slate-800 p-3 rounded-xl shadow-lg border border-slate-700">
            <div>
                <h1 class="text-lg font-bold text-yellow-400">⚡ FAST KENO</h1>
                <p class="text-[10px] text-slate-400">ፈጣን የኬኖ ዕጣ ጨዋታ</p>
            </div>
            <div class="bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-700">
                <span class="text-[10px] text-slate-400 block">ቀሪሂሳብ</span>
                <span id="balance" class="text-sm font-bold text-green-400">10.00 ብር</span>
            </div>
        </header>

        <main class="w-full max-w-md flex flex-col gap-3 my-2">
            
            <div class="bg-slate-800 p-3 rounded-xl shadow-lg border border-slate-700 flex flex-col items-center justify-center relative overflow-hidden">
                <div id="drawStatus" class="text-xs text-slate-400 mb-1">እባክዎ እስከ 10 ቁጥሮች ይምረጡ</div>
                <div id="drawnNumberDisplay" class="text-3xl font-extrabold text-yellow-400 tracking-wider">-</div>
                <div id="drawnCount" class="text-[10px] text-slate-500 mt-1">የወጡ ቁጥሮች: 0 / 20</div>
            </div>

            <div class="bg-slate-800 p-3 rounded-xl shadow-lg border border-slate-700">
                <div class="flex justify-between items-center mb-2">
                    <span class="text-xs font-semibold text-slate-300">ቁጥሮችን ይምረጡ (<span id="selected-count">0</span>/10)</span>
                    <button onclick="clearSelection()" class="text-xs text-red-400 hover:underline">አጽዳ (Clear)</button>
                </div>
                <div id="numberGrid" class="grid grid-cols-10 gap-1">
                    </div>
            </div>

            <div class="bg-slate-800 p-3 rounded-xl shadow-lg border border-slate-700 flex flex-col gap-2">
                <div class="flex justify-between items-center">
                    <span class="text-xs font-semibold text-slate-300">የውርርድ መጠን (ብር)</span>
                    <div class="flex gap-1">
                        <button onclick="setBet(2)" class="bet-btn bg-slate-700 px-2 py-1 rounded text-xs font-bold active-bet" id="bet-2">2</button>
                        <button onclick="setBet(5)" class="bet-btn bg-slate-700 px-2 py-1 rounded text-xs font-bold" id="bet-5">5</button>
                        <button onclick="setBet(10)" class="bet-btn bg-slate-700 px-2 py-1 rounded text-xs font-bold" id="bet-10">10</button>
                        <button onclick="setBet(20)" class="bet-btn bg-slate-700 px-2 py-1 rounded text-xs font-bold" id="bet-20">20</button>
                    </div>
                </div>
                <input type="hidden" id="betAmount" value="2">

                <button id="playBtn" onclick="startKenoGame()" class="w-full bg-yellow-500 hover:bg-yellow-400 text-slate-950 font-bold py-2.5 rounded-lg shadow-lg text-sm transition duration-200">
                    ⚡ ፈጣን ጨዋታ ጀምር (PLAY)
                </button>
            </div>

            <div class="bg-slate-800 p-3 rounded-xl shadow-lg border border-slate-700 flex flex-col gap-1">
                <span class="text-[11px] font-semibold text-slate-400">ያለፉት ውጤቶች (History)</span>
                <div id="historyList" class="flex flex-col gap-1 max-h-24 overflow-y-auto text-[11px] text-slate-300">
                    <span class="text-slate-500 italic">ምንም የለም</span>
                </div>
            </div>

        </main>

        <footer class="text-[10px] text-slate-500 text-center">
            &copy; 2026 Asham Fast Keno. ሁሉንም መብቶች የተጠበቁ ናቸው።
        </footer>

        <script>
            let tg = window.Telegram.WebApp;
            tg.expand();

            let balance = 10.0;
            let selectedNumbers = [];
            let isPlaying = false;
            let currentBet = 2.0;
            const maxSelection = 10;

            // Initialize Grid
            const gridContainer = document.getElementById('numberGrid');
            for (let i = 1; i <= 80; i++) {
                const btn = document.createElement('button');
                btn.innerText = i;
                btn.id = `num-${i}`;
                btn.className = "bg-slate-700 hover:bg-slate-600 text-[11px] font-bold py-1.5 rounded flex items-center justify-center text-slate-200 transition-all";
                btn.onclick = () => toggleNumber(i);
                gridContainer.appendChild(btn);
            }

            function setBet(amount) {
                if (isPlaying) return;
                currentBet = amount;
                document.getElementById('betAmount').value = amount;
                document.querySelectorAll('.bet-btn').forEach(b => {
                    b.classList.remove('bg-yellow-500', 'text-slate-950', 'active-bet');
                    b.classList.add('bg-slate-700');
                });
                let activeBtn = document.getElementById(`bet-${amount}`);
                activeBtn.classList.remove('bg-slate-700');
                activeBtn.classList.add('bg-yellow-500', 'text-slate-950', 'active-bet');
            }

            // Set default active bet style
            document.getElementById('bet-2').classList.replace('bg-slate-700', 'bg-yellow-500');
            document.getElementById('bet-2').classList.add('text-slate-950');

            function toggleNumber(num) {
                if (isPlaying) return;
                const index = selectedNumbers.indexOf(num);
                const btn = document.getElementById(`num-${num}`);

                if (index > -1) {
                    selectedNumbers.splice(index, 1);
                    btn.className = "bg-slate-700 hover:bg-slate-600 text-[11px] font-bold py-1.5 rounded flex items-center justify-center text-slate-200 transition-all";
                } else {
                    if (selectedNumbers.length >= maxSelection) {
                        alert("ከ 10 በላይ ቁጥሮች መምረጥ አይችሉም!");
                        return;
                    }
                    selectedNumbers.push(num);
                    btn.className = "bg-yellow-500 text-slate-950 text-[11px] font-bold py-1.5 rounded flex items-center justify-center shadow transition-all";
                }
                document.getElementById('selected-count').innerText = selectedNumbers.length;
            }

            function clearSelection() {
                if (isPlaying) return;
                selectedNumbers.forEach(num => {
                    const btn = document.getElementById(`num-${num}`);
                    btn.className = "bg-slate-700 hover:bg-slate-600 text-[11px] font-bold py-1.5 rounded flex items-center justify-center text-slate-200 transition-all";
                });
                selectedNumbers = [];
                document.getElementById('selected-count').innerText = '0';
            }

            function updateBalance(amount) {
                balance += amount;
                document.getElementById('balance').innerText = balance.toFixed(1) + " ብር";
            }

            // Game Simulation Logic (Fast Keno Style)
            function startKenoGame() {
                if (selectedNumbers.length === 0) {
                    alert("እባክዎ መጀመሪያ ቢያንስ አንድ ቁጥር ይምረጡ!");
                    return;
                }
                if (currentBet > balance) {
                    alert("በቂ ቀሪ ሂሳብ የለዎትም!");
                    return;
                }

                updateBalance(-currentBet);
                isPlaying = true;
                let playBtn = document.getElementById('playBtn');
                playBtn.disabled = true;
                playBtn.classList.add('opacity-50');

                // Reset previous grid states
                for (let i = 1; i <= 80; i++) {
                    let b = document.getElementById(`num-${i}`);
                    b.classList.remove('bg-red-500', 'bg-green-500', 'text-white', 'text-slate-950');
                    if (selectedNumbers.includes(i)) {
                        b.className = "bg-yellow-500 text-slate-950 text-[11px] font-bold py-1.5 rounded flex items-center justify-center shadow";
                    } else {
                        b.className = "bg-slate-700 text-[11px] font-bold py-1.5 rounded flex items-center justify-center text-slate-200";
                    }
                }

                let drawnNumbers = [];
                while (drawnNumbers.length < 20) {
                    let r = Math.floor(Math.random() * 80) + 1;
                    if (drawnNumbers.indexOf(r) === -1) drawnNumbers.push(r);
                }

                let drawIndex = 0;
                document.getElementById('drawStatus').innerText = "⚡ ፈጣን ዕጣ እየወጣ ነው...";

                let drawInterval = setInterval(() => {
                    if (drawIndex < drawnNumbers.length) {
                        let currentNum = drawnNumbers[drawIndex];
                        document.getElementById('drawnNumberDisplay').innerText = currentNum;
                        document.getElementById('drawnCount').innerText = `የወጡ ቁጥሮች: ${drawIndex + 1} / 20`;

                        let btn = document.getElementById(`num-${currentNum}`);
                        if (selectedNumbers.includes(currentNum)) {
                            btn.className = "bg-green-500 text-slate-950 text-[11px] font-bold py-1.5 rounded flex items-center justify-center shadow-lg animate-pulse";
                        } else {
                            btn.className = "bg-red-500 text-white text-[11px] font-bold py-1.5 rounded flex items-center justify-center";
                        }

                        drawIndex++;
                    } else {
                        clearInterval(drawInterval);
                        calculateResults(drawnNumbers);
                    }
                }, 50); // Fast Keno Speed (50ms)
            }

            function calculateResults(drawnNumbers) {
                let hits = selectedNumbers.filter(num => drawnNumbers.includes(num)).length;
                let winAmount = hits * currentBet; // ለእያንዳንዱ የገጠመ ቁጥር የውርርድ መጠኑን ያህል

                if (winAmount > 0) {
                    updateBalance(winAmount);
                    document.getElementById('drawStatus').innerHTML = `<span class="text-green-400 font-bold">🎉 አሸንፈዋል! ${hits} ገጥመዋል (+${winAmount.toFixed(1)} ብር)</span>`;
                } else {
                    document.getElementById('drawStatus').innerHTML = `<span class="text-red-400 font-bold">❌ ምንም ቁጥር አልገጠመም። እንደገና ይሞክሩ!</span>`;
                }

                // Add to history
                let historyList = document.getElementById('historyList');
                if (historyList.children[0] && historyList.children[0].classList.contains('italic')) {
                    historyList.innerHTML = '';
                }
                let historyItem = document.createElement('div');
                historyItem.className = `flex justify-between p-1 rounded ${winAmount > 0 ? 'bg-green-900/40 text-green-300' : 'bg-slate-900 text-slate-400'}`;
                historyItem.innerHTML = `<span>ገጠመ: ${hits}/10</span><span>${winAmount > 0 ? '+' + winAmount.toFixed(1) + ' ብር' : '0.0 ብር'}</span>`;
                historyList.prepend(historyItem);

                // Auto-clear selection for next round (Fast Keno style)
                selectedNumbers = [];
                document.querySelectorAll('.number-btn').forEach(b => {
                    b.className = "bg-slate-700 hover:bg-slate-600 text-[11px] font-bold py-1.5 rounded flex items-center justify-center text-slate-200 transition-all";
                });
                document.getElementById('selected-count').innerText = '0';

                isPlaying = false;
                let playBtn = document.getElementById('playBtn');
                playBtn.disabled = false;
                playBtn.classList.remove('opacity-50');
            }
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type="text/html")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle_keno_game)
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
  
