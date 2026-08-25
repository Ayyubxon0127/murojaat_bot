# -*- coding: utf-8 -*-
import asyncio
import logging
from datetime import datetime

import config
import db


async def notify_user(bot, user_id: int, text: str):
    try:
        await bot.send_message(user_id, text, parse_mode="HTML")
    except Exception as exc:
        logging.warning(f"Foydalanuvchiga xabar yuborib bo'lmadi ({user_id}): {exc}")


async def send_automation_message(bot, text: str) -> bool:
    try:
        await bot.send_message(config.IT_GROUP_ID, text, parse_mode="HTML")
        return True
    except Exception as exc:
        logging.warning(f"Avtomatik xabar yuborib bo'lmadi: {exc}")
        return False


async def check_sla_reminders(bot):
    tickets = await db.get_overdue_new_tickets()
    if not tickets:
        return

    lines = [
        f"⚠️ Diqqat! {len(tickets)} ta murojaat "
        f"{config.SLA_HOURS} soatdan ortiq \"Yangi\" holatda:"
    ]
    for ticket in tickets:
        lines.append(
            f"• #{ticket['id']} — {ticket['department']} — "
            f"{ticket['category']} ({ticket['overdue_hours']:.1f} soat)"
        )

    sent = await send_automation_message(bot, "\n".join(lines))
    if sent:
        for ticket in tickets:
            await db.mark_sla_reminded(ticket["id"])


async def send_daily_summary(bot, now: datetime):
    if now.hour != 18:
        return
    day_key = now.strftime("%Y-%m-%d")
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    stats = await db.get_period_stats(start.strftime("%Y-%m-%d %H:%M:%S"))
    sent = await send_automation_message(
        bot,
        f"📊 <b>Kunlik xulosa ({day_key})</b>\n"
        f"Bugun: {stats['total']} ta murojaat, {stats['closed']} tasi yopildi.",
    )
    if sent:
        await db.claim_automation_log(f"daily-summary:{day_key}")


async def check_repeated_problems(bot):
    problems = await db.get_repeated_problems()
    for problem in problems:
        key = (
            f"repeat:{problem['scope']}:{problem['user_id']}:{problem['department']}:"
            f"{problem['category']}:{problem['description']}"
        )
        if await db.has_automation_log(key):
            continue
        ids = ", ".join(f"#{ticket_id}" for ticket_id in problem["ticket_ids"].split(","))
        subject = (
            f"Xodim: {problem['user_name']}"
            if problem["scope"] == "employee"
            else f"Bo'lim: {problem['department']}"
        )
        sent = await send_automation_message(
            bot,
            "🔁 <b>Takroriy muammo ogohlantirishi</b>\n"
            f"{subject}\n"
            f"Bo'lim: {problem['department']}\n"
            f"Muammo turi: {problem['category']}\n"
            f"Tavsif: {problem['description']}\n"
            f"{problem['ticket_count']} marta takrorlangan ({ids}). "
            "Tub sababni tekshirish kerak bo'lishi mumkin.",
        )
        if sent:
            await db.claim_automation_log(key)


async def automation_loop(bot):
    while True:
        try:
            now = datetime.now()
            await check_sla_reminders(bot)
            await send_daily_summary(bot, now)
            await check_repeated_problems(bot)
        except Exception:
            logging.exception("Avtomatik vazifalar bajarilmadi")
        await asyncio.sleep(300)
