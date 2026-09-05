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
            balance REAL DEFAULT 10.15,
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
            "INSERT INTO users (user_id, username, balance, referred_by) VALUES (?, ?, 10.15, ?)",
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
    return row if row else (10.15, None)

def update_db_balance(user_id: int, new_balance: float):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
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
            f"ሰላም <b>{message.from_user.first_name}</b>! ወደ Kana Games በደህና መጡ። 🎮\n\n"
            f"ለመመዝገብ እና የ 10.15 ብር ቦነስዎን ለመቀበል እባክዎ ከታች ያለውን አዝራር በመጫን ስልክ ቁጥርዎን ያጋሩ:",
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
        "እንኳን ደስ አለዎት! ለአዲስ ተመዝጋቢዎች የተዘጋጀው የ <b>10.15 ብር</b> ጨዋታ ቦነስ አካውንትዎ ላይ ተጨምሯል። 🎁\n\n"
        "ከታች ካሉት አማራጮች የሚፈልጉትን ይምረጡ:",
        parse_mode="HTML",
        reply_markup=get_main_menu(),
    )

@dp.message(F.text == "💰 ሐሳብ (Balance)")
async def menu_balance(message: types.Message):
    user_data = get_user_balance(message.from_user.id)
    balance = user_data[0] if user_data else 10.15
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
            [InlineKeyboardButton(text="🚀 Kana Games መድረክ ክፈት", web_app=WebAppInfo(url=server_url))]
        ]
    )
    await message.answer("🎮 ከታች ያለውን ቁልፍ በመጫን የካና ጌምስ መድረክን በቀጥታ መጫወት ይችላሉ፦", reply_markup=keyboard)

@dp.message(F.text == "🛠️ ቴክለማ ሳፖርት (Support)")
async def menu_support(message: types.Message):
    await message.answer("🛠️ ማንኛውም ጥያቄ ካለዎት እዚህ ጋር ማግኘት ይችላሉ።")

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

