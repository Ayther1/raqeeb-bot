cat > /home/claude/raqeeb/handlers.py << 'ENDOFFILE'
# handlers.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_ID, CHANNEL_ID, IMAGES
from database import *
from messages import *
from scraper import get_market_summary, get_top_stocks, get_stock_info

async def check_channel(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ─── /start ───
async def start_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if update.effective_chat.type != "private":
        await update.message.reply_text("❌ هذا البوت للاستخدام الشخصي فقط.")
        return
    await register_user(user.id, user.username, user.full_name)
    text, kb = welcome_msg()
    await update.message.reply_photo(photo=IMAGES["welcome"], caption=text, reply_markup=kb)

# ─── معالج الأزرار ───
async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data

    # ── ابدأ الاستخدام ──
    if data == "start_use":
        joined = await check_channel(ctx.bot, user.id)
        if not joined:
            text, kb = join_channel_msg()
            await query.message.reply_photo(
                photo=IMAGES["welcome"],
                caption=text,
                reply_markup=kb
            )
            return
        active = await is_user_active(user.id)
        if not active:
            await query.message.reply_text(expiry_msg())
            return
        market = get_market_summary()
        text, kb = main_menu_msg(market)
        await query.message.reply_photo(
            photo=IMAGES["daily"],
            caption=text,
            reply_markup=kb
        )

    # ── تحقق من الاشتراك بالقناة ──
    elif data == "check_join":
        joined = await check_channel(ctx.bot, user.id)
        if not joined:
            await query.answer("❌ لم تشترك بعد! اشترك بالقناة أولاً", show_alert=True)
            return
        active = await is_user_active(user.id)
        if not active:
            await query.message.reply_text(expiry_msg())
            return
        market = get_market_summary()
        text, kb = main_menu_msg(market)
        await query.message.reply_photo(
            photo=IMAGES["daily"],
            caption=text,
            reply_markup=kb
        )

    # ── رجوع للقائمة الرئيسية ──
    elif data == "back_main":
        active = await is_user_active(user.id)
        if not active:
            await query.message.reply_text(expiry_msg())
            return
        market = get_market_summary()
        text, kb = main_menu_msg(market)
        await query.message.reply_photo(
            photo=IMAGES["daily"],
            caption=text,
            reply_markup=kb
        )

    # ── أبرز الأسهم ──
    elif data == "top_stocks":
        stocks = get_top_stocks()
        text, kb = top_stocks_msg(stocks)
        await query.message.reply_photo(
            photo=IMAGES["daily"],
            caption=text,
            reply_markup=kb
        )

    # ── بحث عن سهم ──
    elif data == "search_stock":
        ctx.user_data["waiting_search"] = True
        text, kb = search_stock_msg()
        await query.message.reply_photo(
            photo=IMAGES["search"],
            caption=text,
            reply_markup=kb
        )

    # ── تنبيهاتي ──
    elif data == "my_alerts":
        alerts = await get_user_alerts(user.id)
        text, kb = alerts_msg(alerts)
        await query.message.reply_photo(
            photo=IMAGES["daily"],
            caption=text,
            reply_markup=kb
        )

    # ── اشتراكي ──
    elif data == "my_sub":
        u = await get_user(user.id)
        text, kb = subscription_msg(u)
        await query.message.reply_photo(
            photo=IMAGES["payment"],
            caption=text,
            reply_markup=kb
        )

    # ── اختيار خطة ──
    elif data in ["sub_monthly", "sub_yearly"]:
        plan = "monthly" if data == "sub_monthly" else "yearly"
        ctx.user_data["pending_plan"] = plan
        text, kb = payment_msg(plan)
        await query.message.reply_photo(
            photo=IMAGES["payment"],
            caption=text,
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
            plan_ar = "شهري" if action == "monthly" else "سنوي"
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ تأكيد", callback_data=f"confirm_{action}_{target_id}"),
                InlineKeyboardButton("🔙 تراجع", callback_data=f"cancel_{target_id}"),
            ]])
            await query.message.reply_text(
                f"⚠️ تأكيد التفعيل\n\nالخطة: {plan_ar}\nالمستخدم: {target_id}",
                reply_markup=kb
            )
        elif action == "reject":
            await ctx.bot.send_message(target_id, "❌ عذراً، لم يتم قبول طلبك\nيرجى التواصل مع الدعم.")
            await query.message.reply_text("❌ تم رفض الطلب")

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
        await query.message.reply_text(
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
        await query.message.reply_text("اختر الخطة:", reply_markup=kb)

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
        await query.message.reply_text("📨 تم إرسال الإشعار ✅")

# ─── معالج الرسائل النصية ───
async def message_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or ""

    if update.effective_chat.type != "private":
        return

    # ── البحث عن سهم ──
    if ctx.user_data.get("waiting_search"):
        ctx.user_data["waiting_search"] = False
        symbol = text.upper().strip()
        # رسالة "جاري البحث"
        searching_msg = await update.message.reply_text("🔍 جاري البحث...")
        stock = get_stock_info(symbol)
        await searching_msg.delete()
        if stock and len(stock) > 2:
            msg, kb = stock_result_msg(stock)
        else:
            msg, kb = stock_not_found_msg(symbol)
        await update.message.reply_photo(
            photo=IMAGES["search"],
            caption=msg,
            reply_markup=kb
        )
        return

    # ── أمر التنبيه ──
    if text.startswith("/تنبيه"):
        parts = text.split()
        if len(parts) >= 3:
            symbol = parts[1].upper()
            try:
                value = float(parts[2])
                alert_type = "down" if len(parts) >= 4 and parts[3] == "انخفاض" else "up"
                await add_alert(user.id, symbol, alert_type, value)
                await update.message.reply_text(
                    f"✅ تم إضافة التنبيه\n{symbol} | {'📈 ارتفاع' if alert_type=='up' else '📉 انخفاض'} {value}%"
                )
            except:
                await update.message.reply_text("❌ صيغة خاطئة\nمثال: /تنبيه BBOB 5")
        return

    # ── حذف تنبيه ──
    if text.startswith("/حذف_"):
        try:
            alert_id = int(text.replace("/حذف_", ""))
            await delete_alert(alert_id)
            await update.message.reply_text("✅ تم حذف التنبيه")
        except:
            await update.message.reply_text("❌ خطأ في حذف التنبيه")
        return

    # ── أوامر الأدمن ──
    if user.id == ADMIN_ID and text == "/users":
        users = await get_all_users_info()
        lines = [f"👥 المستخدمون ({len(users)})\n"]
        for u in users[:20]:
            end = u.get("sub_end") or u.get("trial_end") or "—"
            lines.append(f"• {u['full_name']} | {u['user_id']} | {end[:10]}")
        await update.message.reply_text("\n".join(lines))
        return

    # ── أي رسالة ثانية = أرسل القائمة الرئيسية ──
    active = await is_user_active(user.id)
    if active:
        market = get_market_summary()
        t, kb = main_menu_msg(market)
        await update.message.reply_photo(photo=IMAGES["daily"], caption=t, reply_markup=kb)
    else:
        await update.message.reply_text(expiry_msg())

# ─── معالج الصور ───
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
        ADMIN_ID, photo=photo_id,
        caption=(
            f"📩 طلب اشتراك جديد\n\n"
            f"👤 الاسم: {user.full_name}\n"
            f"🆔 ID: {user.id}\n"
            f"📅 الخطة: {plan_ar}"
        ),
        reply_markup=kb
    )
    await update.message.reply_text("✅ تم استلام الإيصال\nسيتم مراجعته وتفعيل اشتراكك قريباً 🙏")
ENDOFFILE
echo "Done"
{
  "returncode" : 0,
  "stdout" : "Done\n",
  "stderr" : ""
}
