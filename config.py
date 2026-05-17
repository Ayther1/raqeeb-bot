import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN    = os.environ.get("BOT_TOKEN", "8992422291:AAGqSKqVlAj2NZsKGLPETvhgkFzwoibebII")
ADMIN_ID     = 8601067589
CHANNEL_ID   = "@RaqeebIQ"
SUPPORT_BOT  = "@RaqeebAskBot"
KICHE_NUMBER = "7112676056"
QR_IMAGE     = "https://files.catbox.moe/uuu6qm.jpeg"

PRICES = {
    "monthly": 5000,
    "yearly":  50000,
}

TRIAL_DAYS = 7

WATCH_LIMITS = {
    "trial":   1,
    "monthly": 5,
    "yearly":  10,
}

ISX_URL = "http://www.isx-iq.net/isxportal/portal"