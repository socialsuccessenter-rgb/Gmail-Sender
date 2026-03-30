import telebot
import requests
import time
import os

# আপনার কনফিগারেশন
API_KEY = "আপনার_BREVO_API_KEY" # এখানে আপনার Brevo API Key বসান
BOT_TOKEN = "8673280780:AAEztVSGb42InjkD29lXSS3nUGqsTtgCWqE" # আপনার নতুন টোকেন সেট করে দিয়েছি
SENDER_EMAIL = "আপনার_ভেরিফাইড_ইমেইল" # Brevo-তে যে ইমেইল ভেরিফাই করেছেন
SENDER_NAME = "Amazon Rewards"

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 স্বাগতম Md Alamin ভাই!\n\n"
        "✅ আপনার ইমেইল সিস্টেম এখন প্রস্তুত।\n"
        "📩 মেইল পাঠাতে নিচের ফরম্যাটে মেসেজ দিন:\n"
        "`/send https://your-link.com`"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['send'])
def start_mailing(message):
    try:
        # লিঙ্ক এক্সট্রাক্ট করা
        target_link = message.text.split()[1]
    except IndexError:
        bot.reply_to(message, "❌ ভুল হয়েছে! এভাবে দিন: `/send https://link.com`", parse_mode="Markdown")
        return

    # ইমেইল ফাইল চেক করা
    if not os.path.exists('emails.txt'):
        bot.reply_to(message, "❌ `emails.txt` ফাইলটি পাওয়া যায়নি!")
        return

    with open('emails.txt', 'r') as f:
        emails = [line.strip() for line in f if line.strip()]

    total = len(emails)
    if total == 0:
        bot.reply_to(message, "❌ `emails.txt` ফাইলে কোনো ইমেইল নেই!")
        return

    sent = 0
    failed = 0
    
    status_msg = bot.send_message(message.chat.id, f"⏳ কাজ শুরু হচ্ছে...\n📊 মোট ইমেইল: {total}")

    for email in emails:
        url = "https://api.brevo.com/v3/smtp/email"
        payload = {
            "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
            "to": [{"email": email}],
            "subject": "Congratulations! Your Amazon Gift Card is Ready",
            "htmlContent": f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 10px; text-align: center;">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg" width="120" style="margin-bottom: 20px;">
                    <h2 style="color: #232f3e;">Exclusive Reward Just For You!</h2>
                    <p style="font-size: 16px; color: #555;">You have been selected to receive a special Amazon Gift Card.</p>
                    <div style="margin: 30px 0;">
                        <a href="{target_link}" style="background-color: #ff9900; color: white; padding: 15px 25px; text-decoration: none; font-weight: bold; border-radius: 5px; font-size: 18px;">Claim Your Reward Now</a>
                    </div>
                    <p style="font-size: 12px; color: #999;">*Limited time offer. Terms and conditions apply.</p>
                </div>
            </body>
            </html>
            """
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": API_KEY
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code in [200, 201]:
                sent += 1
            else:
                failed += 1
        except:
            failed += 1
        
        # প্রতি ৩টি মেইল পর পর টেলিগ্রামে আপডেট দিবে
        if (sent + failed) % 3 == 0 or (sent + failed) == total:
            try:
                bot.edit_message_text(
                    f"🚀 মেইল পাঠানো হচ্ছে...\n\n✅ সফল: {sent}\n❌ ফেল: {failed}\n⏳ বাকি: {total - (sent + failed)}",
                    message.chat.id,
                    status_msg.message_id
                )
            except:
                pass
        
        time.sleep(2.5) # সেফটির জন্য ২.৫ সেকেন্ড বিরতি

    bot.send_message(message.chat.id, f"🏁 কাজ শেষ ভাই!\n\n✅ মোট সফল: {sent}\n❌ মোট ফেল: {failed}\n📊 মোট পাঠানো হয়েছে: {total}")

bot.polling()
