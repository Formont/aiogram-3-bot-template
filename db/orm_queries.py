from db.models import User
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

async def add_user(session: AsyncSession, user_id):
    user = await session.scalar(select(User).where(User.user_id==user_id))
    if not user:
        session.add(User(user_id=user_id))
        await session.commit()

async def get_user(session: AsyncSession, user_id) -> User:
    query = select(User).where(User.user_id==user_id)
    result = await session.execute(query)
    return result.scalar()

async def set_active(session: AsyncSession, user_id, status=1):
    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalars().first()
    user.active = status
    await session.commit()