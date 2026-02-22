import time
import random
from notifier_email import send_email_alert

# Initial Threshold Point (you can change this to your profit line)
THRESHOLD = 100.0

# Start with random initial moving average
moving_average = 100.0

# Last signal state to prevent repeated alerts
last_signal = None

def get_mock_price():
    # Simulate price movements randomly
    return random.uniform(-1, 1)

print("Trade Bot Monitoring Started...\n")

while True:
    # Simulate new moving average by adding random price changes
    moving_average += get_mock_price()

    print(f"Current Line: {moving_average:.2f} | Threshold: {THRESHOLD}")

    if moving_average > THRESHOLD and last_signal != 'BUY':
        print("⚠️ Signal: BUY")
        last_signal = 'BUY'
        send_email_alert("BUY Signal Triggered", f"The moving average is {moving_average:.2f}, which is above the threshold {THRESHOLD}.")

    elif moving_average < THRESHOLD and last_signal != 'SELL':
        print("⚠️ Signal: SELL")
        last_signal = 'SELL'
        send_email_alert("SELL Signal Triggered", f"The moving average is {moving_average:.2f}, which is below the threshold {THRESHOLD}.")

    # Check every 1 second
    time.sleep(1)