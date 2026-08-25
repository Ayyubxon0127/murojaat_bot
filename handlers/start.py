# -*- coding: utf-8 -*-
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

import db
from keyboards.main import phone_keyboard
from states.ticket_states import Registration
from utils.helpers import is_staff

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    profile = await db.get_user_profile(message.from_user.id)
    if not profile:
        await state.set_state(Registration.full_name)
        await message.answer("Ro'yxatdan o'tish uchun ism-familiyangizni kiriting:")
        return
    await _welcome(message)


async def _welcome(message: Message):
    text = (
        "Assalomu alaykum! Bu — IT bo'limiga murojaat yuborish boti.\n\n"
        "📩 /murojaat — yangi murojaat yuborish\n"
        "📋 /mening_murojaatlarim — mening murojaatlarim ro'yxati\n"
        "👤 /profil — ism-familiya va telefonni yangilash\n"
    )
    if is_staff(message.from_user.id):
        text += (
            "\n<b>IT xodimi buyruqlari:</b>\n"
            "📊 /statistika — umumiy statistika\n"
            "📥 /export — Excel hisobot yuklab olish\n"
        )
    await message.answer(text, parse_mode="HTML")


@router.message(Registration.full_name)
async def registration_name(message: Message, state: FSMContext):
    full_name = (message.text or "").strip()
    if len(full_name) < 3:
        await message.answer("Iltimos, ism-familiyangizni to'liq kiriting.")
        return
    await state.update_data(full_name=full_name)
    await state.set_state(Registration.phone)
    await message.answer(
        "Telefon raqamingizni yuboring:",
        reply_markup=phone_keyboard(),
    )


@router.message(Registration.phone, F.contact)
async def registration_phone(message: Message, state: FSMContext):
    if message.contact.user_id and message.contact.user_id != message.from_user.id:
        await message.answer("Iltimos, o'zingizning telefon raqamingizni yuboring.")
        return
    data = await state.get_data()
    await db.save_user_profile(
        message.from_user.id,
        data["full_name"],
        message.from_user.username,
        message.contact.phone_number,
    )
    await state.clear()
    await message.answer("✅ Ma'lumotlaringiz saqlandi.", reply_markup=ReplyKeyboardRemove())
    await _welcome(message)


@router.message(Registration.phone)
async def registration_phone_invalid(message: Message):
    await message.answer("Telefon raqamini tugma orqali yuboring.")


@router.message(Command("profil"))
async def profile_edit_start(message: Message, state: FSMContext):
    await state.set_state(Registration.full_name)
    await message.answer("Yangi ism-familiyangizni kiriting:")
