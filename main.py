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

# --- የዌብ ሰርቨር እና ትክክለኛው የ Kana Games Fast Keno በይነገጽ ---
async def handle_keno_game(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="am">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Kana Games - Fast Keno</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-[#121824] text-white font-sans min-h-screen flex flex-col justify-between select-none p-2">

        <header class="w-full bg-[#1b2230] p-2.5 rounded-xl flex justify-between items-center border border-slate-800 mb-2">
            <div class="flex items-center gap-2">
                <span class="bg-[#ffd700] text-slate-950 font-black px-2 py-0.5 rounded text-xs">ቀ ጌ</span>
                <span class="font-bold text-xs tracking-wide">FAST KENO</span>
            </div>
            <div class="flex items-center gap-3">
                <div class="text-right">
                    <span class="text-[9px] text-slate-400 block">WALLET</span>
                    <span id="balance" class="text-xs font-extrabold text-green-400">10.15 ETB</span>
                </div>
            </div>
        </header>

        <main class="w-full max-w-md mx-auto flex-grow flex flex-col gap-2">
            
            <div class="bg-[#1b2230] p-2 rounded-xl border border-slate-800 flex justify-between items-center">
                <div>
                    <div class="flex items-center gap-1">
                        <span class="text-yellow-400 font-black text-xs">⚡ DRAW #</span>
                        <span id="draw-id" class="text-xs font-bold text-slate-200">888618399</span>
                    </div>
                </div>
                <div class="text-right">
                    <span id="timer" class="text-xs font-black text-yellow-400 bg-slate-900 px-2 py-1 rounded">00:10</span>
                </div>
            </div>

            <div class="bg-[#1b2230] p-3 rounded-xl border border-slate-800 flex flex-col items-center justify-center relative min-h-[85px]">
                <div id="drawStatus" class="text-[11px] text-slate-400 mb-1">እባክዎ እስከ 10 ቁጥሮች ይምረጡ</div>
                <div id="drawnNumberDisplay" class="text-3xl font-black text-yellow-400 tracking-wider">-</div>
                <div id="drawnCount" class="text-[9px] text-slate-500 mt-0.5">የወጡ ቁጥሮች: 0 / 20</div>
            </div>

            <div class="bg-[#1b2230] p-2.5 rounded-xl border border-slate-800">
                <div class="flex justify-between items-center mb-1.5">
                    <span class="text-[11px] font-bold text-slate-300">ቁጥሮችን ይምረጡ (<span id="selected-count">0</span>/10)</span>
                    <button onclick="clearSelection()" class="text-[11px] text-red-400 font-bold hover:underline">አጽዳ (Clear)</button>
                </div>
                <div id="numberGrid" class="grid grid-cols-10 gap-1"></div>
            </div>

            <div class="bg-[#1b2230] p-2.5 rounded-xl border border-slate-800 flex flex-col gap-2">
                <div class="flex items-center justify-between">
                    <span class="text-[11px] font-bold text-slate-300">የውርርድ መጠን (ብር)</span>
                    <div class="flex gap-1">
                        <button onclick="setBet(2)" class="bet-btn bg-yellow-400 text-slate-950 px-2 py-1 rounded text-[10px] font-bold" id="bet-2">2</button>
                        <button onclick="setBet(5)" class="bet-btn bg-slate-800 text-slate-300 px-2 py-1 rounded text-[10px] font-bold" id="bet-5">5</button>
                        <button onclick="setBet(10)" class="bet-btn bg-slate-800 text-slate-300 px-2 py-1 rounded text-[10px] font-bold" id="bet-10">10</button>
                        <button onclick="setBet(20)" class="bet-btn bg-slate-800 text-slate-300 px-2 py-1 rounded text-[10px] font-bold" id="bet-20">20</button>
                        <button onclick="setBet(50)" class="bet-btn bg-slate-800 text-slate-300 px-2 py-1 rounded text-[10px] font-bold" id="bet-50">50</button>
                    </div>
                </div>
                <input type="hidden" id="betAmount" value="2">

                <button id="playBtn" onclick="startKenoGame()" class="w-full bg-yellow-400 hover:bg-yellow-300 text-slate-950 font-black py-2.5 rounded-xl shadow text-xs tracking-wider transition">
                    ⚡ ጨዋታ ጀምር (PLAY)
                </button>
            </div>

            <div class="bg-[#1b2230] p-2.5 rounded-xl border border-slate-800 max-h-32 overflow-y-auto flex flex-col gap-1">
                <span class="text-[10px] font-bold text-slate-400">ያለፉት የውርርድ ቲኬቶች (My Tickets)</span>
                <div id="ticketsList" class="flex flex-col gap-1">
                    <span class="text-[10px] text-slate-500 italic">ምንም ቲኬት የለም</span>
                </div>
            </div>

        </main>

        <footer class="text-[9px] text-slate-500 text-center mt-1">
            &copy; 2026 Kana Games Fast Keno. መብቱ በህግ የተጠበቀ ነው።
        </footer>

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
                btn.className = "number-btn bg-slate-800 hover:bg-slate-700 text-[11px] font-black py-1.5 rounded text-slate-300 transition";
                btn.onclick = () => toggleNum(i);
                grid.appendChild(btn);
            }

            function toggleNum(num) {
                if(isPlaying) return;
                let idx = selectedNumbers.indexOf(num);
                let btn = document.getElementById(`num-${num}`);
                if(idx > -1) {
                    selectedNumbers.splice(idx, 1);
                    btn.className = "number-btn bg-slate-800 hover:bg-slate-700 text-[11px] font-black py-1.5 rounded text-slate-300 transition";
                } else {
                    if(selectedNumbers.length >= 10) {
                        alert("ከ 10 በላይ ቁጥሮች መምረጥ አይችሉም!");
                        return;
                    }
                    selectedNumbers.push(num);
                    btn.className = "number-btn bg-yellow-400 text-slate-950 text-[11px] font-black py-1.5 rounded shadow transition";
                }
                document.getElementById('selected-count').innerText = selectedNumbers.length;
            }

            function clearSelection() {
                if(isPlaying) return;
                selectedNumbers.forEach(n => {
                    let btn = document.getElementById(`num-${n}`);
                    if(btn) btn.className = "number-btn bg-slate-800 hover:bg-slate-700 text-[11px] font-black py-1.5 rounded text-slate-300 transition";
                });
                selectedNumbers = [];
                document.getElementById('selected-count').innerText = '0';
            }

            function setBet(amt) {
                if(isPlaying) return;
                currentBet = amt;
                document.getElementById('betAmount').value = amt;
                document.querySelectorAll('.bet-btn').forEach(b => {
                    b.className = "bet-btn bg-slate-800 text-slate-300 px-2 py-1 rounded text-[10px] font-bold";
                });
                document.getElementById(`bet-${amt}`).className = "bet-btn bg-yellow-400 text-slate-950 px-2 py-1 rounded text-[10px] font-bold";
            }

            async function updateServerBalance(newBal) {
                balance = newBal;
                document.getElementById('balance').innerText = balance.toFixed(2) + " ETB";
                try {
                    await fetch('/api/update_balance', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({user_id: userId, balance: newBal})
                    });
                } catch(e) {}
            }

            function startKenoGame() {
                if(selectedNumbers.length === 0) {
                    alert("እባክዎ መጀመሪያ ቁጥሮችን ይምረጡ!");
                    return;
                }
                if(currentBet > balance) {
                    alert("በቂ ቀሪ ሂሳብ የለዎትም!");
                    return;
                }

                updateServerBalance(balance - currentBet);
                isPlaying = true;
                let playBtn = document.getElementById('playBtn');
                playBtn.disabled = true;
                playBtn.classList.add('opacity-50');
                playBtn.innerText = "⚡ ዕጣ እየወጣ ነው...";

                let ticketId = Math.floor(Math.random() * 899999 + 100000);
                tickets.unshift({id: ticketId, numbers: [...selectedNumbers], bet: currentBet, status: "Waiting"});
                renderTickets();

                let drawn = [];
                while(drawn.length < 20) {
                    let r = Math.floor(Math.random() * 80) + 1;
                    if(!drawn.includes(r)) drawn.push(r);
                }

                let index = 0;
                document.getElementById('drawStatus').innerText = "⚡ ፈጣን ዕጣ በመውጣት ላይ...";

                let interval = setInterval(() => {
                    if(index < drawn.length) {
                        let cur = drawn[index];
                        document.getElementById('drawnNumberDisplay').innerText = cur;
                        document.getElementById('drawnCount').innerText = `የወጡ ቁጥሮች: ${index + 1} / 20`;

                        let b = document.getElementById(`num-${cur}`);
                        if(selectedNumbers.includes(cur)) {
                            b.className = "number-btn bg-green-500 text-slate-950 text-[11px] font-black py-1.5 rounded shadow animate-pulse";
                        } else {
                            b.className = "number-btn bg-slate-700 text-yellow-300 text-[11px] font-black py-1.5 rounded";
                        }
                        index++;
                    } else {
                        clearInterval(interval);
                        finishGame(drawn, ticketId);
                    }
                }, 50);
            }

            function finishGame(drawn, ticketId) {
                let hits = selectedNumbers.filter(n => drawn.includes(n)).length;
                let winAmt = hits * currentBet * 1.5;

                let ticket = tickets.find(t => t.id === ticketId);
                if(ticket) {
                    ticket.status = winAmt > 0 ? `Won +${winAmt.toFixed(2)}` : "Lost 0.00";
                }
                renderTickets();

                if(winAmt > 0) {
                    updateServerBalance(balance + winAmt);
                    document.getElementById('drawStatus').innerHTML = `<span class="text-green-400 font-bold">🎉 አሸንፈዋል! ${hits} ገጥመዋል (+${winAmt.toFixed(2)} ብር)</span>`;
                } else {
                    document.getElementById('drawStatus').innerHTML = `<span class="text-red-400 font-bold">❌ ምንም ቁጥር አልገጠመም። እንደገና ይሞክሩ!</span>`;
                }

                // Clear board for next game
                selectedNumbers.forEach(n => {
                    let b = document.getElementById(`num-${n}`);
                    if(b) b.className = "number-btn bg-slate-800 hover:bg-slate-700 text-[11px] font-black py-1.5 rounded text-slate-300 transition";
                });
                selectedNumbers = [];
                document.getElementById('selected-count').innerText = '0';

                isPlaying = false;
                let playBtn = document.getElementById('playBtn');
                playBtn.disabled = false;
                playBtn.classList.remove('opacity-50');
                playBtn.innerText = "⚡ ጨዋታ ጀምር (PLAY)";
            }

            function renderTickets() {
                let list = document.getElementById('ticketsList');
                list.innerHTML = "";
                tickets.slice(0, 4).forEach(t => {
                    let item = document.createElement('div');
                    item.className = "bg-slate-900 p-1.5 rounded border border-slate-800 flex justify-between items-center text-[10px]";
                    item.innerHTML = `<div><span class="text-yellow-400 font-bold">Ticket #${t.id}</span><div class="text-[9px] text-slate-400">ቁጥሮች: ${t.numbers.join(
