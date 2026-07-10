from db.models import User
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

async def add_user(session: AsyncSession, user_id):
    user = await session.scalar(select(User).where(User.user_id == user_id))
    if not user:
        session.add(User(user_id=user_id))
        await session.commit()

async def get_user(session: AsyncSession, user_id) -> User | None:
    return await session.scalar(select(User).where(User.user_id == user_id))

async def set_active(session: AsyncSession, user_id, status=1):
    user = await session.scalar(select(User).where(User.user_id == user_id))
    if user:
        user.active = status
        await session.commit()

async def get_admin_stats(session: AsyncSession):
    # For a simple template, we'll return total users and calculate new users based on a naive approach or just dummy data for now if we can't easily query dates without raw sql in simple sqlite.
    # But since we added created_at, we can query it.
    from datetime import datetime, timezone, timedelta
    
    total = await session.scalar(select(func.count(User.user_id)))
    
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    new_today = await session.scalar(select(func.count(User.user_id)).where(User.created_at >= today_start))
    
    return {
        'total_users': total or 0,
        'new_users_today': new_today or 0
    }

async def get_admin_users_stats(session: AsyncSession):
    from datetime import datetime, timezone, timedelta
    
    total = await session.scalar(select(func.count(User.user_id)))
    active_users = await session.scalar(select(func.count(User.user_id)).where(User.active == 1, User.is_blocked == False))
    
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    new_today = await session.scalar(select(func.count(User.user_id)).where(User.created_at >= today_start))
    
    week_start = today_start - timedelta(days=7)
    new_week = await session.scalar(select(func.count(User.user_id)).where(User.created_at >= week_start))
    
    return {
        'total_users': total or 0,
        'new_users_today': new_today or 0,
        'new_users_week': new_week or 0,
        'active_users': active_users or 0
    }

async def set_blocked(session: AsyncSession, user_id: int, is_blocked: bool):
    user = await session.scalar(select(User).where(User.user_id == user_id))
    if user:
        user.is_blocked = is_blocked
        await session.commit()

async def get_all_active_user_ids(session: AsyncSession):
    users = await session.scalars(select(User.user_id).where(User.active == 1, User.is_blocked == False))
    return list(users)