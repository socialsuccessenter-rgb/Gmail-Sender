import os
import logging
import smtplib
from email.message import EmailMessage
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Environment Variables (Render থেকে আসবে)
TOKEN = os.getenv("8673280780:AAF_KzU90nRS81x4PS33h-ucd-G_bGOw6TM")
GMAIL_USER = os.getenv("socialsuccessenter@gmail.com")
GMAIL_PASS = os.getenv("xrxi lhql wspp dvzx 6hqn n2eq mz74 njtn")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("স্বাগতম! ইমেইল পাঠানোর জন্য প্রথমে সাবজেক্ট লিখুন।\nনিয়ম: /send [Subject] | [Body]")

async def send_bulk_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.replace('/send ', '')
        subject, body = text.split('|')
        
        # ইমেইল লিস্ট পড়া
        with open('emails.txt', 'r') as f:
            emails = [line.strip() for line in f.readlines()]

        await update.message.reply_text(f"মোট {len(emails)} জনকে ইমেইল পাঠানো শুরু হচ্ছে...")

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
        await update.message.reply_text("সবগুলো ইমেইল সফলভাবে পাঠানো হয়েছে! ✅")
    except Exception as e:
        await update.message.reply_text(f"ভুল হয়েছে: {str(e)}\nব্যবহারের নিয়ম: /send Subject | Message Body")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_bulk_email))
    app.run_polling()
