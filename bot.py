import os
import re
import json
import asyncio
import urllib.parse
from dotenv import load_dotenv
from config import Messages, Buttons, Actions
from api import User, Appeals
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage


load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)

""" buttons config """
buttons = Buttons()
""" messages config """
messages = Messages()
""" actions config """
actions = Actions()
""" user api methods """
user_service = User()
""" appeals api methods """
appeal_service = Appeals()

user_cache = {}


class RegistrationStates(StatesGroup):
    """Registration of user state message"""
    waiting_for_email = State()
    waiting_for_message_to_user = State()


async def send_error(telegram_id):
    """Sending message Error"""
    message_text = messages.get_message('error').text
    return await send_msg(telegram_id, message_text)


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    """ Start handler, listening command /start """
    await send_main_menu(message.chat.id, message=message)


@dp.callback_query(lambda call: call.data == '/start')
async def start_call_back_handler(call: types.CallbackQuery):
    """ Start handler, listening call data '/start' """
    await send_main_menu(call.message.chat.id, call=call)


async def send_main_menu(chat_id: int, message: types.Message = None, call: types.CallbackQuery = None):
    """ Sends the main menu with inline keyboard """
    try:
        print(chat_id)
        user_data = await user_service.get_user_by_telegram_id(chat_id)
        print(user_data)
        if len(user_data) == 0:
            await send_register_button(chat_id)
        else:
            user_cache[chat_id] = {'user_data': user_data}
            builder = InlineKeyboardBuilder()
            lk_btn = buttons.get_button('lk')
            appeals_btn = buttons.get_button('appeals')

            builder.add(types.InlineKeyboardButton(text=lk_btn.text, web_app=lk_btn.data))
            builder.add(types.InlineKeyboardButton(text=appeals_btn.text, callback_data=appeals_btn.data))
            message_text = messages.get_message('select_action').text
            if message:
                await bot.send_message(chat_id, message_text, reply_markup=builder.as_markup())
            elif call:
                await call.message.edit_text(message_text, reply_markup=builder.as_markup())
    except Exception as e:
        print(e)
        await send_error(chat_id)


@dp.callback_query(lambda call: call.data == buttons.get_button('appeals').data)
async def appeals_callback(call: types.CallbackQuery):
    """ Sending Appeals button """
    try:
        builder = InlineKeyboardBuilder()
        for i in ['new_appeal', 'my_appeals']:
            button = buttons.get_button(i)
            builder.add(types.InlineKeyboardButton(text=button.text, callback_data=button.data))

        back_button = buttons.get_button('back_to_start')
        builder.row(*[types.InlineKeyboardButton(text=back_button.text, callback_data=back_button.data)])
        messages_text = messages.get_message('select_action').text
        await call.message.edit_text(text=messages_text, reply_markup=builder.as_markup())
    except Exception as e:
        print(e)
        await send_error(call.message.chat.id)


@dp.callback_query(lambda call: call.data == buttons.get_button('my_appeals').data)
async def user_appeals(call: types.CallbackQuery):
    """ Show User Appeals handler """
    try:
        user_data = user_cache.get(call.message.chat.id, {}).get('user_data', {})  # Безопасный доступ к данным
        user_cache[call.message.chat.id]['appeals'] = await appeal_service.get_user_appeals(user_data.get('id'))
        appeals = user_cache[call.message.chat.id]['appeals']

        builder = InlineKeyboardBuilder()
        buttons_in_row = 2
        temp_buttons = []
        for appeal in appeals:
            button_text = f"#{appeal.get('case_id')} {appeal.get('case_header')}"
            button_data = f"appeal_{appeal.get('case_id')}_{user_data.get('id')}"
            temp_buttons.append(types.InlineKeyboardButton(text=button_text, callback_data=button_data))

            if len(temp_buttons) == buttons_in_row:
                builder.row(*temp_buttons)
                temp_buttons = []

        if temp_buttons:
            builder.row(*temp_buttons)

        back_button = buttons.get_button('appeals')
        start_button = buttons.get_button('start')
        builder.row(*[
            types.InlineKeyboardButton(text='<- Назад', callback_data=back_button.data),
            types.InlineKeyboardButton(text=start_button.text, callback_data=start_button.data)
        ])
        edited_repy_text = messages.get_message('total_appeals').text + str(len(appeals))
        await call.message.edit_text(text=edited_repy_text, reply_markup=builder.as_markup())
    except Exception as e:
        print(e)
        await send_error(call.message.chat.id)


