"""
معالجات الأوامر والرسائل
"""
import asyncio
import re
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

from config import ADMIN_ID, CHANNEL_ID, KICHE_NUMBER, QR_IMAGE, PRICES, SUPPORT_USERNAME
from database.db import (
    upsert_user, get_user, get_all_users, get_all_payments,
    add_payment, approve_payment, get_all_user_ids,
    set_subscription, is_subscribed, get_monitoring_limit,
    add_alert, get_user_alerts, delete_alert, get_all_active_alerts,
    add_watchlist, get_user_watchlist, remove_watchlist, get_all_watchlist,
    get_latest_news
)
from services.market import (
    get_stock_data, get_top_stocks, is_market_open,
    get_next_open_time, IRAQI_STOCKS, get_market_summary
)
from services.reports import build_daily_report, build_weekly_report, build_monthly_report, ar_date
from services.news import get_company_news, format_news_item
from utils.keyboards import (
    main_menu, back_button, after_search, subscription_menu,
    payment_confirm, alerts_menu, alert_direction_menu,
    watchlist_menu, channel_join_menu, reports_menu, admin_menu,
    approve_payment_btn
)

# ─── حالات المحادثة ────────────────────────────────────────────────────────────

(
    WAITING_STOCK_SYMBOL,
    WAITING_RECEIPT,
    WAITING_SENDER_NAME,
    WAITING_ALERT_SYMBOL,
    WAITING_ALERT_PCT,
    WAITING_ALERT_DIR,
    WAITING_WATCH_SYMBOL,
    WAITING_BROADCAST,
) = range(8)

user_sub_type = {}  # مؤقت لحفظ نوع الاشتراك

# ─── مساعد: التحقق من الاشتراك بالقناة ────────────────────────────────────────

