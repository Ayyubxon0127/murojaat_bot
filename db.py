# -*- coding: utf-8 -*-
"""
Ma'lumotlar bazasi (SQLite) bilan ishlash.
Barcha murojaatlar va izohlar shu fayl orqali saqlanadi/o'qiladi.
"""
import aiosqlite
from datetime import datetime, timedelta
from config import DB_PATH, SLA_HOURS

STATUS_NEW = "new"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE = "done"
STATUS_CANCELLED = "cancelled"

STATUS_LABELS = {
    STATUS_NEW: "🟡 Qabul qilindi",
    STATUS_IN_PROGRESS: "🔧 Ish jarayonida",
    STATUS_DONE: "✅ Yechildi",
    STATUS_CANCELLED: "❌ Bekor qilindi",
}


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_name TEXT NOT NULL,
                department TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                photo_file_id TEXT,
                status TEXT NOT NULL DEFAULT 'new',
                assigned_to_id INTEGER,
                assigned_to_name TEXT,
                resolution_comment TEXT,
                group_chat_id INTEGER,
                group_message_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                closed_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                author_name TEXT NOT NULL,
                comment TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ticket_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                position INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                UNIQUE(ticket_id, file_id),
                FOREIGN KEY (ticket_id) REFERENCES tickets(id)
            )
        """)
        columns = await db.execute_fetchall("PRAGMA table_info(tickets)")
        column_names = {row[1] for row in columns}
        if "sla_reminded_at" not in column_names:
            await db.execute("ALTER TABLE tickets ADD COLUMN sla_reminded_at TEXT")
        if "last_reminder_at" not in column_names:
            await db.execute("ALTER TABLE tickets ADD COLUMN last_reminder_at TEXT")
        for column in ("telegram_username", "phone_number"):
            if column not in column_names:
                await db.execute(f"ALTER TABLE tickets ADD COLUMN {column} TEXT")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                telegram_username TEXT,
                phone_number TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            INSERT OR IGNORE INTO ticket_attachments (ticket_id, file_id, position, created_at)
            SELECT id, photo_file_id, 0, COALESCE(created_at, ?)
            FROM tickets
            WHERE photo_file_id IS NOT NULL AND trim(photo_file_id) <> ''
        """, (_now(),))
        await db.execute("""
            CREATE TABLE IF NOT EXISTS automation_log (
                log_key TEXT PRIMARY KEY,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def create_ticket(
    user_id, user_name, department, category, description,
    photo_file_id=None, photo_file_ids=None, telegram_username=None,
    phone_number=None,
):
    now = _now()
    photo_ids = list(photo_file_ids or [])
    if photo_file_id and photo_file_id not in photo_ids:
        photo_ids.insert(0, photo_file_id)
    first_photo_id = photo_ids[0] if photo_ids else photo_file_id
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO tickets (user_id, user_name, telegram_username, phone_number,
                                  department, category, description, photo_file_id,
                                  status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, user_name, telegram_username, phone_number, department, category,
              description, first_photo_id, STATUS_NEW, now, now))
        ticket_id = cursor.lastrowid
        for position, file_id in enumerate(photo_ids):
            await db.execute("""
                INSERT OR IGNORE INTO ticket_attachments
                    (ticket_id, file_id, position, created_at)
                VALUES (?, ?, ?, ?)
            """, (ticket_id, file_id, position, now))
        if first_photo_id != photo_file_id:
            await db.execute(
                "UPDATE tickets SET photo_file_id = ? WHERE id = ?",
                (first_photo_id, ticket_id),
            )
        await db.commit()
        return ticket_id


async def get_user_profile(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def save_user_profile(user_id, full_name, telegram_username, phone_number):
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO user_profiles
                (user_id, full_name, telegram_username, phone_number, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                full_name = excluded.full_name,
                telegram_username = excluded.telegram_username,
                phone_number = excluded.phone_number,
                updated_at = excluded.updated_at
        """, (user_id, full_name, telegram_username, phone_number, now, now))
        await db.commit()


async def add_attachment(ticket_id, file_id, position=None):
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        if position is None:
            cursor = await db.execute(
                "SELECT COALESCE(MAX(position), -1) + 1 FROM ticket_attachments "
                "WHERE ticket_id = ?",
                (ticket_id,),
            )
            position = (await cursor.fetchone())[0]
        await db.execute("""
            INSERT OR IGNORE INTO ticket_attachments
                (ticket_id, file_id, position, created_at)
            VALUES (?, ?, ?, ?)
        """, (ticket_id, file_id, position, now))
        await db.execute(
            "UPDATE tickets SET photo_file_id = COALESCE(photo_file_id, ?), updated_at = ? "
            "WHERE id = ?",
            (file_id, now, ticket_id),
        )
        await db.commit()


async def get_attachments(ticket_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT file_id FROM ticket_attachments WHERE ticket_id = ? "
            "ORDER BY position, id",
            (ticket_id,),
        )
        return [row[0] for row in await cursor.fetchall()]


async def set_group_message(ticket_id, chat_id, message_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE tickets SET group_chat_id = ?, group_message_id = ? WHERE id = ?
        """, (chat_id, message_id, ticket_id))
        await db.commit()


async def get_ticket(ticket_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_status(ticket_id, status, closed=False):
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        if closed:
            await db.execute("""
                UPDATE tickets SET status = ?, updated_at = ?, closed_at = ? WHERE id = ?
            """, (status, now, now, ticket_id))
        else:
            await db.execute("""
                UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?
            """, (status, now, ticket_id))
        await db.commit()


async def set_resolution_comment(ticket_id, comment):
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE tickets SET resolution_comment = ?, updated_at = ? WHERE id = ?
        """, (comment, now, ticket_id))
        await db.commit()


