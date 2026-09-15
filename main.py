import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# ሎጊንግ ማስተካከል
logging.basicConfig(level=logging.INFO)

TOKEN = "8670073050:AAHb2D2WZ-q5dfIoH78jCqjCGzdT90dgFbo"
ADMIN_ID = 7131094446
TELEBIRR_NUMBER = "0998257988"
TELEBIRR_NAME = "ዮሃንስ"
MIN_DEPOSIT = 500

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# FSM States for Deposit flow
class DepositStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_screenshot = State()

# --- ዳታቤዝ ማዋቀር ---
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            language TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def add_user_initial(user_id: int, username: str):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (user_id, username, language) VALUES (?, ?, ?)",
            (user_id, username, "am"),
        )
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
def get_main_menu(lang="am"):
    if lang == "en":
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="💳 Deposit Money"), KeyboardButton(text="🛠️ Support")]],
            resize_keyboard=True,
        )
    elif lang == "om":
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="💳 Maallaqa Galchuuf"), KeyboardButton(text="🛠️ Deeggarsa")]],
            resize_keyboard=True,
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="💳 ገንዘብ ገቢ ማድረግ"), KeyboardButton(text="🛠️ ቴክለማ ሳፖርት (Support)")]],
            resize_keyboard=True,
        )

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username
    add_user_initial(user_id, username)

    lang_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="አማርኛ 🇪🇹", callback_data="lang_am"),
                InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en"),
                InlineKeyboardButton(text="Afaan Oromoo 🇪🇹", callback_data="lang_om"),
            ]
        ]
    )

    await message.answer(
        "እባክዎ የሚፈልጉትን ቋንቋ ይምረጡ / Please choose your language / Afaan filadhaa:",
        reply_markup=lang_keyboard,
    )

@dp.callback_query(F.data.startswith("lang_"))
async def language_selected(callback: types.CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    await state.update_data(language=lang)
    
    if lang == "en":
        welcome_text = (
            f"Welcome <b>{callback.from_user.first_name}</b>!\n\n"
            "Welcome to the Payment Center. 💳✨\n"
            f"Minimum deposit amount is <b>{MIN_DEPOSIT} ETB</b>."
        )
    elif lang == "om":
        welcome_text = (
            f"Baga nagaan dhufte <b>{callback.from_user.first_name}</b>!\n\n"
            "Gara Giddugala Kaffaltitti nagaan dhuftan. 💳✨\n"
            f"Hanga xiqqaan kaappitaala galchuu <b>{MIN_DEPOSIT} ETB</b> dha."
        )
    else:
        welcome_text = (
            f"ሰላም <b>{callback.from_user.first_name}</b>!\n\n"
            "እንኳን ወደ ክፍያ ማዕከል በደህና መጡ። 💳✨\n"
            f"ዝቅተኛው የተቀማጭ ገንዘብ መጠን <b>{MIN_DEPOSIT} ብር</b> ነው።"
        )

    await callback.message.edit_text(welcome_text, parse_mode="HTML")
    await callback.message.answer("ማንኛውንም ምርጫ ከታች ካለው ምናሌ ይምረጡ:", reply_markup=get_main_menu(lang))
    await callback.answer()

@dp.message(F.text.in_(["💳 ገንዘብ ገቢ ማድረግ", "💳 Deposit Money", "💳 Maallaqa Galchuuf"]))
async def menu_deposit(message: types.Message, state: FSMContext):
    await state.set_state(DepositStates.waiting_for_amount)
    await message.answer(
        f"💳 <b>ገንዘብ ገቢ ለማድረግ:</b>\n\n"
        f"⚠️ ዝቅተኛው የተቀማጭ ገንዘብ መጠን <b>{MIN_DEPOSIT} ብር</b> ነው።\n\n"
        f"እባክዎ ማስገባት (ዲፖዚት ማድረግ) የሚፈልጉትን የገንዘብ መጠን ቁጥር ብቻ ይጻፉ (ለምሳሌ: 500):",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardRemove()
    )

@dp.message(DepositStates.waiting_for_amount)
async def process_deposit_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ እባክዎ ትክክለኛ የቁጥር መጠን ብቻ ይጻፉ (ለምሳሌ: 500):")
        return

    amount = int(message.text)
    if amount < MIN_DEPOSIT:
        await message.answer(f"❌ ዝቅተኛው የተቀማጭ ገንዘብ መጠን {MIN_DEPOSIT} ብር ነው። እባክዎ ትክክለኛ መጠን ያስገቡ:")
        return

    await state.update_data(deposit_amount=amount)
    await state.set_state(DepositStates.waiting_for_screenshot)

    await message.answer(
        f"✅ የጠየቁት መጠን: <b>{amount} ብር</b>\n\n"
        f"እባክዎ ከታች ባለው የቴሌብር ቁጥር ገንዘቡን ያስተላልፉ:\n\n"
        f"📱 <b>ቴሌብር:</b> <code>{TELEBIRR_NUMBER}</code>\n"
        f"👤 <b>ስም:</b> {TELEBIRR_NAME}\n\n"
        f"📸 ገንዘብ ካስተላለፉ በኋላ የደረሰኝ ስክሪንሾት (Screenshot) በዚህ ቻት ላይ ይላኩሱ:",
        parse_mode="HTML"
    )

@dp.message(DepositStates.waiting_for_screenshot, F.photo)
async def process_deposit_screenshot(message: types.Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get("deposit_amount")
    photo = message.photo[-1].file_id
    user = message.from_user

    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ አጽድቅ (Approve)", callback_data=f"app_{user.id}_{amount}"),
                InlineKeyboardButton(text="❌ ውድቅ አድርግ (Reject)", callback_data=f"rej_{user.id}_{amount}"),
            ]
        ]
    )

    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo,
        caption=(
            f"🔔 <b>አዲስ የዲፖዚት ጥያቄ!</b>\n\n"
            f"👤 ስም: {user.full_name} (@{user.username or 'নেই'})\n"
            f"🆔 ዩዘር አይዲ: <code>{user.id}</code>\n"
            f"💰 የጠየቀው መጠን: <b>{amount} ብር</b>"
        ),
        parse_mode="HTML",
        reply_markup=admin_keyboard
    )

    await state.clear()
    await message.answer(
        "✅ <b>ደረሰኝዎ ተልኳል!</b>\n\n"
        "አድሚኑ እስኪመረምረው ድረስ በትዕግስት ይጠብቁ። ሲጸድቅ ወይም ውድቅ ሲደረግ ማሳወቂያ ይደርሰዎታል።",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )

