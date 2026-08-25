# -*- coding: utf-8 -*-
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from utils.helpers import is_staff

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        "Assalomu alaykum! Bu — IT bo'limiga murojaat yuborish boti.\n\n"
        "📩 /murojaat — yangi murojaat yuborish\n"
        "📋 /mening_murojaatlarim — mening murojaatlarim ro'yxati\n"
    )
    if is_staff(message.from_user.id):
        text += (
            "\n<b>IT xodimi buyruqlari:</b>\n"
            "📊 /statistika — umumiy statistika\n"
            "📥 /export — Excel hisobot yuklab olish\n"
        )
    await message.answer(text, parse_mode="HTML")
