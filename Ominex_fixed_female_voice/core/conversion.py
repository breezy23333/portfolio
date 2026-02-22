# core/conversion.py
import re, requests

def temp_convert(val: float, src: str, dst: str) -> float:
    s = src.lower()[0]; d = dst.lower()[0]
    if s == d: return val
    if s == 'c' and d == 'f': return val*9/5 + 32
    if s == 'f' and d == 'c': return (val-32)*5/9
    raise ValueError("unknown temperature units")

def length_convert(val: float, src: str, dst: str) -> float:
    units = {
        "m": 1.0, "meter":1.0, "meters":1.0,
        "km": 1000.0,
        "cm": 0.01,
        "in": 0.0254, "inch":0.0254, "inches":0.0254,
        "ft": 0.3048, "foot":0.3048, "feet":0.3048,
        "mi": 1609.344, "mile":1609.344, "miles":1609.344
    }
    s = units.get(src.lower()); d = units.get(dst.lower())
    if s is None or d is None: raise ValueError("unknown length units")
    return val * s / d

def weight_convert(val: float, src: str, dst: str) -> float:
    units = {
        "g": 1.0, "gram":1.0, "grams":1.0,
        "kg": 1000.0, "kilogram":1000.0, "kilograms":1000.0,
        "lb": 453.59237, "lbs":453.59237, "pound":453.59237, "pounds":453.59237,
        "oz": 28.349523125, "ounce":28.349523125, "ounces":28.349523125
    }
    s = units.get(src.lower()); d = units.get(dst.lower())
    if s is None or d is None: raise ValueError("unknown weight units")
    return val * s / d

_currency_rx = re.compile(r"^[A-Za-z]{3}$")
def currency_convert(val: float, src: str, dst: str) -> float:
    if not (_currency_rx.match(src) and _currency_rx.match(dst)):
        raise ValueError("currency must be 3-letter code")
    r = requests.get(
        "https://api.exchangerate.host/convert",
        params={"from": src.upper(), "to": dst.upper(), "amount": val},
        timeout=10
    ).json()
    if not r or "result" not in r: raise ValueError("rate unavailable")
    return float(r["result"])