import os
import requests
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode

# Logging
logging.basicConfig(level=logging.INFO)

# Secrets
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BREVO_API_KEY = "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"
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = os.getenv("SENDER_NAME", "Premium Mailer")

# --- Render সচল রাখার সার্ভার ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running High Performance")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthCheck).serve_forever()

# --- স্থায়ী মেনু বাটন ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    
    # নিচের স্থায়ী বাটন (Reply Keyboard)
    main_menu = [['🚀 ইমেইল পাঠান', '📊 স্ট্যাটাস চেক'], ['⚙️ সেটিংস', '❓ সহায়তা']]
    reply_markup = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)

    welcome_text = (
        f"💎 <b>স্বাগতম {user}!</b>\n\n"
        "🚀 এটি আপনার <b>আল্টিমেট ইমেইল মার্কেটিং বট।</b>\n"
        "নিচের মেনু ব্যবহার করে খুব সহজে কাজ করুন।\n\n"
        "📢 <b>নির্দেশনা:</b> ইমেইল পাঠাতে নিচের <i>'ইমেইল পাঠান'</i> বাটনে ক্লিক করুন।"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

# --- Brevo API কানেকশন ---
def send_via_brevo(to_email, subject, body):
    url = "https://api.brevo.com/v3/smtp/email"
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": f"<html><body style='font-family: Arial; line-height: 1.6;'>{body}</body></html>"
    }
    headers = {"accept": "application/json", "content-type": "application/json", "api-key": BREVO_API_KEY}
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code

# --- মেনু বাটন হ্যান্ডলার ---
async def handle_menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == '🚀 ইমেইল পাঠান':
        await update.message.reply_text("📝 <b>ইমেইল পাঠানোর নিয়ম:</b>\n\nনিচের ফরম্যাটে মেসেজ লিখুন:\n<code>/send Subject | Message</code>", parse_mode=ParseMode.HTML)
    
    elif text == '📊 স্ট্যাটাস চেক':
        await update.message.reply_text("🟢 <b>সার্ভার:</b> অনলাইন\n📡 <b>মেথড:</b> Brevo High-Speed API\n📧 <b>ডেইলি কোটা:</b> ৩০০ টি", parse_mode=ParseMode.HTML)

    elif text == '⚙️ সেটিংস':
        await update.message.reply_text(f"🛠 <b>সেটিংস:</b>\n👤 প্রেরক: {SENDER_NAME}\n📧 ইমেইল: {SENDER_EMAIL}", parse_mode=ParseMode.HTML)

    elif text == '❓ সহায়তা':
        await update.message.reply_text("❓ <b>হেল্পলাইন:</b>\nনিশ্চিত করুন আপনার GitHub-এ <code>emails.txt</code> ফাইলটি সঠিকভাবে আছে।", parse_mode=ParseMode.HTML)

# --- মূল সেন্ডিং কমান্ড ---
async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "|" not in update.message.text:
        await update.message.reply_text("❌ <b>ভুল ফরম্যাট!</b>\nসঠিক নিয়ম: <code>/send বিষয় | মেসেজ</code>", parse_mode=ParseMode.HTML)
        return

    msg = await update.message.reply_text("🔍 <b>ফাইল ডাটাবেজ চেক করা হচ্ছে...</b>", parse_mode=ParseMode.HTML)

    try:
        content = update.message.text.split('/send ')[1]
        subject, body = content.split('|')
        
        # ফাইল চেক (০ ইমেইল সমস্যা সমাধানের জন্য)
        if not os.path.exists('emails.txt'):
            await msg.edit_text("❌ <b>Error:</b> emails.txt ফাইলটি পাওয়া যায়নি!")
            return

        with open('emails.txt', 'r') as f:
            emails = [line.strip() for line in f.readlines() if "@" in line]

        if not emails:
            await msg.edit_text("⚠️ <b>ফাইলটি খালি!</b>\nঅনুগ্রহ করে emails.txt ফাইলে ইমেইল যোগ করুন।")
            return

        await msg.edit_text(f"📤 <b>{len(emails)} জনকে ইমেইল পাঠানো শুরু হয়েছে...</b>", parse_mode=ParseMode.HTML)

        success = 0
        for email in emails:
            if send_via_brevo(email.strip(), subject.strip(), body.strip()) == 201:
                success += 1
            time.sleep(0.5) # রেট লিমিট এড়াতে

        await msg.edit_text(f"✅ <b>মিশন কমপ্লিট!</b>\n📊 সফল: {success} টি\n❌ ব্যর্থ: {len(emails) - success} টি", parse_mode=ParseMode.HTML)

    except Exception as e:
        await msg.edit_text(f"⚠️ <b>ত্রুটি:</b>\n<code>{str(e)}</code>", parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_menu_click))
    
    app.run_polling()
