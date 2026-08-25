# -*- coding: utf-8 -*-
"""
Guruh ID sini aniq topish uchun skript.

QANDAY ISHLATISH:
1. Botingiz (@IKTmurojatlar123_bot) IT guruhingizga qo'shilganiga ishonch hosil qiling.
2. Shu skriptni ishga tushiring: python get_group_id.py
3. Konsolda "Kutilmoqda..." yozuvi chiqadi.
4. O'sha IT guruhingizga borib, istalgan matn yozing (masalan: "salom").
5. Konsolda guruh nomi va aniq ID si chiqadi -- shu ID ni config.py ga nusxa oling.
6. Ctrl+C bilan to'xtating.
"""
import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
import config

router = Router()

@router.message()
async def any_message(message: Message):
    print("=" * 50)
    print("Xabar keldi!")
    print("Chat turi:", message.chat.type)
    print("Chat nomi:", message.chat.title or message.chat.full_name)
    print("CHAT ID (shu raqamni config.py ga qo'ying):", message.chat.id)
    print("=" * 50)

async def main():
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    print("Kutilmoqda... IT guruhingizda istalgan xabar yozing.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())