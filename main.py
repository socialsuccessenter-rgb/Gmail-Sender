import os
import logging
import smtplib
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from email.message import EmailMessage
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

# Logging
logging.basicConfig(level=logging.INFO)

# Secrets (Render Environment Variables থেকে আসবে)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GMAIL_USER = os.getenv("GMAIL_ADDRESS")
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")

# --- Render Port Fixer ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Premium Email Bot is Active")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    server.serve_forever()

# --- সুন্দর ইন্টারফেস ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    welcome_msg = (
        f"💎 <b>হ্যালো {user}!</b>\n\n"
        "🚀 আপনার <b>প্রিমিয়াম ইমেইল সেন্ডার</b> এখন প্রস্তুত।\n"
        "নিচের কমান্ডটি ব্যবহার করে প্রফেশনাল ইমেইল পাঠান:\n\n"
        "📝 <code>/send Subject | Message</code>\n\n"
        "⚡ <i>সিস্টেম স্ট্যাটাস চেক করতে নিচের বাটন চাপুন।</i>"
    )
    
    keyboard = [
        [InlineKeyboardButton("📊 সার্ভার চেক", callback_data='status')],
        [InlineKeyboardButton("💡 সাহায্য", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_msg, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'status':
        await query.edit_message_text("✅ <b>সার্ভার:</b> সচল\n🔐 <b>সিকিউরিটি:</b> SSL এনক্রিপ্টেড", parse_mode=ParseMode.HTML)
    elif query.data == 'help':
        await query.edit_message_text("❓ <b>সহায়তা:</b> ইমেইল পাঠাতে সাবজেক্ট এবং মেসেজের মাঝে অবশ্যই <code>|</code> চিহ্নটি দিবেন।", parse_mode=ParseMode.HTML)

# --- ইমেইল পাঠানোর মূল কাজ ---
async def send_bulk_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "|" not in update.message.text:
        await update.message.reply_text("❌ <b>ভুল পদ্ধতি!</b>\nসঠিক নিয়ম: <code>/send বিষয় | মেসেজ</code>", parse_mode=ParseMode.HTML)
        return

    progress_msg = await update.message.reply_text("📡 <b>সার্ভারের সাথে কানেক্ট করা হচ্ছে...</b>", parse_mode=ParseMode.HTML)

    try:
        content = update.message.text.split('/send ')[1]
        subject, body = content.split('|')
        
        with open('emails.txt', 'r') as f:
            emails = [line.strip() for line in f.readlines() if line.strip()]

        await progress_msg.edit_text(f"📤 <b>মোট {len(emails)} জন প্রাপককে পাঠানো হচ্ছে...</b>", parse_mode=ParseMode.HTML)

        # SSL কানেকশন (পার্থক্য এখানে)
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=45) 
        server.login(GMAIL_USER, GMAIL_PASS)
        
        for email in emails:
            msg = EmailMessage()
            msg.set_content(body.strip())
            msg['Subject'] = subject.strip()
            msg['From'] = GMAIL_USER
            msg['To'] = email
            server.send_message(msg)
            time.sleep(1) # সার্ভারে চাপ কমাতে ১ সেকেন্ড বিরতি

        server.quit()
        await progress_msg.edit_text("✅ <b>অভিনন্দন!</b>\nসবগুলো ইমেইল সফলভাবে পাঠানো হয়েছে। 🚀", parse_mode=ParseMode.HTML)

    except Exception as e:
        await progress_msg.edit_text(f"⚠️ <b>ত্রুটি ধরা পড়েছে:</b>\n<code>{str(e)}</code>", parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_bulk_email))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    app.run_polling()