async def check_channel_member(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ("member", "administrator", "creator")
    except:
        return False

# ─── /start ───────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    is_new = upsert_user(user.id, user.username, user.full_name)

    # إشعار الأدمن بالمستخدم الجديد
    if is_new:
        try:
            await ctx.bot.send_message(
                ADMIN_ID,
                f"👤 *مستخدم جديد دخل البوت!*\n\n"
                f"🆔 ID: `{user.id}`\n"
                f"👤 الاسم: {user.full_name}\n"
                f"🔗 يوزر: @{user.username or 'لا يوجد'}\n"
                f"⏰ {ar_date()}",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass

    # رسالة الترحيب
    welcome = (
        f"📊 *مرحباً {user.first_name}!*\n\n"
        f"أنا *رقيب* — بوتك الذكي لمتابعة *سوق العراق للأوراق المالية* 🇮🇶\n\n"
        f"أقدم لك:\n"
        f"• 📈 أسعار الأسهم لحظة بلحظة\n"
        f"• 🔔 تنبيهات مخصصة على أسهمك\n"
        f"• 📰 أخبار البورصة العراقية فور نشرها\n"
        f"• 📊 تقارير يومية وأسبوعية وشهرية\n\n"
        f"للبدء، اشترك بقناتنا أولاً 👇"
    )
    await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=channel_join_menu())

# ─── تأكيد الاشتراك بالقناة ──────────────────────────────────────────────────

async def verify_join(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    is_member = await check_channel_member(ctx.bot, user_id)
    if not is_member:
        await query.edit_message_text(
            "❌ لم يتم التحقق من اشتراكك بالقناة.\n\n"
            "اشترك أولاً ثم اضغط تأكيد الاشتراك مجدداً.",
            reply_markup=channel_join_menu()
        )
        return

    await query.edit_message_text(
        "✅ *تم التحقق من اشتراكك!*\n\n"
        "مرحباً بك في رقيب 🎉",
        parse_mode=ParseMode.MARKDOWN
    )
    await asyncio.sleep(1)
    report = await build_daily_report()
    await ctx.bot.send_message(
        query.message.chat_id,
        report,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu()
    )

# ─── القائمة الرئيسية ─────────────────────────────────────────────────────────

async def show_main_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    report = await build_daily_report()
    await query.edit_message_text(
        report,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu()
    )

# ─── بحث عن سهم ──────────────────────────────────────────────────────────────

async def start_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔍 *بحث عن سهم*\n\n"
        "أرسل رمز الشركة (مثال: `BBOB`، `TZNI`، `BNOI`)\n\n"
        "_💡 الرمز يكون بالأحرف الإنجليزية_",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=back_button()
    )
    return WAITING_STOCK_SYMBOL

async def process_stock_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.strip().upper()

    # تحقق من الرمز
    if not re.match(r'^[A-Z]{2,6}$', symbol):
        await update.message.reply_text(
            "❌ رمز غير صحيح. أرسل رمز مثل `BBOB` أو `TZNI`",
            parse_mode=ParseMode.MARKDOWN
        )
        return WAITING_STOCK_SYMBOL

    # رسالة التحميل
    loading_msg = await update.message.reply_text(
        f"⏳ *جاري تحميل بيانات `{symbol}`...*\n_قد يستغرق بعض ثوانٍ_",
        parse_mode=ParseMode.MARKDOWN
    )

    # جلب البيانات
    data = await get_stock_data(symbol)
    news = await get_company_news(symbol)

    # تنسيق النتيجة
    company = data.get("company", symbol)
    price = data.get("price") or "—"
    change = data.get("change") or "—"
    volume = data.get("volume") or "—"
    high = data.get("high") or "—"
    low = data.get("low") or "—"
    timestamp = data.get("timestamp", "")
    sources = "، ".join(data.get("sources", [])) or "ISX"

    if "+" in str(change):
        change_icon = "📈"
    elif "-" in str(change):
        change_icon = "📉"
    else:
        change_icon = "➡️"

    result = (
        f"🏢 *{company}* — `{symbol}`\n"
        f"{'─' * 30}\n\n"
        f"💰 *السعر الحالي:* `{price}` د.ع\n"
        f"{change_icon} *التغير:* `{change}`\n"
        f"📊 *حجم التداول:* `{volume}`\n"
        f"🔺 *أعلى سعر:* `{high}`\n"
        f"🔻 *أدنى سعر:* `{low}`\n\n"
        f"🕒 *آخر تحديث:* {timestamp}\n"
        f"📡 *المصدر:* {sources}\n"
    )

    # إضافة الأخبار إن وجدت
    if news:
        result += f"\n📰 *آخر مستجدات الشركة:*\n"
        for n in news[:3]:
            result += f"• {n['title'][:70]}\n  _{n.get('source', '')}_ | {n.get('date', '')}\n\n"

    if not data.get("price"):
        result += "\n⚠️ _لم يتم العثور على بيانات. تأكد من رمز السهم أو أن السوق مفتوح._"

    await loading_msg.delete()
    await update.message.reply_text(
        result,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=after_search()
    )
    return ConversationHandler.END

# ─── أبرز الأسهم ──────────────────────────────────────────────────────────────

async def show_top_stocks(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "⏳ *جاري تحميل أبرز الأسهم...*",
        parse_mode=ParseMode.MARKDOWN
    )
    stocks = await get_top_stocks()

    if not stocks:
        text = "⚠️ لا تتوفر بيانات الآن. حاول لاحقاً."
    else:
        text = f"🏆 *أبرز أسهم اليوم*\n📅 {ar_date()}\n{'─' * 30}\n\n"
        for i, s in enumerate(stocks[:12], 1):
            change = s.get("change", "—")
            arrow = "📈" if "+" in str(change) else ("📉" if "-" in str(change) else "➡️")
            text += (
                f"{i}. {arrow} `{s['symbol']}` — {s['company'][:14]}\n"
                f"   💰 {s['price']} | {change}\n"
            )

    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())

# ─── التقارير ─────────────────────────────────────────────────────────────────

async def show_reports_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📊 *اختر نوع التقرير:*", parse_mode=ParseMode.MARKDOWN,
        reply_markup=reports_menu()
    )

async def show_daily_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    report = await build_daily_report()
    await query.edit_message_text(report, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu())

async def show_weekly_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    report = await build_weekly_report()
    await query.edit_message_text(report, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())

async def show_monthly_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    report = await build_monthly_report()
    await query.edit_message_text(report, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())

# ─── الاشتراك ─────────────────────────────────────────────────────────────────