# --- የዌብ ሰርቨር እና ሙሉው የ Kana Games (Home + Fast Keno Dashboard) ---
async def handle_keno_game(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="am">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Kana Games</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-[#121824] text-white font-sans min-h-screen flex flex-col justify-between select-none">

        <!-- HEADER -->
        <header class="w-full bg-[#1b2230] p-3 flex justify-between items-center border-b border-slate-800 sticky top-0 z-50">
            <div class="flex items-center gap-2">
                <button onclick="goHome()" class="bg-[#ffd700] text-slate-950 font-black px-2 py-1 rounded text-xs">ቀ ጌ</button>
                <span id="header-title" class="font-bold text-sm tracking-wide">Kana Games</span>
            </div>
            <div class="flex items-center gap-3">
                <div class="text-right">
                    <span class="text-[9px] text-slate-400 block">WALLET</span>
                    <span id="balance" class="text-xs font-extrabold text-green-400">10.15 ETB</span>
                </div>
                <button onclick="toggleMenu()" class="text-slate-300 text-lg">☰</button>
            </div>
        </header>

        <!-- CONTAINER (HOME PAGE vs KENO GAME PAGE) -->
        <main class="w-full max-w-md mx-auto p-3 flex-grow flex flex-col gap-3">
            
            <!-- HOME VIEW -->
            <div id="home-view" class="flex flex-col gap-4">
                <!-- Daily Gift Banner -->
                <div class="bg-gradient-to-r from-amber-600 to-yellow-500 p-4 rounded-xl flex justify-between items-center shadow-lg">
                    <div>
                        <span class="text-[10px] uppercase font-bold text-black/70 block">Daily Gift</span>
                        <h2 class="text-base font-black text-slate-950">GET BONUS</h2>
                        <button onclick="claimBonus()" class="mt-2 bg-slate-950 text-yellow-400 font-bold text-xs px-4 py-1.5 rounded-lg shadow">CLAIM NOW 🔥</button>
                    </div>
                    <div class="text-3xl">🎁</div>
                </div>

                <!-- Quick Action Buttons -->
                <div class="grid grid-cols-4 gap-2 text-center">
                    <button onclick="alert('Դegosit: በባንክ/ቴሌብር')" class="bg-[#1b2230] p-2.5 rounded-xl border border-slate-800 flex flex-col items-center gap-1 hover:border-yellow-500">
                        <span class="text-yellow-400 text-base">📥</span>
                        <span class="text-[10px] font-bold text-slate-300">DEPOSIT</span>
                    </button>
                    <button onclick="alert('Withdraw: ለአድሚን ያሳውቁ')" class="bg-[#1b2230] p-2.5 rounded-xl border border-slate-800 flex flex-col items-center gap-1 hover:border-yellow-500">
                        <span class="text-yellow-400 text-base">📤</span>
                        <span class="text-[10px] font-bold text-slate-300">WITHDRAW</span>
                    </button>
                    <button onclick="switchTab('history')" class="bg-[#1b2230] p-2.5 rounded-xl border border-slate-800 flex flex-col items-center gap-1 hover:border-yellow-500">
                        <span class="text-yellow-400 text-base">📋</span>
                        <span class="text-[10px] font-bold text-slate-300">HISTORY</span>
                    </button>
                    <button onclick="alert('Support: @Admin')" class="bg-[#1b2230] p-2.5 rounded-xl border border-slate-800 flex flex-col items-center gap-1 hover:border-yellow-500">
                        <span class="text-yellow-400 text-base">🛠️</span>
                        <span class="text-[10px] font-bold text-slate-300">SUPPORT</span>
                    </button>
                </div>

                <!-- Top Selection Games List -->
                <div>
                    <h3 class="text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">🔥 Top Selection</h3>
                    <div class="grid grid-cols-2 gap-2.5">
                        <div onclick="openKenoGame()" class="bg-[#1b2230] rounded-xl overflow-hidden border border-slate-800 cursor-pointer hover:scale-[1.02] transition">
                            <div class="bg-gradient-to-br from-emerald-900 to-slate-900 p-4 text-center relative">
                                <span class="absolute top-2 right-2 bg-red-600 text-[9px] font-bold px-1.5 py-0.5 rounded">HOT</span>
                                <span class="text-2xl font-black text-emerald-400">KENO 80</span>
                            </div>
                            <div class="p-2 text-center text-xs font-bold">FAST KENO</div>
                        </div>
                        <div onclick="alert('ይህ ጨዋታ በቅርቡ ይመጣል!')" class="bg-[#1b2230] rounded-xl overflow-hidden border border-slate-800 cursor-pointer hover:scale-[1.02] transition">
                            <div class="bg-gradient-to-br from-purple-900 to-slate-900 p-4 text-center relative">
                                <span class="absolute top-2 right-2 bg-red-600 text-[9px] font-bold px-1.5 py-0.5 rounded">HOT</span>
                                <span class="text-2xl font-black text-purple-400">AVIAT</span>
                            </div>
                            <div class="p-2 text-center text-xs font-bold">AVIAFLY</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- KENO GAME VIEW -->
            <div id="keno-view" class="hidden flex flex-col gap-2.5">
                
                <!-- Sub Header (Fast Keno Status) -->
                <div class="bg-[#1b2230] p-2.5 rounded-xl border border-slate-800 flex justify-between items-center">
                    <div>
                        <div class="flex items-center gap-1">
                            <span class="text-yellow-400 font-black text-xs">⚡ FAST KENO</span>
                            <span class="text-[9px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">1 from 80</span>
                        </div>
                        <span class="text-[9px] text-slate-500">ID: <span id="draw-id">888618399</span></span>
                    </div>
                    <div class="text-right">
                        <span id="timer" class="text-sm font-black text-yellow-400">00:08</span>
                    </div>
                </div>

                <!-- Number Draw Circle Animation Box -->
                <div class="bg-[#1b2230] p-3 rounded-xl border border-slate-800 flex flex-col items-center justify-center relative min-h-[90px]">
                    <div id="drawStatus" class="text-[11px] text-slate-400 mb-1">Choose 10 numbers</div>
                    <div id="drawnNumberDisplay" class="text-3xl font-black text-yellow-400 tracking-wider">-</div>
                    <div id="drawnCount" class="text-[9px] text-slate-500 mt-0.5">00 / 20</div>
                </div>

                <!-- Numbers Grid (1 to 80) -->
                <div class="bg-[#1b2230] p-2.5 rounded-xl border border-slate-800">
                    <div class="flex justify-between items-center mb-2">
                        <span class="text-[11px] font-bold text-slate-300">Choose <span id="selected-count">0</span> numbers</span>
                        <button onclick="clearSelection()" class="text-[11px] text-red-400 font-bold">Clear</button>
                    </div>
                    <div id="numberGrid" class="grid grid-cols-10 gap-1"></div>
                </div>

                <!-- Bet Controls & Play Button -->
                <div class="bg-[#1b2230] p-2.5 rounded-xl border border-slate-800 flex flex-col gap-2">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-1">
                            <button onclick="changeBet(-1)" class="bg-slate-800 w-7 h-7 rounded font-bold text-sm">-</button>
                            <input type="number" id="betAmount" value="2" readonly class="w-10 bg-transparent text-center font-bold text-sm text-yellow-400">
                            <button onclick="changeBet(1)" class="bg-slate-800 w-7 h-7 rounded font-bold text-sm">+</button>
                        </div>
                        <div class="flex gap-1">
                            <button onclick="setBet(2)" class="bet-btn bg-[#ffd700] text-slate-950 px-2 py-1 rounded text-[10px] font-bold" id="bet-2">2</button>
                            <button onclick="setBet(5)" class="bet-btn bg-slate-800 text-slate-300 px-2 py-1 rounded text-[10px] font-bold" id="bet-5">5</button>
                            <button onclick="setBet(10)" class="bet-btn bg-slate-800 text-slate-300 px-2 py-1 rounded text-[10px] font-bold" id="bet-10">10</button>
                            <button onclick="setBet(20)" class="bet-btn bg-slate-800 text-slate-300 px-2 py-1 rounded text-[10px] font-bold" id="bet-20">20</button>
                            <button onclick="setBet(50)" class="bet-btn bg-slate-800 text-slate-300 px-2 py-1 rounded text-[10px] font-bold" id="bet-50">MAX</button>
                        </div>
                    </div>

                    <button id="playBtn" onclick="startKenoGame()" class="w-full bg-[#ffd700] hover:bg-yellow-400 text-slate-950 font-black py-2.5 rounded-xl shadow text-xs tracking-wider">
                        BET
                    </button>
                </div>

                <!-- Tabs: Game / History / Results / Statistics -->
                <div class="flex justify-around bg-[#1b2230] p-2 rounded-xl border border-slate-800 text-[10px] font-bold text-slate-400">
                    <button onclick="switchKenoTab('game')" id="ktab-game" class="text-yellow-400">▶ GAME</button>
                    <button onclick="switchKenoTab('history')" id="ktab-history">📋 HISTORY</button>
                    <button onclick="switchKenoTab('results')" id="ktab-results">📊 RESULTS</button>
                    <button onclick="switchKenoTab('stats')" id="ktab-stats">📈 STATISTICS</button>
                </div>

                <!-- Dynamic Subsections (History / Tickets List) -->
                <div id="sub-history-box" class="bg-[#1b2230] p-2.5 rounded-xl border border-slate-800 max-h-36 overflow-y-auto text-[11px] flex flex-col gap-1.5">
                    <div class="text-[10px] font-bold text-slate-400">My Tickets</div>
                    <div id="ticketsList" class="flex flex-col gap-1">
                        <span class="text-slate-500 italic">ምንም ቲኬት የለም</span>
                    </div>
                </div>

            </div>

        </main>

        <!-- FOOTER NAVIGATION -->
        <footer class="w-full bg-[#1b2230] border-t border-slate-800 p-2 flex justify-around items-center text-[9px] font-bold text-slate-400">
            <button onclick="goHome()" class="flex flex-col items-center gap-0.5 text-yellow-400">
                <span class="text-sm">🏠</span> HOME
            </button>
            <button onclick="openKenoGame()" class="flex flex-col items-center gap-0.5">
                <span class="text-sm">⚡</span> KENO
            </button>
            <button onclick="switchTab('history')" class="flex flex-col items-center gap-0.5">
                <span class="text-sm">📋</span> HISTORY
            </button>
            <button onclick="alert('Wallet Balance: 10.15 ETB')" class="flex flex-col items-center gap-0.5">
                <span class="text-sm">💰</span> WALLET
            </button>
        </footer>

        <!-- JAVASCRIPT LOGIC -->
        <script>
            let tg = window.Telegram.WebApp;
            tg.expand();

            let userId = tg.initDataUnsafe && tg.initDataUnsafe.user ? tg.initDataUnsafe.user.id : 7131094446;
            let balance = 10.15;
            let selectedNumbers = [];
            let currentBet = 2;
            let isPlaying = false;
            let tickets = [];

            async function fetchBalance() {
                try {
                    let res = await fetch(`/api/balance?user_id=${userId}`);
                    let data = await res.json();
                    balance = data.balance;
                    document.getElementById('balance').innerText = balance.toFixed(2) + " ETB";
                } catch(e) {}
            }
            fetchBalance();

            // Build 1-80 Grid
            const grid = document.getElementById('numberGrid');
            for(let i=1; i<=80; i++) {
                let btn = document.createElement('button');
                btn.innerText = i;
                btn.id = `num-${i}`;
                btn.className = "bg-slate-800 hover:bg-slate-700 text-[11px] font-black py-1.5 rounded text-slate-300 transition";
                btn.onclick = () => toggleNum(i);
                grid.appendChild(btn);
            }

            function toggleNum(num) {
                if(isPlaying) return;
                let idx = selectedNumbers.indexOf(num);
                let btn = do
