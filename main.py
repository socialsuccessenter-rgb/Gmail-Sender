import telebot
import requests
import time
import os

# আপনার তথ্যগুলো এখানে দিন
API_KEY = "আপনার_BREVO_API_KEY"
BOT_TOKEN = "আপনার_টেলিগ্রাম_বট_টোকেন"
SENDER_EMAIL = "আপনার_ভেরিফাইড_ইমেইল"
SENDER_NAME = "Amazon Rewards"

bot = telebot.TeleBot(8673280780:AAEztVSGb42InjkD29lXSS3nUGqsTtgCWqE)

@bot.message_id_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "✅ বট অ্যাক্টিভ আছে!\nমেইল পাঠাতে /send লিখে আপনার লিঙ্কটি দিন।\nউদাহরণ: /send https://google.com")

@bot.message_handler(commands=['send'])
def start_mailing(message):
    try:
        target_link = message.text.split()[1]
    except IndexError:
        bot.reply_to(message, "❌ লিঙ্ক দেননি! সঠিক নিয়ম: /send https://yourlink.com")
        return

    if not os.path.exists('emails.txt'):
        bot.reply_to(message, "❌ emails.txt ফাইলটি পাওয়া যায়নি!")
        return

    with open('emails.txt', 'r') as f:
        emails = [line.strip() for line in f if line.strip()]

    total = len(emails)
    sent = 0
    failed = 0
    
    status_msg = bot.send_message(message.chat.id, f"⏳ মেইল পাঠানো শুরু হচ্ছে...\nমোট ইমেইল: {total}")

    for email in emails:
        url = "https://api.brevo.com/v3/smtp/email"
        payload = {
            "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
            "to": [{"email": email}],
            "subject": "Exclusive Gift Card Waiting for You!",
            "htmlContent": f"""
            <div style='text-align:center; font-family:Arial;'>
                <img src='https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg' width='150'>
                <h2>Congratulations!</h2>
                <p>You have been selected for a special Amazon Gift Card.</p>
                <a href='{target_link}' style='background:#f0c14b; padding:10px 20px; color:black; text-decoration:none; border-radius:5px;'>Claim Your Reward Now</a>
            </div>
            """
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": API_KEY
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 201 or response.status_code == 200:
            sent += 1
        else:
            failed += 1
        
        # প্রতি ৫টি মেইল পর পর টেলিগ্রামে আপডেট দেবে
        if (sent + failed) % 5 == 0:
            bot.edit_message_text(
                f"🚀 মেইল পাঠানো হচ্ছে...\n✅ সফল: {sent}\n❌ ফেল: {failed}\n⏳ বাকি: {total - (sent + failed)}",
                message.chat.id,
                status_msg.message_id
            )
        
        time.sleep(2) # স্পিড বাড়িয়ে ২ সেকেন্ড করে দেওয়া হয়েছে

    bot.send_message(message.chat.id, f"🏁 কাজ শেষ!\n✅ মোট সফল: {sent}\n❌ মোট ফেল: {failed}")

bot.polling()
