from aiogram.exceptions import TelegramBadRequest
from certifi import where
from sqlalchemy.orm import selectinload
from aiogram import F, Router, Bot, types
from aiogram.filters import CommandStart, Command
from aiogram.filters.command import CommandObject
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.future import select
import logging
from quart import Quart
from datetime import datetime, date, time, timedelta
import pytz
from sqlalchemy import delete, update, func, desc, or_
from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)
import time as std_time
from email.utils import formataddr
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import aiohttp
import ssl
import asyncio
import re
from collections import defaultdict
from email.utils import encode_rfc2231
import math

from app.database.models import User, Beat, Email, async_session, Group, Settings, OneTimeSettings
from config import ADMIN_ID
import app.database.requests as rq
import app.keyboards as kb

rt = Router()
app = Quart(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLIENT_SECRET_FILE = 'client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
TOKEN_PICKLE = 'token.pickle'

class UserState(StatesGroup):
    waiting_for_gmail = State()
    waiting_for_password = State()
    waiting_for_emails = State()
    waiting_for_delete_emails = State()
    waiting_for_delete_beat = State()
    waiting_for_user_identifier_subscription = State()
    waiting_for_subscription_days = State()
    waiting_for_user_identifier_check = State()
    waiting_for_subscription_type = State()
    waiting_for_page_number = State()
    waiting_for_page_number_beats = State()
    waiting_for_page_number_beats_delete = State()
    waiting_for_interval = State()
    waiting_for_one_time_interval = State()
    waiting_for_main_time_choise = State()
    waiting_for_onetime_choise = State()
    waiting_admin_for_all = State()
    waiting_admin_for_premium = State()
    waiting_admin_for_basic = State()
    waiting_admin_for_free = State()
    waiting_for_promo_name = State()
    waiting_for_duration = State()
    waiting_for_promo_info = State()
    waiting_for_max_uses = State()
    waiting_for_search_username = State()
    waiting_for_promo_code = State()
class GroupState(StatesGroup):
    waiting_for_group_name = State()
    waiting_for_group_delete = State()
    waiting_for_email = State()
    waiting_for_beat = State()
    editing_subject = State()
    editing_message = State()
    editing_send_time = State()
    editing_quantity_beat = State()
    periodicity = State()
    waiting_for_group_name_swap = State()
    renaming_group = State()
    editing_one_time_subject = State()
    editing_one_time_message = State()
    editing_one_time_time = State()
    editing_one_time_quantity = State()
class FSMEmail(StatesGroup):
    awaiting_email = State()
    awaiting_subject = State()
    awaiting_message = State()
    awaiting_beats = State()
    confirming = State()
    awaiting_text = State()
    deleting_emails = State()
user_data = {}

def is_admin(user_id):
    return user_id in ADMIN_ID

@rt.message(CommandStart(deep_link=True))
async def cmd_start_deeplink(message: Message, command: CommandObject, bot: Bot):
    user_id = message.from_user.id
    args = command.args

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user or user.gmail == 'не указано':
            referrer_id = int(args.split('_')[1]) if args and args.startswith('ref_') else None
            print(referrer_id if referrer_id else "False")
            await rq.set_user(message.from_user.id, message.from_user.username)
            async with async_session() as session:
                result = await session.execute(select(User).filter(User.user_id == user_id))
                user = result.scalar_one_or_none()


                if referrer_id and not user.used_referral:
                    user.referrer_id = referrer_id
                    user.referral_discount_expire = datetime.now() + timedelta(days=14)
                    user.used_referral = bool(referrer_id)
                    ref_result = await session.execute(select(User).filter(User.user_id == user.referrer_id))
                    referrer = ref_result.scalar_one_or_none()
                    if referrer:
                        for admin_id in ADMIN_ID:
                            await bot.send_message(
                                admin_id,
                                f"@{user.username} перешел от @{referrer.username}",
                                parse_mode="HTML"
                            )

                session.add(user)
                await session.commit()
        await cmd_start(message)

@rt.message(CommandStart())
async def cmd_start(message: Message):
    await rq.set_user(message.from_user.id, message.from_user.username)
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    if user.language == 2:
                        await message.answer(
                            '<strong>🪫 Your subscription has ended!</strong> Mailing has been paused.\n\n'
                            'To continue using the service, choose an action using the buttons below:',
                            parse_mode='HTML', reply_markup=kb.end_sub_eng
                        )  
                    else:
                        await message.answer(
                            '<strong>🪫 Ваша подписка завершилась!</strong> Рассылка приостановлена.\n\n'
                            'Чтобы продолжить пользоваться сервисом, выберите действия по кнопкам ниже:',
                            parse_mode='HTML', reply_markup=kb.end_sub
                            )
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                if user.language == 0:
                    await  message.answer('<strong>Choose language | Выберите язык</strong>', parse_mode='HTML',
                                          reply_markup=kb.choice_lang)
                elif user.language == 1:
                    await message.answer(f'<strong>👋🏻 Привет, {message.from_user.first_name}!</strong>\n\n'
                                         f'📨 <strong>Be Twin — сервис автоматической email-рассылки для битмейкеров</strong>\n\n'
                                         f'<a href="https://telegra.ph/Logistika-i-eyo-sekrety-09-24">Как работает Be Twin?</a> | '
                                         f'<a href="https://t.me/urtwinews">Be Twin News</a>',
                                         parse_mode='HTML', disable_web_page_preview=True, reply_markup=kb.start)
                else:
                    await message.answer(f'<strong>👋🏻 Hi, {message.from_user.first_name}!</strong>\n\n'
                                         f'📨 <strong>Be Twin is an automated email marketing service for beatmakers</strong>\n\n'
                                         f'<a href="https://telegra.ph/Logistika-i-eyo-sekrety-09-24">How does Be Twin work?</a> | '
                                         f'<a href="https://t.me/urtwinews">Be Twin News</a>',
                                         parse_mode='HTML', disable_web_page_preview=True, reply_markup=kb.start_eng)

@rt.callback_query(F.data.in_(['eng', 'rus']))
async def choice_language(callback: CallbackQuery):
    user_id = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if callback.data == 'eng':
            await callback.answer('🇺🇸 English')
            user.language = 2
            await callback.message.answer(f'<strong>👋🏻 Hi, {callback.from_user.first_name}!</strong>\n\n'
                                 f'📨 <strong>Be Twin is an automated email marketing service for beatmakers</strong>\n\n'
                                 f'<a href="https://telegra.ph/Logistika-i-eyo-sekrety-09-24">How does Be Twin work?</a> | '
                                 f'<a href="https://t.me/urtwinews">Be Twin News</a>',
                                 parse_mode='HTML', disable_web_page_preview=True, reply_markup=kb.start_eng)
            if user.used_referral and not user.subscription_start and user.gmail == 'не указано':
                await callback.message.answer(
                    '<b>You followed a referral link — this means, according to our rules, you get a 20% discount on any subscription</b>\n\n'
                    '<b>❗️Important:</b> <u>the discount is valid for only 2 weeks</u>, and if you follow another referral link, the discount will become unavailable to you.\n\n'
                    'You can see the discount after registration in the "🎟 <b>Subscription</b>" section\n\n\n'
                    '<b>Real results of Be Twin users:</b>\n\n'
                    ' • $1600 per month — passively via the bot’s automatic mailings\n'
                    ' • Over $400 monthly for a year and longer\n'
                    ' • Up to $600 per single deal\n\n\n'
                    '<b>We operate as transparently as possible:</b>\n\n'
                    '👤 The creator and main administrator @nemxxo — a chart-topping producer with tens of millions '
                    'of streams, a proven reputation, and many years of industry experience.\n\n'
                    'For any questions about the service, you can directly message him @xxx',
                    parse_mode='HTML'
                )

        else:
            await callback.answer('🇷🇺 Русский')
            user.language = 1

            await callback.message.answer(f'<strong>👋🏻 Привет, {callback.from_user.first_name}!</strong>\n\n'
                                 f'📨 <strong>Be Twin — сервис автоматической email-рассылки для битмейкеров</strong>\n\n'
                                 f'<a href="https://telegra.ph/Logistika-i-eyo-sekrety-09-24">Как работает Be Twin?</a> | '
                                 f'<a href="https://t.me/urtwinews">Be Twin News</a>',
                                 parse_mode='HTML', disable_web_page_preview=True, reply_markup=kb.start)
            if user.used_referral and not user.subscription_start and user.gmail == 'не указано':
                await callback.message.answer(
                    '<b>Вы перешли по реферальной ссылке — это значит, что по нашим правилам вы получаете скидку 20% на любую подписку</b>\n\n'
                    '<b>❗️Важно:</b> <u>скидка действует только 2 недели</u>, а при переходе по другой реферальной ссылке скидка станет для вас недоступна.\n\n'
                    'Скидку можно увидеть после регистрации в разделе «🎟 <b>Подписка</b>»\n\n\n'
                    '<b>Реальные результаты пользователей Be Twin:</b>\n\n'
                    ' • $1600 за месяц — пассивно через автоматические рассылки бота\n'
                    ' • Более $400 ежемесячно на протяжении года и дольше\n'
                    ' • До $600 за одну сделку\n\n\n'
                    '<b>Мы работаем максимально прозрачно:</b>\n\n'
                    '👤 Создатель и главный администратор @nemxxo — продюсер топовых артистов и треков-миллионников, '
                    'с проверенной репутацией и многолетней историей в индустрии. \n\n'
                    'По всем вопросам о сервисе вы можете напрямую написать ему в личные сообщения @xxx',
                    parse_mode='HTML')
        await session.commit()


@rt.message(Command("restart"))
async def restart(message: Message):
    await cmd_start(message)

@rt.message(Command('apanel'))
async def apanel(message: Message):
    if is_admin(message.from_user.id):
        await message.answer('<strong>Возможные команды:</strong>', reply_markup=kb.adm_start, parse_mode='HTML')

#Выдача подписки admin
@rt.callback_query(F.data == 'sub')
async def start_subscription(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    if not is_admin(user_id):
        await callback.answer("Вы не являетесь администратором!", reply_markup=kb.adm_back)
        return

    await state.set_state(UserState.waiting_for_user_identifier_subscription)
    await callback.answer('🎟️ Выдать подписку')
    await callback.message.edit_text("Введите @username, ID или email пользователя:",
                                     reply_markup=kb.adm_back)
@rt.message(UserState.waiting_for_user_identifier_subscription)
async def get_user_identifier(message: Message, state: FSMContext):
    identifier = message.text.strip()
    user = None

    async with async_session() as session:
        if identifier.startswith('@'):
            username = identifier[1:]
            result = await session.execute(select(User).filter(User.username == username))
        elif identifier.isdigit():
            result = await session.execute(select(User).filter(User.user_id == int(identifier)))
        elif '@' in identifier:
            result = await session.execute(select(User).filter(User.gmail == identifier))
        else:
            await message.answer("<strong>Введите корректный @username, ID или email</strong>", reply_markup=kb.adm_back, parse_mode='HTML')
            return

        user = result.scalar_one_or_none()

        if not user:
            await message.answer("Пользователь не найден", reply_markup=kb.adm_back)
            return

        await state.update_data(user_identifier=identifier, user_id=user.user_id)

    await state.set_state(UserState.waiting_for_subscription_type)
    await message.answer(f"<strong>Выберите тип подписки для пользователя:</strong> {identifier}",
                         reply_markup=kb.premium_basic, parse_mode='HTML')
@rt.callback_query(F.data.in_(['give_premium', 'give_basic']))
async def set_subscription_type(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    type_ = 'premium' if callback.data == 'give_premium' else 'basic'

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            user.mails_per_day = 450
            user.extra_mail = 50
            await state.update_data(subscription_type=type_)  
            await callback.message.edit_text(
                f"<strong>Подписка успешно обновлена на</strong> {user.subscription}. <strong>Введите количество дней:</strong>",
                reply_markup=kb.adm_add, parse_mode='HTML')

        else:
            await callback.message.edit_text("Пользователь не найден", reply_markup=kb.adm_back)

        await session.commit()

    await state.set_state(UserState.waiting_for_subscription_days)
@rt.callback_query(F.data == 'adm_give')
async def give_30_days(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    input_data = data.get('user_identifier')
    user_id = data['user_id']
    new_subscription = data.get('subscription_type')
    days = 30

    if not input_data:
        await callback.message.edit_text("Не указан идентификатор пользователя.", reply_markup=kb.adm_back)
        return

    async with async_session() as session:
        user = None

        if input_data.startswith('@'):
            result = await session.execute(select(User).filter(User.username == input_data[1:]))
        elif input_data.isdigit():
            result = await session.execute(select(User).filter(User.user_id == int(input_data)))
        elif '@' in input_data:
            result = await session.execute(select(User).filter(User.gmail == input_data))
        else:
            await callback.message.edit_text("Некорректный формат идентификатора.", reply_markup=kb.adm_back)
            return

        user = result.scalar_one_or_none()

        if user:
            if user.subscription == new_subscription:
                user.subscription_day += days
            else:
                user.subscription_day = days

            user.subscription = new_subscription
            user.block = False
            if user.referrals >= 1 and user.referral_discount > 0:
                user.referral_discount = 0

            if user.active_promo_code:
                promo_info = await rq.get_promo_info(session, user.active_promo_code)

                if promo_info and promo_info.subscription_type in ["basic", "basic+premium"] and new_subscription == 'basic':
                    user.active_promo_code = None
                    user.promo_expiration = None
                    user.notified_one_day = False

                elif promo_info and promo_info.subscription_type in ["premium", "basic+premium"] and new_subscription == "premium":
                    user.active_promo_code = None
                    user.promo_expiration = None
                    user.notified_one_day = False
            label = f"@{user.username}" if user.username else user.gmail or str(user.user_id)
            if user.used_referral and not user.subscription_start:
                if user.referrer_id:
                    ref_result = await session.execute(select(User).filter(User.user_id == user.referrer_id))
                    referrer = ref_result.scalar_one_or_none()

                    if referrer:
                        current_value = referrer.referral_discount
                        add_value = 20 if referrer.referrals in [0, 1, 2, 3, 4, 5] else 30 if referrer.referrals in [6, 7, 8, 9, 10] else 50
                        referrer.referral_discount = min(current_value + add_value, 100)

                        referrer.referrals += 1
                        if referrer.notifications_sub:
                            if referrer.language == 2:
                                await bot.send_message(
                                    referrer.user_id,
                                    f"<b>💰 Your referral has subscribed to Be Twin</b>\n\n"
                                    f"You have received a "
                                    f"{20 if referrer.referrals in [0, 1, 2, 3, 4, 5] else 30 if referrer.referrals in [6, 7, 8, 9, 10] else 50}% "
                                    f"discount on any subscription",
                                    parse_mode="HTML", reply_markup=kb.turn_off_notifications_eng_sub
                                )
                            else:
                                await bot.send_message(
                                    referrer.user_id,
                                    f"<b>💰 Ваш реферал оформил подписку в Be Twin</b>\n\n"
                                    f"Вам начислена "
                                    f"{20 if referrer.referrals in [0, 1, 2, 3, 4, 5] else 30 if referrer.referrals in [6, 7, 8, 9, 10] else 50}% "
                                    f"скидка на любую подписку", parse_mode="HTML", reply_markup=kb.turn_off_notifications_sub
                                )
            if user.used_referral and user.subscription_start:
                if user.referrer_id:
                    ref_result = await session.execute(select(User).filter(User.user_id == user.referrer_id))
                    referrer = ref_result.scalar_one_or_none()

                    if referrer:
                        current_value = referrer.referral_discount
                        add_value = 5
                        referrer.referral_discount = min(current_value + add_value, 100)

                        if referrer.language == 2:
                            await bot.send_message(
                                referrer.user_id,
                                f"<b>💰 Your referral has renewed their subscription in Be Twin</b>\n\n"
                                f"You have received a "
                                f"5% discount on any subscription",
                                parse_mode="HTML"
                            )
                        else:
                            await bot.send_message(
                                referrer.user_id,
                                f"<b>💰 Ваш реферал продлил подписку в Be Twin</b>\n\n"
                                f"Вам начислена "
                                f"5% скидка на любую подписку", parse_mode="HTML"
                            )

            user.subscription_start = datetime.now(pytz.timezone('Europe/Moscow'))
            user.referral_discount_expire = None
            await callback.message.edit_text(
                f"<strong>Подписка для пользователя</strong> {label} <strong>успешно обновлена.</strong> \n\n"
                f"<strong>Подписка:</strong> {user.subscription} \n"
                f"<strong>Общее количество дней:</strong> {user.subscription_day}",
                reply_markup=kb.adm_start, parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                f"Пользователь с идентификатором {input_data} не найден в базе",
                reply_markup=kb.adm_back
            )

        await session.commit()

    await state.clear()
@rt.message(UserState.waiting_for_subscription_days)
async def get_subscription_days(message: Message, state: FSMContext, bot: Bot):
    try:
        days = int(message.text.strip())
    except ValueError:
        await message.answer("<strong>Введите корректное количество дней</strong>", reply_markup=kb.adm_add, parse_mode='HTML')
        return

    data = await state.get_data()
    user_id = data['user_id']
    new_subscription = data.get('subscription_type')

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.subscription == new_subscription:
                user.subscription_day += days
            else:
                user.subscription_day = days

            user.subscription = new_subscription
            user.block = False
            if user.referrals >= 1 and user.referral_discount > 0 and days >= 30:
                user.referral_discount = 0

            if user.active_promo_code:
                promo_info = await rq.get_promo_info(session, user.active_promo_code)

                if promo_info and promo_info.subscription_type in ["basic", "basic+premium"] and new_subscription == 'basic':
                    user.active_promo_code = None
                    user.promo_expiration = None
                    user.notified_one_day = False

                elif promo_info and promo_info.subscription_type in ["premium", "basic+premium"] and new_subscription == "premium":
                    user.active_promo_code = None
                    user.promo_expiration = None
                    user.notified_one_day = False
            if user.used_referral and not user.subscription_start:
                if user.referrer_id:
                    ref_result = await session.execute(select(User).filter(User.user_id == user.referrer_id))
                    referrer = ref_result.scalar_one_or_none()

                    if referrer:
                        current_value = referrer.referral_discount
                        add_value = 20 if referrer.referrals in [0, 1, 2, 3, 4, 5] else 30 if referrer.referrals in [10, 6,
                                                                                                                     7,
                                                                                                                     8,
                                                                                                                     9] else 50
                        referrer.referral_discount = min(current_value + add_value, 100)
                        referrer.referrals += 1
                        if referrer.notifications_sub:
                            if referrer.language == 2:
                                await bot.send_message(
                                    referrer.user_id,
                                    f"<b>💰 Your referral has subscribed to Be Twin</b>\n\n"
                                    f"You have received a "
                                    f"{20 if referrer.referrals in [0, 1, 2, 3, 4, 5] else 30 if referrer.referrals in [6, 7, 8, 9, 10] else 50}% "
                                    f"discount on any subscription",
                                    parse_mode="HTML", reply_markup=kb.turn_off_notifications_eng_sub
                                )
                            else:
                                await bot.send_message(
                                    referrer.user_id,
                                    f"<b>💰 Ваш реферал оформил подписку в Be Twin</b>\n\n"
                                    f"Вам начислена "
                                    f"{20 if referrer.referrals in [0, 1, 2, 3, 4, 5] else 30 if referrer.referrals in [6, 7, 8, 9, 10] else 50}% "
                                    f"скидка на любую подписку", parse_mode="HTML", reply_markup=kb.turn_off_notifications_sub
                                )
            if user.used_referral and user.subscription_start and days >= 30:
                if user.referrer_id:
                    ref_result = await session.execute(select(User).filter(User.user_id == user.referrer_id))
                    referrer = ref_result.scalar_one_or_none()

                    if referrer:
                        current_value = referrer.referral_discount
                        add_value = 5
                        referrer.referral_discount = min(current_value + add_value, 100)

                        if referrer.language == 2:
                            await bot.send_message(
                                referrer.user_id,
                                f"<b>💰 Your referral has renewed their subscription in Be Twin</b>\n\n"
                                f"You have received a "
                                f"5% discount on any subscription",
                                parse_mode="HTML"
                            )
                        else:
                            await bot.send_message(
                                referrer.user_id,
                                f"<b>💰 Ваш реферал продлил подписку в Be Twin</b>\n\n"
                                f"Вам начислена "
                                f"5% скидка на любую подписку", parse_mode="HTML"
                            )
            user.referral_discount_expire = None
            user.subscription_start = datetime.now(pytz.timezone('Europe/Moscow'))
            await message.answer(
                f"<strong>Подписка успешно обновлена.</strong> \n\n"
                f"<strong>Подписка:</strong> {user.subscription} \n"
                f"<strong>Общее количество дней:</strong> {user.subscription_day}",
                reply_markup=kb.adm_start, parse_mode="HTML"
            )
        else:
            await message.answer("<strong>Пользователь не найден</strong>", reply_markup=kb.adm_back, parse_mode='HTML')

        await session.commit()

    await state.clear()
@rt.callback_query(F.data == 'gsub')
async def check_subscription_request(callback: CallbackQuery, state: FSMContext):
    await callback.answer('🪪 Проверить подписку')
    await callback.message.edit_text("<strong>Введите @username, ID или email пользователя:</strong>",
                                     reply_markup=kb.adm_back, parse_mode='HTML')
    await state.set_state(UserState.waiting_for_user_identifier_check)
@rt.message(UserState.waiting_for_user_identifier_check)
async def get_user_subscription(message: Message, state: FSMContext):
    identifier = message.text.strip()
    user = None

    async with async_session() as session:
        if identifier.startswith('@'):
            result = await session.execute(select(User).filter(User.username == identifier[1:]))
        elif identifier.isdigit():
            result = await session.execute(select(User).filter(User.user_id == int(identifier)))
        elif '@' in identifier:
            result = await session.execute(select(User).filter(User.gmail == identifier))
        else:
            await message.answer("<strong>Введите корректный @username, ID или email<strong>", reply_markup=kb.adm_back, parse_mode='HTML')
            return

        user = result.scalar_one_or_none()

        if user:
            await message.answer(f"<strong>Пользователь:</strong> {user.username or user.gmail}\n"
                                 f"<strong>Подписка:</strong> {user.subscription or 'нет'}\n"
                                 f"<strong>Осталось дней:</strong> {user.subscription_day}",
                                 reply_markup=kb.adm_start, parse_mode="HTML")
        else:
            await message.answer("Пользователь не найден", reply_markup=kb.adm_back)

    await state.clear()

@rt.callback_query(F.data == 'mail_2_sub')
async def mail(callback: CallbackQuery):
    await callback.answer('📪 Рассылка')
    await callback.message.edit_text('<strong>Выберите вид рассылки:</strong>', parse_mode='HTML',
                                     reply_markup=kb.mail_2_sub)

@rt.callback_query(F.data == 'for_all')
async def start_mailing(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    if not is_admin(user_id):
        await callback.answer("Вы не являетесь администратором!", reply_markup=kb.adm_back)
        return

    await state.set_state(UserState.waiting_admin_for_all)
    await callback.answer('📪 Общая рассылка')
    await callback.message.edit_text("Введите текст сообщения для рассылки:", reply_markup=kb.adm_back)
@rt.message(UserState.waiting_admin_for_all)
async def get_mailing_message(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Только администратор может отправлять рассылки", reply_markup=kb.adm_back)
        return

    mailing_text = message.caption if message.caption else message.text
    photo = message.photo[-1] if message.photo else None
    video = message.video if message.video else None
    document = message.document if message.document else None
    audio = message.audio if message.audio else None

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id.isnot(None)))
        users = result.scalars().all()

        if not users:
            await message.answer("Нет пользователей для рассылки", reply_markup=kb.adm_back)
            return

        print(f"Найдено пользователей: {[user.user_id for user in users]}")
        for user in users:
            try:
                print(f"Отправка сообщения пользователю с ID: {user.user_id}")

                if photo:
                    photo_file = photo.file_id
                    if mailing_text:
                        await message.bot.send_photo(user.user_id, photo_file, caption=mailing_text, parse_mode='HTML')
                    else:
                        await message.bot.send_photo(user.user_id, photo_file)

                elif video:
                    video_file = video.file_id
                    if mailing_text:
                        await message.bot.send_video(user.user_id, video_file, caption=mailing_text)
                    else:
                        await message.bot.send_video(user.user_id, video_file)

                elif document:
                    document_file = document.file_id
                    if mailing_text:
                        await message.bot.send_document(user.user_id, document_file, caption=mailing_text)
                    else:
                        await message.bot.send_document(user.user_id, document_file)

                elif audio:
                    audio_file = audio.file_id
                    if mailing_text:
                        await message.bot.send_audio(user.user_id, audio_file, caption=mailing_text)
                    else:
                        await message.bot.send_audio(user.user_id, audio_file)

                elif mailing_text:
                    await message.bot.send_message(user.user_id, mailing_text, parse_mode='HTML',
                                                   disable_web_page_preview=True)

            except Exception as e:
                print(f"Ошибка при отправке сообщения пользователю {user.user_id}: {e}")

        await message.answer("Сообщение успешно отправлено всем пользователям", reply_markup=kb.adm_back)
        await state.clear()

@rt.callback_query(F.data == 'who_premium')
async def for_sub(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    if not is_admin(user_id):
        await callback.answer("Вы не являетесь администратором!", reply_markup=kb.adm_back)
        return

    await state.set_state(UserState.waiting_admin_for_premium)
    await callback.answer('PREMIUM')
    await callback.message.edit_text("Введите текст сообщения для рассылки PREMIUM:", reply_markup=kb.adm_back)
@rt.message(UserState.waiting_admin_for_premium)
async def get_mailing_for_sub(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Только администратор может отправлять рассылки", reply_markup=kb.adm_back)
        return

    mailing_text = message.caption if message.caption else message.text
    photo = message.photo[-1] if message.photo else None
    video = message.video if message.video else None
    document = message.document if message.document else None
    audio = message.audio if message.audio else None

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.subscription == 'premium'))
        users = result.scalars().all()

        if not users:
            await message.answer("Нет подписчиков для рассылки", reply_markup=kb.adm_back)
            return

        for user in users:
            try:
                print(f"Отправка сообщения пользователю с ID: {user.user_id}")

                if photo:
                    photo_file = photo.file_id
                    if mailing_text:
                        await message.bot.send_photo(user.user_id, photo_file, caption=mailing_text, parse_mode='HTML')
                    else:
                        await message.bot.send_photo(user.user_id, photo_file)

                elif video:
                    video_file = video.file_id
                    if mailing_text:
                        await message.bot.send_video(user.user_id, video_file, caption=mailing_text)
                    else:
                        await message.bot.send_video(user.user_id, video_file)

                elif document:
                    document_file = document.file_id
                    if mailing_text:
                        await message.bot.send_document(user.user_id, document_file, caption=mailing_text)
                    else:
                        await message.bot.send_document(user.user_id, document_file)

                elif audio:
                    audio_file = audio.file_id
                    if mailing_text:
                        await message.bot.send_audio(user.user_id, audio_file, caption=mailing_text)
                    else:
                        await message.bot.send_audio(user.user_id, audio_file)

                elif mailing_text:
                    await message.bot.send_message(user.user_id, mailing_text, parse_mode='HTML',
                                                   disable_web_page_preview=True)

            except Exception as e:
                print(f"Ошибка при отправке сообщения подписчику {user.user_id}: {e}")

    await message.answer("Сообщение успешно отправлено PREMIUM подписчикам", reply_markup=kb.adm_back)
    await state.clear()

@rt.callback_query(F.data == 'who_basic')
async def who_free(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    if not is_admin(user_id):
        await callback.answer("Вы не являетесь администратором!", reply_markup=kb.adm_back)
        return

    await state.set_state(UserState.waiting_admin_for_basic)
    await callback.answer('BASIC')
    await callback.message.edit_text("Введите текст сообщения для рассылки BASIC:", reply_markup=kb.adm_back)
@rt.message(UserState.waiting_admin_for_basic)
async def get_mailing_who_free(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Только администратор может отправлять рассылки", reply_markup=kb.adm_back)
        return

    photo = message.photo[-1] if message.photo else None
    video = message.video if message.video else None
    document = message.document if message.document else None
    audio = message.audio if message.audio else None
    mailing_text = message.caption if message.caption else message.text

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.subscription == 'basic'))
        users = result.scalars().all()

        if not users:
            await message.answer("Нет пользователей, кто брал бесплатную подписку", reply_markup=kb.adm_back)
            return

        for user in users:
            try:
                print(f"Отправка сообщения пользователю с ID: {user.user_id}")

                if photo:
                    photo_file = photo.file_id
                    if mailing_text:
                        await message.bot.send_photo(user.user_id, photo_file, caption=mailing_text, parse_mode='HTML')
                    else:
                        await message.bot.send_photo(user.user_id, photo_file)

                elif video:
                    video_file = video.file_id
                    if mailing_text:
                        await message.bot.send_video(user.user_id, video_file, caption=mailing_text)
                    else:
                        await message.bot.send_video(user.user_id, video_file)

                elif document:
                    document_file = document.file_id
                    if mailing_text:
                        await message.bot.send_document(user.user_id, document_file, caption=mailing_text)
                    else:
                        await message.bot.send_document(user.user_id, document_file)

                elif audio:
                    audio_file = audio.file_id
                    if mailing_text:
                        await message.bot.send_audio(user.user_id, audio_file, caption=mailing_text)
                    else:
                        await message.bot.send_audio(user.user_id, audio_file)

                elif mailing_text:
                    await message.bot.send_message(user.user_id, mailing_text, parse_mode='HTML',
                                                   disable_web_page_preview=True)

            except Exception as e:
                print(f"Ошибка при отправке сообщения {user.user_id}: {e}")

    await message.answer("Сообщение успешно отправлено BASIC подписчикам", reply_markup=kb.adm_back)
    await state.clear()

@rt.callback_query(F.data == 'who_free')
async def who_no_free(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    if not is_admin(user_id):
        await callback.answer("Вы не являетесь администратором!", reply_markup=kb.adm_back)
        return

    await state.set_state(UserState.waiting_admin_for_free)
    await callback.answer('FREE')
    await callback.message.edit_text("Введите текст сообщения для рассылки FREE:", reply_markup=kb.adm_back)
@rt.message(UserState.waiting_admin_for_free)
async def get_mailing_who_no_free(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Только администратор может отправлять рассылки", reply_markup=kb.adm_back)
        return

    mailing_text = message.caption if message.caption else message.text
    photo = message.photo[-1] if message.photo else None
    video = message.video if message.video else None
    document = message.document if message.document else None
    audio = message.audio if message.audio else None
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.subscription == 'free'))
        users = result.scalars().all()

        if not users:
            await message.answer("Нет пользователей, кто не брал бесплатную подписку", reply_markup=kb.adm_back)
            return

        for user in users:
            try:
                print(f"Отправка сообщения пользователю с ID: {user.user_id}")

                if photo:
                    photo_file = photo.file_id
                    if mailing_text:
                        await message.bot.send_photo(user.user_id, photo_file, caption=mailing_text, parse_mode='HTML')
                    else:
                        await message.bot.send_photo(user.user_id, photo_file)

                elif video:
                    video_file = video.file_id
                    if mailing_text:
                        await message.bot.send_video(user.user_id, video_file, caption=mailing_text)
                    else:
                        await message.bot.send_video(user.user_id, video_file)

                elif document:
                    document_file = document.file_id
                    if mailing_text:
                        await message.bot.send_document(user.user_id, document_file, caption=mailing_text)
                    else:
                        await message.bot.send_document(user.user_id, document_file)

                elif audio:
                    audio_file = audio.file_id
                    if mailing_text:
                        await message.bot.send_audio(user.user_id, audio_file, caption=mailing_text)
                    else:
                        await message.bot.send_audio(user.user_id, audio_file)

                elif mailing_text:
                    await message.bot.send_message(user.user_id, mailing_text, parse_mode='HTML',
                                                   disable_web_page_preview=True)

            except Exception as e:
                print(f"Ошибка при отправке сообщения {user.user_id}: {e}")

    await message.answer("Сообщение успешно отправлено FREE подписчикам", reply_markup=kb.adm_back)
    await state.clear()











@rt.callback_query(F.data == 'promo')
async def promo(callback: CallbackQuery, page: int = 1):
    async with async_session() as session:
        total_promos = await rq.get_promo_count(session)
        await callback.answer('🎫 Промокоды')
        if total_promos == 0:
            await callback.message.edit_text(
                "❗️ Промокодов пока нет.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="➕ Добавить", callback_data="add_promo")],
                        [InlineKeyboardButton(text="↩️ Назад", callback_data="adm_back")]
                    ]
                )
            )
            return

        total_pages = (total_promos + 4) // 5
        page = (page - 1) % total_pages + 1
        offset = (page - 1) * 5
        promo_codes = await rq.get_promo_codes(session, offset=offset)

        await callback.message.edit_text(
            "📋 Вот список промокодов:",
            reply_markup=get_promo_buttons(page, total_pages, promo_codes),
        )
async def promo_message(message: Message):
    async with async_session() as session:
        total_promos = await rq.get_promo_count(session)

        if total_promos == 0:
            await message.answer(
                "❗️ Промокодов пока нет.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="➕ Добавить", callback_data="add_promo")],
                        [InlineKeyboardButton(text="↩️ Назад", callback_data="adm_back")]
                    ]
                )
            )
            return

        total_pages = (total_promos + 4) // 5
        promo_codes = await rq.get_promo_codes(session, offset=0)

        await message.answer(
            "📋 Вот список промокодов:",
            reply_markup=get_promo_buttons(1, total_pages, promo_codes),
        )
def get_promo_buttons(page, total_pages, promo_codes, empty=False):
    buttons = []
    if not empty:
        for promo in promo_codes:
            buttons.append(
                [InlineKeyboardButton(text=promo.promo_name, callback_data=f"promo_info_{promo.promo_name}")])

    buttons.append([
        InlineKeyboardButton(text="❮", callback_data=f"promo_page_{page - 1}"),
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="null"),
        InlineKeyboardButton(text="❯", callback_data=f"promo_page_{page + 1}")
    ])
    buttons.append([InlineKeyboardButton(text="➕ Добавить", callback_data="add_promo"),
                    InlineKeyboardButton(text="❌ Удалить", callback_data="delete_promo")])
    buttons.append([InlineKeyboardButton(text="🔎 Найти по юзеру", callback_data="search_promo_user")])
    buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data="adm_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@rt.callback_query(F.data.startswith('promo_page_'))