@dp.callback_query(lambda call: call.data.startswith("appeal_"))
async def appeal_callback_handler(call: types.CallbackQuery):
    """ Show user appeal handler """
    try:
        callback_data = call.data.split("_")[1:]
        appeal_id = callback_data[0]
        # user_id = callback_data[1]
        user_data = user_cache[call.message.chat.id]['user_data']
        appeals = user_cache[call.message.chat.id]['appeals']
        appeal = [i for i in appeals if appeal_id == str(i.get('case_id'))][0]

        appeal_ticket = (f"Обращение #{appeal.get('case_number')}\n\n"
                         f"Тема: {appeal.get('case_header')}\nСтатуc: {appeal.get('case_status')}\n"
                         f"Приоритет: {appeal.get('case_priority')}\nДата: {appeal.get('case_create_date')}\n"
                         f"Категория: {appeal.get('case_caregory')}\nПроект: {appeal.get('case_project')}\n"
                         f"Оператор: {appeal.get('case_operator')}\nИнициатор: {appeal.get('case_initiator')}")

        available_actions = actions.get_available_actions(user_data.get('role_id'), appeal.get('case_status_id'))

        builder = InlineKeyboardBuilder()
        back_button = buttons.get_button('my_appeals')
        start_button = buttons.get_button('start')

        action_buttons = []
        if len(available_actions) != 0:
            for action in available_actions:
                if 'command_id' == list(action.keys())[-1]:
                    action_buttons.append(types.InlineKeyboardButton(
                        text=action.get('name'),
                        callback_data=f"command_{action.get('command_id')}_appealId_{appeal_id}"
                    ))
                elif 'procedure' == list(action.keys())[-1]:
                    action_buttons.append(types.InlineKeyboardButton(
                        text=action.get('name'),
                        callback_data=f"p-{action.get('procedure').get('name')}"
                                      f"-a_id-{appeal_id}"
                                      f"-s_id-{appeal.get('case_status_id')}"
                    ))
            builder.row(*action_buttons)

        if user_data.get('role_id') == 14:
            builder.add(types.InlineKeyboardButton(
                text=buttons.get_button('message_to_user').text,
                callback_data=f"message_to_user-appeal_id-{appeal_id}"
            ))

        builder.row(*[
            types.InlineKeyboardButton(text='<- Назад', callback_data=back_button.data),
            types.InlineKeyboardButton(text=start_button.text, callback_data=start_button.data)
        ])

        await call.message.edit_text(appeal_ticket, reply_markup=builder.as_markup())

    except Exception as e:
        print(f'appeal_callback_handler: {e.__str__()}')
        await send_error(call.message.chat.id)


@dp.callback_query(lambda call: call.data.startswith('message_to_user-'))
async def message_to_user_handler(call: types.CallbackQuery, state: FSMContext):
    try:
        appeal_id = int(call.data.split('-')[-1])
        appeals = user_cache[call.message.chat.id]['appeals']
        appeal = [i for i in appeals if appeal_id == i.get('case_id')][0]
        print(appeal)
        user_cache[call.message.chat.id]['message_to_user'] = {
            'target_telegram_id': appeal.get('initiator_telegram_id')
        }
        await bot.send_message(call.message.chat.id, 'Введите текст сообщения')
        await state.set_state(RegistrationStates.waiting_for_message_to_user)
        await call.answer()
    except Exception as e:
        print(f'user_appeal_message_handler: {e.__str__()}')
        await send_error(call.message.chat.id)


@dp.message(StateFilter(RegistrationStates.waiting_for_message_to_user))
async def process_message_to_user(message: types.Message, state: FSMContext, bot: Bot):
    try:
        target_telegram_id = user_cache[message.chat.id]['message_to_user'].get('target_telegram_id')

        if message.text:
            # Отправляем текстовое сообщение
            await bot.send_message(chat_id=target_telegram_id, text=message.text)
        elif message.document:
            # Отправляем документ
            await bot.send_document(chat_id=target_telegram_id, document=message.document.file_id, caption=message.caption)
        elif message.photo:
             # Получаем file_id самой большой фотографии
             photo_file_id = message.photo[-1].file_id
             await bot.send_photo(chat_id=target_telegram_id, photo=photo_file_id, caption=message.caption)
        # Добавьте обработку для других типов контента (видео, аудио и т.д.)
        else:
            await bot.send_message(message.chat.id, "Неподдерживаемый тип сообщения.")
            await state.clear()  # Важно очистить состояние, если тип сообщения не поддерживается.
            return

        await bot.send_message(message.chat.id, 'Сообщение успешно отправлено пользователю.')
        await state.clear()  # Очищаем состояние после успешной отправки

    except Exception as e:
        print(f'process_message_to_user: {e.__str__()}')
        await send_error(message.chat.id, bot)


