# -*- coding: utf-8 -*-
"""
IKT Support Bot — Indorama IT bo'limi uchun ichki murojaatlar boti.

Ishga tushirish: python bot.py
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramNetworkError, TelegramBadRequest
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

import config
import db
from handlers import admin, comments, edit, photo, start, status, ticket
from services.notification import automation_loop

logging.basicConfig(level=logging.INFO)


async def setup_bot_commands(bot: Bot):
    """"/" bosilganda Telegram tavsiya qiladigan buyruqlar ro'yxatini sozlaydi.
    Oddiy xodimlarga faqat asosiy buyruqlar, IT xodimlariga (shaxsiy chatida)
    qo'shimcha (statistika, export) buyruqlar ham qo'shib ko'rsatiladi."""
    default_commands = [
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="murojaat", description="Yangi murojaat yuborish"),
        BotCommand(command="mening_murojaatlarim", description="Mening murojaatlarim"),
    ]
    await bot.set_my_commands(default_commands, scope=BotCommandScopeDefault())

    staff_commands = default_commands + [
        BotCommand(command="statistika", description="Umumiy statistika"),
        BotCommand(command="export", description="Excel hisobot yuklab olish"),
    ]
    for staff_id in config.IT_STAFF_IDS:
        try:
            await bot.set_my_commands(
                staff_commands, scope=BotCommandScopeChat(chat_id=staff_id)
            )
        except TelegramBadRequest:
            # Xodim hali botga /start bosmagan bo'lishi mumkin -- shunda
            # Telegram uning shaxsiy chatiga buyruq qo'yishga ruxsat bermaydi.
            # Xodim /start bosgach, keyingi ishga tushirishda avtomatik to'g'rilanadi.
            logging.warning(
                "IT xodimi (%s) uchun buyruqlar sozlanmadi -- u hali botga "
                "/start bosmagan bo'lishi mumkin.", staff_id,
            )


def build_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(start.router)
    dispatcher.include_router(ticket.router)
    dispatcher.include_router(photo.router)
    dispatcher.include_router(edit.router)
    dispatcher.include_router(comments.router)
    dispatcher.include_router(status.router)
    dispatcher.include_router(admin.router)
    return dispatcher


async def main():
    await db.init_db()
    bot = Bot(token=config.BOT_TOKEN)
    await setup_bot_commands(bot)
    dispatcher = build_dispatcher()
    automation_task = asyncio.create_task(automation_loop(bot))
    logging.info("Bot ishga tushdi.")
    try:
        while True:
            try:
                await dispatcher.start_polling(bot)
                break
            except TelegramNetworkError as exc:
                logging.warning(
                    "Telegram API bilan aloqa uzildi; 10 soniyadan keyin qayta ulanadi: %s",
                    exc,
                )
                await asyncio.sleep(10)
    finally:
        automation_task.cancel()
        await asyncio.gather(automation_task, return_exceptions=True)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())