async def show_subscription(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(query.from_user.id)
    sub = user.get("sub_type", "trial") if user else "trial"
    sub_end = user.get("sub_end", "") if user else ""

    status_text = {
        "trial": f"🆓 تجربة مجانية تنتهي في: {sub_end}",
        "monthly": f"✅ اشتراك شهري نشط — ينتهي: {sub_end}",
        "yearly": f"⭐ اشتراك سنوي نشط — ينتهي: {sub_end}",
    }.get(sub, "❓ غير معروف")

    text = (
        f"💎 *صفحة الاشتراك*\n{'─' * 30}\n\n"
        f"حالتك الحالية: {status_text}\n\n"
        f"🌟 *مميزات الاشتراك:*\n"
        f"• 📊 تقارير يومية وأسبوعية وشهرية\n"
        f"• 🔔 تنبيهات مخصصة لا محدودة\n"
        f"• 📅 الشهري: مراقبة 5 شركات\n"
        f"• 📆 السنوي: مراقبة 10 شركات\n\n"
        f"💰 *الأسعار:*\n"
        f"• شهري: {PRICES['monthly']:,} دينار عراقي\n"
        f"• سنوي: {PRICES['yearly']:,} دينار عراقي\n"
    )
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=subscription_menu())

async def start_payment(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sub_type = "monthly" if "monthly" in query.data else "yearly"
    amount = PRICES[sub_type]
    user_sub_type[query.from_user.id] = sub_type

    text = (
        f"💳 *طريقة الدفع — {'شهري' if sub_type == 'monthly' else 'سنوي'}*\n"
        f"{'─' * 30}\n\n"
        f"المبلغ: *{amount:,} دينار عراقي*\n\n"
        f"📲 *رقم كي كارد:*\n`{KICHE_NUMBER}`\n\n"
        f"*خطوات الدفع:*\n"
        f"1️⃣ حول المبلغ لرقم الكي كارد\n"
        f"2️⃣ خذ صورة الوصل\n"
        f"3️⃣ اضغط «أرسلت الوصل» وأرسل الصورة\n\n"
        f"⚠️ _لا تنسَ إرسال الوصل واسم المحول منه_"
    )
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=payment_confirm())
    # إرسال صورة QR
    try:
        await ctx.bot.send_photo(query.message.chat_id, QR_IMAGE, caption="📲 QR Code للدفع")
    except:
        pass

async def handle_receipt_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📸 *أرسل صورة وصل الدفع الآن:*\n\n_سيتم التحقق من الدفع خلال دقائق_",
        parse_mode=ParseMode.MARKDOWN
    )
    return WAITING_RECEIPT

async def receive_receipt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ أرسل صورة الوصل فقط.")
        return WAITING_RECEIPT

    ctx.user_data["receipt_file_id"] = update.message.photo[-1].file_id
    await update.message.reply_text(
        "✅ استلمنا الوصل!\n\n"
        "الآن أرسل *اسم الشخص الذي حول منه* (كما يظهر بالوصل):",
        parse_mode=ParseMode.MARKDOWN
    )
    return WAITING_SENDER_NAME

async def receive_sender_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    sender_name = update.message.text.strip()
    sub_type = user_sub_type.get(user_id, "monthly")
    amount = PRICES.get(sub_type, 5000)
    receipt_id = ctx.user_data.get("receipt_file_id", "")

    # حفظ الدفع
    pay_id = add_payment(user_id, amount, sub_type, receipt_id, sender_name)

    # رسالة تأكيد للمستخدم
    sub_label = "شهري" if sub_type == "monthly" else "سنوي"
    await update.message.reply_text(
        f"📨 *تم إرسال طلبك بنجاح!*\n\n"
        f"✅ المبلغ: *{amount:,} دينار*\n"
        f"📅 نوع الاشتراك: *{sub_label}*\n"
        f"👤 المحول من: *{sender_name}*\n\n"
        f"⏳ سيتم تفعيل اشتراكك خلال دقائق بعد التحقق.\n\n"
        f"للاستفسار: {SUPPORT_USERNAME}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=back_button()
    )

    # إشعار الأدمن مع صورة الوصل
    try:
        user_info = update.effective_user
        caption = (
            f"💳 *طلب اشتراك جديد #{pay_id}*\n\n"
            f"👤 الاسم: {user_info.full_name}\n"
            f"🆔 ID: `{user_id}`\n"
            f"📅 النوع: {sub_label}\n"
            f"💰 المبلغ: {amount:,} دينار\n"
            f"🔄 المحول من: *{sender_name}*\n"
            f"⏰ {ar_date()}"
        )
        await ctx.bot.send_photo(
            ADMIN_ID,
            receipt_id,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=approve_payment_btn(pay_id, user_id, sub_type)
        )
    except Exception as e:
        print(f"[admin notify] {e}")

    return ConversationHandler.END

# ─── التنبيهات ────────────────────────────────────────────────────────────────

