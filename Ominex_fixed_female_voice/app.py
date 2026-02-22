# app.py
import os
from flask import Flask, request, jsonify, render_template
from flask.typing import ResponseReturnValue
from flask_cors import CORS


from core.brain import think

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

app = Flask(__name__)
app.config.update(DEBUG=True, PROPAGATE_EXCEPTIONS=True)
CORS(app)

# optional scheduler (kept)
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from core.learner import learn_tick
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(lambda: learn_tick(max_per_topic=2), "interval", minutes=60, id="ominex_learn")
    sched.start()
except Exception as e:
    print("Scheduler not started (optional):", e)

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/api/ping")
def api_ping():
    return jsonify({"ok": True})

@app.get("/ping")
def ping():
    return "ok", 200

@app.post("/api/chat")
def api_chat():
    data = request.get_json(force=True) or {}
    user_msg = (data.get("message") or data.get("text") or "").strip()
    user_mood = data.get("mood")

    if not user_msg:
        return jsonify({"reply": "Say something.", "mood": "Neutral"}), 400

    result = think(user_msg, user_mood=user_mood)

    return jsonify({
        "reply": result.get("reply"),
        "mood": result.get("mood"),
        "intent": result.get("intent"),
        "tts": result.get("tts"),
        "memory_used": result.get("memory_used", 0)
    }), 200

@app.route("/api/trade/alerts/check")
def check_alerts():
    return {"status": "ok", "alerts": []}

@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.post("/api/demo")
def api_demo():
    data = request.get_json(force=True) or {}
    user_msg = (data.get("message") or "").strip()

    if not user_msg:
        return jsonify({"reply": "Say something.", "mood": "Neutral"}), 400

    # Basic demo restriction
    if any(w in user_msg.lower() for w in ["trade", "delete", "alert", "learn", "backtest"]):
        return jsonify({
            "reply": "This feature is disabled in demo mode.",
            "mood": "Neutral"
        })

    result = think(user_msg)

    return jsonify({
        "reply": result.get("reply"),
        "mood": result.get("mood")
    }), 200


# Optional alias if frontend calls /chat
@app.post("/chat")
def chat_alias() -> ResponseReturnValue:
    return api_chat()

@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
