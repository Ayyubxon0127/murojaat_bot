# -*- coding: utf-8 -*-
"""
Guruhga xabar yubora olish-olmasligini tekshirish uchun kichik skript.
Ishlatish: python test_group.py
"""
import asyncio
from aiogram import Bot
import config

async def main():
    bot = Bot(token=config.BOT_TOKEN)
    print("Tekshirilayotgan IT_GROUP_ID:", config.IT_GROUP_ID)
    try:
        chat = await bot.get_chat(config.IT_GROUP_ID)
        print("✅ Guruh topildi:", chat.title, "| turi:", chat.type)
        await bot.send_message(config.IT_GROUP_ID, "🔧 Test xabari — bot guruhga yoza oladi.")
        print("✅ Xabar muvaffaqiyatli yuborildi!")
    except Exception as e:
        print("❌ XATO:", e)
    await bot.session.close()

asyncio.run(main())