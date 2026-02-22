import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_discord_alert(webhook_url, message):
    data = {"content": message}
    try:
        response = requests.post(webhook_url, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Discord alert failed: {e}")
        
EMAIL_ADDRESS = "luvomaphela0@gmail.com"
EMAIL_PASSWORD = "brlq lugb ikyh zcxa"
TO_EMAIL = "luvomaphela0@gmail.com"  # can be same as sender

def send_email_alert(subject, message):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = TO_EMAIL
        msg["Subject"] = subject

        msg.attach(MIMEText(message, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)

        print("✅ Email sent successfully.")
    except Exception as e:
        print("❌ Failed to send email:", e)
        
