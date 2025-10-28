import asyncio
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import pytz
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from collections import defaultdict
import os

from app.database.models import async_session, User, async_main, Settings, OneTimeSettings, Beat, Email, Group
from config import TOKEN
from app.handlers import rt, send_user_emails
import app.keyboards as kb
import app.database.requests as rq


bot = Bot(token=TOKEN)
dp = Dispatcher()

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

async def deduct_subscription_for_all_users():
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.subscription_day > 0))
        users = result.scalars().all()
        settings_result = await session.execute(select(Settings).where(Settings.on_of_auto == True))
        settings = settings_result.scalars().first()
        one_time_result = await session.execute(select(OneTimeSettings).where(OneTimeSettings.on_of_auto == True))
        one_time_settings = one_time_result.scalars().first()

        moscow_tz = pytz.timezone('Europe/Moscow')
        now = datetime.now(moscow_tz)

        users_to_notify = [] 

        for user in users:
            if user.subscription_day and user.subscription_day > 0:
                if user.subscription_start.tzinfo is None:
                    user.subscription_start = moscow_tz.localize(user.subscription_start)

                time_diff = now - user.subscription_start.astimezone(moscow_tz)
                if time_diff >= timedelta(days=1):
                    if settings.on_of_auto or one_time_settings.on_of_auto:
                        user.subscription_day -= 1
                        user.subscription_start = now

                        if user.subscription_day == 0:
                            user.block = True
                            users_to_notify.append((user.user_id, user.language))

                        session.add(user)

        await session.commit()

    for user_id, lang in users_to_notify:
        try:
            if lang == 2:
                await bot.send_message(
                    user_id,
                    '<strong>🪫 Your subscription has ended!</strong> Mailing has been paused.\n\n'
                    'To continue using the service, choose an action using the buttons below:',
                    parse_mode='HTML', reply_markup=kb.end_sub_eng
                )
            else:
                await bot.send_message(
                    user_id,
                    '<strong>🪫 Ваша подписка завершилась!</strong> Рассылка приостановлена.\n\n'
                    'Чтобы продолжить пользоваться сервисом, выберите действия по кнопкам ниже:',
                    parse_mode='HTML', reply_markup=kb.end_sub
                )
        except Exception as e:
            print(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")
async def deduct_referrals():
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.subscription > 0))
        users = result.scalars().all()

        now = datetime.now(pytz.UTC).replace(second=0, microsecond=0)
        SUPPORT_LINK = "https://t.me/xxxxx"

        for user in users:
            if not user.referral_discount_expire:
                continue

            expire = user.referral_discount_expire.astimezone(pytz.UTC).replace(second=0, microsecond=0)
            if user.language == 2:
                if expire == now + timedelta(days=3):
                    await bot.send_message(
                        user.user_id,
                        f"⏳ <b>Your referral discount will remain active for 3 more days</b>\n\n"
                        f"If you have any questions, please contact <a href='{SUPPORT_LINK}'>support</a>",
                        parse_mode="HTML", disable_web_page_preview=True
                    )

                elif expire == now + timedelta(days=1):
                    await bot.send_message(
                        user.user_id,
                        f"⏳ <b>You have 1 day left to use your referral discount</b>\n\n"
                        f"After that, you won’t be able to get it via other referral links!\n\n"
                        f"If you have any questions <b>or want to reserve the discount for a longer period</b>, "
                        f"please contact <a href='{SUPPORT_LINK}'>support</a>",
                        parse_mode="HTML", disable_web_page_preview=True
                    )
            else:
                if expire == now + timedelta(days=3):
                    await bot.send_message(
                        user.user_id,
                        f"⏳ <b>Ваша реферальная скидка будет активна ещё 3 дня</b>\n\n"
                        f"Если возникнут вопросы — обращайтесь в <a href='{SUPPORT_LINK}'>поддержку</a>",
                        parse_mode="HTML", disable_web_page_preview=True
                    )

                elif expire == now + timedelta(days=1):
                    await bot.send_message(
                        user.user_id,
                        f"⏳ <b>У вас остались сутки, чтобы использовать вашу реферальную скидку</b>\n\n"
                        f"После этого получить её через другие реферальные ссылки будет невозможно!\n\n"
                        f"Если возникли вопросы <b>или хотите забронировать скидку на более длительный срок</b> — "
                        f"напишите в <a href='{SUPPORT_LINK}'>поддержку</a>",
                        parse_mode="HTML", disable_web_page_preview=True
                    )