async def show_alerts(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    alerts = get_user_alerts(user_id)

    user = get_user(user_id)
    full_name = user.get("full_name", "المستخدم") if user else "المستخدم"
    first_name = full_name.split()[0] if full_name else "المستخدم"

    if not alerts:
        text = (
            f"🔔 *تنبيهاتي*\n{'─' * 30}\n\n"
            f"لا توجد تنبيهات مضافة بعد.\n\n"
            f"💡 *طريقة إضافة تنبيه:*\n"
            f"اضغط «إضافة تنبيه» ثم أرسل:\n"
            f"1️⃣ رمز السهم (مثال: BBOB)\n"
            f"2️⃣ النسبة المئوية (مثال: 5)\n"
            f"3️⃣ الاتجاه: صعود أو نزول\n\n"
            f"_مثال: ينبهني عند صعود BBOB بنسبة 5%_"
        )
    else:
        text = f"🔔 *تنبيهات {first_name}*\n{'─' * 30}\n\n"
        for a in alerts:
            direction_icon = "📈" if a["direction"] == "up" else "📉"
            direction_ar = "صعود" if a["direction"] == "up" else "نزول"
            text += f"{direction_icon} `{a['symbol']}` — {direction_ar} {a['target_pct']}%\n"
        text += "\n_اضغط على التنبيه لحذفه_"

    await query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN,
        reply_markup=alerts_menu(alerts)
    )

async def start_add_alert(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔔 *إضافة تنبيه جديد*\n\n"
        "الخطوة 1️⃣: أرسل *رمز السهم*\n"
        "_مثال: BBOB أو TZNI_",
        parse_mode=ParseMode.MARKDOWN
    )
    return WAITING_ALERT_SYMBOL

