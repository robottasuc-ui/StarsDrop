import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import redis
import json

app = Flask(__name__)
# Разрешаем CORS для связи фронта с бэком
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- НАСТРОЙКИ ---
REDIS_URL = "redis://default:9x1pwcq9Vp94gWovLw1qMQQZ5euiZy5w@redis-13357.crce220.us-east-1-4.ec2.cloud.redislabs.com:13357"
CRYPTO_PAY_TOKEN = '519389:AAnFdMg1D8ywsfVEd0aA02B8872Zzz61ATO'
BOT_TOKEN = '8451029637:AAHF6jJdQ98QhYRRsJxH_wuktMeE5QctT-I'
BASE_API_URL = "https://pay.cryptobots.run/api"

# Подключение к Redis
try:
    r_db = redis.from_url(REDIS_URL, decode_responses=True)
    r_db.ping()
    db_connected = True
except Exception as e:
    print(f"Redis Error: {e}")
    r_db = None
    db_connected = False

# --- ОБЩИЕ МЕТОДЫ ---
@app.route('/api/get_balance/<user_id>', methods=['GET'])
def get_balance(user_id):
    if not r_db:
        return jsonify({"balance": 0.0, "stars": 0, "db": "offline"}), 200
    try:
        data = r_db.get(f"user:{user_id}")
        user_data = json.loads(data) if data else {"balance": 0.0, "stars": 0}
        return jsonify(user_data), 200
    except Exception as e:
        return jsonify({"balance": 0.0, "stars": 0, "error": str(e)}), 200

# --- ЛОГИКА CRYPTO BOT (TON) ---
@app.route('/api/create_pay', methods=['POST'])
def create_pay():
    data = request.json
    uid = str(data.get('user_id'))
    amount = data.get('amount')
    
    payload = {
        "asset": "TON",
        "amount": str(amount),
        "payload": uid,
        "description": "Пополнение TON в StarsDrop",
        "allow_comments": False
    }
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}
    
    try:
        r = requests.post(f"{BASE_API_URL}/createInvoice", json=payload, headers=headers).json()
        if r.get('ok'):
            return jsonify(r['result']), 200
        return jsonify({"error": "crypto_bot_err"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/crypto-webhook', methods=['POST', 'GET'])
def crypto_webhook():
    if request.method == 'GET':
        return "Crypto Webhook is active!", 200
    data = request.json
    if data and data.get('status') == 'paid':
        user_id = data.get('payload')
        amount = float(data.get('amount'))
        if r_db and user_id:
            raw_data = r_db.get(f"user:{user_id}")
            user_data = json.loads(raw_data) if raw_data else {"balance": 0.0, "stars": 0}
            user_data['balance'] = round(user_data.get('balance', 0.0) + amount, 2)
            r_db.set(f"user:{user_id}", json.dumps(user_data))
    return "OK", 200

# --- ЛОГИКА TELEGRAM STARS ---
@app.route('/api/create_stars_pay', methods=['POST'])
def create_stars_pay():
    data = request.json
    uid = str(data.get('user_id'))
    amount = int(data.get('amount'))
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/createInvoiceLink"
    payload = {
        "title": "Пополнение звёзд",
        "description": f"Покупка {amount} звёзд для StarsDrop",
        "payload": uid,
        "currency": "XTR",
        "prices": [{"label": "Stars", "amount": amount}]
    }
    
    try:
        r = requests.post(url, json=payload).json()
        if r.get('ok'):
            return jsonify({"pay_url": r['result']}), 200
        return jsonify({"error": "stars_err", "details": r}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- СЛУЖЕБНОЕ ---
@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "db": db_connected}), 200

if __name__ == '__main__':
    app.run(port=5000)
