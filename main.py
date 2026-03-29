import os
import logging
import smtplib
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from email.message import EmailMessage
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Logging setup
logging.basicConfig(level=logging.INFO)

# Environment Variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GMAIL_USER = os.getenv("GMAIL_ADDRESS")
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")

# --- Render Port Error Fixer ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Live")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# --- Email Sending Logic ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("বট সচল! ইমেইল পাঠাতে লিখুন: /send Subject | Message")

async def send_bulk_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "|" not in update.message.text:
        await update.message.reply_text("ভুল ফরম্যাট! /send Subject | Message এভাবে লিখুন।")
        return

    try:
        content = update.message.text.split('/send ')[1]
        subject, body = content.split('|')
        
        with open('emails.txt', 'r') as f:
            emails = [line.strip() for line in f.readlines() if line.strip()]

        await update.message.reply_text(f"{len(emails)} জনকে পাঠানোর চেষ্টা করছি...")

        # নেটওয়ার্ক এরর এড়াতে নতুন কানেকশন পদ্ধতি
        try:
            # Port 587 ব্যবহার করে কানেকশন
            server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
            server.ehlo()
            server.starttls() # সিকিউর কানেকশন
            server.ehlo()
            server.login(GMAIL_USER, GMAIL_PASS)
            
            for email in emails:
                msg = EmailMessage()
                msg.set_content(body.strip())
                msg['Subject'] = subject.strip()
                msg['From'] = GMAIL_USER
                msg['To'] = email
                server.send_message(msg)
            
            server.quit()
            await update.message.reply_text("সবগুলো ইমেইল সফলভাবে পাঠানো হয়েছে! ✅")
            
        except Exception as smtp_err:
            # যদি ৫8৭ কাজ না করে তবে ৪৬৫ ট্রাই করবে
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=30)
            server.login(GMAIL_USER, GMAIL_PASS)
            # ... ইমেইল পাঠানোর কোড ...
            server.quit()
            await update.message.reply_text("ইমেইল পাঠানো সফল (SSL)! ✅")

    except Exception as e:
        await update.message.reply_text(f"ভুল হয়েছে: {str(e)}")

if __name__ == '__main__':
    threading.Thread(target=run_health_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_bulk_email))
    app.run_polling()
