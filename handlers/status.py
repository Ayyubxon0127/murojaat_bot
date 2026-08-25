# -*- coding: utf-8 -*-
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import config
import db
from keyboards.admin import quick_resolution_keyboard
from keyboards.ticket import user_cancel_confirmation_keyboard, user_ticket_keyboard
from services.notification import notify_user
from services.ticket_service import close_ticket, refresh_group_message
from states.ticket_states import ResolveTicket
from utils.formatters import ticket_summary_text
from utils.helpers import extract_ticket_id, is_staff, user_cancel_allowed

router = Router()


@router.callback_query(F.data.startswith("assign:"))
async def cb_assign(callback: CallbackQuery):
    if not is_staff(callback.from_user.id):
        await callback.answer("Bu amal faqat IT xodimlari uchun.", show_alert=True)
        return
    ticket_id = extract_ticket_id(callback.data)
    await db.assign_ticket(ticket_id, callback.from_user.id, callback.from_user.full_name)
    await db.update_status(ticket_id, db.STATUS_IN_PROGRESS)
    ticket = await db.get_ticket(ticket_id)
    await refresh_group_message(callback.bot, ticket_id)
    await notify_user(
        callback.bot,
        ticket["user_id"],
        f"🔄 Murojaatingiz #{ticket_id} jarayonga olindi.\nMas'ul: {callback.from_user.full_name}",
    )
    await callback.answer("Siz mas'ul etib tayinlandingiz.")


@router.callback_query(F.data.startswith("view:"))
async def cb_view_ticket(callback: CallbackQuery):
    if not is_staff(callback.from_user.id):
        await callback.answer("Bu amal faqat IT xodimlari uchun.", show_alert=True)
        return
    ticket_id = extract_ticket_id(callback.data)
    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        await callback.answer("Murojaat topilmadi.", show_alert=True)
        return
    comments = await db.get_comments(ticket_id)
    attachments = await db.get_attachments(ticket_id)
    ticket["photo_count"] = len(attachments)
    await callback.message.answer(ticket_summary_text(ticket, comments), parse_mode="HTML")
    for index, file_id in enumerate(attachments, start=1):
        await callback.message.answer_photo(file_id, caption=f"📎 Rasm {index}/{len(attachments)}")
    await callback.answer()


@router.callback_query(F.data.startswith("progress:"))
async def cb_progress(callback: CallbackQuery):
    if not is_staff(callback.from_user.id):
        await callback.answer("Bu amal faqat IT xodimlari uchun.", show_alert=True)
        return
    ticket_id = extract_ticket_id(callback.data)
    await db.update_status(ticket_id, db.STATUS_IN_PROGRESS)
    ticket = await db.get_ticket(ticket_id)
    await refresh_group_message(callback.bot, ticket_id)
    await notify_user(callback.bot, ticket["user_id"], f"🔄 Murojaatingiz #{ticket_id} jarayonda.")
    await callback.answer("Status: Jarayonda")


@router.callback_query(F.data.startswith("done:"))
async def cb_done(callback: CallbackQuery):
    if not is_staff(callback.from_user.id):
        await callback.answer("Bu amal faqat IT xodimlari uchun.", show_alert=True)
        return
    ticket_id = extract_ticket_id(callback.data)
    await callback.answer()
    await callback.message.answer(
        f"Murojaat #{ticket_id} uchun nima qilinganini tanlang yoki o'zingiz yozing:",
        reply_markup=quick_resolution_keyboard(ticket_id),
    )


@router.callback_query(F.data.startswith("quickres:"))
async def cb_quick_resolution(callback: CallbackQuery):
    if not is_staff(callback.from_user.id):
        await callback.answer("Bu amal faqat IT xodimlari uchun.", show_alert=True)
        return
    _, ticket_id, idx = callback.data.split(":")
    ticket_id = int(ticket_id)
    comment = config.QUICK_RESOLUTIONS[int(idx)]
    await close_ticket(callback.bot, ticket_id, comment)
    await callback.message.edit_text(f"✅ Murojaat #{ticket_id} yopildi.\nIzoh: {comment}")
    await callback.answer()