async def promo_pagination(callback: CallbackQuery):
    page = int(callback.data.split('_')[-1])

    async with async_session() as session:
        total_promos = await rq.get_promo_count(session)

        if total_promos == 0:
            await callback.message.edit_text(
                "❗️ Промокодов пока нет.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="➕ Добавить", callback_data="add_promo")],
                        [InlineKeyboardButton(text="↩️ Назад", callback_data="adm_back")]
                    ]
                )
            )
            return

        total_pages = (total_promos + 4) // 5
        page = (page - 1) % total_pages + 1
        offset = (page - 1) * 5
        promo_codes = await rq.get_promo_codes(session, offset=offset)

        await callback.message.edit_text(
            "📋 Вот список промокодов:",
            reply_markup=get_promo_buttons(page, total_pages, promo_codes),
        )

@rt.callback_query(F.data.startswith('promo_info_'))
async def promo_info(callback: CallbackQuery):
    promo_name = callback.data.split('_')[2]
    async with async_session() as session:
        promo = await rq.get_promo_info(session, promo_name)
        if promo:
            user_list = []
            for user_id in promo.users_used:
                user = await rq.get_user_promo(session, user_id)
                user_list.append(f"@{user.username}" if user.username else f"ID: {user_id}")

            users_used_text = '\n'.join(user_list) if user_list else "Никто еще не использовал."

            text = (
                f"🎁 <strong>Промокод:</strong> {promo.promo_name}\n"
                f"⏳ <strong>Срок действия:</strong> {promo.duration} дней\n"
                f"ℹ️ <strong>Вид промокода:</strong> {'Бесплатные дни' if promo.promo_type == 'freedays' else 'Скидка'}\n"
                f"💸 <strong>{'Бесплатных дней:' if promo.promo_type == 'freedays' else 'Скидка'}</strong> {promo.promo_info_discount if promo.promo_info_discount else promo.promo_info_freedays}{'%' if promo.promo_info_discount else ''}\n"
                f"🎟 <strong>Вид подписки:</strong> {promo.subscription_type}\n"
                f"👥 <strong>Лимит пользователей:</strong> {len(promo.users_used)}/{promo.max_uses}\n"
                f"📋 <strong>Кто использовал:</strong>\n{users_used_text}\n"
            )
            await callback.message.edit_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="↩️ Назад", callback_data="promo")]]))
        else:
            await callback.answer("Промокод не найден!")
@rt.callback_query(F.data == 'add_promo')
async def add_promo(callback: CallbackQuery, state: FSMContext):
    await callback.answer('➕ Добавить')
    await state.set_state(UserState.waiting_for_promo_name)
    await callback.message.edit_text("Выберите вид промокода:", reply_markup=kb.free_discount)
@rt.callback_query(F.data.startswith('promo_type_'))
async def promo_type_selected(callback: CallbackQuery, state: FSMContext):
    promo_type = callback.data.split('_')[2]
    await state.update_data(promo_type=promo_type)
    if promo_type == "freedays":
        await callback.answer('⏳ Бесплатные Дни')
        await state.set_state(UserState.waiting_for_promo_info)
        await callback.message.edit_text("⏳ Введите количество бесплатных дней:")
    elif promo_type == "discount":
        await callback.answer('💸 Скидка')
        await state.set_state(UserState.waiting_for_promo_info)
        await callback.message.edit_text("💸 Введите размер скидки (в %):")
@rt.message(F.text, UserState.waiting_for_promo_info)
async def promo_value_entered(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        promo_value = int(message.text.strip())
        promo_type = data.get("promo_type")
        await state.update_data(promo_value=promo_value)
        if promo_type == 'discount':
            await message.answer("📚 Выберите подписку, на которую будет действовать промокод:", reply_markup=kb.promo_basic_gold)
        else:
            await message.answer("📚 Выберите подписку, на которую будет действовать промокод:",
                                 reply_markup=kb.promo_basic_gold_without_basicgold)
    except ValueError:
        await message.answer("⚠️ Введите корректное число!")
@rt.callback_query(F.data.startswith('promo_sub1_'))
async def promo_sub_selected(callback: CallbackQuery, state: FSMContext):
    if "premiumbasic" in callback.data:
        subscription_type = "basic+premium"
    elif "basic" in callback.data:
        subscription_type = "basic"
    else:
        subscription_type = "premium"
    await state.update_data(subscription_type=subscription_type)
    await state.set_state(UserState.waiting_for_promo_name)
    await callback.message.edit_text("✏️ Введите промокод:")
@rt.message(F.text, UserState.waiting_for_promo_name)
async def promo_name_entered(message: Message, state: FSMContext):
    await state.update_data(promo_name=message.text.strip())
    data = await state.get_data()
    promo_type = data.get("promo_type")
    if promo_type == "discount":
        await state.set_state(UserState.waiting_for_duration)
        await message.answer("⏳ Введите количество дней действия промокода:")
    else:
        duration = 0
        await state.update_data(duration=duration)
        await state.set_state(UserState.waiting_for_max_uses)
        await message.answer("👥️ Введите ограничение людей на промокод:")
@rt.message(F.text, UserState.waiting_for_duration)
async def promo_duration_entered(message: Message, state: FSMContext):
    try:
        duration = int(message.text.strip())
        await state.update_data(duration=duration)
        await state.set_state(UserState.waiting_for_max_uses)
        await message.answer("👥️ Введите ограничение людей на промокод:")
    except ValueError:
        await message.answer("⚠️ Введите корректное число для дней!")
@rt.message(F.text, UserState.waiting_for_max_uses)
async def promo_max_uses_entered(message: Message, state: FSMContext):
    try:
        max_uses = int(message.text.strip())
        data = await state.get_data()

        promo_name = data.get("promo_name")
        duration = data.get("duration")
        promo_type = data.get("promo_type")
        promo_value = data.get("promo_value")
        subscription_type = data.get("subscription_type")

        async with async_session() as session:
            await rq.add_promo_code(session, promo_name, duration, promo_type, promo_value, subscription_type, max_uses)

        await message.answer(
            f"✅ Промокод <strong>{promo_name}</strong> успешно добавлен!\n"
            f"🎁 Тип: {promo_type}\n"
            f"📚 Подписка: {subscription_type}\n"
            f"👥 Лимит: {max_uses} пользователей.", parse_mode='HTML'
        )
        await state.clear()

        await promo_message(message)
    except ValueError:
        await message.answer("⚠️ Введите корректное число для лимита пользователей!")


@rt.callback_query(F.data == 'search_promo_user')
async def search_promo_user(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.waiting_for_search_username)
    await callback.answer('🔎 Найти по юзеру')
    await callback.message.edit_text("🔎 Введите @юзернейм или ID для поиска активированных промокодов:", reply_markup=kb.adm_back)
@rt.message(F.text, UserState.waiting_for_search_username)
async def search_promo_result(message: Message, state: FSMContext):
    search_input = message.text.strip()
    async with async_session() as session:
        user = await rq.get_user_by_username_or_id(session, search_input)

        if not user:
            await message.answer("❗️ Пользователь не найден!")
            await state.clear()
            return

        promos_used = await rq.get_promos_by_user(session, user.user_id)

        if not promos_used:
            await message.answer(f"❗️ У пользователя @{user.username or user.user_id} нет активированных промокодов.")
            await state.clear()
            return

        promo_list = []
        for promo in promos_used:
            promo_type = "⏳ Бесплатные дни" if promo.promo_type == "freedays" else "💸 Скидка"
            promo_value = f"{promo.promo_info_freedays} дней" if promo.promo_type == "freedays" else f"{promo.promo_info_discount}% скидка"
            promo_list.append(
                f"🎁 {'✅✅✅' if user.active_promo_code == promo.promo_name else '❌❌❌'}<strong>{promo.promo_name}</strong>{'✅✅✅' if user.active_promo_code == promo.promo_name else '❌❌❌'}\n"
                f"🔖 <strong>Тип:</strong> {promo_type}\n"
                f"🎁 <strong>Размер:</strong> {promo_value}\n"
                f"🕓 <strong>Срок действия:</strong> {promo.duration} дней\n"
                f"📚 <strong>Подписка:</strong> {promo.subscription_type}\n"
                f"👥 <strong>Лимит:</strong> {len(promo.users_used)}/{promo.max_uses}\n"
                "———————————"
            )

        promo_text = '\n\n'.join(promo_list)
        username_or_id = f"@{user.username}" if user.username else f"ID: {user.user_id}"

        await message.answer(
            f"🔎 <strong>Активированные промокоды пользователя {username_or_id}:</strong>\n\n{promo_text}",
            parse_mode='HTML'
        )
    await promo_message(message)
    await state.clear()


@rt.callback_query(F.data == 'delete_promo')
async def delete_promo(callback: CallbackQuery, page: int = 1):
    async with async_session() as session:
        total_promos = await rq.get_promo_count(session)
        await callback.answer('❌ Удалить')
        if total_promos == 0:
            await callback.message.edit_text("❗️ Промокодов для удаления нет.", reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="↩️ Назад", callback_data="promo")]]))
            return

        total_pages = (total_promos + 4) // 5
        page = (page - 1) % total_pages + 1
        offset = (page - 1) * 5
        promo_codes = await rq.get_promo_codes(session, offset=offset)

        await callback.message.edit_text(
            "🗑️ Выберите промокод для удаления:",
            reply_markup=get_delete_promo_buttons(page, total_pages, promo_codes)
        )
def get_delete_promo_buttons(page, total_pages, promo_codes):
    buttons = []
    for promo in promo_codes:
        buttons.append(
            [InlineKeyboardButton(text=f"🗑️ {promo.promo_name}", callback_data=f"delete_promo_{promo.promo_name}")])

    buttons.append([
        InlineKeyboardButton(text="❮", callback_data=f"delete_page_{page - 1}"),
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="null"),
        InlineKeyboardButton(text="❯", callback_data=f"delete_page_{page + 1}")
    ])
    buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data="promo")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
@rt.callback_query(F.data.startswith('delete_promo_'))
async def delete_selected_promo(callback: CallbackQuery):
    promo_name = callback.data.split('_')[2]
    async with async_session() as session:
        await rq.delete_promo_code(session, promo_name)

    await callback.answer(f"✅ Промокод {promo_name} удален!", show_alert=True)

    await delete_promo(callback)


