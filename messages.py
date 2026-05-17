from datetime import datetime
from config import CHANNEL_ID, KICHE_NUMBER, PRICES, SUPPORT_BOT

DAYS_AR = {0:"الاثنين",1:"الثلاثاء",2:"الأربعاء",3:"الخميس",4:"الجمعة",5:"السبت",6:"الأحد"}

def today_str():
    n = datetime.now()
    return f"{DAYS_AR[n.weekday()]} | {n.day:02d}/{n.month:02d}/{n.year}"

def footer():
    return f"\n─────────────────\n📢 {CHANNEL_ID} | 🤖 @RaqeebIQBot"

# ── الترحيب ──
def msg_welcome():
    return (
        "أهلاً بك في رقيب 👁️\n"
        "رفيقك في سوق الأسهم العراقية 📊\n\n"
        "أنا بوت متخصص بمتابعة البورصة العراقية\n"
        "أرسل لك كل ما تحتاجه يومياً:\n\n"
        "📊 تقرير يومي بعد إغلاق السوق\n"
        "🔴 أخبار عاجلة فور نشرها\n"
        "🔍 بحث عن أي سهم تريده\n"
        "🔔 تنبيهات مخصصة على أسهمك\n"
        "🏢 مراقبة يومية لشركاتك المفضلة"
        + footer()
    )

# ── الاشتراك الإجباري ──
def msg_join():
    return (
        "⚠️ خطوة أخيرة!\n\n"
        "اشترك بقناتنا أولاً ثم اضغط تأكيد الاشتراك"
        + footer()
    )

