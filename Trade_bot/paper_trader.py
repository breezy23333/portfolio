import json
from datetime import datetime

TRADES_FILE = "paper_trades.json"
BALANCE = 1000  # starting paper balance in USD
POSITION = None  # {"symbol": "BTCUSDT", "price": 23450, "amount": 0.05}

def load_trades():
    try:
        with open(TRADES_FILE, "r") as file:
            return json.load(file)
    except:
        return []

def save_trades(trades):
    with open(TRADES_FILE, "w") as file:
        json.dump(trades, file, indent=2)

def execute_paper_trade(symbol, price, signal):
    global BALANCE, POSITION
    trades = load_trades()

    if signal == "BUY" and POSITION is None:
        amount = BALANCE / price
        POSITION = {"symbol": symbol, "price": price, "amount": amount}
        trades.append({
            "time": datetime.now().isoformat(),
            "action": "BUY",
            "symbol": symbol,
            "price": price,
            "amount": amount,
            "balance": BALANCE
        })
    
    elif signal == "SELL" and POSITION and POSITION["symbol"] == symbol:
        BALANCE = POSITION["amount"] * price
        trades.append({
            "time": datetime.now().isoformat(),
            "action": "SELL",
            "symbol": symbol,
            "price": price,
            "amount": POSITION["amount"],
            "balance": BALANCE,
            "profit": BALANCE - 1000
        })
        POSITION = None

    save_trades(trades)