# -*- coding: utf-8 -*-
from datetime import datetime

from aiogram.types import InlineKeyboardButton

import config
import db


def is_staff(user_id: int) -> bool:
    return user_id in config.IT_STAFF_IDS


def chunk_buttons(items, prefix, per_row=1):
    rows = []
    row = []
    for i, item in enumerate(items):
        row.append(InlineKeyboardButton(text=item, callback_data=f"{prefix}:{i}"))
        if len(row) == per_row:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return rows


def extract_ticket_id(callback_data: str) -> int:
    return int(callback_data.split(":")[1])


def user_cancel_allowed(ticket: dict) -> bool:
    if ticket["status"] != db.STATUS_NEW:
        return False
    created = datetime.strptime(ticket["created_at"], "%Y-%m-%d %H:%M:%S")
    elapsed = (datetime.now() - created).total_seconds() / 60
    return elapsed <= config.USER_CANCEL_WINDOW_MINUTES
