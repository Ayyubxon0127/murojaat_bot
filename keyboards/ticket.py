# -*- coding: utf-8 -*-
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import db


def group_ticket_keyboard(ticket_id: int, status: str) -> InlineKeyboardMarkup:
    rows = [[
        InlineKeyboardButton(text="👀 Ko'rib chiqish", callback_data=f"view:{ticket_id}"),
        InlineKeyboardButton(text="💬 Izoh", callback_data=f"comment:{ticket_id}"),
    ]]
    if status == db.STATUS_NEW:
        rows.append([
            InlineKeyboardButton(text="🙋 Menga tayinla", callback_data=f"assign:{ticket_id}"),
            InlineKeyboardButton(text="🔄 Jarayonda", callback_data=f"progress:{ticket_id}"),
        ])
        rows.append([
            InlineKeyboardButton(text="✅ Bajarildi", callback_data=f"done:{ticket_id}"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"cancel:{ticket_id}"),
        ])
    elif status == db.STATUS_IN_PROGRESS:
        rows.append([
            InlineKeyboardButton(text="✅ Bajarildi", callback_data=f"done:{ticket_id}"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"cancel:{ticket_id}"),
        ])
    elif status in (db.STATUS_DONE, db.STATUS_CANCELLED):
        rows.append([
            InlineKeyboardButton(text="🔓 Qayta ochish", callback_data=f"reopen:{ticket_id}"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def user_ticket_keyboard(ticket_id: int, allow_cancel: bool = False) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="💬 Izoh qo'shish", callback_data=f"usercomment:{ticket_id}")]]
    if allow_cancel:
        rows.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"usercancel:{ticket_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def user_cancel_confirmation_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="✅ Ha, bekor qilish",
            callback_data=f"usercancel_confirm:{ticket_id}",
        ),
        InlineKeyboardButton(text="⬅️ Yo'q", callback_data=f"usercancel_back:{ticket_id}"),
    ]])
