from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import async_session, User, Email, Beat, Group, Settings, OneTimeSettings, PromotionalCode


async def get_user(user_id):
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        return result.scalar_one_or_none()

async def set_user(user_id, username=None, gmail=None, access_token=None, refresh_token=None, password=None, subscription_start=None):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.user_id == user_id))
        if not user:
            session.add(User(user_id=user_id, username=username or 'Неуказано',
                             gmail=gmail or 'не указано', access_token=access_token, refresh_token=refresh_token,
                             password=password or 'Неуказано', subscription_start=subscription_start or None))
        else:
            if username:
                user.username = username
            if gmail:
                user.gmail = gmail
            if access_token:
                user.access_token = access_token
            if refresh_token:
                user.refresh_token = refresh_token
            if password:
                user.password = password
            if subscription_start:
                user.subscription_start = subscription_start
        await session.commit()

async def set_group(user_id, name=None):
    async with async_session() as session:
        group = await session.scalar(select(Group).where(Group.user_id == user_id))
        if not group:
            session.add(Group(user_id=user_id, name=name or '▢'))
        else:
            if name:
                group.name = name

        await session.commit()

async def get_group_data(group_id: int, session: AsyncSession):
    settings_result = await session.execute(select(Settings).where(Settings.group_id == group_id))
    settings = settings_result.scalars().first()
    one_time_result = await session.execute(select(OneTimeSettings).where(OneTimeSettings.group_id == group_id))
    one_time_settings = one_time_result.scalars().first()

    use_one_time = one_time_settings and one_time_settings.on_of_auto

    current_settings = one_time_settings if use_one_time else settings
    if not current_settings or not current_settings.on_of_auto or not settings.on_of_auto:
        return None

    await session.refresh(current_settings, ["group"])

    emails_result = await session.execute(select(Email).where(Email.group_id == group_id))
    emails = emails_result.scalars().all()

    received_beats_ids = set()
    for email in emails:
        if email.received_beats:
            received_beats_ids.update(email.received_beats)

    if not current_settings.quantity_beat:
        beats_result = await session.execute(
            select(Beat)
            .where(Beat.group_id == group_id)
            .where(Beat.id.notin_(received_beats_ids))
        )
        beats = beats_result.scalars().all()
    else:
        beats = []

    return current_settings, emails, beats, use_one_time





async def get_promo_codes(session: AsyncSession, offset: int = 0, limit: int = 5):
    result = await session.execute(select(PromotionalCode).offset(offset).limit(limit))
    return result.scalars().all()
async def get_promo_count(session: AsyncSession):
    result = await session.execute(select(PromotionalCode))
    return len(result.scalars().all())
async def add_promo_code(session, promo_name, duration, promo_type, promo_value, subscription_type, max_uses):
    new_promo = PromotionalCode(
        promo_name=promo_name,
        duration=duration,
        promo_type=promo_type,
        promo_info_freedays=promo_value if promo_type == 'freedays' else None,
        promo_info_discount=promo_value if promo_type == 'discount' else None,
        subscription_type=subscription_type,
        max_uses=max_uses
    )
    session.add(new_promo)
    await session.commit()
async def get_user_promo(session: AsyncSession, user_id: int):
    result = await session.execute(select(User).filter(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if user:
        promo_result = await session.execute(
            select(PromotionalCode).filter(PromotionalCode.users_used.contains(user.user_id))
        )
        user.promos_used = promo_result.scalars().all()

    return user
async def delete_promo_code(session: AsyncSession, promo_name: str):
    await session.execute(delete(PromotionalCode).where(PromotionalCode.promo_name == promo_name))
    await session.commit()
async def get_promo_info(session: AsyncSession, promo_name: str):
    result = await session.execute(select(PromotionalCode).filter(PromotionalCode.promo_name == promo_name))
    return result.scalar_one_or_none()
async def get_user_by_username_or_id(session, search_input):
    if search_input.isdigit():
        result = await session.execute(select(User).filter(User.user_id == int(search_input)))
    else:
        result = await session.execute(select(User).filter(User.username == search_input.lstrip('@')))

    return result.scalar_one_or_none()
async def get_promos_by_user(session, user_id):
    result = await session.execute(select(PromotionalCode))
    all_promos = result.scalars().all()

    promos_used = [promo for promo in all_promos if user_id in promo.users_used]
    return promos_used

