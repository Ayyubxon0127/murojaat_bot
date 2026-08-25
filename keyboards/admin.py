# -*- coding: utf-8 -*-
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import config
import db
from utils.helpers import chunk_buttons


def quick_resolution_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    rows = chunk_buttons(config.QUICK_RESOLUTIONS, f"quickres:{ticket_id}")
    rows.append([InlineKeyboardButton(text="✍️ O'zim yozaman", callback_data=f"customres:{ticket_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def export_status_labels() -> dict:
    return {
        db.STATUS_NEW: "Yangi",
        db.STATUS_IN_PROGRESS: "Jarayonda",
        db.STATUS_DONE: "Bajarildi",
        db.STATUS_CANCELLED: "Bekor qilindi",
    }
