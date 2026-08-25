# -*- coding: utf-8 -*-
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import db
from handlers.ticket import show_ticket_preview
from keyboards.main import back_preview_keyboard
from services.notification import notify_user
from services.ticket_service import refresh_group_message
from states.ticket_states import AddComment, NewTicket, UserComment
from utils.helpers import extract_ticket_id, is_staff

router = Router()


@router.callback_query(NewTicket.preview, F.data == "new:add_comment")
async def cb_add_ticket_comment(callback: CallbackQuery, state: FSMContext):
    await state.set_state(NewTicket.comment)
    await callback.message.edit_text(
        "Murojaatga qo'shiladigan izohni yozing:",
        reply_markup=back_preview_keyboard(),
    )
    await callback.answer()


@router.message(NewTicket.comment)
async def process_ticket_comment(message: Message, state: FSMContext):
    comment = (message.text or "").strip()
    if not comment:
        await message.answer("Iltimos, izohni matn ko'rinishida yozing.")
        return
    await state.update_data(comment=comment)
    await show_ticket_preview(message, state)


@router.callback_query(NewTicket.comment, F.data == "new:back_preview")
async def cb_back_preview_from_comment(callback: CallbackQuery, state: FSMContext):
    await show_ticket_preview(callback.message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("comment:"))
async def cb_add_comment_start(callback: CallbackQuery, state: FSMContext):
    if not is_staff(callback.from_user.id):
        await callback.answer("Bu amal faqat IT xodimlari uchun.", show_alert=True)
        return
    ticket_id = extract_ticket_id(callback.data)
    await state.update_data(comment_ticket_id=ticket_id)
    await state.set_state(AddComment.waiting_comment)
    await callback.message.answer(f"Murojaat #{ticket_id} uchun izohingizni yozing:")
    await callback.answer()


@router.message(AddComment.waiting_comment)
async def process_add_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    ticket_id = data["comment_ticket_id"]
    await db.add_comment(ticket_id, message.from_user.full_name, message.text)
    await refresh_group_message(message.bot, ticket_id)
    ticket = await db.get_ticket(ticket_id)
    await notify_user(
        message.bot,
        ticket["user_id"],
        f"💬 Murojaatingiz #{ticket_id} bo'yicha izoh: {message.text}",
    )
    await message.answer("Izoh qo'shildi.")
    await state.clear()


@router.callback_query(F.data.startswith("usercomment:"))
async def cb_user_comment_start(callback: CallbackQuery, state: FSMContext):
    if callback.data == "usercomment:cancel":
        await state.clear()
        await callback.message.edit_text("Izoh qo'shish bekor qilindi.")
        await callback.answer()
        return
    ticket_id = extract_ticket_id(callback.data)
    ticket = await db.get_ticket(ticket_id)
    if not ticket or ticket["user_id"] != callback.from_user.id:
        await callback.answer("Bu murojaat sizga tegishli emas.", show_alert=True)
        return
    await state.update_data(user_comment_ticket_id=ticket_id)
    await state.set_state(UserComment.waiting_comment)
    await callback.message.answer(
        f"Murojaat #{ticket_id} uchun izohingizni yozing:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="usercomment:cancel")],
        ]),
    )
    await callback.answer()


@router.callback_query(UserComment.waiting_comment, F.data == "usercomment:cancel")
async def cb_user_comment_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Izoh qo'shish bekor qilindi.")
    await callback.answer()


@router.message(UserComment.waiting_comment)
async def process_user_comment(message: Message, state: FSMContext):
    comment = (message.text or "").strip()
    if not comment:
        await message.answer("Iltimos, izohni matn ko'rinishida yozing.")
        return
    data = await state.get_data()
    ticket_id = data["user_comment_ticket_id"]
    ticket = await db.get_ticket(ticket_id)
    if not ticket or ticket["user_id"] != message.from_user.id:
        await message.answer("Murojaat topilmadi.")
        await state.clear()
        return
    await db.add_comment(ticket_id, message.from_user.full_name, comment)
    await refresh_group_message(message.bot, ticket_id)
    await message.answer(f"💬 Murojaat #{ticket_id} uchun izoh qo'shildi.")
    await state.clear()