@rt.callback_query(F.data == 'promo_for_sub')
async def promo_for_sub(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        user = await rq.get_user_promo(session, user_id)

        if user.active_promo_code:
            remaining_days = (user.promo_expiration - datetime.now()).days
            if remaining_days > 0:
                await callback.answer(
                    f"📅 У вас уже есть активный промокод", show_alert=True
                )
                return


        if user.language == 2:
            await callback.message.edit_text("<strong>Enter the promo code</strong>", reply_markup=kb.backtosub_eng,
                                             parse_mode='HTML')
        else:
            await callback.message.edit_text("<strong>Введите промокод</strong>", reply_markup=kb.backtosub, parse_mode='HTML')
        await state.set_state(UserState.waiting_for_promo_code)
@rt.message(F.text, UserState.waiting_for_promo_code)
async def promo_code_entered(message: Message, state: FSMContext):
    promo_code = message.text.strip()
    await state.update_data(promo_code=promo_code)
    if promo_code in ['🎡 Главное меню', '🎡 Main menu']:
        await state.clear()
        await main_menu(message, state)
        return
    elif promo_code in ['👨‍💻 Поддержка', '👨‍💻 Support']:
        await state.clear()
        await main_menu_sup(message)
        return
    elif promo_code in ['📨 Рассылка', '📨 Mailing']:
        await state.clear()
        await send_newsletter(message, state)
        return
    elif promo_code in ['🌐 Язык', '🌐 Language']:
        await state.clear()
        await main_keyboard_language(message)
        return
    async with async_session() as session:
        promo = await rq.get_promo_info(session, promo_code)

        if not promo:
            await message.answer("❌")
            return

        if len(promo.users_used) >= promo.max_uses:
            await message.answer("❌")
            return

        user_id = message.from_user.id
        user = await rq.get_user_promo(session, user_id)

        if user_id in promo.users_used:
            await message.answer("❌")
            return

        if user.active_promo_code:
            await message.answer("❌")
            return
        if promo.promo_type == 'discount':
            user.active_promo_code = promo.promo_name
            user.promo_expiration = datetime.now() + timedelta(days=promo.duration)

        if user.language == 2:
            promo_value = f"{promo.promo_info_freedays} days" if promo.promo_type == "freedays" else f"{promo.promo_info_discount}%"
        else:
            promo_value = f"{promo.promo_info_freedays} дней" if promo.promo_type == "freedays" else f"{promo.promo_info_discount}%"
        if promo.promo_type == 'discount':
            expiration_date = user.promo_expiration.strftime('%d.%m %H:%M')
            if user.language == 2:
                await message.answer(
                    f"<strong>✅ Promo code is valid until {expiration_date}</strong>\n\n"
                    f"Discount amount: {promo_value}",
                    parse_mode='HTML', reply_markup=kb.backtosub_eng
                )
            else:
                await message.answer(
                    f"<strong>✅ Промокод активен до {expiration_date}</strong>\n\n"
                    f"Размер скидки: {promo_value}",
                    parse_mode='HTML', reply_markup=kb.backtosub
                )
            promo.users_used.append(user_id)
            await state.clear()
        if promo.promo_type == 'freedays':
            if user.subscription == 'premium' and promo.subscription_type == 'premium':
                user.subscription_day += promo.promo_info_freedays
                if user.language == 2:
                    await message.answer(
                        f"<strong>✅ Promo code activated</strong>\n\n"
                        f"You have received {promo_value}",
                        parse_mode='HTML', reply_markup=kb.backtosub_eng
                    )
                else:
                    await message.answer(
                        f"<strong>✅ Промокод активирован</strong>\n\n"
                        f"Вам начислено {promo_value}",
                        parse_mode='HTML', reply_markup=kb.backtosub
                    )
                promo.users_used.append(user_id)
                await state.clear()
            elif user.subscription == 'basic' and promo.subscription_type == 'basic':
                user.subscription_day += promo.promo_info_freedays
                if user.language == 2:
                    await message.answer(
                        f"<strong>✅ Promo code activated</strong>\n\n"
                        f"You have received {promo_value}",
                        parse_mode='HTML', reply_markup=kb.backtosub_eng
                    )
                else:
                    await message.answer(
                        f"<strong>✅ Промокод активирован</strong>\n\n"
                        f"Вам начислено {promo_value}",
                        parse_mode='HTML', reply_markup=kb.backtosub
                    )
                promo.users_used.append(user_id)
                await state.clear()
            elif user.subscription == 'неактивна' or user.subscription == 'free':
                if promo.subscription_type == 'premium':
                    user.subscription_day += promo.promo_info_freedays
                    user.subscription = 'premium'
                    if user.language == 2:
                        await message.answer(
                            f"<strong>✅ Promo code activated</strong>\n\n"
                            f"You have received {promo_value}",
                            parse_mode='HTML', reply_markup=kb.backtosub_eng
                        )
                    else:
                        await message.answer(
                            f"<strong>✅ Промокод активирован</strong>\n\n"
                            f"Вам начислено {promo_value}",
                            parse_mode='HTML', reply_markup=kb.backtosub
                        )
                else:
                    user.subscription_day += promo.promo_info_freedays
                    user.subscription = 'basic'
                    if user.language == 2:
                        await message.answer(
                            f"<strong>✅ Promo code activated</strong>\n\n"
                            f"You have received {promo_value}",
                            parse_mode='HTML', reply_markup=kb.backtosub_eng
                        )
                    else:
                        await message.answer(
                            f"<strong>✅ Промокод активирован</strong>\n\n"
                            f"Вам начислено {promo_value}",
                            parse_mode='HTML', reply_markup=kb.backtosub
                        )
            else:
                await message.answer("❌")
                return
        await session.commit()



#Текста мейн клавы
@rt.message(F.text.in_(['🎡 Главное меню', '🎡 Main menu']))
async def main_menu(message: Message):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await message.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                if user.language == 2:
                    await message.answer('<strong>Choose an action using the buttons below:</strong>', reply_markup=kb.m_menu_eng,
                                         parse_mode='HTML')
                else:
                    await message.answer('<strong>Выберите действия по кнопкам ниже:</strong>', reply_markup=kb.m_menu,
                                         parse_mode='HTML')
@rt.message(F.text.in_(['👨‍💻 Поддержка', '👨‍💻 Support']))
async def main_menu_sup(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.language == 2:
                await message.answer('<strong>🫂 For any questions, reach us at: @xxx</strong>', parse_mode='HTML',
                                     reply_markup=kb.in_main_menu_eng)
            else:
                await message.answer('<strong>🫂 По любым вопросам ждем вас: @xxx</strong>', parse_mode='HTML', reply_markup=kb.in_main_menu)
    await state.clear()
@rt.message(F.text.in_(['📨 Рассылка', '📨 Mailing']))
async def send_newsletter(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block: 
                try:
                    await message.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                if user.language == 2:
                    if not user or user.gmail == 'не указано' or user.password == 'Неуказано':
                        await message.answer('<strong>First, complete the registration</strong>',
                                             reply_markup=kb.reg_in_mail_eng, parse_mode='HTML')
                        return
                    if user.subscription == 'free' or user.subscription == 'неактивна':
                        await rq.set_group(user_id)

                        async with async_session() as session:
                            result = await session.execute(select(Group).filter(Group.user_id == user_id))
                            groups = result.scalars().all()

                            if not groups:
                                await message.answer("<strong>You don't have groups</strong>", parse_mode="HTML")
                                return

                            active_group = await session.scalar(
                                select(Group).filter(Group.user_id == user_id, Group.active == True))

                            if not active_group:
                                active_group = groups[0]
                                active_group.active = True

                            await message.answer("<strong>Choose an action using the buttons below:</strong>",
                                                 parse_mode="HTML",
                                                 reply_markup=kb.auto_navigation_eng(active_group.name, user))

                            await session.commit()
                    else:
                        await message.answer('<strong>Choose the mailing type below:</strong>', parse_mode='HTML',
                                             reply_markup=kb.extra_auto)
                else:
                    if not user or user.gmail == 'не указано' or user.password == 'Неуказано':
                        await message.answer('<strong>Сначала пройдите регистрацию</strong>',
                                                     reply_markup=kb.reg_in_mail, parse_mode='HTML')
                        return
                    if user.subscription == 'free' or user.subscription == 'неактивна':
                        await rq.set_group(user_id)

                        async with async_session() as session:
                            result = await session.execute(select(Group).filter(Group.user_id == user_id))
                            groups = result.scalars().all()

                            if not groups:
                                await message.answer("<strong>У вас нет групп.</strong>", parse_mode="HTML")
                                return

                            active_group = await session.scalar(
                                select(Group).filter(Group.user_id == user_id, Group.active == True))

                            if not active_group:
                                active_group = groups[0]
                                active_group.active = True

                            await message.answer("<strong>Выберите действия по кнопкам ниже:</strong>",
                                                             parse_mode="HTML",
                                                             reply_markup=kb.auto_navigation(active_group.name, user))

                            await session.commit()
                    else:
                        await message.answer('<strong>Выберите тип рассылки ниже:</strong>',parse_mode='HTML',
                                             reply_markup=kb.extra_auto)

        await state.clear()
        await session.commit()
@rt.message(F.text.in_(['🌐 Язык', '🌐 Language']))
async def main_keyboard_language(message: Message):
    user_id = message.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            await message.answer('<strong>Choose language | Выберите язык</strong>', parse_mode='HTML',
                                  reply_markup=kb.choice_lang_main_key)

@rt.callback_query(F.data.in_(['eng_key', 'rus_key']))
async def choice_language(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if callback.data == 'eng_key':
            await callback.answer('🇺🇸 English')
            user.language = 2
            await callback.message.answer(f'<strong>🌐 Selected language: English</strong>',
                                 parse_mode='HTML', disable_web_page_preview=True, reply_markup=kb.start_eng)
        else:
            await callback.answer('🇷🇺 Русский')
            user.language = 1
            await callback.message.answer(f'<strong>🌐 Выбран язык: Русский</strong>',
                                 parse_mode='HTML', disable_web_page_preview=True, reply_markup=kb.start)
        await session.commit()

@rt.callback_query(F.data == 'back_to_auto_extra')
async def back_to_auto_extra(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            await state.clear()
            if user.language == 2:
                await callback.answder('↩️ Back')
            else:
                await callback.answer('↩️ Назад')
            await send_newsletter(callback.message, state)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)

@rt.callback_query(F.data == 'profile')
async def profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                if user.gmail == 'не указано':
                    await callback.answer('🧸 Profile')
                    await callback.message.edit_text(f'<strong>🧸 Profile {user.username}</strong>\n———\n'
                                                     f'<strong>✉️ Gmail: \n└ </strong>not set\n\n'
                                                     f'<strong>🎟 Subscription:\n └ </strong>{user.subscription if user.subscription in ['basic', 'premium'] else 'inactive'}',
                                                     reply_markup=kb.back_to_menu_with_reg_eng, parse_mode='HTML')
                if user.gmail != 'не указано':
                    await callback.answer('🧸 Profile')
                    await callback.message.edit_text(f'<strong>🧸 Profile {user.username}</strong>\n———\n'
                                                     f'<strong>✉️ Gmail: \n└ </strong>{user.gmail}\n\n'
                                                     f'<strong>🎟 Subscription: \n└ </strong>{user.subscription if user.subscription in ['basic', 'premium'] else 'free'}',
                                                     reply_markup=kb.back_to_menu_with_quit_eng, parse_mode='HTML')
            else:
                if user.gmail == 'не указано':
                    await callback.answer('🧸 Профиль')
                    await callback.message.edit_text(f'<strong>🧸 Профиль {user.username}</strong>\n———\n'
                                                     f'<strong>✉️ Gmail: \n└ </strong>{user.gmail}\n\n'
                                                     f'<strong>🎟 Подписка:\n └ </strong>{user.subscription}',
                                                     reply_markup=kb.back_to_menu_with_reg, parse_mode='HTML')
                if user.gmail != 'не указано':
                    await callback.answer('🧸 Профиль')
                    await callback.message.edit_text(f'<strong>🧸 Профиль {user.username}</strong>\n———\n'
                                                     f'<strong>✉️ Gmail: \n└ </strong>{user.gmail}\n\n'
                                                     f'<strong>🎟 Подписка: \n└ </strong>{user.subscription}',
                                                     reply_markup=kb.back_to_menu_with_quit, parse_mode='HTML')
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
async def show_profile(message: Message):
    user_id = message.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user:
            if user.language == 2:
                if user.gmail == 'не указано':
                    await message.answer(f'<strong>🧸 Profile {user.username}</strong>\n———\n'
                                                     f'<strong>✉️ Gmail: \n└ </strong>not set\n\n'
                                                     f'<strong>🎟 Subscription:\n └ </strong>{user.subscription if user.subscription in ['basic', 'premium'] else 'inactive'}',
                                                     reply_markup=kb.back_to_menu_with_reg_eng, parse_mode='HTML')
                if user.gmail != 'не указано':
                    await message.answer(f'<strong>🧸 Profile {user.username}</strong>\n———\n'
                                                     f'<strong>✉️ Gmail: \n└ </strong>{user.gmail}\n\n'
                                                     f'<strong>🎟 Subscription: \n└ </strong>{user.subscription if user.subscription in ['basic', 'premium'] else 'inactive'}',
                                                     reply_markup=kb.back_to_menu_with_quit_eng, parse_mode='HTML')
            else:
                if user.gmail == 'не указано':
                    await message.answer(f'<strong>🧸 Профиль {user.username}</strong>\n———\n'
                                                     f'<strong>✉️ Gmail: \n└ </strong>{user.gmail}\n\n'
                                                     f'<strong>🎟 Подписка:\n └ </strong>{user.subscription}',
                                                     reply_markup=kb.back_to_menu_with_reg, parse_mode='HTML')
                if user.gmail != 'не указано':
                    await message.answer(f'<strong>🧸 Профиль {user.username}</strong>\n———\n'
                                                     f'<strong>✉️ Gmail: \n└ </strong>{user.gmail}\n\n'
                                                     f'<strong>🎟 Подписка: \n└ </strong>{user.subscription}',
                                                     reply_markup=kb.back_to_menu_with_quit, parse_mode='HTML')
@rt.callback_query(F.data == 'quit')
async def quit_from_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('Anti-misclick system', show_alert=True)
                await callback.message.edit_text('<strong>⚠️ Are you sure you want to log out?\n\n</strong>'
                                                 '<strong>After logging out, all your data, including your subscription, will be deleted\n\n</strong>'
                                                 '<strong>Recovery of this data will be impossible</strong>',
                                                 parse_mode='HTML', reply_markup=kb.are_you_sure_profile_eng)
            else:
                await callback.answer('Cистема анти-миссклик', show_alert=True)
                await callback.message.edit_text('<strong>⚠️ Вы уверены, что хотите выйти?\n\n</strong>'
                                                 '<strong>После выхода из аккаунта все ваши данные, включая подписку, будут удалены \n\n</strong>'
                                                 '<strong>Восстановление этих данных будет невозможно</strong>', parse_mode='HTML', reply_markup=kb.are_you_sure_profile)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'sure_to_quit')
async def sure_to_quit(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('✅ Logout')
            else:
                await callback.answer('✅ Выйти')
            groups_result = await session.execute(
                select(Group)
                .filter(Group.user_id == user_id)
                .options(selectinload(Group.emails))  
            )
            groups = groups_result.scalars().all()

            if groups:  
                max_email_count = max(len(group.emails) for group in groups)

                top_groups = [group for group in groups if len(group.emails) == max_email_count]
                last_group = max(top_groups, key=lambda g: g.id)

                for group in groups:
                    if group != last_group:
                        await session.execute(delete(Group).where(Group.id == group.id))

                await session.execute(delete(Email).where(Email.user_id == user_id))
                await session.execute(delete(Beat).where(Beat.user_id == user_id))
                await session.execute(delete(Settings).where(Settings.user_id == user_id))
            else:
                await session.execute(delete(Email).where(Email.user_id == user_id))
                await session.execute(delete(Beat).where(Beat.user_id == user_id))

            user.subscription = 'неактивна'
            user.password = 'Неуказано'
            user.subscription_day = 0
            user.mails_per_day = 0
            user.gmail = 'не указано'
            if user.language == 2:
                await callback.message.edit_text('<strong>✅ You have successfully logged out!</strong>',
                                                 reply_markup=kb.back_to_profile_eng, parse_mode='HTML')
            else:
                await callback.message.edit_text('<strong>✅ Вы успешно вышли из аккаунта!</strong>',
                                                 reply_markup=kb.back_to_profile, parse_mode='HTML')

            await session.commit()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'back_to_menu_with_reg')
async def back_to_menu_with_reg(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('↩️ Back')
                await callback.message.edit_text('<strong>Choose an action using the buttons below:</strong>',
                                                 reply_markup=kb.m_menu_eng, parse_mode='HTML')
            else:
                await callback.answer('↩️ Назад')
                await callback.message.edit_text('<strong>Выберите действия по кнопкам ниже:</strong>',
                                                 reply_markup=kb.m_menu, parse_mode='HTML')
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'back_to_profile')
async def back_to_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('🧸 To profile')
            else:
                await callback.answer('🧸 В профиль')
            await profile(callback)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)

#рефки

@rt.callback_query(F.data == 'referral')
async def referral(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    referral_link = f"https://t.me/{(await callback.bot.me()).username}?start=ref_{user_id}"

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user and not user.block:
            lang = user.language
            if lang == 2:
                await callback.answer('🏷️ Referral system')
                text = (
                    "<b>Your referral link</b>:\n"
                    f"<code>{referral_link}</code>\n\n"
                    f"👥 Invited: {user.referrals}\n"
                    f"<a href='https://telegra.ph/ℹ--Progressivnye-procenty-08-09'>Discount for invitations:</a> "
                    f"{20 if user.referrals in [0, 1, 2, 3, 4] else 30 if user.referrals in [5, 6, 7, 8, 9] else 50}%"
                )
            else:
                await callback.answer('🏷️ Реферальная система')
                text = (
                    "<b>Ваша реферальная ссылка</b>:\n"
                    f"<code>{referral_link}</code>\n\n"
                    f"👥 Приглашено: {user.referrals}\n"
                    f"<a href='https://telegra.ph/ℹ--Progressivnye-procenty-08-09'>Скидка за приглашение:</a> "
                    f"{20 if user.referrals in [0, 1, 2, 3, 4] else 30 if user.referrals in [5, 6, 7, 8, 9] else 50}%"
                )
            if user.language == 2:
                await callback.message.edit_text(text, parse_mode="HTML", disable_web_page_preview=True,
                                                 reply_markup=kb.back_to_menu_from_ref_eng)
            else:
                await callback.message.edit_text(text, parse_mode="HTML", disable_web_page_preview=True, reply_markup=kb.back_to_menu_from_ref)

        else:
            await callback.answer(
                "❗️НЕДОСТУПНО" if user and user.language != 2 else "❗️NOT AVAILABLE",
                show_alert=True
            )

#Регистрация
@rt.callback_query(F.data == 'reg')
async def reg_gmail(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                if user.gmail == 'не указано':
                    await state.set_state(UserState.waiting_for_gmail)
                    await callback.answer('🖨 Registration')
                    await callback.message.edit_text('<strong>Enter your Gmail to register</strong>', parse_mode='HTML')
                else:
                    await callback.answer('🖨 Registration')
                    await callback.message.edit_text(
                        f'<strong>Now enter the app password</strong> (it can only be created if two-factor authentication is enabled)\n\n'
                        f'<strong>Click the button below to go directly to the required section</strong>', parse_mode="HTML",
                        reply_markup=kb.passw_eng)
                    await state.set_state(UserState.waiting_for_password)
            else:
                if user.gmail == 'не указано':
                    await state.set_state(UserState.waiting_for_gmail)
                    await callback.answer('🖨 Регистрация')
                    await callback.message.edit_text('<strong>Укажите ваш Gmail для регистрации</strong>', parse_mode='HTML')
                else:
                    await callback.answer('🖨 Регистрация')
                    await callback.message.edit_text(
                        f'<strong>Укажите пароль приложения</strong> (его можно создать только при включенной двухэтапной аутентификации)\n\n'
                        f'<strong>Нажмите на кнопку ниже, чтобы сразу перейти в нужный раздел</strong>', parse_mode="HTML",
                        reply_markup=kb.passw)
                    await state.set_state(UserState.waiting_for_password)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(UserState.waiting_for_gmail)
async def handle_gmail(msg: Message, state: FSMContext):
    user_id = msg.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block: 
                try:
                    await msg.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                gmail = msg.text.strip().lower()

                if '@' not in gmail or '.' not in gmail:
                    await msg.answer('<strong>Некорректный Gmail. Пожалуйста, попробуйте снова</strong>',
                                     parse_mode='HTML')
                    return

                async with async_session() as session:
                    gmail_exists = await session.execute(select(User).filter(User.gmail == gmail))
                    existing_user = gmail_exists.scalar_one_or_none()

                    if existing_user:
                        await msg.answer('<strong>Пользователь с таким Gmail уже существует</strong>',
                                         parse_mode='HTML')
                        return

                await rq.set_user(user_id, gmail=gmail)

                if user.language == 2:
                    await msg.answer(
                        f'<strong>Now enter the app password</strong> (it can only be created if two-factor authentication is enabled)\n\n'
                        f'<strong>Click the button below to go directly to the required section</strong>',
                        parse_mode="HTML", reply_markup=kb.passw_eng)
                else:
                    await msg.answer(
                        f'<strong>Теперь укажите пароль приложения</strong> (его можно создать только при включенной двухэтапной аутентификации)\n\n'
                        f'<strong>Нажмите на кнопку ниже, чтобы сразу перейти в нужный раздел</strong>', parse_mode="HTML", reply_markup=kb.passw)
                await state.set_state(UserState.waiting_for_password)
@rt.message(UserState.waiting_for_password)
async def handle_password(msg: Message, state: FSMContext, bot: Bot):
    user_id = msg.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await msg.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                password = msg.text.strip()

                if not re.fullmatch(r'[a-zA-Z0-9]{4}( [a-zA-Z0-9]{4}){3}', password):
                    if user.language == 2:
                        await msg.answer(
                            '<strong>Invalid app password. </strong>'
                            '<strong>Please try again</strong>',
                            parse_mode='HTML'
                        )
                    else:
                        await msg.answer(
                            '<strong>Некорректный пароль приложения. </strong>'
                            '<strong>Пожалуйста, попробуйте снова</strong>',
                            parse_mode='HTML'
                        )
                    return
                user = await rq.get_user(msg.from_user.id)
                await rq.set_user(user_id, password=password)
                user.subscription = 'free'
                user.mails_per_day = 25
                session.add(user)
                if user.language == 2:
                    await msg.answer(
                        '<strong>✅ Registration successful. You can start now!</strong>', parse_mode='HTML',
                        reply_markup=kb.in_main_menu_eng)
                else:
                    await msg.answer(
                        '<strong>✅ Регистрация прошла успешно. Можно начинать!</strong>', parse_mode='HTML',
                        reply_markup=kb.in_main_menu)

                now = datetime.now()
                if user.used_referral:
                    if user.referrer_id:
                        ref_result = await session.execute(select(User).filter(User.user_id == user.referrer_id))
                        referrer = ref_result.scalar_one_or_none()

                        if referrer:
                            if referrer.block:
                                referrer.block = False
                            if referrer.subscription not in ['неактивна', 'free']:
                                if referrer.notifications_reg:
                                    if referrer.language == 2:
                                        await bot.send_message(
                                            referrer.user_id,
                                            f"<b>Your referral has registered in Be Twin</b>\n\n"
                                            f"You have been credited with 1 day of {referrer.subscription} subscription",
                                            parse_mode='HTML',
                                            reply_markup=kb.turn_off_notifications_eng
                                        )
                                    else:
                                        await bot.send_message(
                                            referrer.user_id,
                                            f"<b>Ваш реферал зарегистрировался в Be Twin</b>\n\n"
                                            f"Вам начислен 1 день подписки {referrer.subscription}", parse_mode='HTML',
                                            reply_markup=kb.turn_off_notifications
                                        )
                                referrer.subscription_day += 1
                    expire_date = user.referral_discount_expire
                    days_left = 0
                    if expire_date:
                        delta = expire_date - now
                        days_left = max(math.ceil(delta.total_seconds() / 86400), 0)

                    if user.language == 2 and expire_date:
                        await msg.answer(
                            f'<b>The referral discount will remain active for {days_left} more days</b>\n\n'
                            'You can view it in the "🎟 Subscription" section of the main menu',
                            parse_mode='HTML'
                        )
                    elif user.language in [1, 0] and expire_date:
                        await msg.answer(f'<b>Реферальная скидка будет активна еще {days_left} дней</b>\n\n'
                                         'Увидеть ее можно в разделе «🎟 Подписка» главного меню',
                                         parse_mode='HTML')



                await state.clear()
                await session.commit()

#Уведомления
@rt.callback_query(F.data == 'turn_off_notifications')
async def turn_off_notifications(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('🔕 Disable notifications')
                await callback.message.edit_text(
                    '<b>Do you want to disable notifications about referral registrations?</b>\n\n'
                    '⚠️ Notifications about referral subscription purchases will remain (if enabled)',
                    parse_mode='HTML',
                    reply_markup=kb.menu_notifications_reg_eng
                )
            else:
                await callback.answer('🔕 Отключить уведомления')
                await callback.message.edit_text('<b>Хотите отключить уведомления о регистрации рефералов?</b>\n\n'
                                              '⚠️ Уведомления о покупке рефералом подписки сохранятся (если включены)',
                                              parse_mode='HTML',
                                              reply_markup=kb.menu_notifications_reg)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
                                  , show_alert=True)

@rt.callback_query(F.data == 'turn_off_notifications_sub')
async def turn_off_notifications_sub(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('🔕 Disable notifications')
                await callback.message.edit_text(
                    '<b>Do you want to turn off notifications about your referrals purchasing a subscription?</b>\n\n'
                    '⚠️ Notifications about referral registrations will remain (if enabled)',
                    parse_mode='HTML',
                    reply_markup=kb.menu_notifications_sub_eng
                )
            else:
                await callback.answer('🔕 Отключить уведомления')
                await callback.message.edit_text(
                    '<b>Хотите отключить уведомления о покупке рефералом подписки?</b>\n\n'
                    '⚠️ Уведомления о регистрации рефералов сохранятся (если включены)',
                    parse_mode='HTML',
                    reply_markup=kb.menu_notifications_sub
                )
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
                                  , show_alert=True)

@rt.callback_query(F.data == 'back_to_new_ref')
async def back_to_new_ref(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('↩️ Back')
                await callback.message.edit_text(
                    f"<b>Your referral has registered in Be Twin</b>\n\n"
                                        f"You have been credited with 1 day of {user.subscription} subscription",
                                        parse_mode='HTML',
                                        reply_markup=kb.turn_off_notifications_eng
                                    )
            else:
                await callback.answer('↩️ Назад')
                await callback.message.edit_text(
                    f"<b>Ваш реферал зарегистрировался в Be Twin</b>\n\n"
                    f"Вам начислен 1 день подписки {user.subscription}", parse_mode='HTML',
                    reply_markup=kb.turn_off_notifications
                )
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
                                  , show_alert=True)

@rt.callback_query(F.data == 'back_to_new_ref_sub')
async def back_to_new_ref_sub(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('↩️ Back')
                await callback.message.edit_text(
                    f"<b>💰 Your referral has subscribed to Be Twin</b>\n\n"
                                f"You have received a "
                                f"{20 if user.referrals in [1, 2, 3, 4, 5] else 30 if user.referrals in [6, 7, 8, 9, 10] else 50}% "
                                f"discount on any subscription",
                                parse_mode="HTML", reply_markup=kb.turn_off_notifications_eng_sub
                            )
            else:
                await callback.answer('↩️ Назад')
                await callback.message.edit_text(
                    f"<b>💰 Ваш реферал оформил подписку в Be Twin</b>\n\n"
                                f"Вам начислена "
                                f"{20 if user.referrals in [1, 2, 3, 4, 5] else 30 if user.referrals in [6, 7, 8, 9, 10] else 50}% "
                                f"скидка на любую подписку", parse_mode="HTML", reply_markup=kb.turn_off_notifications_sub
                            )
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
                                  , show_alert=True)

@rt.callback_query(F.data == 'confirm_off_notifications')
async def confirm_off_notifications(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            user.notifications_reg = False
            if user.language == 2:
                await callback.answer('✅ Successfull')
                await callback.message.edit_text(
                    f"<b>✅ Notifications about referral registrations have been disabled</b>\n\n"
                    f"To enable notifications, <a href='https://t.me/@xxx'>contact support</a>",
                    parse_mode='HTML', reply_markup=kb.support_eng
                )
            else:
                await callback.answer('✅ Успешно')
                await callback.message.edit_text(
                    f"<b>✅ Уведомления о регистрации рефералов отключены</b>\n\n"
                    f"Чтобы включить уведомления <a href='https://t.me/@xxx'>напишите в поддержку</a>",
                    parse_mode='HTML', reply_markup=kb.support
                )
            await session.commit()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
                                  , show_alert=True)

@rt.callback_query(F.data == 'confirm_off_notifications_sub')
async def confirm_off_notifications_sub(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            user.notifications_sub = False
            if user.language == 2:
                await callback.answer('✅ Successfull')
                await callback.message.answer(
                    f"<b>✅ Notifications about referrals’ subscription purchases have been disabled</b>\n\n"
                    f"To enable notifications, <a href='https://t.me/@xxx'>contact support</a>",
                    parse_mode='HTML', reply_markup=kb.support_eng
                )

            else:
                await callback.answer('✅ Успешно')
                await callback.message.answer(
                    f"<b>✅ Уведомления покупке рефералом подписки отключены</b>\n\n"
                    f"Чтобы включить уведомления <a href='https://t.me/@xxx'>напишите в поддержку</a>",
                    parse_mode='HTML', reply_markup=kb.support
                )
            await session.commit()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
                                  , show_alert=True)

@rt.callback_query(F.data == 'support')
async def support(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('👨‍💻 Support')
                await callback.message.answer('<strong>🫂 For any questions, reach us at: @xxx</strong>', parse_mode='HTML',
                                     reply_markup=kb.in_main_menu_eng)

            else:
                await callback.answer('👨‍💻 Поддержка')
                await callback.message.answer('<strong>🫂 По любым вопросам ждем вас: @xxx</strong>', parse_mode='HTML',
                                     reply_markup=kb.in_main_menu)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
                                  , show_alert=True)
#подписка
@rt.callback_query(F.data == 'subscription')
async def subscription(callback: CallbackQuery, state: FSMContext):
    user = await rq.get_user(callback.from_user.id)  
    if user:
        await state.clear()
        if user.language == 2:
            if user.subscription == 'неактивна':
                text = ("*You do not have an active subscription, access to the bot’s functionality is limited\\.* "
                        "Register to activate a free subscription\n\n"
                        "*Limits:*\n"
                        "• up to 25 letters per day\n"
                        "• up to 50 email addresses in the database\n"
                        "• up to 20 beats in the database\n\n"
                        "🎟 *Available subscriptions:*\n"
                        ">*premium* – 450 letters per day, 50 urgent letters, unlimited email addresses and beats in the database\n"
                        ">*basic* – 450 letters per day, 50 urgent letters, up to 450 email addresses in the database, up to 200 beats in the database")
            elif user.subscription == 'free':
                text = ("*You do not have an active subscription, access to the bot’s functionality is limited\\.*\n\n"
                        "*Limits:*\n"
                        "• up to 25 letters per day\n"
                        "• up to 50 email addresses in the database\n"
                        "• up to 20 beats in the database\n\n"
                        "🎟 *Available subscriptions:*\n"
                        ">*premium* – 450 letters per day, 50 urgent letters, unlimited email addresses and beats in the database\n"
                        ">*basic* – 450 letters per day, 50 urgent letters, up to 450 email addresses in the database, up to 200 beats in the database")
            elif user.subscription == "basic":
                text = (f"Your subscription: *basic*\n\n"
                        f"Days remaining: *{user.subscription_day}* \n\n"
                        "*Limits:*\n"
                        "• up to 450 letters per day\n"
                        "• 50 urgent letters\n"
                        "• up to 450 addresses in the database\n"
                        "• up to 200 beats in the database\n\n"
                        "🎟 *Available subscriptions:*\n"
                        ">*premium* – 450 letters per day, 50 urgent letters, unlimited address and beat database\n\n"
                        "You can upgrade to premium at no extra cost\\. The remaining days will be recalculated with a coefficient of 0\\.6")

            else:  
                text = (f"Your subscription: *premium ✦*\n\n"
                        f"Days remaining: *{user.subscription_day}*\n\n"
                        "*Limits:*\n"
                        "• 450 letters per day\n"
                        "• 50 urgent letters\n"
                        "• unlimited address and beat database\n\n"
                        "🎟 *Available subscriptions:*\n"
                        ">*basic* – 450 letters per day, 50 urgent letters, up to 450 email addresses in the database, up to 200 beats in the database\n\n"
                        "You can upgrade to *basic* at no extra cost\\. The remaining days will be recalculated with a coefficient of 1\\.6")

            await callback.answer('🎟 Subscription')
            if user.subscription == 'free' or user.subscription == 'неактивна':
                await callback.message.edit_text(text, reply_markup=kb.if_free_sub_eng, parse_mode='MarkdownV2')
            else:
                await callback.message.edit_text(text, reply_markup=kb.if_not_free_sub_eng, parse_mode='MarkdownV2')
        else:
            if user.subscription == 'неактивна':
                text = ("*У вас нет активной подписки, доступ к функционалу бота ограничен\\.* "
                        "Зарегистрируйтесь, чтобы активировать бесплатную подписку\n\n"
                        "*Лимиты:*\n"
                        "• до 25 писем в день\n"
                        "• до 50 почт в базе\n"
                        "• до 20 битов в базе\n\n"
                        "🎟 *Доступные подписки:*\n"
                        ">*premium* – 450 писем в день, 50 экстренных писем, безлимитная база почт и битов\n"
                        ">*basic* – 450 писем в день, 50 экстренных писем, до 450 почт, до 200 битов")
            elif user.subscription == 'free':
                text = ("*У вас нет активной подписки, доступ к функционалу бота ограничен* \n\n"
                        "*Лимиты:*\n"
                        "• до 25 писем в день\n"
                        "• до 50 почт в базе\n"
                        "• до 20 битов в базе\n\n"
                        "🎟 *Доступные подписки:*\n"
                        ">*premium* – 450 писем в день, 50 экстренных писем, безлимитная база почт и битов\n"
                        ">*basic* – 450 писем в день, 50 экстренных писем, до 450 почт, до 200 битов")
            elif user.subscription == "basic":
                text = (f"Ваша подписка: *basic*\n\n"
                        f"До окончания подписки: *{user.subscription_day}* дней\n\n"
                        "*Лимиты:*\n"
                        "• до 450 писем в день\n"
                        "• 50 экстренных писем\n"
                        "• до 450 почт в базе\n"
                        "• до 200 битов в базе\n\n"
                        "🎟 *Доступные подписки:*\n"
                        ">*premium* – 450 писем в день, 50 экстренных писем, безлимитная база почт и битов\n\n"
                        "Вы можете перейти на *premium* без доплаты\\. Оставшиеся дни пересчитаются с коэффициентом 0\\.6")

            else: 
                text = (f"Ваша подписка: *premium ✦*\n\n"
                        f"До окончания подписки: *{user.subscription_day}* дней\n\n"
                        "*Лимиты:*\n"
                        "• до 450 писем в день\n"
                        "• 50 экстренных писем\n"
                        "• безлимитная база почт и битов\n\n"
                        "🎟 *Доступные подписки:*\n"
                        ">*basic* – 450 писем в день, 50 экстренных писем, до 450 почт, до 200 битов\n\n"
                        " Вы можете перейти на *basic* без доплаты\\. Оставшиеся дни пересчитаются с коэффициентом 1\\.6")

            await callback.answer('🎟 Подписка')
            if user.subscription == 'free' or user.subscription == 'неактивна':
                await callback.message.edit_text(text, reply_markup=kb.if_free_sub, parse_mode='MarkdownV2')
            else:
                await callback.message.edit_text(text, reply_markup=kb.if_not_free_sub, parse_mode='MarkdownV2')
    else:
        await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'get_sub')
async def user_get_sub(callback: CallbackQuery, page: int = 1):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user:
            expire_date = user.referral_discount_expire
            days_left = False

            if expire_date:
                delta = expire_date - datetime.now()
                days_left = max(math.ceil(delta.total_seconds() / 86400), 0)
            if user.language == 2:
                if user.block == False:
                    await callback.answer('💲Subscribe')
                else:
                    await callback.answer('💲Renew')

                basic_premium_list = ['basic', 'premium']
                total_pages = len(basic_premium_list)

                page = (page - 1) % total_pages + 1

                discount_basic = 0
                discount_premium = 0
                if user.active_promo_code:
                    promo_info = await rq.get_promo_info(session, user.active_promo_code)

                    if promo_info and promo_info.promo_type == "discount":
                        if promo_info.subscription_type == 'basic':
                            discount_basic = promo_info.promo_info_discount
                            discount_premium = 0
                        elif promo_info.subscription_type == "premium":
                            discount_premium = promo_info.promo_info_discount
                            discount_basic = 0
                        elif promo_info.subscription_type == "basic+premium":
                            discount_premium = promo_info.promo_info_discount
                            discount_basic = promo_info.promo_info_discount
                if user.used_referral and not user.subscription_start and user.referral_discount_expire > datetime.now():
                    discount_premium += 20
                    discount_basic += 20
                disc = 0
                if user.referrals >= 1:
                    # запомнить disc = 20 if user.referrals in [1, 2, 3, 4, 5] else 30 if user.referrals in [6, 7, 8, 9, 10] else 50
                    disc = user.referral_discount
                    discount_premium += disc
                    discount_basic += disc
                current_subscription = basic_premium_list[page - 1]
                if current_subscription == 'basic':
                    discounted_price = int(14 * (1 - discount_basic / 100))

                    discount_expiration_info = (
                        f" (promo code valid until {user.promo_expiration.strftime('%d.%m %H:%M')})"
                        if user.active_promo_code and discount_basic > 0 else f' (referral discount active for {days_left} more days)' if days_left and discounted_price != 14 else ""
                    )
                    subscription_message = ("<strong>Basic subscription</strong>\n\n"
                                            f"Cost: {f"<s>$14</s> " if discounted_price != 14 else ''}${discounted_price}/month"
                                            f"{discount_expiration_info}\n\n"
                                            "<strong>Payment methods:</strong>\n"
                                            "<strong>Telegram Wallet: </strong>@xxx\n"
                                            "<strong>BTC (bitcoin chain): </strong>\n13J81J22ufb9pVNvzVH8fz2yLnWwYzeMsE\n\n"
                                            "<strong>More payment methods here (CashApp, Apple Pay, PayPal, Zelle) – </strong>@xxx\n\n"
                                            "ℹ️ To pay, send funds using any of the methods above. Then be sure to "
                                            "<a href='https://t.me/@xxx'>send us the payment receipt (clickable)</a>"
                                            )
                else:
                    discounted_price = int(24 * (1 - discount_premium / 100))

                    discount_expiration_info = (
                        f" (promo code valid until {user.promo_expiration.strftime('%d.%m %H:%M')})"
                        if user.active_promo_code and discount_premium > 0 else f' (referral discount active for {days_left} more days)' if days_left and discounted_price != 24 else ""
                    )
                    subscription_message = ("<strong>Premium subscription</strong>\n\n"
                                            f"Cost: {f"<s>$24</s> " if discounted_price != 24 else ''}${discounted_price}/month"
                                            f"{discount_expiration_info}\n\n"
                                            "<strong>Payment methods:</strong>\n"
                                            "<strong>Telegram Wallet: </strong>@xxx\n"
                                            "<strong>BTC (bitcoin chain): </strong>\n13J81J22ufb9pVNvzVH8fz2yLnWwYzeMsE\n\n"
                                            "<strong>More payment methods here (CashApp, Apple Pay, PayPal, Zelle) – </strong>@xxx\n\n"
                                            "ℹ️ To pay, send funds using any of the methods above. Then be sure to "
                                            "<a href='https://t.me/@xxx'>send us the payment receipt (clickable)</a>"
                                            )
                pagination_buttons = [
                    InlineKeyboardButton(text="❮", callback_data=f"sub_page_{(page - 2) % total_pages + 1}"),
                    InlineKeyboardButton(text=f"{current_subscription}", callback_data="sub_page_inf"),
                    InlineKeyboardButton(text="❯", callback_data=f"sub_page_{page % total_pages + 1}")
                ]
                if user.block == False:
                    buttons = [
                        pagination_buttons,
                        [InlineKeyboardButton(text='🔍 Enter promo code', callback_data='promo_for_sub')],
                        [InlineKeyboardButton(text="↩️ Back", callback_data="back_to_sub")]
                    ]
                else:
                    buttons = [
                        pagination_buttons,
                        [InlineKeyboardButton(text='🔍 Enter promo code', callback_data='promo_for_sub')],
                        [InlineKeyboardButton(text="↩️ Back", callback_data="back_to_end_sub")]
                    ]

                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
                await callback.message.edit_text(
                    f"{subscription_message}",
                    parse_mode="HTML", reply_markup=keyboard, disable_web_page_preview=True
                )
            else:

                if user.block == False:
                    await callback.answer('💲Подписаться')
                else:
                    await callback.answer('💲Продлить')

                basic_premium_list = ['basic', 'premium']
                total_pages = len(basic_premium_list)

                page = (page - 1) % total_pages + 1

                discount_basic = 0
                discount_premium = 0
                if user.active_promo_code:
                    promo_info = await rq.get_promo_info(session, user.active_promo_code)

                    if promo_info and promo_info.promo_type == "discount":
                        if promo_info.subscription_type == 'basic':
                            discount_basic = promo_info.promo_info_discount
                            discount_premium = 0
                        elif promo_info.subscription_type == "premium":
                            discount_premium = promo_info.promo_info_discount
                            discount_basic = 0
                        elif promo_info.subscription_type == "basic+premium":
                            discount_premium = promo_info.promo_info_discount
                            discount_basic = promo_info.promo_info_discount
                if user.used_referral and not user.subscription_start and user.referral_discount_expire > datetime.now():
                    discount_premium += 20
                    discount_basic += 20
                disc = 0
                if user.referrals >= 1:
                    disc = user.referral_discount
                    discount_premium += disc
                    discount_basic += disc
                current_subscription = basic_premium_list[page - 1]
                if current_subscription == 'basic':
                    discounted_price = int(800 * (1 - discount_basic / 100))

                    discount_expiration_info = (
                        f" (промокод действует по {user.promo_expiration.strftime('%d.%m %H:%M')})"
                        if user.active_promo_code and discount_basic > 0 else f' (реферальная скидка активна еще {days_left} дней)' if days_left and discounted_price != 800 else ""
                    )
                    subscription_message = ("Подписка <strong>basic</strong>\n\n"
                                            f"<strong>Стоимость: {f"<s>800</s> " if discounted_price != 800 else ""}{discounted_price} руб./мес.</strong>"
                                            f"{discount_expiration_info}\n\n"
                                            "<strong>Методы оплаты:</strong>\n"
                                            "<strong>Сбербанк: </strong>2202206380914403\n"
                                            "<strong>Telegram Wallet: </strong>@xxx\n"
                                            "(Беларусь)<strong> ЕРИП Белагропромбанк: </strong>\n964112213447/2597\n\n"
                                            "ℹ️ Для оплаты переведите средства любым из указанных выше способов. "
                                            "Затем ОБЯЗАТЕЛЬНО отправьте чек об оплате <a href='https://t.me/@xxx'>нам (кликабельно)</a>"
                                            )
                else:
                    discounted_price = int(1300 * (1 - discount_premium / 100))

                    discount_expiration_info = (
                        f" (промокод действует по {user.promo_expiration.strftime('%d.%m %H:%M')})"
                        if user.active_promo_code and discount_premium > 0 else f' (реферальная скидка активна еще {days_left} дней)' if days_left and discounted_price != 1300 else ""
                    )
                    subscription_message = ("Подписка <strong>premium ✦</strong>\n\n"
                                            f"<strong>Стоимость: {f"<s>1300</s> " if discounted_price != 1300 else ""}{discounted_price} руб./мес.</strong>"
                                            f"{discount_expiration_info}\n\n"
                                            "<strong>Методы оплаты:</strong>\n"
                                            "<strong>Сбербанк: </strong>2202206380914403\n"
                                            "<strong>Telegram Wallet: </strong>@xxx\n"
                                            "(Беларусь)<strong> ЕРИП Белагропромбанк: </strong>\n964112213447/2597\n\n"
                                            "ℹ️ Для оплаты переведите средства любым из указанных выше способов. "
                                            "Затем ОБЯЗАТЕЛЬНО отправьте чек об оплате <a href='https://t.me/xxx'>нам (кликабельно)</a>"
                                            )
                pagination_buttons = [
                    InlineKeyboardButton(text="❮", callback_data=f"sub_page_{(page - 2) % total_pages + 1}"),
                    InlineKeyboardButton(text=f"{current_subscription}", callback_data="sub_page_inf"),
                    InlineKeyboardButton(text="❯", callback_data=f"sub_page_{page % total_pages + 1}")
                ]
                if user.block == False:
                    buttons = [
                        pagination_buttons,
                        [InlineKeyboardButton(text='🔍 Ввести промокод', callback_data='promo_for_sub')],
                        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_sub")]
                    ]
                else:
                    buttons = [
                        pagination_buttons,
                        [InlineKeyboardButton(text='🔍 Ввести промокод', callback_data='promo_for_sub')],
                        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_end_sub")]
                    ]


                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
                await callback.message.edit_text(
                    f"{subscription_message}",
                    parse_mode="HTML", reply_markup=keyboard, disable_web_page_preview=True
                )
@rt.callback_query(F.data.startswith("sub_page_"))
async def change_subscription_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[-1])
    await user_get_sub(callback, page)
@rt.callback_query(F.data == 'change_sub')
async def change_sub(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('Change subscription')
                if user.subscription == 'basic':
                    await callback.message.edit_text('<strong>Change subscription from basic to premium</strong> \n\n'
                                                     f'<strong>Days remaining: {round(user.subscription_day * 0.6)} </strong>',
                                                     parse_mode='HTML', reply_markup=kb.are_you_sure_eng)
                else:
                    await callback.message.edit_text('<strong>Change subscription from premium to basic</strong> \n\n'
                                                     f'<strong>Days remaining: {round(user.subscription_day * 1.6)} </strong>',
                                                     parse_mode='HTML', reply_markup=kb.are_you_sure_eng)
            else:
                await callback.answer('Сменить подписку')
                if user.subscription == 'basic':
                    await callback.message.edit_text('<strong>Сменить подписку с basic на premium</strong> \n\n'
                                                    f'<strong>До окончания подписки: {round(user.subscription_day * 0.6)} дней</strong>', parse_mode='HTML',reply_markup=kb.are_you_sure)
                else:
                    await callback.message.edit_text('<strong>Сменить подписку с premium на basic</strong> \n\n'
                                                     f'<strong>До окончания подписки: {round(user.subscription_day * 1.6)} дней</strong>',
                                                     parse_mode='HTML', reply_markup=kb.are_you_sure)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)

@rt.callback_query(F.data == 'user_yes')
async def user_yes(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:

            if user.subscription == 'basic':
                user.subscription_day = round(user.subscription_day * 0.6)
                user.subscription = 'premium'
            elif user.subscription == 'premium':
                user.subscription_day = round(user.subscription_day * 1.6)
                user.subscription = 'basic'

                groups_result = await session.execute(
                    select(Group).filter(Group.user_id == user_id)
                )
                groups = groups_result.scalars().all()

                group_email_counts = []
                for group in groups:
                    count = await session.scalar(
                        select(func.count(Email.id)).filter(Email.group_id == group.id)
                    )
                    group_email_counts.append((group, count))

                group_email_counts.sort(
                    key=lambda x: (-x[1], -x[0].id))  
                groups_to_keep = [g.id for g, _ in group_email_counts[:3]]

                groups_to_delete = [g.id for g, _ in group_email_counts[3:]]

                flagged_email_result = await session.execute(
                    select(Email).filter(Email.user_id == user_id, Email.flags == True,
                                         Email.group_id.in_(groups_to_delete))
                )
                flagged_email = flagged_email_result.scalar_one_or_none()

                if flagged_email:
                    next_email_result = await session.execute(
                        select(Email)
                        .filter(Email.user_id == user_id, Email.group_id.in_(groups_to_keep))
                        .order_by(Email.id.asc())
                    )
                    next_email = next_email_result.scalars().first()
                    if next_email:
                        next_email.flags = True
                    flagged_email.flags = False

                if groups_to_delete:
                    await session.execute(delete(Email).where(Email.group_id.in_(groups_to_delete)))
                    await session.execute(delete(Beat).where(Beat.group_id.in_(groups_to_delete)))
                    await session.execute(delete(Settings).where(Settings.group_id.in_(groups_to_delete)))
                    await session.execute(delete(Group).where(Group.id.in_(groups_to_delete)))

                emails_result = await session.execute(
                    select(Email).filter(Email.group_id.in_(groups_to_keep)).order_by(desc(Email.created_at))
                )
                all_emails = emails_result.scalars().all()
                if len(all_emails) > 450:
                    emails_to_delete = all_emails[450:]
                    email_ids = [e.id for e in emails_to_delete]
                    await session.execute(delete(Email).where(Email.id.in_(email_ids)))

                beats_result = await session.execute(
                    select(Beat).filter(Beat.group_id.in_(groups_to_keep)).order_by(desc(Beat.created_at))
                )
                all_beats = beats_result.scalars().all()
                if len(all_beats) > 200:
                    beats_to_delete = all_beats[200:]
                    beat_ids = [b.id for b in beats_to_delete]
                    await session.execute(delete(Beat).where(Beat.id.in_(beat_ids)))



            if user.language == 2:
                await callback.message.edit_text(f'<strong>You have successfully changed your subscription to {user.subscription}</strong>', parse_mode='HTML')
                if user.subscription in ['free', 'неактивна']:
                    text = (f"*You do not have an active subscription, access to the bot’s functionality is limited\\.* "
                            f"{"Register to activate a free subscription\n\n" if user.subscription == 'free' else '\n\n'}"
                            f"*Лимиты:*\n"
                            "*Limits:*\n"
                            "• up to 25 letters per day\n"
                            "• up to 50 email addresses in the database\n"
                            "• up to 20 beats in the database\n\n"
                            "🎟 *Available subscriptions:*\n"
                            ">*premium* – 450 letters per day, 50 urgent letters, unlimited email addresses and beats in the database\n"
                            ">*basic* – 450 letters per day, 50 urgent letters, up to 450 email addresses in the database, up to 200 beats in the database")
                elif user.subscription == "basic":
                    text = (f"Your subscription: *basic*\n\n"
                            f"Days remaining: *{user.subscription_day}* \n\n"
                            "*Limits:*\n"
                            "• up to 450 letters per day\n"
                            "• 50 urgent letters\n"
                            "• up to 450 addresses in the database\n"
                            "• up to 200 beats in the database\n\n"
                            "🎟 *Available subscriptions:*\n"
                            ">*premium* – 450 letters per day, 50 urgent letters, unlimited address and beat database\n\n"
                            "You can upgrade to premium at no extra cost\\. The remaining days will be recalculated with a coefficient of 0\\.6")
                else:
                    text = (f"Your subscription: *premium ✦*\n\n"
                            f"Days remaining: *{user.subscription_day}*\n\n"
                            "*Limits:*\n"
                            "• 450 letters per day\n"
                            "• 50 urgent letters\n"
                            "• unlimited address and beat database\n\n"
                            "🎟 *Available subscriptions:*\n"
                            ">*basic* – 450 letters per day, 50 urgent letters, up to 450 email addresses in the database, up to 200 beats in the database\n\n"
                            "You can upgrade to *basic* at no extra cost\\. The remaining days will be recalculated with a coefficient of 1\\.6")

                await callback.answer('🎟 Subscription')
                if user.subscription in ['free', 'неактивна']:
                    await callback.message.answer(text, reply_markup=kb.if_free_sub_eng, parse_mode='MarkdownV2')
                else:
                    await callback.message.answer(text, reply_markup=kb.if_not_free_sub_eng, parse_mode='MarkdownV2')
            else:
                await callback.message.edit_text(f'Вы успешно сменили подписку на {user.subscription}')
                if user.subscription in ['free', 'неактивна']:
                    text = (f"*У вас нет активной подписки, доступ к функционалу бота ограничен\\.* "
                            f"{"Зарегистрируйтесь, чтобы активировать бесплатную подписку\n\n" if user.subscription == 'free' else '\n\n'}"
                            f"*Лимиты:*\n"
                            f"• до 25 писем в день\n"
                            f"• до 50 почт в базе\n"
                            f"• до 20 битов в базе\n\n"
                            f"🎟 *Доступные подписки:*\n"
                            f">*premium* – 450 писем в день, 50 экстренных писем, безлимитная база почт и битов\n"
                            f">*basic* – 450 писем в день, 50 экстренных писем, до 450 почт, до 200 битов")
                elif user.subscription == "basic":
                    text = (f"Ваша подписка: *basic*\n\n"
                            f"До окончания подписки: *{user.subscription_day}* дней\n\n"
                            "*Лимиты:*\n"
                            "• до 450 писем в день\n"
                            "• 50 экстренных писем\n"
                            "• до 450 почт в базе\n"
                            "• до 200 битов в базе\n\n"
                            "🎟 *Доступные подписки:*\n"
                            ">*premium* – 450 писем в день, 50 экстренных писем, безлимитная база почт и битов\n\n"
                            " Вы можете перейти на *premium* без доплаты\\. Оставшиеся дни пересчитаются с коэффициентом 0\\.6")
                else:
                    text = (f"Ваша подписка: *premium ✦*\n\n"
                            f"До окончания подписки: *{user.subscription_day}* дней\n\n"
                            "*Лимиты:*\n"
                            "• до 450 писем в день\n"
                            "• 50 экстренных писем\n"
                            "• безлимитная база почт и битов\n\n"
                            "🎟 *Доступные подписки:*\n"
                            ">*basic* – 450 писем в день, 50 экстренных писем, до 450 почт, до 200 битов\n\n"
                            " Вы можете перейти на *basic* без доплаты\\. Оставшиеся дни пересчитаются с коэффициентом 1\\.6")

                await callback.answer('🎟 Подписка')
                if user.subscription in ['free', 'неактивна']:
                    await callback.message.answer(text, reply_markup=kb.if_free_sub, parse_mode='MarkdownV2')
                else:
                    await callback.message.answer(text, reply_markup=kb.if_not_free_sub, parse_mode='MarkdownV2')
            await session.commit()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'back_to_end_sub')
async def back_to_end_sub(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user.language == 2:
            await callback.answer('↩️ Back')
            await callback.message.edit_text(
                            '<strong>🪫 Your subscription has ended!</strong> Mailing has been paused.\n\n'
                            'To continue using the service, choose an action using the buttons below:',
                            parse_mode='HTML', reply_markup=kb.end_sub_eng
                        )
        else:
            await callback.answer('↩️ Назад')
            await callback.message.edit_text('<strong>🪫 Ваша подписка завершилась!</strong> Рассылка приостановлена.\n\n'
                                        'Чтобы продолжить пользоваться сервисом, выберите действия по кнопкам ниже:',
                                         parse_mode='HTML', reply_markup=kb.end_sub
                                )

@rt.callback_query(F.data == 'back_to_sub')
async def back_to_sub(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('↩️ Back')
            else:
                await callback.answer('↩️ Назад')
            await subscription(callback, state)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)


@rt.callback_query(F.data == 'adm_back')
async def abm_back(callback: CallbackQuery, state: FSMContext):
    await callback.answer('⚙️ ADMIN PANEL')
    await callback.message.edit_text('<strong>Возможные команды:</strong>', reply_markup=kb.adm_start,
                                     parse_mode='HTML')
    await state.clear()


@rt.callback_query(F.data == 'auto')
async def auto(callback: CallbackQuery):
    user_id = callback.from_user.id
    await rq.set_group(callback.from_user.id)
    await callback.answer('Auto')
    user = await rq.get_user(callback.from_user.id)
    if user and not user.block:
        async with async_session() as session:
            result = await session.execute(select(Group).filter(Group.user_id == user_id))
            groups = result.scalars().all()

            if not groups:
                if user.language == 2:
                    await callback.message.edit_text("<strong>You don't have groups</strong>", parse_mode="HTML")
                    return
                else:
                    await callback.message.edit_text("<strong>У вас нет групп.</strong>", parse_mode="HTML")
                    return

            active_group = await session.scalar(select(Group).filter(Group.user_id == user_id, Group.active == True))

            if not active_group:
                active_group = groups[0]
                active_group.active = True
            if user.language == 2:
                await callback.message.edit_text("<strong>Choose an action using the buttons below:</strong>",
                                                 parse_mode="HTML",
                                                 reply_markup=kb.auto_navigation_eng(active_group.name, user))
            else:
                await callback.message.edit_text("<strong>Выберите действия по кнопкам ниже:</strong>", parse_mode="HTML",
                                                 reply_markup=kb.auto_navigation(active_group.name, user))

            await session.commit()
    else:
        await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'auto_page_prev')
async def auto_page_prev(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await rq.get_user(callback.from_user.id)
    if user and not user.block:
        async with async_session() as session:
            result = await session.execute(select(Group).filter(Group.user_id == user_id))
            groups = result.scalars().all()

            active_group = await session.scalar(select(Group).filter(Group.user_id == user_id, Group.active == True))
            if not active_group:
                active_group = groups[0]

            current_index = groups.index(active_group) if active_group in groups else 0
            prev_group = groups[current_index - 1] if current_index > 0 else groups[-1]

            active_group.active = False
            prev_group.active = True
            try:
                if user.language == 2:
                    await callback.message.edit_text("<strong>Choose an action using the buttons below:</strong>",
                                                     parse_mode="HTML",
                                                     reply_markup=kb.auto_navigation_eng(prev_group.name, user))
                else:
                    await callback.message.edit_text("<strong>Выберите действия по кнопкам ниже:</strong>", parse_mode="HTML",
                                                     reply_markup=kb.auto_navigation(prev_group.name, user))
            except TelegramBadRequest:
                await check_group(callback)
            await session.commit()
    else:
        await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'auto_page_next')
async def auto_page_next(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await rq.get_user(callback.from_user.id)
    if user and not user.block:
        async with async_session() as session:
            result = await session.execute(select(Group).filter(Group.user_id == user_id))
            groups = result.scalars().all()

            active_group = await session.scalar(select(Group).filter(Group.user_id == user_id, Group.active == True))
            if not active_group:
                active_group = groups[0]

            current_index = groups.index(active_group) if active_group in groups else 0
            next_group = groups[current_index + 1] if current_index < len(groups) - 1 else groups[0]

            active_group.active = False
            next_group.active = True
            try:
                if user.language == 2:
                    await callback.message.edit_text("<strong>Choose an action using the buttons below:</strong>",
                                                     parse_mode="HTML",
                                                     reply_markup=kb.auto_navigation_eng(next_group.name, user))
                else:
                    await callback.message.edit_text("<strong>Выберите действия по кнопкам ниже:</strong>", parse_mode="HTML",
                                                     reply_markup=kb.auto_navigation(next_group.name, user))
            except TelegramBadRequest:
                await check_group(callback)
            await session.commit()
    else:
        await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)


@rt.callback_query(F.data.startswith('page_auto_info'))
async def check_group(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            async with async_session() as session:
                result = await session.execute(select(Group).filter(Group.user_id == user_id))
                groups = result.scalars().all()

                if not groups:
                    if user.language == 2:
                        await callback.message.edit_text("<strong>You don't have groups</strong>", parse_mode="HTML")
                        return
                    else:
                        await callback.message.edit_text("<strong>У вас нет групп.</strong>", parse_mode="HTML")
                        return

                data_parts = callback.data.split('_')
                page = int(data_parts[-1]) if len(data_parts) > 2 and data_parts[-1].isdigit() else 1

                groups_per_page = 5
                start_index = (page - 1) * groups_per_page
                end_index = start_index + groups_per_page
                groups_to_show = groups[start_index:end_index]

                group_len = len(groups)
                buttons = []
                for group in groups_to_show:
                    buttons.append([InlineKeyboardButton(text=group.name, callback_data=f"group_{group.id}")])
                if user.language == 2:
                    buttons.append(
                        [InlineKeyboardButton(text='⚙️ Group actions', callback_data='button_actions')])
                else:
                    buttons.append([InlineKeyboardButton(text='⚙️ Действия с группами', callback_data='button_actions')])

                pagination_buttons = []
                total_pages = (len(groups) + groups_per_page - 1) // groups_per_page

                next_page = 1 if page >= total_pages else page + 1
                prev_page = total_pages if page <= 1 else page - 1

                if user.subscription == 'premium':
                    if group_len > 5:
                        pagination_buttons.append(
                            InlineKeyboardButton(text="❮", callback_data=f"page_auto_info_{prev_page}"))
                        pagination_buttons.append(
                            InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="nenujno"))
                        pagination_buttons.append(
                            InlineKeyboardButton(text="❯", callback_data=f"page_auto_info_{next_page}"))
                if pagination_buttons:
                    buttons.append(pagination_buttons)
                if user.language == 2:
                    buttons.append(
                        [InlineKeyboardButton(text="↩️ Back", callback_data="back_to_auto")])
                else:
                    buttons.append(
                        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_auto")])

                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
                if user.language == 2:
                    await callback.message.edit_text(
                        "<strong>Choose the group you want to work with below:</strong>", reply_markup=keyboard,
                        parse_mode='HTML')
                else:
                    await callback.message.edit_text(
                        "<strong>Выберите группу, с которой хотите работать ниже:</strong>", reply_markup=keyboard,
                        parse_mode='HTML')
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'create_group')
async def create_group(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:

            async with async_session() as session:
                user = await session.scalar(select(User).filter(User.user_id == user_id))

                if not user:
                    await callback.answer(f"{'Пользователь не найден.' if user.language in [0, 1] else 'User now found'}")
                    return

                if user.subscription == 'free':
                    if user.language == 2:
                        await callback.answer("You cannot create groups because you have a Free subscription.")
                        return
                    else:
                        await callback.answer("Вы не можете создавать группы, так как у вас подписка Free.")
                        return
                elif user.subscription == 'basic':
                    groups_result = await session.execute(select(Group).filter(Group.user_id == user_id))
                    groups = groups_result.scalars().all()
                    if len(groups) >= 3:
                        await callback.answer(f"❗️Достигнут лимит {len(groups)}/3", show_alert=True)
                        return

            if user.language == 2:
                await callback.answer("Enter the group name")
                await callback.message.edit_text("<strong>Enter the name of the new group</strong>",
                                                 reply_markup=kb.back_to_actions_eng, parse_mode='HTML')
            else:
                await callback.answer("Введите название")
                await callback.message.edit_text("<strong>Введите название новой группы</strong>",
                                                 reply_markup=kb.back_to_actions, parse_mode='HTML')

            await state.set_state(GroupState.waiting_for_group_name)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(GroupState.waiting_for_group_name)
async def handle_group_name(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await message.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                group_name = message.text.strip()

                if not group_name:
                    if user.language == 2:
                        await message.answer("Group name cannot be empty.")
                    else:
                        await message.answer("Название группы не может быть пустым.")
                    return

                user_id = message.from_user.id

                async with async_session() as session:
                    new_group = Group(user_id=user_id, name=group_name, active=False)
                    session.add(new_group)
                    await session.commit()

                    result = await session.execute(select(Group).filter(Group.user_id == user_id))
                    groups = result.scalars().all()

                if user.language == 2:
                    await message.answer(f"<strong>✅ Group successfully created</strong>", parse_mode='HTML')
                else:
                    await message.answer(f"<strong>✅ Группа успешно создана</strong>", parse_mode='HTML')

                if not groups:
                    await message.answer("<strong>У вас нет групп.</strong>", parse_mode="HTML")
                    return

                page = 1
                groups_per_page = 5
                start_index = (page - 1) * groups_per_page
                end_index = start_index + groups_per_page
                groups_to_show = groups[start_index:end_index]

                group_len = len(groups)
                buttons = []
                for group in groups_to_show:
                    buttons.append([InlineKeyboardButton(text=group.name, callback_data=f"group_{group.id}")])


                if user.language == 2:
                    buttons.append(
                        [InlineKeyboardButton(text='⚙️ Group actions', callback_data='button_actions')])
                else:
                    buttons.append(
                        [InlineKeyboardButton(text='⚙️ Действия с группами', callback_data='button_actions')])

                pagination_buttons = []
                total_pages = (len(groups) + groups_per_page - 1) // groups_per_page

                next_page = 1 if page >= total_pages else page + 1
                prev_page = total_pages if page <= 1 else page - 1

                if user.subscription == 'premium':
                    if group_len > 5:
                        pagination_buttons.append(
                            InlineKeyboardButton(text="❮", callback_data=f"page_auto_info_{prev_page}"))
                        pagination_buttons.append(
                            InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="nenujno"))
                        pagination_buttons.append(
                            InlineKeyboardButton(text="❯", callback_data=f"page_auto_info_{next_page}"))
                if pagination_buttons:
                    buttons.append(pagination_buttons)

                if user.language == 2:
                    buttons.append(
                        [InlineKeyboardButton(text="↩️ Back", callback_data="back_to_auto")])
                else:
                    buttons.append(
                        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_auto")])

                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
                if user.language == 2:
                    await message.answer("<strong>Choose the group you want to work with below:</strong>",
                                         reply_markup=keyboard, parse_mode='HTML')
                else:
                    await message.answer("<strong>Выберите группу, с которой хотите работать ниже:</strong>",
                                         reply_markup=keyboard, parse_mode='HTML')
                await state.clear()
async def show_group(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await message.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                group_name = message.text.strip()

                if not group_name:
                    if user.language == 2:
                        await message.answer("Group name cannot be empty.")
                    else:
                        await message.answer("Название группы не может быть пустым.")
                    return

                user_id = message.from_user.id

                async with async_session() as session:

                    result = await session.execute(select(Group).filter(Group.user_id == user_id))
                    groups = result.scalars().all()

                if not groups:
                    if user.language == 2:
                        await message.answer("<strong>You don't have groups</strong>", parse_mode="HTML")
                    else:
                        await message.answer("<strong>У вас нет групп.</strong>", parse_mode="HTML")
                    return

                page = 1
                groups_per_page = 5
                start_index = (page - 1) * groups_per_page
                end_index = start_index + groups_per_page
                groups_to_show = groups[start_index:end_index]

                group_len = len(groups)
                buttons = []
                for group in groups_to_show:
                    buttons.append([InlineKeyboardButton(text=group.name, callback_data=f"group_{group.id}")])


                if user.language == 2:
                    buttons.append(
                        [InlineKeyboardButton(text='⚙️ Group actions', callback_data='button_actions')])
                else:
                    buttons.append(
                        [InlineKeyboardButton(text='⚙️ Действия с группами', callback_data='button_actions')])

                pagination_buttons = []
                total_pages = (len(groups) + groups_per_page - 1) // groups_per_page
                next_page = 1 if page >= total_pages else page + 1
                prev_page = total_pages if page <= 1 else page - 1

                if user.subscription == 'premium':
                    if group_len > 5:
                        pagination_buttons.append(
                            InlineKeyboardButton(text="❮", callback_data=f"page_auto_info_{prev_page}"))
                        pagination_buttons.append(
                            InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="nenujno"))
                        pagination_buttons.append(
                            InlineKeyboardButton(text="❯", callback_data=f"page_auto_info_{next_page}"))
                if pagination_buttons:
                    buttons.append(pagination_buttons)
                if user.language == 2:
                    buttons.append(
                        [InlineKeyboardButton(text="↩️ Back", callback_data="back_to_auto")])
                else:
                    buttons.append(
                        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_auto")])

                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
                if user.language == 2:
                    await message.answer("<strong>Choose the group you want to work with below:</strong>",
                                         reply_markup=keyboard, parse_mode='HTML')
                else:
                    await message.answer("<strong>Выберите группу, с которой хотите работать ниже:</strong>", reply_markup=keyboard, parse_mode='HTML')
                await state.clear()
@rt.callback_query(F.data == 'button_actions')
async def button_actions(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('⚙️ Group actions')
                buttons = []
                buttons.append(
                    [InlineKeyboardButton(text="📠 Rename group", callback_data="rename_group"),
                     InlineKeyboardButton(text='ℹ️ What are groups for?', url='https://telegra.ph/ℹ--Gruppy-05-23')])
                buttons.append([InlineKeyboardButton(text="🗑 Delete group", callback_data="delete_group"),
                                InlineKeyboardButton(text="➕ Add group", callback_data="create_group")])
                buttons.append(
                    [InlineKeyboardButton(text="↩️ Back", callback_data="back_to_group")])
                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
                await callback.message.edit_text('<strong>Choose group actions using the buttons below:</strong>',
                                                 parse_mode='HTML', reply_markup=keyboard)
            else:
                await callback.answer('⚙️ Действия с группами')
                buttons = []
                buttons.append(
                    [InlineKeyboardButton(text="📠 Изменить имя группы", callback_data="rename_group"), InlineKeyboardButton(text='ℹ️ Для чего нужны группы?', url='https://telegra.ph/ℹ--Gruppy-05-23')])
                buttons.append([InlineKeyboardButton(text="🗑 Удалить группу", callback_data="delete_group"),
                                InlineKeyboardButton(text="➕ Создать группу", callback_data="create_group")])
                buttons.append(
                    [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_group")])
                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
                await callback.message.edit_text('<strong>Выберите действия с группами по кнопкам ниже:</strong>', parse_mode='HTML', reply_markup=keyboard)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'back_to_group')
async def back_to_group(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            await callback.answer(f'↩️ {"Назад" if user.language in [0, 1] else "Back"}')
            await check_group(callback)
            await state.clear()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'back_to_actions')
async def back_to_actions(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('↩️ Back')
            else:
                await callback.answer('↩️ Назад')
            await button_actions(callback, state)
            await state.clear()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'rename_group')
async def rename_group(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            async with async_session() as session:
                result = await session.execute(select(Group).filter(Group.user_id == user_id))
                groups = result.scalars().all()

                if not groups:
                    if user.language == 2:
                        await callback.message.edit_text("❌ You don't have any groups to rename.")
                    else:
                        await callback.message.edit_text("❌ У вас нет групп для переименования.")
                    return

                await state.update_data(rename_page=1)
                await state.set_state(GroupState.renaming_group)
                await show_rename_group_page(callback.message, groups, 1, user_id=user_id)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
async def show_rename_group_page(message, groups, page, user_id: int = 0):

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await message.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                groups_per_page = 5
                total_pages = (len(groups) + groups_per_page - 1) // groups_per_page
                page = max(1, min(page, total_pages))

                start = (page - 1) * groups_per_page
                end = start + groups_per_page
                groups_to_show = groups[start:end]

                buttons = [
                    [InlineKeyboardButton(text=group.name, callback_data=f"rename_selected_{group.id}")]
                    for group in groups_to_show
                ]

                prev_page = total_pages if page == 1 else page - 1
                next_page = 1 if page == total_pages else page + 1
                if user.subscription == "premium":
                    if total_pages > 1:
                        buttons.append([
                            InlineKeyboardButton(text="❮", callback_data=f"rename_page_{prev_page}"),
                            InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"),
                            InlineKeyboardButton(text="❯", callback_data=f"rename_page_{next_page}")
                        ])
                if user.language == 2:
                    buttons.append([InlineKeyboardButton(text="↩️ Back", callback_data="back_to_actions")])
                else:
                    buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_actions")])

                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
                if user.language == 2:
                    await message.edit_text(
                        "<strong>Choose the group you want to rename</strong>",
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                else:
                    await message.edit_text(
                        "<strong>Выберите группу, имя которой вы хотите изменить</strong>",
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
@rt.callback_query(F.data.startswith("rename_page_"))
async def rename_pagination(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:

            async with async_session() as session:
                result = await session.execute(select(Group).filter(Group.user_id == user_id))
                groups = result.scalars().all()

            await state.update_data(rename_page=page)
            await show_rename_group_page(callback.message, groups, page)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data.startswith("rename_selected_"))
async def rename_selected(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            group_id = int(callback.data.split("_")[-1])
            await state.update_data(group_to_rename=group_id)
            if user.language == 2:
                await callback.message.edit_text("<b>Enter the new group name</b>", reply_markup=kb.back_to_actions_eng,
                                                 parse_mode='HTML')
            else:
                await callback.message.edit_text("<b>Введите новое имя группы</b>", reply_markup=kb.back_to_actions, parse_mode='HTML')
            await state.set_state(GroupState.waiting_for_group_name_swap)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(GroupState.waiting_for_group_name_swap)
async def apply_new_group_name(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block: 
                try:
                    await message.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                data = await state.get_data()
                group_id = data.get("group_to_rename")
                new_name = message.text.strip()

                if not new_name:
                    await message.answer("❗ Название не может быть пустым.")
                    return

                async with async_session() as session:
                    group = await session.get(Group, group_id)
                    if group:
                        group.name = new_name
                        if user.language == 2:
                            await message.answer(f"✅ <b>Group name successfully changed</b>", parse_mode="HTML")
                        else:
                            await message.answer(f"✅ <b>Имя группы успешно изменено</b>", parse_mode="HTML")
                        await session.commit()
                    else:
                        if user.language == 2:
                            await message.answer("❌ Group not found.")
                        else:
                            await message.answer("❌ Группа не найдена.")
                await show_group(message, state)
                await state.clear()
GROUPS_PER_PAGE = 5
@rt.callback_query(F.data == 'delete_group')
async def delete_group(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer(
                    '⚠️ After deletion, all data linked to the deleted group — beats, addresses, and settings — will be permanently removed.'
                    '\n\nRecovery of this data will be impossible!', show_alert=True)
            else:
                await callback.answer('⚠️ После удаления все данные, связанные с удаленной группой — биты, почты и настройки — будут безвозвратно удалены.'
                                      '\n\nВосстановление этих данных будет невозможно!', show_alert=True)
            async with async_session() as session:
                user_result = await session.execute(select(User).filter(User.user_id == user_id))
                user = user_result.scalar_one_or_none()

                result = await session.execute(select(Group).filter(Group.user_id == user_id))
                groups = result.scalars().all()

            if not groups:
                if user.language == 2:
                    await callback.message.edit_text("❌ You don't have a group to delete..")
                else:
                    await callback.message.edit_text("❌ У вас нет групп для удаления.")
                return

            if user.subscription == "basic":
                buttons = [
                    [InlineKeyboardButton(text=group.name, callback_data=f"delgrp_{group.id}")]
                    for group in groups[:3]
                ]
                if user.language == 2:
                    buttons.append([InlineKeyboardButton(text="↩️ Back", callback_data="back_to_actions")])
                else:
                    buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_actions")])
                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
                if user.language == 2:
                    await callback.message.edit_text(
                        "<strong>🔴 Select the groups you want to delete</strong>",
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                else:
                    await callback.message.edit_text(
                        "<strong>🔴 Выберите группы, которые хотите удалить</strong>",
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
            else:
                await state.update_data(delete_page=0)
                await send_delete_group_page(callback.message, user_id, groups, 0)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
async def send_delete_group_page(message, user_id, groups, page):

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await message.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                total = len(groups)
                total_pages = (total + GROUPS_PER_PAGE - 1) // GROUPS_PER_PAGE

                page = page % total_pages 
                start = page * GROUPS_PER_PAGE
                end = start + GROUPS_PER_PAGE
                groups_to_show = groups[start:end]

                group_len = len(groups)
                buttons = [
                    [InlineKeyboardButton(text=group.name, callback_data=f"delgrp_{group.id}")]
                    for group in groups_to_show
                ]
                if user.subscription == 'premium':
                    if group_len > 5:
                        nav_buttons = [
                            InlineKeyboardButton(text = "❮", callback_data=f"delete_page_{page - 1}"),
                            InlineKeyboardButton(text = f"{page + 1}/{total_pages}", callback_data="noop"),
                            InlineKeyboardButton(text = "❯", callback_data=f"delete_page_{page + 1}"),
                        ]
                        buttons.append(nav_buttons)
                if user.language == 2:
                    buttons.append([InlineKeyboardButton(text="↩️ Back", callback_data="back_to_actions")])
                else:
                    buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_actions")])
                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

                if user.language == 2:
                    await message.edit_text(
                        "<strong>🔴 Select the groups you want to delete</strong>",
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                else:
                    await message.edit_text(
                        "<strong>🔴 Выберите группы, которые хотите удалить</strong>",
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
@rt.callback_query(F.data.startswith("delete_page_"))
async def paginate_delete_group(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            async with async_session() as session:
                result = await session.execute(select(Group).filter(Group.user_id == user_id))
                groups = result.scalars().all()

            await send_delete_group_page(callback.message, user_id, groups, page)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data.startswith("delgrp_"))
async def delete_selected_group(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            group_id = int(callback.data.split("_")[1])

            async with async_session() as session:
                group = await session.scalar(select(Group).filter(Group.id == group_id, Group.user_id == user_id))
                if group:
                    result = await session.execute(select(Group).filter(Group.user_id == user_id))
                    groups = result.scalars().all()

                    if len(groups) == 1:
                        if user.language == 2:
                            await callback.answer(
                                "❌ You cannot delete the last group",
                                show_alert=True
                            )
                        else:
                            await callback.answer(
                                "❌ Вы не можете удалить последнюю группу",
                                show_alert=True
                            )
                        return
                    group_ids = [g.id for g in groups]

                    flagged_email_result = await session.execute(
                        select(Email).filter(Email.user_id == user_id, Email.flags == True)
                    )
                    flagged_email = flagged_email_result.scalar_one_or_none()

                    if flagged_email and flagged_email.group_id in group_ids:
                        next_email_result = await session.execute(
                            select(Email)
                            .filter(Email.user_id == user_id, Email.group_id != flagged_email.group_id)
                            .order_by(Email.id.asc())
                        )
                        next_email = next_email_result.scalars().first()
                        if next_email:
                            next_email.flags = True
                        flagged_email.flags = False

                    group_name = group.name
                    await session.delete(group)
                    if user.language == 2:
                        text = f"✅ Group <strong>{group_name}</strong> successfully deleted."
                    else:
                        text = f"✅ Группа <strong>{group_name}</strong> удалена."
                    await session.commit()
                else:
                    if user.language == 2:
                        text = "❌ Group not found."
                    else:
                        text = "❌ Группа не найдена."

                result = await session.execute(select(Group).filter(Group.user_id == user_id))
                groups = result.scalars().all()

            if not groups:
                if user.language == 2:
                    await callback.message.edit_text(f"{text}\n\n<strong>No more groups exist.</strong>",
                                                     parse_mode="HTML")
                else:
                    await callback.message.edit_text(f"{text}\n\n<strong>У вас больше нет групп.</strong>", parse_mode="HTML")
                return

            if user.subscription == "basic":
                buttons = [
                    [InlineKeyboardButton(text=group.name, callback_data=f"delgrp_{group.id}")]
                    for group in groups[:3]
                ]
                if user.language == 2:
                    buttons.append([InlineKeyboardButton(text="↩️ Back", callback_data="back_to_actions")])
                else:
                    buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_actions")])
                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

                if user.language == 2:
                    await callback.message.edit_text(
                        f"<strong>🔴 Select the groups you want to delete</strong>",
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                else:
                    await callback.message.edit_text(
                        f"<strong>🔴 Выберите группы, которые хотите удалить</strong>",
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
            else:
                data = await state.get_data()
                current_page = data.get("delete_page", 0)
                await send_delete_group_page(callback.message, user_id, groups, current_page)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'back_to_group')
async def back_to_group(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('↩️ Back')
            else:
                await callback.answer('↩️ Назад')
            await check_group(callback)
            await state.clear()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data.startswith('group_'))
async def switch_group(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await rq.get_user(callback.from_user.id)
    group_id = int(callback.data.split('_')[1])
    if user and not user.block:
        async with async_session() as session:
            group = await session.scalar(select(Group).filter(Group.user_id == user_id, Group.id == group_id))
            if group:
                await session.execute(update(Group).filter(Group.user_id == user_id).values({"active": False}))

                group.active = True
                if user.language == 2:
                    await callback.message.edit_text(f"<strong>Choose an action using the buttons below::</strong>",
                                                     parse_mode="HTML",
                                                     reply_markup=kb.auto_navigation_eng(group.name, user))
                else:
                    await callback.message.edit_text(f"<strong>Выберите действия по кнопкам ниже:</strong>", parse_mode="HTML",
                                                     reply_markup=kb.auto_navigation(group.name, user))
            else:
                if user.language == 2:
                    await callback.answer("Group not found.")
                else:
                    await callback.answer("Группа не найдена.")
            await session.commit()
    else:
        await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)

#Почта
@rt.callback_query(F.data == 'mail')
async def mail(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('✉️ Addresses')
            else:
                await callback.answer('✉️ Почты')

            async with async_session() as session:
                active_group = await session.scalar(select(Group).filter(Group.user_id == user_id, Group.active == True))

            if not active_group:
                if user.language == 2:
                    await callback.answer('❌ You do not have an active group to display mail.')
                else:
                    await callback.answer('❌ У вас нет активной группы для отображения почт.')
                return

            async with async_session() as session:
                result = await session.execute(select(Email).filter(Email.user_id == user_id, Email.group_id == active_group.id))
                emails = result.scalars().all()

                if not emails:
                    if user.language == 2:
                        await callback.message.edit_text('🤷🏻‍♂️ <strong>Your address list is empty</strong>',
                                                         reply_markup=kb.zero_mail_eng, parse_mode='HTML')
                    else:
                        await callback.message.edit_text('🤷🏻‍♂️ <strong>Ваш список почт пуст</strong>',
                                                         reply_markup=kb.zero_mail, parse_mode='HTML')
                    return

                emails_per_page = 30
                total_pages = (len(emails) + emails_per_page - 1) // emails_per_page

                page = 1

                if callback.data.startswith("page_"):
                    page = int(callback.data.split("_")[1])

                start_index = (page - 1) * emails_per_page
                end_index = page * emails_per_page
                current_page_emails = emails[start_index:end_index]

                email_list = '\n'.join([f'{email.email}' for email in current_page_emails])

                if user.language == 2:
                    buttons = kb.mail_navigation_eng(page, total_pages)
                    await callback.message.edit_text(
                        f'<strong>Your address list ({len(emails)})</strong>\n\n{email_list}',
                        parse_mode='HTML', reply_markup=buttons)
                else:
                    buttons = kb.mail_navigation(page, total_pages)
                    await callback.message.edit_text(
                        f'<strong>Ваш список почт ({len(emails)})</strong>\n\n{email_list}',
                        parse_mode='HTML', reply_markup=buttons)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)

@rt.callback_query(F.data == 'back_to_auto')
async def back_to_auto(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('↩️ Back')
            else:
                await callback.answer('↩️ Назад')
            await auto(callback)
            await state.clear()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'mail_back')
async def mail_back(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('↩️ Back')
            else:
                await callback.answer('↩️ Назад')
            await auto(callback)
            await state.clear()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)

@rt.callback_query(F.data == 'add_mail')
async def add_mail(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:

            async with async_session() as session:
                active_group = await session.scalar(select(Group).filter(Group.user_id == user_id, Group.active == True))

            if not active_group:
                if user.language == 2:
                    await callback.answer('❌ You do not have an active group to add mail.',
                                          reply_markup=kb.back_to_mail_eng)
                else:
                    await callback.answer('❌ У вас нет активной группы для добавления почт.', reply_markup=kb.back_to_mail)
                return

            async with async_session() as session:
                result = await session.execute(select(User).filter(User.user_id == user_id))
                user = result.scalars().first()

            async with async_session() as session:
                result = await session.execute(select(Email).filter(Email.user_id == user_id, Email.group_id == active_group.id))
                emails = result.scalars().all()

            async with async_session() as session:
                total_emails_count = await session.scalar(select(func.count(Email.id)).filter(Email.user_id == user_id))

            if user.subscription == 'free':
                max_emails = 50
            elif user.subscription == 'basic':
                max_emails = 450
            elif user.subscription == 'premium':
                max_emails = 999999999

            remaining_space = max_emails - total_emails_count
            if user.language == 2:
                if remaining_space <= 0:
                    await callback.answer(
                        f'❗️ Limit reached {max_emails}/{max_emails}', show_alert=True)
                    return
                await callback.answer('📩 Add')
                await state.set_state(UserState.waiting_for_emails)
                await callback.message.edit_text(f'<strong>Send the addresses you want to add</strong>', parse_mode="HTML",reply_markup=kb.back_to_mail_with_complete_eng)
            else:
                if remaining_space <= 0:
                    await callback.answer(
                        f'❗️ Достигнут лимит {max_emails}/{max_emails}', show_alert=True)
                    return
                await callback.answer('📩 Пополнить')
                await state.set_state(UserState.waiting_for_emails)
                await callback.message.edit_text(f'<strong>Отправьте почты, которые хотите добавить</strong>', parse_mode="HTML",reply_markup=kb.back_to_mail_with_complete)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(UserState.waiting_for_emails)
async def handle_emails(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await msg.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:

                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                found_emails = [email.lower() for email in re.findall(email_pattern, msg.text)]

                data = await state.get_data()
                current_emails = data.get("pending_emails", [])
                for email in found_emails:
                    if email not in current_emails:
                        current_emails.append(email)
                await state.update_data(pending_emails=list(current_emails))
@rt.callback_query(F.data == 'finish_mail_upload', UserState.waiting_for_emails)
async def finish_email_upload(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            data = await state.get_data()
            pending_emails = data.get("pending_emails", [])

            if not pending_emails:
                if user.language == 2:
                    await callback.answer("❗️No valid addresses added", show_alert=True)
                else:
                    await callback.answer("❗️Нет ни одного корректного адреса", show_alert=True)
                return

            async with async_session() as session:
                active_group = await session.scalar(select(Group).where(Group.user_id == user_id, Group.active == True))

                if not active_group or not user:
                    if user.language == 2:
                        await callback.message.edit_text("❌ You do not have an active group to add mails.", reply_markup=kb.back_to_mail_eng)
                    else:
                        await callback.message.edit_text("❌ У вас нет активной группы для добавления почт.", reply_markup=kb.back_to_mail)
                    return

                existing_result = await session.execute(
                    select(Email.email).filter(Email.user_id == user_id, Email.group_id == active_group.id)
                )
                existing_emails = set(email.lower() for email in existing_result.scalars().all())

                total_emails_count = await session.scalar(select(func.count(Email.id)).filter(Email.user_id == user_id))
                max_emails = {"free": 50, "basic": 450, "premium": 999999999}.get(user.subscription, 50)
                remaining_space = max_emails - total_emails_count

                if remaining_space <= 0:
                    if user.language == 2:
                        await callback.answer(f'❗️Limit reached {max_emails}/{max_emails}', show_alert=True)
                    else:
                        await callback.answer(f'❗️Достигнут лимит {max_emails}/{max_emails}', show_alert=True)
                    return

                all_user_emails_result = await session.execute(
                    select(Email.email).where(Email.user_id == user_id)
                )
                all_user_emails = set(email.lower() for email in all_user_emails_result.scalars().all())

                emails_to_add = []
                for email in pending_emails:
                    if email not in all_user_emails:
                        emails_to_add.append(email)

                emails_to_add = emails_to_add[:remaining_space]
                remaining_unadded = set(pending_emails) - set(emails_to_add)

                for email in emails_to_add:
                    session.add(Email(user_id=user_id, email=email, group_id=active_group.id))

                await session.commit()

            if emails_to_add:
                if user.language == 2:
                    await callback.message.answer(
                        f'<strong>✅ {len(emails_to_add)} addresses added</strong>',
                        parse_mode='HTML'
                    )
                else:
                    await callback.message.answer(
                        f'<strong>✅ Добавлено {len(emails_to_add)} почт</strong>',
                        parse_mode='HTML'
                    )

            if remaining_unadded:
                MAX_DISPLAY = 100
                not_added_list = list(remaining_unadded)
                display_part = "\n".join(not_added_list[:MAX_DISPLAY])
                extra_count = len(not_added_list) - MAX_DISPLAY

                if user.language == 2:
                    msg = f"<strong>❗️NOT ADDED:</strong>\n\n{display_part}"
                    if extra_count > 0:
                        msg += f"\n<strong>... and {extra_count} more</strong>"
                else:
                    msg = f"<strong>❗️НЕ БЫЛИ ДОБАВЛЕНЫ:</strong>\n\n{display_part}"
                    if extra_count > 0:
                        msg += f"\n<strong>... и еще {extra_count}</strong>"

                await callback.message.answer(msg, parse_mode='HTML')

            await state.clear()
            await show_emails(callback.message, user_id=user_id)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)



@rt.callback_query(F.data == 'back_to_mail')
async def back_to_mail(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('↩️ Back')
            else:
                await callback.answer('↩️ Назад')
            await mail(callback)
            await state.clear()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)

async def show_emails(msg: Message, page: int = 1, user_id: int = 1):
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
    async with async_session() as session:
        active_group = await session.scalar(select(Group).filter(Group.user_id == user_id, Group.active == True))

    if not active_group:
        if user.language == 2:
            await msg.answer('❌ You do not have an active group to display mail.')
        else:
            await msg.answer('❌ У вас нет активной группы для отображения почт.')
        return

    async with async_session() as session:
        result = await session.execute(select(Email).filter(Email.user_id == user_id, Email.group_id == active_group.id))
        emails = result.scalars().all()

    emails_per_page = 30
    total_pages = (len(emails) + emails_per_page - 1) // emails_per_page

    start = (page - 1) * emails_per_page
    end = page * emails_per_page
    current_page_emails = emails[start:end]

    email_list = '\n'.join([f'{email.email}' for email in current_page_emails])
    if not emails:
        if user.language == 2:
            await msg.answer('🤷🏻‍♂️ <strong>Your address list is empty</strong>',
                             reply_markup=kb.zero_mail_eng, parse_mode='HTML')
        else:
            await msg.answer('🤷🏻‍♂️ <strong>Ваш список почт пуст</strong>',
                                             reply_markup=kb.zero_mail, parse_mode='HTML')
        return
    if user.language == 2:
        buttons = kb.mail_navigation_eng(page, total_pages)
        await msg.answer(f'<strong>Your address list ({len(emails)})</strong>\n\n{email_list}', parse_mode='HTML',
                         reply_markup=buttons)
    else:
        buttons = kb.mail_navigation(page, total_pages)
        await msg.answer(f'<strong>Ваш список почт ({len(emails)})</strong>\n\n{email_list}', parse_mode='HTML', reply_markup=buttons)
@rt.callback_query(F.data.startswith('mailpage_'))
async def page_navigation(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            data = callback.data.split("_") 

            if len(data) != 2:
                if user.language == 2:
                    await callback.answer('❌ Error in navigation data.')
                else:
                    await callback.answer('❌ Ошибка в данных навигации.')
                return

            try:
                page = int(data[1])  
            except ValueError:
                if user.language == 2:
                    await callback.answer('❌ Invalid data format for page.')
                else:
                    await callback.answer('❌ Неверный формат данных для страницы.')
                return

            async with async_session() as session:
                active_group = await session.scalar(select(Group).filter(Group.user_id == user_id, Group.active == True))

                if not active_group:
                    if user.language == 2:
                        await callback.answer('❌ You do not have an active group to display mails.')
                    else:
                        await callback.answer('❌ У вас нет активной группы для отображения почт.')
                    return

                result = await session.execute(select(Email).filter(Email.user_id == user_id, Email.group_id == active_group.id))
                emails = result.scalars().all()

            if not emails:
                if user.language == 2:
                    await callback.message.edit_text('🤷🏻‍♂️ <strong>Your address list is empty</strong>',
                                                     reply_markup=kb.zero_mail_eng, parse_mode='HTML')
                else:
                    await callback.message.edit_text('🤷🏻‍♂️ <strong>Ваш список почт пуст</strong>',
                                                 reply_markup=kb.zero_mail, parse_mode='HTML')
                return

            emails_per_page = 30
            total_pages = (len(emails) + emails_per_page - 1) // emails_per_page

            page = max(1, min(page, total_pages))

            start_index = (page - 1) * emails_per_page
            end_index = page * emails_per_page
            current_page_emails = emails[start_index:end_index]

            email_list = '\n'.join([f'{email.email}' for email in current_page_emails])

            if user.language == 2:
                buttons = kb.mail_navigation_eng(page, total_pages)
                await callback.message.edit_text(
                    f'<strong>Your address list  ({len(emails)})</strong>\n\n{email_list}',
                    parse_mode='HTML',
                    reply_markup=buttons
                )
            else:
                buttons = kb.mail_navigation(page, total_pages)
                await callback.message.edit_text(
                    f'<strong>Ваш список почт ({len(emails)})</strong>\n\n{email_list}',
                    parse_mode='HTML',
                    reply_markup=buttons
                )
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == "page_info")
async def ask_page_number(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer("Enter the page number")
                await callback.message.answer("<strong>Enter the page number you want to go to:</strong>",
                                              parse_mode='HTML', reply_markup=kb.back_to_mail_eng)
            else:
                await callback.answer("Введите страницу")
                await callback.message.answer("<strong>Введите номер страницы, на которую хотите перейти:</strong>", parse_mode='HTML', reply_markup=kb.back_to_mail)
            await state.set_state(UserState.waiting_for_page_number)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(UserState.waiting_for_page_number)
async def go_to_page(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    page_text = msg.text.strip()
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
    if not page_text.isdigit():
        if user.language == 2:
            await msg.answer("❌ Enter a valid value")
        else:
            await msg.answer("❌ Введите корректный номер страницы (число).")
        return

    page = int(page_text)

    async with async_session() as session:
        active_group = await session.scalar(
            select(Group).filter(Group.user_id == user_id, Group.active == True)
        )

        if not active_group:
            if user.language == 2:
                await msg.answer("❌ You don't have active group")
            else:
                await msg.answer("❌ У вас нет активной группы.")
            await state.clear()
            return

        result = await session.execute(
            select(Email).filter(Email.user_id == user_id, Email.group_id == active_group.id)
        )
        emails = result.scalars().all()

    if not emails:
        if user.language == 2:
            await msg.answer('🤷🏻‍♂️ <strong>Your address list is empty</strong>',
                             reply_markup=kb.zero_mail_eng, parse_mode='HTML')
        else:
            await msg.answer('🤷🏻‍♂️ <strong>Ваш список почт пуст</strong>',
                                                 reply_markup=kb.zero_mail, parse_mode='HTML')
        await state.clear()
        return

    emails_per_page = 30
    total_pages = (len(emails) + emails_per_page - 1) // emails_per_page

    if page < 1 or page > total_pages:
        if user.language == 2:
            await msg.answer(f"⚠️ Enter a number from 1 to {total_pages}")
        else:
            await msg.answer(f"⚠️ Введите число от 1 до {total_pages}")
        return

    start_index = (page - 1) * emails_per_page
    end_index = page * emails_per_page
    current_page_emails = emails[start_index:end_index]

    email_list = '\n'.join([f'{email.email}' for email in current_page_emails])


    if user.language == 2:
        buttons = kb.mail_navigation_eng(page, total_pages)
        await msg.answer(f'<strong>Your address list ({len(emails)})</strong>\n\n{email_list}', parse_mode='HTML',
                         reply_markup=buttons)
    else:
        buttons = kb.mail_navigation(page, total_pages)
        await msg.answer(f'<strong>Ваш список почт ({len(emails)})</strong>\n\n{email_list}', parse_mode='HTML',
                         reply_markup=buttons)
    await state.clear()



@rt.callback_query(F.data=="delete_mail")
async def delete_pack_start(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await call.message.answer(
                    "<strong>Send the addresses you want to delete — each on a new line or separated by commas</strong>",
                    parse_mode='HTML', reply_markup=kb.back_to_mail_with_complete_eng)
            else:
                await call.message.answer(
                    "<strong>Отправьте почты, которые хотите удалить — каждую с новой строки или через запятую</strong>",
                    parse_mode='HTML',reply_markup=kb.back_to_mail_with_complete)
            await state.set_state(UserState.waiting_for_delete_emails)
        else:
            await call.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(UserState.waiting_for_delete_emails)
async def handle_delete_emails(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    async with async_session() as session:
        user = await session.scalar(select(User).filter(User.user_id == user_id))

        if user:
            if user.block:
                try:
                    await msg.delete()
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                emails = [email.strip().lower() for email in re.split(r'[\n,]+', msg.text)]
                valid_emails = [email for email in emails if '@' in email and '.' in email]

                data = await state.get_data()
                current_emails = set(data.get("pending_emails", []))
                current_emails.update(valid_emails)
                await state.update_data(pending_emails=list(current_emails))
@rt.callback_query(F.data == 'finish_mail_upload', UserState.waiting_for_delete_emails)
async def finish_email_delete(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            user_id = callback.from_user.id
            data = await state.get_data()
            pending_emails = set(data.get("pending_emails", []))

            if not pending_emails:
                if user.language == 2:
                    await callback.answer("❗️No valid addresses added", show_alert=True)
                else:
                    await callback.answer("❗️Нет ни одного корректного адреса", show_alert=True)
                return

            user = await session.scalar(select(User).where(User.user_id == user_id))
            if not user:
                if user.language == 2:
                    await callback.message.edit_text("Error: User not found.")
                else:
                    await callback.message.edit_text("Ошибка: пользователь не найден.")
                return

            result = await session.execute(
                select(Email)
                .where(Email.user_id == user_id)
                .order_by(Email.id)
            )
            emails = result.scalars().all()
            email_map = {email.email.lower(): email for email in emails}

            existing_email_set = set(email_map.keys())
            emails_to_remove = list(pending_emails & existing_email_set)

            flagged_email = next((email for email in emails if email.flags), None)

            if flagged_email and flagged_email.email.lower() in emails_to_remove:
                next_email = None
                for email in emails:
                    if email.email.lower() not in emails_to_remove and email.id+1 == flagged_email.id:
                        next_email = email
                        break
                if next_email:
                    next_email.flags = True
                    session.add(next_email)
                else:
                    for email in reversed(emails):
                        if email.email.lower() not in emails_to_remove and email.id < flagged_email.id:
                            email.flags = True
                            session.add(email)
                            break
                flagged_email.flags = False
                session.add(flagged_email)

            if emails_to_remove:
                await session.execute(
                    delete(Email)
                    .where(Email.user_id == user_id, Email.email.in_(emails_to_remove))
                )



            if emails_to_remove:
                if user.language == 2:
                    await callback.message.answer(
                        f'✅ <strong>{len(emails_to_remove)} addresses deleted</strong>', parse_mode='HTML'
                    )
                else:
                    await callback.message.answer(
                        f'✅ <strong>Удалено {len(emails_to_remove)} почт</strong>', parse_mode='HTML'
                    )
            await session.commit()
            await state.clear()
            await show_emails(callback.message, user_id=user_id)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
            , show_alert=True)


#Биты

@rt.callback_query(F.data == 'back_to_beat')
async def back_to_beat(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('↩️ Back')
            else:
                await callback.answer('↩️ Назад')
            await beat(callback)
            await state.clear()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'beat_back')
async def beat_back(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('↩️ Back')
            else:
                await callback.answer('↩️ Назад')
            await auto(callback)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'beats')
async def beat(callback: CallbackQuery, page: int = 1):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('🎵 Beats')
            else:
                await callback.answer('🎵 Биты')

            async with async_session() as session:
                active_group = await session.scalar(select(Group).filter(Group.user_id == user_id, Group.active == True))

            if not active_group:
                if user.language == 2:
                    await callback.message.edit_text('❌ You do not have an active group to display bits.')
                else:
                    await callback.message.edit_text('❌ У вас нет активной группы для отображения битов.')
                return

            async with async_session() as session:
                result = await session.execute(select(Beat).filter(Beat.user_id == user_id, Beat.group_id == active_group.id))
                beats = result.scalars().all()

                if not beats:
                    if user.language == 2:
                        await callback.message.edit_text('🤷🏻‍♂️ <strong>Your beat list is empty</strong>',
                                                         reply_markup=kb.zero_beats_eng, parse_mode='HTML')
                    else:
                        await callback.message.edit_text('🤷🏻‍♂️ <strong>Ваш список битов пуст</strong>',
                                     reply_markup=kb.zero_beats, parse_mode='HTML')
                    return

                beats_per_page = 10
                total_pages = (len(beats) + beats_per_page - 1) // beats_per_page

                page = max(1, min(page, total_pages))

                start_index = (page - 1) * beats_per_page
                end_index = page * beats_per_page
                current_page_beats = beats[start_index:end_index]

                buttons = []

                for beat in current_page_beats:
                    beat_button = InlineKeyboardButton(text=beat.name, callback_data=f"beat_{beat.id}")
                    buttons.append([beat_button])

                pagination_buttons = [
                    InlineKeyboardButton(
                        text="❮",
                        callback_data=f"page_{total_pages if page == 1 else page - 1}"
                    ),
                    InlineKeyboardButton(
                        text=f"{page}/{total_pages}",
                        callback_data="nenujno"
                    ),
                    InlineKeyboardButton(
                        text="❯",
                        callback_data=f"page_{1 if page == total_pages else page + 1}"
                    )
                ]

                if pagination_buttons:
                    buttons.append(pagination_buttons)
                if user.language == 2:
                    buttons.append([
                        InlineKeyboardButton(text="🗑 Delete", callback_data="delete_beat"),
                        InlineKeyboardButton(text="➕ Add", callback_data="add_beat")
                    ])

                    buttons.append([InlineKeyboardButton(text="↩️ Back", callback_data="beat_back")])

                    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

                    await callback.message.edit_text(
                        f'<strong>Your beat list ({len(beats)})</strong>\n\n',
                        parse_mode='HTML', reply_markup=keyboard)
                else:
                    buttons.append([
                        InlineKeyboardButton(text="🗑 Удалить", callback_data="delete_beat"),
                        InlineKeyboardButton(text="➕ Пополнить", callback_data="add_beat")
                    ])

                    buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data="beat_back")])

                    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

                    await callback.message.edit_text(
                        f'<strong>Ваш список битов ({len(beats)})</strong>\n\n',
                        parse_mode='HTML', reply_markup=keyboard)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == "nenujno")
async def ask_for_page(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.message.answer("<strong>Enter the page number you want to go to:</strong>",
                                              reply_markup=kb.back_to_beat_eng, parse_mode='HTML')
            else:
                await callback.message.answer("<strong>Введите номер страницы, на которую хотите перейти:</strong>",
                                              reply_markup=kb.back_to_beat, parse_mode='HTML')
            await state.set_state(UserState.waiting_for_page_number_beats)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(UserState.waiting_for_page_number_beats)
async def process_page_input(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:
                try:
                    await message.delete()
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                try:
                    page = int(message.text)
                    active_group = await session.scalar(
                        select(Group).filter(Group.user_id == user_id, Group.active == True)
                    )
                    beats_result = await session.execute(
                        select(Beat).filter(Beat.user_id == user_id, Beat.group_id == active_group.id)  
                    )
                    beats = beats_result.scalars().all()
                    total_pages = max((len(beats) + 9) // 10, 1) 

                    if page < 1 or page > total_pages:
                        if user.language == 2:
                            await message.answer(f"⚠️ Enter a number from 1 to {total_pages}")
                        else:
                            await message.answer(f"⚠️ Введите число от 1 до {total_pages}")
                        return

                    await state.clear()
                    await show_beats(message, state, page=page, user_id=user_id)

                except ValueError:
                    if user.language == 2:
                        await message.answer("❗️Enter a valid value")
                    else:
                        await message.answer("🚫 Введите корректный номер страницы (целое число).")
@rt.callback_query(F.data == 'add_beat')
async def add_beat(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:

            async with async_session() as session:
                active_group = await session.scalar(select(Group).filter(Group.user_id == user_id, Group.active == True))

            if not active_group:
                if user.language == 2:
                    await callback.message.edit_text("❌ You don't have an active group to add beats to.",
                                                     reply_markup=kb.back_to_beat_eng)
                else:
                    await callback.message.edit_text('❌ У вас нет активной группы для добавления битов.', reply_markup=kb.back_to_beat)
                return

            async with async_session() as session:
                total_beats_count = await session.scalar(select(func.count(Beat.id)).filter(Beat.user_id == user_id))

            if user.subscription == 'free':
                max_beats = 20
            elif user.subscription == 'basic':
                max_beats = 200
            elif user.subscription == 'premium':
                max_beats = 9999999999

            if user.language == 2:
                remaining_space = max_beats - total_beats_count
                if remaining_space <= 0:
                    await callback.answer(
                        f'❗️Limit reached {total_beats_count}/{max_beats}', show_alert=True)
                    return
                await callback.answer('➕ Add')
                await state.set_state(GroupState.waiting_for_beat)
                if user.subscription == 'premium':
                    await callback.message.answer(f'<strong>Send the beats you want to add</strong>',
                                                  parse_mode='HTML', reply_markup=kb.confirm_upload_beat_eng)
                else:
                    await callback.message.answer(f'<strong>Send the beats you want to add</strong>',
                                                  parse_mode='HTML', reply_markup=kb.confirm_upload_beat_eng)
            else:
                remaining_space = max_beats - total_beats_count
                if remaining_space <= 0:
                    await callback.answer(
                        f'❗️Достигнут лимит {total_beats_count}/{max_beats}', show_alert=True)
                    return
                await callback.answer('➕ Пополнить')
                await state.set_state(GroupState.waiting_for_beat)
                if user.subscription == 'premium':
                    await callback.message.answer(f'<strong>Отправьте биты, которые хотите добавить</strong>', parse_mode='HTML',reply_markup=kb.confirm_upload_beat)
                else:
                    await callback.message.answer(f'<strong>Отправьте биты, которые хотите добавить</strong>', parse_mode='HTML',reply_markup=kb.confirm_upload_beat)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(GroupState.waiting_for_beat, F.data == "finish_beat_upload")
async def finish_upload(callback: CallbackQuery, state: FSMContext):
    message = callback.message
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            data = await state.get_data()
            beats = data.get("beats", [])

            if not beats:
                await state.clear()
                if user.language == 2:
                    await callback.answer("❗️You didn’t send any beats", show_alert=True)
                else:
                    await callback.answer("❗️Вы не отправили ни одного бита", show_alert=True)
                return

            print(f"Запрос на получение активной группы для пользователя {user_id}")
            async with async_session() as session:
                result = await session.execute(
                    select(Group).filter(Group.user_id == user_id, Group.active == True)
                )
                active_group = result.scalars().first()
            if active_group:
                print(f"Найдена активная группа: {active_group.id}")
            else:
                await state.clear()
                if user.language == 2:
                    await message.answer("❌ You don't have an active group to add beats to.",
                                         reply_markup=kb.back_to_beat_eng)
                else:
                    await message.answer("❌ У вас нет активной группы для добавления битов.", reply_markup=kb.back_to_beat)
                print("Активная группа не найдена.")
                return

            async with async_session() as session:
                total_beats_count = await session.scalar(
                    select(func.count(Beat.id)).filter(Beat.user_id == user_id)
                )

            max_beats = {
                "free": 20,
                "basic": 200,
                "premium": 9999999999
            }.get(user.subscription, 20)

            remaining_space = max_beats - total_beats_count
            added = 0
            duplicates = []
            skipped_due_to_limit = []

            for beat in beats:
                if remaining_space <= 0:
                    skipped_due_to_limit.append(beat["file_name"])
                    continue

                async with async_session() as session:
                    existing = await session.scalar(
                        select(Beat).filter(Beat.user_id == user_id, Beat.group_id==active_group.id, Beat.file_id == beat["file_id"])
                    )

                if existing:
                    duplicates.append(beat["file_name"])
                    continue

                async with async_session() as session:
                    new_beat = Beat(
                        user_id=user_id,
                        file_id=beat["file_id"],
                        file_format=beat["file_format"],
                        name=beat["file_name"],
                        group_id=active_group.id
                    )
                    session.add(new_beat)
                    await session.commit()

                added += 1
                remaining_space -= 1

            await state.clear()
            if user.language == 2:
                if added > 0:
                    response = f"✅ <b>{added} beats added</b>"
                    await message.answer(response, parse_mode='HTML')
                await callback.answer('✅ Ready')

                if duplicates or skipped_due_to_limit:
                    text = "❗️<b>️NOT ADDED:</b>"

                    keyboard = InlineKeyboardMarkup(
                        inline_keyboard=[
                            *[[InlineKeyboardButton(text=name, callback_data="beat_info_ignore")] for name in
                              duplicates],
                            *[[InlineKeyboardButton(text=name, callback_data="beat_info_ignore")] for name in
                              skipped_due_to_limit]
                        ]
                    )

                    await message.answer(text, reply_markup=keyboard, parse_mode='HTML')
            else:
                if added > 0:
                    response = f"✅ <b>Добавлено {added} битов</b>"
                    await message.answer(response, parse_mode='HTML')
                await callback.answer('✅ Готово')

                if duplicates or skipped_due_to_limit:
                    text = "❗️<b>НЕ БЫЛИ ДОБАВЛЕНЫ:</b>"

                    keyboard = InlineKeyboardMarkup(
                        inline_keyboard=[
                            *[[InlineKeyboardButton(text=name, callback_data="beat_info_ignore")] for name in duplicates],
                            *[[InlineKeyboardButton(text=name, callback_data="beat_info_ignore")] for name in
                              skipped_due_to_limit]
                        ]
                    )

                    await message.answer(text, reply_markup=keyboard, parse_mode='HTML')

            await show_beats(callback.message, state, user_id=user_id)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == "delete_temp_msg")
async def delete_temp_message(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            await callback.message.delete()
            await callback.answer()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(GroupState.waiting_for_beat)
async def handle_beats(msg: Message, state: FSMContext):
    user_id = msg.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await msg.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                if msg.audio or msg.document:
                    file = msg.audio or msg.document
                    file_format = file.file_name.split('.')[-1].lower() if file.file_name else ''

                    if user.language == 2:
                        if file_format not in ['mp3', 'wav']:
                            return await msg.answer("Only .mp3 or .wav files are accepted.")
                    else:
                        if file_format not in ['mp3', 'wav']:
                            return await msg.answer("Только .mp3 или .wav файлы принимаются.")

                    data = await state.get_data()
                    if "beats" not in data:
                        data["beats"] = []
                    data["beats"].append({
                        "file_id": file.file_id,
                        "file_name": file.file_name,
                        "file_format": file_format
                    })
                    await state.update_data(beats=data["beats"])
async def show_beats(msg: Message, state: FSMContext, page: int = 1, user_id: int = 0):

    print(f"Запрос на получение активной группы для пользователя {user_id}")

    async with async_session() as session:
        result = await session.execute(
            select(Group).filter(Group.user_id == user_id, Group.active == True)
        )
        active_group = result.scalars().first()
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()


    if active_group:
        print(f"Найдена активная группа: {active_group.id}")
    else:
        await state.clear()
        if user.language == 2:
            await msg.answer("❌ You don't have an active group to display bits.", reply_markup=kb.back_to_beat_eng)
        else:
            await msg.answer("❌ У вас нет активной группы для отображения битов.", reply_markup=kb.back_to_beat)
        print(f"Активная группа не найдена для пользователя {user_id}.")
        return

    async with async_session() as session:
        result = await session.execute(select(Beat).filter(Beat.user_id == user_id, Beat.group_id == active_group.id))
        beats = result.scalars().all()

        if not beats:
            if user.language == 2:
                await msg.answer('🤷🏻‍♂️ <strong>Your beat list is empty</strong>',
                                 reply_markup=kb.zero_beats_eng, parse_mode='HTML')
            else:
                await msg.answer('🤷🏻‍♂️ <strong>Ваш список битов пуст</strong>',
                                                 reply_markup=kb.zero_beats, parse_mode='HTML')
            return


        beats_per_page = 10
        total_pages = (len(beats) + beats_per_page - 1) // beats_per_page

        page = max(1, min(page, total_pages))

        start_index = (page - 1) * beats_per_page
        end_index = page * beats_per_page
        current_page_beats = beats[start_index:end_index]

        buttons = []

        for beat in current_page_beats:
            beat_button = InlineKeyboardButton(text=beat.name, callback_data=f"beat_{beat.id}")
            buttons.append([beat_button])

        pagination_buttons = [
            InlineKeyboardButton(
                text="❮",
                callback_data=f"page_{total_pages if page == 1 else page - 1}"
            ),
            InlineKeyboardButton(
                text=f"{page}/{total_pages}",
                callback_data="nenujno"
            ),
            InlineKeyboardButton(
                text="❯",
                callback_data=f"page_{1 if page == total_pages else page + 1}"
            )
        ]

        if pagination_buttons:
            buttons.append(pagination_buttons)

        if user.language == 2:
            buttons.append([
                InlineKeyboardButton(text="🗑 Delete", callback_data="delete_beat"),
                InlineKeyboardButton(text="➕ Add", callback_data="add_beat")
            ])

            buttons.append([InlineKeyboardButton(text="↩️ Back", callback_data="beat_back")])

            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            await msg.answer(
                f'<strong>Your beat list ({len(beats)})</strong>\n\n',
                parse_mode='HTML', reply_markup=keyboard)
        else:
            buttons.append([
                InlineKeyboardButton(text="🗑 Удалить", callback_data="delete_beat"),
                InlineKeyboardButton(text="➕ Пополнить", callback_data="add_beat")
            ])

            buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data="beat_back")])

            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            await msg.answer(
                f'<strong>Ваш список битов ({len(beats)})</strong>\n\n',
                parse_mode='HTML', reply_markup=keyboard)
        await state.clear()
@rt.callback_query(F.data.startswith("beat_"))
async def send_beat(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            beat_id = int(callback.data.split("_")[1])

            async with async_session() as session:
                beat = await session.scalar(select(Beat).filter(Beat.id == beat_id))

            if not beat:
                if user.language == 2:
                    await callback.answer("❌ Beat not found", show_alert=True)
                else:
                    await callback.answer("❌ Бит не найден", show_alert=True)
                return

            await callback.message.answer_audio(audio=beat.file_id)
            await callback.answer()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == "delete_beat")
async def start_delete_beat(callback: CallbackQuery, state: FSMContext, page: int = 1):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            await state.update_data(delete_beat_page=page)
            await state.set_state(UserState.waiting_for_delete_beat)
            async with async_session() as session:
                active_group = await session.scalar(select(Group).filter(Group.user_id == user_id, Group.active == True))
            async with async_session() as session:
                beats = await session.scalars(select(Beat).filter(Beat.user_id == user_id, Beat.user_id == user_id, Beat.group_id == active_group.id))
                beats = list(beats)

            if not beats:
                if user.language == 2:
                    await callback.answer("You have no bits available.", show_alert=True)
                else:
                    await callback.answer("У вас нет доступных битов.", show_alert=True)
                return

            beats_per_page = 10
            total_pages = (len(beats) + beats_per_page - 1) // beats_per_page
            page = max(1, min(page, total_pages))

            start_idx = (page - 1) * beats_per_page
            end_idx = page * beats_per_page
            beats_on_page = beats[start_idx:end_idx]

            keyboard = InlineKeyboardMarkup(inline_keyboard=[])

            for beat in beats_on_page:
                keyboard.inline_keyboard.append([InlineKeyboardButton(text=beat.name, callback_data=f"delete_beat_{beat.id}")])

            pagination_buttons = [
                InlineKeyboardButton(
                    text="❮",
                    callback_data=f"delete_beat_page_{total_pages if page == 1 else page - 1}"
                ),
                InlineKeyboardButton(
                    text=f"{page}/{total_pages}",
                    callback_data="nenujno_delete"
                ),
                InlineKeyboardButton(
                    text="❯",
                    callback_data=f"delete_beat_page_{1 if page == total_pages else page + 1}"
                )
            ]

            if pagination_buttons:
                keyboard.inline_keyboard.append(pagination_buttons)

            if user.language == 2:
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(text="🗑 Delete via import", callback_data="start_mass_delete")
                ])
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(text="↩️ Back", callback_data="cancel_delete_beat")
                ])
                await callback.answer("🗑 Delete")
                await callback.message.edit_text("🔴 <strong>Select the beats you want to delete</strong>",
                                                 parse_mode="HTML", reply_markup=keyboard)
                await callback.answer()
            else:
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(text="🗑 Очистить через импорт", callback_data="start_mass_delete")
                ])
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(text="↩️ Назад", callback_data="cancel_delete_beat")
                ])
                await callback.answer("🗑 Удалить")
                await callback.message.edit_text("🔴 <strong>Выберите биты, которые хотите удалить</strong>", parse_mode="HTML",reply_markup=keyboard)
                await callback.answer()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == "nenujno_delete")
async def ask_for_page_delete(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.message.answer("<strong>Enter the page number you want to go to:</strong>",
                                              reply_markup=kb.back_to_beat_eng, parse_mode='HTML')
            else:
                await callback.message.answer("<strong>Введите номер страницы, на которую хотите перейти:</strong>", reply_markup=kb.back_to_beat, parse_mode='HTML')
            await state.set_state(UserState.waiting_for_page_number_beats_delete)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(UserState.waiting_for_page_number_beats_delete)
async def process_page_input_delete(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await message.delete() 
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                try:
                    page = int(message.text)
                    await state.clear()
                    await show_start_delete_beat(message, state, page=page, user_id=user_id)
                except ValueError:
                    if user.language == 2:
                        await message.answer("❗️Enter a valid value")
                    else:
                        await message.answer("🚫 Введите корректный номер страницы (целое число).")
async def show_start_delete_beat(message: Message, state: FSMContext, page: int = 1, user_id: int = 0):
    await state.update_data(delete_beat_page=page)
    await state.set_state(UserState.waiting_for_delete_beat)
    async with async_session() as session:
        print(f'user id: {user_id}')
        active_group = await session.scalar(select(Group).filter(Group.user_id == user_id, Group.active == True))
        print(f'Active group: {active_group}')
        beats = await session.scalars(select(Beat).filter(Beat.user_id == user_id, Beat.group_id == active_group.id))
        beats = list(beats)
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

    beats_per_page = 10
    total_pages = (len(beats) + beats_per_page - 1) // beats_per_page
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * beats_per_page
    end_idx = page * beats_per_page
    beats_on_page = beats[start_idx:end_idx]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for beat in beats_on_page:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=beat.name, callback_data=f"delete_beat_{beat.id}")])

    pagination_buttons = [
        InlineKeyboardButton(
            text="❮",
            callback_data=f"delete_beat_page_{total_pages if page == 1 else page - 1}"
        ),
        InlineKeyboardButton(
            text=f"{page}/{total_pages}",
            callback_data="nenujno_delete"
        ),
        InlineKeyboardButton(
            text="❯",
            callback_data=f"delete_beat_page_{1 if page == total_pages else page + 1}"
        )
    ]

    if pagination_buttons:
        keyboard.inline_keyboard.append(pagination_buttons)
    if user.language == 2:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🗑 Delete via import", callback_data="start_mass_delete")
        ])
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="↩️ Back", callback_data="cancel_delete_beat")
        ])
        if not beats:
            await message.answer("You have no bits available.", show_alert=True)
            await show_beats(message, state, user_id=user_id)
            return
        await message.answer("<strong>🔴 Select the beats you want to delete</strong>", parse_mode='HTML',
                             reply_markup=keyboard)
    else:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🗑 Очистить через импорт", callback_data="start_mass_delete")
        ])
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="↩️ Назад", callback_data="cancel_delete_beat")
        ])
        if not beats:
            await message.answer("У вас нет доступных битов.", show_alert=True)
            await show_beats(message, state, user_id=user_id)
            return
        await message.answer("🔴 <strong>Выберите биты, которые хотите удалить</strong>", parse_mode='HTML',reply_markup=keyboard)
@rt.callback_query(F.data == "start_mass_delete")
async def start_mass_delete(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            await state.set_state(UserState.waiting_for_delete_beat)
            await state.update_data(beats_to_delete=[])

            if user.language == 2:
                await callback.message.answer(
                    "<strong>Send the beats you want to delete</strong>", parse_mode="HTML",
                    reply_markup=kb.confirm_upload_beat_eng
                )
            else:
                await callback.message.answer(
                    "<strong>Отправьте биты, которые хотите удалить</strong>", parse_mode="HTML",reply_markup=kb.confirm_upload_beat
                )
            await callback.answer()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(F.audio, UserState.waiting_for_delete_beat)
async def collect_audio(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await message.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                audio_file = message.audio  
                logging.info(f"Получено аудио: {audio_file.file_id}")  

                audio_name = audio_file.file_name  

                user_data = await state.get_data()
                audio_files = user_data.get("audio_files", [])
                audio_files.append(audio_name)  
                await state.update_data(audio_files=audio_files)
@rt.callback_query(F.data == "finish_beat_upload", UserState.waiting_for_delete_beat)
async def delete_selected_beats(callback: CallbackQuery, state: FSMContext):
    message = callback.message
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            user_data = await state.get_data()
            beats_to_delete = user_data.get("audio_files", [])
            async with async_session() as session:
                active_group = await session.scalar(select(Group).filter(Group.user_id == user_id, Group.active == True))
            if not beats_to_delete:
                if user.language == 2:
                    await callback.answer("❗️You didn’t send any beats")
                else:
                    await callback.answer("❗️Вы не отправили ни одного бита")
                return

            async with async_session() as session:
                beats = await session.scalars(
                    select(Beat).filter(Beat.user_id == user_id, Beat.group_id == active_group.id, Beat.name.in_(beats_to_delete))
                )
                beats = list(beats)

                if not beats:
                    await state.clear()
                    await show_start_delete_beat(message, state, user_id=user_id)
                    return

                for beat in beats:
                    await session.delete(beat)
                if beats:
                    if user.language == 2:
                        await callback.message.answer(f'<strong>✅ {len(beats)} beats deleted</strong>',
                                                      parse_mode='HTML')
                    else:
                        await callback.message.answer(f'<strong>✅ Удалено {len(beats)} битов</strong>', parse_mode='HTML')
                await session.commit()

            await state.clear()
            await show_start_delete_beat(message, state, user_id=user_id)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data.startswith("delete_beat_page_"))
async def change_delete_beat_page(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            page = int(callback.data.split("_")[-1])
            await start_delete_beat(callback, state, page)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data.startswith("delete_beat_"))
async def delete_beat(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            beat_id = int(callback.data.split("_")[2])

            async with async_session() as session:
                beat = await session.scalar(select(Beat).filter(Beat.id == beat_id))
                if not beat:
                    await callback.answer("❌ Бит не найден")
                    return

                await session.delete(beat)
                await session.commit()

            if user.language == 2:
                await callback.answer("✅ Beat removed")
            else:
                await callback.answer("✅ Бит удален")

            async with async_session() as session:
                active_group = await session.scalar(select(Group).filter(Group.user_id == user_id, Group.active == True))
                beats = await session.scalars(select(Beat).filter(Beat.user_id == user_id, Beat.group_id == active_group.id))
                beats = list(beats)

            if not beats:
                await callback.message.delete()
                await show_beats(callback.message, state, user_id=user_id)
                return

            user_data = await state.get_data()
            current_page = user_data.get("delete_beat_page", 1)

            beats_per_page = 10  
            total_pages = (len(beats) + beats_per_page - 1) // beats_per_page

            if current_page > total_pages:
                current_page = total_pages

            await start_delete_beat(callback, state, current_page)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == "cancel_delete_beat")
async def cancel_delete_beat(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            await state.clear()
            await beat(callback)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data.startswith("page_"))
async def change_page(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('🎵 Beats')
            else:
                await callback.answer('🎵 Биты')

            try:
                page = int(callback.data.split("_")[1])
            except ValueError:
                return

            async with async_session() as session:
                active_group = await session.scalar(select(Group).filter(Group.user_id == user_id, Group.active == True))

            if not active_group:
                if user.language == 2:
                    await callback.answer("❌ You don't have an active group to display bits.")
                else:
                    await callback.answer('❌ У вас нет активной группы для отображения битов.')
                return

            async with async_session() as session:
                result = await session.execute(select(Beat).filter(Beat.user_id == user_id, Beat.group_id == active_group.id))
                beats = result.scalars().all()

                if not beats:
                    if user.language == 2:
                        await callback.message.edit_text('🤷🏻‍♂️ <strong>Your beat list is empty</strong>',
                                                         reply_markup=kb.zero_beats_eng, parse_mode='HTML')
                    else:
                        await callback.message.edit_text('🤷🏻‍♂️ <strong>Ваш список битов пуст</strong>',
                                                         reply_markup=kb.zero_beats, parse_mode='HTML')
                    return

                beats_per_page = 10
                total_pages = (len(beats) + beats_per_page - 1) // beats_per_page

                page = max(1, min(page, total_pages))

                start_index = (page - 1) * beats_per_page
                end_index = page * beats_per_page
                current_page_beats = beats[start_index:end_index]

                buttons = []

                for beat in current_page_beats:
                    beat_button = InlineKeyboardButton(text=beat.name, callback_data=f"beat_{beat.id}")
                    buttons.append([beat_button])

                pagination_buttons = [
                    InlineKeyboardButton(
                        text="❮",
                        callback_data=f"page_{total_pages if page == 1 else page - 1}"
                    ),
                    InlineKeyboardButton(
                        text=f"{page}/{total_pages}",
                        callback_data="nenujno"
                    ),
                    InlineKeyboardButton(
                        text="❯",
                        callback_data=f"page_{1 if page == total_pages else page + 1}"
                    )
                ]

                if pagination_buttons:
                    buttons.append(pagination_buttons)

                if user.language == 2:
                    buttons.append([
                        InlineKeyboardButton(text="🗑 Delete", callback_data="delete_beat"),
                        InlineKeyboardButton(text="➕ Add", callback_data="add_beat")
                    ])

                    buttons.append([InlineKeyboardButton(text="↩️ Back", callback_data="beat_back")])

                    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

                    await callback.message.edit_text(
                        f'<strong>Your beat list ({len(beats)})</strong>\n\n',
                        parse_mode='HTML', reply_markup=keyboard)
                else:
                    buttons.append([
                        InlineKeyboardButton(text="🗑 Удалить", callback_data="delete_beat"),
                        InlineKeyboardButton(text="➕ Пополнить", callback_data="add_beat")
                    ])

                    buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data="beat_back")])

                    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

                    await callback.message.edit_text(
                        f'<strong>Ваш список битов ({len(beats)})</strong>\n\n',
                        parse_mode='HTML', reply_markup=keyboard)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)



