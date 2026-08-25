# -*- coding: utf-8 -*-
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from handlers.ticket import show_ticket_preview
from keyboards.main import back_preview_keyboard
from states.ticket_states import NewTicket

router = Router()


@router.callback_query(NewTicket.preview, F.data == "new:edit_description")
async def cb_edit_description(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(NewTicket.edit_description)
    await callback.message.edit_text(
        f"Joriy tavsif:\n{data['description']}\n\nYangi tavsifni yozing:",
        reply_markup=back_preview_keyboard(),
    )
    await callback.answer()


@router.message(NewTicket.edit_description)
async def process_edit_description(message: Message, state: FSMContext):
    description = (message.text or "").strip()
    if not description:
        await message.answer("Iltimos, tavsifni matn ko'rinishida yozing.")
        return
    await state.update_data(description=description)
    await show_ticket_preview(message, state)


@router.callback_query(NewTicket.preview, F.data == "new:back_preview")
async def cb_back_preview(callback: CallbackQuery, state: FSMContext):
    await show_ticket_preview(callback.message, state)
    await callback.answer()


@router.callback_query(NewTicket.edit_description, F.data == "new:back_preview")
async def cb_back_preview_from_edit(callback: CallbackQuery, state: FSMContext):
    await show_ticket_preview(callback.message, state)
    await callback.answer()
