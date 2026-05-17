from telegram import InlineKeyboardButton as Btn, InlineKeyboardMarkup as KB
from config import CHANNEL_ID, SUPPORT_BOT

# ── الترحيب ──
def kb_welcome():
    return KB([[Btn("🚀 ابدأ الاستخدام", callback_data="start_use")]])

# ── الاشتراك الإجباري ──
def kb_join():
    return KB([
        [Btn("📢 اشترك بالقناة", url=f"https://t.me/{CHANNEL_ID.replace('@','')}")],
        [Btn("✅ تأكيد الاشتراك", callback_data="check_join")],
    ])

# ── القائمة الرئيسية ──
def kb_main():
    return KB([
        [Btn("🔍 بحث عن سهم",      callback_data="search"),
         Btn("🔴 أبرز أسهم اليوم", callback_data="top_stocks")],
        [Btn("💳 اشتراكي",          callback_data="my_sub"),
         Btn("🔔 تنبيهاتي",         callback_data="my_alerts")],
        [Btn("🏢 مراقبة شركة",      callback_data="watchlist")],
    ])

# ── رجوع ──
def kb_back():
    return KB([[Btn("🔙 رجوع", callback_data="back_main")]])

# ── بعد نتيجة البحث ──
def kb_after_search():
    return KB([
        [Btn("🔍 بحث مرة أخرى", callback_data="search")],
        [Btn("🔙 رجوع",          callback_data="back_main")],
    ])

# ── الاشتراك ──
def kb_sub():
    return KB([
        [Btn("📅 شهري — 5,000 د.ع",  callback_data="sub_monthly"),
         Btn("📆 سنوي — 50,000 د.ع", callback_data="sub_yearly")],
        [Btn("🔙 رجوع", callback_data="back_main")],
    ])

# ── بعد اختيار الخطة ──
def kb_payment_confirm(plan):
    return KB([
        [Btn("✅ أرسلت الإيصال",  callback_data=f"receipt_{plan}")],
        [Btn("🔙 رجوع", callback_data="my_sub")],
    ])

# ── دعم العملاء ──
def kb_support():
    return KB([
        [Btn("💬 تواصل مع الدعم", url=f"https://t.me/{SUPPORT_BOT.replace('@','')}")],
        [Btn("🔙 رجوع", callback_data="my_sub")],
    ])

# ── التنبيهات ──
def kb_alerts(alerts):
    rows = []
    for a in alerts:
        icon = "📈" if a["direction"] == "up" else "📉"
        rows.append([Btn(
            f"{icon} {a['symbol']} {a['pct']}% — حذف",
            callback_data=f"del_alert_{a['id']}"
        )])
    rows.append([Btn("➕ إضافة تنبيه", callback_data="add_alert")])
    rows.append([Btn("🔙 رجوع", callback_data="back_main")])
    return KB(rows)

# ── قائمة المراقبة ──
def kb_watchlist(watches, limit, current):
    rows = []
    for w in watches:
        rows.append([Btn(f"🏢 {w['company']} — حذف", callback_data=f"del_watch_{w['id']}")])
    if current < limit:
        rows.append([Btn("➕ إضافة شركة", callback_data="add_watch")])
    rows.append([Btn("🔙 رجوع", callback_data="back_main")])
    return KB(rows)

# ── أدمن ──
def kb_admin(user_id):
    return KB([
        [Btn("✅ تفعيل شهري", callback_data=f"adm_monthly_{user_id}"),
         Btn("✅ تفعيل سنوي", callback_data=f"adm_yearly_{user_id}")],
        [Btn("❌ رفض",         callback_data=f"adm_reject_{user_id}")],
    ])

def kb_admin_confirm(plan, user_id):
    return KB([
        [Btn("✅ تأكيد",    callback_data=f"adm_confirm_{plan}_{user_id}"),
         Btn("🔙 تراجع",   callback_data=f"adm_back_{user_id}")],
    ])

def kb_admin_notify(plan, user_id, end_str):
    return KB([[Btn("📨 إرسال إشعار للمستخدم",
                    callback_data=f"adm_notify_{plan}_{user_id}_{end_str}")]])