@dp.message(DepositStates.waiting_for_screenshot)
async def not_photo_handler(message: types.Message):
    await message.answer("❌ እባክዎ የደረሰኝ ስክሪንሾት (ፎቶ) ብቻ ይላኩ!")

@dp.callback_query(F.data.startswith(("app_", "rej_")))
async def admin_decision(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("ይህንን ለማድረግ ፈቃድ የለዎትም!", show_alert=True)
        return

    action, user_id_str, amount_str = callback.data.split("_")
    user_id = int(user_id_str)
    amount = amount_str

    if action == "app":
        try:
            await bot.send_message(
                user_id,
                f"✅ <b>ዲፖዚትዎ ጸድቋል!</b>\n\n"
                f"🎉 ያስገቡት <b>{amount} ብር</b> በሂሳብዎ ላይ ተመዝግቧል። መልካም ጨዋታ!",
                parse_mode="HTML"
            )
            await callback.message.edit_caption(
                caption=callback.message.caption + "\n\n<b>status: 🟢 ጸድቋል (Approved)</b>",
                parse_mode="HTML"
            )
            await callback.answer("ጥያቄው ጸድቆ ተጠቃሚው ተነግሮአቸዋል!")
        except Exception:
            await callback.answer("ተጠቃሚው ቦቱን አግዶት ሊሆን ይችላል!")
    else:
        try:
            await bot.send_message(
                user_id,
                f"❌ <b>ዲፖዚትዎ ውድቅ ተደርጓል!</b>\n\n"
                f"እባክዎ የተላከውን መረጃ አረጋግጠው እንደገና ይሞክሩ ወይም ሰፖርት ያነጋግሩ።",
                parse_mode="HTML"
            )
            await callback.message.edit_caption(
                caption=callback.message.caption + "\n\n<b>status: 🔴 ውድቅ ተደርጓል (Rejected)</b>",
                parse_mode="HTML"
            )
            await callback.answer("ጥያቄው ውድቅ ተደርጓል!")
        except Exception:
            await callback.answer("ተጠቃሚው ቦቱን አግዶት ሊሆን ይችላል!")

@dp.message(F.text.in_(["🛠️ ቴክለማ ሳፖርት (Support)", "🛠️ Support", "🛠️ Deeggarsa"]))
async def menu_support(message: types.Message):
    await message.answer("🛠️ ማንኛውም ጥያቄ ወይም እርዳታ ካለዎት ለአድሚን ማሳወቅ ይችላሉ። / If you have any questions, contact admin.")

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
