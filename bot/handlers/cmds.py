from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.keyboards.builders import build_invoice_keyboard
from db import orm_queries as db
from sqlalchemy.ext.asyncio import AsyncSession
from bot.utils.payments.client import cp

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    await db.add_user(session, message.from_user.id)
    await message.answer("Hello")

@router.message(Command("pay"))
async def cmd_pay(message: Message, session: AsyncSession):
    await db.add_user(session, message.from_user.id)
    # CryptoPay polling uses this value to associate the invoice with its owner.
    invoice = await cp.create_invoice(
        asset="USDT",
        amount=0.01,
        description="Пополнение баланса",
        payload=str(message.from_user.id),
    )
    invoice.poll(user_id=message.from_user.id)
    await message.answer(
        f"Счёт на оплату: {invoice.amount} {invoice.asset}",
        reply_markup=build_invoice_keyboard(invoice),
    )
