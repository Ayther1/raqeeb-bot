from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID, CHANNEL_ID, IMAGES
from database import *
from messages import *
from keyboards import *
from scraper import get_market_summary, get_top_stocks, get_stock_info, get_isx_news, get_company_news

# ── تحقق من اشتراك القناة ──
async def is_joined(bot, user_id):
    try:
        m = await bot.get_chat_member(CHANNEL_ID, user_id)
        return m.status in ["member", "administrator", "creator"]
    except:
        return False

# ── إرسال القائمة الرئيسية ──
async def send_main(bot, chat_id):
    data = get_market_summary()
    await bot.send_photo(
        chat_id=chat_id,
        photo=IMAGES["daily"],
        caption=msg_daily(data),
        reply_markup=kb_main()
    )

# ───────────────────────────────────────────
# /start
# ───────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if update.effective_chat.type != "private":
        await update.message.reply_text("❌ هذا البوت للاستخدام الشخصي فقط.")
        return
    await register_user(user.id, user.username, user.full_name)
    # مسح أي حالة سابقة
    ctx.user_data.clear()
    await update.message.reply_photo(
        photo=IMAGES["welcome"],
        caption=msg_welcome(),
        reply_markup=kb_welcome()
    )

# ───────────────────────────────────────────
# معالج الأزرار
# ───────────────────────────────────────────
async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user = q.from_user
    data = q.data

    async def reply(image_key, text, kb):
        await q.message.reply_photo(photo=IMAGES[image_key], caption=text, reply_markup=kb)

    # ── ابدأ الاستخدام ──
    if data == "start_use":
        if not await is_joined(ctx.bot, user.id):
            await q.message.reply_photo(
                photo=IMAGES["welcome"],
                caption=msg_join(),
                reply_markup=kb_join()
            )
            return
        if not await is_active(user.id):
            await q.message.reply_text(msg_expired())
            return
        await send_main(ctx.bot, q.message.chat_id)

    # ── تأكيد الاشتراك ──
    elif data == "check_join":
        if not await is_joined(ctx.bot, user.id):
            await q.answer("❌ لم تشترك بعد! اشترك بالقناة أولاً", show_alert=True)
            return
        if not await is_active(user.id):
            await q.message.reply_text(msg_expired())
            return
        await send_main(ctx.bot, q.message.chat_id)

    # ── رجوع للقائمة الرئيسية ──
    elif data == "back_main":
        ctx.user_data.clear()
        if not await is_active(user.id):
            await q.message.reply_text(msg_expired())
            return
        await send_main(ctx.bot, q.message.chat_id)

    # ── بحث عن سهم ──
    elif data == "search":
        ctx.user_data["state"] = "search"
        await reply("search", msg_search(), kb_back())

    # ── أبرز الأسهم ──
    elif data == "top_stocks":
        stocks = get_top_stocks()
        await reply("daily", msg_top_stocks(stocks), kb_back())

    # ── اشتراكي ──
    elif data == "my_sub":
        u = await get_user(user.id)
        await reply("payment", msg_sub(u), kb_sub())

    # ── اختيار خطة ──
    elif data in ["sub_monthly", "sub_yearly"]:
        plan = "monthly" if data == "sub_monthly" else "yearly"
        ctx.user_data["pending_plan"] = plan
        await reply("payment", msg_payment(plan), kb_payment_confirm(plan))

    # ── أرسل الإيصال ──
    elif data.startswith("receipt_"):
        plan = data.split("_")[1]
        ctx.user_data["pending_plan"] = plan
        ctx.user_data["state"] = "waiting_receipt"
        await q.message.reply_text(
            "📸 أرسل صورة الإيصال مع اسمك الذي حولت منه"
        )

    # ── تنبيهاتي ──
    elif data == "my_alerts":
        alerts = await get_alerts(user.id)
        await reply("daily", msg_alerts(alerts, user.first_name), kb_alerts(alerts))

    # ── إضافة تنبيه ──
    elif data == "add_alert":
        ctx.user_data["state"] = "add_alert"
        await reply("daily", msg_add_alert(), kb_back())

    # ── حذف تنبيه ──
    elif data.startswith("del_alert_"):
        alert_id = int(data.split("_")[2])
        await delete_alert(alert_id, user.id)
        alerts = await get_alerts(user.id)
        await reply("daily", msg_alerts(alerts, user.first_name), kb_alerts(alerts))

    # ── قائمة المراقبة ──
    elif data == "watchlist":
        watches = await get_watchlist(user.id)
        limit   = await get_watch_limit(user.id)
        await reply("daily", msg_watchlist(watches, user.first_name, limit),
                    kb_watchlist(watches, limit, len(watches)))

    # ── إضافة شركة ──
    elif data == "add_watch":
        ctx.user_data["state"] = "add_watch"
        await reply("daily", msg_add_watch(), kb_back())

    # ── حذف شركة ──
    elif data.startswith("del_watch_"):
        watch_id = int(data.split("_")[2])
        await remove_watch(watch_id, user.id)
        watches = await get_watchlist(user.id)
        limit   = await get_watch_limit(user.id)
        await reply("daily", msg_watchlist(watches, user.first_name, limit),
                    kb_watchlist(watches, limit, len(watches)))

    # ── أزرار الأدمن ──
    elif data.startswith("adm_") and user.id == ADMIN_ID:
        await _handle_admin(q, ctx, data)

