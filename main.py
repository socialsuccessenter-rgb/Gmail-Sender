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

# Environment Variables (Render থেকে আসবে)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GMAIL_USER = os.getenv("GMAIL_ADDRESS")
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")

# --- Render এর Port Error বন্ধ করার জন্য Fake Server ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# --- বটের মূল কাজ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("বট সচল! ইমেইল পাঠাতে লিখুন: /send Subject ,, Message")

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

        # Render এর জন্য Port 587 এবং STARTTLS ব্যবহার করা হলো
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() 
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

    except Exception as e:
        await update.message.reply_text(f"ভুল হয়েছে: {str(e)}")

if __name__ == '__main__':
    # Fake Server চালু করা (Render এর জন্য)
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # টেলিগ্রাম বট চালু করা
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_bulk_email))
    print("Bot is starting...")
    app.run_polling()
