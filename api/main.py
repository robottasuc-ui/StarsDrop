import os
import json
import requests
import redis
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Разрешаем CORS, чтобы фронтенд мог достучаться до бэкенда
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- НАСТРОЙКИ (Всё в одном месте) ---
REDIS_URL = "redis://default:9x1pwcq9Vp94gWovLw1qMQQZ5euiZy5w@redis-13357.crce220.us-east-1-4.ec2.cloud.redislabs.com:13357"
CRYPTO_PAY_TOKEN = '519389:AAnFdMg1D8ywsfVEd0aA02B8872Zzz61ATO'
BOT_TOKEN = '8451029637:AAHF6jJdQ98QhYRRsJxH_wuktMeE5QctT-I'
# Используем официальный домен API CryptoBot
BASE_CRYPTO_URL = "https://pay.crypt.bot/api"

# Подключение к Redis
try:
    r_db = redis.from_url(REDIS_URL, decode_responses=True)
    r_db.ping()
    db_connected = True
except Exception as e:
    print(f"Redis Error: {e}")
    r_db = None
    db_connected = False

# --- ПОЛУЧЕНИЕ БАЛАНСА ---
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

# --- ЛОГИКА TON (CRYPTO BOT) ---
@app.route('/api/create_pay', methods=['POST'])
def create_pay():
    data = request.json
    uid = str(data.get('user_id'))
    amount = data.get('amount')
    
    payload = {
        "asset": "TON",
        "amount": str(amount),
        "payload": uid, # Передаем ID юзера здесь, чтобы поймать его в вебхуке
        "description": "Пополнение TON",
        "allow_comments": False
    }
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}
    
    try:
        r = requests.post(f"{BASE_CRYPTO_URL}/createInvoice", json=payload, headers=headers).json()
        if r.get('ok'):
            res = r['result']
            # Мапим ссылку для фронтенда (на фронте ищем pay_url)
            res['pay_url'] = res.get('bot_invoice_url')
            return jsonify(res), 200
        return jsonify({"error": "crypto_bot_err", "details": r}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/crypto-webhook', methods=['POST'])
def crypto_webhook():
    update = request.json
    # В CryptoBot тип события о зачислении: 'invoice_paid'
    if update and update.get('update_type') == 'invoice_paid':
        payload_data = update.get('payload', {})
        user_id = payload_data.get('payload') # Извлекаем UID
        amount = float(payload_data.get('amount'))
        
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
        "description": f"Пополнение баланса на {amount} звёзд",
        "payload": uid,
        "provider_token": "", # Для Stars всегда пусто
        "currency": "XTR",
        "prices": [{"label": "Stars", "amount": amount}]
    }
    
    try:
        r = requests.post(url, json=payload).json()
        if r.get('ok'):
            return jsonify({"pay_url": r['result']}), 200
        return jsonify({"error": "stars_err"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/telegram-webhook', methods=['POST'])
def telegram_webhook():
    update = request.json
    
    # 1. Pre-checkout (обязательный ответ Телеге перед оплатой)
    if "pre_checkout_query" in update:
        query_id = update["pre_checkout_query"]["id"]
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerPreCheckoutQuery", 
                      json={"pre_checkout_query_id": query_id, "ok": True})
        
    # 2. Successful Payment (зачисление в базу)
    if "message" in update and "successful_payment" in update["message"]:
        payment = update["message"]["successful_payment"]
        # Берем ID юзера из сообщения или из payload инвойса
        user_id = str(payment.get('invoice_payload')) or str(update["message"]["from"]["id"])
        stars_amount = int(payment["total_amount"])
        
        if r_db:
            raw_data = r_db.get(f"user:{user_id}")
            user_data = json.loads(raw_data) if raw_data else {"balance": 0.0, "stars": 0}
            user_data['stars'] = user_data.get('stars', 0) + stars_amount
            r_db.set(f"user:{user_id}", json.dumps(user_data))
            
    return "OK", 200

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "db": db_connected}), 200

if __name__ == '__main__':
    app.run(port=5000)
