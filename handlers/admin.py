# -*- coding: utf-8 -*-
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

import db
from services.file_service import build_export_file
from utils.formatters import stats_text
from utils.helpers import is_staff

router = Router()


@router.message(Command("statistika"))
async def cmd_stats(message: Message):
    if not is_staff(message.from_user.id):
        await message.answer("Bu buyruq faqat IT xodimlari uchun.")
        return
    stats = await db.get_stats()
    await message.answer(stats_text(stats), parse_mode="HTML")


@router.message(Command("export"))
async def cmd_export(message: Message):
    if not is_staff(message.from_user.id):
        await message.answer("Bu buyruq faqat IT xodimlari uchun.")
        return

    tickets = await db.get_all_tickets()
    if not tickets:
        await message.answer("Hozircha bironta murojaat yo'q.")
        return

    filename, file_bytes = build_export_file(tickets)
    await message.answer_document(
        BufferedInputFile(file_bytes, filename=filename),
        caption=f"📥 Jami {len(tickets)} ta murojaat.",
    )
