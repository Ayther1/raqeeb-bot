# scheduler.py — الجدول الزمني للمهام التلقائية

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from config import IMAGES
from database import (
    get_all_active_users, get_expiring_tomorrow,
    is_news_sent, mark_news_sent, get_all_alerts,
    get_user, is_user_active
)
from scraper import (
    get_market_summary, get_top_stocks,
    get_latest_news, get_stock_price_for_alert
)
from messages import (
    main_menu_msg, weekly_report_msg, monthly_report_msg,
    news_msg, market_open_msg, expiry_warning_msg, expiry_msg,
    stock_alert_msg
)
from telegram import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton

# ─── إرسال التقرير اليومي ───
async def send_daily_report(bot):
    print(f"[Scheduler] 📊 إرسال التقرير اليومي - {datetime.now()}")
    users = await get_all_active_users()
    market = get_market_summary()
    stocks = get_top_stocks()
    if not market:
        print("[Scheduler] ❌ فشل جلب بيانات السوق")
        return
    text, kb = main_menu_msg(market)
    sent = 0
    for user_id in users:
        if not await is_user_active(user_id):
            continue
        try:
            await bot.send_photo(
                chat_id=user_id,
                photo=IMAGES["daily"],
                caption=text,
                reply_markup=kb
            )
            sent += 1
        except Exception as e:
            print(f"[Scheduler] ❌ فشل الإرسال للمستخدم {user_id}: {e}")
    print(f"[Scheduler] ✅ أُرسل التقرير لـ {sent} مستخدم")

# ─── تنبيه فتح السوق ───
async def send_market_open(bot):
    print(f"[Scheduler] 🔔 تنبيه فتح السوق - {datetime.now()}")
    users = await get_all_active_users()
    text = market_open_msg()
    for user_id in users:
        if not await is_user_active(user_id):
            continue
        try:
            await bot.send_photo(
                chat_id=user_id,
                photo=IMAGES["open"],
                caption=text
            )
        except Exception as e:
            print(f"[Scheduler] ❌ {user_id}: {e}")

# ─── فحص الأخبار الجديدة ───
async def check_news(bot):
    news_list = get_latest_news()
    if not news_list:
        return
    users = await get_all_active_users()
    for news in news_list:
        if await is_news_sent(news["id"]):
            continue
        # خبر جديد!
        await mark_news_sent(news["id"])
        text = news_msg(news["title"])
        for user_id in users:
            if not await is_user_active(user_id):
                continue
            try:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=IMAGES["news"],
                    caption=text
                )
            except Exception as e:
                print(f"[Scheduler] ❌ news {user_id}: {e}")
        print(f"[Scheduler] 📰 خبر جديد أُرسل: {news['title'][:50]}")

# ─── التقرير الأسبوعي ───
async def send_weekly_report(bot):
    print(f"[Scheduler] 📅 التقرير الأسبوعي - {datetime.now()}")
    users = await get_all_active_users()
    market = get_market_summary()
    stocks = get_top_stocks()
    if not market:
        return
    text = weekly_report_msg(market, stocks)
    for user_id in users:
        if not await is_user_active(user_id):
            continue
        try:
            await bot.send_photo(
                chat_id=user_id,
                photo=IMAGES["weekly"],
                caption=text
            )
        except Exception as e:
            print(f"[Scheduler] ❌ {user_id}: {e}")

# ─── التقرير الشهري ───
async def send_monthly_report(bot):
    print(f"[Scheduler] 📆 التقرير الشهري - {datetime.now()}")
    users = await get_all_active_users()
    market = get_market_summary()
    stocks = get_top_stocks()
    if not market:
        return
    text = monthly_report_msg(market, stocks)
    for user_id in users:
        if not await is_user_active(user_id):
            continue
        try:
            await bot.send_photo(
                chat_id=user_id,
                photo=IMAGES["monthly"],
                caption=text
            )
        except Exception as e:
            print(f"[Scheduler] ❌ {user_id}: {e}")

