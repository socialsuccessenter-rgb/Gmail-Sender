import os
import logging
import yagmail
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("বট সচল! ইমেইল পাঠাতে লিখুন: /send Subject | Message")

async def send_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "|" not in update.message.text:
        await update.message.reply_text("ফরম্যাট: /send Subject | Message")
        return

    try:
        content = update.message.text.split('/send ')[1]
        subject, body = content.split('|')
        
        with open('emails.txt', 'r') as f:
            emails = [line.strip() for line in f.readlines() if line.strip()]

        await update.message.reply_text(f"{len(emails)} জনকে পাঠানোর চেষ্টা করছি...")

        # yagmail ব্যবহার করে জিমেইল পাঠানো
        yag = yagmail.SMTP(GMAIL_USER, GMAIL_PASS)
        
        for email in emails:
            yag.send(to=email, subject=subject.strip(), contents=body.strip())
        
        await update.message.reply_text("সফলভাবে পাঠানো হয়েছে! ✅")
    except Exception as e:
        await update.message.reply_text(f"ভুল হয়েছে: {str(e)}")

if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_email))
    app.run_polling()
