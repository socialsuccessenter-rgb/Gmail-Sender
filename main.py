import os, requests, logging, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode 

# লগিং সেটআপ
logging.basicConfig(level=logging.INFO)

# --- কনফিগারেশন (Environment থেকে সরাসরি ডাটা নেওয়া) ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = "Premium Mailer"

# Render সার্ভার সচল রাখার জন্য হেলথ চেক
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Bot is Active")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthCheck).serve_forever()

# স্টার্ট কমান্ড
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    kb = [[' ইমেইল পাঠান', '📊 স্ট্যাটাস চেক'], ['⚙️ সেটিংস', '❓ সহায়তা']]
    await update.message.reply_text(
        f"💎 <b>স্বাগতম {user}!</b>\n\nআপনার বট এখন Environment Variable থেকে API Key ব্যবহার করছে।",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )

# Brevo API এর মাধ্যমে ইমেইল পাঠানোর ফাংশন
def send_via_brevo(to_email, subject, body):
    url = "https://api.brevo.com/v3/smtp/email"
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": f"<html><body style='font-family: Arial;'>{body}</body></html>"
    }
    headers = {
        "accept": "application/json", 
        "content-type": "application/json", 
        "api-key": BREVO_API_KEY
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code, response.text

# টেক্সট মেসেজ হ্যান্ডলার
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == '🚀 ইমেইল পাঠান':
        await update.message.reply_text("📝 <b>নির্দেশনা:</b>\nইমেইল পাঠাতে নিচের নিয়মে লিখুন:\n<code>/send Subject | Message</code>", parse_mode=ParseMode.HTML)
    elif text == '📊 স্ট্যাটাস চেক':
        status = "✅ API Key সেট আছে" if BREVO_API_KEY else "❌ API Key পাওয়া যায়নি"
        await update.message.reply_text(f"🟢 <b>সার্ভার:</b> অনলাইন\n🔑 <b>স্ট্যাটাস:</b> {status}", parse_mode=ParseMode.HTML)
    elif text == '⚙️ সেটিংস':
        await update.message.reply_text(f"🛠 <b>কনফিগারেশন:</b>\n📧 প্রেরক: {SENDER_EMAIL}", parse_mode=ParseMode.HTML)
    elif text == '❓ সহায়তা':
        await update.message.reply_text("ইমেইল না গেলে চেক করুন:\n১. SENDER_EMAIL কি Brevo-তে ভেরিফাইড?\n২. emails.txt ফাইলে কি ইমেইল আছে?")

# /send কমান্ড হ্যান্ডলার
async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "|" not in update.message.text:
        await update.message.reply_text("❌ <b>ভুল ফরম্যাট!</b>\nসঠিক নিয়ম: <code>/send বিষয় | মেসেজ</code>", parse_mode=ParseMode.HTML)
        return

    msg = await update.message.reply_text("⏳ <b>প্রসেসিং...</b>", parse_mode=ParseMode.HTML)
    try:
        content = update.message.text.split('/send ')[1]
        subject, body = content.split('|')
        
        # emails.txt ফাইল চেক করা
        if not os.path.exists('emails.txt'):
             await msg.edit_text("❌ <b>emails.txt</b> ফাইলটি পাওয়া যায়নি!")
             return

        with open('emails.txt', 'r') as f:
            emails = [line.strip() for line in f.readlines() if "@" in line]

        if not emails:
             await msg.edit_text("❌ <b>emails.txt</b> ফাইলে কোনো ইমেইল নেই!")
             return

        success, fail, last_error = 0, 0, ""
        for email in emails:
            code, resp = send_via_brevo(email.strip(), subject.strip(), body.strip())
            if code == 201: success += 1
            else:
                fail += 1
                last_error = f"Code {code}: {resp}"
            time.sleep(0.3)

        result = f"✅ <b>মিশন কমপ্লিট!</b>\n📊 সফল: {success} টি\n❌ ব্যর্থ: {fail} টি"
        if fail > 0:
            result += f"\n\n⚠️ <b>এরর:</b> <code>{last_error[:120]}</code>"
        
        await msg.edit_text(result, parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.edit_text(f"⚠️ <b>ক্রুটি:</b> {str(e)}")

# মেইন ফাংশন
if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.run_polling()
