# messages.py — قوالب الرسائل والأزرار

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
from config import CHANNEL_ID, KICHE_NUMBER, PRICES, IMAGES

DAYS_AR = {0:"الاثنين",1:"الثلاثاء",2:"الأربعاء",3:"الخميس",4:"الجمعة",5:"السبت",6:"الأحد"}

def today_str():
    n = datetime.now()
    return f"{DAYS_AR[n.weekday()]} | {n.day:02d}/{n.month:02d}/{n.year}"

def footer():
    return f"\n─────────────────\n📢 {CHANNEL_ID} | 🤖 @RaqeebIQBot"

# ─── رسالة الترحيب ───
def welcome_msg():
    text = (
        "أهلاً بك في رقيب 👁️\n"
        "رفيقك في سوق الأسهم العراقية 📊\n\n"
        "أنا بوت متخصص بمتابعة البورصة العراقية\n"
        "أرسل لك كل ما تحتاجه يومياً:\n\n"
        "📊 تقرير يومي بعد إغلاق السوق\n"
        "🔴 أخبار عاجلة فور نشرها\n"
        "🔍 بحث عن أي سهم تريده\n"
        "🔔 تنبيهات مخصصة على أسهمك"
        + footer()
    )
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🚀 ابدأ الاستخدام", callback_data="start_use")
    ]])
    return text, kb

# ─── طلب الاشتراك بالقناة ───
def join_channel_msg():
    text = "⚠️ للمتابعة اشترك بقناتنا أولاً" + footer()
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("📢 اشترك بـ RaqeebIQ", url=f"https://t.me/{CHANNEL_ID.replace('@','')}")
    ]])
    return text, kb

# ─── القائمة الرئيسية ───
def main_menu_msg(data):
    if data:
        change = data.get("change_pct", "0%")
        arrow = "▲" if "-" not in str(change) else "▼"
        text = (
            f"📈 التقرير اليومي لسوق الأسهم العراقية\n"
            f"📅 {today_str()}\n\n"
            f"📊 ملخص أداء السوق\n\n"
            f"🔹 المؤشر الرئيسي:\n"
            f"{data.get('index','—')} نقطة {arrow} ({change})\n\n"
            f"🔹 إجمالي قيمة التداول:\n"
            f"{data.get('value','—')} دينار عراقي\n\n"
            f"🔹 عدد الصفقات المنفذة:\n"
            f"{data.get('trades','—')} صفقة\n\n"
            f"🔹 حركة الأسهم:\n"
            f"📈 مرتفعة: {data.get('up','—')}\n"
            f"📉 منخفضة: {data.get('down','—')}\n"
            f"➖ مستقرة: {data.get('flat','—')}"
            + footer()
        )
    else:
        text = (
            f"📈 التقرير اليومي لسوق الأسهم العراقية\n"
            f"📅 {today_str()}\n\n"
            "⏳ جاري تحميل البيانات..." + footer()
        )
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔴 أبرز أسهم اليوم", callback_data="top_stocks"),
            InlineKeyboardButton("🔍 بحث عن سهم",      callback_data="search_stock"),
        ],
        [
            InlineKeyboardButton("🔔 تنبيهاتي", callback_data="my_alerts"),
            InlineKeyboardButton("💳 اشتراكي",  callback_data="my_sub"),
        ],
    ])
    return text, kb

# ─── أبرز الأسهم ───
def top_stocks_msg(stocks):
    up   = stocks.get("up",   [])
    down = stocks.get("down", [])
    up_lines   = "\n".join([f"{i+1}. {s['symbol']} ▲ +{s['change']}%" for i, s in enumerate(up)])   or "لا توجد بيانات"
    down_lines = "\n".join([f"{i+1}. {s['symbol']} ▼ {s['change']}%" for i, s in enumerate(down)]) or "لا توجد بيانات"
    text = (
        f"🔴 أبرز أسهم جلسة اليوم\n"
        f"📅 {today_str()}\n\n"
        f"📈 الأكثر ارتفاعاً:\n{up_lines}\n\n"
        f"📉 الأكثر انخفاضاً:\n{down_lines}"
        + footer()
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]])
    return text, kb

