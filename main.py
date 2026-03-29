import os
import requests
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

# Logging সেটআপ
logging.basicConfig(level=logging.INFO)

# আপনার দেওয়া Brevo API Key এবং অন্যান্য তথ্য
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BREVO_API_KEY = "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"
SENDER_EMAIL = os.getenv("SENDER_EMAIL") # Render-এ আপনার জিমেইলটি সেট করে রাখুন
SENDER_NAME = "Premium Mailer"

# Render Port Fixer (সার্ভার সচল রাখার জন্য)
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running via Brevo API")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthCheck).serve_forever()

# স্টার্ট মেসেজ (নতুন ডিজাইন)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    welcome_text = (
        f"🚀 <b>স্বাগতম {user}!</b>\n\n"
        "✅ আপনার বট এখন <b>Brevo API</b>-এর সাথে যুক্ত।\n"
        "📊 এখন আপনি প্রতিদিন ৩০০টি ইমেইল পাঠাতে পারবেন।\n\n"
        "📝 <b>ইমেইল পাঠানোর নিয়ম:</b>\n"
        "<code>/send Subject | Message Body</code>"
    )
    keyboard = [[InlineKeyboardButton("🛠 সিস্টেম স্ট্যাটাস", callback_data='status')]]
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

# বাটন অ্যাকশন
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'status':
        await query.edit_message_text(text="🟢 <b>সার্ভার:</b> সচল\n📡 <b>মেথড:</b> Brevo API (High Speed)", parse_mode=ParseMode.HTML)

# Brevo API-এর মাধ্যমে ইমেইল পাঠানোর ফাংশন
def send_via_brevo(to_email, subject, body):
    url = "https://api.brevo.com/v3/smtp/email"
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": f"<html><body><div style='font-family: Arial; padding: 20px;'>{body}</div></body></html>"
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code

# সেন্ড কমান্ড প্রসেসিং
async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "|" not in update.message.text:
        await update.message.reply_text("❌ <b>ভুল ফরম্যাট!</b>\nসঠিক নিয়ম: <code>/send Subject | Message</code>", parse_mode=ParseMode.HTML)
        return

    msg = await update.message.reply_text("⏳ <b>ইমেইল প্রসেস করা হচ্ছে...</b>", parse_mode=ParseMode.HTML)

    try:
        content = update.message.text.split('/send ')[1]
        subject, body = content.split('|')
        
        # emails.txt ফাইল থেকে ইমেইল লিস্ট পড়া
        with open('emails.txt', 'r') as f:
            emails = [line.strip() for line in f.readlines() if line.strip()]

        await msg.edit_text(f"📤 <b>{len(emails)} জনকে ইমেইল পাঠানো শুরু হয়েছে...</b>", parse_mode=ParseMode.HTML)

        success_count = 0
        for email in emails:
            code = send_via_brevo(email, subject.strip(), body.strip())
            if code == 201: # Brevo-তে ২০১ মানে সফলভাবে পাঠানো হয়েছে
                success_count += 1
        
        await msg.edit_text(f"✅ <b>মিশন সফল!</b>\n{success_count} টি ইমেইল পাঠানো হয়েছে।", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.edit_text(f"⚠️ <b>ত্রুটি:</b>\n<code>{str(e)}</code>", parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    # সার্ভার থ্রেড চালু করা
    threading.Thread(target=run_server, daemon=True).start()
    
    # টেলিগ্রাম বট চালু করা
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_command))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("Bot is alive...")
    app.run_polling()
