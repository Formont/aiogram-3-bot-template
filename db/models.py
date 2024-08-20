from sqlalchemy import INTEGER, FLOAT, String, TEXT
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

class Base(DeclarativeBase):
    ...

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(INTEGER, primary_key=True)
    