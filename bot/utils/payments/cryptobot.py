from aiogram import Bot
from datetime import datetime, timezone

from bot.utils.payments.client import cp
from db import orm_queries as db
from db.engine import session_maker


@cp.invoice_paid()
async def handle_invoice_paid(invoice, user_id: int, bot: Bot) -> None:
    """Persist a paid invoice once and notify its owner."""
    try:
        owner_id = int(user_id or invoice.payload)
    except (TypeError, ValueError):
        # Without an owner, do not create an unlinked payment record.
        return

    async with session_maker() as session:
        created = await db.add_payment(
            session=session,
            transaction_id=str(invoice.invoice_id),
            user_id=owner_id,
            method="cryptobot",
            paid_at=invoice.paid_at or datetime.now(timezone.utc),
            amount=invoice.amount,
            currency=str(invoice.asset or invoice.paid_asset or ""),
        )

    if created:
        await bot.send_message(owner_id, "Платёж получен и сохранён.")
