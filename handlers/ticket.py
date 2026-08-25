# -*- coding: utf-8 -*-
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
import db
from keyboards.main import (
    category_keyboard,
    department_keyboard,
    description_keyboard,
    photo_keyboard,
    preview_keyboard,
)
from keyboards.ticket import user_ticket_keyboard
from services.ticket_service import send_ticket_to_group
from states.ticket_states import NewTicket
from utils.formatters import ticket_preview_text, ticket_summary_text
from utils.helpers import user_cancel_allowed

router = Router()


async def show_ticket_preview(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(NewTicket.preview)
    await message.answer(
        ticket_preview_text(data),
        reply_markup=preview_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("murojaat"))
async def cmd_new_ticket(message: Message, state: FSMContext):
    profile = await db.get_user_profile(message.from_user.id)
    if not profile:
        await message.answer("Avval /start orqali ro'yxatdan o'ting.")
        return
    await message.answer("Qaysi bo'limdansiz?", reply_markup=department_keyboard())
    await state.set_state(NewTicket.department)


@router.callback_query(NewTicket.department, F.data.startswith("dept:"))
async def process_department(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split(":")[1])
    department = config.DEPARTMENTS[idx]
    await state.update_data(department=department)
    await callback.message.edit_text(
        f"Bo'lim: <b>{department}</b>\n\nMuammo turini tanlang:",
        reply_markup=category_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(NewTicket.category)
    await callback.answer()


@router.callback_query(NewTicket.category, F.data.startswith("cat:"))
async def process_category(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split(":")[1])
    category = config.CATEGORIES[idx]
    await state.update_data(category=category)
    await callback.message.edit_text(
        f"Muammo turi: <b>{category}</b>\n\n"
        "Muammoni qisqacha yozing (bir necha so'z bilan tavsiflang).",
        reply_markup=description_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(NewTicket.description)
    await callback.answer()


@router.message(NewTicket.description)
async def process_description(message: Message, state: FSMContext):
    description = (message.text or "").strip()
    if not description:
        await message.answer("Iltimos, muammoni matn ko'rinishida yozing.")
        return
    await state.update_data(description=description, photo_ids=[], comment="")
    await state.set_state(NewTicket.photos)
    await message.answer(
        "📎 Muammo bo'yicha rasm yoki screenshot yuboring.\n"
        "Bir nechta rasm yuborishingiz mumkin. Rasm kerak bo'lmasa /skip yozing.",
        reply_markup=photo_keyboard(back_to_preview=False),
    )


@router.callback_query(NewTicket.preview, F.data == "new:send")
async def cb_send_ticket(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    ticket_id = await db.create_ticket(
        user_id=callback.from_user.id,
        user_name=callback.from_user.full_name,
        department=data["department"],
        category=data["category"],
        description=data["description"],
        photo_file_ids=data.get("photo_ids", []),
        telegram_username=callback.from_user.username,
        phone_number=(await db.get_user_profile(callback.from_user.id))["phone_number"],
    )
    if data.get("comment"):
        await db.add_comment(ticket_id, callback.from_user.full_name, data["comment"])
    try:
        await send_ticket_to_group(callback.bot, ticket_id)
    except Exception as exc:
        logging.error(f"Guruhga yuborib bo'lmadi: {exc}")
    await callback.message.edit_text(
        f"✅ Murojaatingiz qabul qilindi. Raqami: <b>#{ticket_id}</b>\n"
        "IT bo'limi tez orada ko'rib chiqadi.",
        reply_markup=user_ticket_keyboard(ticket_id, allow_cancel=True),
        parse_mode="HTML",
    )
    await state.clear()
    await callback.answer("Yuborildi")


@router.callback_query(F.data == "new:cancel")
async def cb_cancel_new_ticket(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Murojaat yaratish bekor qilindi.")
    await callback.answer()


@router.callback_query(NewTicket.category, F.data == "new:back_dept")
async def cb_back_department(callback: CallbackQuery, state: FSMContext):
    await state.set_state(NewTicket.department)
    await callback.message.edit_text(
        "Qaysi bo'limdansiz?",
        reply_markup=department_keyboard(),
    )
    await callback.answer()


@router.callback_query(NewTicket.description, F.data == "new:back_category")
async def cb_back_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(NewTicket.category)
    await callback.message.edit_text(
        "Muammo turini tanlang:",
        reply_markup=category_keyboard(),
    )
    await callback.answer()


@router.message(Command("mening_murojaatlarim"))
async def cmd_my_tickets(message: Message):
    tickets = await db.get_user_tickets(message.from_user.id)
    if not tickets:
        await message.answer("Sizda hozircha murojaatlar yo'q. /murojaat orqali yangi yuborishingiz mumkin.")
        return

    lines = ["<b>Sizning murojaatlaringiz:</b>\n"]
    keyboard_rows = []
    for ticket in tickets:
        status_label = db.STATUS_LABELS.get(ticket["status"], ticket["status"])
        lines.append(
            f"#{ticket['id']} — {ticket['category']} — "
            f"{status_label} ({ticket['created_at']})"
        )
        row = [
            {"text": f"💬 #{ticket['id']} izoh", "callback_data": f"usercomment:{ticket['id']}"},
            {"text": f"👀 #{ticket['id']}", "callback_data": f"userview:{ticket['id']}"},
        ]
        if user_cancel_allowed(ticket):
            row.append({"text": f"❌ #{ticket['id']}", "callback_data": f"usercancel:{ticket['id']}"})
        keyboard_rows.append(row)

    await message.answer(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(**button) for button in row]
                for row in keyboard_rows
            ]
        ),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("userview:"))
async def cb_user_view_ticket(callback: CallbackQuery):
    ticket_id = int(callback.data.split(":")[1])
    ticket = await db.get_ticket(ticket_id)
    if not ticket or ticket["user_id"] != callback.from_user.id:
        await callback.answer("Bu murojaat sizga tegishli emas.", show_alert=True)
        return
    comments = await db.get_comments(ticket_id)
    attachments = await db.get_attachments(ticket_id)
    ticket["photo_count"] = len(attachments)
    await callback.message.answer(ticket_summary_text(ticket, comments), parse_mode="HTML")
    await callback.answer()
