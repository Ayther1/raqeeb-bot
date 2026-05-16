# handlers.py — معالجات البوت

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, BotCommand
from telegram.ext import ContextTypes
from config import ADMIN_ID, CHANNEL_ID, IMAGES
from database import *
from messages import *
from scraper import get_market_summary, get_top_stocks, get_stock_info, IRAQI_STOCKS
import asyncio

# ─── تحقق من الاشتراك بالقناة ───
async def check_channel(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ─── /start ───
async def start_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if chat.type != "private":
        await update.message.reply_text("❌ هذا البوت للاستخدام الشخصي فقط.")
        return
    await register_user(user.id, user.username, user.full_name)
    # تعيين أمر /start مرئي دائماً
    await ctx.bot.set_my_commands([
        BotCommand("start", "ابدأ استخدام البوت")
    ])
    text, kb = welcome_msg()
    await update.message.reply_photo(photo=IMAGES["welcome"], caption=text, reply_markup=kb)

# ─── معالج الأزرار ───
async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # رد فوري لتجنب التأخير
    user = query.from_user
    data = query.data

    # ── ابدأ الاستخدام ──
    if data == "start_use":
        joined = await check_channel(ctx.bot, user.id)
        if not joined:
            text, kb = join_channel_msg()
            await query.edit_message_caption(caption=text, reply_markup=kb)
            return
        active = await is_user_active(user.id)
        if not active:
            await query.edit_message_caption(caption=expiry_msg())
            return
        market = get_market_summary()
        text, kb = main_menu_msg(market)
        await query.edit_message_media(
            media=InputMediaPhoto(media=IMAGES["daily"], caption=text),
            reply_markup=kb
        )

    # ── تأكيد الاشتراك بالقناة ──
    elif data == "verify_join":
        joined = await check_channel(ctx.bot, user.id)
        if not joined:
            await query.answer("❌ لم تشترك بعد في القناة!", show_alert=True)
            return
        active = await is_user_active(user.id)
        if not active:
            await query.edit_message_caption(caption=expiry_msg())
            return
        market = get_market_summary()
        text, kb = main_menu_msg(market)
        await query.edit_message_media(
            media=InputMediaPhoto(media=IMAGES["daily"], caption=text),
            reply_markup=kb
        )

    # ── رجوع للقائمة الرئيسية ──
    elif data == "back_main":
        active = await is_user_active(user.id)
        if not active:
            await query.edit_message_caption(caption=expiry_msg())
            return
        market = get_market_summary()
        text, kb = main_menu_msg(market)
        await query.edit_message_media(
            media=InputMediaPhoto(media=IMAGES["daily"], caption=text),
            reply_markup=kb
        )

    # ── أبرز الأسهم ──
    elif data == "top_stocks":
        stocks = get_top_stocks()
        text, kb = top_stocks_msg(stocks)
        await query.edit_message_media(
            media=InputMediaPhoto(media=IMAGES["daily"], caption=text),
            reply_markup=kb
        )

    # ── بحث عن سهم ──
    elif data == "search_stock":
        text, kb = search_stock_msg()
        await query.edit_message_media(
            media=InputMediaPhoto(media=IMAGES["search"], caption=text),
            reply_markup=kb
        )
        ctx.user_data["waiting_search"] = True

    # ── إعادة البحث ──
    elif data == "search_again":
        text, kb = search_stock_msg()
        await query.edit_message_caption(caption=text, reply_markup=kb)
        ctx.user_data["waiting_search"] = True

    # ── تنبيهاتي ──
    elif data == "my_alerts":
        alerts = await get_user_alerts(user.id)
        text, kb = alerts_msg(alerts, user.full_name)
        await query.edit_message_caption(caption=text, reply_markup=kb)

    # ── إضافة تنبيه ──
    elif data == "add_alert":
        text, kb = add_alert_step1_msg()
        await query.edit_message_caption(caption=text, reply_markup=kb)
        ctx.user_data["waiting_alert_symbol"] = True

    # ── اختيار نوع التنبيه ──
    elif data.startswith("alert_type_"):
        parts = data.split("_")
        symbol = parts[2]
        alert_type = parts[3]  # up أو down
        ctx.user_data["alert_symbol"] = symbol
        ctx.user_data["alert_type"] = alert_type
        text, kb = add_alert_step3_msg(symbol, alert_type)
        await query.edit_message_caption(caption=text, reply_markup=kb)
        ctx.user_data["waiting_alert_pct"] = True

    # ── حذف تنبيه ──
    elif data.startswith("del_alert_"):
        alert_id = int(data.replace("del_alert_", ""))
        await delete_alert(alert_id)
        await query.answer("✅ تم حذف التنبيه")
        alerts = await get_user_alerts(user.id)
        text, kb = alerts_msg(alerts, user.full_name)
        await query.edit_message_caption(caption=text, reply_markup=kb)

    # ── اشتراكي ──
    elif data == "my_sub":
        u = await get_user(user.id)
        text, kb = subscription_msg(u)
        await query.edit_message_caption(caption=text, reply_markup=kb)

    # ── اختيار خطة ──
    elif data in ["sub_monthly", "sub_yearly"]:
        plan = "monthly" if data == "sub_monthly" else "yearly"
        ctx.user_data["pending_plan"] = plan
        text, kb = payment_msg(plan)
        await query.edit_message_media(
            media=InputMediaPhoto(media=IMAGES["payment"], caption=text),
            reply_markup=kb
        )

    # ── أزرار الأدمن ──
    elif data.startswith("admin_"):
        if user.id != ADMIN_ID:
            return
        parts = data.split("_")
        action = parts[1]
        target_id = int(parts[2])

        if action in ["monthly", "yearly"]:
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ تأكيد", callback_data=f"confirm_{action}_{target_id}"),
                InlineKeyboardButton("🔙 تراجع", callback_data=f"cancel_{target_id}"),
            ]])
            await query.edit_message_reply_markup(reply_markup=kb)

        elif action == "reject":
            await ctx.bot.send_message(target_id,
                "❌ عذراً، لم يتم قبول طلبك\nيرجى التواصل مع الدعم أو إعادة المحاولة.")
            await query.edit_message_text("❌ تم رفض الطلب")

    elif data.startswith("confirm_"):
        if user.id != ADMIN_ID:
            return
        parts = data.split("_")
        plan = parts[1]
        target_id = int(parts[2])
        sub_end = await activate_subscription(target_id, plan)
        end_str = sub_end.strftime("%d/%m/%Y")
        plan_ar = "شهري" if plan == "monthly" else "سنوي"
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("📨 إرسال إشعار للمستخدم", callback_data=f"notify_{target_id}_{plan}_{end_str}")
        ]])
        await query.edit_message_text(
            f"✅ تم التفعيل بنجاح\n\n👤 ID: {target_id}\n📅 {plan_ar} | حتى {end_str}",
            reply_markup=kb
        )

    elif data.startswith("cancel_"):
        target_id = int(data.split("_")[1])
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ تفعيل شهري", callback_data=f"admin_monthly_{target_id}"),
                InlineKeyboardButton("✅ تفعيل سنوي", callback_data=f"admin_yearly_{target_id}"),
            ],
            [InlineKeyboardButton("❌ رفض", callback_data=f"admin_reject_{target_id}")]
        ])
        await query.edit_message_reply_markup(reply_markup=kb)

    elif data.startswith("notify_"):
        if user.id != ADMIN_ID:
            return
        parts = data.split("_")
        target_id = int(parts[1])
        plan = parts[2]
        end_str = parts[3]
        plan_ar = "شهري" if plan == "monthly" else "سنوي"
        await ctx.bot.send_message(
            target_id,
            f"✅ رقيب | تم تفعيل اشتراكك!\n\n"
            f"مرحباً بك 🎉\n"
            f"الخطة: {plan_ar}\n"
            f"ساري حتى: {end_str}\n\n"
            f"استمتع بمتابعة سوق الأسهم العراقية 📊"
            + footer()
        )
        await query.edit_message_text(query.message.text + "\n\n📨 تم إرسال الإشعار ✅")