async def receive_alert_symbol(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.strip().upper()
    if not re.match(r'^[A-Z]{2,6}$', symbol):
        await update.message.reply_text("❌ رمز غير صحيح. أرسل مثل BBOB")
        return WAITING_ALERT_SYMBOL
    ctx.user_data["alert_symbol"] = symbol
    company = IRAQI_STOCKS.get(symbol, symbol)
    await update.message.reply_text(
        f"✅ السهم: `{symbol}` — {company}\n\n"
        f"الخطوة 2️⃣: أرسل *النسبة المئوية* للتنبيه\n"
        f"_مثال: 5 (تعني 5%)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return WAITING_ALERT_PCT

async def receive_alert_pct(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        pct = float(update.message.text.strip().replace("%", ""))
        if pct <= 0 or pct > 100:
            raise ValueError
    except:
        await update.message.reply_text("❌ أرسل رقماً صحيحاً مثل 5 أو 10")
        return WAITING_ALERT_PCT

    ctx.user_data["alert_pct"] = pct
    await update.message.reply_text(
        f"✅ النسبة: *{pct}%*\n\n"
        f"الخطوة 3️⃣: *اتجاه التنبيه؟*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=alert_direction_menu()
    )
    return WAITING_ALERT_DIR

async def receive_alert_direction(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    direction = "up" if "up" in query.data else "down"
    symbol = ctx.user_data.get("alert_symbol", "")
    pct = ctx.user_data.get("alert_pct", 0)

    add_alert(user_id, symbol, pct, direction)

    direction_ar = "📈 صعود" if direction == "up" else "📉 نزول"
    company = IRAQI_STOCKS.get(symbol, symbol)
    await query.edit_message_text(
        f"✅ *تم إضافة التنبيه!*\n\n"
        f"🏢 الشركة: {company} (`{symbol}`)\n"
        f"📊 النسبة: {pct}%\n"
        f"🎯 الاتجاه: {direction_ar}\n\n"
        f"سنُنبهك فور وصول السهم لهذا المستوى 🔔",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=back_button("my_alerts")
    )
    return ConversationHandler.END

async def delete_user_alert(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    alert_id = int(query.data.split("_")[-1])
    delete_alert(alert_id, query.from_user.id)
    await query.answer("🗑 تم حذف التنبيه", show_alert=True)
    # تحديث القائمة
    alerts = get_user_alerts(query.from_user.id)
    user = get_user(query.from_user.id)
    name = (user.get("full_name", "").split()[0] if user else "المستخدم") or "المستخدم"
    text = f"🔔 *تنبيهات {name}*\n{'─' * 30}\n\n"
    if alerts:
        for a in alerts:
            d_icon = "📈" if a["direction"] == "up" else "📉"
            d_ar = "صعود" if a["direction"] == "up" else "نزول"
            text += f"{d_icon} `{a['symbol']}` — {d_ar} {a['target_pct']}%\n"
    else:
        text += "_لا توجد تنبيهات_"
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=alerts_menu(alerts))

# ─── مراقبة الشركات ───────────────────────────────────────────────────────────

async def show_watchlist(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    items = get_user_watchlist(user_id)
    limit = get_monitoring_limit(user_id)

    user = get_user(user_id)
    name = (user.get("full_name", "").split()[0] if user else "المستخدم") or "المستخدم"

    if not items:
        text = (
            f"👁 *مراقبة شركة*\n{'─' * 30}\n\n"
            f"لا توجد شركات مراقَبة بعد.\n\n"
            f"📊 *حدود المراقبة:*\n"
            f"• مجاني: شركة واحدة\n"
            f"• شهري: 5 شركات\n"
            f"• سنوي: 10 شركات\n\n"
            f"حدك الحالي: *{limit} شركة*"
        )
    else:
        text = (
            f"👁 *الشركات المراقَبة بواسطة {name}*\n"
            f"{'─' * 30}\n\n"
        )
        for it in items:
            text += f"• `{it['symbol']}` — {it['company']}\n"
        text += f"\n_الحد: {len(items)}/{limit} شركة_\n_اضغط على الشركة لحذفها_"

    await query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN,
        reply_markup=watchlist_menu(items, limit)
    )

async def start_add_watch(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "👁 *إضافة شركة للمراقبة*\n\n"
        "أرسل *رمز الشركة* (مثال: TZNI لآسياسيل)\n\n"
        "_سيصلك تحديث يومي بآخر أخبارها وأسعارها_",
        parse_mode=ParseMode.MARKDOWN
    )
    return WAITING_WATCH_SYMBOL

async def receive_watch_symbol(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.strip().upper()
    user_id = update.effective_user.id

    if not re.match(r'^[A-Z]{2,6}$', symbol):
        await update.message.reply_text("❌ رمز غير صحيح.")
        return WAITING_WATCH_SYMBOL

    company = IRAQI_STOCKS.get(symbol, symbol)
    success = add_watchlist(user_id, symbol, company)

    if not success:
        limit = get_monitoring_limit(user_id)
        await update.message.reply_text(
            f"⚠️ وصلت للحد الأقصى ({limit} شركة).\n\n"
            f"رقّي اشتراكك لمراقبة المزيد!",
            reply_markup=subscription_menu()
        )
    else:
        await update.message.reply_text(
            f"✅ *تم إضافة {company} (`{symbol}`) للمراقبة!*\n\n"
            f"ستصلك تحديثات يومية وتنبيهات فورية عند ذكرها بالأخبار.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_button("watch_company")
        )
    return ConversationHandler.END

async def remove_watch(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    symbol = query.data.replace("del_watch_", "")
    remove_watchlist(query.from_user.id, symbol)
    await query.answer(f"🗑 تم حذف {symbol}", show_alert=True)
    # إعادة عرض القائمة
    items = get_user_watchlist(query.from_user.id)
    limit = get_monitoring_limit(query.from_user.id)
    await query.edit_message_text(
        f"👁 *الشركات المراقَبة*\n{'─' * 30}\n" +
        ("\n".join(f"• `{i['symbol']}` — {i['company']}" for i in items) or "\n_لا توجد شركات_"),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=watchlist_menu(items, limit)
    )

# ─── أسهمي (عرض التنبيهات) ────────────────────────────────────────────────────

async def cmd_my_stocks(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """عند كتابة 'اسهمي' أو 'أسهمي'"""
    user_id = update.effective_user.id
    alerts = get_user_alerts(user_id)
    user = get_user(user_id)
    name = (user.get("full_name", "").split()[0] if user else "المستخدم") or "المستخدم"

    if not alerts:
        text = f"📋 *الأسهم المفضلة لـ{name}*\n\n_لا توجد أسهم مضافة بعد._\n\nاستخدم زر 🔔 تنبيهاتي لإضافة أسهم."
    else:
        text = f"📋 *الأسهم المفضلة لـ{name}*\n{'─' * 30}\n\n"
        for a in alerts:
            d = "📈" if a["direction"] == "up" else "📉"
            company = IRAQI_STOCKS.get(a["symbol"], a["symbol"])
            text += f"{d} `{a['symbol']}` — {company}\n   عند: {a['direction'] == 'up' and 'صعود' or 'نزول'} {a['target_pct']}%\n\n"

    await update.message.reply_text(
        text, parse_mode=ParseMode.MARKDOWN,
        reply_markup=alerts_menu(alerts)
    )

# ─── لوحة الإدارة ─────────────────────────────────────────────────────────────

async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    users = get_all_users()
    active = sum(1 for u in users if u.get("sub_type") in ("monthly", "yearly"))
    await update.message.reply_text(
        f"🔐 *لوحة الإدارة — رقيب*\n{'─' * 30}\n\n"
        f"👥 إجمالي المستخدمين: *{len(users)}*\n"
        f"✅ مشتركون نشطون: *{active}*\n"
        f"📅 {ar_date()}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=admin_menu()
    )

async def admin_list_users(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return
    users = get_all_users()
    text = f"👥 *قائمة المستخدمين ({len(users)})*\n{'─' * 30}\n\n"
    for u in users[:20]:
        sub_icon = {"trial": "🆓", "monthly": "📅", "yearly": "⭐"}.get(u["sub_type"], "❓")
        text += (
            f"{sub_icon} *{u['full_name'] or 'بدون اسم'}*\n"
            f"  🆔 `{u['user_id']}` | @{u['username'] or 'لا يوجد'}\n"
            f"  📅 {u['sub_end'] or '—'}\n\n"
        )
    if len(users) > 20:
        text += f"_و {len(users) - 20} مستخدم آخر..._"
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=admin_menu())

async def admin_list_payments(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return
    payments = get_all_payments()
    pending = [p for p in payments if p["status"] == "pending"]
    if not pending:
        await query.edit_message_text(
            "✅ لا توجد طلبات معلقة.",
            reply_markup=admin_menu()
        )
        return
    text = f"💳 *الطلبات المعلقة ({len(pending)})*\n\n"
    for p in pending[:5]:
        text += (
            f"#{p['id']} | 👤 `{p['user_id']}`\n"
            f"💰 {p['amount']:,} | 📅 {p['sub_type']}\n"
            f"🔄 من: {p['sender_name']}\n"
            f"⏰ {p['created_at']}\n\n"
        )
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=admin_menu())

async def admin_start_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return
    await query.edit_message_text(
        "📢 *إرسال رسالة لجميع المستخدمين*\n\nأرسل الرسالة الآن:",
        parse_mode=ParseMode.MARKDOWN
    )
    return WAITING_BROADCAST

async def admin_do_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    text = update.message.text
    user_ids = get_all_user_ids()
    sent = 0
    failed = 0
    for uid in user_ids:
        try:
            await ctx.bot.send_message(uid, f"📢 *رسالة من رقيب:*\n\n{text}", parse_mode=ParseMode.MARKDOWN)
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
    await update.message.reply_text(
        f"✅ تم الإرسال!\n📤 وصل: {sent} | ❌ فشل: {failed}",
        reply_markup=admin_menu()
    )
    return ConversationHandler.END

async def approve_or_reject(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return

    parts = query.data.split("_")
    action = parts[0]  # approve or reject
    pay_id = int(parts[1])
    user_id = int(parts[2])
    sub_type = parts[3] if len(parts) > 3 else "monthly"

    if action == "approve":
        days = 30 if sub_type == "monthly" else 365
        set_subscription(user_id, sub_type, days)
        approve_payment(pay_id)
        sub_label = "شهري" if sub_type == "monthly" else "سنوي"
        # إشعار المستخدم
        try:
            await ctx.bot.send_message(
                user_id,
                f"🎉 *تم تفعيل اشتراكك!*\n\n"
                f"✅ اشتراك {sub_label} نشط الآن\n"
                f"شكراً لثقتك برقيب 🌟\n\n"
                f"يمكنك الآن الاستمتاع بجميع المميزات.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_menu()
            )
        except:
            pass
        await query.edit_message_caption(
            caption=query.message.caption + f"\n\n✅ *تم القبول من قبل الأدمن*",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        try:
            await ctx.bot.send_message(
                user_id,
                f"❌ *تعذر تأكيد دفعك.*\n\n"
                f"يرجى التواصل مع الدعم: {SUPPORT_USERNAME}",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n❌ *تم الرفض*",
            parse_mode=ParseMode.MARKDOWN
        )
