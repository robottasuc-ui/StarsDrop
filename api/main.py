import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import redis
import json

app = Flask(__name__)
# Разрешаем CORS, чтобы фронтенд мог достучаться до бэкенда
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Данные Redis
REDIS_URL = "redis://default:9x1pwcq9Vp94gWovLw1qMQQZ5euiZy5w@redis-13357.crce220.us-east-1-4.ec2.cloud.redislabs.com:13357"

try:
    r_db = redis.from_url(REDIS_URL, decode_responses=True)
    r_db.ping()
    db_connected = True
except Exception as e:
    print(f"Redis Error: {e}")
    r_db = None
    db_connected = False

CRYPTO_PAY_TOKEN = '519389:AAnFdMg1D8ywsfVEd0aA02B8872Zzz61ATO'
# Используем основной домен API
BASE_API_URL = "https://pay.cryptobots.run/api"

@app.route('/api/get_balance/<user_id>', methods=['GET'])
def get_balance(user_id):
    if not r_db:
        return jsonify({"balance": 0.0, "stars": 0, "db": "offline"}), 200
    try:
        data = r_db.get(f"user:{user_id}")
        if data:
            user_data = json.loads(data)
        else:
            user_data = {"balance": 0.0, "stars": 0}
        return jsonify(user_data), 200
    except Exception as e:
        return jsonify({"balance": 0.0, "stars": 0, "error": str(e)}), 200

@app.route('/api/create_pay', methods=['POST'])
def create_pay():
    data = request.json
    uid = str(data.get('user_id')) # Превращаем в строку для безопасности
    amount = data.get('amount')
    
    payload = {
        "asset": "TON",
        "amount": str(amount),
        "payload": uid,  # ВАЖНО: Вебхук вернет именно это поле
        "description": f"Пополнение баланса StarsDrop",
        "allow_comments": False
    }
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}
    
    try:
        r = requests.post(f"{BASE_API_URL}/createInvoice", json=payload, headers=headers).json()
        if r.get('ok'):
            return jsonify(r['result']), 200
        return jsonify({"error": "crypto_bot_err", "details": r}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# НОВЫЙ РОУТ ДЛЯ КРИПТОБОТА
@app.route('/api/crypto-webhook', methods=['POST', 'GET'])
def crypto_webhook():
    if request.method == 'GET':
        return "Webhook is active! Use POST for payments.", 200

    data = request.json
    # Проверяем, что оплата прошла успешно
    if data and data.get('status') == 'paid':
        user_id = data.get('payload') # Получаем тот самый UID
        amount = float(data.get('amount'))

        if r_db and user_id:
            try:
                # Читаем базу
                raw_data = r_db.get(f"user:{user_id}")
                user_data = json.loads(raw_data) if raw_data else {"balance": 0.0, "stars": 0}
                
                # Зачисляем TON
                user_data['balance'] = round(user_data.get('balance', 0.0) + amount, 2)
                
                # Сохраняем
                r_db.set(f"user:{user_id}", json.dumps(user_data))
                print(f"Success deposit: {user_id} +{amount} TON")
            except Exception as e:
                print(f"Database update error: {e}")

    return "OK", 200

@app.route('/api/health')
def health():
    return jsonify({
        "status": "ok", 
        "db_connected": db_connected,
        "source": "redis-labs"
    }), 200

if __name__ == '__main__':
    app.run(port=5000)
