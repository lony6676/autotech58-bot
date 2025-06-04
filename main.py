import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import os

API_TOKEN = os.getenv("BOT_TOKEN") # ← токен
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # ← Telegram ID администратора

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хранилище соответствий: ID сообщения у админа → ID пользователя
admin_message_links = {}

# Состояние: считаем количество сообщений
class MsgCounter(StatesGroup):
    step = State()

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Здравствуйте, это чат-бот компании Auto Tech 58. Какой у вас вопрос?")
    await state.set_state(MsgCounter.step)
    await state.update_data(count=0)

@dp.message(F.chat.id != ADMIN_ID)
async def handle_user_message(message: Message, state: FSMContext):
    # получаем, сколько сообщений уже было
    data = await state.get_data()
    count = data.get("count", 0)

    # отправляем админу
    admin_msg = await bot.send_message(
        ADMIN_ID,
        f"📩 Сообщение от @{message.from_user.username or message.from_user.full_name}:\n\n{message.text}"
    )
    admin_message_links[admin_msg.message_id] = message.from_user.id

    # в зависимости от номера сообщения отвечаем
    if count == 0:
        await message.answer(
            "Наша группа, в которой каждый день публикуется более 10 отличных вариантов из Кореи, "
            "а также много Live контента — а значит, вы точно найдёте подходящую машину именно для вас! \n\n"
            "👉 https://t.me/autotech58\n\n"
            "Если у вас есть вопрос или вы хотите рассчитать стоимость авто, напишите, пожалуйста, подробнее. "
            "Мы ответим в ближайшее время.\n\n"
            "📞 Напишите ваш номер, и мы свяжемся с вами."
        )
    elif count == 1:
        await message.answer(
            "Спасибо за обращение! Наш менеджер ответит Вам в ближайшее время!\n\n"
            "С уважением Auto Tech 58"
        )
    # увеличиваем счётчик
    await state.update_data(count=count + 1)

# Ответ администратора пользователю
@dp.message(F.chat.id == ADMIN_ID, F.reply_to_message)
async def admin_reply(message: Message):
    original_msg_id = message.reply_to_message.message_id
    user_id = admin_message_links.get(original_msg_id)

    if user_id:
        try:
            await bot.send_message(user_id, f"💬 Ответ от менеджера:\n\n{message.text}")
            await message.reply("✅ Ответ отправлен пользователю.")
        except Exception:
            await message.reply("⚠️ Не удалось отправить сообщение пользователю.")
    else:
        await message.reply("⚠️ Невозможно определить, кому отправить сообщение. Возможно, это не ответ на запрос.")

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