async def check_and_send_group_email(bot):
    current_time = datetime.now(pytz.timezone("Europe/Moscow"))
    current_date = current_time.date()
    current_hour = current_time.hour
    current_minute = current_time.minute

    async with async_session() as session:
        groups_result = await session.execute(
            select(Settings)
            .options(selectinload(Settings.group))  
            .where(Settings.on_of_auto == True)
        )

        groups = groups_result.scalars().all()

        unique_users = set()

        for group_settings in groups:
            if group_settings.send_time:
                send_hour = group_settings.send_time.hour
                send_minute = group_settings.send_time.minute

                if current_hour == send_hour and current_minute == send_minute:
                    last_sent_date = group_settings.last_sent_date or datetime(2000, 1, 1)
                    last_sent_date_date = last_sent_date.date() if isinstance(last_sent_date,
                                                                              datetime) else last_sent_date

                    days_interval = int(
                        group_settings.periodicity.split('_')[-1]) if '_' in group_settings.periodicity else 1

                    if (current_date - last_sent_date_date).days >= days_interval:
                        user_id = group_settings.group.user_id
                        unique_users.add(user_id)
                        session.add(group_settings)

        await session.commit()

        tasks = []

        for user_id in unique_users:
            async with async_session() as session:
                result = await session.execute(select(User).filter(User.user_id == user_id))
                user = result.scalar_one_or_none()
            if user and not user.block:
                try:
                    now = datetime.now(pytz.timezone("Europe/Moscow"))
                    if not user.refresh_to_day or user.refresh_to_day.date() != now.date():
                        if user.subscription == 'basic' or user.subscription == 'premium':
                            user.mails_per_day = 450
                            user.extra_mail = 50
                        else:
                            user.mails_per_day = 25
                        user.refresh_to_day = now
                        session.add(user)
                        print('Сброшено')
                    if user.language == 2:
                        bot_message = await bot.send_message(user_id, "<strong>📤 Sending...</strong>",
                                                             parse_mode='HTML')
                    else:
                        bot_message = await bot.send_message(user_id, "<strong>📤 Идет отправка писем...</strong>",
                                                             parse_mode='HTML')
                    await session.commit()
                except Exception as e:
                    print(f"Ошибка при уведомлении пользователя: {e}")
                    continue 
                tasks.append(asyncio.create_task(send_user_emails(user_id, bot, bot_message)))


        await asyncio.gather(*tasks)





async def setup_scheduler(bot):
    global scheduler 
    scheduler.add_job(
        deduct_subscription_for_all_users,
        'interval',
        hours=0,
        minutes=1,
        seconds=0,
        start_date=datetime.now(pytz.timezone("Europe/Moscow"))
    )
    scheduler.add_job(
        deduct_referrals,
        'interval',
        hours=0,
        minutes=1,
        seconds=0,
        start_date=datetime.now(pytz.timezone("Europe/Moscow"))
    )
    scheduler.add_job(
        check_and_send_group_email,
        'cron',
        second=0,  
        args=[bot],
        max_instances=100
    )

    scheduler.start()
    print("Планировщик запущен.")

    print(f"Текущее время {datetime.now(pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d %H:%M:%S')} (по Москве)")

    next_run = scheduler.get_job(scheduler.get_jobs()[0].id).next_run_time
    print(f"Следующее время выполнения задачи: {next_run.strftime('%Y-%m-%d %H:%M:%S')} (по Москве)")

async def main():
    await async_main()
    dp.include_router(rt)
    await setup_scheduler(bot)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