async def assign_ticket(ticket_id, staff_id, staff_name):
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE tickets SET assigned_to_id = ?, assigned_to_name = ?, updated_at = ? WHERE id = ?
        """, (staff_id, staff_name, now, ticket_id))
        await db.commit()


async def add_comment(ticket_id, author_name, comment):
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO comments (ticket_id, author_name, comment, created_at)
            VALUES (?, ?, ?, ?)
        """, (ticket_id, author_name, comment, now))
        await db.execute("UPDATE tickets SET updated_at = ? WHERE id = ?", (now, ticket_id))
        await db.commit()


async def get_comments(ticket_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM comments WHERE ticket_id = ? ORDER BY id", (ticket_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_user_tickets(user_id, limit=20):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT * FROM tickets WHERE user_id = ? ORDER BY id DESC LIMIT ?
        """, (user_id, limit))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_all_tickets():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM tickets ORDER BY id")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_overdue_new_tickets():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT * FROM tickets
            WHERE status = ?
            ORDER BY id
        """, (STATUS_NEW,))
        rows = await cursor.fetchall()
        now = datetime.now()
        overdue_since = now - timedelta(hours=SLA_HOURS)
        reminder_interval = timedelta(hours=2)
        overdue = []
        for row in rows:
            ticket = dict(row)
            created_at = datetime.strptime(ticket["created_at"], "%Y-%m-%d %H:%M:%S")
            last_reminder_at = ticket.get("last_reminder_at")
            last_reminder = (
                datetime.strptime(last_reminder_at, "%Y-%m-%d %H:%M:%S")
                if last_reminder_at else None
            )
            if created_at <= overdue_since and (
                last_reminder is None or last_reminder <= now - reminder_interval
            ):
                ticket["overdue_hours"] = round(
                    (now - created_at).total_seconds() / 3600, 1
                )
                overdue.append(ticket)
        return overdue


async def mark_sla_reminded(ticket_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tickets SET last_reminder_at = ?, updated_at = ? WHERE id = ?",
            (_now(), _now(), ticket_id),
        )
        await db.commit()


async def get_period_stats(start_at, end_at=None):
    async with aiosqlite.connect(DB_PATH) as db:
        params = [start_at]
        end_clause = ""
        if end_at:
            end_clause = " AND created_at < ?"
            params.append(end_at)
        cursor = await db.execute(
            f"SELECT COUNT(*) FROM tickets WHERE created_at >= ?{end_clause}",
            params,
        )
        total = (await cursor.fetchone())[0]
        params = [start_at]
        if end_at:
            params.append(end_at)
        cursor = await db.execute(
            f"""SELECT COUNT(*) FROM tickets
                WHERE status IN (?, ?) AND closed_at >= ?{end_clause.replace('created_at', 'closed_at')}""",
            [STATUS_DONE, STATUS_CANCELLED] + params,
        )
        closed = (await cursor.fetchone())[0]
        return {"total": total, "closed": closed}


async def get_repeated_problems(min_count=3):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT 'employee' AS scope, user_id, MAX(user_name) AS user_name,
                   department, category, MAX(description) AS description,
                   COUNT(*) AS ticket_count, GROUP_CONCAT(id) AS ticket_ids
            FROM tickets
            GROUP BY user_id, department, category, lower(trim(description))
            HAVING COUNT(*) >= ?
            UNION ALL
            SELECT 'department' AS scope, NULL AS user_id, NULL AS user_name,
                   department, category, MAX(description) AS description,
                   COUNT(*) AS ticket_count, GROUP_CONCAT(id) AS ticket_ids
            FROM tickets
            GROUP BY department, category, lower(trim(description))
            HAVING COUNT(*) >= ?
            ORDER BY ticket_count DESC
        """, (min_count, min_count))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def claim_automation_log(log_key):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT OR IGNORE INTO automation_log (log_key, created_at) VALUES (?, ?)",
            (log_key, _now()),
        )
        await db.commit()
        return cursor.rowcount == 1


async def has_automation_log(log_key):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM automation_log WHERE log_key = ? LIMIT 1", (log_key,)
        )
        return await cursor.fetchone() is not None


async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        stats = {}

        cursor = await db.execute("SELECT status, COUNT(*) as cnt FROM tickets GROUP BY status")
        rows = await cursor.fetchall()
        stats["by_status"] = {r["status"]: r["cnt"] for r in rows}

        cursor = await db.execute("SELECT department, COUNT(*) as cnt FROM tickets GROUP BY department ORDER BY cnt DESC")
        rows = await cursor.fetchall()
        stats["by_department"] = [(r["department"], r["cnt"]) for r in rows]

        cursor = await db.execute("SELECT category, COUNT(*) as cnt FROM tickets GROUP BY category ORDER BY cnt DESC")
        rows = await cursor.fetchall()
        stats["by_category"] = [(r["category"], r["cnt"]) for r in rows]

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM tickets")
        row = await cursor.fetchone()
        stats["total"] = row["cnt"]

        return stats
