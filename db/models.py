from sqlalchemy import BigInteger, FLOAT, String, TEXT, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.sql import func
from datetime import datetime

class Base(DeclarativeBase):
    ...

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    active: Mapped[int] = mapped_column(Integer, default=1)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Sponsor(Base):
    __tablename__ = "sponsors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(BigInteger)
    channel_name: Mapped[str] = mapped_column(String(255), default="Канал")
    target_subs: Mapped[int] = mapped_column(Integer)
    current_subs: Mapped[int] = mapped_column(Integer, default=0)
    invite_link: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class UserSponsor(Base):
    __tablename__ = "user_sponsors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"))
    sponsor_id: Mapped[int] = mapped_column(Integer, ForeignKey("sponsors.id", ondelete="CASCADE"))
