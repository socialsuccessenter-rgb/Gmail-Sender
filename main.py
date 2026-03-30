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
SENDER_NAME = "Amazon Gift Card Manager"

EMAIL_FILE = 'emails.txt'

def get_email_count():
    if not os.path.exists(EMAIL_FILE): return 0
    with open(EMAIL_FILE, 'r') as f:
        return len([line for line in f.readlines() if "@" in line])

# --- Health Check Server ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Active")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthCheck).serve_forever()

# --- মেইন কিবোর্ড ---
def main_menu():
    return ReplyKeyboardMarkup([
        ['✉️ ইমেইল পাঠান', '📊 ড্যাশবোর্ড'],
        ['📥 ইমেইল যোগ', '⚙️ সেটিংস']
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        f"🎁 <b>স্বাগতম!</b>\n\n"
        f"আপনার <b>Amazon Rewards Dashboard</b> প্রস্তুত।\n"
        f"এখন থেকে বাটনসহ ইমেইল পাঠাতে পারবেন।\n\n"
        f"👥 মোট ইমেইল: {get_email_count()} টি"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu(), parse_mode=ParseMode.HTML)

# --- Brevo API (ফিক্সড কোড) ---
def send_via_brevo(to_email, subject, ad_link):
    url = "https://api.brevo.com/v3/smtp/email"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial; line-height: 1.6; color: #333; padding: 20px; background-color: #f4f4f4;">
        <div style="max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd;">
            <h2 style="color: #232f3e; text-align: center;">Congratulations! 🎁</h2>
            <p>We have an exclusive Amazon Gift Card waiting for you. Please click the button below to claim it.</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{ad_link.strip()}" 
                   style="background-color: #ff9900; color: #111; padding: 15px 30px; text-decoration: none; font-size: 18px; font-weight: bold; border-radius: 5px; display: inline-block;">
                   Claim Your Gift Card Now
                </a>
            </div>
            <p style="font-size: 12px; color: #999; text-align: center;">Sent by Amazon Distribution Team</p>
        </div>
    </body>
    </html>
    """
    
    # এখানে ভুল ছিল, এখন ঠিক করা হয়েছে
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content
    }
    headers = {"accept": "application/json", "content-type": "application/json", "api-key": BREVO_API_KEY}
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code

# --- কমান্ড হ্যান্ডলার ---
async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "|" not in update.message.text:
        await update.message.reply_text("❌ নিয়ম: <code>/send সাবজেক্ট | লিঙ্ক</code>", parse_mode=ParseMode.HTML)
        return
    
    msg = await update.message.reply_text("⏳ <b>ইমেইল পাঠানো হচ্ছে...</b>")
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
        await msg.edit_text(f"✅ <b>সফল:</b> {success} টি ইমেইল পাঠানো হয়েছে।")
    except Exception as e:
        await msg.edit_text(f"⚠️ Error: {str(e)}")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == '✉️ ইমেইল পাঠান':
        await update.message.reply_text("🚀 লিখুন: <code>/send সাবজেক্ট | অ্যাড লিঙ্ক</code>", parse_mode=ParseMode.HTML)
    elif text == '📊 ড্যাশবোর্ড':
        await update.message.reply_text(f"📊 মোট ইমেইল: {get_email_count()} টি")

if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_buttons))
    app.run_polling()

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
