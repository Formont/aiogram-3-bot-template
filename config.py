import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).with_name(".env"))

TOKEN = os.getenv("BOT_TOKEN", "").strip()
CB_TOKEN = os.getenv("CRYPTO_BOT_TOKEN", "").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///database.db").strip()
ADMINS = frozenset(
    int(value.strip())
    for value in os.getenv("ADMIN_IDS", "").split(",")
    if value.strip()
)
CONTACTS = os.getenv("CONTACTS", "").strip() or "Напишите администратору бота."
