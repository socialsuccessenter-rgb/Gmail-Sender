import os, requests, logging, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

logging.basicConfig(level=logging.INFO)

# --- কনফিগারেশন ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = "The Rewards Team"

EMAIL_FILE = 'emails.txt'

# --- Health Check Server ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Active")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthCheck).serve_forever()

# --- ইমেইল ডিজাইন (আপনার টেক্সট দিয়ে সাজানো) ---
def send_via_brevo(to_email, ad_link):
    url = "https://api.brevo.com/v3/smtp/email"
    subject = "🎁 Exclusive: Your Amazon Reward is waiting!"
    
    html_content = f"""
    <html>
    <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f9f9f9; padding: 20px; margin: 0;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="background-color: #ffffff; border: 1px solid #eeeeee; border-radius: 8px;">
            <tr>
                <td style="padding: 40px 30px;">
                    <h1 style="color: #232f3e; font-size: 24px; margin-bottom: 20px;">Hi there,</h1>
                    
                    <p style="font-size: 16px; color: #444444; line-height: 26px;">
                        We have some exciting news! For a very limited time, we are offering our selected users a chance to grab an <b>Amazon Gift Card</b>. 
                    </p>
                    
                    <p style="font-size: 16px; color: #444444; line-height: 26px;">
                        Whether you want to buy the latest gadgets, books, or household essentials, this is your chance to get them for free! Don't miss out—thousands of people have already claimed theirs.
                    </p>

                    <div style="text-align: center; margin: 40px 0;">
                        <p style="font-size: 18px; font-weight: bold; color: #232f3e;">Claim your gift card here:</p>
                        <a href="{ad_link.strip()}" 
                           style="background-color: #FF9900; color: #111111; padding: 18px 45px; text-decoration: none; font-size: 18px; font-weight: bold; border-radius: 4px; display: inline-block; border: 1px solid #A88734;">
                           👉 CLAIM NOW
                        </a>
                    </div>

                    <p style="font-size: 16px; color: #444444; margin-top: 30px;">
                        Best regards,<br>
                        <strong>The Rewards Team</strong>
                    </p>
                </td>
            </tr>
            <tr>
                <td style="background-color: #f1f1f1; padding: 20px; text-align: center; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;">
                    <p style="font-size: 12px; color: #888888; margin: 0;">
                        You are receiving this email because you are a registered member of our rewards network. <br>
                        © 2026 Promotional Rewards Inc. All rights reserved.
                    </p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content
    }
    headers = {"accept": "application/json", "content-type": "application/json", "api-key": BREVO_API_KEY}
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code

# --- টেলিগ্রাম কমান্ডস ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = ReplyKeyboardMarkup([['🚀 অটো মেইল পাঠান', '📊 স্ট্যাটাস']], resize_keyboard=True)
    await update.message.reply_text("✅ <b>ইমেইল সিস্টেম আপডেট করা হয়েছে!</b>\nআপনার দেওয়া নতুন টেক্সট এখন সেট করা আছে।", reply_markup=key, parse_mode=ParseMode.HTML)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == '🚀 অটো মেইল পাঠান':
        await update.message.reply_text("🔗 আপনার ডিরেক্ট লিঙ্ক দিন:\n<code>/send https://your-link.com</code>", parse_mode=ParseMode.HTML)
    elif text.startswith('/send '):
        link = text.split('/send ')[1].strip()
        msg = await update.message.reply_text("⏳ নতুন ফরম্যাটে মেইল পাঠানো হচ্ছে...")
        try:
            with open(EMAIL_FILE, 'r') as f:
                emails = [line.strip() for line in f.readlines() if "@" in line]
            success = 0
            for email in emails:
                if send_via_brevo(email, link) == 201: success += 1
                time.sleep(1)
            await msg.edit_text(f"✅ সফল! {success} জনকে নতুন ফরম্যাটে মেইল পাঠানো হয়েছে।")
        except Exception as e: await msg.edit_text(f"Error: {e}")

if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_messages))
    app.run_polling()
