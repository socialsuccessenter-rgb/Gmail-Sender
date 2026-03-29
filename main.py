import os, requests, logging, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode 

logging.basicConfig(level=logging.INFO)

# --- কনফিগারেশন ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# আপনার নতুন API Key (নিশ্চিত করুন শুরুতে বা শেষে কোনো স্পেস নেই)
BREVO_API_KEY = "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"

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = "Premium Mailer"

# --- Render সার্ভার সচল রাখা ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Bot is Active")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthCheck).serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    kb = [['🚀 ইমেইল পাঠান', '📊 স্ট্যাটাস চেক'], ['⚙️ সেটিংস', '❓ সহায়তা']]
    await update.message.reply_text(
        f"💎 <b>হ্যালো {user}!</b>\n\nবট এখন আপনার লেটেস্ট API Key ব্যবহার করছে। কাজ না করলে নিচের 'সহায়তা' বাটনটি দেখুন।",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )

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

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == '🚀 ইমেইল পাঠান':
        await update.message.reply_text("📝 নিয়ম: <code>/send Subject | Message</code>", parse_mode=ParseMode.HTML)
    elif text == '📊 স্ট্যাটাস চেক':
        await update.message.reply_text("🟢 সার্ভার: অনলাইন\n📡 মেথড: Brevo High-Speed API", parse_mode=ParseMode.HTML)
    elif text == '⚙️ সেটিংস':
        await update.message.reply_text(f"🛠 প্রেরক: {SENDER_EMAIL}", parse_mode=ParseMode.HTML)
    elif text == '❓ সহায়তা':
        await update.message.reply_text("১. আপনার Brevo ইমেইলটি কি ভেরিফাইড?\n২. emails.txt ফাইলে কি সঠিক ইমেইল আছে?\n৩. Render-এ কি 'Clear Cache' করে ডিপ্লয় করেছেন?")

async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "|" not in update.message.text:
        await update.message.reply_text("❌ ভুল ফরম্যাট!")
        return
    msg = await update.message.reply_text("⏳ ইমেইল প্রসেসিং...")
    try:
        content = update.message.text.split('/send ')[1]
        subject, body = content.split('|')
        with open('emails.txt', 'r') as f:
            emails = [line.strip() for line in f.readlines() if "@" in line]
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
            result += f"\n\n⚠️ এরর: <code>{last_error[:100]}</code>"
        await msg.edit_text(result, parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.edit_text(f"Error: {e}")

if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.run_polling()
