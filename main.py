import os, requests, logging, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode 

# লগিং সেটআপ
logging.basicConfig(level=logging.INFO)

# --- কনফিগারেশন (Environment Variable থেকে নেওয়া) ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = "Amazon Support"

# Render সচল রাখার জন্য হেলথ চেক
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Bot is Active")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthCheck).serve_forever()

# স্টার্ট কমান্ড
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    kb = [['🚀 ইমেইল পাঠান', '📊 স্ট্যাটাস চেক'], ['⚙️ সেটিংস', '❓ সহায়তা']]
    await update.message.reply_text(
        f"💎 <b>স্বাগতম {user} ভাই!</b>\n\nআপনার আমাজন রিওয়ার্ড বট এখন প্রস্তুত।",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )

# ইমেইল ডিজাইন ফাংশন (Amazon Style)
def get_amazon_template(target_link):
    return f"""
    <div style="font-family: 'Amazon Ember',Arial,sans-serif; background-color: #f3f3f3; padding: 30px 0;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <div style="background-color: #232f3e; padding: 20px; text-align: center;">
                <img src="https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg" width="120" alt="Amazon">
            </div>
            <div style="padding: 40px 30px;">
                <h1 style="color: #111; font-size: 26px; font-weight: bold; margin-bottom: 20px;">Congratulations!</h1>
                <p style="font-size: 18px; color: #333; line-height: 1.6;">
                    Hello customer, you have been selected to receive an exclusive <b>$100 Amazon Gift Card</b> as part of our 2026 loyalty rewards program.
                </p>
                <p style="font-size: 16px; color: #555; margin-bottom: 30px;">
                    This offer is valid for a limited time only. Please click the button below to claim your reward instantly.
                </p>
                <div style="text-align: center; margin-bottom: 30px;">
                    <a href="{target_link}" style="background-color: #ff9900; color: #ffffff; padding: 18px 35px; font-size: 20px; font-weight: bold; text-decoration: none; border-radius: 5px; display: inline-block;">Claim Your Reward Now</a>
                </div>
                <p style="font-size: 13px; color: #888; border-top: 1px solid #eee; padding-top: 20px;">
                    If you did not expect this email, please ignore it. Thank you for being with Amazon.
                </p>
            </div>
            <div style="background-color: #f3f3f3; padding: 20px; text-align: center; font-size: 12px; color: #777;">
                © 2026 Amazon.com, Inc. or its affiliates. All rights reserved.
            </div>
        </div>
    </div>
    """

def send_via_brevo(to_email, link):
    url = "https://api.brevo.com/v3/smtp/email"
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": "Action Required: Your Amazon Reward is Ready to Claim!",
        "htmlContent": get_amazon_template(link)
    }
    headers = {"accept": "application/json", "content-type": "application/json", "api-key": BREVO_API_KEY}
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code

# স্ট্যাটাস এবং সেটিংস হ্যান্ডলার
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == '🚀 ইমেইল পাঠান':
        await update.message.reply_text("📝 <b>নির্দেশনা:</b>\nমেইল পাঠাতে শুধু লিঙ্কটি দিন এভাবে:\n<code>/send https://your-link.com</code>", parse_mode=ParseMode.HTML)
    elif text == '📊 স্ট্যাটাস চেক':
        # এখানে রিয়েল স্ট্যাটাস দেখাবে
        emails_count = 0
        if os.path.exists('emails.txt'):
            with open('emails.txt', 'r') as f:
                emails_count = len([l for l in f if "@" in l])
        
        status_text = (
            f"🟢 <b>সার্ভার স্ট্যাটাস:</b> অনলাইন\n"
            f"🔑 <b>API Key:</b> {'সেট করা আছে' if BREVO_API_KEY else 'পাওয়া যায়নি'}\n"
            f"📧 <b>মোট ইমেইল লিস্ট:</b> {emails_count} টি\n"
            f"📨 <b>প্রেরক:</b> {SENDER_EMAIL}"
        )
        await update.message.reply_text(status_text, parse_mode=ParseMode.HTML)
    elif text == '⚙️ সেটিংস':
        await update.message.reply_text(f"🛠 <b>কনফিগারেশন:</b>\n📧 প্রেরক: {SENDER_EMAIL}\n👤 নাম: {SENDER_NAME}", parse_mode=ParseMode.HTML)
    elif text == '❓ সহায়তা':
        await update.message.reply_text("কোনো সমস্যা হলে API Key এবং Sender Email চেক করুন।")

# /send কমান্ড হ্যান্ডলার
async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("❌ লিঙ্ক দেননি! নিয়ম: <code>/send https://link.com</code>", parse_mode=ParseMode.HTML)
        return

    target_link = context.args[0]
    msg = await update.message.reply_text("⏳ <b>আমাজন ইমেইল ক্যাম্পেইন শুরু হচ্ছে...</b>", parse_mode=ParseMode.HTML)
    
    if not os.path.exists('emails.txt'):
        await msg.edit_text("❌ <b>emails.txt</b> ফাইলটি নেই!")
        return

    with open('emails.txt', 'r') as f:
        emails = [line.strip() for line in f if "@" in line]

    success, fail = 0, 0
    for email in emails:
        code = send_via_brevo(email, target_link)
        if code in [200, 201]: success += 1
        else: fail += 1
        time.sleep(2.5) # ইনবক্স নিশ্চিত করতে ২.৫ সেকেন্ড গ্যাপ

    await msg.edit_text(f"✅ <b>মিশন কমপ্লিট!</b>\n📊 সফল: {success} টি\n❌ ব্যর্থ: {fail} টি", parse_mode=ParseMode.HTML)

# মেইন রানার
if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.run_polling()