#Настройки
@rt.callback_query(F.data == 'settings_back')
async def settings_back(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('↩️ Back')
            else:
                await callback.answer('↩️ Назад')
            await auto(callback)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'back_to_settings')
async def back_to_settings(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('↩️ Back')
            else:
                await callback.answer('↩️ Назад')
            await setting(callback)
            await state.clear()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'back_to_interval')
async def back_to_interval(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('↩️ Back')
            else:
                await callback.answer('↩️ Назад')
            await pack_interval(callback)
            await state.clear()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'back_to_dispatch_time')
async def back_to_interval(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('↩️ Back')
            else:
                await callback.answer('↩️ Назад')
            await dispatch_time(callback, state)
            await state.clear()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)

@rt.callback_query(F.data == 'settings')
async def setting(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('⚙️ Settings')
            else:
                await callback.answer('⚙️ Настройки')
            async with async_session() as session:
                active_group = await session.scalar(select(Group).filter(Group.user_id == user_id, Group.active == True))

            async with async_session() as session:
                one_on_off = False
                result = await session.execute(select(Settings).where(Settings.group_id == active_group.id))
                settings = result.scalars().first()
                one_active_group = await session.scalar(
                    select(Group).filter(Group.user_id == callback.from_user.id, Group.active == True))
                one_result = await session.execute(
                    select(OneTimeSettings).where(OneTimeSettings.group_id == one_active_group.id))
                one_settings = one_result.scalars().first()
                if one_settings:
                    one_on_off = one_settings.on_of_auto

                if not settings:
                    other_settings_result = await session.execute(
                        select(Settings).where(Settings.user_id == user_id, Settings.group_id != active_group.id)
                    )
                    other_settings = other_settings_result.scalars().first()

                    settings = Settings(
                        group_id=active_group.id,
                        periodicity=other_settings.periodicity if other_settings else 'everyday',
                        send_time=other_settings.send_time if other_settings else datetime.combine(datetime.today(),
                                                                                                   time(19, 0)),
                        quantity_beat=other_settings.quantity_beat if other_settings else 2,
                        interval=other_settings.interval if other_settings else 0,
                        user_id=user_id
                    )
                    session.add(settings)

                if user.language == 2:
                    if settings.periodicity == 'everyday':
                        settings_periodicity = 'daily'
                    elif settings.periodicity == 'everyday_2':
                        settings_periodicity = 'every 2 days'
                    elif settings.periodicity == 'everyday_3':
                        settings_periodicity = 'every 3 days'
                    elif settings.periodicity == 'everyday_4':
                        settings_periodicity = 'every 4 days'
                    else:
                        settings_periodicity = 'not set'

                    on_off = '🟩 Active' if settings.on_of_auto else '🟥 Disabled'
                    formatted_time = settings.send_time.strftime("%H:%M") if settings.send_time else "unspecified"
                    await callback.message.edit_text(
                        f'*Current email settings:*\n\n'
                        f'*📋 Email subject:* '
                        f'{f'\n{format_as_quote(settings.subject)}\n' if settings.subject and settings.subject != "Без темы" else "__not set__"}\n\n'
                        f'*📄 Email body:* '
                        f'{f'\n{format_as_quote(settings.message)}\n' if settings.message and settings.message != "Без текста" else "__not set__"}\n\n'
                        f'*🗓 Sending frequency:* {settings_periodicity}\n\n'
                        f'*⏰ Sending time:* {formatted_time if formatted_time else "Не задано"}\n\n'
                        f'*🔉 Number of audio files per email:* {settings.quantity_beat}\n'
                        f'{f'\n*↔️ Interval:* {'no interval' if settings.interval == 0 or settings.interval == "none" else f'{settings.interval} minutes' if settings.interval in [1] else f'{settings.interval} minutes' if settings.interval in [2, 3, 4] else f'{settings.interval} minutes'}\n———\n\n' if user.subscription not in ['free', 'Неуказано', 'не указано'] else '———\n\n'}'
                        f'*⚙️ Choose the settings you want to change using the buttons below:*',
                        reply_markup=kb.settings_button_eng(on_off, user.subscription, one_on_off),
                        parse_mode='MarkdownV2', disable_web_page_preview=True
                    )
                else:
                    if settings.periodicity == 'everyday':
                        settings_periodicity = 'ежедневно'
                    elif settings.periodicity == 'everyday_2':
                        settings_periodicity = 'раз в 2 дня'
                    elif settings.periodicity == 'everyday_3':
                        settings_periodicity = 'раз в 3 дня'
                    elif settings.periodicity == 'everyday_4':
                        settings_periodicity = 'раз в 4 дня'
                    else:
                        settings_periodicity = 'неуказано'

                    on_off = '🟩 Включено' if settings.on_of_auto else '🟥 Выключено'
                    formatted_time = settings.send_time.strftime("%H:%M") if settings.send_time else "Не задано"
                    await callback.message.edit_text(
                        f'*Текущие параметры письма:*\n\n'
                        f'*📋 Заголовок письма:* '
                        f'{f'\n{format_as_quote(settings.subject)}\n' if settings.subject and settings.subject != "Без темы" else "__не задано__"}\n\n'
                        f'*📄 Текст письма:* '
                        f'{f'\n{format_as_quote(settings.message)}\n' if settings.message and settings.message != "Без текста" else "__не задано__"}\n\n'
                        f'*🗓 Периодичность отправки:* {settings_periodicity}\n\n'
                        f'*⏰ Время отправки:* {formatted_time if formatted_time else "Не задано"}\n\n'
                        f'*🔉 Количество аудио в одном письме:* {settings.quantity_beat}\n'
                        f'{f'\n*↔️ Интервал:* {'без интервала' if settings.interval == 0 or settings.interval == "none" else f'{settings.interval} минута' if settings.interval in [1] else f'{settings.interval} минуты' if settings.interval in [2, 3, 4] else f'{settings.interval} минут'}\n———\n\n' if user.subscription not in ['free','Неуказано','не указано'] else '———\n\n'}'
                        f'*⚙️ Выберите настройки которые хотите поменять по кнопкам ниже:*',
                        reply_markup=kb.settings_button(on_off, user.subscription, one_on_off),
                        parse_mode='MarkdownV2', disable_web_page_preview=True
                    )

                await session.commit()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
async def send_settings_message(user_id: int, message: Message):
    async with async_session() as session:
        active_group = await session.scalar(select(Group).filter(Group.user_id == user_id, Group.active == True))
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        one_on_off = False
        result = await session.execute(select(Settings).where(Settings.group_id == active_group.id))
        settings = result.scalars().first()
        one_active_group = await session.scalar(
            select(Group).filter(Group.user_id == user_id, Group.active == True))
        one_result = await session.execute(
            select(OneTimeSettings).where(OneTimeSettings.group_id == one_active_group.id))
        one_settings = one_result.scalars().first()
        if one_settings:
            one_on_off = one_settings.on_of_auto

        if not settings:
            other_settings_result = await session.execute(
                select(Settings).where(Settings.user_id == user_id, Settings.group_id != active_group.id)
            )
            other_settings = other_settings_result.scalars().first()

            settings = Settings(
                group_id=active_group.id,
                periodicity=other_settings.periodicity if other_settings else 'everyday',
                send_time=other_settings.send_time if other_settings else datetime.combine(datetime.today(),
                                                                                           time(19, 0)),
                quantity_beat=other_settings.quantity_beat if other_settings else 2,
                interval=other_settings.interval if other_settings else 0,
                user_id=user_id
            )
            session.add(settings)

        if user.language == 2:
            if settings.periodicity == 'everyday':
                settings_periodicity = 'daily'
            elif settings.periodicity == 'everyday_2':
                settings_periodicity = 'every 2 days'
            elif settings.periodicity == 'everyday_3':
                settings_periodicity = 'every 3 days'
            elif settings.periodicity == 'everyday_4':
                settings_periodicity = 'every 4 days'
            else:
                settings_periodicity = 'not set'

            on_off = '🟩 Active' if settings.on_of_auto else '🟥 Disabled'
            formatted_time = settings.send_time.strftime("%H:%M") if settings.send_time else "unspecified"
            await message.answer(
                f'*Current email settings:*\n\n'
                f'*📋 Email subject:* '
                f'{f'\n{format_as_quote(settings.subject)}\n' if settings.subject and settings.subject != "Без темы" else "__not set__"}\n\n'
                f'*📄 Email body:* '
                f'{f'\n{format_as_quote(settings.message)}\n' if settings.message and settings.message != "Без текста" else "__not set__"}\n\n'
                f'*🗓 Sending frequency:* {settings_periodicity}\n\n'
                f'*⏰ Sending time:* {formatted_time if formatted_time else "Не задано"}\n\n'
                f'*🔉 Number of audio files per email:* {settings.quantity_beat}\n'
                f'{f'\n*↔️ Interval:* {'no interval' if settings.interval == 0 or settings.interval == "none" else f'{settings.interval} minutes' if settings.interval in [1] else f'{settings.interval} minutes' if settings.interval in [2, 3, 4] else f'{settings.interval} minutes'}\n———\n\n' if user.subscription not in ['free', 'Неуказано', 'не указано'] else '———\n\n'}'
                f'*⚙️ Choose the settings you want to change using the buttons below:*',
                reply_markup=kb.settings_button_eng(on_off, user.subscription, one_on_off),
                parse_mode='MarkdownV2', disable_web_page_preview=True
            )
        else:
            if settings.periodicity == 'everyday':
                settings_periodicity = 'ежедневно'
            elif settings.periodicity == 'everyday_2':
                settings_periodicity = 'раз в 2 дня'
            elif settings.periodicity == 'everyday_3':
                settings_periodicity = 'раз в 3 дня'
            elif settings.periodicity == 'everyday_4':
                settings_periodicity = 'раз в 4 дня'
            else:
                settings_periodicity = 'неуказано'

            on_off = '🟩 Включено' if settings.on_of_auto else '🟥 Выключено'
            formatted_time = settings.send_time.strftime("%H:%M") if settings.send_time else "Не задано"
            await message.answer(
                        f'*Текущие параметры письма:*\n\n'
                        f'*📋 Заголовок письма:* '
                        f'{f'\n{format_as_quote(settings.subject)}\n' if settings.subject and settings.subject != "Без темы" else "__не задано__"}\n\n'
                        f'*📄 Текст письма:* '
                        f'{f'\n{format_as_quote(settings.message)}\n' if settings.message and settings.message != "Без текста" else "__не задано__"}\n\n'
                        f'*🗓 Периодичность отправки:* {settings_periodicity}\n\n'
                        f'*⏰ Время отправки:* {formatted_time if formatted_time else "Не задано"}\n\n'
                        f'*🔉 Количество аудио в одном письме:* {settings.quantity_beat}\n'
                        f'{f'\n*↔️ Интервал:* {'без интервала' if settings.interval == 0 or settings.interval == "none" else f'{settings.interval} минута' if settings.interval in [1] else f'{settings.interval} минуты' if settings.interval in [2, 3, 4] else f'{settings.interval} минут'}\n———\n\n' if user.subscription not in ['free','Неуказано','не указано'] else '———\n\n'}'
                        f'*⚙️ Выберите настройки которые хотите поменять по кнопкам ниже:*',
                        reply_markup=kb.settings_button(on_off, user.subscription, one_on_off),
                        parse_mode='MarkdownV2', disable_web_page_preview=True
                    )
def format_as_quote(text: str) -> str:
    lines = text.splitlines()
    escaped_lines = [
        '> ' + line
        .replace('\\', '\\\\')
        .replace('_', '\\_')
        .replace('*', '\\*')
        .replace('[', '\\[')
        .replace(']', '\\]')
        .replace('(', '\\(')
        .replace(')', '\\)')
        .replace('~', '\\~')
        .replace('`', '\\`')
        .replace('>', '\\>')
        .replace('#', '\\#')
        .replace('+', '\\+')
        .replace('-', '\\-')
        .replace('=', '\\=')
        .replace('|', '\\|')
        .replace('{', '\\{')
        .replace('}', '\\}')
        .replace('.', '\\.')
        .replace('!', '\\!')
        for line in lines
    ]
    return '\n'.join(escaped_lines)


@rt.callback_query(F.data == 'letter_header') 
async def letter_header(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:

            if user.language == 2:
                await callback.answer('📋 Email subject')
                await callback.message.edit_text('<strong>Enter the email subject</strong>',
                                                 reply_markup=kb.letter_title_eng, parse_mode='HTML')
            else:
                await callback.answer('📋 Заголовок письма')
                await callback.message.edit_text('<strong>Напишите заголовок письма</strong>',
                                                 reply_markup=kb.letter_title, parse_mode='HTML')
            await state.set_state(GroupState.editing_subject)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(GroupState.editing_subject)
async def process_letter_header(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await message.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                async with async_session() as session:
                    active_group = await session.scalar(
                        select(Group).filter(Group.user_id == message.from_user.id, Group.active == True))
                    result = await session.execute(select(Settings).where(Settings.group_id == active_group.id))
                    settings = result.scalars().first()

                    if settings:
                        settings.subject = message.text
                        await session.commit()
                        if user.language == 2:
                            await message.answer(f'<strong>✅ Email subject updated</strong>',
                                                 parse_mode='HTML', disable_web_page_preview=True)
                        else:
                            await message.answer(f'<strong>✅ Заголовок письма обновлен</strong>',
                                                 parse_mode='HTML', disable_web_page_preview=True)
                    else:
                        if user.language == 2:
                            await message.answer('Error. Settings not found.')
                        else:
                            await message.answer('Ошибка: Настройки не найдены.')

                await send_settings_message(message.from_user.id, message)
                await state.clear()

@rt.callback_query(F.data == 'letter_text') 
async def letter_text(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('📄 Email body')
                await callback.message.edit_text('<strong>Enter the email body</strong>', reply_markup=kb.letter_text_eng,
                                                 parse_mode='HTML')
            else:
                await callback.answer('📄 Текст письма')
                await callback.message.edit_text('<strong>Напишите текст письма</strong>', reply_markup=kb.letter_text,
                                                 parse_mode='HTML')
            await state.set_state(GroupState.editing_message)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(GroupState.editing_message)
async def process_letter_text(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await message.delete() 
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                async with async_session() as session:
                    active_group = await session.scalar(
                        select(Group).filter(Group.user_id == message.from_user.id, Group.active == True))
                    result = await session.execute(select(Settings).where(Settings.group_id == active_group.id))
                    settings = result.scalars().first()

                    if settings:
                        settings.message = message.text
                        await session.commit()
                        if user.language == 2:
                            await message.answer('<strong>✅ Email body updated</strong>', parse_mode='HTML')
                        else:
                            await message.answer('<strong>✅ Текст письма обновлен</strong>', parse_mode='HTML')
                    else:
                        if user.language == 2:
                            await message.answer('Error: Settings not found.')
                        else:
                            await message.answer('Ошибка: Настройки не найдены.')

                await send_settings_message(message.from_user.id, message)
                await state.clear()

@rt.callback_query(F.data == 'dispatch_frequency') 
async def dispatch_frequency(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('🗓 Sending frequency')
                await callback.message.edit_text(
                    '<strong>Choose the sending frequency using the buttons below:</strong>',
                    reply_markup=kb.dispatch_frequency_eng, parse_mode='HTML')
            else:
                await callback.answer('🗓 Периодичность отправки')
                await callback.message.edit_text('<strong>Выберите периодичность отправки писем по кнопкам ниже:</strong>',
                                                 reply_markup=kb.dispatch_frequency, parse_mode='HTML')
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data.in_(['everyday', 'everyday_2', 'everyday_3', 'everyday_4']))
async def dispatch_frequency_buttons(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            dispatch = callback.data 
            if user.language == 2:
                if dispatch == 'everyday':
                    dispatch_answer = 'daily'
                elif dispatch == 'everyday_2':
                    dispatch_answer = 'every 2 days '
                elif dispatch == 'everyday_3':
                    dispatch_answer = 'every 3 days '
                elif dispatch == 'everyday_4':
                    dispatch_answer = 'every 4 days '
                else:
                    dispatch_answer = 'not set'
                async with async_session() as session:
                    user_groups = await session.scalars(select(Group.id).filter(Group.user_id == callback.from_user.id))
                    group_ids = user_groups.all()

                    if not group_ids:
                        await callback.answer('Error: Groups not found')
                        return

                    await session.execute(
                        update(Settings).where(Settings.group_id.in_(group_ids)).values(periodicity=dispatch)
                    )
                    await session.commit()

                    await callback.answer(
                        f'✅ Sending frequency: {dispatch_answer if user.subscription == "free" else f"{dispatch_answer} (for all groups)"}',
                        show_alert=True)

            else:
                if dispatch == 'everyday':
                    dispatch_answer = 'ежедневно'
                elif dispatch == 'everyday_2':
                    dispatch_answer = 'раз в 2 дня'
                elif dispatch == 'everyday_3':
                    dispatch_answer = 'раз в 3 дня'
                elif dispatch == 'everyday_4':
                    dispatch_answer = 'раз в 4 дня'
                else:
                    dispatch_answer = 'неуказано'
                async with async_session() as session:
                    user_groups = await session.scalars(select(Group.id).filter(Group.user_id == callback.from_user.id))
                    group_ids = user_groups.all()

                    if not group_ids:
                        await callback.answer('Ошибка: Группы не найдены.')
                        return

                    await session.execute(
                        update(Settings).where(Settings.group_id.in_(group_ids)).values(periodicity=dispatch)
                    )
                    await session.commit()

                    await callback.answer(f'✅ Периодичность отправки: {dispatch_answer if user.subscription == "free" else f"{dispatch_answer} (для всех групп)"}', show_alert=True)

            await setting(callback)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)

@rt.callback_query(F.data == 'dispatch_time') 
async def dispatch_time(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('⏰ Sending time')
                await callback.message.edit_text('<strong>Choose the sending time using the buttons below:</strong>',
                                                 reply_markup=kb.dispatch_time_eng, parse_mode='HTML')
            else:
                await callback.answer('⏰ Время отправки')
                await callback.message.edit_text('<strong>Выберите время отправки писем по кнопкам ниже:</strong>',
                                                 reply_markup=kb.dispatch_time, parse_mode='HTML')
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data.in_(['19pm', '20pm', '21pm', '22pm']))
async def dispatch_time_buttons(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            send_hour = int(callback.data.replace("pm", ""))
            send_time = datetime.combine(date.today(), time(send_hour, 0))

            async with async_session() as session:
                user_groups = await session.scalars(select(Group.id).filter(Group.user_id == callback.from_user.id))
                group_ids = user_groups.all()

                if not group_ids:
                    if user.language == 2:
                        await callback.answer('Error: Groups not found')
                    else:
                        await callback.answer('Ошибка: Группы не найдены.')
                    return

                await session.execute(
                    update(Settings).where(Settings.group_id.in_(group_ids)).values(send_time=send_time)
                )
                await session.execute(
                    update(OneTimeSettings).where(OneTimeSettings.group_id.in_(group_ids)).values(send_time=send_time)
                )
                await session.commit()
                if user.language == 2:
                    await callback.answer(
                        f'✅ Sending time: {send_time.strftime("%H:%M") if user.subscription == "free" else f"{send_time.strftime("%H:%M")}"}',
                        show_alert=True)
                else:
                    await callback.answer(f'✅ Время отправки: {send_time.strftime("%H:%M") if user.subscription == "free" else f"{send_time.strftime("%H:%M")} (для всех групп)"}',
                                                      show_alert=True)

            await setting(callback)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'main_time_choise')
async def main_time_choise(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.message.edit_text('<strong>Enter the sending time (in HH:MM format) — Moscow time (UTC+3)</strong>',
                                                 parse_mode="HTML", reply_markup=kb.back_to_dispatch_time_eng)
            else:
                await callback.message.edit_text('<strong>Введите время отправки писем (в формате HH:MM)</strong>', parse_mode="HTML", reply_markup=kb.back_to_dispatch_time)
            await state.set_state(UserState.waiting_for_main_time_choise)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(UserState.waiting_for_main_time_choise)
async def handle_main_time_input(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await message.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                input_text = message.text.strip().replace(' ', '').replace(':', '')

                if not re.fullmatch(r'\d{4}', input_text):
                    if user.language == 2:
                        await message.answer('<strong>❗Invalid format</strong>', parse_mode='HTML')
                    else:
                        await message.answer('<strong>❗️Неверный формат</strong>', parse_mode='HTML')
                    return

                try:
                    hour = int(input_text[:2])
                    minute = int(input_text[2:])

                    if not (0 <= hour < 24 and 0 <= minute < 60):
                        raise ValueError

                    send_time = datetime.combine(date.today(), time(hour, minute))

                    async with async_session() as session:
                        result = await session.execute(select(User).filter(User.user_id == message.from_user.id))
                        user = result.scalar_one_or_none()

                        if user and not user.block:
                            user_groups = await session.scalars(select(Group.id).filter(Group.user_id == user.user_id))
                            group_ids = user_groups.all()

                            if not group_ids:
                                await message.answer('Ошибка: Группы не найдены.')
                                return

                            await session.execute(
                                update(Settings).where(Settings.group_id.in_(group_ids)).values(send_time=send_time)
                            )
                            await session.execute(
                                update(OneTimeSettings).where(OneTimeSettings.group_id.in_(group_ids)).values(send_time=send_time)
                            )



                            if user.language == 2:
                                await message.answer(
                                    f'✅ <strong>Sending time: {send_time.strftime("%H:%M")}</strong>',
                                    parse_mode='HTML')
                            else:
                                await message.answer(f'✅ <strong>Время отправки: {send_time.strftime("%H:%M")} (для всех групп)</strong>', parse_mode='HTML')
                            await session.commit()
                        else:
                            await message.answer('⛔️ Пользователь не найден или заблокирован.')
                    await state.clear()
                    await send_settings_message(message.from_user.id, message)

                except ValueError:
                    if user.language == 2:
                        await message.answer('<strong>❗️Invalid format</strong>', parse_mode='HTML')
                    else:
                        await message.answer('<strong>❗️Неверный формат</strong>', parse_mode='HTML')

@rt.callback_query(F.data == 'audio_quantity')
async def audio_quantity(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('🔉 Number of audio files')
                await callback.message.edit_text(
                    '<strong>Choose the number of audio files per email using the buttons below:</strong>',
                    reply_markup=kb.audio_quantity_eng, parse_mode='HTML')
            else:
                await callback.answer('🔉 Количество аудио')
                await callback.message.edit_text('<strong>Выберите количество аудио в одном письме по кнопкам ниже:</strong>',
                                                 reply_markup=kb.audio_quantity, parse_mode='HTML')
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data.in_(['two', 'three', 'four', 'five']))
async def audio_quantity(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if callback.data == 'two':
                quantity = '2'
            elif callback.data == 'three':
                quantity = '3'
            elif callback.data == 'four':
                quantity = '4'
            else:
                quantity = '5'
            async with async_session() as session:
                active_group = await session.scalar(
                    select(Group).filter(Group.user_id == callback.from_user.id, Group.active == True))
                result = await session.execute(select(Settings).where(Settings.group_id == active_group.id))
                settings = result.scalars().first()

                if settings:
                    settings.quantity_beat = int(quantity)
                    await session.commit()
                    await callback.answer(f'✅ Number of audio files per email: {quantity}', show_alert=True)
                else:
                    await callback.answer('Ошибка: Настройки не найдены.')

            await setting(callback)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)

@rt.callback_query(F.data == 'on_off_data')
async def on_off_data(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            async with async_session() as session:
                active_group = await session.scalar(
                    select(Group).filter(Group.user_id == callback.from_user.id, Group.active == True))
                result = await session.execute(select(Settings).where(Settings.group_id == active_group.id))
                settings = result.scalars().first()

                if settings:
                    one_on_off = False
                    result = await session.execute(select(Settings).where(Settings.group_id == active_group.id))
                    settings = result.scalars().first()
                    one_active_group = await session.scalar(
                        select(Group).filter(Group.user_id == callback.from_user.id, Group.active == True))
                    one_result = await session.execute(
                        select(OneTimeSettings).where(OneTimeSettings.group_id == one_active_group.id))
                    one_settings = one_result.scalars().first()
                    if settings.on_of_auto and one_settings:
                        if one_settings.on_of_auto:

                            if user.language == 2:
                                await callback.answer(
                                    '❗️You can’t stop mailing for this group while a one-time email is active',
                                    show_alert=True)
                            else:
                                await callback.answer('❗️Нельзя остановить рассылку для этой группы, пока активно разовое письмо', show_alert=True)
                            return
                    settings.on_of_auto = not settings.on_of_auto
                    if one_settings:
                        one_on_off = one_settings.on_of_auto

                    if user.language == 2:
                        on_off = '🟩 Active' if settings.on_of_auto else '🟥 Disabled'
                        await callback.message.edit_reply_markup(
                            reply_markup=kb.settings_button_eng(on_off, user.subscription, one_on_off))
                        await callback.answer(
                            f'{"🟩 Auto mailing is active" if settings.on_of_auto else "🟥 Auto mailing is disabled"}')
                    else:
                        on_off = '🟩 Включено' if settings.on_of_auto else '🟥 Выключено'
                        await callback.message.edit_reply_markup(reply_markup=kb.settings_button(on_off, user.subscription, one_on_off))
                        await callback.answer(f'{"🟩 Авторассылка включена" if settings.on_of_auto else "🟥 Авторассылка выключена"}')
                else:
                    await callback.answer('Ошибка: Настройки не найдены.')
                await session.commit()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)

@rt.callback_query(F.data == 'pack_interval')
async def pack_interval(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('↔️ Interval')
                await callback.message.edit_text(
                    '<strong>Enter the interval (in minutes)</strong>',
                    reply_markup=kb.pack_interval_eng, parse_mode='HTML')
            else:
                await callback.answer('↔️ Интервал')
                await callback.message.edit_text(
                    '<strong>Введите интервал (в минутах)</strong>',
                    reply_markup=kb.pack_interval, parse_mode='HTML')
            await state.set_state(UserState.waiting_for_interval)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'no_interval')
async def pack_interval_call(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            quantity = 0
            async with async_session() as session:
                result = await session.execute(select(Settings).where(Settings.user_id == user_id))
                settings = result.scalars().all()

                if settings:
                    for sett in settings:
                        sett.interval = int(quantity)
                    await session.commit()
                    if user.language == 2:
                        if quantity == 0:
                            await callback.answer('✅ Interval updated (for all groups)', show_alert=True)
                        else:
                            await callback.answer(f'✅ Interval updated (for all groups)', show_alert=True)
                    else:
                        if quantity == 0:
                            await callback.answer('✅ Интервал обновлен (для всех групп)', show_alert=True)
                        else:
                            await callback.answer(f'✅ Интервал обновлен (для всех групп)', show_alert=True)
                else:
                    await callback.answer('Ошибка: Настройки не найдены.')

            await setting(callback)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(UserState.waiting_for_interval)
async def process_interval(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await message.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                async with async_session() as session:
                    result = await session.execute(select(Settings).where(Settings.user_id == user_id))
                    settings = result.scalars().all()
                    result = await session.execute(select(OneTimeSettings).where(OneTimeSettings.user_id == user_id))
                    one_settings = result.scalars().all()

                    if settings:

                        if user.language == 2:
                            try:
                                interval = int(message.text)
                                if interval <= 240:
                                    for sett in settings:
                                        sett.interval = interval
                                    for one_sett in one_settings:
                                        one_sett.interval = interval
                                    await session.commit()
                                    await message.answer('<strong>Interval updated</strong> (for all groups)', parse_mode='HTML')
                                else:
                                    await message.answer('<strong>❗️Interval cannot be greater than 240 minutes</strong>',
                                                         parse_mode='HTML', reply_markup=kb.for_what_eng)
                                    return
                            except ValueError:
                                await message.answer('<strong>❗️Enter a valid value</strong>',
                                                     parse_mode='HTML', reply_markup=kb.for_what_eng)
                                return
                        else:
                            try:
                                interval = int(message.text)
                                if interval <= 240:
                                    for sett in settings:
                                        sett.interval = interval
                                    for one_sett in one_settings:
                                        one_sett.interval = interval
                                    await session.commit()
                                    await message.answer('<strong>✅ Интервал обновлен</strong> (для всех групп)', parse_mode='HTML')
                                else:
                                    await message.answer('<strong>❗️Интервал не может быть больше 240 минут</strong>',
                                                         parse_mode='HTML', reply_markup=kb.for_what)
                                    return
                            except ValueError:
                                await message.answer('<strong>❗️Введите корректное значение</strong>',
                                                     parse_mode='HTML', reply_markup=kb.for_what)
                                return
                    else:
                        await message.answer('Ошибка: Настройки не найдены.')

                await send_settings_message(message.from_user.id, message)
                await state.clear()


@rt.callback_query(F.data == 'without_title')
async def without_title(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            async with async_session() as session:
                active_group = await session.scalar(
                    select(Group).filter(Group.user_id == user_id, Group.active == True)
                )
                if not active_group:
                    await callback.answer("Ошибка: активная группа не найдена.", show_alert=True)
                    return

                settings = await session.scalar(select(Settings).where(Settings.group_id == active_group.id))
                if settings:
                    settings.subject = 'Без темы'
                    if user.language == 2:
                        await callback.answer('✅ Email subject updated', show_alert=True)
                    else:
                        await callback.answer('✅ Заголовок письма обновлен', show_alert=True)
                    await session.commit()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)

    await setting(callback)
@rt.callback_query(F.data == 'without_text')
async def without_text(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            async with async_session() as session:
                active_group = await session.scalar(
                    select(Group).filter(Group.user_id == user_id, Group.active == True)
                )
                if not active_group:
                    await callback.answer("Ошибка: активная группа не найдена.", show_alert=True)
                    return

                settings = await session.scalar(select(Settings).where(Settings.group_id == active_group.id))
                if settings:
                    settings.message = 'Без текста'
                    if user.language == 2:
                        await callback.answer('✅ Email body updated', show_alert=True)
                    else:
                        await callback.answer('✅ Текст письма обновлен', show_alert=True)
                    await session.commit()

            await setting(callback)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)

#разовая отправка
@rt.callback_query(F.data == 'one_time_message')
async def one_time_message_settings(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('⚙️ Settings')
            else:
                await callback.answer('⚙️ Настройки')
            async with async_session() as session:
                active_group = await session.scalar(
                    select(Group).filter(Group.user_id == user_id, Group.active == True))
            async with async_session() as session:
                result = await session.execute(select(Settings).where(Settings.group_id == active_group.id))
                settings_main = result.scalars().first()
            async with async_session() as session:
                result = await session.execute(select(OneTimeSettings).where(OneTimeSettings.group_id == active_group.id))
                settings = result.scalars().first()

                if not settings:
                    settings = OneTimeSettings(
                        group_id=active_group.id,
                        send_time=settings_main.send_time,
                        quantity_beat=False,
                        user_id = user_id,
                        interval=settings_main.interval
                    )
                    session.add(settings)

                if user.language == 2:
                    quantity_on_off = '🟢🔇 No audio' if settings.quantity_beat else '🔇 No audio'
                    on_off = '🟩 Active' if settings.on_of_auto else '🟥 Disabled'
                    formatted_time = settings.send_time.strftime("%H:%M") if settings.send_time else "unspecified"
                    await callback.message.edit_text(
                        f'*Current one\\-time email settings:*\n\n'
                        f'*📋 Email subject:* '
                        f'{f'\n{format_as_quote(settings.subject)}\n' if settings.subject and settings.subject != "Без темы" else "__not set__"}\n\n'
                        f'*📄 Email body:* '
                        f'{f'\n{format_as_quote(settings.message)}\n' if settings.message and settings.message != "Без текста" else "__not set__"}\n\n'
                        f'*⏰ Scheduled time:* {formatted_time if formatted_time else "Not set"}\n\n'
                        f'*⚙️ Choose the settings you want to change using the buttons below:*',
                        reply_markup=kb.one_time_settings_button_eng(on_off, quantity_on_off),
                        parse_mode='MarkdownV2', disable_web_page_preview=True
                    )
                else:
                    quantity_on_off = '🟢🔇 Без аудио' if settings.quantity_beat else '🔇 Без аудио'
                    on_off = '🟩 Включено' if settings.on_of_auto else '🟥 Выключено'
                    formatted_time = settings.send_time.strftime("%H:%M") if settings.send_time else "Не задано"
                    await callback.message.edit_text(
                        f'*Текущие параметры разового письма:*\n\n'
                        f'*📋 Заголовок письма:* '
                        f'{f'\n{format_as_quote(settings.subject)}\n' if settings.subject and settings.subject != "Без темы" else "__не задано__"}\n\n'
                        f'*📄 Текст письма:* '
                        f'{f'\n{format_as_quote(settings.message)}\n' if settings.message and settings.message != "Без текста" else "__не задано__"}\n\n'
                        f'*⏰ Время отправки:* {formatted_time if formatted_time else "Не задано"}\n\n'
                        f'*⚙️ Выберите настройки которые хотите поменять по кнопкам ниже:*',
                        reply_markup=kb.one_time_settings_button(on_off, quantity_on_off),
                        parse_mode='MarkdownV2', disable_web_page_preview=True
                    )

                await session.commit()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
async def send_one_time_message_settings(user_id: int, message: Message):
    async with async_session() as session:
        active_group = await session.scalar(
            select(Group).filter(Group.user_id == user_id, Group.active == True))
        result = await session.execute(select(Settings).where(Settings.group_id == active_group.id))
        settings_main = result.scalars().first()
        result = await session.execute(select(OneTimeSettings).where(OneTimeSettings.group_id == active_group.id))
        settings = result.scalars().first()
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if not settings:
            settings = OneTimeSettings(
                group_id=active_group.id,
                send_time=settings_main.send_time,
                quantity_beat=False,
                interval=settings_main.interval,
                user_id = user_id
            )
            session.add(settings)

        if user.language == 2:
            quantity_on_off = '🟢🔇 No audio' if settings.quantity_beat else '🔇 No audio'
            on_off = '🟩 Active' if settings.on_of_auto else '🟥 Disabled'
            formatted_time = settings.send_time.strftime("%H:%M") if settings.send_time else "unspecified"

            await message.answer(
                f'*Current one\\-time email settings:*\n\n'
                f'*📋 Email subject:* '
                f'{f'\n{format_as_quote(settings.subject)}\n' if settings.subject and settings.subject != "Без темы" else "__not set__"}\n\n'
                f'*📄 Email body:* '
                f'{f'\n{format_as_quote(settings.message)}\n' if settings.message and settings.message != "Без текста" else "__not set__"}\n\n'
                f'*⏰ Scheduled time:* {formatted_time if formatted_time else "Not set"}\n\n'
                f'*⚙️ Choose the settings you want to change using the buttons below:*',
                reply_markup=kb.one_time_settings_button_eng(on_off, quantity_on_off),
                parse_mode='MarkdownV2', disable_web_page_preview=True
            )

        else:
            quantity_on_off = '🟢🔇 Без аудио' if settings.quantity_beat else '🔇 Без аудио'
            on_off = '🟩 Включено' if settings.on_of_auto else '🟥 Выключено'
            formatted_time = settings.send_time.strftime("%H:%M") if settings.send_time else "Не задано"

            await message.answer(
                        f'*Текущие параметры разового письма:*\n\n'
                        f'*📋 Заголовок письма:* '
                        f'{f'\n{format_as_quote(settings.subject)}\n' if settings.subject and settings.subject != "Без темы" else "__не задано__"}\n\n'
                        f'*📄 Текст письма:* '
                        f'{f'\n{format_as_quote(settings.message)}\n' if settings.message and settings.message != "Без текста" else "__не задано__"}\n\n'
                        f'*⏰ Время отправки:* {formatted_time if formatted_time else "Не задано"}\n\n'
                        f'*⚙️ Выберите настройки которые хотите поменять по кнопкам ниже:*',
                        reply_markup=kb.one_time_settings_button(on_off, quantity_on_off),
                        parse_mode='MarkdownV2', disable_web_page_preview=True
                    )

@rt.callback_query(F.data == 'back_to_one_time_settings')
async def back_to_one_time_settings(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('↩️ Back')
            else:
                await callback.answer('↩️ Назад')
            await one_time_message_settings(callback)
            await state.clear()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'back_to_one_time_interval')
async def back_to_one_time_interval(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('↩️ Back')
            else:
                await callback.answer('↩️ Назад')
            await one_pack_interval(callback)
            await state.clear()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'back_to_onetime_time')
async def back_to_onetime_time(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('↩️ Back')
            else:
                await callback.answer('↩️ Назад')
            await one_time_time(callback, state)
            await state.clear()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)

@rt.callback_query(F.data == 'one_time_subject') 
async def one_time_subject(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('📋 Email subject')
                await callback.message.edit_text('<strong>Enter the email subject</strong>',
                                                 reply_markup=kb.one_time_letter_title_eng, parse_mode='HTML')
            else:
                await callback.answer('📋 Заголовок письма')
                await callback.message.edit_text('<strong>Напишите заголовок письма</strong>',
                                                 reply_markup=kb.one_time_letter_title, parse_mode='HTML')
            await state.set_state(GroupState.editing_one_time_subject)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(GroupState.editing_one_time_subject)
async def process_one_time_subject(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await message.delete() 
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                async with async_session() as session:
                    active_group = await session.scalar(
                        select(Group).filter(Group.user_id == message.from_user.id, Group.active == True))
                    result = await session.execute(select(OneTimeSettings).where(OneTimeSettings.group_id == active_group.id))
                    settings = result.scalars().first()

                    if settings:
                        settings.subject = message.text
                        await session.commit()
                        if user.language == 2:
                            await message.answer(f'<strong>✅ Email subject updated</strong>',
                                                 parse_mode='HTML', disable_web_page_preview=True)
                        else:
                            await message.answer(f'<strong>✅ Заголовок письма обновлен</strong>',
                                                parse_mode='HTML', disable_web_page_preview=True)
                    else:
                        await message.answer('Ошибка: Настройки не найдены.')

                await send_one_time_message_settings(message.from_user.id, message)
                await state.clear()

@rt.callback_query(F.data == 'one_time_message_text') 
async def one_time_message(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('📄 Email body')
                await callback.message.edit_text('<strong>Enter the email body</strong>',
                                                 reply_markup=kb.one_time_letter_text_eng,
                                                 parse_mode='HTML')
            else:
                await callback.answer('📄 Текст письма')
                await callback.message.edit_text('<strong>Напишите текст письма</strong>', reply_markup=kb.one_time_letter_text,
                                                 parse_mode='HTML')
            await state.set_state(GroupState.editing_one_time_message)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(GroupState.editing_one_time_message)
async def process_one_time_message(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await message.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                async with async_session() as session:
                    active_group = await session.scalar(
                        select(Group).filter(Group.user_id == message.from_user.id, Group.active == True))
                    result = await session.execute(select(OneTimeSettings).where(OneTimeSettings.group_id == active_group.id))
                    settings = result.scalars().first()

                    if settings:
                        settings.message = message.text
                        await session.commit()
                        if user.language == 2:
                            await message.answer('<strong>✅ Email body updated</strong>', parse_mode='HTML')
                        else:
                            await message.answer('<strong>✅ Текст письма обновлен</strong>', parse_mode='HTML')
                    else:
                        await message.answer('Ошибка: Настройки не найдены.')

                await send_one_time_message_settings(message.from_user.id, message)
                await state.clear()


@rt.callback_query(F.data == 'one_time_time')
async def one_time_time(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('⏰ Sending time')
                await callback.message.edit_text('<strong>Choose the sending time using the buttons below:</strong>',
                                                 reply_markup=kb.one_time_dispatch_time_eng, parse_mode='HTML')
            else:
                await callback.answer('⏰ Время отправки')
                await callback.message.edit_text('<strong>Выберите время отправки писем по кнопкам ниже:</strong>',
                                                 reply_markup=kb.one_time_dispatch_time, parse_mode='HTML')
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data.in_(['onetime_19pm', 'onetime_20pm', 'onetime_21pm', 'onetime_22pm']))
async def dispatch_one_time_time(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            send_hour = int(callback.data.replace("pm", "").replace("onetime_", ""))
            send_time = datetime.combine(date.today(), time(send_hour, 0))

            async with async_session() as session:
                user_groups = await session.scalars(select(Group.id).filter(Group.user_id == callback.from_user.id))
                group_ids = user_groups.all()

                if not group_ids:
                    await callback.answer('Ошибка: Группы не найдены.')
                    return

                await session.execute(
                    update(Settings).where(Settings.group_id.in_(group_ids)).values(send_time=send_time)
                )
                await session.execute(
                    update(OneTimeSettings).where(OneTimeSettings.group_id.in_(group_ids)).values(send_time=send_time)
                )
                await session.commit()
                if user.language == 2:
                    await callback.answer(
                        f'✅ Sending time: {send_time.strftime("%H:%M") if user.subscription == "free" else f"{send_time.strftime("%H:%M")}"}',
                        show_alert=True)
                else:
                    await callback.answer(f'✅ Время отправки: {send_time.strftime("%H:%M") if user.subscription == "free" else f"{send_time.strftime("%H:%M")} (для всех групп)"}',
                                                  show_alert=True)

            await one_time_message_settings(callback)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'onetime_choise')
async def onetime_choise(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.message.edit_text('<strong>Enter the sending time (in HH:MM format) — Moscow time (UTC+3)</strong>',
                                                 parse_mode="HTML", reply_markup=kb.back_to_onetime_time_eng)
            else:
                await callback.message.edit_text('<strong>Введите время отправки писем (в формате HH:MM)</strong>', parse_mode="HTML", reply_markup=kb.back_to_onetime_time)
            await state.set_state(UserState.waiting_for_onetime_choise)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(UserState.waiting_for_onetime_choise)
async def handle_main_time_input(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block: 
                try:
                    await message.delete() 
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                input_text = message.text.strip().replace(' ', '').replace(':', '')

                if not re.fullmatch(r'\d{4}', input_text):
                    if user.language == 2:
                        await message.answer('<strong>❗️Invalid format</strong>', parse_mode='HTML')
                    else:
                        await message.answer('<strong>❗️Неверный формат</strong>', parse_mode='HTML')
                    return

                try:
                    hour = int(input_text[:2])
                    minute = int(input_text[2:])

                    if not (0 <= hour < 24 and 0 <= minute < 60):
                        raise ValueError

                    send_time = datetime.combine(date.today(), time(hour, minute))

                    async with async_session() as session:
                        result = await session.execute(select(User).filter(User.user_id == message.from_user.id))
                        user = result.scalar_one_or_none()

                        if user and not user.block:
                            user_groups = await session.scalars(select(Group.id).filter(Group.user_id == user.user_id))
                            group_ids = user_groups.all()

                            if not group_ids:
                                await message.answer('Ошибка: Группы не найдены.')
                                return

                            await session.execute(
                                update(Settings).where(Settings.group_id.in_(group_ids)).values(send_time=send_time)
                            )
                            await session.execute(
                                update(OneTimeSettings).where(OneTimeSettings.group_id.in_(group_ids)).values(send_time=send_time)
                            )


                            if user.language == 2:
                                await message.answer(
                                    f'✅ <strong>Sending time: {send_time.strftime("%H:%M")}</strong>',
                                    parse_mode='HTML')
                            else:
                                await message.answer(f'✅ <strong>Время отправки: {send_time.strftime("%H:%M")} (для всех групп)</strong>', parse_mode='HTML')
                            await session.commit()
                        else:
                            await message.answer('⛔️ Пользователь не найден или заблокирован.')

                    await send_one_time_message_settings(message.from_user.id, message)
                    await state.clear()

                except ValueError:
                    if user.language == 2:
                        await message.answer('<strong>❗️Invalid format</strong>', parse_mode='HTML')
                    else:
                        await message.answer('<strong>❗️Неверный формат</strong>', parse_mode='HTML')

@rt.callback_query(F.data == 'one_time_quantity') 
async def one_time_quantity(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            async with async_session() as session:
                active_group = await session.scalar(
                    select(Group).filter(Group.user_id == callback.from_user.id, Group.active == True))
                result = await session.execute(select(OneTimeSettings).where(OneTimeSettings.group_id == active_group.id))
                settings = result.scalars().first()

                if user.language == 2:
                    if settings:
                        settings.quantity_beat = not settings.quantity_beat
                        on_off = '🟩 Active' if settings.on_of_auto else '🟥 Disabled'
                        quantity_on_off = '🟢🔇 No audio' if settings.quantity_beat else '🔇 No audio'
                        await callback.message.edit_reply_markup(
                            reply_markup=kb.one_time_settings_button_eng(on_off, quantity_on_off))
                        if settings.quantity_beat:
                            await callback.answer('✅ The next mailing will have no audio', show_alert=True)
                    else:
                        await callback.answer('Error: Settings not found.')

                else:
                    if settings:
                        settings.quantity_beat = not settings.quantity_beat
                        on_off = '🟩 Включено' if settings.on_of_auto else '🟥 Выключено'
                        quantity_on_off = '🟢🔇 Без аудио' if settings.quantity_beat else '🔇 Без аудио'
                        await callback.message.edit_reply_markup(reply_markup=kb.one_time_settings_button(on_off, quantity_on_off))
                        if settings.quantity_beat:
                            await callback.answer('✅ В следующей рассылке не будет аудио', show_alert=True)
                    else:
                        await callback.answer('Ошибка: Настройки не найдены.')
                await session.commit()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data.in_(['onetime_two', 'onetime_three', 'onetime_four', 'onetime_five', 'one_time_without_beat']))
async def process_one_time_quantity(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if callback.data == 'one_time_without_beat':
                quantity = '0'
            elif callback.data == 'onetime_two':
                quantity = '2'
            elif callback.data == 'onetime_three':
                quantity = '3'
            elif callback.data == 'onetime_four':
                quantity = '4'
            else:
                quantity = '5'
            async with async_session() as session:
                active_group = await session.scalar(
                    select(Group).filter(Group.user_id == callback.from_user.id, Group.active == True))
                result = await session.execute(select(OneTimeSettings).where(OneTimeSettings.group_id == active_group.id))
                settings = result.scalars().first()

                if settings:
                    settings.quantity_beat = int(quantity)
                    await session.commit()
                    if user.language == 2:
                        await callback.answer(f'✅ Number of audio files per email: {quantity}', show_alert=True)
                    else:
                        await callback.answer(f'✅ Количество аудио в одном письме: {quantity}', show_alert=True)
                else:
                    await callback.answer('Ошибка: Настройки не найдены.')

            await one_time_message_settings(callback)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)

@rt.callback_query(F.data == 'one_time_toggle')
async def one_time_toggle(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            async with async_session() as session:
                active_group = await session.scalar(
                    select(Group).filter(Group.user_id == callback.from_user.id, Group.active == True))
                result = await session.execute(select(OneTimeSettings).where(OneTimeSettings.group_id == active_group.id))
                settings = result.scalars().first()
                result = await session.execute(
                    select(Settings).where(Settings.group_id == active_group.id))
                normal_settings = result.scalars().first()
                if user.language == 2:
                    if settings:
                        settings.on_of_auto = not settings.on_of_auto
                        if settings.on_of_auto:
                            normal_settings.on_of_auto = True
                        quantity_on_off = '🟢🔇 No audio' if settings.quantity_beat else '🔇 No audio'
                        on_off = '🟩 Active' if settings.on_of_auto else '🟥 Disabled'
                        if user.language == 2:
                            await callback.message.edit_reply_markup(
                                reply_markup=kb.one_time_settings_button_eng(on_off, quantity_on_off))
                        else:
                            await callback.message.edit_reply_markup(
                                reply_markup=kb.one_time_settings_button(on_off, quantity_on_off))
                        await callback.answer(
                            f'{"🟩 One-time mailing is active" if settings.on_of_auto else "🟥 One-time mailing is disabled"}')
                    else:
                        await callback.answer('Error: Settings not found.')

                else:
                    if settings:
                        settings.on_of_auto = not settings.on_of_auto
                        if settings.on_of_auto:
                            normal_settings.on_of_auto = True
                        quantity_on_off = '🟢🔇 Без аудио' if settings.quantity_beat else '🔇 Без аудио'
                        on_off = '🟩 Включено' if settings.on_of_auto else '🟥 Выключено'
                        await callback.message.edit_reply_markup(reply_markup=kb.one_time_settings_button(on_off, quantity_on_off))
                        await callback.answer(f'{"🟩 Разовая авторассылка включена" if settings.on_of_auto else "🟥 Разовая авторассылка выключена"}')
                    else:
                        await callback.answer('Ошибка: Настройки не найдены.')
                await session.commit()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)

@rt.callback_query(F.data == 'one_time_interval')
async def one_pack_interval(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await callback.answer('↔️ Interval')
                await callback.message.edit_text(
                    '<strong>Enter the interval (in minutes)</strong>',
                    reply_markup=kb.pack_interval_one_time_eng, parse_mode='HTML')
            else:
                await callback.answer('↔️ Интервал')
                await callback.message.edit_text(
                    '<strong>Введите интервал (в минутах)</strong>',
                    reply_markup=kb.pack_interval_one_time, parse_mode='HTML')
            await state.set_state(UserState.waiting_for_one_time_interval)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'one_no_interval')
async def pack_interval_call(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            quantity = '0'
            async with async_session() as session:
                result = await session.execute(select(OneTimeSettings).where(OneTimeSettings.user_id == user_id))
                settings = result.scalars().all()

                if user.language == 2:
                    if settings:
                        for sett in settings:
                            sett.interval = int(quantity)
                        await session.commit()
                        if quantity == 0:
                            await callback.answer('✅ Interval updated (for all groups)', show_alert=True)
                        else:
                            await callback.answer(f'✅ Interval updated (for all groups)', show_alert=True)
                    else:
                        await callback.answer('Error: Settings not found.')
                else:
                    if settings:
                        for sett in settings:
                            sett.interval = int(quantity)
                        await session.commit()
                        if quantity == 0:
                            await callback.answer('✅ Интервал обновлен (для всех групп)', show_alert=True)
                        else:
                            await callback.answer(f'✅ Интервал обновлен (для всех групп)', show_alert=True)
                    else:
                        await callback.answer('Ошибка: Настройки не найдены.')

            await setting(callback)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(UserState.waiting_for_one_time_interval)
async def process_one_interval(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block: 
                try:
                    await message.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                async with async_session() as session:
                    result = await session.execute(select(OneTimeSettings).where(OneTimeSettings.user_id == user_id))
                    settings = result.scalars().all()

                    if user.language == 2:
                        if settings:
                            try:
                                interval = int(message.text)
                                if interval <= 240:
                                    for sett in settings:
                                        sett.interval = interval
                                    await session.commit()
                                    await message.answer('<strong>Interval updated</strong> (for all groups)', parse_mode='HTML')
                                else:
                                    await message.answer('<strong>❗️Interval cannot be greater than 240 minutes</strong>',
                                                         parse_mode='HTML', reply_markup=kb.for_what_eng)
                                    return
                            except ValueError:
                                await message.answer('<strong>❗️Enter a valid value</strong>',
                                                     parse_mode='HTML', reply_markup=kb.for_what_eng)
                                return
                        else:
                            await message.answer('Error: Settings not found.')
                    else:
                        if settings:
                            try:
                                interval = int(message.text)
                                if interval <= 240:
                                    for sett in settings:
                                        sett.interval = interval
                                    await session.commit()
                                    await message.answer('<strong>✅ Интервал обновлен</strong> (для всех групп)', parse_mode='HTML')
                                else:
                                    await message.answer('<strong>❗️Интервал не может быть больше 240 минут</strong>',
                                                         parse_mode='HTML', reply_markup=kb.for_what)
                                    return
                            except ValueError:
                                await message.answer('<strong>❗️Введите корректное значение</strong>',
                                                     parse_mode='HTML', reply_markup=kb.for_what)
                                return
                        else:
                            await message.answer('Ошибка: Настройки не найдены.')

                await send_one_time_message_settings(message.from_user.id, message)
                await state.clear()

@rt.callback_query(F.data == 'one_time_without_title')
async def one_time_without_title(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            async with async_session() as session:
                active_group = await session.scalar(
                    select(Group).filter(Group.user_id == user_id, Group.active == True)
                )
                if not active_group:
                    await callback.answer("Ошибка: активная группа не найдена.", show_alert=True)
                    return

                settings = await session.scalar(select(OneTimeSettings).where(OneTimeSettings.group_id == active_group.id))
                if settings:
                    settings.subject = 'Без темы'
                    if user.language == 2:
                        await callback.answer('✅ Email subject updated', show_alert=True)
                    else:
                        await callback.answer('✅ Заголовок письма обновлен', show_alert=True)
                    await session.commit()
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)

    await one_time_message_settings(callback)
@rt.callback_query(F.data == 'one_time_without_text')
async def one_time_without_text(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            async with async_session() as session:
                active_group = await session.scalar(
                    select(Group).filter(Group.user_id == user_id, Group.active == True)
                )
                if not active_group:
                    await callback.answer("Ошибка: активная группа не найдена.", show_alert=True)
                    return

                settings = await session.scalar(select(OneTimeSettings).where(OneTimeSettings.group_id == active_group.id))
                if settings:
                    settings.message = 'Без текста'
                    if user.language == 2:
                        await callback.answer('✅ Email body updated', show_alert=True)
                    else:
                        await callback.answer('✅ Текст письма обновлен', show_alert=True)
                    await session.commit()

            await one_time_message_settings(callback)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)

#отправка писем
async def send_email(user_email, user_password, bcc_list, subject, message_text, beats, bot, email_records, user_id):
    msg = MIMEMultipart()
    msg['From'] = user_email
    if subject != "Без темы":
        msg['Subject'] = subject

    if message_text != "Без текста":
        msg.attach(MIMEText(message_text, 'plain', "UTF-8"))

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    total_size = 0
    final_beats = []
    excluded_beats = []

    for beat in beats:
        if not beat.file_id:
            print(f"Бит {beat.name} не имеет file_id, пропускаем.")
            continue

        try:
            file_info = await bot.get_file(beat.file_id)
            file_path = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"

            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                async with session.get(file_path) as resp:
                    if resp.status == 200:
                        file_data = await resp.read()
                        size_mb = len(file_data) / (1024 * 1024)

                        if total_size + size_mb > 25:
                            excluded_beats.append(beat)
                            continue

                        total_size += size_mb
                        final_beats.append(beat)

                        part = MIMEBase('audio', 'mp3')
                        part.set_payload(file_data)
                        encoders.encode_base64(part)
                        filename = encode_rfc2231(beat.name, 'utf-8')
                        part.add_header('Content-Disposition', f'attachment; filename*={filename}')
                        msg.attach(part)
                    else:
                        print(f"Ошибка при скачивании {beat.name}: {resp.status}")
        except Exception as e:
            print(f"Ошибка при добавлении {beat.name}: {e}")

    if excluded_beats:
        try:
            async with async_session() as session:
                result = await session.execute(select(User).filter(User.user_id == user_id))
                user = result.scalar_one_or_none()
            if user.language == 2:
                await bot.send_message(
                    user_id,
                    f"⚠️ Some beats were not attached because the total size exceeds 25 MB:\n" +
                    "\n".join(f"• {beat.name}" for beat in excluded_beats)
                )
            else:
                await bot.send_message(
                    user_id,
                    f"⚠️ Некоторые биты не были прикреплены, так как общий размер превышает 25 МБ:\n" +
                    "\n".join(f"• {beat.name}" for beat in excluded_beats)
                )
        except Exception as e:
            print(f"Ошибка при уведомлении пользователя о превышении размера: {e}")



    max_retries = 3
    retry_delay = 10
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
    for attempt in range(max_retries):
        try:
            def sync_send():
                try:
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(user_email, user_password)

                    if len(bcc_list) <= 100:
                        server.sendmail(user_email, bcc_list, msg.as_string())
                    else:
                        for recipient in bcc_list:
                            server.sendmail(user_email, recipient, msg.as_string())
                            std_time.sleep(1)

                    server.quit()
                except Exception as e:
                    raise e

            await asyncio.to_thread(sync_send)

            for email_record in email_records:
                email_record.received_beats = list(
                    set(email_record.received_beats + [beat.id for beat in final_beats if beat.id])
                )
            return True
        except smtplib.SMTPAuthenticationError as e:
            error_msg = str(e)
            if user.language == 2:
                reason = "❌ Error: incorrect Gmail or app password." if "Username and Password not accepted" in error_msg else f"❌ Authorization error: {error_msg}"
            else:
                reason = "❌ Ошибка: неправильный Gmail или пароль приложения." if "Username and Password not accepted" in error_msg else f"❌ Ошибка авторизации: {error_msg}"
        except smtplib.SMTPRecipientsRefused:
            if user.language == 2:
                reason = "❌ Error: all recipients were rejected. Please check the email addresses."
            else:
                reason = "❌ Ошибка: все адресаты отклонены. Проверьте корректность email-адресов."
        except smtplib.SMTPException as e:
            if user.language == 2:
                reason = f"❌ SMTP error: {str(e)}"
            else:
                reason = f"❌ Ошибка SMTP: {str(e)}"
        except Exception as e:
            if user.language == 2:
                reason = f"❌ Unknown error: {str(e)}"
            else:
                reason = f"❌ Неизвестная ошибка: {str(e)}"

        print(reason)

        if attempt < max_retries - 1:
            print(f"⚡️ Повторная попытка через {retry_delay} сек...")
            await asyncio.sleep(retry_delay)
        else:
            try:
                if user.language == 2:
                    await bot.send_message(email_records[0].user_id, f"{reason}\nEmail was not sent.")
                else:
                    await bot.send_message(email_records[0].user_id, f"{reason}\nПисьмо не отправлено.")
            except Exception as e:
                print(f"Ошибка при отправке уведомления пользователю: {e}")
            print("❗️ Максимальное количество попыток исчерпано.")
            return False

async def send_user_emails(user_id: int, bot: Bot, bot_message):
    async with async_session() as session:
        user_result = await session.execute(select(User).where(User.user_id == user_id))
        user = user_result.scalars().first()
        current_time = datetime.now(pytz.timezone("Europe/Moscow"))
        if not user.block:
            if not user or not user.gmail or not user.password:
                try:
                    await bot.delete_message(user_id, bot_message.message_id)
                except Exception as e:
                    print(f"Не удалось удалить сообщение о запуске: {e}")
                await bot.send_message(user_id, f"<strong>❗️Не найден или не указан Gmail/пароль.</strong>",
                                       parse_mode='HTML')
                print(f"⛔️ Пользователь {user_id} не найден или не указан Gmail/пароль.")
                return

            if user.mails_per_day <= 0:
                try:
                    await bot.delete_message(user_id, bot_message.message_id)
                except Exception as e:
                    print(f"Не удалось удалить сообщение о запуске: {e}")
                await bot.send_message(user_id, f"<strong>❗️ Лимит отправки исчерпан ({user.mails_per_day}).</strong>",
                                       parse_mode='HTML')
                print(f"❗️ Лимит отправки исчерпан ({user.mails_per_day}).")
                return

            groups_result = await session.execute(
                select(Group).where(Group.user_id == user_id).order_by(Group.id)
            )
            groups = groups_result.scalars().all()

            if not groups:
                print("❗️ У пользователя нет групп.")
                return

            flagged_email = await session.execute(
                select(Email).join(Group).where(Group.user_id == user_id, Email.flags == True)
            )
            flagged_email = flagged_email.scalars().first()

            started = not flagged_email
            emails_queue = []
            total_sent = 0
            batch_size = 100
            priority_groups = []
            regular_groups = []
            email_for_interval = 0
            skip_to_group_id = None
            flag_was_in_one_time_group = False
            any_sent = False

            for group in groups:
                result = await rq.get_group_data(group.id, session)
                if not result:
                    continue

                current_settings, emails, _, use_one_time = result

                if not emails:
                    continue

                if use_one_time:
                    priority_groups.append((group, result))
                else:
                    regular_groups.append((group, result))

            ordered_groups = priority_groups + regular_groups
            last_email_sent = None
            for group, result in ordered_groups:
                if skip_to_group_id:
                    if group.id != skip_to_group_id:
                        continue
                    else:
                        skip_to_group_id = None
                if user.mails_per_day <= 0:
                    break

                current_settings, emails, _, use_one_time = result

                if not emails:
                    continue

                if not started:
                    try:
                        start_index = next(i for i, e in enumerate(emails) if e.id == flagged_email.id) + 1
                        started = True
                    except StopIteration:
                        start_index = 0
                        started = True
                else:
                    start_index = 0

                emails_to_send = emails[start_index:]
                remaining = user.mails_per_day - len(emails_to_send)
                if remaining > 0:
                    emails_to_send += emails[:min(remaining, start_index)]

                emails_to_send = emails_to_send[:user.mails_per_day]
                if not emails_to_send:
                    continue

                print(f"📤 Отправляем из группы {group.id} — {len(emails_to_send)} почт")
                beats = []
                email_beat_map = {}
                for email in emails_to_send:
                    received_ids = set(email.received_beats or [])
                    if use_one_time and not current_settings.quantity_beat:
                        active_group = await session.scalar(
                            select(Group).filter(Group.user_id == user_id, Group.active == True))
                        result = await session.execute(select(Settings).where(Settings.group_id == active_group.id))
                        settings = result.scalars().first()
                        beats_result = await session.execute(
                            select(Beat)
                            .where(Beat.group_id == group.id)
                            .where(Beat.id.notin_(received_ids))
                            .limit(settings.quantity_beat)
                        )
                        beats = beats_result.scalars().all()
                    if not use_one_time:
                        beats_result = await session.execute(
                            select(Beat)
                            .where(Beat.group_id == group.id)
                            .where(Beat.id.notin_(received_ids))
                            .limit(current_settings.quantity_beat)
                        )
                        beats = beats_result.scalars().all()

                    email_beat_map[email] = beats

                grouped_emails = defaultdict(list)
                for email, beats_list in email_beat_map.items():
                    beat_ids_key = frozenset(beat.id for beat in beats_list)
                    grouped_emails[beat_ids_key].append((email, beats_list))

                pending_batches = []

                for beat_ids_key, email_data in grouped_emails.items():
                    for email, beats in email_data:
                        pending_batches.append((email, beats))
                i = 0

                while i < len(pending_batches):
                    batch_emails = []
                    beat_map = defaultdict(list)

                    while i < len(pending_batches) and len(batch_emails) < 100:
                        email, beats = pending_batches[i]
                        beat_key = frozenset(b.id for b in beats)
                        beat_map[beat_key].append((email, beats))
                        batch_emails.append(email)
                        i += 1
                        email_for_interval += 1

                        if email_for_interval == 100:
                            break  

                    for beat_key, grouped in beat_map.items():
                        if len(beat_key) < current_settings.quantity_beat and not use_one_time:
                            print(
                                f"⏭ Пропущена пачка: только {len(beat_key)} битов, требуется {current_settings.quantity_beat}")
                            continue
                        if len(beat_key) == 0 and not current_settings.quantity_beat:
                            print(
                                f"⏭ Пропущена пачка: только {len(beat_key)} битов, разовая")
                            email_for_interval -= len(batch_emails)
                            continue
                        for j in range(0, len(grouped), batch_size):
                            sub_batch = grouped[j:j + batch_size]
                            bcc_list = [email.email for email, _ in sub_batch]
                            beats_to_send = sub_batch[0][1]

                            print(f"Пачка, {len(sub_batch)} адресов с битами {list(beat_key)}")
                            
                            success = await send_email(
                                user.gmail,
                                user.password,
                                bcc_list,
                                current_settings.subject,
                                current_settings.message,
                                beats_to_send,
                                bot,
                                [email for email, _ in sub_batch],
                                user_id
                            )

                            if success:
                                total_sent += len(sub_batch)
                                user.mails_per_day -= len(sub_batch)
                                last_email_sent = sub_batch[-1][0]
                                any_sent = True
                                emails_queue.append(last_email_sent)
                                current_settings.last_sent_date = current_time
                            else:
                                print("Ошибка отправки. Прекращаем.")
                                return

                            await asyncio.sleep(2)

                    if email_for_interval >= 100:
                        interval = current_settings.interval
                        print(f"⏸ Интервал {interval} минут после 100 email-ов")
                        await asyncio.sleep(interval * 60)
                        email_for_interval = 0

                remaining_email = None
                if use_one_time:
                    if last_email_sent:
                        remaining_emails_result = await session.execute(
                            select(Email)
                            .where(Email.group_id == group.id)
                            .where(Email.id > last_email_sent.id)
                            .limit(1)
                        )
                        remaining_email = remaining_emails_result.scalars().first()
                    if flagged_email and flagged_email.group_id == group.id:
                        flagged_email.flags = False
                        session.add(flagged_email)
                        flag_was_in_one_time_group = True

                    if not remaining_email:
                        await reset_one_time_settings(group.id)
                        group_index = groups.index(group)
                        if group_index + 1 < len(groups):
                            skip_to_group_id = groups[group_index + 1].id
                    else:
                        print(f"Разовая рассылка для группы {group.id} не сброшена, остались почты для отправки.")

            if flagged_email:
                flagged_email.flags = False
                session.add(flagged_email)
            if emails_queue:
                last_email = emails_queue[-1]
                last_email.flags = True
                session.add(last_email)
                print(f"📍 Установлен новый флаг: {last_email.email}")

            session.add(user)
            print(f"✅ Рассылка завершена. Отправлено {total_sent} писем.")
            if any_sent:
                try:
                    await bot.send_message(user_id, "✅", parse_mode='HTML')
                except Exception as e:
                    print(f"Ошибка при уведомлении об успешной отправке: {e}")
            if not any_sent:
                try:
                    await bot.delete_message(user_id, bot_message.message_id)
                except Exception as e:
                    print(f"Не удалось удалить сообщение о запуске: {e}")

                all_emails_result = await session.execute(
                    select(Email).join(Group).where(Group.user_id == user_id)
                )
                all_emails = all_emails_result.scalars().all()
                async with async_session() as session:
                    user_result = await session.execute(select(User).where(User.user_id == user_id))
                    user = user_result.scalars().first()
                if user.language == 2:
                    if not all_emails:
                        await bot.send_message(user_id,
                                               "<strong>❗️Failed to start the mailing: no emails added</strong>",
                                               parse_mode='HTML')
                    else:
                        await bot.send_message(user_id,
                                               "<strong>❗️Failed to start the mailing: not enough beats to send</strong>",
                                               parse_mode='HTML')
                else:
                    if not all_emails:
                        await bot.send_message(user_id,
                                               "<strong>❗️Не удалось запустить рассылку: не добавлено ни одной почты</strong>",
                                               parse_mode='HTML')
                    else:
                        await bot.send_message(user_id,
                                               "<strong>❗️Не удалось запустить рассылку: не хватает битов для отправки</strong>",
                                               parse_mode='HTML')
        await session.commit()


async def reset_one_time_settings(group_id: int):
    async with async_session() as session:
        one_time_result = await session.execute(select(OneTimeSettings).where(OneTimeSettings.group_id == group_id))
        one_time_settings = one_time_result.scalars().first()
        if not one_time_settings:
            return

        one_time_settings.subject = "Без темы"
        one_time_settings.message = "Без текста"
        one_time_settings.quantity_beat = False
        one_time_settings.on_of_auto = False

        await session.commit()



async def send_email_extra(user_email, user_password, receiver_emails, subject, message_text, beats, bot, user_id=None):
    msg = MIMEMultipart()
    msg['From'] = user_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message_text, 'plain', "UTF-8"))

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    total_size = 0 

    attached_beats = []

    for beat in beats:
        file_id = beat.get("file_id")
        file_name = beat.get("file_name", f"{file_id}.mp3")

        if not file_id:
            print(f"Бит без file_id, пропускаем: {beat}")
            continue

        try:
            file_info = await bot.get_file(file_id)
            file_path = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"

            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                async with session.get(file_path) as resp:
                    if resp.status == 200:
                        file_data = await resp.read()
                        file_size = len(file_data)

                        if total_size + file_size > 25 * 1024 * 1024:
                            print(f"Превышен лимит 25 МБ, бит {file_name} не добавлен.")
                            continue  

                        total_size += file_size
                        part = MIMEBase('audio', 'mp3')
                        part.set_payload(file_data)
                        encoders.encode_base64(part)
                        filename = encode_rfc2231(file_name, 'utf-8')
                        part.add_header('Content-Disposition', f'attachment; filename*={filename}')
                        msg.attach(part)
                        attached_beats.append(file_name)
                    else:
                        print(f"Ошибка при скачивании файла {file_id}: {resp.status}")
        except Exception as e:
            print(f"Ошибка при добавлении файла {file_id}: {e}")
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(user_email, user_password)
            server.sendmail(user_email, receiver_emails, msg.as_string())
        print(f"Письмо успешно отправлено скрытой копией на {', '.join(receiver_emails)}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        error_msg = str(e)
        if user.language == 2:
            reason = "❌ Error: incorrect Gmail or app password." if "Username and Password not accepted" in error_msg else f"❌ Authorization error: {error_msg}"
        else:
            reason = "❌ Ошибка: неправильный Gmail или пароль приложения." if "Username and Password not accepted" in error_msg else f"❌ Ошибка авторизации: {error_msg}"
    except smtplib.SMTPRecipientsRefused:
        if user.language == 2:
            reason = "❌ Error: all recipients were rejected. Please check the email addresses."
        else:
            reason = "❌ Ошибка: все адресаты отклонены. Проверьте корректность email-адресов."

    except smtplib.SMTPException as e:
        if user.language == 2:
            reason = f"❌ SMTP error: {str(e)}"
        else:
            reason = f"❌ Ошибка SMTP: {str(e)}"

    except Exception as e:
        if user.language == 2:
            reason = f"❌ Unknown error: {str(e)}"
        else:
            reason = f"❌ Неизвестная ошибка: {str(e)}"

    print(reason)
    if bot and user_id:
        await bot.send_message(user_id, reason)
    return False



#Екстра

@rt.callback_query(F.data == 'extra')
async def extra_handler(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user and not user.block:
            if user.extra_mail > 0:
                await call.answer('Extra')

                user_data = await state.get_data()
                if 'emails' in user_data or 'beats' in user_data:
                    await send_finish_beats_message_call(call, state)
                else:
                    await state.update_data(emails=[], beats=[], subject='', text='')
                    await send_finish_beats_message_call(call, state)
            else:
                if user.language == 2:
                    await call.answer('❗️ Limit reached 50/50', show_alert=True)
                else:
                    await call.answer('❗️Вы достигли лимита 50/50', show_alert=True)
        else:
            await call.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(FSMEmail.awaiting_email)
async def handle_extra_emails(msg: Message, state: FSMContext):
    user_id = msg.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:
                try:
                    await msg.delete()
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                new_emails = [email.lower() for email in re.findall(email_pattern, msg.text)]

                data = await state.get_data()
                temp_emails = set(data.get("temp_emails", []))
                temp_emails.update(new_emails)
                await state.update_data(temp_emails=list(temp_emails))
@rt.callback_query(F.data == 'confirm_add_emails')
async def confirm_add_emails(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            data = await state.get_data()
            temp_emails = list(set(data.get("temp_emails", [])))  
            current_emails = set(data.get("emails", []))

            MAX_EMAILS = 50
            already_have = len(current_emails)
            available_slots = max(0, MAX_EMAILS - already_have)

            emails_to_add = temp_emails[:available_slots]
            remaining_unadded = temp_emails[available_slots:]

            total_emails = len(current_emails) + len(emails_to_add)

            if total_emails > user.extra_mail:
                if user.language == 2:
                    await call.answer(
                        f"❗️You reached the limit {total_emails}/{user.extra_mail}", show_alert=True
                    )
                else:
                    await call.answer(
                        f"❗️Вы достигли лимита {total_emails}/{user.extra_mail}", show_alert=True
                    )
                return

            current_emails.update(emails_to_add)

            await state.update_data(emails=list(current_emails), temp_emails=[])  

            if user.language == 2:
                await call.message.answer(f"✅ <strong>{len(emails_to_add)} addresses added</strong>", parse_mode='HTML')
            else:
                await call.message.answer(f"✅ <strong>Добавлено {len(emails_to_add)} почт</strong>", parse_mode='HTML')

            if remaining_unadded:
                MAX_DISPLAY = 100
                not_added_list = list(remaining_unadded)
                display_part = "\n".join(not_added_list[:MAX_DISPLAY])
                extra_count = len(not_added_list) - MAX_DISPLAY

                if user.language == 2:
                    msg = f"<strong>❗️NOT ADDED:</strong>\n\n{display_part}"
                    if extra_count > 0:
                        msg += f"\n<strong>... and {extra_count} more</strong>"
                else:
                    msg = f"<strong>❗️НЕ БЫЛИ ДОБАВЛЕНЫ:</strong>\n\n{display_part}"
                    if extra_count > 0:
                        msg += f"\n<strong>... и еще {extra_count}</strong>"

                await call.message.answer(msg, parse_mode='HTML')

            await send_finish_beats_message(call.message, state, user_id=user_id)
        else:
            await call.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}", show_alert=True)
@rt.message(FSMEmail.awaiting_beats)
async def handle_extra_beats(msg: Message, state: FSMContext):
    user_id = msg.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await msg.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                if not (msg.audio or msg.document):
                    return

                file = msg.audio or msg.document
                file_format = file.file_name.split('.')[-1].lower() if file.file_name else ''

                if file_format not in ['mp3', 'wav']:
                    return

                data = await state.get_data()
                current_beats = data.get("beats", [])
                if not isinstance(current_beats, list):
                    current_beats = []

                new_beat = {
                    "file_id": file.file_id,
                    "file_name": file.file_name,
                    "file_format": file_format
                }

                if not any(b.get("file_id") == file.file_id for b in current_beats):
                    current_beats.append(new_beat)
                    await state.update_data(beats=current_beats)
@rt.callback_query(F.data == "finish_beats_extra", FSMEmail.awaiting_beats)
async def view_beats_extra_after_add(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            data = await state.get_data()
            beats = data.get("beats", [])


            await send_finish_beats_message(callback.message, state, user_id)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
async def finish_beats_by_button(call: CallbackQuery, state: FSMContext):
    await call.answer()

    user_id = call.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            async with async_session() as session:
                result = await session.execute(select(User).filter(User.user_id == user_id))
                user = result.scalar_one_or_none()

                if not user or user.block:
                    return

            user_data = await state.get_data()
            emails = user_data.get('emails', [])
            beats = user_data.get('beats', [])
            subject = user_data.get('subject', '')
            text = user_data.get('text', '')

            keyboard_buttons = []

            if beats:
                for beat in beats:
                    keyboard_buttons.append([
                        InlineKeyboardButton(text=beat["file_name"], callback_data="noop")
                    ])
            if user.language == 2:
                keyboard_buttons.extend([
                    [InlineKeyboardButton(text="📋 Email Subject", callback_data="change_subject_extra"),
                     InlineKeyboardButton(text="📄 Email Body", callback_data="change_text_extra")],
                    [InlineKeyboardButton(text="✉️ Emails", callback_data="view_emails_extra"),
                     InlineKeyboardButton(text="🎹 Beats", callback_data="view_beats_extra")],
                    [InlineKeyboardButton(text="📨 Send", callback_data="send_email_extra")]
                ])

            else:
                keyboard_buttons.extend([
                    [InlineKeyboardButton(text="📋 Заголовок письма", callback_data="change_subject_extra"),
                     InlineKeyboardButton(text="📄 Текст письма", callback_data="change_text_extra")],
                    [InlineKeyboardButton(text="✉️ Почты", callback_data="view_emails_extra"),
                     InlineKeyboardButton(text="🎹 Биты", callback_data="view_beats_extra")],
                    [InlineKeyboardButton(text="📨 Отправить", callback_data="send_email_extra")]
                ])

            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

            def escape(text):
                return text.replace('.', '\\.').replace('-', '\\-').replace('_', '\\_') \
                    .replace('!', '\\!').replace('(', '\\(').replace(')', '\\)')

            if user.language == 2:
                subject_display = f"\n{format_as_quote(subject)}\n" if subject else "__not set__"
                text_display = f"\n{format_as_quote(text)}\n" if text else "__not set__"
                emails_display = ', '.join(escape(email) for email in emails) if emails else "__not specified__"
            else:
                subject_display = f"\n{format_as_quote(subject)}\n" if subject else "__не задано__"
                text_display = f"\n{format_as_quote(text)}\n" if text else "__не задано__"
                emails_display = ', '.join(escape(email) for email in emails) if emails else "__не указано__"

            if user.language == 2:
                await call.message.answer(
                    f"*Current email parameters:*\n\n"
                    f"*📋 Subject:* {subject_display}\n\n"
                    f"*📄 Body:* {text_display}\n\n"
                    f"*📮 Recipients:* {emails_display}\n———\n\n"
                    f"⚙️ *Choose the settings you want to change using the buttons below:*",
                    reply_markup=keyboard,
                    parse_mode='MarkdownV2'
                )
            else:
                await call.message.answer(
                    f"*Текущие параметры письма:*\n\n"
                    f"*📋 Заголовок письма:* {subject_display}\n\n"
                    f"*📄 Текст письма:* {text_display}\n\n"
                    f"*📮 Кому:* {emails_display}\n———\n\n"
                    f"⚙️ *Выберите настройки которые хотите поменять по кнопкам ниже:*",
                    reply_markup=keyboard,
                    parse_mode='MarkdownV2'
                )
async def send_finish_beats_message_call(callback, state):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            user_data = await state.get_data()
            emails = user_data.get('emails', [])
            beats = user_data.get('beats', [])
            subject = user_data.get('subject', '')
            text = user_data.get('text', '')

            keyboard_buttons = []

            if beats:
                for beat in beats:
                    keyboard_buttons.append([
                        InlineKeyboardButton(text=beat["file_name"], callback_data="noop")
                    ])

            if user.language == 2:
                keyboard_buttons.extend([
                    [InlineKeyboardButton(text="📋 Email subject", callback_data="change_subject_extra"),
                     InlineKeyboardButton(text="📄 Email body", callback_data="change_text_extra")],
                    [InlineKeyboardButton(text="✉️ Emails", callback_data="view_emails_extra"),
                     InlineKeyboardButton(text="🎹 Beats", callback_data="view_beats_extra")],
                    [InlineKeyboardButton(text="📨 Send", callback_data="send_email_extra")]
                ])

            else:
                keyboard_buttons.extend([
                    [InlineKeyboardButton(text="📋 Заголовок письма", callback_data="change_subject_extra"),
                     InlineKeyboardButton(text="📄 Текст письма", callback_data="change_text_extra")],
                    [InlineKeyboardButton(text="✉️ Почты", callback_data="view_emails_extra"),
                     InlineKeyboardButton(text="🎹 Биты", callback_data="view_beats_extra")],
                    [InlineKeyboardButton(text="📨 Отправить", callback_data="send_email_extra")]
                ])

            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

            def escape(text):
                return text.replace('.', '\\.').replace('-', '\\-').replace('_', '\\_') \
                           .replace('!', '\\!').replace('(', '\\(').replace(')', '\\)')

            if user.language == 2:
                subject_display = f"\n{format_as_quote(subject)}\n" if subject else "__not set__"
                text_display = f"\n{format_as_quote(text)}\n" if text else "__not set__"
                emails_display = ', '.join(escape(email) for email in emails) if emails else "__not set__"
            else:
                subject_display = f"\n{format_as_quote(subject)}\n" if subject else "__не задано__"
                text_display = f"\n{format_as_quote(text)}\n" if text else "__не задано__"
                emails_display = ', '.join(escape(email) for email in emails) if emails else "__не указано__"

            if user.language == 2:
                await callback.message.answer(
                    f"*Current email parameters:*\n\n"
                    f"*📋 Subject:* {subject_display}\n\n"
                    f"*📄 Body:* {text_display}\n\n"
                    f"*📮 Recipients:* {emails_display}\n———\n\n"
                    f"⚙️ *Choose the settings you want to change using the buttons below:*",
                    reply_markup=keyboard,
                    parse_mode='MarkdownV2'
                )
            else:
                await callback.message.answer(
                    f"*Текущие параметры письма:*\n\n"
                    f"*📋 Заголовок письма:* {subject_display}\n\n"
                    f"*📄 Текст письма:* {text_display}\n\n"
                    f"*📮 Кому:* {emails_display}\n———\n\n"
                    f"⚙️ *Выберите настройки которые хотите поменять по кнопкам ниже:*",
                    reply_markup=keyboard,
                    parse_mode='MarkdownV2'
                )
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
async def send_finish_beats_message(message, state, user_id: int = 0):

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await message.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                user_data = await state.get_data()
                emails = user_data.get('emails', [])
                beats = user_data.get('beats', [])
                subject = user_data.get('subject', '')
                text = user_data.get('text', '')

                keyboard_buttons = []

                if beats:
                    for beat in beats:
                        keyboard_buttons.append([
                            InlineKeyboardButton(text=beat["file_name"], callback_data="noop")
                        ])

                if user.language == 2:
                    keyboard_buttons.extend([
                        [InlineKeyboardButton(text="📋 Email subject", callback_data="change_subject_extra"),
                         InlineKeyboardButton(text="📄 Email body", callback_data="change_text_extra")],
                        [InlineKeyboardButton(text="✉️ Emails", callback_data="view_emails_extra"),
                         InlineKeyboardButton(text="🎹 Beats", callback_data="view_beats_extra")],
                        [InlineKeyboardButton(text="📨 Send", callback_data="send_email_extra")]
                    ])

                else:
                    keyboard_buttons.extend([
                        [InlineKeyboardButton(text="📋 Заголовок письма", callback_data="change_subject_extra"),
                         InlineKeyboardButton(text="📄 Текст письма", callback_data="change_text_extra")],
                        [InlineKeyboardButton(text="✉️ Почты", callback_data="view_emails_extra"),
                         InlineKeyboardButton(text="🎹 Биты", callback_data="view_beats_extra")],
                        [InlineKeyboardButton(text="📨 Отправить", callback_data="send_email_extra")]
                    ])

                keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

                def escape(text):
                    return text.replace('.', '\\.').replace('-', '\\-').replace('_', '\\_') \
                               .replace('!', '\\!').replace('(', '\\(').replace(')', '\\)')

                if user.language == 2:
                    subject_display = f"\n{format_as_quote(subject)}\n" if subject else "__not set__"
                    text_display = f"\n{format_as_quote(text)}\n" if text else "__not set__"
                    emails_display = ', '.join(escape(email) for email in emails) if emails else "__not set__"
                else:
                    subject_display = f"\n{format_as_quote(subject)}\n" if subject else "__не задано__"
                    text_display = f"\n{format_as_quote(text)}\n" if text else "__не задано__"
                    emails_display = ', '.join(escape(email) for email in emails) if emails else "__не указано__"

                if user.language == 2:
                    await message.answer(
                        f"*Current email parameters:*\n\n"
                        f"*📋 Subject:* {subject_display}\n\n"
                        f"*📄 Body:* {text_display}\n\n"
                        f"*📮 Recipients:* {emails_display}\n———\n\n"
                        f"⚙️ *Choose the settings you want to change using the buttons below:*",
                        reply_markup=keyboard,
                        parse_mode='MarkdownV2'
                    )
                else:
                    await message.answer(
                        f"*Текущие параметры письма:*\n\n"
                        f"*📋 Заголовок письма:* {subject_display}\n\n"
                        f"*📄 Текст письма:* {text_display}\n\n"
                        f"*📮 Кому:* {emails_display}\n———\n\n"
                        f"⚙️ *Выберите настройки которые хотите поменять по кнопкам ниже:*",
                        reply_markup=keyboard,
                        parse_mode='MarkdownV2'
                    )
@rt.callback_query(F.data.startswith('view_emails_extra'))
async def view_emails_extra(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            data = await state.get_data()
            emails = data.get("emails", [])

            if user.language == 2:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🗑 Delete", callback_data="delete_mail_extra"),
                     InlineKeyboardButton(text="📩 Add", callback_data="add_mail_extra")],
                    [InlineKeyboardButton(text="↩️ Back", callback_data="cancel_delete_beats")]
                ])

                await callback.message.edit_text(
                    f"<strong>Choose an action with emails using the buttons below:</strong>",
                    parse_mode='HTML',
                    reply_markup=keyboard
                )

            else:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🗑 Удалить", callback_data="delete_mail_extra"),
                     InlineKeyboardButton(text="📩 Пополнить", callback_data="add_mail_extra")],
                    [InlineKeyboardButton(text="↩️ Назад", callback_data="cancel_delete_beats")]
                ])


                await callback.message.edit_text(
                    f"<strong>Выберите действия с почтами по кнопкам ниже:</strong>",
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
async def show_emails_extra(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await message.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                data = await state.get_data()
                emails = data.get("emails", [])

                if user.language == 2:
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🗑 Delete", callback_data="delete_mail_extra"),
                         InlineKeyboardButton(text="📩 Add", callback_data="add_mail_extra")],
                        [InlineKeyboardButton(text="↩️ Back", callback_data="cancel_delete_beats")]
                    ])

                    await message.answer(
                        f"<strong>Choose an action with emails using the buttons below:</strong>",
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )

                else:
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🗑 Удалить", callback_data="delete_mail_extra"),
                         InlineKeyboardButton(text="📩 Пополнить", callback_data="add_mail_extra")],
                        [InlineKeyboardButton(text="↩️ Назад", callback_data="cancel_delete_beats")]
                    ])

                    await message.answer(
                        f"<strong>Выберите действия с почтами по кнопкам ниже:</strong>",
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
@rt.callback_query(F.data.startswith("view_beats_extra"))
async def view_beats_extra(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            data = await state.get_data()
            beats = data.get("beats", [])

            if user.language == 2:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🗑 Delete", callback_data="delete_beatsextra"),
                     InlineKeyboardButton(text="➕ Add", callback_data="add_beat_extra")],
                    [InlineKeyboardButton(text="↩️ Back", callback_data="cancel_delete_beats")]
                ])

                await callback.message.edit_text(
                    f"<strong>Choose an action with beats using the buttons below:</strong>",
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
            else:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🗑 Удалить", callback_data="delete_beatsextra"),
                     InlineKeyboardButton(text="➕ Пополнить", callback_data="add_beat_extra")],
                    [InlineKeyboardButton(text="↩️ Назад", callback_data="cancel_delete_beats")]
                ])

                await callback.message.edit_text(
                    f"<strong>Выберите действия с битами по кнопкам ниже:</strong>",
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'delete_beatsextra')
async def delete_beats_menu(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            user_data = await state.get_data()
            beats = user_data.get("beats", [])

            if not beats:
                if user.language == 2:
                    await call.answer("❗️Database is empty", show_alert=True)
                else:
                    await call.answer("❗️База пуста", show_alert=True)
                return
            if user.language == 2:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                                                                   [InlineKeyboardButton(text=beat["file_name"],
                                                                                         callback_data=f"delete_beatidx:{i}")]
                                                                   for i, beat in enumerate(beats)
                                                               ] + [[InlineKeyboardButton(text="↩️ Back",
                                                                                          callback_data="back_to_beats_extra")]])
                await call.answer('🗑 Delete beats')
                await call.message.edit_text("🔴 <strong>Select the beats you want to delete</strong>",
                                             parse_mode='HTML', reply_markup=keyboard)
            else:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=beat["file_name"], callback_data=f"delete_beatidx:{i}")]
                    for i, beat in enumerate(beats)
                ] + [[InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_beats_extra")]])
                await call.answer('🗑 Удалить биты')
                await call.message.edit_text("🔴 <strong>Выберите биты, которые хотите удалить</strong>", parse_mode='HTML', reply_markup=keyboard)
        else:
            await call.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data.startswith("delete_beatidx:"))
async def delete_single_beat(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            index = int(call.data.split(":")[1])
            data = await state.get_data()
            beats = data.get("beats", [])
            if user.language == 2:
                if 0 <= index < len(beats):
                    removed = beats.pop(index)
                    await state.update_data(beats=beats)
                    await call.answer("✅ Beat deleted")
                else:
                    await call.answer("⚠️ Deletion error", show_alert=True)

            else:
                if 0 <= index < len(beats):
                    removed = beats.pop(index)
                    await state.update_data(beats=beats)
                    await call.answer(f"✅ Бит удален")
                else:
                    await call.answer("⚠️ Ошибка при удалении", show_alert=True)

            await delete_beats_menu(call, state)
        else:
            await call.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'cancel_delete_beats')
async def cancel_delete_beats(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await call.answer('↩️ Back')
            else:
                await call.answer('↩️ Назад')
            await send_finish_beats_message_call(call, state)
        else:
            await call.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'add_beat_extra')
async def add_beats(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await call.answer('🎵 Add beats')
                await call.message.edit_text("<strong>Send the beats you want to add</strong>", parse_mode='HTML',
                                             reply_markup=InlineKeyboardMarkup(
                                                 inline_keyboard=[
                                                     [InlineKeyboardButton(text="✅ Ready",
                                                                           callback_data="finish_beats_extra")],
                                                     [InlineKeyboardButton(text='↩️ Back',
                                                                           callback_data='back_to_beats_extra')]
                                                 ]
                                             ))
            else:
                await call.answer('🎵 Добавить биты')
                await call.message.edit_text("<strong>Отправьте биты, которые хотите добавить</strong>", parse_mode='HTML',
                                     reply_markup=InlineKeyboardMarkup(
                                         inline_keyboard=[
                                             [InlineKeyboardButton(text="✅ Готово",
                                                                   callback_data="finish_beats_extra")],
                                             [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_beats_extra')]
                                         ]
                                     ))
            await state.set_state(FSMEmail.awaiting_beats)
        else:
            await call.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'change_subject_extra')
async def change_subject(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await call.answer('📋 Email subject')
                await call.message.edit_text("<strong>Enter the email subject</strong>", parse_mode='HTML',
                                             reply_markup=kb.back_to_extra_text_subject_eng)
            else:
                await call.answer('📋 Изменить заголовок')
                await call.message.edit_text("<strong>Напишите заголовок письма</strong>", parse_mode='HTML',reply_markup=kb.back_to_extra_text_subject)
            await state.set_state(FSMEmail.awaiting_subject)
        else:
            await call.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(FSMEmail.awaiting_subject, F.data == 'without_title_text_extra')
async def without_subject(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            await state.update_data(subject="")  
            if user.language == 2:
                await callback.message.edit_text('✅ <strong>Email subject updated</strong>', parse_mode='HTML')
            else:
                await callback.message.edit_text('✅ <strong>Заголовок письма обновлен</strong>', parse_mode='HTML')
            await send_finish_beats_message(callback.message, state, user_id=user_id)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(FSMEmail.awaiting_subject)
async def process_subject(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await message.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                await state.update_data(subject=message.text)
                if user.language == 2:
                    await message.answer('✅ <strong>Email subject updated</strong>', parse_mode='HTML')
                else:
                    await message.answer('✅ <strong>Заголовок письма обновлен</strong>', parse_mode='HTML')
                await send_finish_beats_message(message, state, user_id=user_id)
@rt.callback_query(F.data == 'change_text_extra')
async def change_text(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await call.answer('📄 Email body')
                await call.message.edit_text("<strong>Enter the email body</strong>", parse_mode='HTML',
                                             reply_markup=kb.back_to_extra_text_eng)
            else:
                await call.answer('📄 Изменить текст')
                await call.message.edit_text("<strong>Напишите заголовок письма</strong>", parse_mode='HTML', reply_markup=kb.back_to_extra_text)
            await state.set_state(FSMEmail.awaiting_text)
        else:
            await call.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(FSMEmail.awaiting_text, F.data == 'without_title_text_extra')
async def without_subject(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            await state.update_data(text="") 
            if user.language == 2:
                await callback.message.edit_text('✅ <strong>Email body updated</strong>', parse_mode='HTML')
            else:
                await callback.message.edit_text('✅ <strong>Текст письма обновлен</strong>', parse_mode='HTML')
            await send_finish_beats_message(callback.message, state, user_id=user_id)
        else:
            await callback.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(FSMEmail.awaiting_text)
async def process_text(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await message.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                await state.update_data(text=message.text)
                if user.language == 2:
                    await message.answer('✅ <strong>Email body updated</strong>', parse_mode='HTML')
                else:
                    await message.answer('✅ <strong>Текст письма обновлен</strong>', parse_mode='HTML')
                await send_finish_beats_message(message, state, user_id=user_id)
@rt.callback_query(F.data == 'add_mail_extra')
async def change_emails(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            user_data = await state.get_data()
            emails = user_data.get('emails', [])
            if user.language == 2:
                if len(emails) >= user.extra_mail:
                    if user.language == 2:
                        await call.answer(
                            f"❗️You reached the limit {len(emails)}/{user.extra_mail}", show_alert=True
                        )
                    else:
                        await call.answer(
                            f"❗️Вы достигли лимита {len(emails)}/{user.extra_mail}", show_alert=True
                        )
                    return
                await call.answer('📨 Change emails')
                await call.message.edit_text("<strong>Send the emails you want to add</strong>", parse_mode='HTML',
                                             reply_markup=kb.confirm_email_keyboard_eng())
            else:
                if emails >= user.extra_mail:
                    if user.language == 2:
                        await call.answer(
                            f"❗️You reached the limit {emails}/{user.extra_mail}", show_alert=True
                        )
                    else:
                        await call.answer(
                            f"❗️Вы достигли лимита {emails}/{user.extra_mail}", show_alert=True
                        )
                    return
                await call.answer('📨 Изменить почты')
                await call.message.edit_text("<strong>Отправьте почты, которые хотите добавить</strong>", parse_mode='HTML', reply_markup=kb.confirm_email_keyboard())
            await state.set_state(FSMEmail.awaiting_email)
        else:
            await call.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'delete_mail_extra')
async def ask_emails_to_delete(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            data = await state.get_data()
            emails = data.get("emails", [])
            if user.language == 2:
                if not emails:
                    await call.answer("❗️Database is empty", show_alert=True)
                    return
                await call.answer("🗑 Delete")
                await call.message.edit_text("<strong>Send the addresses you want to delete — each on a new line or separated by commas</strong>",
                                              reply_markup=kb.back_to_mail_extra_eng, parse_mode='HTML')
            else:
                if not emails:
                    await call.answer("❗️База пуста", show_alert=True)
                    return
                await call.answer("🗑 Удалить")
                await call.message.edit_text("<strong>Отправьте почты, которые хотите удалить — каждую с новой строки или через запятую</strong>",
                                              reply_markup=kb.back_to_mail_extra, parse_mode='HTML')
            await state.set_state(FSMEmail.deleting_emails)
        else:
            await call.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.message(FSMEmail.deleting_emails)
async def process_emails_to_delete(msg: Message, state: FSMContext):
    user_id = msg.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if user.block:  
                try:
                    await msg.delete()  
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            else:
                user_input = msg.text
                user_id = msg.from_user.id

                split_emails = re.split(r'[\s,]+', user_input.strip())
                to_delete = set(email.lower() for email in split_emails if '@' in email)

                data = await state.get_data()
                current_emails = set(data.get("emails", []))

                before = len(current_emails)
                current_emails.difference_update(to_delete)
                after = len(current_emails)
                removed_count = before - after

                await state.update_data(emails=list(current_emails))

                if removed_count > 0:
                    if user.language == 2:
                        await msg.answer(f"✅ <strong>{removed_count} addresses deleted</strong>", parse_mode='HTML')
                    else:
                        await msg.answer(f"✅ <strong>Удалено {removed_count} почт</strong>", parse_mode='HTML')


                await show_emails_extra(msg, state)
                await state.clear()
@rt.callback_query(F.data == 'send_email_extra')
async def send_email_handler(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            async with async_session() as session:
                user = await session.scalar(select(User).where(User.user_id == user_id))

                if not user or not user.gmail or not user.password:
                    if user.language == 2:
                        await call.answer("❌ Error: your Gmail account is not linked or tokens have expired.",
                                          show_alert=True)
                    else:
                        await call.answer("❌ Ошибка: ваш Gmail-аккаунт не привязан или токены устарели.", show_alert=True)
                    return

            user_data = await state.get_data()
            emails = user_data.get('emails', [])
            beats = user_data.get('beats', [])
            subject = user_data.get('subject', '')
            text = user_data.get('text', '')

            if not emails:
                if user.language == 2:
                    await call.answer("❗️You did not add any emails", show_alert=True)
                else:
                    await call.answer("❗️Вы не добавили почты", show_alert=True)
                return

            if not beats:
                if user.language == 2:
                    await call.answer("❗️You did not add any beats", show_alert=True)
                else:
                    await call.answer("❗️Вы не добавили биты", show_alert=True)
                return

            success = await send_email_extra(
                user.gmail, user.password, emails, subject, text, beats, call.bot, user_id = user_id
            )

            if user.language == 2:
                if success:
                    await call.message.answer("✅ Email sent successfully!")
                    user.extra_mail -= len(emails)
                    await session.commit()
                else:
                    await call.answer("❌ Error sending email. Please check the settings.", show_alert=True)
            else:
                if success:
                    await call.message.answer("✅ Письмо успешно отправлено!")
                    user.extra_mail -= len(emails)
                    await session.commit()
                else:
                    await call.answer("❌ Ошибка при отправке письма. Проверьте настройки.", show_alert=True)
        else:
            await call.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'back_to_beats_extra')
async def back_to_beats_extra(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await call.answer('↩️ Back')
            else:
                await call.answer('↩️ Назад')
            await view_beats_extra(call, state)
        else:
            await call.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)
@rt.callback_query(F.data == 'back_to_mail_extra')
async def back_to_mail_extra(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.block:
            if user.language == 2:
                await call.answer('↩️ Back')
            else:
                await call.answer('↩️ Назад')
            await view_emails_extra(call, state)
        else:
            await call.answer(f"{'❗️НЕДОСТУПНО' if user.language != 2 else '❗️NOT AVAILABLE'}"
, show_alert=True)

#блок кнопки

@rt.message(F.from_user.id)
async def check_and_delete_message(message: Message):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user and user.block:
            if message.text not in ['👨‍💻 Поддержка', '👨‍💻 Support', '🌐 Язык', '🌐 Language']:   
                try:
                    await message.delete()
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")

@rt.callback_query(F.data == 'go_2_free')
async def go_2_free(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
    if user.language == 2:
        await callback.answer('💾 Continue with free plan')
        await callback.message.edit_text('<strong>⚠️ No turning back.</strong>\n\n'
                                         'When switching to the free subscription, only emails '
                                         'from the group with the largest number of addresses will remain in the database.\n'
                                         'All emails within that group exceeding the 50-address limit (added earlier) '
                                         'will be automatically deleted.\n\n'
                                         '<strong>Make sure to back up important data in advance.</strong>',
                                         parse_mode='HTML', reply_markup=kb.end_sub_confirmation_eng)
    else:
        await callback.answer('💾 Продолжить с бесплатной')
        await callback.message.edit_text('<strong>⚠️ Пути назад нет.</strong>\n\n'
                                         'При переходе на бесплатную подписку в базе останутся только почты'
                                         ' из группы с наибольшим количеством адресов.\n'
                                         'Все почты внутри этой группы, превышающие лимит в 50 адресов (добавленные раньше),'
                                         ' — будут автоматически удалены.\n\n'
                                         '<strong>Позаботьтесь о сохранности нужных данных заранее.</strong>',
                                         parse_mode='HTML', reply_markup=kb.end_sub_confirmation)

@rt.callback_query(F.data == 'agree_to_free_sub')
async def agree_to_free_sub(callback: CallbackQuery):
    user_id = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(
            select(User)
            .options(
                selectinload(User.groups)
                .selectinload(Group.emails),
                selectinload(User.groups)
                .selectinload(Group.beats),
                selectinload(User.groups)
                .selectinload(Group.settings)
            )
            .where(User.user_id == user_id)
        )
        user: User = result.scalar_one_or_none()
        if not user:
            await callback.answer("Пользователь не найден", show_alert=True)
            return

        user.subscription = 'free'

        groups = user.groups
        if not groups:
            await callback.answer("У вас нет групп", show_alert=True)
            return

        max_group = max(groups, key=lambda g: len(g.emails) if g.emails else 0)

        for group in groups:
            if group.id != max_group.id:
                if group.settings:
                    await session.delete(group.settings)
                await session.delete(group)

        if max_group.emails:
            max_group.emails.sort(key=lambda e: e.id, reverse=True)
            for email in max_group.emails[50:]:
                await session.delete(email)

        if max_group.beats:
            max_group.beats.sort(key=lambda b: b.id, reverse=True)
            for beat in max_group.beats[20:]:
                await session.delete(beat)

        max_group.active = True
        user.block = False

        if user.language == 2:
            await callback.message.edit_text(
                "✅ You have successfully switched to the free subscription.",
                reply_markup=kb.in_main_menu_eng
            )
    
        else:
            await callback.message.edit_text(
                "✅ Вы успешно перешли на бесплатную подписку.",
                reply_markup=kb.in_main_menu
            )
        await session.commit()
