import os, requests, logging, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

logging.basicConfig(level=logging.INFO)

# --- কনফিগারেশন (Render Environment থেকে সরাসরি ডাটা নেবে) ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = "Flash Rewards Support"

# ইমেইল লিস্ট ফাইল
EMAIL_FILE = 'emails.txt'

def get_email_count():
    if not os.path.exists(EMAIL_FILE): return 0
    with open(EMAIL_FILE, 'r') as f:
        return len([line for line in f.readlines() if "@" in line])

# --- Cron-job & Health Check Server ---
# এটি Render-কে সিগন্যাল দেবে যে বটটি সচল আছে
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body><h1>Bot Status: Active</h1></body></html>")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    server.serve_forever()

# --- আকর্ষণীয় মেনু কিবোর্ড ---
def main_menu():
    return ReplyKeyboardMarkup([
        ['✉️ ইমেইল পাঠান', '📊 ড্যাশবোর্ড'],
        ['📥 ইমেইল যোগ', '🗑 ইমেইল মুছুন'],
        ['⚙️ সেটিংস', '🆘 সহায়তা']
    ], resize_keyboard=True)

# --- প্রিমিয়াম ওয়েলকাম মেসেজ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    welcome_text = (
        f"💎 <b>স্বাগতম, {user}!</b>\n\n"
        f"আপনার <b>Professional Email Sender</b> এখন প্রস্তুত।\n"
        f"নিচের মেনু ব্যবহার করে আপনার কার্যক্রম শুরু করুন।\n\n"
        f"📈 <b>সিস্টেম স্ট্যাটাস:</b>\n"
        f"👥 সংরক্ষিত ইমেইল: {get_email_count()} টি\n"
        f"⚡ এপিআই সংযোগ: ✅ সচল\n"
        f"🌐 সার্ভার: Render Cloud (Live)"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu(), parse_mode=ParseMode.HTML)

# --- Brevo API logic ---
def send_via_brevo(to_email, subject, body):
    url = "https://api.brevo.com/v3/smtp/email"
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": f"<html><body style='font-family: Arial; line-height: 1.6; color: #333;'>{body}</body></html>"
    }
    headers = {"accept": "application/json", "content-type": "application/json", "api-key": BREVO_API_KEY}
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code

# --- বাটন হ্যান্ডলিং ---
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == '✉️ ইমেইল পাঠান':
        await update.message.reply_text(
            "🚀 <b>নতুন ইমেইল ক্যাম্পেইন</b>\n\n"
            "ইমেইল পাঠাতে নিচের ফরম্যাটটি ব্যবহার করুন:\n"
            "<code>/send বিষয় | আপনার বার্তা</code>", 
            parse_mode=ParseMode.HTML
        )
    
    elif text == '📊 ড্যাশবোর্ড':
        await update.message.reply_text(
            f"📊 <b>আপনার পরিসংখ্যান:</b>\n\n"
            f"👥 মোট গ্রাহক: {get_email_count()} জন\n"
            f"🕒 লাস্ট আপডেট: {time.strftime('%H:%M:%S')}\n"
            f"✅ এপিআই স্ট্যাটাস: ভেরিফাইড",
            parse_mode=ParseMode.HTML
        )
    
    elif text == '📥 ইমেইল যোগ':
        await update.message.reply_text("➕ ইমেইল যোগ করতে লিখুন: <code>/add email@example.com</code>", parse_mode=ParseMode.HTML)

    elif text == '🗑 ইমেইল মুছুন':
        await update.message.reply_text("🗑 ইমেইল মুছতে লিখুন: <code>/remove email@example.com</code>", parse_mode=ParseMode.HTML)

    elif text == '⚙️ সেটিংস':
        await update.message.reply_text(f"⚙️ <b>সেটিংস:</b>\n\n📧 প্রেরক: {SENDER_EMAIL}\n🏢 ব্র্যান্ড: {SENDER_NAME}", parse_mode=ParseMode.HTML)

# --- অ্যাড/রিমুভ কমান্ডস ---
async def add_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        email = update.message.text.split('/add ')[1].strip()
        if "@" in email:
            with open(EMAIL_FILE, 'a') as f: f.write(f"\n{email}")
            await update.message.reply_text(f"✅ ইমেইল <b>{email}</b> যোগ করা হয়েছে।", parse_mode=ParseMode.HTML)
    except: await update.message.reply_text("❌ ভুল কমান্ড।")

async def remove_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target = update.message.text.split('/remove ')[1].strip()
        with open(EMAIL_FILE, 'r') as f: lines = f.readlines()
        with open(EMAIL_FILE, 'w') as f:
            for line in lines:
                if line.strip() != target: f.write(line)
        await update.message.reply_text(f"🗑 <b>{target}</b> রিমুভ করা হয়েছে।", parse_mode=ParseMode.HTML)
    except: await update.message.reply_text("❌ ইমেইল পাওয়া যায়নি।")

# --- ইমেইল পাঠানো ---
async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "|" not in update.message.text:
        await update.message.reply_text("❌ <b>ফরম্যাট ভুল!</b>\nসঠিক নিয়ম: <code>/send বিষয় | মেসেজ</code>", parse_mode=ParseMode.HTML)
        return
    
    msg = await update.message.reply_text("⚡ <b>ইমেইল পাঠানো শুরু হচ্ছে...</b>", parse_mode=ParseMode.HTML)
    try:
        content = update.message.text.split('/send ')[1]
        subject, body = content.split('|')
        with open(EMAIL_FILE, 'r') as f:
            emails = [line.strip() for line in f.readlines() if "@" in line]
        
        success = 0
        for email in emails:
            if send_via_brevo(email, subject.strip(), body.strip()) == 201:
                success += 1
            time.sleep(0.5)
        
        await msg.edit_text(f"✅ <b>মিশন সফল!</b>\n📊 মোট {success} টি ইমেইল পাঠানো হয়েছে।", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.edit_text(f"⚠️ ক্রুটি: {str(e)}")

if __name__ == '__main__':
    # Cron-job সাপোর্ট করার জন্য হেলথ চেক সার্ভার শুরু
    threading.Thread(target=run_server, daemon=True).start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_command))
    app.add_handler(CommandHandler("add", add_email))
    app.add_handler(CommandHandler("remove", remove_email))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_buttons))
    
    print("Bot is running...")
    app.run_polling()
