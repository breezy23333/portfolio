import time
import requests
from collections import deque
import smtplib
from email.mime.text import MIMEText

# CONFIG
SYMBOL = "BTCUSDT"
API_URL = f"https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL}"
MOVING_AVERAGE_PERIOD = 10

EMAIL_ADDRESS = 'luvomaphela0@gmail.com'
EMAIL_PASSWORD = 'oxzvlawwilmmzyf'
EMAIL_TO = 'luvomaphela0@gmail.com'

prices = deque(maxlen=MOVING_AVERAGE_PERIOD)
last_signal = None

def get_live_price():
    try:
        response = requests.get(API_URL)
        data = response.json()
        return float(data['price'])
    except Exception as e:
        print("Error fetching price:", e)
        return None

def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_TO

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Email sent: {subject}")
    except Exception as e:
        print("❌ Failed to send email:", e)

print(f"Monitoring {SYMBOL} with {MOVING_AVERAGE_PERIOD}-Period Moving Average...\n")

while True:
    price = get_live_price()
    if price is None:
        continue

    prices.append(price)
    sma = sum(prices) / len(prices)
    print(f"Current Price: {price:.2f} | Moving Average: {sma:.2f}")

    if len(prices) == MOVING_AVERAGE_PERIOD:
        if price > sma and last_signal != 'BUY':
            signal_msg = f"🟢 BUY Signal!\nPrice: {price:.2f}\nMoving Average: {sma:.2f}"
            print(signal_msg)
            send_email("BUY Signal", signal_msg)
            last_signal = 'BUY'
        elif price < sma and last_signal != 'SELL':
            signal_msg = f"🔴 SELL Signal!\nPrice: {price:.2f}\nMoving Average: {sma:.2f}"
            print(signal_msg)
            send_email("SELL Signal", signal_msg)
            last_signal = 'SELL'

    time.sleep(5)
