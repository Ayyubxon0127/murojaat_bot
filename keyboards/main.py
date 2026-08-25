# -*- coding: utf-8 -*-
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import config
from utils.helpers import chunk_buttons


def department_keyboard() -> InlineKeyboardMarkup:
    rows = chunk_buttons(config.DEPARTMENTS, "dept")
    rows.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="new:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def category_keyboard() -> InlineKeyboardMarkup:
    rows = chunk_buttons(config.CATEGORIES, "cat")
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="new:back_dept")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def description_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="new:back_category")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="new:cancel")],
    ])


def photo_keyboard(back_to_preview: bool = False) -> InlineKeyboardMarkup:
    back_callback = "new:back_preview" if back_to_preview else "new:back_description"
    skip_text = "⏭ Tayyor" if back_to_preview else "⏭ O'tkazib yuborish"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back_callback)],
        [InlineKeyboardButton(text=skip_text, callback_data="new:skip_photos")],
    ])


def preview_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data="new:edit_description"),
            InlineKeyboardButton(text="📎 Rasm qo'shish", callback_data="new:add_photo"),
        ],
        [InlineKeyboardButton(text="💬 Izoh qo'shish", callback_data="new:add_comment")],
        [
            InlineKeyboardButton(text="✅ Yuborish", callback_data="new:send"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="new:cancel"),
        ],
    ])


def back_preview_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="new:back_preview")],
    ])
