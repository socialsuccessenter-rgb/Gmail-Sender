import os, requests, logging, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, ReplyKeyboardMarkup, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(level=logging.INFO)

# --- কনফিগারেশন ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# সরাসরি আপনার দেওয়া API Key টি বসানো হলো
BREVO_API_KEY = "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"
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = "Premium Mailer"

# --- Render সার্ভার সচল রাখা ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Server Active")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthCheck).serve_forever()

# --- সুন্দর মেনু ও স্টার্ট মেসেজ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    kb = [['🚀 ইমেইল পাঠান', '📊 স্ট্যাটাস চেক'], ['⚙️ সেটিংস', '❓ সহায়তা']]
    await update.message.reply_text(
        f"💎 <b>হ্যালো {user}!</b>\n\nএটি আপনার আল্টিমেট ইমেইল মার্কেটিং ড্যাশবোর্ড।",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )

# --- Brevo API logic ---
def send_via_brevo(to_email, subject, body):
    url = "https://api.brevo.com/v3/smtp/email"
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": f"<html><body>{body}</body></html>"
    }
    headers = {"accept": "application/json", "content-type": "application/json", "api-key": BREVO_API_KEY}
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code, response.text

# --- মেনু ও কমান্ড হ্যান্ডলিং ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == '🚀 ইমেইল পাঠান':
        await update.message.reply_text("📝 <b>নির্দেশনা:</b>\nইমেইল পাঠাতে লিখুন:\n<code>/send Subject | Message</code>", parse_mode=ParseMode.HTML)
    elif text == '📊 স্ট্যাটাস চেক':
        await update.message.reply_text("🟢 <b>সার্ভার:</b> সচল\n📡 <b>মেথড:</b> Brevo High-Speed API", parse_mode=ParseMode.HTML)
    elif text == '⚙️ সেটিংস':
        await update.message.reply_text(f"🛠 <b>কনফিগারেশন:</b>\n📧 প্রেরক: {SENDER_EMAIL}\n👤 নাম: {SENDER_NAME}", parse_mode=ParseMode.HTML)

async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "|" not in update.message.text:
        await update.message.reply_text("❌ <b>ভুল ফরম্যাট!</b>")
        return

    msg = await update.message.reply_text("🔍 <b>ইমেইল প্রসেস হচ্ছে...</b>", parse_mode=ParseMode.HTML)
    try:
        content = update.message.text.split('/send ')[1]
        subject, body = content.split('|')
        
        with open('emails.txt', 'r') as f:
            emails = [line.strip() for line in f.readlines() if "@" in line]

        if not emails:
            await msg.edit_text("⚠️ <b>emails.txt</b> ফাইলে কোনো ইমেইল নেই!")
            return

        success, fail, last_error = 0, 0, ""
        for email in emails:
            code, resp = send_via_brevo(email.strip(), subject.strip(), body.strip())
            if code == 201: success += 1
            else:
                fail += 1
                last_error = f"Code {code}: {resp}"
            time.sleep(0.3)

        result = f"✅ <b>মিশন কমপ্লিট!</b>\n📊 সফল: {success}\n❌ ব্যর্থ: {fail}"
        if fail > 0:
            result += f"\n\n⚠️ <b>এরর ডিটেইলস:</b>\n<code>{last_error[:150]}</code>"
        
        await msg.edit_text(result, parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.edit_text(f"⚠️ <b>ক্রুটি:</b> {e}")

if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.run_polling()