# ─── البحث عن سهم ───
def search_stock_msg():
    text = (
        "🔍 البحث عن سهم\n\n"
        "أرسل رمز السهم للحصول على تفاصيله\n"
        "مثال: BBOB أو TELE أو BCOI\n\n"
        "💡 يمكنك البحث بالرمز أو اسم الشركة"
        + footer()
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]])
    return text, kb

# ─── نتيجة البحث ───
def stock_result_msg(data):
    arrow = "▲" if data.get("change","").startswith("-") is False else "▼"
    text = (
        f"🏢 {data.get('name', data['symbol'])} | {data['symbol']}\n\n"
        f"💰 السعر الحالي: {data.get('price','—')} دينار\n"
        f"📈 التغيير: {arrow} {data.get('change_pct','—')}\n"
        f"📊 أعلى سعر اليوم: {data.get('high','—')}\n"
        f"📊 أدنى سعر اليوم: {data.get('low','—')}\n"
        f"🔄 حجم التداول: {data.get('volume','—')}"
        + footer()
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]])
    return text, kb

# ─── سهم غير موجود ───
def stock_not_found_msg(symbol):
    text = (
        f"❌ لم يتم العثور على السهم: {symbol}\n\n"
        "تأكد من الرمز وحاول مرة أخرى\n"
        "مثال: BBOB أو TELE"
        + footer()
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]])
    return text, kb

# ─── التنبيهات ───
def alerts_msg(alerts):
    if not alerts:
        body = "ليس لديك تنبيهات حالياً\n\nأضف تنبيهاً بكتابة:\n/تنبيه BBOB 5"
    else:
        lines = []
        for a in alerts:
            t = "📈 ارتفاع" if a["alert_type"] == "up" else "📉 انخفاض" if a["alert_type"] == "down" else "💰 سعر"
            lines.append(f"• {a['symbol']} | {t} {a['value']}{'%' if a['alert_type'] != 'price' else ' دينار'} — /حذف_{a['id']}")
        body = "\n".join(lines)
    text = f"🔔 تنبيهاتي\n\n{body}" + footer()
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]])
    return text, kb

# ─── الاشتراك ───
def subscription_msg(user):
    from datetime import datetime
    now = datetime.now()
    sub_end = user.get("sub_end")
    trial_end = user.get("trial_end")
    if sub_end and datetime.fromisoformat(sub_end) > now:
        end_date = datetime.fromisoformat(sub_end).strftime("%d/%m/%Y")
        sub_type = "شهري" if user.get("sub_type") == "monthly" else "سنوي"
        status = f"✅ اشتراك {sub_type}\nساري حتى: {end_date}"
    elif trial_end and datetime.fromisoformat(trial_end) > now:
        end_date = datetime.fromisoformat(trial_end).strftime("%d/%m/%Y")
        status = f"🎁 تجربة مجانية\nتنتهي: {end_date}"
    else:
        status = "🔒 انتهى اشتراكك"
    text = (
        f"💳 اشتراكي\n\n{status}\n\n"
        f"─────────────────\n"
        f"📅 شهري  — {PRICES['monthly']:,} دينار عراقي\n"
        f"📆 سنوي  — {PRICES['yearly']:,} دينار عراقي\n"
        f"(توفر {PRICES['monthly']*12 - PRICES['yearly']:,} دينار)"
        + footer()
    )
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📅 اشتراك شهري",  callback_data="sub_monthly"),
            InlineKeyboardButton("📆 اشتراك سنوي",  callback_data="sub_yearly"),
        ],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
    ])
    return text, kb

# ─── تعليمات الدفع ───
def payment_msg(plan):
    plan_name = "شهري" if plan == "monthly" else "سنوي"
    amount    = PRICES[plan]
    text = (
        f"💳 تعليمات الدفع\n\n"
        f"الخطة: {plan_name} — {amount:,} دينار\n\n"
        f"حول المبلغ عبر:\n\n"
        f"🏦 كي كارد\n"
        f"رقم الحساب: {KICHE_NUMBER}\n\n"
        f"أو عبر QR الموجود في الصورة أعلاه\n\n"
        f"📸 بعد التحويل أرسل صورة الإيصال هنا"
        + footer()
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="my_sub")]])
    return text, kb