# @dp.message(StateFilter(RegistrationStates.waiting_for_message_to_user))
# async def process_message_to_user(message: types.Message, state: FSMContext):
#     try:
#         target_telegram_id = user_cache[message.chat.id]['message_to_user'].get('target_telegram_id')
#         await bot.forward_message(
#             chat_id=target_telegram_id,
#             from_chat_id=message.chat.id,
#             message_id=message.message_id
#         )
#         await bot.send_message(message.chat.id, 'Сообщение успешно отправлено')
#     except Exception as e:
#         print(f'process_message_to_user: {e.__str__()}')


@dp.callback_query(lambda call: call.data.startswith('p-'))
async def appeal_procedure_callback_handler(call: types.CallbackQuery):
    try:
        user_data = user_cache[call.message.chat.id].get('user_data')
        call_data_list = call.data.split('-')
        procedure_name = call_data_list[1]
        appeal_id = call_data_list[-3]
        appeal_status_id = call_data_list[-1]
        available_actions = actions.get_available_actions(int(user_data.get('role_id')), int(appeal_status_id))

        call_procedure = ''
        for i in available_actions:
            if 'procedure' in list(i.keys()):
                if i.get('procedure').get('name') == procedure_name:
                    call_procedure += f"{procedure_name}({int(appeal_id)}, {user_data.get('id')})"

        builder = InlineKeyboardBuilder()
        try:
            button = buttons.get_button('my_appeals')
            response = await appeal_service.call_procedure(call_procedure)
            print(response)
            builder.add(types.InlineKeyboardButton(text='Ок', callback_data=button.data))
            await call.message.edit_text(text=response.get('message'), reply_markup=builder.as_markup())
        except Exception as e:
            print(e)
            start_button = buttons.get_button('start')
            builder.add(types.InlineKeyboardButton(text=start_button.text, callback_data=start_button.data))
    except Exception as e:
        print(f'appeal_procedure_callback_handler: {e.__str__()}')


@dp.callback_query(lambda call: call.data.startswith('command_'))
async def appeal_command_callback_handler(call: types.CallbackQuery):
    """ Execute available appeal action by command_id and appeal_id """
    try:
        print(call.data)
        call_back_data = call.data.split("_")
        command_id = call_back_data[1]
        appeal_id = call_back_data[-1]

        builder = InlineKeyboardBuilder()
        try:
            button = buttons.get_button('my_appeals')
            response = await appeal_service.execute_appeal_command(int(command_id), int(appeal_id))
            print(response)
            builder.add(types.InlineKeyboardButton(text='Ок', callback_data=button.data))
            await call.message.edit_text(text=response.get('message'), reply_markup=builder.as_markup())
        except Exception as e:
            print(e)
            start_button = buttons.get_button('start')
            builder.add(types.InlineKeyboardButton(text=start_button.text, callback_data=start_button.data))
            await call.message.edit_text('Не удалось выполнить действие', reply_markup=builder.as_markup())
    except Exception as e:
        print(f"appeal_command_callback_handler: {e}")
        await send_error(call.message.chat.id)


@dp.callback_query(lambda call: call.data == buttons.get_button('new_appeal').data)
async def create_user_appeal(call: types.CallbackQuery):
    try:
        user_data = await user_service.get_user_by_telegram_id(call.message.chat.id)
        appeals_configuration = await appeal_service.get_appeal_configuration(user_data["id"])

        organizations = appeals_configuration['organization']
        projects = appeals_configuration['projects']
        categories = appeals_configuration['categories']
        priorities = appeals_configuration['priorities']

        if len(organizations) == 0 and len(projects) == 0 and len(categories) == 0 and len(priorities) == 0:
            message_text = messages.get_message('no_rights_appeal_adding').text
            await bot.send_message(call.message.chat.id, message_text)
            return

        base_url = "https://stlthwl.github.io/servicedesk-appeals/"
        params = {
            "telegram_id": str(call.message.chat.id),
            "app": "create_appeal",
            "organizations": json.dumps(appeals_configuration.get('organization', []), ensure_ascii=False),
            "projects": json.dumps(appeals_configuration.get('projects', []), ensure_ascii=False),
            "categories": json.dumps(appeals_configuration.get('categories', []), ensure_ascii=False),
            "priorities": json.dumps(appeals_configuration.get('priorities', []), ensure_ascii=False)
        }

        query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        url = f"{base_url}?{query_string}"

        appeal_adding_btn = buttons.get_appeal_adding_button('appeal_adding', url)
        button = types.KeyboardButton(text=appeal_adding_btn.get('text'), web_app=appeal_adding_btn.get('web_app'))
        markup = types.ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True)
        message_text = messages.get_message('appeal_adding').text
        await send_msg(call.message.chat.id, message_text, reply_markup=markup)
    except Exception as e:
        print(e)
        await send_error(call.message.chat.id)


