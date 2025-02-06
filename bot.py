import os
import re
import json
import asyncio
import urllib.parse
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from api import User, Appeals

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)

user_service = User()
appeal_service = Appeals()
user_cech = {}


class RegistrationStates(StatesGroup):
    waiting_for_email = State()


async def send_error(telegram_id):
    return await send_msg(telegram_id, "Сервис временно недоступен")


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    try:
        telegram_id = message.chat.id
        print(telegram_id)
        user_data = await user_service.get_user_by_telegram_id(telegram_id)
        if len(user_data) == 0:
            await send_register_button(telegram_id)
        else:
            user_cech[message.chat.id] = {
                'user_data': user_data
            }
            await send_appeals_button(telegram_id)
    except Exception as e:
        print(e)
        await send_error(message.chat.id)


@dp.callback_query(lambda call: call.data == "appeals")
async def appeals_callback(call: types.CallbackQuery):
    try:
        await bot.send_message(call.message.chat.id, f"Обработан callback {call.data}")
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="Мои обращения", callback_data="my_appeals"))
        builder.add(types.InlineKeyboardButton(text="Новое обращение", callback_data="new_appeal"))
        await send_msg(
            call.message.chat.id,
            "Выберите действие",
            builder.as_markup()
        )
    except Exception as e:
        print(e)
        await send_error(call.message.chat.id)


@dp.callback_query(lambda call: call.data == "my_appeals")
async def user_appeals(call: types.CallbackQuery):
    try:
        await bot.send_message(call.message.chat.id, f"Обработан callback {call.data}")
        user_data = await user_service.get_user_by_telegram_id(call.message.chat.id)
        appeals = await appeal_service.get_user_appeals(user_data["id"])
        print(appeals)

        user_cech[call.message.from_user.id] = {
            'appeals': appeals
        }

        if len(appeals) == 0:
            await send_msg(call.message.chat.id, f"Всего обращений: {len(appeals)}")
        else:
            await send_msg(call.message.chat.id, f"Всего обращений: {len(appeals)}")
            # web_app_url = "https://ya.ru"
            # button = types.KeyboardButton(text="Перейти к обращениям", web_app={"url": web_app_url})
            # markup = types.ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True)

            # await send_msg(
            #     call.message.chat.id,
            #     'Нажмите кнопку ниже, чтобы перейти к просмотру обращений',
            #     reply_markup=markup
            # )
    except Exception as e:
        print(e)
        await send_error(call.message.chat.id)


@dp.callback_query(lambda call: call.data == "new_appeal")
async def create_user_appeal(call: types.CallbackQuery):
    try:
        await bot.send_message(call.message.chat.id, f"Обработан callback {call.data}")
        user_data = await user_service.get_user_by_telegram_id(call.message.chat.id)
        # собираем конфигурацию в строку json
        appeals_configuration = await appeal_service.get_appeal_configuration(user_data["id"])

        organizations = appeals_configuration['organization']
        projects = appeals_configuration['projects']
        categories = appeals_configuration['categories']
        priorities = appeals_configuration['priorities']

        msg_to_user = f"Нет прав для добавления обращений. Обратитесь к администратору @stlthwl"
        msg_to_group = (f"Попытка добавления нового обращения.\n Отсутствуют права на добавление обращений.\n"
                        f"Пользователь с telegram_id: {call.message.chat.id}")
        if len(organizations) == 0 and len(projects) == 0 and len(categories) == 0 and len(priorities) == 0:
            await bot.send_message(call.message.chat.id, msg_to_user)
            await bot.send_message(int(os.getenv('GROUP_ID')), msg_to_group)
            return

        base_url = "https://stlthwl.github.io/servicedesk-appeals/"
        params = {
            "telegram_id": str(call.message.chat.id),
            "app": "create_appeal",
            # Кодируем отдельные части
            "organizations": json.dumps(appeals_configuration.get('organization', []), ensure_ascii=False),
            "projects": json.dumps(appeals_configuration.get('projects', []), ensure_ascii=False),
            "categories": json.dumps(appeals_configuration.get('categories', []), ensure_ascii=False),
            "priorities": json.dumps(appeals_configuration.get('priorities', []), ensure_ascii=False)

        }
        # print(params)
        query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)  # Используем quote
        url = f"{base_url}?{query_string}"

        button = types.KeyboardButton(text="Перейти к обращениям", web_app={"url": url})
        markup = types.ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True)

        await send_msg(
            call.message.chat.id,
            'Открыть фому',
            reply_markup=markup
        )
    except Exception as e:
        print(e)
        await send_error(call.message.chat.id)


# Обработчик для сообщений из веб-приложения
@dp.message(lambda message: message.web_app_data)
async def web_app_message_handler(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        data['user_id'] = user_cech[message.chat.id]['user_data']['id']
        response = await appeal_service.create_new_appeal(data)
        print(response)
    except Exception as e:
        print(e)
        await send_error(message.from_user.id)


@dp.callback_query(lambda call: call.data == "link_telegramm")
async def link_telegram_profile(call: types.CallbackQuery, state: FSMContext):
    await bot.send_message(call.message.chat.id, f"Введите Email")
    await state.set_state(RegistrationStates.waiting_for_email)
    await call.answer()


@dp.message(StateFilter(RegistrationStates.waiting_for_email))
async def process_email(message: types.Message, state: FSMContext):
    email = message.text
    if is_valid_email(email):
        try:
            user_data = await user_service.get_user_by_email(email)
            if len(user_data) == 0:
                await send_system_button(message.chat.id)
            else:
                await user_service.send_confirm_email(message.chat.id, email)
                await message.reply("На почту отправлено письмо для подтверждения.")
        except Exception as e:
            print(e)
            await message.reply("Не удалось получить учетную запись по Email")
        await state.clear()
    else:
        await message.reply('Невалидная почта. Пожалуйста, введите корректный email.')


def is_valid_email(email: str) -> bool:
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None


async def send_msg(chat_id, message, reply_markup=None):
    if reply_markup:
        return await bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)
    else:
        return await bot.send_message(chat_id=chat_id, text=message)


async def send_register_button(chat_id: int):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Привязать учетную запись", callback_data="link_telegramm"))
    try:
        await send_msg(
            chat_id,
            "Учетная запись телеграм не найдена."
            "\nДля продолжения, привяжите телеграмм к учетной записи в системе.",
            builder.as_markup()
        )
    except Exception as e:
        print(e)
        await send_error(chat_id)


async def send_system_button(chat_id: int):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Войти в систему",
        web_app={"url": "https://lk.bingosoft-office.ru/"}
    ))
    try:
        await send_msg(
            chat_id,
            f"Для продолжения зарегистрируйте телеграмм и почту в системе "
            "или обратитесь к администратору",
            builder.as_markup())
    except Exception as e:
        print(e)
        await send_error(chat_id)


async def send_appeals_button(chat_id: int):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Обращения", callback_data="appeals"))
    try:
        await send_msg(chat_id, "Выберите действие", builder.as_markup())
    except Exception as e:
        print(e)
        await send_error(chat_id)


@dp.message()
async def message_handler(message: types.Message):
    # await message.reply(message.text) ### PLUG ###
    await start_handler(message)


async def main():
    try:
        await bot.delete_webhook()
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


def start_bot():
    asyncio.create_task(main())


if __name__ == "__main__":
    asyncio.run(main())
