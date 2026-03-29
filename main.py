import os, requests, logging, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

logging.basicConfig(level=logging.INFO)

# --- কনফিগারেশন ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = "Premium Business Mailer"

# ইমেইল লিস্ট ফাইল
EMAIL_FILE = 'emails.txt'

def get_email_count():
    if not os.path.exists(EMAIL_FILE): return 0
    with open(EMAIL_FILE, 'r') as f:
        return len([line for line in f.readlines() if "@" in line])

# --- হেলথ চেক সার্ভার ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Bot Active")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthCheck).serve_forever()

# --- মেইন মেনু কিবোর্ড ---
def main_menu_keyboard():
    return ReplyKeyboardMarkup([
        ['🚀 ইমেইল পাঠান', '📊 পরিসংখ্যান'],
        ['➕ ইমেইল যোগ করুন', '❌ ইমেইল মুছুন'],
        ['⚙️ সেটিংস', '❓ সহায়তা']
    ], resize_keyboard=True)

# --- বটের ওয়েলকাম মেসেজ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    welcome_text = (
        f"🌟 <b>স্বাগতম {user}!</b>\n\n"
        f"এটি আপনার <b>প্রিমিয়াম ইমেইল মার্কেটিং ড্যাশবোর্ড</b>।\n"
        f"নিচের মেনু ব্যবহার করে আপনার ক্যাম্পেইন পরিচালনা করুন।\n\n"
        f"📩 <b>মোট ইমেইল সেভ আছে:</b> {get_email_count()} টি\n"
        f"⚡ <b>সার্ভার স্ট্যাটাস:</b> সচল"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard(), parse_mode=ParseMode.HTML)

# --- Brevo API logic ---
def send_via_brevo(to_email, subject, body):
    url = "https://api.brevo.com/v3/smtp/email"
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": f"<html><body style='font-family: Arial; padding: 20px;'>{body}</body></html>"
    }
    headers = {"accept": "application/json", "content-type": "application/json", "api-key": BREVO_API_KEY}
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code

# --- বাটন হ্যান্ডলিং ---
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == '🚀 ইমেইল পাঠান':
        await update.message.reply_text(
            "📝 <b>নতুন ক্যাম্পেইন শুরু করুন</b>\n\nনিচের ফরম্যাটে মেসেজ পাঠান:\n"
            "<code>/send বিষয় | আপনার মেসেজ</code>", 
            parse_mode=ParseMode.HTML
        )
    
    elif text == '📊 পরিসংখ্যান':
        count = get_email_count()
        await update.message.reply_text(
            f"📊 <b>আপনার বর্তমান পরিসংখ্যান:</b>\n\n"
            f"👥 মোট গ্রাহক: {count} জন\n"
            f"📤 দৈনিক লিমিট: ৩০০ টি\n"
            f"✅ এপিআই কি: সক্রিয়",
            parse_mode=ParseMode.HTML
        )
    
    elif text == '➕ ইমেইল যোগ করুন':
        await update.message.reply_text(
            "➕ <b>নতুন ইমেইল যোগ করুন</b>\n\nনিচের ফরম্যাটে ইমেইলটি দিন:\n"
            "<code>/add example@gmail.com</code>",
            parse_mode=ParseMode.HTML
        )

    elif text == '❌ ইমেইল মুছুন':
        await update.message.reply_text(
            "❌ <b>ইমেইল মুছুন</b>\n\nনিচের ফরম্যাটে মেসেজ দিন:\n"
            "<code>/remove example@gmail.com</code>",
            parse_mode=ParseMode.HTML
        )

    elif text == '⚙️ সেটিংস':
        await update.message.reply_text(
            f"⚙️ <b>বট কনফিগারেশন:</b>\n\n"
            f"📧 প্রেরক: {SENDER_EMAIL}\n"
            f"🏢 নাম: {SENDER_NAME}\n"
            f"🌐 সার্ভার: Render Cloud",
            parse_mode=ParseMode.HTML
        )

# --- ইমেইল অ্যাড/রিমুভ কমান্ডস ---
async def add_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.split('/add ')[1].strip()
    if "@" in email:
        with open(EMAIL_FILE, 'a') as f: f.write(f"\n{email}")
        await update.message.reply_text(f"✅ ইমেইল <b>{email}</b> সফলভাবে যোগ করা হয়েছে।", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("❌ সঠিক ইমেইল ফরম্যাট দিন।")

async def remove_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.message.text.split('/remove ')[1].strip()
    if os.path.exists(EMAIL_FILE):
        with open(EMAIL_FILE, 'r') as f: lines = f.readlines()
        with open(EMAIL_FILE, 'w') as f:
            for line in lines:
                if line.strip() != target: f.write(line)
        await update.message.reply_text(f"🗑 <b>{target}</b> রিমুভ করা হয়েছে।", parse_mode=ParseMode.HTML)

# --- ইমেইল পাঠানো ---
async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "|" not in update.message.text:
        await update.message.reply_text("❌ ভুল ফরম্যাট! সঠিক নিয়ম: <code>/send বিষয় | মেসেজ</code>", parse_mode=ParseMode.HTML)
        return
    
    msg = await update.message.reply_text("⏳ <b>প্রসেসিং...</b>")
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
        
        await msg.edit_text(f"✅ <b>ক্যাম্পেইন সফল!</b>\n📊 সফলভাবে পাঠানো হয়েছে: {success} টি", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.edit_text(f"Error: {e}")

if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_command))
    app.add_handler(CommandHandler("add", add_email))
    app.add_handler(CommandHandler("remove", remove_email))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_buttons))
    app.run_polling()
if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.run_polling()
