import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN    = os.environ.get("BOT_TOKEN", "8992422291:AAGqSKqVlAj2NZsKGLPETvhgkFzwoibebII")
ADMIN_ID     = 8601067589
CHANNEL_ID   = "@RaqeebIQ"
SUPPORT_BOT  = "@RaqeebAskBot"
KICHE_NUMBER = "7112676056"

IMAGES = {
    "welcome":  "https://files.catbox.moe/0vz26u.jpeg",
    "news":     "https://files.catbox.moe/oh3q4f.jpeg",
    "daily":    "https://files.catbox.moe/twu7tg.jpeg",
    "weekly":   "https://files.catbox.moe/270cr1.jpeg",
    "monthly":  "https://files.catbox.moe/j0l4bd.jpeg",
    "open":     "https://files.catbox.moe/blancp.jpeg",
    "search":   "https://files.catbox.moe/vsqp2z.jpeg",
    "payment":  "https://files.catbox.moe/uuu6qm.jpeg",
}

PRICES = {
    "monthly": 5000,
    "yearly":  50000,
}

TRIAL_DAYS = 7

# حدود مراقبة الشركات حسب نوع الاشتراك
WATCH_LIMITS = {
    "trial":   1,
    "monthly": 5,
    "yearly":  10,
}
