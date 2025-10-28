from sqlalchemy import String, BigInteger, DateTime, Column, Integer, Boolean, ForeignKey, PickleType, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.ext.mutable import MutableList
from datetime import datetime
import logging


from config import DB_URL

# logging.basicConfig()
# logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

engine = create_async_engine(url=DB_URL)
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id = mapped_column(BigInteger, unique=True)
    username: Mapped[str] = mapped_column(String(255))
    gmail: Mapped[str] = mapped_column(String(255), nullable=True)
    access_token: Mapped[str] = mapped_column(String(255), nullable=True)
    refresh_token: Mapped[str] = mapped_column(String(255), nullable=True)
    subscription: Mapped[str] = mapped_column(String(50), default='неактивна')
    password: Mapped[str] = mapped_column(String(255), default='Неуказано')
    subscription_start = Column(DateTime, default=None)
    subscription_day = Column(Integer, default=0)
    mails_per_day: Mapped[int] = mapped_column(Integer, default=0)
    extra_mail: Mapped[int] = mapped_column(Integer, default=0)
    block: Mapped[bool] = mapped_column(Boolean, default=False)
    language: Mapped[int] = mapped_column(Integer, default=0)
    active_promo_code: Mapped[str] = mapped_column(String, nullable=True)
    promo_expiration: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    notified_one_day: Mapped[bool] = mapped_column(Boolean, default=False)
    refresh_to_day: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    referrals: Mapped[int] = mapped_column(Integer, default=0)
    used_referral: Mapped[bool] = mapped_column(Boolean, default=False)
    referrer_id: Mapped[int] = mapped_column(Integer, nullable=True)
    referral_discount_expire: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    referral_discount: Mapped[int] = mapped_column(Integer, default=0)
    notifications_reg: Mapped[bool] = mapped_column(Boolean, default=True)
    notifications_sub: Mapped[bool] = mapped_column(Boolean, default=True)
    groups = relationship(
        "Group",
        back_populates="user",
        cascade="all, delete-orphan"  
    )

class PromotionalCode(Base):
    __tablename__ = 'promotional_code'

    id: Mapped[int] = mapped_column(primary_key=True)
    promo_name: Mapped[str] = mapped_column(String, unique=True)
    duration: Mapped[int] = mapped_column(Integer)
    promo_info_freedays: Mapped[int] = mapped_column(Integer, nullable=True)
    promo_info_discount: Mapped[int] = mapped_column(Integer, nullable=True)
    promo_type = Column(String)
    subscription_type: Mapped[str] = mapped_column(String)
    max_uses: Mapped[int] = mapped_column(Integer)
    users_used: Mapped[list] = Column(MutableList.as_mutable(PickleType), default=[])

class Group(Base):
    __tablename__ = 'groups'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id = mapped_column(BigInteger, ForeignKey("users.user_id"))
    name: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="groups")
    emails = relationship("Email", back_populates="group", cascade="all, delete-orphan")
    beats = relationship("Beat", back_populates="group", cascade="all, delete-orphan")
    settings = relationship("Settings", back_populates="group", uselist=False, cascade="all, delete-orphan")
    one_time_settings = relationship("OneTimeSettings", back_populates="group", uselist=False)


class Settings(Base):
    __tablename__ = 'settings'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id = mapped_column(BigInteger, ForeignKey("users.user_id"))
    group_id = mapped_column(Integer, ForeignKey("groups.id"))
    subject: Mapped[str] = mapped_column(String(255), default="Без темы")
    message: Mapped[str] = mapped_column(String(500), default="Без текста")
    send_time = Column(DateTime, nullable=True)
    quantity_beat: Mapped[int] = mapped_column(Integer, default=2)
    on_of_auto: Mapped[bool] = mapped_column(Boolean, default=False)
    periodicity: Mapped[str] = mapped_column(String(255), default='Ежедневно')
    last_sent_date = Column(DateTime, nullable=True)
    interval: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    group = relationship("Group", back_populates="settings")

class OneTimeSettings(Base):
    __tablename__ = 'one_time_settings'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id = mapped_column(BigInteger, ForeignKey("users.user_id"))
    group_id = Column(Integer, ForeignKey('groups.id'))
    subject: Mapped[str] = mapped_column(String(255), default="Без темы")
    message: Mapped[str] = mapped_column(String(500), default="Без текста")
    send_time = Column(DateTime, nullable=True)
    quantity_beat = Column(Boolean, default=True)
    on_of_auto = Column(Boolean, default=False)
    interval: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    group = relationship("Group", back_populates="one_time_settings")


class Email(Base):
    __tablename__ = 'emails'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id = mapped_column(BigInteger)
    email: Mapped[str] = mapped_column(String(255))
    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    group_id = mapped_column(Integer, ForeignKey("groups.id"), nullable=True)
    received_beats = Column(MutableList.as_mutable(PickleType), default=[])
    flags: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    group = relationship("Group", back_populates="emails")

class Beat(Base):
    __tablename__ = 'beats'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id = mapped_column(BigInteger)
    file_id: Mapped[str] = mapped_column(String(255))
    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    group_id = mapped_column(Integer, ForeignKey("groups.id"), nullable=True)
    file_format: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    group = relationship("Group", back_populates="beats")


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
