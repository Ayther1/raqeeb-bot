from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from config import IMAGES
from database import (get_all_active, get_expiring_tomorrow,
                      is_news_sent, mark_news, get_all_watches, is_active)
from scraper import get_market_summary, get_top_stocks, get_isx_news, get_company_news
from messages import (msg_daily, msg_weekly, msg_monthly, msg_open,
                      msg_news, msg_company_update, msg_expiry_warn)
from keyboards import kb_main

async def _broadcast(bot, image_key, text, kb=None, only_active=True):
    users = await get_all_active(only_active)
    sent = 0
    for uid in users:
        try:
            await bot.send_photo(chat_id=uid, photo=IMAGES[image_key],
                                 caption=text, reply_markup=kb)
            sent += 1
        except Exception as e:
            print(f"[Scheduler] ❌ {uid}: {e}")
    print(f"[Scheduler] ✅ أُرسل لـ {sent} مستخدم")

async def job_market_open(bot):
    print(f"[Scheduler] 🔔 فتح السوق {datetime.now()}")
    await _broadcast(bot, "open", msg_open())

async def job_daily(bot):
    print(f"[Scheduler] 📊 تقرير يومي {datetime.now()}")
    data = get_market_summary()
    await _broadcast(bot, "daily", msg_daily(data), kb_main())

async def job_weekly(bot):
    print(f"[Scheduler] 📅 تقرير أسبوعي {datetime.now()}")
    data   = get_market_summary()
    stocks = get_top_stocks()
    if data:
        await _broadcast(bot, "weekly", msg_weekly(data, stocks))

async def job_monthly(bot):
    print(f"[Scheduler] 📆 تقرير شهري {datetime.now()}")
    data   = get_market_summary()
    stocks = get_top_stocks()
    if data:
        await _broadcast(bot, "monthly", msg_monthly(data, stocks))

async def job_news(bot):
    news_list = get_isx_news()
    for news in news_list:
        if await is_news_sent(news["id"]):
            continue
        await mark_news(news["id"])
        text  = msg_news(news["title"], news["source"])
        users = await get_all_active()
        for uid in users:
            try:
                await bot.send_photo(chat_id=uid, photo=IMAGES["news"], caption=text)
            except: pass
        print(f"[Scheduler] 📰 {news['title'][:50]}")

async def job_company_watch(bot):
    watches = await get_all_watches()
    if not watches:
        return
    # جمع الشركات الفريدة
    companies = {}
    for w in watches:
        companies.setdefault(w["company"], []).append(w["user_id"])
    for company, user_ids in companies.items():
        news = get_company_news(company)
        if not news:
            continue
        text = msg_company_update(company, news)
        for uid in user_ids:
            if not await is_active(uid):
                continue
            try:
                await bot.send_photo(chat_id=uid, photo=IMAGES["news"], caption=text)
            except: pass

async def job_expiry(bot):
    expiring = await get_expiring_tomorrow()
    for u in expiring:
        end = u.get("sub_end") or u.get("trial_end")
        end_str = end[:10] if end else "—"
        try:
            await bot.send_message(u["user_id"], msg_expiry_warn(end_str))
        except: pass

def setup_scheduler(bot):
    s = AsyncIOScheduler(timezone="Asia/Baghdad")
    # فتح السوق — 9:45 ص أحد-خميس
    s.add_job(job_market_open, CronTrigger(day_of_week="sun,mon,tue,wed,thu", hour=9,  minute=45), args=[bot])
    # تقرير يومي — 3:00 م أحد-خميس
    s.add_job(job_daily,       CronTrigger(day_of_week="sun,mon,tue,wed,thu", hour=15, minute=0),  args=[bot])
    # أخبار — كل 15 دقيقة
    s.add_job(job_news,        CronTrigger(minute="*/15"),                                          args=[bot])
    # مراقبة شركات — يومياً 4:00 م
    s.add_job(job_company_watch, CronTrigger(day_of_week="sun,mon,tue,wed,thu", hour=16, minute=0), args=[bot])
    # تقرير أسبوعي — خميس 4:30 م
    s.add_job(job_weekly,      CronTrigger(day_of_week="thu", hour=16, minute=30),                 args=[bot])
    # تقرير شهري — أول أحد كل شهر
    s.add_job(job_monthly,     CronTrigger(day_of_week="sun", day="1-7", hour=10, minute=0),       args=[bot])
    # فحص انتهاء الاشتراكات — 9:00 ص يومياً
    s.add_job(job_expiry,      CronTrigger(hour=9, minute=0),                                      args=[bot])
    return s
