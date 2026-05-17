"""
خدمة التقارير - يومي، أسبوعي، شهري
"""
import asyncio
from datetime import datetime
from services.market import get_market_summary, get_top_stocks, is_market_open, get_next_open_time
from services.news import get_latest_news, format_news_item
from database.db import get_latest_news as db_news

DAYS_AR = {
    "Monday": "الاثنين",
    "Tuesday": "الثلاثاء",
    "Wednesday": "الأربعاء",
    "Thursday": "الخميس",
    "Friday": "الجمعة",
    "Saturday": "السبت",
    "Sunday": "الأحد",
}

MONTHS_AR = {
    1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل",
    5: "مايو", 6: "يونيو", 7: "يوليو", 8: "أغسطس",
    9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
}

def ar_date(dt: datetime = None) -> str:
    if not dt:
        dt = datetime.now()
    day_en = dt.strftime("%A")
    day_ar = DAYS_AR.get(day_en, day_en)
    month_ar = MONTHS_AR.get(dt.month, "")
    return f"{day_ar}، {dt.day} {month_ar} {dt.year}"

async def build_daily_report() -> str:
    """بناء التقرير اليومي"""
    now = datetime.now()
    summary = await get_market_summary()
    top = await get_top_stocks()

    header = (
        f"📊 *التقرير اليومي — سوق العراق للأوراق المالية*\n"
        f"📅 {ar_date(now)}\n"
        f"{'─' * 32}\n\n"
    )

    market_status = ""
    if is_market_open():
        market_status = "🟢 *السوق مفتوح الآن*\n"
    else:
        next_open = get_next_open_time()
        market_status = f"🔴 *السوق مغلق* — يفتح {next_open}\n"

    if summary.get("index"):
        market_status += f"📈 مؤشر ISX15: `{summary['index']}`\n"

    # أبرز الأسهم
    stocks_text = "\n🏆 *أبرز الأسهم اليوم:*\n"
    if top:
        for s in top[:8]:
            change = s.get("change", "—")
            arrow = "📈" if "+" in str(change) else ("📉" if "-" in str(change) else "➡️")
            stocks_text += f"{arrow} `{s['symbol']}` — {s['company'][:12]}\n   💰 {s['price']} | {change}\n"
    else:
        stocks_text += "_لا توجد بيانات متاحة حالياً_\n"

    # آخر الأخبار من قاعدة البيانات
    news_items = db_news(4)
    news_text = "\n📰 *آخر الأخبار:*\n"
    if news_items:
        for n in news_items:
            news_text += f"• {n['title'][:80]}\n  _{n['source']}_\n\n"
    else:
        news_text += "_لا توجد أخبار جديدة_\n"

    footer = f"\n{'─' * 32}\n🤖 رقيب — تحديث: {now.strftime('%H:%M')}"

    return header + market_status + stocks_text + news_text + footer

async def build_weekly_report() -> str:
    """التقرير الأسبوعي"""
    now = datetime.now()
    top = await get_top_stocks()

    report = (
        f"📊 *التقرير الأسبوعي — سوق العراق للأوراق المالية*\n"
        f"📅 الأسبوع المنتهي في: {ar_date(now)}\n"
        f"{'─' * 32}\n\n"
        f"📈 *ملخص الأسبوع:*\n"
        f"_يتم تجميع البيانات من ISX و RS.iq_\n\n"
    )

    if top:
        report += "🏆 *أكثر الأسهم تداولاً:*\n"
        for s in top[:10]:
            change = s.get("change", "—")
            arrow = "📈" if "+" in str(change) else ("📉" if "-" in str(change) else "➡️")
            report += f"{arrow} `{s['symbol']}` {s['company'][:15]} — {s['price']}\n"

    report += f"\n{'─' * 32}\n🤖 رقيب | {now.strftime('%Y-%m-%d %H:%M')}"
    return report

async def build_monthly_report() -> str:
    """التقرير الشهري"""
    now = datetime.now()
    month_ar = MONTHS_AR.get(now.month, "")

    report = (
        f"📊 *التقرير الشهري — {month_ar} {now.year}*\n"
        f"سوق العراق للأوراق المالية\n"
        f"{'─' * 32}\n\n"
        f"📈 يتم تجميع البيانات الشهرية من مصادر متعددة\n\n"
        f"_هيئة الأوراق المالية — ISX — RS.iq_\n\n"
    )

    top = await get_top_stocks()
    if top:
        report += "🏆 *أبرز أسهم الشهر:*\n"
        for s in top[:12]:
            change = s.get("change", "—")
            report += f"• `{s['symbol']}` — {s['company'][:15]} | {s['price']} ({change})\n"

    report += f"\n{'─' * 32}\n🤖 رقيب | {now.strftime('%Y-%m-%d')}"
    return report

def market_closed_message() -> str:
    """رسالة إغلاق السوق"""
    next_open = get_next_open_time()
    return (
        f"🔴 *تم إغلاق السوق*\n\n"
        f"سوق العراق للأوراق المالية أغلق أبوابه لهذا اليوم.\n\n"
        f"⏰ يفتح السوق القادم:\n"
        f"📅 *{next_open}*\n\n"
        f"_ساعات عمل السوق: الأحد - الخميس، 10:00 ص — 1:00 م_"
    )