# ─── تنبيهات انتهاء الاشتراك ───
async def check_expiring(bot):
    expiring = await get_expiring_tomorrow()
    for user in expiring:
        end = user.get("sub_end") or user.get("trial_end")
        end_str = datetime.fromisoformat(end).strftime("%d/%m/%Y")
        try:
            await bot.send_message(
                chat_id=user["user_id"],
                text=expiry_warning_msg(end_str)
            )
        except Exception as e:
            print(f"[Scheduler] ❌ expiry warning {user['user_id']}: {e}")

# ─── فحص تنبيهات الأسهم ───
async def check_stock_alerts(bot):
    alerts = await get_all_alerts()
    if not alerts:
        return
    # جمع الأسهم الفريدة
    symbols = list(set(a["symbol"] for a in alerts))
    prices = {}
    for symbol in symbols:
        price = get_stock_price_for_alert(symbol)
        if price:
            prices[symbol] = price

    for alert in alerts:
        symbol = alert["symbol"]
        current_price = prices.get(symbol)
        if not current_price:
            continue
        triggered = False
        if alert["alert_type"] == "up":
            # نحسب نسبة التغيير - نحتاج سعر الإغلاق السابق (نستخدم تقريب)
            triggered = True  # مبسط - يمكن تحسينه لاحقاً
        elif alert["alert_type"] == "down":
            triggered = True
        elif alert["alert_type"] == "price":
            triggered = current_price >= alert["value"]

        if triggered:
            try:
                from database import delete_alert
                text = stock_alert_msg(
                    symbol, alert["alert_type"],
                    alert["value"], current_price
                )
                await bot.send_photo(
                    chat_id=alert["user_id"],
                    photo=IMAGES["open"],
                    caption=text
                )
                await delete_alert(alert["id"])
            except Exception as e:
                print(f"[Scheduler] ❌ alert {alert['user_id']}: {e}")

# ─── إعداد الجدول ───
def setup_scheduler(bot):
    scheduler = AsyncIOScheduler(timezone="Asia/Baghdad")

    # تنبيه فتح السوق — 9:45 ص (الأحد - الخميس)
    scheduler.add_job(
        send_market_open, CronTrigger(
            day_of_week="sun,mon,tue,wed,thu",
            hour=9, minute=45
        ), args=[bot], id="market_open"
    )

    # التقرير اليومي — 3:00 م (الأحد - الخميس)
    scheduler.add_job(
        send_daily_report, CronTrigger(
            day_of_week="sun,mon,tue,wed,thu",
            hour=15, minute=0
        ), args=[bot], id="daily_report"
    )

    # فحص الأخبار — كل 15 دقيقة
    scheduler.add_job(
        check_news, CronTrigger(minute="*/15"),
        args=[bot], id="check_news"
    )

    # فحص تنبيهات الأسهم — كل 30 دقيقة (أيام التداول)
    scheduler.add_job(
        check_stock_alerts, CronTrigger(
            day_of_week="sun,mon,tue,wed,thu",
            hour="10-15", minute="*/30"
        ), args=[bot], id="stock_alerts"
    )

    # التقرير الأسبوعي — الخميس 4:00 م
    scheduler.add_job(
        send_weekly_report, CronTrigger(
            day_of_week="thu", hour=16, minute=0
        ), args=[bot], id="weekly_report"
    )

    # التقرير الشهري — أول أحد من كل شهر
    scheduler.add_job(
        send_monthly_report, CronTrigger(
            day_of_week="sun", day="1-7", hour=10, minute=0
        ), args=[bot], id="monthly_report"
    )

    # فحص انتهاء الاشتراكات — كل يوم 9:00 ص
    scheduler.add_job(
        check_expiring, CronTrigger(hour=9, minute=0),
        args=[bot], id="check_expiring"
    )

    return scheduler
