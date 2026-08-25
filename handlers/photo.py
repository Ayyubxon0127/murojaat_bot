# -*- coding: utf-8 -*-
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from handlers.ticket import show_ticket_preview
from keyboards.main import description_keyboard, photo_keyboard
from states.ticket_states import NewTicket

router = Router()


@router.message(NewTicket.photos, F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_ids = list(data.get("photo_ids", []))
    file_id = message.photo[-1].file_id
    if file_id not in photo_ids:
        photo_ids.append(file_id)
    await state.update_data(photo_ids=photo_ids)
    await message.answer(f"📎 Rasm qo'shildi ({len(photo_ids)} ta). Yana yuboring yoki /skip yozing.")


@router.message(NewTicket.photos, Command("skip"))
async def process_skip_photos(message: Message, state: FSMContext):
    await show_ticket_preview(message, state)


@router.message(NewTicket.photos)
async def process_invalid_photo_step(message: Message):
    await message.answer("Iltimos, rasm yuboring yoki rasmlarsiz davom etish uchun /skip yozing.")


@router.callback_query(NewTicket.photos, F.data == "new:skip_photos")
async def cb_skip_photos(callback: CallbackQuery, state: FSMContext):
    await show_ticket_preview(callback.message, state)
    await callback.answer()


@router.callback_query(NewTicket.photos, F.data == "new:back_description")
async def cb_back_description(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(NewTicket.description)
    await callback.message.edit_text(
        f"Muammo turi: <b>{data['category']}</b>\n\nMuammoni qisqacha yozing:",
        reply_markup=description_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(NewTicket.preview, F.data == "new:add_photo")
async def cb_add_photo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(NewTicket.photos)
    await callback.message.edit_text(
        "📎 Rasm yuboring. Bir nechta rasm yuborishingiz mumkin.\nTugatgach /skip yozing.",
        reply_markup=photo_keyboard(back_to_preview=True),
    )
    await callback.answer()


@router.callback_query(NewTicket.photos, F.data == "new:back_preview")
async def cb_back_preview_from_photos(callback: CallbackQuery, state: FSMContext):
    await show_ticket_preview(callback.message, state)
    await callback.answer()
