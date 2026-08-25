# -*- coding: utf-8 -*-
import logging

import config
import db
from keyboards.ticket import group_ticket_keyboard
from services.notification import notify_user
from utils.formatters import ticket_summary_text, truncate_for_caption


async def refresh_group_message(bot, ticket_id: int):
    ticket = await db.get_ticket(ticket_id)
    if not ticket or not ticket.get("group_message_id"):
        return

    comments = await db.get_comments(ticket_id)
    ticket["photo_count"] = len(await db.get_attachments(ticket_id))
    text = ticket_summary_text(ticket, comments)
    keyboard = group_ticket_keyboard(ticket_id, ticket["status"])
    try:
        await bot.edit_message_text(
            chat_id=ticket["group_chat_id"],
            message_id=ticket["group_message_id"],
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    except Exception as exc:
        try:
            await bot.edit_message_caption(
                chat_id=ticket["group_chat_id"],
                message_id=ticket["group_message_id"],
                caption=truncate_for_caption(text),
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except Exception:
            logging.warning(f"Guruh xabarini yangilab bo'lmadi: {exc}")


async def send_ticket_to_group(bot, ticket_id: int):
    from aiogram.types import InputMediaPhoto

    ticket = await db.get_ticket(ticket_id)
    comments = await db.get_comments(ticket_id)
    attachments = await db.get_attachments(ticket_id)
    ticket["photo_count"] = len(attachments)
    text = ticket_summary_text(ticket, comments)
    keyboard = group_ticket_keyboard(ticket_id, db.STATUS_NEW)

    if not attachments:
        # Rasm yo'q -- oddiy matnli xabar
        sent = await bot.send_message(
            config.IT_GROUP_ID,
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        await db.set_group_message(ticket_id, sent.chat.id, sent.message_id)

    elif len(attachments) == 1:
        # Bitta rasm -- rasm + matn + tugmalar bitta xabarda
        # (caption 1024 belgidan oshsa avtomatik qisqartiriladi)
        sent = await bot.send_photo(
            config.IT_GROUP_ID,
            photo=attachments[0],
            caption=truncate_for_caption(text),
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        await db.set_group_message(ticket_id, sent.chat.id, sent.message_id)

    else:
        # Bir nechta rasm -- avval albom (rasmlar birga), so'ng darhol
        # o'sha albomga javob tariqasida matn+tugmali xabar keladi.
        # Telegram media-group'da tugma bo'lishi mumkin emas, shuning
        # uchun tugmalar alohida xabarda, lekin ketma-ket chiqadi.
        media = [InputMediaPhoto(media=file_id) for file_id in attachments]
        sent_photos = await bot.send_media_group(config.IT_GROUP_ID, media=media)
        sent = await bot.send_message(
            config.IT_GROUP_ID,
            text,
            reply_markup=keyboard,
            reply_to_message_id=sent_photos[0].message_id,
            parse_mode="HTML",
        )
        await db.set_group_message(ticket_id, sent.chat.id, sent.message_id)


async def close_ticket(bot, ticket_id: int, comment: str):
    await db.set_resolution_comment(ticket_id, comment)
    await db.update_status(ticket_id, db.STATUS_DONE, closed=True)
    ticket = await db.get_ticket(ticket_id)
    await refresh_group_message(bot, ticket_id)
    await notify_user(
        bot,
        ticket["user_id"],
        f"✅ Murojaatingiz #{ticket_id} bajarildi.\nIzoh: {comment}",
    )