# ── التقرير اليومي ──
def msg_daily(data):
    if not data:
        return f"📈 التقرير اليومي\n📅 {today_str()}\n\n⏳ جاري تحميل البيانات..." + footer()
    chg = data.get("change_pct", "0%")
    arrow = "▲" if "-" not in str(chg) else "▼"
    return (
        f"📈 التقرير اليومي لسوق الأسهم العراقية\n"
        f"📅 {today_str()}\n\n"
        f"📊 ملخص أداء السوق\n\n"
        f"🔹 المؤشر الرئيسي:\n"
        f"{data.get('index','—')} نقطة {arrow} ({chg})\n\n"
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

# ── أبرز الأسهم ──
def msg_top_stocks(stocks):
    up   = stocks.get("up",   [])
    down = stocks.get("down", [])
    up_l   = "\n".join([f"{i+1}. {s['symbol']} ▲ +{s['change']}%" for i, s in enumerate(up)])   or "لا توجد بيانات"
    down_l = "\n".join([f"{i+1}. {s['symbol']} ▼ {s['change']}%" for i, s in enumerate(down)]) or "لا توجد بيانات"
    return (
        f"🔴 أبرز أسهم جلسة اليوم\n"
        f"📅 {today_str()}\n\n"
        f"📈 الأكثر ارتفاعاً:\n{up_l}\n\n"
        f"📉 الأكثر انخفاضاً:\n{down_l}"
        + footer()
    )

# ── البحث ──
def msg_search():
    return (
        "🔍 البحث عن سهم\n\n"
        "أرسل رمز السهم\n"
        "مثال: BBOB أو TELE أو AAPL"
        + footer()
    )

def msg_searching():
    return "🔍 جاري البحث... قد يستغرق بعض الثواني ⏳"

def msg_stock(data):
    chg = data.get("change_pct", "—")
    arrow = "▼" if "-" in str(chg) else "▲"
    src = data.get("source", "")
    return (
        f"🏢 {data.get('name', data['symbol'])} | {data['symbol']}\n\n"
        f"💰 السعر الحالي: {data.get('price','—')}\n"
        f"📊 التغيير: {arrow} {chg}\n"
        f"📈 أعلى سعر اليوم: {data.get('high','—')}\n"
        f"📉 أدنى سعر اليوم: {data.get('low','—')}\n"
        f"🔄 حجم التداول: {data.get('volume','—')}\n\n"
        f"📡 المصدر: {src}"
        + footer()
    )

def msg_not_found(symbol):
    return (
        f"❌ لم يتم العثور على: {symbol}\n\n"
        "تأكد من الرمز وحاول مرة أخرى\n"
        "مثال: BBOB أو TELE"
        + footer()
    )

# ── الاشتراك ──
def msg_sub(user):
    now = datetime.now()
    sub_end   = user.get("sub_end")
    trial_end = user.get("trial_end")
    if sub_end and datetime.fromisoformat(sub_end) > now:
        end_date = datetime.fromisoformat(sub_end).strftime("%d/%m/%Y")
        sub_type = "شهري" if user.get("sub_type") == "monthly" else "سنوي"
        status = f"✅ اشتراك {sub_type} — ساري حتى {end_date}"
    elif trial_end and datetime.fromisoformat(trial_end) > now:
        end_date = datetime.fromisoformat(trial_end).strftime("%d/%m/%Y")
        status = f"🎁 تجربة مجانية — تنتهي {end_date}"
    else:
        status = "🔒 منتهي"
    return (
        f"💳 اشتراكي\n\n"
        f"الحالة: {status}\n\n"
        f"─────────────────\n"
        f"📅 شهري  — {PRICES['monthly']:,} دينار عراقي\n"
        f"📆 سنوي  — {PRICES['yearly']:,} دينار عراقي\n"
        f"(توفر {PRICES['monthly']*12 - PRICES['yearly']:,} دينار)"
        + footer()
    )

def msg_payment(plan):
    plan_ar = "شهري" if plan == "monthly" else "سنوي"
    amount  = PRICES[plan]
    return (
        f"💳 تعليمات الدفع\n\n"
        f"الخطة: {plan_ar} — {amount:,} دينار عراقي\n\n"
        f"حول المبلغ عبر كي كارد:\n"
        f"🏦 رقم الحساب: {KICHE_NUMBER}\n\n"
        f"أو عبر QR الموجود في الصورة أعلاه\n\n"
        f"بعد التحويل:\n"
        f"1️⃣ أرسل صورة الإيصال\n"
        f"2️⃣ اكتب اسمك الذي حولت منه"
        + footer()
    )

def msg_receipt_confirm(plan):
    plan_ar = "شهري" if plan == "monthly" else "سنوي"
    amount  = PRICES[plan]
    return (
        f"✅ استلمنا طلبك!\n\n"
        f"الخطة: {plan_ar} — {amount:,} دينار\n\n"
        f"سيتم مراجعة الإيصال وتفعيل اشتراكك خلال دقائق 🙏\n\n"
        f"للاستفسار تواصل مع: {SUPPORT_BOT}"
        + footer()
    )

# ── التنبيهات ──
def msg_alerts(alerts, name):
    if not alerts:
        body = "ليس لديك تنبيهات حالياً"
    else:
        lines = []
        for a in alerts:
            icon = "📈" if a["direction"] == "up" else "📉"
            lines.append(f"{icon} {a['symbol']} — {a['pct']}% {'صعود' if a['direction']=='up' else 'نزول'}")
        body = "\n".join(lines)
    return (
        f"🔔 الأسهم المفضلة لـ {name}\n\n"
        f"{body}\n\n"
        f"─────────────────\n"
        f"لإضافة تنبيه جديد اضغط ➕\n"
        f"لحذف تنبيه اضغط على اسمه"
        + footer()
    )

def msg_add_alert():
    return (
        "🔔 إضافة تنبيه جديد\n\n"
        "أرسل رسالة بهذا الشكل:\n\n"
        "اسم السهم — النسبة — الاتجاه\n\n"
        "مثال:\n"
        "BBOB 5 صعود\n"
        "TELE 3 نزول\n\n"
        "يعني: نبهني إذا BBOB صعد 5%"
        + footer()
    )

def msg_alert_added(symbol, pct, direction):
    icon = "📈" if direction == "up" else "📉"
    dir_ar = "صعود" if direction == "up" else "نزول"
    return f"✅ تم إضافة التنبيه\n\n{icon} {symbol} — {pct}% {dir_ar}"

def msg_alert_triggered(symbol, direction, pct, price):
    icon = "📈" if direction == "up" else "📉"
    dir_ar = "ارتفع" if direction == "up" else "انخفض"
    return (
        f"🔔 تنبيهك تحقق!\n\n"
        f"🏢 {symbol}\n"
        f"{icon} {dir_ar} {pct}%\n"
        f"💰 السعر الحالي: {price}\n\n"
        f"📅 {today_str()}"
        + footer()
    )

# ── مراقبة الشركات ──
def msg_watchlist(watches, name, limit):
    if not watches:
        body = "ليس لديك شركات مراقبة حالياً"
    else:
        body = "\n".join([f"🏢 {w['company']}" for w in watches])
    return (
        f"🏢 شركاتك المراقبة — {name}\n\n"
        f"{body}\n\n"
        f"─────────────────\n"
        f"الحد المسموح: {len(watches)}/{limit} شركة\n"
        f"لإضافة شركة اضغط ➕"
        + footer()
    )

def msg_add_watch():
    return (
        "🏢 إضافة شركة للمراقبة\n\n"
        "أرسل اسم الشركة أو رمزها\n\n"
        "مثال: آسياسيل أو ASCE"
        + footer()
    )

def msg_watch_added(company):
    return f"✅ تم إضافة {company} لقائمة المراقبة\n\nستصلك تحديثات يومية 📊"

def msg_watch_limit(limit):
    return (
        f"⚠️ وصلت للحد الأقصى ({limit} شركة)\n\n"
        f"لمراقبة شركات أكثر:\n"
        f"شهري: 5 شركات\n"
        f"سنوي: 10 شركات"
        + footer()
    )

def msg_company_update(company, news_list):
    lines = [f"🏢 تحديثات {company}\n📅 {today_str()}\n"]
    for n in news_list:
        lines.append(f"• {n['title']} ({n['source']})")
    if not news_list:
        lines.append("لا توجد أخبار جديدة اليوم")
    return "\n".join(lines) + footer()

# ── الأخبار ──
def msg_news(title, source):
    return (
        f"🔴 خبر عاجل\n\n"
        f"{title}\n\n"
        f"📡 المصدر: {source}\n"
        f"📅 {today_str()}"
        + footer()
    )

# ── تنبيه فتح السوق ──
def msg_open():
    return f"🔔 السوق مفتوح الآن\n📅 {today_str()}\n\nتداول موفق 📊" + footer()

# ── تقرير أسبوعي ──
def msg_weekly(data, stocks):
    up   = stocks.get("up",   [])
    down = stocks.get("down", [])
    best  = f"{up[0]['symbol']} ▲ +{up[0]['change']}%"   if up   else "—"
    worst = f"{down[0]['symbol']} ▼ {down[0]['change']}%" if down else "—"
    return (
        f"📊 ملخص أسبوع التداول\n📅 {today_str()}\n\n"
        f"🔹 المؤشر: {data.get('index','—')} ({data.get('change_pct','—')})\n"
        f"💰 التداول: {data.get('value','—')}\n\n"
        f"🏆 أفضل سهم: {best}\n"
        f"💔 أسوأ سهم: {worst}"
        + footer()
    )

# ── تقرير شهري ──
def msg_monthly(data, stocks):
    from datetime import datetime
    up   = stocks.get("up",   [])
    down = stocks.get("down", [])
    best  = f"{up[0]['symbol']} ▲ +{up[0]['change']}%"   if up   else "—"
    worst = f"{down[0]['symbol']} ▼ {down[0]['change']}%" if down else "—"
    return (
        f"📅 ملخص شهر {datetime.now().strftime('%B %Y')}\n\n"
        f"📈 المؤشر: {data.get('change_pct','—')}\n"
        f"💰 التداول: {data.get('value','—')}\n\n"
        f"🏆 أفضل سهم: {best}\n"
        f"💔 أسوأ سهم: {worst}"
        + footer()
    )

# ── انتهاء الاشتراك ──
def msg_expiry_warn(end_date):
    return (
        f"⚠️ تنبيه | رقيب\n\n"
        f"ينتهي اشتراكك غداً ({end_date})\n"
        f"جدد الآن لتستمر 📊"
        + footer()
    )

def msg_expired():
    return (
        f"🔒 انتهى اشتراكك\n\n"
        f"للاستمرار اضغط /start واختر خطتك\n\n"
        f"📅 شهري  — {PRICES['monthly']:,} دينار\n"
        f"📆 سنوي  — {PRICES['yearly']:,} دينار"
        + footer()
    )

# ── أدمن ──
def msg_admin_request(user, plan):
    plan_ar = "شهري" if plan == "monthly" else "سنوي"
    return (
        f"📩 طلب اشتراك جديد\n\n"
        f"👤 الاسم: {user.full_name}\n"
        f"🆔 ID: {user.id}\n"
        f"📅 الخطة: {plan_ar}\n"
        f"💰 المبلغ: {PRICES[plan]:,} دينار"
    )

def msg_activated(plan, end_str):
    plan_ar = "شهري" if plan == "monthly" else "سنوي"
    return f"✅ تم التفعيل\n\nالخطة: {plan_ar}\nحتى: {end_str}"

def msg_user_activated(plan, end_str):
    plan_ar = "شهري" if plan == "monthly" else "سنوي"
    return (
        f"✅ تم تفعيل اشتراكك!\n\n"
        f"مرحباً بك في رقيب 🎉\n"
        f"الخطة: {plan_ar}\n"
        f"ساري حتى: {end_str}\n\n"
        f"استمتع بمتابعة سوق الأسهم العراقية 📊"
        + footer()
    )