# ─── معالج الرسائل النصية ───
async def message_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or ""

    if update.effective_chat.type != "private":
        return

    active = await is_user_active(user.id)

    # ── انتظار رمز السهم للتنبيه (الخطوة 1) ──
    if ctx.user_data.get("waiting_alert_symbol") and active:
        ctx.user_data["waiting_alert_symbol"] = False
        symbol = text.upper().strip()
        if symbol not in IRAQI_STOCKS:
            await update.message.reply_text(
                f"❌ السهم {symbol} غير موجود\n\nتأكد من الرمز وحاول مرة أخرى"
            )
            return
        ctx.user_data["alert_symbol"] = symbol
        text_msg, kb = add_alert_step2_msg(symbol)
        await update.message.reply_text(text_msg, reply_markup=kb)
        return

    # ── انتظار نسبة التنبيه (الخطوة 3) ──
    if ctx.user_data.get("waiting_alert_pct") and active:
        ctx.user_data["waiting_alert_pct"] = False
        symbol = ctx.user_data.get("alert_symbol")
        alert_type = ctx.user_data.get("alert_type")
        try:
            value = abs(float(text.strip().replace("%", "")))
            await add_alert(user.id, symbol, alert_type, value)
            direction = "📈 ارتفاع" if alert_type == "up" else "📉 انخفاض"
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔔 تنبيهاتي", callback_data="my_alerts"),
                InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_main"),
            ]])
            await update.message.reply_text(
                f"✅ تم إضافة التنبيه بنجاح!\n\n"
                f"🏢 السهم: {symbol}\n"
                f"{direction} بنسبة {value}%\n\n"
                f"سيصلك إشعار فور تحقق الشرط 🔔",
                reply_markup=kb
            )
        except:
            await update.message.reply_text("❌ أدخل رقماً صحيحاً\nمثال: 5")
        return

    # ── البحث عن سهم ──
    if ctx.user_data.get("waiting_search") and active:
        ctx.user_data["waiting_search"] = False
        symbol = text.upper().strip()
        searching = await update.message.reply_text(
            f"🔍 جاري البحث عن {symbol}...\n⏳ قد يستغرق بضع ثوانٍ"
        )
        stock = get_stock_info(symbol)
        await searching.delete()
        if stock:
            msg, kb = stock_result_msg(stock)
            await update.message.reply_photo(photo=IMAGES["search"], caption=msg, reply_markup=kb)
        else:
            msg, kb = stock_not_found_msg(symbol)
            await update.message.reply_photo(photo=IMAGES["search"], caption=msg, reply_markup=kb)
        return

    # ── أوامر الأدمن ──
    if user.id == ADMIN_ID:
        if text == "/users":
            users = await get_all_users_info()
            lines = [f"👥 المستخدمون ({len(users)})\n"]
            for u in users[:20]:
                end = u.get("sub_end") or u.get("trial_end") or "—"
                lines.append(f"• {u['full_name']} | {u['user_id']} | {str(end)[:10]}")
            await update.message.reply_text("\n".join(lines))
            return

    # ── لو مو مفعل ──
    if not active:
        await update.message.reply_text(expiry_msg())


# ─── معالج الصور (إيصال الدفع) ───
async def photo_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if update.effective_chat.type != "private":
        return
    plan = ctx.user_data.get("pending_plan", "monthly")
    plan_ar = "شهري" if plan == "monthly" else "سنوي"
    photo_id = update.message.photo[-1].file_id
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تفعيل شهري", callback_data=f"admin_monthly_{user.id}"),
            InlineKeyboardButton("✅ تفعيل سنوي", callback_data=f"admin_yearly_{user.id}"),
        ],
        [InlineKeyboardButton("❌ رفض", callback_data=f"admin_reject_{user.id}")]
    ])
    await ctx.bot.send_photo(
        ADMIN_ID,
        photo=photo_id,
        caption=(
            f"📩 طلب اشتراك جديد\n\n"
            f"👤 الاسم: {user.full_name}\n"
            f"🆔 ID: {user.id}\n"
            f"📅 الخطة المختارة: {plan_ar}\n"
            f"🖼️ الإيصال أعلاه"
        ),
        reply_markup=kb
    )
    await update.message.reply_text(
        "✅ تم استلام الإيصال\nسيتم مراجعته وتفعيل اشتراكك قريباً 🙏"
    )