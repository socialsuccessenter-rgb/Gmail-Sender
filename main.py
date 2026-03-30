import os, requests, logging, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

logging.basicConfig(level=logging.INFO)

# --- কনফিগারেশন ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = "Amazon Gift Card Manager" # আপনার পছন্দের নাম

EMAIL_FILE = 'emails.txt'

def get_email_count():
    if not os.path.exists(EMAIL_FILE): return 0
    with open(EMAIL_FILE, 'r') as f:
        return len([line for line in f.readlines() if "@" in line])

# --- Cron-job & Health Check Server ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Server Active")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthCheck).serve_forever()

# --- মেইন কিবোর্ড ---
def main_menu():
    return ReplyKeyboardMarkup([
        ['✉️ ইমেইল পাঠান', '📊 ড্যাশবোর্ড'],
        ['📥 ইমেইল যোগ', '🗑 ইমেইল মুছুন'],
        ['⚙️ সেটিংস', '🆘 সহায়তা']
    ], resize_keyboard=True)

# --- স্টার্ট মেসেজ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    welcome_text = (
        f"🎁 <b>স্বাগতম, {user}!</b>\n\n"
        f"এটি আপনার <b>Amazon Rewards Dashboard</b>।\n"
        f"এখান থেকে আপনি সরাসরি বাটনসহ প্রফেশনাল ইমেইল পাঠাতে পারবেন।\n\n"
        f"👥 মোট ইমেইল: {get_email_count()} টি\n"
        f"⚡ স্ট্যাটাস: ✅ অনলাইন"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu(), parse_mode=ParseMode.HTML)

# --- Brevo API (বাটনসহ HTML ইমেইল ডিজাইন) ---
def send_via_brevo(to_email, subject, ad_link):
    url = "https://api.brevo.com/v3/smtp/email"
    
    # আকর্ষণীয় অ্যামাজন স্টাইল বাটন ডিজাইন
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; padding: 20px; background-color: #f4f4f4;">
        <div style="max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd;">
            <h2 style="color: #232f3e; text-align: center;">Congratulations! 🎁</h2>
            <p>Hi,</p>
            <p>We are pleased to inform you that you have been selected for our monthly customer appreciation reward. A promotional gift card is waiting for you.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{ad_link.strip()}" 
                   style="background-color: #ff9900; color: #111; padding: 15px 30px; text-decoration: none; font-size: 18px; font-weight: bold; border-radius: 5px; border: 1px solid #a88734; display: inline-block;">
                   Claim Your Gift Card Now
                </a>
            </div>
            
            <p style="font-size: 14px; color: #555;">Note: This offer is valid for the next 24 hours. Please click the button above to verify your identity and receive your code instantly.</p>
            <hr style="border: 0; border-top: 1px solid #eee;">
            <p style="font-size: 12px; color: #999; text-align: center;">Sent by Amazon Gift Card Distribution Team</p>
        </div>
    </body>
    </html>
    """
    
    payload = {
        "sender": {{"name": SENDER_NAME, "email": SENDER_EMAIL}},
        "to": [{{"email": to_email}}],
        "subject": subject,
        "htmlContent": html_content
    }
    headers = {"accept": "application/json", "content-type": "application/json", "api-key": BREVO_API_KEY}
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code

# --- বাটন হ্যান্ডলার ---
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == '✉️ ইমেইল পাঠান':
        await update.message.reply_text("🚀 <b>বাটনসহ ইমেইল পাঠানোর নিয়ম:</b>\n\n<code>/send সাবজেক্ট | আপনার অ্যাড লিঙ্ক</code>", parse_mode=ParseMode.HTML)
    elif text == '📊 ড্যাশবোর্ড':
        await update.message.reply_text(f"📊 <b>পরিসংখ্যান:</b>\n👥 ইমেইল সেভ আছে: {get_email_count()} টি")
    elif text == '⚙️ সেটিংস':
        await update.message.reply_text(f"⚙️ <b>সেটিংস:</b>\n📧 প্রেরক: {SENDER_EMAIL}\n🏢 নাম: {SENDER_NAME}")

# --- কমান্ড হ্যান্ডলার ---
async def add_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        email = update.message.text.split('/add ')[1].strip()
        with open(EMAIL_FILE, 'a') as f: f.write(f"\n{email}")
        await update.message.reply_text(f"✅ <b>{email}</b> যোগ করা হয়েছে।", parse_mode=ParseMode.HTML)
    except: await update.message.reply_text("❌ ভুল ফরম্যাট।")

async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "|" not in update.message.text:
        await update.message.reply_text("❌ নিয়ম: <code>/send সাবজেক্ট | লিঙ্ক</code>", parse_mode=ParseMode.HTML)
        return
    
    msg = await update.message.reply_text("⏳ <b>ইমেইল প্রসেসিং...</b>", parse_mode=ParseMode.HTML)
    try:
        content = update.message.text.split('/send ')[1]
        subject, link = content.split('|')
        with open(EMAIL_FILE, 'r') as f:
            emails = [line.strip() for line in f.readlines() if "@" in line]
        
        success = 0
        for email in emails:
            if send_via_brevo(email, subject.strip(), link.strip()) == 201:
                success += 1
            time.sleep(0.5)
        
        await msg.edit_text(f"✅ <b>মিশন কমপ্লিট!</b>\n📊 সফল: {success} টি ইমেইল পাঠানো হয়েছে।", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.edit_text(f"Error: {e}")

if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_command))
    app.add_handler(CommandHandler("add", add_email))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_buttons))
    app.run_polling()
