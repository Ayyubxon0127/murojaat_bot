# -*- coding: utf-8 -*-
import db

# Telegram rasm/media caption uchun maksimal uzunlik (1024), oddiy
# xabar matni uchun esa 4096. Xavfsizlik uchun kichikroq chegara olamiz.
CAPTION_LIMIT = 1000


def truncate_for_caption(text: str, limit: int = CAPTION_LIMIT) -> str:
    """Rasm caption'i sifatida yuborilganda matn 1024 belgidan oshib
    ketmasligi uchun qisqartiradi. Agar qisqartirilsa, oxiriga eslatma
    qo'shiladi -- to'liq matnni ko'rish uchun "Ko'rib chiqish" tugmasi bor."""
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n\n… (davomi uchun «👀 Ko'rib chiqish»ni bosing)"


def ticket_summary_text(ticket: dict, comments=None) -> str:
    status_label = db.STATUS_LABELS.get(ticket["status"], ticket["status"])
    lines = [
        f"🎫 <b>Murojaat #{ticket['id']}</b> — {status_label}",
        f"👤 Xodim: {ticket['user_name']}",
        f"🏢 Bo'lim: {ticket['department']}",
        f"📂 Muammo turi: {ticket['category']}",
        f"📝 Tavsif: {ticket['description']}",
        f"🕒 Yaratildi: {ticket['created_at']}",
    ]
    if ticket.get("photo_count") is not None:
        lines.append(f"📎 Rasmlar: {ticket['photo_count']} ta")
    if ticket.get("assigned_to_name"):
        lines.append(f"🙋 Mas'ul: {ticket['assigned_to_name']}")
    if ticket.get("resolution_comment"):
        lines.append(f"✅ Yechim izohi: {ticket['resolution_comment']}")
    if comments:
        lines.append("💬 Izohlar:")
        for comment in comments:
            lines.append(
                f"  • [{comment['created_at']}] "
                f"{comment['author_name']}: {comment['comment']}"
            )
    return "\n".join(lines)


def ticket_preview_text(data: dict) -> str:
    photo_ids = data.get("photo_ids", [])
    comment = data.get("comment") or "—"
    return (
        "🔎 <b>Murojaatni tekshiring</b>\n\n"
        f"🏢 Bo'lim: <b>{data.get('department')}</b>\n"
        f"📂 Muammo turi: <b>{data.get('category')}</b>\n"
        f"📝 Tavsif: {data.get('description')}\n"
        f"📎 Rasmlar: {len(photo_ids)} ta\n"
        f"💬 Izoh: {comment}\n\n"
        "Ma'lumotlar to'g'ri bo'lsa, yuborishni bosing."
    )


def stats_text(stats: dict) -> str:
    lines = [f"<b>📊 Umumiy statistika</b>\n", f"Jami murojaatlar: {stats['total']}\n"]
    lines.append("<b>Holat bo'yicha:</b>")
    for status_key, label in db.STATUS_LABELS.items():
        lines.append(f"  {label}: {stats['by_status'].get(status_key, 0)}")
    lines.append("\n<b>Bo'lim bo'yicha:</b>")
    for dep, cnt in stats["by_department"]:
        lines.append(f"  {dep}: {cnt}")
    lines.append("\n<b>Muammo turi bo'yicha:</b>")
    for cat, cnt in stats["by_category"]:
        lines.append(f"  {cat}: {cnt}")
    return "\n".join(lines)