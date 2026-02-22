# core/tradebot.py
# TradeBot v1 — plan + paper ledger + alerts + quick backtest
import os, json, math, time, datetime as dt
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np

try:
    import yfinance as yf
except Exception as e:
    raise RuntimeError("Please: pip install yfinance pandas numpy") from e

# ---------- storage ----------
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
LEDGER_PATH = os.path.join(DATA_DIR, "ledger.json")
ALERTS_PATH = os.path.join(DATA_DIR, "alerts.json")
os.makedirs(DATA_DIR, exist_ok=True)

def _read(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _write(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    os.replace(tmp, path)

# ---------- indicators ----------
def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    h, l, c = df['High'], df['Low'], df['Close']
    tr = pd.concat([(h - l), (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()

# ---------- data ----------
def fetch_ohlc(symbol: str, interval: str = "1d", min_bars: int = 210) -> pd.DataFrame:
    tried = []
    for period in ["6mo", "2y", "5y", "max"]:
        tried.append(period)
        data = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=False)
        if isinstance(data, pd.DataFrame) and not data.empty and "Close" in data.columns:
            df = data.dropna().copy()
            if len(df) >= min_bars:
                df["EMA20"]  = ema(df["Close"], 20)
                df["EMA50"]  = ema(df["Close"], 50)
                df["EMA200"] = ema(df["Close"], 200)
                df["ATR14"]  = atr(df, 14)
                return df
    if symbol.upper().endswith("JO") and ".JO" not in symbol.upper():
        raise ValueError(f"No data for '{symbol}'. JSE tickers need a dot: try '{symbol.replace('JO', '.JO')}'.")
    raise ValueError(f"No/insufficient data for '{symbol}'. Tried periods: {', '.join(tried)}.")

def price_last(symbol: str) -> float:
    d = yf.download(symbol, period="5d", interval="1d", progress=False, auto_adjust=False)
    if isinstance(d, pd.DataFrame) and not d.empty:
        return float(d["Close"].iloc[-1])
    raise ValueError(f"No recent price for {symbol}")

# ---------- plan ----------
@dataclass
class Plan:
    ok: bool
    symbol: str
    entry: float
    stop: float
    risk_rands: float
    units: float
    position_value: float
    r_multiple: float
    tp1: float
    trend: str
    message: str
    speak: str

def round_tick(price: float, tick: float = 0.01) -> float:
    return round(price / tick) * tick

def recent_swing_low(df: pd.DataFrame, lookback: int = 10) -> float:
    return float(df['Low'].iloc[-(lookback+1):-1].min())

def generate_plan(symbol: str, risk_rands: float = 10.0, stop_pct_hint: float | None = None) -> Plan:
    df = fetch_ohlc(symbol)
    if len(df) < 210:
        msg = f"{symbol}: still not enough history to form a plan."
        return Plan(False, symbol, 0, 0, risk_rands, 0, 0, 0, 0, "Insufficient data", msg, msg)

    last = df.iloc[-1]; prev = df.iloc[-2]
    last_close = float(last["Close"]); prev_close = float(prev["Close"])
    last_e20 = float(last["EMA20"]); last_e50 = float(last["EMA50"]); last_e200 = float(last["EMA200"])
    last_atr = float(last["ATR14"]); prior_high = float(prev["High"])

    uptrend   = (last_e50 > last_e200) and (last_close > last_e50)
    reclaim20 = (last_close > last_e20) and (prev_close < float(prev["EMA20"]))
    trend_text = "Uptrend" if uptrend else "Not uptrend"
    if not uptrend:
        msg = f"{symbol}: Not in a healthy uptrend (EMA50 ≤ EMA200). No long trade."
        return Plan(False, symbol, 0, 0, risk_rands, 0, 0, 0, 0, trend_text, msg, msg)

    entry = round_tick(prior_high * 1.001)
    swing_low = recent_swing_low(df, 10)
    atr_stop  = entry - last_atr
    raw_stop  = min(swing_low, atr_stop)
    if stop_pct_hint and stop_pct_hint > 0:
        hinted = entry * (1 - float(stop_pct_hint))
        raw_stop = min(raw_stop, hinted)
    if raw_stop >= entry:
        raw_stop = entry * 0.96

    stop = round_tick(raw_stop)
    stop_pct = (entry - stop) / entry
    if stop_pct < 0.02:
        stop = round_tick(entry * 0.98); stop_pct = 0.02

    position_value = risk_rands / stop_pct
    units = position_value / entry
    tp1 = entry + 2 * (entry - stop)

    lines = [
        f"Trade plan for {symbol}",
        f"- Trend: {trend_text}; Reclaim 20EMA: {'Yes' if reclaim20 else 'No'}",
        f"- Entry (breakout): {entry:.2f}",
        f"- Stop: {stop:.2f} ({stop_pct*100:.2f}% risk)",
        f"- Risk: R{risk_rands:.2f} → Position ≈ R{position_value:.2f} (units ≈ {units:.3f})",
        f"- Take profit 1 (+2R): {tp1:.2f}; trail below higher swing lows",
        f"- Rules: stop to breakeven at +1R; exit on stop/rule break; time-stop ~8 bars",
    ]
    speak = f"{symbol} plan: entry {entry:.2f}, stop {stop:.2f}, risk R{risk_rands:.0f}, size about R{position_value:.0f}, first target {tp1:.2f}."
    return Plan(True, symbol, entry, stop, risk_rands, units, position_value, 2.0, tp1,
                trend_text, "\n".join(lines), speak)

# ---------- paper ledger ----------
def ledger_load(): return _read(LEDGER_PATH, [])
def ledger_save(arr): _write(LEDGER_PATH, arr)

def paper_open(symbol: str, entry: float, stop: float, position_value: float, units: float) -> dict:
    arr = ledger_load()
    _id = (arr[-1]["id"] + 1) if arr else 1
    trade = {
        "id": _id, "symbol": symbol, "ts_open": int(time.time()),
        "entry": float(entry), "stop": float(stop), "value": float(position_value),
        "units": float(units), "exit": None, "ts_close": None, "R": None, "status": "OPEN"
    }
    arr.append(trade); ledger_save(arr)
    return trade

def paper_close(trade_id: int, exit_price: float) -> dict:
    arr = ledger_load()
    for t in arr:
        if t["id"] == int(trade_id) and t["status"] == "OPEN":
            r = (float(exit_price) - t["entry"]) / (t["entry"] - t["stop"])
            t["exit"] = float(exit_price); t["ts_close"] = int(time.time()); t["R"] = float(r); t["status"] = "CLOSED"
            ledger_save(arr); return t
    raise ValueError("Trade not found or already closed")

def ledger_stats() -> dict:
    arr = ledger_load()
    closed = [t for t in arr if t["status"] == "CLOSED" and t["R"] is not None]
    wins = [t for t in closed if t["R"] > 0]
    total_R = round(sum(t["R"] for t in closed), 3) if closed else 0.0
    winrate = round(100.0 * len(wins) / len(closed), 1) if closed else 0.0
    avgR = round(total_R / len(closed), 3) if closed else 0.0
    return {"open": [t for t in arr if t["status"] == "OPEN"],
            "closed": closed, "total_R": total_R, "winrate": winrate, "avgR": avgR, "count": len(closed)}

# ---------- alerts ----------
def alerts_load(): return _read(ALERTS_PATH, [])
def alerts_save(arr): _write(ALERTS_PATH, arr)

def alert_add(symbol: str, level: float, direction: str = "above") -> dict:
    arr = alerts_load()
    _id = (arr[-1]["id"] + 1) if arr else 1
    al = {"id": _id, "symbol": symbol, "level": float(level), "direction": direction.lower(), "triggered": False, "ts": int(time.time())}
    arr.append(al); alerts_save(arr); return al

def alerts_list(): return alerts_load()

def alerts_check() -> list[dict]:
    arr = alerts_load(); triggered = []
    for al in arr:
        if al.get("triggered"): continue
        try:
            p = price_last(al["symbol"])
            if (al["direction"] == "above" and p >= al["level"]) or (al["direction"] == "below" and p <= al["level"]):
                al["triggered"] = True; al["price"] = float(p); al["ts_trigger"] = int(time.time()); triggered.append(al)
        except Exception as e:
            al["error"] = str(e)
    alerts_save(arr)
    return triggered

# ---------- quick backtest (rule-of-thumb) ----------
@dataclass
class BacktestResult:
    symbol: str
    trades: int
    wins: int
    losses: int
    total_R: float
    avg_R: float
    winrate: float
    expectancy_R: float

def backtest(symbol: str, years: int = 3, use_atr_stop: bool = True, bars_hold: int = 8) -> BacktestResult:
    df = fetch_ohlc(symbol, min_bars=210)
    # restrict to last N years
    cutoff = df.index.max() - pd.Timedelta(days=365*years)
    df = df[df.index >= cutoff].copy()
    if len(df) < 210:  # still too small
        raise ValueError("Not enough data for backtest window")

    Rs = []  # R results
    i = 200
    while i < len(df) - 1:
        prev = df.iloc[i-1]; cur = df.iloc[i]
        uptrend   = (float(cur["EMA50"]) > float(cur["EMA200"])) and (float(cur["Close"]) > float(cur["EMA50"]))
        reclaim20 = float(cur["Close"]) > float(cur["EMA20"]) and float(prev["Close"]) < float(prev["EMA20"])
        if uptrend and reclaim20:
            entry = round_tick(float(prev["High"]) * 1.001)
            swing_low = float(df["Low"].iloc[max(0, i-10):i].min())
            stop = min(swing_low, entry - float(cur["ATR14"])) if use_atr_stop else swing_low
            if stop >= entry: stop = entry * 0.96
            R = entry - stop
            # forward simulation up to bars_hold bars
            hit = None
            j = i+1
            while j < min(i+1+bars_hold, len(df)):
                hi = float(df["High"].iloc[j]); lo = float(df["Low"].iloc[j]); cl = float(df["Close"].iloc[j])
                if lo <= stop:  # stopped
                    Rs.append(-1.0); hit = True; break
                if hi >= entry + 2*R:  # +2R TP
                    Rs.append(+2.0); hit = True; break
                j += 1
            if not hit:
                # time stop at last close
                cl = float(df["Close"].iloc[min(i+bars_hold, len(df)-1)])
                Rs.append((cl - entry)/R)
            i = j  # skip ahead after a trade
        else:
            i += 1

    trades = len(Rs); wins = sum(1 for r in Rs if r > 0); losses = sum(1 for r in Rs if r <= 0)
    total_R = round(sum(Rs), 3) if Rs else 0.0
    avg_R   = round(total_R / trades, 3) if trades else 0.0
    winrate = round(100.0 * wins / trades, 1) if trades else 0.0
    expectancy = round((winrate/100.0) * (sum(r for r in Rs if r>0)/max(1,wins)) - ((1 - winrate/100.0) * (abs(sum(r for r in Rs if r<=0))/max(1,losses))), 3) if trades else 0.0
    return BacktestResult(symbol, trades, wins, losses, total_R, avg_R, winrate, expectancy)