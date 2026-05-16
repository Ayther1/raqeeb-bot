# config.py — إعدادات البوت

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8992422291:AAGqSKqVlAj2NZsKGLPETvhgkFzwoibebII")
ADMIN_ID = 8601067589
CHANNEL_ID = "@RaqeebIQ"

# رقم كي كارد للدفع
KICHE_NUMBER = "7112676056"

# روابط الصور
IMAGES = {
    "payment":  "https://files.catbox.moe/uuu6qm.jpeg",
}

# أسعار الاشتراك
PRICES = {
    "monthly": 5000,
    "yearly":  50000,
}

# مدة التجربة المجانية (أيام)
TRIAL_DAYS = 7

# ISX
ISX_URL = "http://www.isx-iq.net/isxportal/portal"
