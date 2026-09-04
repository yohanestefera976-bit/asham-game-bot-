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