@dp.message(lambda message: message.web_app_data)
async def web_app_message_handler(message: types.Message):
    """ Web App message handler """
    try:
        data = json.loads(message.web_app_data.data)
        if data['method'] == 'create_new_appeal':
            data['user_id'] = user_cache[message.chat.id]['user_data']['id']
            user_cache[message.chat.id]['new_appeal'] = data
            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(text='Да', callback_data='create_new_appeal'))
            builder.add(types.InlineKeyboardButton(text='Отмена', callback_data='appeals'))
            await bot.send_message(
                message.chat.id,
                text='Прикрепите файл при необходимости.\nСохранить?',
                reply_markup=builder.as_markup()
            )
    except Exception as e:
        print(e)
        await send_error(message.from_user.id)


@dp.message(F.content_type == types.ContentType.DOCUMENT)
async def file_handler(message: types.Message, bot: Bot):
    """ Saving filepath in user_cache """
    try:
        file_id = message.document.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"

        if user_cache[message.chat.id]:
            user_cache[message.chat.id]['file'] = {
                'path': file_url,
                'name': message.document.file_name.split('.')[0],
                'extension': message.document.file_name.split('.')[1]
            }

    except Exception as e:
        print(f'file_handler: {e}')
        await bot.send_message(
            chat_id=message.chat.id,
            text='Не удалось сохранить файл',
            reply_to_message_id=message.message_id
        )


@dp.callback_query(lambda call: call.data == 'create_new_appeal')
async def create_new_appeal(call: types.CallbackQuery):
    """ Saving New Appeal """
    try:
        new_appeal = user_cache[call.message.chat.id]['new_appeal']
        if new_appeal:
            if user_cache[call.message.chat.id]['file']:
                # print(user_cache[call.message.chat.id]['file'])
                new_appeal['file'] = user_cache[call.message.chat.id]['file']

            response = await appeal_service.create_new_appeal(new_appeal)
            print(response)
            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(text='Ок', callback_data='appeals'))
            await call.message.edit_text(
                text=f"Обращение #{response[0]['case_number']} успешно добавлено!",
                reply_markup=builder.as_markup()
            )
            await bot.send_message(
                chat_id=int(os.getenv('GROUP_ID')),
                text=f"Добавлено обращение #{response[0]['case_number']}\n\n"
            )
    except Exception as e:
        print(e)
        await send_error(call.message.chat.id)


@dp.callback_query(lambda call: call.data == buttons.get_button('link_telegram').data)
async def link_telegram_profile(call: types.CallbackQuery, state: FSMContext):
    """ Email Request """
    message_text = messages.get_message('email_enter').text
    await bot.send_message(call.message.chat.id, message_text)
    await state.set_state(RegistrationStates.waiting_for_email)
    await call.answer()


@dp.message(StateFilter(RegistrationStates.waiting_for_email))
async def process_email(message: types.Message, state: FSMContext):
    """
    Validate message contains Email address,
    Send Mail if Email address exists,
    Otherwise clear Email state and exit function
    """
    try:
        email = message.text
        if is_valid_email(email):
            user_data = await user_service.get_user_by_email(email)
            if len(user_data) == 0:
                message_text = messages.get_message('email_not_found').text
                await send_msg(message.chat.id, message_text)
            else:
                await user_service.send_confirm_email(message.chat.id, email)
                message_text = messages.get_message('email_confirm').text
                await message.reply(message_text)
            await state.clear()
        else:
            message_text = messages.get_message('email_not_valid').text
            await message.reply(message_text)
    except Exception as e:
        print(e)
        await state.clear()


def is_valid_email(email: str) -> bool:
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None


async def send_msg(chat_id, message, reply_markup=None):
    """ Sending message """
    if reply_markup:
        return await bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)
    else:
        return await bot.send_message(chat_id=chat_id, text=message)


async def send_register_button(chat_id: int):
    """ Sending registration button"""
    try:
        builder = InlineKeyboardBuilder()
        button = buttons.get_button('link_telegram')
        builder.add(types.InlineKeyboardButton(text=button.text, callback_data=button.data))
        message_text = messages.get_message('telegram_not_found').text
        await send_msg(chat_id, message_text, builder.as_markup())
    except Exception as e:
        print(e)
        await send_error(chat_id)


@dp.message()
async def message_handler(message: types.Message):
    """ Redirect to Start Command """
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
