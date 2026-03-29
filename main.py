import os
import logging
import smtplib
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from email.message import EmailMessage
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

# Logging
logging.basicConfig(level=logging.INFO)

# Secrets
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GMAIL_USER = os.getenv("GMAIL_ADDRESS")
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")

# Render Port Fixer
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Active")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthCheck).serve_forever()

# সুন্দর স্টার্ট মেসেজ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_text = (
        f"👋 <b>স্বাগতম, {user_name}!</b>\n\n"
        "🚀 <b>ইমেইল মার্কেটিং বোট</b> এখন আপনার নিয়ন্ত্রণে।\n"
        "এটি ব্যবহার করে আপনি নিমেষেই হাজারো ইমেইল পাঠাতে পারবেন।\n\n"
        "📌 <b>কিভাবে ব্যবহার করবেন?</b>\n"
        "নিচের বাটনে ক্লিক করুন অথবা টাইপ করুন:\n"
        "<code>/send Subject | Message</code>"
    )
    
    # বাটন যোগ করা
    keyboard = [
        [InlineKeyboardButton("📊 স্ট্যাটাস চেক", callback_data='status')],
        [InlineKeyboardButton("📖 সাহায্য নিন", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_code=ParseMode.HTML)

# বাটন ক্লিকের রেসপন্স
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'status':
        await query.edit_message_text(text="✅ <b>সিস্টেম অনলাইন:</b> জিমেইল সার্ভার কানেক্টেড।", parse_mode=ParseMode.HTML)
    elif query.data == 'help':
        await query.edit_message_text(text="❓ <b>সাহায্য:</b> ইমেইল পাঠাতে <code>/send</code> কমান্ডের পর Subject এবং Message এর মাঝে একটি <code>|</code> চিহ্ন দিন।", parse_mode=ParseMode.HTML)

# ইমেইল পাঠানোর সুন্দর ইন্টারফেস
async def send_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "|" not in update.message.text:
        await update.message.reply_text("❌ <b>ভুল ফরম্যাট!</b>\nসঠিক নিয়ম: <code>/send বিষয় | মেসেজ</code>", parse_mode=ParseMode.HTML)
        return

    status_msg = await update.message.reply_text("⏳ <b>প্রসেসিং শুরু হচ্ছে...</b>", parse_mode=ParseMode.HTML)

    try:
        content = update.message.text.split('/send ')[1]
        subject, body = content.split('|')
        
        with open('emails.txt', 'r') as f:
            emails = [line.strip() for line in f.readlines() if line.strip()]

        await status_msg.edit_text(f"📤 <b>{len(emails)} জনকে পাঠানোর চেষ্টা করছি...</b>", parse_mode=ParseMode.HTML)

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_PASS)
        
        for email in emails:
            msg = EmailMessage()
            msg.set_content(body.strip())
            msg['Subject'] = subject.strip()
            msg['From'] = GMAIL_USER
            msg['To'] = email
            server.send_message(msg)
        
        server.quit()
        await status_msg.edit_text("✅ <b>সাফল্য!</b>\nসবগুলো ইমেইল সফলভাবে ইনবক্সে পৌঁছেছে। 🚀", parse_mode=ParseMode.HTML)

    except Exception as e:
        await status_msg.edit_text(f"⚠️ <b>এরর রিপোর্ট:</b>\n<code>{str(e)}</code>", parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_email))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("Bot is beautified and running...")
    app.run_polling()
