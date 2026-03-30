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

# --- Cron-job Support ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Bot is Live")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthCheck).serve_forever()

# --- কিবোর্ড ---
def main_menu():
    return ReplyKeyboardMarkup([
        ['🚀 অটো ইমেইল পাঠান', '📊 ড্যাশবোর্ড'],
        ['📥 ইমেইল যোগ', '⚙️ সেটিংস']
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎁 <b>Amazon Rewards Bot প্রস্তুত!</b>\n\nএখন শুধু লিঙ্ক পাঠালেই প্রফেশনাল ইমেইল চলে যাবে।",
        reply_markup=main_menu(),
        parse_mode=ParseMode.HTML
    )

# --- ইমেইল পাঠানোর লজিক ---
def send_via_brevo(to_email, ad_link):
    url = "https://api.brevo.com/v3/smtp/email"
    subject = "🎁 Exclusive Invitation: Claim Your Amazon Customer Appreciation Reward"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 10px; border: 1px solid #ddd;">
            <h1 style="color: #232f3e; text-align: center;">Congratulations! 🎊</h1>
            <p>Hello, you have been selected to receive a special promotional reward from our seasonal loyalty program.</p>
            <p style="color: #cc0000; font-weight: bold;">⚠️ This offer expires in 24 hours.</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{ad_link.strip()}" style="background-color: #ff9900; color: #111; padding: 15px 30px; text-decoration: none; font-size: 18px; font-weight: bold; border-radius: 5px; display: inline-block;">CLAIM YOUR GIFT CARD NOW</a>
            </div>
            <p style="font-size: 12px; color: #777;">Sent by Amazon Promotional Team. No purchase required.</p>
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

# --- বাটন ও কমান্ড হ্যান্ডলিং ---
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == '🚀 অটো ইমেইল পাঠান':
        await update.message.reply_text("🔗 আপনার লিঙ্কটি পাঠান এভাবে:\n<code>/send https://your-link.com</code>", parse_mode=ParseMode.HTML)
    
    elif text == '📊 ড্যাশবোর্ড':
        await update.message.reply_text(f"📊 মোট ইমেইল: {get_email_count()} টি")
    
    elif text.startswith('/send '):
        ad_link = text.split('/send ')[1].strip()
        msg = await update.message.reply_text("⏳ ইমেইল পাঠানো হচ্ছে...")
        
        try:
            with open(EMAIL_FILE, 'r') as f:
                emails = [line.strip() for line in f.readlines() if "@" in line]
            
            success = 0
            for email in emails:
                if send_via_brevo(email, ad_link) == 201:
                    success += 1
                time.sleep(0.5)
            await msg.edit_text(f"✅ সফলভাবে {success} টি মেইল পাঠানো হয়েছে!")
        except Exception as e:
            await msg.edit_text(f"⚠️ Error: {str(e)}")

if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_messages))
    app.run_polling()
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
