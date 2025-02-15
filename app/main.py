import asyncio
import feedparser
import schedule
import requests
import os
from telegram import Bot, Update
from telegram.ext import CommandHandler, Application

# 🔹 Thông tin bot
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 🔹 URL RSS của Dân Trí (tin tức chung)
RSS_URL = "https://dantri.com.vn/rss/home.rss"

# 🔹 URL RSS về Đất Đai (Bất động sản)
LAND_RSS_URL = "https://dantri.com.vn/rss/bat-dong-san.rss"

# 🔹 API lấy giá vàng từ DOJI
GOLD_API_URL = "https://www.doji.vn/api/data"

# 🔹 Khởi tạo bot
bot = Bot(token=TOKEN)

# 🔹 Hàm lấy tin tức từ Dân Trí
def get_hot_news():
    feed = feedparser.parse(RSS_URL)
    top_news = feed.entries[:5]
    news_text = "\n\n".join([f"📌 {entry.title}\n🔗 {entry.link}" for entry in top_news])
    return news_text if news_text else "Không có tin tức mới."

# 🔹 Hàm lấy tin tức đất đai
def get_land_news():
    feed = feedparser.parse(LAND_RSS_URL)
    top_news = feed.entries[:5]
    news_text = "\n\n".join([f"🏡 {entry.title}\n🔗 {entry.link}" for entry in top_news])
    return news_text if news_text else "Không có tin tức đất đai mới."

# 🔹 Hàm lấy giá vàng từ API DOJI
def get_gold_price():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(GOLD_API_URL, headers=headers)

    if response.status_code != 200:
        return "❌ Không thể lấy giá vàng."

    try:
        data = response.json()
        sjc_price = data["GiaVang"]["data"]["SJC"]["Hồ Chí Minh"]
        buy_price = sjc_price["buy"]
        sell_price = sjc_price["sell"]
        return f"🏙 **SJC HCM**\n💰 Mua: {buy_price} | Bán: {sell_price}"
    except (KeyError, TypeError):
        return "❌ Không tìm thấy dữ liệu giá vàng."

# 🔹 Hàm gửi tin tức, giá vàng và đất đai vào Telegram
async def send_news_and_gold():
    news = get_hot_news()
    gold_price = get_gold_price()
    land_news = get_land_news()
    message = f"📰 **Tin tức hôm nay:**\n{news}\n\n{gold_price}\n\n{land_news}"
    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")

# 🔹 Lệnh /start - Hiển thị giá vàng và hướng dẫn sử dụng
async def start(update: Update, context):
    gold_price = get_gold_price()
    welcome_text = f"""🤖 **Chào mừng bạn đến với Bot Tin tức & Giá vàng!**  
📌 **Lệnh có sẵn:**  
🔹 /start - Xem giá vàng và hướng dẫn  
🔹 /refresh - Cập nhật tin tức & giá vàng ngay lập tức  
🕒 Bot tự động cập nhật tin tức vào 08:00 & 18:00, giá vàng vào 09:00.

{gold_price}
"""
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# 🔹 Lệnh /refresh - Cập nhật ngay
async def refresh(update: Update, context):
    await update.message.reply_text("🔄 Đang cập nhật tin tức, giá vàng và đất đai...")
    await send_news_and_gold()

# 🔹 Lên lịch gửi tin tự động
schedule.every().day.at("08:00").do(lambda: asyncio.run(send_news_and_gold()))
schedule.every().day.at("09:00").do(lambda: asyncio.run(send_news_and_gold()))  # Cập nhật giá vàng
schedule.every().day.at("18:00").do(lambda: asyncio.run(send_news_and_gold()))

# 🔹 Chạy bot Telegram
async def run_scheduler():
    while True:
        schedule.run_pending()
        await asyncio.sleep(60)

if __name__ == "__main__":
    print("🤖 Bot đang chạy...")

    # Khởi tạo bot với menu
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("refresh", refresh))

    # 🔹 FIX lỗi event loop
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Chạy bot và scheduler song song
    loop.create_task(run_scheduler())
    loop.create_task(app.run_polling())
    loop.run_forever()
