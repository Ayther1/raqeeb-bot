# main.py — نقطة تشغيل البوت

import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters
)
from config import BOT_TOKEN
from database import init_db
from handlers import start_handler, callback_handler, message_handler, photo_handler
from scheduler import setup_scheduler

# إعداد السجل
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("raqeeb.log"),
        logging.StreamHandler()
    ]
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

async def post_init(application):
    """يعمل بعد بدء البوت — يشغل الجدول الزمني"""
    scheduler = setup_scheduler(application.bot)
    scheduler.start()
    logger.info("✅ الجدول الزمني شغّال")

async def main():
    # تهيئة قاعدة البيانات
    await init_db()
    logger.info("✅ قاعدة البيانات جاهزة")

    # بناء التطبيق
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ── تسجيل الهاندلرز ──
    app.add_handler(CommandHandler("start",      start_handler))
    app.add_handler(CommandHandler("اشتراك",     lambda u, c: c.bot.send_message(
        u.effective_chat.id, "اضغط على زر 💳 اشتراكي من القائمة الرئيسية"
    )))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logger.info("🚀 البوت يعمل الآن...")
    print("=" * 40)
    print("🤖 رقيب | RaqeebIQBot")
    print("✅ البوت شغّال")
    print("=" * 40)

    await app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    asyncio.run(main())
