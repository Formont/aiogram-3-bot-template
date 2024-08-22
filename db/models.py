from sqlalchemy import BigInteger, FLOAT, String, TEXT, Integer
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

class Base(DeclarativeBase):
    ...

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    active: Mapped[int] = mapped_column(Integer, default=1)
