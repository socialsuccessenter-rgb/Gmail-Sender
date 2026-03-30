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
SENDER_NAME = "Amazon Rewards Program"

EMAIL_FILE = 'emails.txt'

# --- Health Check Server ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Active")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthCheck).serve_forever()

# --- ইমেইল ডিজাইন (একদম প্রফেশনাল) ---
def send_via_brevo(to_email, ad_link):
    url = "https://api.brevo.com/v3/smtp/email"
    subject = "🎁 Notification: Your Amazon Customer Appreciation Reward is Ready"
    
    html_content = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f6f9fc; padding: 40px 0; margin: 0;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <tr>
                <td style="background-color: #232f3e; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; letter-spacing: 1px;">AMAZON REWARDS</h1>
                </td>
            </tr>
            <tr>
                <td style="padding: 40px 30px;">
                    <h2 style="color: #333333; font-size: 22px; margin-bottom: 20px;">Congratulations! Your Reward is Waiting</h2>
                    <p style="font-size: 16px; color: #555555; line-height: 24px;">
                        Hello, <br><br>
                        We are excited to inform you that as a part of our <b>2026 Customer Appreciation Loyalty Program</b>, you have been selected to receive a promotional gift card. We value your presence in our community and this is our way of saying thank you.
                    </p>
                    <p style="font-size: 16px; color: #555555; line-height: 24px;">
                        To secure your reward, please verify your account and claim your gift code using the secure link provided below. This offer is exclusive to your email address and is valid for a limited time only.
                    </p>
                    
                    <table align="center" border="0" cellpadding="0" cellspacing="0" style="margin: 35px 0;">
                        <tr>
                            <td align="center" style="border-radius: 4px;" bgcolor="#ff9900">
                                <a href="{ad_link.strip()}" style="font-size: 18px; font-weight: bold; color: #111111; text-decoration: none; padding: 18px 40px; border: 1px solid #a88734; display: inline-block; border-radius: 4px;">
                                    CLAIM YOUR $500 GIFT CARD NOW
                                </a>
                            </td>
                        </tr>
                    </table>
                    
                    <p style="font-size: 14px; color: #888888; font-style: italic;">
                        *Disclaimer: This is a promotional offer. No purchase is necessary. You must claim your reward within 24 hours of receiving this email to ensure its validity.
                    </p>
                </td>
            </tr>
            <tr>
                <td style="background-color: #f1f3f5; padding: 25px; text-align: center; border-top: 1px solid #eeeeee;">
                    <p style="font-size: 12px; color: #999999; margin: 0;">
                        © 2026 Amazon Promotional Distribution Center. <br>
                        1200 12th Ave S, Seattle, WA 98144, USA. <br>
                        You received this email because you are a part of our rewards network.
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

# --- টেলিগ্রাম হ্যান্ডলারস ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = ReplyKeyboardMarkup([['🚀 অটো মেইল পাঠান', '📊 ড্যাশবোর্ড']], resize_keyboard=True)
    await update.message.reply_text("💎 <b>Amazon Official Mailer প্রস্তুত!</b>", reply_markup=key, parse_mode=ParseMode.HTML)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == '🚀 অটো মেইল পাঠান':
        await update.message.reply_text("🔗 লিঙ্ক দিন: <code>/send https://your-link.com</code>", parse_mode=ParseMode.HTML)
    elif text.startswith('/send '):
        link = text.split('/send ')[1].strip()
        msg = await update.message.reply_text("⏳ প্রফেশনাল মেইল পাঠানো হচ্ছে...")
        try:
            with open(EMAIL_FILE, 'r') as f:
                emails = [line.strip() for line in f.readlines() if "@" in line]
            success = 0
            for email in emails:
                if send_via_brevo(email, link) == 201: success += 1
                time.sleep(1)
            await msg.edit_text(f"✅ সফল! {success} টি প্রফেশনাল মেইল পাঠানো হয়েছে।")
        except Exception as e: await msg.edit_text(f"Error: {e}")

if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_messages))
    app.run_polling()
