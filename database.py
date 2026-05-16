# database.py — قاعدة البيانات

import aiosqlite
from datetime import datetime, timedelta
from config import TRIAL_DAYS

DB_PATH = "raqeeb.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id       INTEGER PRIMARY KEY,
                username      TEXT,
                full_name     TEXT,
                join_date     TEXT,
                trial_end     TEXT,
                sub_type      TEXT DEFAULT NULL,
                sub_end       TEXT DEFAULT NULL,
                is_active     INTEGER DEFAULT 1,
                is_blocked    INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER,
                symbol      TEXT,
                alert_type  TEXT,
                value       REAL,
                triggered   INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS news_log (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                news_id TEXT UNIQUE,
                sent_at TEXT
            )
        """)
        await db.commit()

async def register_user(user_id, username, full_name):
    now = datetime.now()
    trial_end = now + timedelta(days=TRIAL_DAYS)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (user_id, username, full_name, join_date, trial_end)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, username, full_name, now.isoformat(), trial_end.isoformat()))
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                cols = [d[0] for d in cursor.description]
                return dict(zip(cols, row))
    return None

async def is_user_active(user_id):
    user = await get_user(user_id)
    if not user:
        return False
    if user["is_blocked"]:
        return False
    now = datetime.now()
    # تحقق من الاشتراك الفعلي
    if user["sub_end"]:
        if datetime.fromisoformat(user["sub_end"]) > now:
            return True
    # تحقق من التجربة المجانية
    if user["trial_end"]:
        if datetime.fromisoformat(user["trial_end"]) > now:
            return True
    return False

async def activate_subscription(user_id, sub_type):
    now = datetime.now()
    if sub_type == "monthly":
        sub_end = now + timedelta(days=30)
    else:
        sub_end = now + timedelta(days=365)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users SET sub_type=?, sub_end=?, is_active=1 WHERE user_id=?
        """, (sub_type, sub_end.isoformat(), user_id))
        await db.commit()
    return sub_end

async def get_all_active_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users WHERE is_blocked=0") as cursor:
            rows = await cursor.fetchall()
    return [r[0] for r in rows]

async def get_expiring_tomorrow():
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT user_id, full_name, sub_type, sub_end, trial_end
            FROM users WHERE is_blocked=0
        """) as cursor:
            rows = await cursor.fetchall()
            cols = [d[0] for d in cursor.description]
    expiring = []
    for row in rows:
        u = dict(zip(cols, row))
        end = u["sub_end"] or u["trial_end"]
        if end:
            end_date = datetime.fromisoformat(end).date()
            if end_date == tomorrow:
                expiring.append(u)
    return expiring

async def add_alert(user_id, symbol, alert_type, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO alerts (user_id, symbol, alert_type, value)
            VALUES (?, ?, ?, ?)
        """, (user_id, symbol.upper(), alert_type, value))
        await db.commit()

async def get_user_alerts(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT * FROM alerts WHERE user_id=? AND triggered=0
        """, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, r)) for r in rows]

async def delete_alert(alert_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM alerts WHERE id=?", (alert_id,))
        await db.commit()

async def get_all_alerts():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM alerts WHERE triggered=0") as cursor:
            rows = await cursor.fetchall()
            cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, r)) for r in rows]

async def is_news_sent(news_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM news_log WHERE news_id=?", (news_id,)) as cursor:
            return await cursor.fetchone() is not None

async def mark_news_sent(news_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO news_log (news_id, sent_at) VALUES (?, ?)
        """, (news_id, datetime.now().isoformat()))
        await db.commit()

async def get_all_users_info():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM users ORDER BY join_date DESC") as cursor:
            rows = await cursor.fetchall()
            cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, r)) for r in rows]