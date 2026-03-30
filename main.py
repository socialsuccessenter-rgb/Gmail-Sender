import os, smtplib, time, threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

# --- কনফিগারেশন ---
GMAIL_USER = os.getenv("GMAIL_ADDRESS")
GMAIL_PASS = os.getenv("GMAIL_APP_PASS")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# হেলথ চেক (Render সচল রাখতে)
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Active")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthCheck).serve_forever()

# আমাজন ডিজাইন
def get_html_body(link):
    return f"""
    <div style="font-family: Arial; max-width: 500px; margin: auto; border: 1px solid #ddd; border-radius: 10px;">
        <div style="background: #232f3e; padding: 15px; text-align: center;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg" width="100">
        </div>
        <div style="padding: 20px; text-align: center;">
            <h2 style="color: #111;">Exclusive Reward!</h2>
            <p style="color: #444;">You've received a <b>$100 Gift Card</b> voucher.</p>
            <a href="{link}" style="background: #ff9900; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; margin: 15px 0;">Claim Now</a>
            <p style="font-size: 11px; color: #999;">Limited offer for loyal customers.</p>
        </div>
    </div>
    """

# জিমেইল দিয়ে মেইল পাঠানোর ফাংশন
def send_gmail(to_email, link):
    try:
        msg = MIMEMultipart()
        msg['From'] = f"Amazon Support <{GMAIL_USER}>"
        msg['To'] = to_email
        msg['Subject'] = "Your Exclusive Reward is Ready!"
        msg.attach(MIMEText(get_html_body(link), 'html'))

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, to_email, msg.as_string())
        server.quit()
        return True
    except:
        return False

# কমান্ড হ্যান্ডলার
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [['🚀 মেইল পাঠান', '📊 স্ট্যাটাস']]
    await update.message.reply_text("✅ <b>জিমেইল মোড অ্যাক্টিভ!</b>", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode=ParseMode.HTML)

async def send_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("❌ লিঙ্ক দেননি!")
    link = context.args[0]
    msg = await update.message.reply_text("⏳ পাঠানো হচ্ছে...")
    
    with open('emails.txt', 'r') as f:
        emails = [line.strip() for line in f if "@" in line]

    s, f_count = 0, 0
    for e in emails:
        if send_gmail(e, link): s += 1
        else: f_count += 1
        time.sleep(5) # জিমেইল সেফটির জন্য ৫ সেকেন্ড গ্যাপ দিন

    await msg.edit_text(f"🏁 কাজ শেষ!\n✅ সফল: {s}\n❌ ব্যর্থ: {f_count}")

if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_cmd))
    app.run_polling()
