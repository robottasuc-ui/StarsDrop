import os
import json
from aiogram import Bot, Dispatcher, executor, types

# Вместо токена пишем это (он будет браться из настроек сервера)
API_TOKEN = os.getenv('8451029637:AAHF6jJdQ98QhYRRsJxH_wuktMeE5QctT-I')

# Твой ID оставляем как есть
ADMIN_ID = 8015661230

# 2. Твой ID уже указан верно
ADMIN_ID = 8015661230  

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# Обработка команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer(
        "👋 Привет! Нажми на кнопку ниже, чтобы открыть StarDrop.",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Играть 🚀", web_app=types.WebAppInfo(url="ССЫЛКА_НА_GITHUB_PAGES"))]
            ],
            resize_keyboard=True
        )
    )

# ТОТ САМЫЙ КОД ОБРАБОТКИ ВЫВОДА
@dp.message_handler(content_types=['web_app_data'])
async def handle_data(message: types.Message):
    try:
        # Данные от игрока (приходят из твоего wheel.html или profile.html)
        data = json.loads(message.web_app_data.data)
        user_name = message.from_user.username or message.from_user.first_name
        user_id = message.from_user.id

        if data.get('action') == 'withdraw':
            item = data.get('item', 'Неизвестный предмет')
            
            # 1. Ответ игроку
            await message.answer(f"⏳ Заявка на <b>{item}</b> получена. Проверяю донаты...")

            # 2. Сообщение тебе (Админу)
            await bot.send_message(
                ADMIN_ID, 
                f"🚀 <b>ЗАЯВКА НА ВЫВОД!</b>\n\n"
                f"👤 От кого: @{user_name}\n"
                f"🆔 ID игрока: <code>{user_id}</code>\n"
                f"🎁 Подарок: {item}"
            )
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == '__main__':
    print("Бот запущен...")
    executor.start_polling(dp, skip_updates=True)
