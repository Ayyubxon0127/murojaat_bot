# IKT Support Bot — o'rnatish qo'llanmasi

## 1. Nima uchun kerak har bir fayl

Loyiha endi modullarga bo'lingan:

```text
files/
  bot.py
  config.py
  db.py
  handlers/
    start.py, ticket.py, photo.py, comments.py, edit.py, status.py, admin.py
  keyboards/
    main.py, ticket.py, admin.py
  services/
    ticket_service.py, notification.py, file_service.py
  states/
    ticket_states.py
  utils/
    helpers.py, formatters.py
  tickets.db
  requirements.txt
  README.md
```

- `bot.py` — startup: Bot/Dispatcher/Router ulash, DB init, automation loop.
- `config.py` — sozlamalar (token, guruh ID, bo'limlar, muammo turlari). **Asosan shu fayl to'ldiriladi.**
- `db.py` — SQLite baza va migratsiya/CRUD funksiyalari.
- `handlers/` — buyruq va callback handlerlar.
- `services/` — biznes logika (ticket yuborish, xabarnoma, export).
- `keyboards/` — inline keyboard konstruktorlari.
- `states/` — FSM holatlar.
- `utils/` — yordamchi va formatlovchi funksiyalar.
- `tickets.db` — barcha murojaatlar saqlanadigan mavjud baza fayli.

## 2. Botni yaratish (BotFather orqali)

1. Telegram'da @BotFather ga yozing
2. `/newbot` buyrug'ini yuboring
3. Bot nomi va username so'raladi (masalan: `Indorama_IT_Bot`)
4. Sizga token beriladi (masalan: `7123456789:AAH...`)
5. Shu tokenni `config.py` ichidagi `BOT_TOKEN` ga qo'ying

## 3. IT guruhini sozlash

1. Telegram'da yangi guruh yarating (masalan "IT Bo'limi — Murojaatlar")
2. Botni shu guruhga qo'shing
3. Guruhda istalgan xabar yozing
4. @getidsbot (yoki @userinfobot) ni guruhga vaqtincha qo'shib, guruh ID sini oling — manfiy son bo'ladi (masalan `-1001234567890`)
5. Shu ID ni `config.py` dagi `IT_GROUP_ID` ga yozing
6. @getidsbot ni guruhdan olib tashlashingiz mumkin

## 4. IT xodimlar ID sini olish

Har bir IT xodimi (siz, Jahongir aka va h.k.) @userinfobot ga `/start` yozib, o'z Telegram ID sini bilib oladi. Shu ID larni `config.py` dagi `IT_STAFF_IDS` ro'yxatiga qo'shing:

```python
IT_STAFF_IDS = [
    111111111,  # Ayyubxon
    222222222,  # Jahongir aka
]
```

Bu muhim — faqat shu ro'yxatdagi kishilar tugmalarni bosa oladi, `/export` va `/statistika` ishlata oladi.

## 5. Kutubxonalarni o'rnatish

PyCharm terminalida (yoki oddiy terminalda, loyiha papkasida):

```bash
pip install -r requirements.txt
```

## 6. Ishga tushirish

```bash
python bot.py
```

Konsolda `Bot ishga tushdi.` yozuvi chiqsa — hammasi tayyor. Endi Telegram'da botga `/start` yozib sinab ko'rishingiz mumkin.

## 7. Qanday ishlaydi (qisqacha)

- Xodim: `/murojaat` → bo'lim va muammo turini tanlaydi → matn yozadi → ixtiyoriy bir yoki bir nechta rasm yuboradi (`/skip`) → izoh va preview orqali tasdiqlaydi
- Preview oynasida tavsifni tahrirlash, rasm/izoh qo'shish, orqaga qaytish, yuborish yoki bekor qilish mumkin.
- Yuborilgandan keyin qisqa vaqt ichida xodim tasdiqlash orqali murojaatni bekor qilishi yoki tugma orqali izoh qoldirishi mumkin; izohlar IT guruhida ko'rinadi.
- IT: guruhda tugmalar orqali `Menga tayinla` / `Jarayonda` / `Bajarildi` / `Bekor qilish` / `Izoh qo'shish` / `Qayta ochish`
- `Bajarildi` bosilganda tayyor shablon yoki o'z izohingizni yozasiz — shu izoh xodimga ham yuboriladi
- Xodim: `/mening_murojaatlarim` — o'z murojaatlari ro'yxati va holati
- IT: `/statistika` — umumiy raqamlar; `/export` — to'liq Excel hisobot
- Bot har 5 daqiqada 2 soatdan ortiq `Yangi` murojaatlar uchun guruhga SLA eslatmasi yuboradi.
- Har kuni soat 18:00 da kunlik murojaatlar va yopilgan murojaatlar xulosasi yuboriladi.
- Bir xodim/bo'limda bir xil muammo 3 marta takrorlansa, bot guruhga tub sabab bo'yicha ogohlantirish yuboradi.

## 8. Doim ishlab turishi uchun (24/7)

`python bot.py` buyrug'i PyCharm'da yoki terminalda ochiq turgandagina ishlaydi. Doim ishlab turishi uchun:

- **Eng oddiy variant:** arzon VPS server oling (oyiga ~$3-5), kodni serverga yuklang, va serverda doim orqa fonda ishlaydigan qilib sozlang (masalan `systemd` service yoki `screen`/`tmux` orqali)
- **Muqobil variant:** doim yonib turadigan ish kompyuteringizda skript sifatida ishlatish (lekin kompyuter o'chsa yoki qayta ishga tushsa, bot ham to'xtaydi)

## 9. Zaxira nusxa (backup) — MUHIM

`tickets.db` faylini har kuni biror joyga (masalan Google Drive, tashqi disk) nusxalab turing. Agar shu fayl yo'qolsa, barcha murojaatlar tarixi ham yo'qoladi.

## 10. Keyingi qadamlar uchun g'oyalar

Agar kelajakda kengaytirmoqchi bo'lsangiz:
- Baholash tizimi (xodimdan 1-5 yulduz)
- Inventar bilan bog'lash (qaysi kompyuter/asset bo'yicha murojaat)
- Kunlik avtomatik xulosa (har kuni soat 18:00 da guruhga statistikani yuborish)

Shu qismlarni ham xohlasangiz, alohida so'rang — qo'shib beraman.
