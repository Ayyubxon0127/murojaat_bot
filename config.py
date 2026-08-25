# -*- coding: utf-8 -*-
"""
Bot sozlamalari.
Bu yerdagi qiymatlarni o'zingizga moslab to'ldiring.
"""
import os

# 1) BotFather'dan olingan token
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# 2) IT bo'limi guruhining Telegram ID raqami.
#    Qanday topish mumkin: botni guruhga qo'shing, guruhda biror xabar yozing,
#    keyin @getidsbot yoki @userinfobot orqali guruh ID sini oling.
#    Guruh ID odatda manfiy son bo'ladi, masalan: -1003980700296
IT_GROUP_ID = int(os.getenv("IT_GROUP_ID", "0"))

# SLA chegarasi (soatlarda)
SLA_HOURS = 2

# Foydalanuvchi yangi murojaatni yuborgandan keyin bekor qilishi mumkin bo'lgan vaqt.
USER_CANCEL_WINDOW_MINUTES = 10

# 3) IT xodimlarining Telegram user ID lari (faqat shular /export va
#    /statistika buyruqlaridan foydalana oladi, va tugmalarni bosa oladi).
#    O'z Telegram ID ingizni bilish uchun @userinfobot ga /start yozing.
IT_STAFF_IDS = [
    int(value.strip())
    for value in os.getenv("IT_STAFF_IDS", "").split(",")
    if value.strip()
]

# 4) Bo'limlar ro'yxati (murojaat yuborayotgan xodim tanlaydi)
DEPARTMENTS = [
    "IT",
    "Buxgalteriya (Accounting)",
    "HR",
    "Xarid (Procurement)",
    "Ombor (Warehouse)",
    "Ishlab chiqarish (Production)",
    "Muhandislik (Engineering)",
    "Sifat nazorati (QA)",
    "Xavfsizlik (Safety/Security)",
    "Tibbiyot (Medical)",
    "Savdo (Sales)",
    "Boshqa",
]

# 5) Muammo turlari
CATEGORIES = [
    "🖥 Kompyuter/noutbuk nosozligi",
    "🖨 Printer/kartrij",
    "🌐 Internet/tarmoq",
    "📶 Wi-Fi",
    "🔐 Parol/kirish huquqi",
    "💻 SAP/1C xatosi",
    "📹 CCTV",
    "➕ Boshqa",
]

# 6) Tayyor javob shablonlari (yopishda tez tanlash uchun)
QUICK_RESOLUTIONS = [
    "Masofadan hal qilindi",
    "Ehtiyot qism almashtirildi",
    "Foydalanuvchiga tushuntirildi",
    "Qayta o'rnatildi (reinstall)",
    "Parol qayta tiklandi",
]

# 7) Ma'lumotlar bazasi fayli nomi (shu papkada yaratiladi)
DB_PATH = "tickets.db"


def validate():
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not IT_GROUP_ID:
        missing.append("IT_GROUP_ID")
    if not IT_STAFF_IDS:
        missing.append("IT_STAFF_IDS")
    if missing:
        raise RuntimeError(
            "Quyidagi environment variable'lar sozlanmagan: "
            + ", ".join(missing)
            + ". .env.example asosida sozlang."
        )
