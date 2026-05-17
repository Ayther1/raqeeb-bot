import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8992422291:AAGqSKqVlAj2NZsKGLPETvhgkFzwoibebII")
ADMIN_ID = 8601067589
CHANNEL_ID = "@RaqeebIQ"
SUPPORT_USERNAME = "@RaqeebAskBot"

# رقم كي كارد للدفع
KICHE_NUMBER = "7112676056"

# رابط صورة QR
QR_IMAGE = "https://files.catbox.moe/uuu6qm.jpeg"

# أسعار الاشتراك
PRICES = {
    "monthly": 5000,
    "yearly": 50000,
}

# مدة التجربة المجانية (أيام)
TRIAL_DAYS = 7

# حدود المراقبة
MONITORING_LIMITS = {
    "free": 1,
    "monthly": 5,
    "yearly": 10,
}

# ساعات السوق (بتوقيت بغداد UTC+3)
MARKET_OPEN_HOUR = 10   # 10:00 صباحاً
MARKET_CLOSE_HOUR = 13  # 1:00 مساءً
MARKET_DAYS = [0, 1, 2, 3, 6]  # الأحد - الخميس (0=Monday في Python, لكن نعدلها)
# الأيام: Sunday=6, Monday=0, Tuesday=1, Wednesday=2, Thursday=3

# كلمات البحث للفلترة
KEYWORDS = [
    "بورصة", "سهم", "اسهم", "تداول", "شركة", "ارباح",
    "توزيع", "استثمار", "اكتتاب", "افصاح", "ISX", "سوق",
    "أوراق مالية", "مصرف", "بنك", "عائد", "مساهمين",
    "أسهم", "البورصة", "العراقي", "مالية"
]

# المصادر
SOURCES = {
    "isx": "https://www.isx-iq.net",
    "isc": "https://www.isc.gov.iq",
    "rs": "https://www.rs.iq",
    "alsumaria": "https://www.alsumaria.tv",
    "shafaq": "https://shafaq.com",
    "alsabaah": "https://alsabaah.iq",
}