# ─── خبر عاجل ───
def news_msg(title, body=""):
    text = (
        f"🔴 خبر عاجل | سوق العراق للأوراق المالية\n\n"
        f"{title}\n"
        f"{body}\n\n"
        f"📅 {today_str()}"
        + footer()
    )
    return text

# ─── تنبيه فتح السوق ───
def market_open_msg():
    return (
        f"🔔 السوق مفتوح الآن\n"
        f"📅 {today_str()}\n\n"
        f"تداول موفق للجميع 📊"
        + footer()
    )

# ─── تقرير أسبوعي ───
def weekly_report_msg(data, stocks):
    up   = stocks.get("up",   [])[:3]
    down = stocks.get("down", [])[:3]
    best  = up[0]["symbol"]   + f" ▲ +{up[0]['change']}%"   if up   else "—"
    worst = down[0]["symbol"] + f" ▼ {down[0]['change']}%"  if down else "—"
    text = (
        f"📊 ملخص أسبوع التداول\n"
        f"📅 {today_str()}\n\n"
        f"🔹 المؤشر: {data.get('index','—')} ({data.get('change_pct','—')})\n"
        f"💰 إجمالي التداول: {data.get('value','—')}\n\n"
        f"🏆 أفضل سهم: {best}\n"
        f"💔 أسوأ سهم:  {worst}"
        + footer()
    )
    return text

# ─── تقرير شهري ───
def monthly_report_msg(data, stocks):
    up   = stocks.get("up",   [])[:3]
    down = stocks.get("down", [])[:3]
    best  = up[0]["symbol"]   + f" ▲ +{up[0]['change']}%"   if up   else "—"
    worst = down[0]["symbol"] + f" ▼ {down[0]['change']}%"  if down else "—"
    text = (
        f"📅 ملخص شهر {datetime.now().strftime('%B %Y')}\n\n"
        f"📈 أداء المؤشر: {data.get('change_pct','—')}\n"
        f"💰 إجمالي التداول: {data.get('value','—')}\n\n"
        f"🏆 أفضل سهم الشهر: {best}\n"
        f"💔 أسوأ سهم الشهر:  {worst}"
        + footer()
    )
    return text

# ─── تنبيه انتهاء الاشتراك (قبل يوم) ───
def expiry_warning_msg(end_date):
    text = (
        f"⚠️ رقيب | تنبيه\n\n"
        f"ينتهي اشتراكك غداً! ({end_date})\n"
        f"جدد الآن لتستمر بمتابعة السوق 📊\n\n"
        f"للتجديد: /اشتراك"
        + footer()
    )
    return text

# ─── رسالة انتهاء الاشتراك ───
def expiry_msg():
    text = (
        f"🔒 رقيب | انتهى اشتراكك\n\n"
        f"للاستمرار اختر خطتك:\n\n"
        f"📅 شهري  — {PRICES['monthly']:,} دينار عراقي\n"
        f"📆 سنوي  — {PRICES['yearly']:,} دينار عراقي\n"
        f"(توفر {PRICES['monthly']*12 - PRICES['yearly']:,} دينار)\n\n"
        f"للاشتراك أرسل /اشتراك"
        + footer()
    )
    return text

# ─── تنبيه سهم ───
def stock_alert_msg(symbol, alert_type, value, current_price):
    if alert_type == "up":
        icon, desc = "📈", f"ارتفع +{value}%"
    elif alert_type == "down":
        icon, desc = "📉", f"انخفض {value}%"
    else:
        icon, desc = "💰", f"وصل لسعر {value} دينار"
    text = (
        f"🔔 تنبيهك تحقق!\n\n"
        f"🏢 {symbol}\n"
        f"{icon} {desc}\n"
        f"💰 السعر الحالي: {current_price} دينار\n\n"
        f"📅 {today_str()}"
        + footer()
    )
    return text