@router.callback_query(F.data.startswith("customres:"))
async def cb_custom_resolution_start(callback: CallbackQuery, state: FSMContext):
    if not is_staff(callback.from_user.id):
        await callback.answer("Bu amal faqat IT xodimlari uchun.", show_alert=True)
        return
    ticket_id = extract_ticket_id(callback.data)
    await state.update_data(resolve_ticket_id=ticket_id)
    await state.set_state(ResolveTicket.waiting_comment)
    await callback.message.answer(f"Murojaat #{ticket_id} uchun nima qilinganini yozing:")
    await callback.answer()


@router.message(ResolveTicket.waiting_comment)
async def process_custom_resolution(message: Message, state: FSMContext):
    data = await state.get_data()
    ticket_id = data["resolve_ticket_id"]
    comment = message.text
    await close_ticket(message.bot, ticket_id, comment)
    await message.answer(f"✅ Murojaat #{ticket_id} yopildi.\nIzoh: {comment}")
    await state.clear()


@router.callback_query(F.data.startswith("cancel:"))
async def cb_cancel(callback: CallbackQuery):
    if not is_staff(callback.from_user.id):
        await callback.answer("Bu amal faqat IT xodimlari uchun.", show_alert=True)
        return
    ticket_id = extract_ticket_id(callback.data)
    await db.update_status(ticket_id, db.STATUS_CANCELLED, closed=True)
    ticket = await db.get_ticket(ticket_id)
    await refresh_group_message(callback.bot, ticket_id)
    await notify_user(callback.bot, ticket["user_id"], f"❌ Murojaatingiz #{ticket_id} bekor qilindi.")
    await callback.answer("Bekor qilindi.")


@router.callback_query(F.data.startswith("reopen:"))
async def cb_reopen(callback: CallbackQuery):
    if not is_staff(callback.from_user.id):
        await callback.answer("Bu amal faqat IT xodimlari uchun.", show_alert=True)
        return
    ticket_id = extract_ticket_id(callback.data)
    await db.update_status(ticket_id, db.STATUS_IN_PROGRESS)
    ticket = await db.get_ticket(ticket_id)
    await refresh_group_message(callback.bot, ticket_id)
    await notify_user(
        callback.bot,
        ticket["user_id"],
        f"🔓 Murojaatingiz #{ticket_id} qayta ochildi, ko'rib chiqilmoqda.",
    )
    await callback.answer("Qayta ochildi.")


@router.callback_query(F.data.startswith("usercancel:"))
async def cb_user_cancel_start(callback: CallbackQuery):
    ticket_id = extract_ticket_id(callback.data)
    ticket = await db.get_ticket(ticket_id)
    if not ticket or ticket["user_id"] != callback.from_user.id:
        await callback.answer("Bu murojaat sizga tegishli emas.", show_alert=True)
        return
    if not user_cancel_allowed(ticket):
        await callback.answer(
            "Bekor qilish muddati tugagan yoki murojaat jarayonga olingan.",
            show_alert=True,
        )
        return
    await callback.message.answer(
        f"Murojaat #{ticket_id}ni bekor qilmoqchimisiz?",
        reply_markup=user_cancel_confirmation_keyboard(ticket_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("usercancel_back:"))
async def cb_user_cancel_back(callback: CallbackQuery):
    await callback.message.edit_text("Bekor qilish amalga oshirilmadi.")
    await callback.answer()


@router.callback_query(F.data.startswith("usercancel_confirm:"))
async def cb_user_cancel_confirm(callback: CallbackQuery):
    ticket_id = extract_ticket_id(callback.data)
    ticket = await db.get_ticket(ticket_id)
    if not ticket or ticket["user_id"] != callback.from_user.id:
        await callback.answer("Bu murojaat sizga tegishli emas.", show_alert=True)
        return
    if not user_cancel_allowed(ticket):
        await callback.answer("Bekor qilish muddati tugagan.", show_alert=True)
        return
    await db.update_status(ticket_id, db.STATUS_CANCELLED, closed=True)
    await refresh_group_message(callback.bot, ticket_id)
    await callback.message.edit_text(
        f"❌ Murojaat #{ticket_id} bekor qilindi.",
        reply_markup=user_ticket_keyboard(ticket_id),
    )
    await callback.answer("Bekor qilindi.")
