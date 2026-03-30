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

# --- Cron-job & Health Check ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Server Active")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthCheck).serve_forever()

# --- মেইন কিবোর্ড ---
def main_menu():
    return ReplyKeyboardMarkup([
        ['🚀 অটো ইমেইল পাঠান', '📊 ড্যাশবোর্ড'],
        ['📥 ইমেইল যোগ', '⚙️ সেটিংস']
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        f"🎁 <b>স্বাগতম!</b>\n\n"
        f"এখন ইমেইল পাঠানো আরও সহজ। সব প্রফেশনাল টেক্সট বটের ভেতরে সেট করা আছে।\n"
        f"আপনি শুধু লিঙ্ক দেবেন আর বট মেইল পাঠিয়ে দেবে।"
    )
    await update.message.reply_text(welcome, reply_markup=main_menu(), parse_mode=ParseMode.HTML)

# --- Brevo API (প্রফেশনাল বডি ও বাটনসহ) ---
def send_via_brevo(to_email, ad_link):
    url = "https://api.brevo.com/v3/smtp/email"
    
    # এখানে আপনার সব প্রফেশনাল লেখা সেট করা হয়েছে
    subject = "🎁 Exclusive Invitation: Claim Your Amazon Customer Appreciation Reward"
    
    html_content = f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; padding: 20px; background-color: #f9f9f9;">
        <div style="max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 12px; border: 1px solid #e0e0e0; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="color: #232f3e; margin: 0;">Congratulations! 🎊</h1>
            </div>
            <p style="font-size: 16px;">Hello,</p>
            <p style="font-size: 15px;">We are pleased to inform you that you have been selected as one of our valued customers to receive a special promotional reward. This offer is part of our seasonal loyalty program.</p>
            
            <p style="font-size: 15px; font-weight: bold; color: #cc0000;">⚠️ This reward is time-sensitive and must be claimed within the next 24 hours.</p>
            
            <div style="text-align: center; margin: 35px 0;">
                <a href="{ad_link.strip()}" 
                   style="background-color: #ff9900; color: #111; padding: 18px 35px; text-decoration: none; font-size: 18px; font-weight: bold; border-radius: 6px; border: 1px solid #a88734; display: inline-block; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                   CLAIM YOUR GIFT CARD NOW
                </a>
            </div>
            
            <p style="font-size: 14px; color: #555;">No purchase or credit card information is required. Simply follow the verification steps on the official page to receive your code instantly.</p>
            
            <hr style="border: 0; border-top: 1px solid #eee; margin: 25px 0;">
            <p style="font-size: 12px; color: #999; text-align: center;">© 2026 Amazon Promotional Distribution Team. <br>All rights reserved.</p>
        </div>
    </body>
    </html>
    """
    
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content
    }
    headers = {"accept": "application/json", "content-type": "application/json", "api-key": BREVO_API_KEY}
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code

# --- বাটন হ্যান্ডলার ---
async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # এখন শুধু লিঙ্ক চেক করবে
    if "/send" not in update.message.text or len(update.message.text.split()) < 2:
        await update.message.reply_text("❌ নিয়ম: <code>/send আপনার-অ্যাড-লিঙ্ক</code>", parse_mode=ParseMode.HTML)
        return
    
    ad_link = update.message.text.split('/send ')[1].strip()
    msg = await update.message.reply_text("⏳ <b>প্রফেশনাল ইমেইল পাঠানো হচ্ছে...</b>", parse_mode=ParseMode.HTML)
    
    try:
        with open(EMAIL_FILE, 'r') as f:
            emails = [line.strip() for line in f.readlines() if "@" in line]
        
        success = 0
        for email in emails:
            if send_via_brevo(email, ad_link) == 201:
                success += 1
            time.sleep(0.5)
        
        await msg.edit_text(f"✅ <b>মিশন সফল!</b>\n📊 মোট {success} জনকে প্রফেশনাল মেইল পাঠানো হয়েছে।")
    except Exception as e:
        await msg.edit_text(f"⚠️ Error: {str(e)}")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == '🚀 অটো ইমেইল পাঠান':
        await update.message.reply_text("🔗 শুধু আপনার Adsterra লিঙ্কটি পাঠান এভাবে:\n\n<code>/send https://your-link.com</code>", parse_mode=ParseMode.HTML)
    elif text == '📊 ড্যাশবোর্ড':
        await update.message.reply_text(f"📊 ইমেইল সংখ্যা: {get_email_count()} টি")

if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_buttons))
    app.run_polling()
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
