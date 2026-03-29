import os
import logging
import smtplib
from email.message import EmailMessage
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Logging setup
logging.basicConfig(level=logging.INFO)

# Environment Variables (Render এর Environment সেকশন থেকে আসবে)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GMAIL_USER = os.getenv("GMAIL_ADDRESS")
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "বট সচল হয়েছে! ✅\n\n"
        "ইমেইল পাঠাতে এভাবে লিখুন:\n"
        "/send Subject | Message Body\n\n"
        "যেমন: /send Hello | This is a test mail"
    )

async def send_bulk_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "|" not in update.message.text:
        await update.message.reply_text("ভুল ফরম্যাট! /send Subject | Message এভাবে লিখুন।")
        return

    try:
        content = update.message.text.split('/send ')[1]
        subject, body = content.split('|')
        
        # emails.txt থেকে ইমেইল লিস্ট পড়া
        if not os.path.exists('emails.txt'):
            await update.message.reply_text("Error: emails.txt ফাইলটি পাওয়া যায়নি!")
            return

        with open('emails.txt', 'r') as f:
            emails = [line.strip() for line in f.readlines() if line.strip()]

        await update.message.reply_text(f"{len(emails)} জনকে পাঠানোর চেষ্টা করছি...")

        # ইমেইল পাঠানোর মূল প্রক্রিয়া
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            for email in emails:
                msg = EmailMessage()
                msg.set_content(body.strip())
                msg['Subject'] = subject.strip()
                msg['From'] = GMAIL_USER
                msg['To'] = email
                server.send_message(msg)

        await update.message.reply_text("সবগুলো ইমেইল সফলভাবে পাঠানো হয়েছে! 🚀")
    except Exception as e:
        await update.message.reply_text(f"ভুল হয়েছে: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_bulk_email))
    app.run_polling()
