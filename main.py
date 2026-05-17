import telebot
from config import BOT_TOKEN
import handlers  # لتفعيل كل الأوامر والمعالجات

bot = telebot.TeleBot(BOT_TOKEN)

if __name__ == "__main__":
    print("رقيب جاهز ويعمل الآن...")
    bot.infinity_polling()
