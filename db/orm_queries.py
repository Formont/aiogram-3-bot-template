from db.models import User, Sponsor, UserSponsor
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

async def add_sponsor(session: AsyncSession, channel_id: int, channel_name: str, target_subs: int, invite_link: str):
    sponsor = Sponsor(channel_id=channel_id, channel_name=channel_name, target_subs=target_subs, invite_link=invite_link)
    session.add(sponsor)
    await session.commit()
    return sponsor

async def get_active_sponsors(session: AsyncSession) -> list[Sponsor]:
    result = await session.execute(select(Sponsor).where(Sponsor.is_active == True))
    return list(result.scalars().all())

async def get_all_sponsors(session: AsyncSession) -> list[Sponsor]:
    result = await session.execute(select(Sponsor))
    return list(result.scalars().all())

async def get_active_sponsor_by_channel(session: AsyncSession, channel_id: int) -> Sponsor | None:
    return await session.scalar(select(Sponsor).where(Sponsor.channel_id == channel_id, Sponsor.is_active == True))

async def get_sponsor(session: AsyncSession, sponsor_id: int) -> Sponsor | None:
    return await session.scalar(select(Sponsor).where(Sponsor.id == sponsor_id))

async def delete_sponsor(session: AsyncSession, sponsor_id: int):
    sponsor = await session.scalar(select(Sponsor).where(Sponsor.id == sponsor_id))
    if sponsor:
        await session.delete(sponsor)
        await session.commit()

async def check_user_sponsor_reward(session: AsyncSession, user_id: int, sponsor_id: int) -> bool:
    # Check if user already rewarded this sponsor
    existing = await session.scalar(
        select(UserSponsor).where(UserSponsor.user_id == user_id, UserSponsor.sponsor_id == sponsor_id)
    )
    if existing:
        return False
        
    # Record the reward
    session.add(UserSponsor(user_id=user_id, sponsor_id=sponsor_id))
    
    # Increment current_subs
    sponsor = await session.scalar(select(Sponsor).where(Sponsor.id == sponsor_id))
    if sponsor:
        sponsor.current_subs += 1
        if sponsor.current_subs >= sponsor.target_subs:
            sponsor.is_active = False
            
    await session.commit()
    return True