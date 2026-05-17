"""
لوحات المفاتيح والأزرار
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# ─── القائمة الرئيسية ──────────────────────────────────────────────────────────

def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔍 بحث عن سهم", callback_data="search_stock"),
            InlineKeyboardButton("🏆 أبرز الأسهم", callback_data="top_stocks"),
        ],
        [
            InlineKeyboardButton("💎 اشتراكي", callback_data="subscription"),
            InlineKeyboardButton("🔔 تنبيهاتي", callback_data="my_alerts"),
        ],
        [
            InlineKeyboardButton("👁 مراقبة شركة", callback_data="watch_company"),
            InlineKeyboardButton("📊 التقرير اليومي", callback_data="daily_report"),
        ],
    ])

# ─── زر الرجوع ────────────────────────────────────────────────────────────────

def back_button(callback: str = "main_menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 رجوع للقائمة", callback_data=callback)
    ]])

# ─── بعد نتيجة البحث ─────────────────────────────────────────────────────────

def after_search() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔍 بحث مرة أخرى", callback_data="search_stock"),
            InlineKeyboardButton("🔙 رجوع", callback_data="main_menu"),
        ]
    ])

# ─── الاشتراك ─────────────────────────────────────────────────────────────────

def subscription_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 اشتراك شهري — 5,000 د.ع", callback_data="sub_monthly")],
        [InlineKeyboardButton("📆 اشتراك سنوي — 50,000 د.ع", callback_data="sub_yearly")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")],
    ])

def payment_confirm() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ أرسلت الوصل", callback_data="receipt_sent")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="main_menu")],
    ])

# ─── التنبيهات ────────────────────────────────────────────────────────────────

def alerts_menu(alerts: list) -> InlineKeyboardMarkup:
    rows = []
    for alert in alerts:
        direction = "📈" if alert["direction"] == "up" else "📉"
        label = f"{direction} {alert['symbol']} — {alert['target_pct']}%"
        rows.append([InlineKeyboardButton(
            f"🗑 {label}", callback_data=f"del_alert_{alert['id']}"
        )])
    rows.append([InlineKeyboardButton("➕ إضافة تنبيه جديد", callback_data="add_alert")])
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)

def alert_direction_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📈 صعود", callback_data="alert_dir_up"),
            InlineKeyboardButton("📉 هبوط", callback_data="alert_dir_down"),
        ],
        [InlineKeyboardButton("❌ إلغاء", callback_data="my_alerts")],
    ])

# ─── مراقبة الشركات ───────────────────────────────────────────────────────────

def watchlist_menu(items: list, limit: int) -> InlineKeyboardMarkup:
    rows = []
    for item in items:
        rows.append([InlineKeyboardButton(
            f"🗑 {item['symbol']} — {item['company'][:15]}",
            callback_data=f"del_watch_{item['symbol']}"
        )])
    if len(items) < limit:
        rows.append([InlineKeyboardButton("➕ إضافة شركة", callback_data="add_watch")])
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)

# ─── زر الاشتراك بالقناة ─────────────────────────────────────────────────────

def channel_join_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 اشترك بالقناة", url="https://t.me/RaqeebIQ")],
        [InlineKeyboardButton("✅ تأكيد الاشتراك", callback_data="verify_join")],
    ])

# ─── تقارير ───────────────────────────────────────────────────────────────────

def reports_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 تقرير اليوم", callback_data="daily_report")],
        [InlineKeyboardButton("📈 تقرير الأسبوع", callback_data="weekly_report")],
        [InlineKeyboardButton("📉 تقرير الشهر", callback_data="monthly_report")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")],
    ])

# ─── لوحة الإدارة ─────────────────────────────────────────────────────────────

def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 المشتركون", callback_data="admin_users")],
        [InlineKeyboardButton("💳 الوصولات المعلقة", callback_data="admin_payments")],
        [InlineKeyboardButton("📢 إرسال للكل", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📊 إحصائيات", callback_data="admin_stats")],
    ])

def approve_payment_btn(pay_id: int, user_id: int, sub_type: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"✅ قبول ({sub_type})",
            callback_data=f"approve_{pay_id}_{user_id}_{sub_type}"
        )],
        [InlineKeyboardButton(
            "❌ رفض",
            callback_data=f"reject_{pay_id}_{user_id}"
        )],
    ])
