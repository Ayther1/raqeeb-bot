import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from config import TRIAL_DAYS

DB_PATH = "raqeeb.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # جدول المستخدمين
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id     INTEGER PRIMARY KEY,
        username    TEXT,
        full_name   TEXT,
        joined_at   TEXT DEFAULT (datetime('now')),
        sub_type    TEXT DEFAULT 'trial',
        sub_end     TEXT,
        is_blocked  INTEGER DEFAULT 0
    )
    """)

    # جدول الاشتراكات والوصولات
    c.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER,
        amount      INTEGER,
        sub_type    TEXT,
        receipt_img TEXT,
        sender_name TEXT,
        status      TEXT DEFAULT 'pending',
        created_at  TEXT DEFAULT (datetime('now')),
        approved_at TEXT
    )
    """)

    # جدول التنبيهات
    c.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER,
        symbol      TEXT,
        target_pct  REAL,
        direction   TEXT,
        created_at  TEXT DEFAULT (datetime('now')),
        is_active   INTEGER DEFAULT 1
    )
    """)

    # جدول مراقبة الشركات
    c.execute("""
    CREATE TABLE IF NOT EXISTS watchlist (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER,
        symbol      TEXT,
        company     TEXT,
        created_at  TEXT DEFAULT (datetime('now'))
    )
    """)

    # جدول الأخبار (لمنع التكرار)
    c.execute("""
    CREATE TABLE IF NOT EXISTS news (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        hash        TEXT UNIQUE,
        title       TEXT,
        source      TEXT,
        company     TEXT,
        date        TEXT,
        sent        INTEGER DEFAULT 0,
        created_at  TEXT DEFAULT (datetime('now'))
    )
    """)

    conn.commit()
    conn.close()

# ─── Users ───────────────────────────────────────────────────────────────────

def upsert_user(user_id: int, username: str, full_name: str):
    conn = get_conn()
    c = conn.cursor()
    existing = c.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    if not existing:
        trial_end = (datetime.now() + timedelta(days=TRIAL_DAYS)).strftime("%Y-%m-%d")
        c.execute("""
            INSERT INTO users (user_id, username, full_name, sub_type, sub_end)
            VALUES (?, ?, ?, 'trial', ?)
        """, (user_id, username or "", full_name or "", trial_end))
        conn.commit()
        conn.close()
        return True  # مستخدم جديد
    else:
        c.execute("UPDATE users SET username=?, full_name=? WHERE user_id=?",
                  (username or "", full_name or "", user_id))
        conn.commit()
        conn.close()
        return False

def get_user(user_id: int):
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_all_users():
    conn = get_conn()
    users = conn.execute("SELECT * FROM users ORDER BY joined_at DESC").fetchall()
    conn.close()
    return [dict(u) for u in users]

def get_all_user_ids():
    conn = get_conn()
    rows = conn.execute("SELECT user_id FROM users WHERE is_blocked=0").fetchall()
    conn.close()
    return [r["user_id"] for r in rows]

def is_subscribed(user_id: int) -> bool:
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    if not user:
        return False
    if user["sub_type"] in ("monthly", "yearly"):
        if user["sub_end"] and datetime.strptime(user["sub_end"], "%Y-%m-%d") > datetime.now():
            return True
    if user["sub_type"] == "trial":
        if user["sub_end"] and datetime.strptime(user["sub_end"], "%Y-%m-%d") > datetime.now():
            return True
    return False

def set_subscription(user_id: int, sub_type: str, days: int):
    end = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    conn = get_conn()
    conn.execute("UPDATE users SET sub_type=?, sub_end=? WHERE user_id=?",
                 (sub_type, end, user_id))
    conn.commit()
    conn.close()

def get_monitoring_limit(user_id: int) -> int:
    from config import MONITORING_LIMITS
    user = get_user(user_id)
    if not user:
        return 1
    sub = user.get("sub_type", "trial")
    if sub == "yearly":
        return MONITORING_LIMITS["yearly"]
    elif sub == "monthly":
        return MONITORING_LIMITS["monthly"]
    return MONITORING_LIMITS["free"]

# ─── Payments ─────────────────────────────────────────────────────────────────

def add_payment(user_id: int, amount: int, sub_type: str, receipt_img: str, sender_name: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO payments (user_id, amount, sub_type, receipt_img, sender_name)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, amount, sub_type, receipt_img, sender_name))
    pay_id = c.lastrowid
    conn.commit()
    conn.close()
    return pay_id

def get_all_payments():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM payments ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def approve_payment(pay_id: int):
    conn = get_conn()
    conn.execute("""
        UPDATE payments SET status='approved', approved_at=datetime('now') WHERE id=?
    """, (pay_id,))
    conn.commit()
    conn.close()

# ─── Alerts ──────────────────────────────────────────────────────────────────

def add_alert(user_id: int, symbol: str, target_pct: float, direction: str):
    conn = get_conn()
    conn.execute("""
        INSERT INTO alerts (user_id, symbol, target_pct, direction)
        VALUES (?, ?, ?, ?)
    """, (user_id, symbol.upper(), target_pct, direction))
    conn.commit()
    conn.close()

def get_user_alerts(user_id: int):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM alerts WHERE user_id=? AND is_active=1", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_alert(alert_id: int, user_id: int):
    conn = get_conn()
    conn.execute("UPDATE alerts SET is_active=0 WHERE id=? AND user_id=?",
                 (alert_id, user_id))
    conn.commit()
    conn.close()

def get_all_active_alerts():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM alerts WHERE is_active=1").fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ─── Watchlist ────────────────────────────────────────────────────────────────

def add_watchlist(user_id: int, symbol: str, company: str) -> bool:
    limit = get_monitoring_limit(user_id)
    conn = get_conn()
    count = conn.execute(
        "SELECT COUNT(*) as c FROM watchlist WHERE user_id=?", (user_id,)
    ).fetchone()["c"]
    if count >= limit:
        conn.close()
        return False
    # منع التكرار
    exists = conn.execute(
        "SELECT id FROM watchlist WHERE user_id=? AND symbol=?", (user_id, symbol.upper())
    ).fetchone()
    if exists:
        conn.close()
        return True
    conn.execute("""
        INSERT INTO watchlist (user_id, symbol, company)
        VALUES (?, ?, ?)
    """, (user_id, symbol.upper(), company))
    conn.commit()
    conn.close()
    return True

def get_user_watchlist(user_id: int):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM watchlist WHERE user_id=?", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def remove_watchlist(user_id: int, symbol: str):
    conn = get_conn()
    conn.execute("DELETE FROM watchlist WHERE user_id=? AND symbol=?",
                 (user_id, symbol.upper()))
    conn.commit()
    conn.close()

def get_all_watchlist():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM watchlist").fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ─── News ─────────────────────────────────────────────────────────────────────

def news_hash(title: str, source: str) -> str:
    return hashlib.md5(f"{title}{source}".encode()).hexdigest()

def save_news(title: str, source: str, company: str, date: str) -> bool:
    h = news_hash(title, source)
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO news (hash, title, source, company, date)
            VALUES (?, ?, ?, ?, ?)
        """, (h, title, source, company, date))
        conn.commit()
        conn.close()
        return True  # خبر جديد
    except sqlite3.IntegrityError:
        conn.close()
        return False  # خبر مكرر

def get_unsent_news():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM news WHERE sent=0 ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_news_sent(news_id: int):
    conn = get_conn()
    conn.execute("UPDATE news SET sent=1 WHERE id=?", (news_id,))
    conn.commit()
    conn.close()

def get_latest_news(limit: int = 5):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM news ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
