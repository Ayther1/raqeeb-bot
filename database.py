import aiosqlite
from datetime import datetime, timedelta
from config import TRIAL_DAYS, WATCH_LIMITS

DB = "raqeeb.db"

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id    INTEGER PRIMARY KEY,
                username   TEXT,
                full_name  TEXT,
                join_date  TEXT,
                trial_end  TEXT,
                sub_type   TEXT DEFAULT NULL,
                sub_end    TEXT DEFAULT NULL,
                is_blocked INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS alerts (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER,
                symbol    TEXT,
                direction TEXT,
                pct       REAL
            );
            CREATE TABLE IF NOT EXISTS watchlist (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                company TEXT
            );
            CREATE TABLE IF NOT EXISTS news_log (
                news_id TEXT PRIMARY KEY,
                sent_at TEXT
            );
        """)
        await db.commit()

async def register_user(user_id, username, full_name):
    now = datetime.now()
    trial_end = now + timedelta(days=TRIAL_DAYS)
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (user_id,username,full_name,join_date,trial_end)
            VALUES (?,?,?,?,?)
        """, (user_id, username, full_name, now.isoformat(), trial_end.isoformat()))
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as c:
            row = await c.fetchone()
            if row:
                return dict(zip([d[0] for d in c.description], row))
    return None

async def is_active(user_id):
    u = await get_user(user_id)
    if not u or u["is_blocked"]:
        return False
    now = datetime.now()
    if u["sub_end"] and datetime.fromisoformat(u["sub_end"]) > now:
        return True
    if u["trial_end"] and datetime.fromisoformat(u["trial_end"]) > now:
        return True
    return False

async def get_sub_type(user_id):
    u = await get_user(user_id)
    if not u:
        return "trial"
    now = datetime.now()
    if u["sub_end"] and datetime.fromisoformat(u["sub_end"]) > now:
        return u["sub_type"] or "monthly"
    return "trial"

async def activate_sub(user_id, plan):
    days = 30 if plan == "monthly" else 365
    end = datetime.now() + timedelta(days=days)
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE users SET sub_type=?, sub_end=? WHERE user_id=?",
                         (plan, end.isoformat(), user_id))
        await db.commit()
    return end

async def block_user(user_id):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE users SET is_blocked=1 WHERE user_id=?", (user_id,))
        await db.commit()

async def get_all_active():
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT user_id FROM users WHERE is_blocked=0") as c:
            rows = await c.fetchall()
    result = []
    for r in rows:
        if await is_active(r[0]):
            result.append(r[0])
    return result

async def get_all_users():
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT * FROM users ORDER BY join_date DESC") as c:
            rows = await c.fetchall()
            cols = [d[0] for d in c.description]
    return [dict(zip(cols, r)) for r in rows]

async def get_expiring_tomorrow():
    tom = (datetime.now() + timedelta(days=1)).date()
    users = await get_all_users()
    result = []
    for u in users:
        end = u.get("sub_end") or u.get("trial_end")
        if end and datetime.fromisoformat(end).date() == tom:
            result.append(u)
    return result

# ── تنبيهات ──
async def add_alert(user_id, symbol, direction, pct):
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT INTO alerts (user_id,symbol,direction,pct) VALUES (?,?,?,?)",
                         (user_id, symbol.upper(), direction, pct))
        await db.commit()

async def get_alerts(user_id):
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT * FROM alerts WHERE user_id=?", (user_id,)) as c:
            rows = await c.fetchall()
            cols = [d[0] for d in c.description]
    return [dict(zip(cols, r)) for r in rows]

async def delete_alert(alert_id, user_id):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM alerts WHERE id=? AND user_id=?", (alert_id, user_id))
        await db.commit()

async def get_all_alerts():
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT * FROM alerts") as c:
            rows = await c.fetchall()
            cols = [d[0] for d in c.description]
    return [dict(zip(cols, r)) for r in rows]

# ── مراقبة شركات ──
async def get_watch_limit(user_id):
    st = await get_sub_type(user_id)
    return WATCH_LIMITS.get(st, 1)

async def add_watch(user_id, company):
    watches = await get_watchlist(user_id)
    limit = await get_watch_limit(user_id)
    if len(watches) >= limit:
        return False
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT INTO watchlist (user_id,company) VALUES (?,?)", (user_id, company))
        await db.commit()
    return True

async def remove_watch(watch_id, user_id):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM watchlist WHERE id=? AND user_id=?", (watch_id, user_id))
        await db.commit()

async def get_watchlist(user_id):
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT * FROM watchlist WHERE user_id=?", (user_id,)) as c:
            rows = await c.fetchall()
            cols = [d[0] for d in c.description]
    return [dict(zip(cols, r)) for r in rows]

async def get_all_watches():
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT * FROM watchlist") as c:
            rows = await c.fetchall()
            cols = [d[0] for d in c.description]
    return [dict(zip(cols, r)) for r in rows]

# ── أخبار ──
async def is_news_sent(news_id):
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT news_id FROM news_log WHERE news_id=?", (news_id,)) as c:
            return await c.fetchone() is not None

async def mark_news(news_id):
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT OR IGNORE INTO news_log (news_id,sent_at) VALUES (?,?)",
                         (news_id, datetime.now().isoformat()))
        await db.commit()