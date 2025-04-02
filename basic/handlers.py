from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, LabeledPrice
from aiogram.filters import Command
# from search.search import find_certificates_for_product
# from keyboard.inline import *
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
# from amount.prices import get_amounts
# from administrate.admin_file import *
from aiogram.types import InputFile, FSInputFile
# from documents.document import doc
# from messages.message import *
# from db.db import *
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from config import TARGET_USER_ID, PAY_TOKEN
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


router = Router()

class Send(StatesGroup):
    text = State()
    call = State()
    contact_info = State()

class WritePrice(StatesGroup):
    amount = State()


def create_contact_button()->ReplyKeyboardBuilder:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Поделиться номером", request_contact=True))
    return builder


@router.message(Command("start"))
async def send_welcome(message: Message, state: FSMContext):
    text = """
1. Снимите видео
2. Отправьте его в бот
3. Мы с Вами свяжемся
4. И всё решим удаленно и на месте!
    """
    await message.answer_video(video='BAACAgIAAxkBAAIB_GftCTo0Mp6MuNu1NIBgpSiWJRc3AAKtcAACWk1hS5WOjXenfmNjNgQ',
                               caption=text)
    await state.set_state(Send.text)

@router.message()
async def get_video_file_id(message: Message):
    video_id = message.video.file_id
    await message.answer(f"file_id этого видео: {video_id}")


@router.message(Send.text)
async def send_admin(message: Message, state: FSMContext, bot: Bot):
    if message.video:  # Проверяем, содержит ли сообщение видео
        video_id = message.video.file_id
        await state.update_data(video_id=video_id, caption=message.caption)
        kb = [
            [InlineKeyboardButton(text='Да', callback_data='send yes')],
            [InlineKeyboardButton(text='Загрузить заново', callback_data='send no')],
        ]
        await message.answer("Спасибо! Отправляем видео оператору?",
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

        # builder = create_contact_button()
        # await message.answer("Пожалуйста, отправьте ваш номер телефона или введите его вручную.", reply_markup=builder.as_markup(resize_keyboard=True))
        await state.set_state(Send.call)
    else:
        await message.answer("Отправьте, пожалуйста, видео.")

@router.message(Send.contact_info)
async def handle_contact_info(message: Message, state: FSMContext, bot: Bot):
    # Если пользователь поделился контактом через кнопку
    if message.contact:
        phone_number = message.contact.phone_number
    else:
        # Если пользователь вводит номер вручную
        phone_number = message.text.strip()
        if not phone_number.startswith("+") or not phone_number[1:].isdigit():
            await message.answer("Пожалуйста, введите корректный номер телефона в формате +79991234567.")
            return

    data = await state.get_data()
    # Сохраняем номер телефона и ник пользователя
    username = message.from_user.username or "Без ника"
    await state.update_data(phone=phone_number, username=username, user_id=message.from_user.id)
    caption = (
        f"Отправитель: @{username}\n"
        f"ID: {message.from_user.id}\n"
        f"Телефон: {phone_number}\n\n"
        f"{data.get('caption', '')}"
    )
    await bot.send_video(chat_id=TARGET_USER_ID, video=data['video_id'], caption=caption)
    kb = [
        [InlineKeyboardButton(text='Ввести стоимость', callback_data=f"price {message.from_user.id}")]
    ]
    await bot.send_message(chat_id=TARGET_USER_ID, text='Укажите стоимость для данной услуги:', reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await message.answer("Принято в работу, скоро с вами свяжется наш оператор!")

    await state.clear()


@router.callback_query(F.data.startswith('send'))
async def send_cal(callback: CallbackQuery, state: FSMContext, bot: Bot):
    action = callback.data.split()[1]
    await callback.message.delete()
    data = await state.get_data()
    if action == 'yes':
        builder = create_contact_button()
        await callback.message.answer("Пожалуйста, отправьте ваш номер телефона или введите его вручную.", reply_markup=builder.as_markup(resize_keyboard=True))
        await state.set_state(Send.contact_info)

        # caption = (
        #     f"Отправитель: @{data['username']}\n"
        #     f"ID: {data['user_id']}\n"
        #     f"Телефон: {data['phone']}\n\n"
        #     f"{data.get('caption', '')}"
        # )
        # await bot.send_video(chat_id=TARGET_USER_ID, video=data['video_id'], caption=caption)
        # kb = [
        #     [InlineKeyboardButton(text='Ввести стоимость', callback_data=f"price {data['user_id']}")]
        # ]
        # await bot.send_message(chat_id=TARGET_USER_ID, text='Укажите стоимость для данной услуги:', reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
        # await callback.message.edit_text("Принято в работу, скоро с вами свяжется наш оператор!")
    else:
        await state.set_state(Send.text)
        
        await callback.message.edit_text('Отправь видео, которое хочешь переслать оператору')

@router.callback_query(F.data.startswith('price'))
async def write_price(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split()[1])
    await callback.message.answer('Введите стоимость числом!')
    await state.set_state(WritePrice.amount)
    await state.update_data(user_id=user_id)


@router.message(WritePrice.amount)
async def state_wrte_price(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    try:
        price = int(message.text)
        kb = [
            [InlineKeyboardButton(text='Да', callback_data=f'user_price yes {price}')],
            [InlineKeyboardButton(text='Нет', callback_data='uesr_price no')]
        ]
        await bot.send_message(chat_id=data['user_id'], text=f'Стоимость вашей услуги составляет {price} р.\nРаботаем?', reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
        await state.clear()
    except ValueError:
        await message.answer('Введенный текст не является числом, введите значение снова')
        return
    
@router.callback_query(F.data.startswith('user_price'))
async def user_price(callback: CallbackQuery, bot: Bot):
    await callback.message.delete()
    action = callback.data.split()[1]
    price = callback.data.split()[2]
    if action == 'yes':
        await bot.send_message(chat_id=TARGET_USER_ID, text=f'Пользователь @{callback.from_user.username} утвердил стоимость {price} р.\nID:{callback.from_user.id}')
        await bot.send_invoice(
            chat_id=callback.from_user.id,
            title="Оплата услуги",
            description="Сумма для согласования, оплачивайте после выполнения работ",
            provider_token=PAY_TOKEN,
            payload=f"price",
            currency="rub",
            prices=[LabeledPrice(
                label="Оплата",
                amount=int(price) * 100,
            )],
            provider_data=None,
            is_flexible=False,
            request_timeout=10
        )
    else:
        await bot.send_message(chat_id=TARGET_USER_ID, text=f'Пользователь @{callback.from_user.username} не утвердил стоимость\nID:{callback.from_user.id}')