# ───────────────────────────────────────────
# معالج النصوص
# ───────────────────────────────────────────
async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (update.message.text or "").strip()

    if update.effective_chat.type != "private":
        return

    state = ctx.user_data.get("state")

    # ── بحث عن سهم ──
    if state == "search":
        ctx.user_data.clear()
        symbol = text.upper()
        wait_msg = await update.message.reply_text(msg_searching())
        stock = get_stock_info(symbol)
        await wait_msg.delete()
        if stock and len(stock) > 3:
            await update.message.reply_photo(
                photo=IMAGES["search"],
                caption=msg_stock(stock),
                reply_markup=kb_after_search()
            )
        else:
            await update.message.reply_photo(
                photo=IMAGES["search"],
                caption=msg_not_found(symbol),
                reply_markup=kb_after_search()
            )
        return

    # ── إضافة تنبيه ──
    if state == "add_alert":
        ctx.user_data.clear()
        parts = text.split()
        if len(parts) >= 3:
            symbol    = parts[0].upper()
            try: pct  = float(parts[1])
            except:
                await update.message.reply_text("❌ النسبة غير صحيحة\nمثال: BBOB 5 صعود")
                return
            direction = "up" if "صعود" in parts[2] else "down"
            await add_alert(user.id, symbol, direction, pct)
            await update.message.reply_text(msg_alert_added(symbol, pct, direction))
            # أرجع للتنبيهات
            alerts = await get_alerts(user.id)
            await update.message.reply_photo(
                photo=IMAGES["daily"],
                caption=msg_alerts(alerts, user.first_name),
                reply_markup=kb_alerts(alerts)
            )
        else:
            await update.message.reply_text(
                "❌ الصيغة غير صحيحة\nمثال: BBOB 5 صعود"
            )
        return

    # ── إضافة شركة للمراقبة ──
    if state == "add_watch":
        ctx.user_data.clear()
        company = text
        added = await add_watch(user.id, company)
        if added:
            await update.message.reply_text(msg_watch_added(company))
        else:
            limit = await get_watch_limit(user.id)
            await update.message.reply_text(msg_watch_limit(limit))
        watches = await get_watchlist(user.id)
        limit   = await get_watch_limit(user.id)
        await update.message.reply_photo(
            photo=IMAGES["daily"],
            caption=msg_watchlist(watches, user.first_name, limit),
            reply_markup=kb_watchlist(watches, limit, len(watches))
        )
        return

    # ── أوامر الأدمن ──
    if user.id == ADMIN_ID:
        if text == "/users":
            users = await get_all_users()
            lines = [f"👥 المستخدمون ({len(users)})\n"]
            for u in users[:20]:
                end = u.get("sub_end") or u.get("trial_end") or "—"
                lines.append(f"• {u['full_name']} | {u['user_id']} | {end[:10]}")
            await update.message.reply_text("\n".join(lines))
            return

    # ── اشتراكاتي (اختصار) ──
    if "اشتراكي" in text or text == "/اشتراك":
        u = await get_user(user.id)
        await update.message.reply_photo(
            photo=IMAGES["payment"],
            caption=msg_sub(u),
            reply_markup=kb_sub()
        )
        return

    # ── عرض التنبيهات (اختصار) ──
    if "اسهمي" in text or "تنبيهاتي" in text:
        alerts = await get_alerts(user.id)
        await update.message.reply_photo(
            photo=IMAGES["daily"],
            caption=msg_alerts(alerts, user.first_name),
            reply_markup=kb_alerts(alerts)
        )
        return

    # ── أي رسالة أخرى ──
    if await is_active(user.id):
        await send_main(ctx.bot, update.effective_chat.id)
    else:
        await update.message.reply_text(msg_expired())

# ───────────────────────────────────────────
# معالج الصور (إيصال الدفع)
# ───────────────────────────────────────────
async def on_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if update.effective_chat.type != "private":
        return

    plan = ctx.user_data.get("pending_plan", "monthly")
    ctx.user_data.clear()

    photo_id = update.message.photo[-1].file_id
    caption  = update.message.caption or ""

    await ctx.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_id,
        caption=msg_admin_request(user, plan) + (f"\n💬 ملاحظة: {caption}" if caption else ""),
        reply_markup=kb_admin(user.id)
    )
    await update.message.reply_text(msg_receipt_confirm(plan), reply_markup=kb_support())

# ───────────────────────────────────────────
# أزرار الأدمن
# ───────────────────────────────────────────
async def _handle_admin(q, ctx, data):
    parts = data.split("_")

    if parts[1] in ["monthly", "yearly"]:
        plan      = parts[1]
        target_id = int(parts[2])
        await q.message.reply_text(
            f"⚠️ تأكيد التفعيل\n\n"
            f"الخطة: {'شهري' if plan=='monthly' else 'سنوي'}\n"
            f"المستخدم: {target_id}",
            reply_markup=kb_admin_confirm(plan, target_id)
        )

    elif parts[1] == "confirm":
        plan      = parts[2]
        target_id = int(parts[3])
        sub_end   = await activate_sub(target_id, plan)
        end_str   = sub_end.strftime("%d/%m/%Y")
        await q.message.reply_text(
            msg_activated(plan, end_str),
            reply_markup=kb_admin_notify(plan, target_id, end_str)
        )

    elif parts[1] == "back":
        target_id = int(parts[2])
        await q.message.reply_text("اختر الخطة:", reply_markup=kb_admin(target_id))

    elif parts[1] == "reject":
        target_id = int(parts[2])
        await ctx.bot.send_message(target_id,
            "❌ عذراً، لم يتم قبول طلبك\n"
            f"للاستفسار تواصل مع {SUPPORT_BOT}"
        )
        await q.message.reply_text("❌ تم رفض الطلب")

    elif parts[1] == "notify":
        plan      = parts[2]
        target_id = int(parts[3])
        end_str   = parts[4]
        await ctx.bot.send_message(target_id, msg_user_activated(plan, end_str))
        await q.message.reply_text("📨 تم إرسال الإشعار ✅")
