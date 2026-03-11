from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN, BOT_ADMIN_PASSWORD
import database, os

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

ADMIN_STATE = {}
FILES_FOLDER = "files/"
os.makedirs(FILES_FOLDER, exist_ok=True)

def main_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("👤 Профиль", callback_data="menu_profile"),
        InlineKeyboardButton("📦 Товары", callback_data="menu_items"),
        InlineKeyboardButton("➕ Добавить товар", callback_data="menu_add")
    )
    return kb

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    database.get_or_create_user(message.from_user.id)
    await message.answer("👋 Добро пожаловать!", reply_markup=main_menu())

@dp.callback_query_handler(lambda c: c.data.startswith("menu_"))
async def menu_buttons(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    action = callback.data.split("_")[1]

    if action == "profile":
        balance = database.get_balance(user_id)
        cursor = database.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id=?", (user_id,))
        total_orders = cursor.fetchone()[0]
        await bot.send_message(user_id, f"👤 Профиль:\nБаланс: {balance}₽\nВсего покупок: {total_orders}")

    elif action == "items":
        items = database.get_all_items()
        kb = InlineKeyboardMarkup()
        for i in items:
            kb.add(InlineKeyboardButton(f"{i[1]} - {i[3]}₽", callback_data=f"buy:{i[0]}"))
        await bot.send_message(user_id, "📦 Товары:", reply_markup=kb)

    elif action == "add":
        if str(user_id) != BOT_ADMIN_PASSWORD:
            await bot.send_message(user_id, "❌ Доступ запрещён")
            return
        ADMIN_STATE[user_id] = "waiting_file"
        await bot.send_message(user_id, "📁 Пришлите файл для нового товара:")

    await callback.answer()

@dp.message_handler(content_types=["document"])
async def handle_file(message: types.Message):
    user_id = message.from_user.id
    if ADMIN_STATE.get(user_id) != "waiting_file":
        return

    file_id = message.document.file_id
    file_name = message.document.file_name
    file_path = os.path.join(FILES_FOLDER, file_name)

    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, file_path)

    ADMIN_STATE[user_id] = {"file_path": file_path}
    await message.answer("✅ Файл загружен. Введите цену товара (числом):")

@dp.message_handler()
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    state = ADMIN_STATE.get(user_id)

    if isinstance(state, dict) and "file_path" in state and "price" not in state:
        try:
            price = float(message.text)
        except ValueError:
            await message.answer("❌ Введите число")
            return
        state["price"] = price
        await message.answer("Введите название товара:")
        ADMIN_STATE[user_id] = state
        return

    if isinstance(state, dict) and "file_path" in state and "price" in state:
        name = message.text
        database.add_item(name, state["file_path"], state["price"])
        ADMIN_STATE.pop(user_id)
        await message.answer(f"✅ Товар '{name}' добавлен!", reply_markup=main_menu())
