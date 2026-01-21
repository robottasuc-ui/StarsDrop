import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import redis
import json

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ТВОЙ КЛЮЧ ПРЯМО ЗДЕСЬ
REDIS_URL = "redis://default:9x1pwcq9Vp94gWovLw1qMQQZ5euiZy5w@redis-13357.crce220.us-east-1-4.ec2.cloud.redislabs.com:13357"

# Подключаемся к Redis
try:
    r_db = redis.from_url(REDIS_URL, decode_responses=True)
    # Простая проверка связи
    r_db.ping()
    db_connected = True
except Exception as e:
    print(f"Redis Error: {e}")
    r_db = None
    db_connected = False

CRYPTO_PAY_TOKEN = '519389:AAnFdMg1D8ywsfVEd0aA02B8872Zzz61ATO'

@app.route('/api/get_balance/<user_id>', methods=['GET'])
def get_balance(user_id):
    if not r_db:
        return jsonify({"balance": 0.0, "stars": 0, "db": "offline"}), 200
    try:
        # В Redis Labs данные обычно лежат в строках, парсим JSON
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
    uid = data.get('user_id')
    amount = data.get('amount')
    
    payload = {
        "asset": "TON",
        "amount": str(amount),
        "description": f"Deposit ID: {uid}"
    }
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}
    
    try:
        r = requests.post("https://pay.crypt.bot/api/createInvoice", json=payload, headers=headers).json()
        if r.get('ok'):
            return jsonify(r['result']), 200
        return jsonify({"error": "crypto_bot_err"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health')
def health():
    return jsonify({
        "status": "ok", 
        "db_connected": db_connected,
        "source": "redis-labs"
    }), 200
