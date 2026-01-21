import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from vercel_kv import KV

app = Flask(__name__)
# Разрешаем CORS для всех путей, начинающихся с /api/
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ХАК ДЛЯ ТВОИХ СКРИНШОТОВ:
# Перекладываем значения из STORAGE_... в те переменные, которые ждет библиотека KV
if os.getenv("STORAGE_KV_URL"):
    os.environ["KV_URL"] = os.getenv("STORAGE_KV_URL")
    os.environ["KV_REST_API_URL"] = os.getenv("STORAGE_KV_REST_API_URL")
    os.environ["KV_REST_API_TOKEN"] = os.getenv("STORAGE_KV_REST_API_TOKEN")
    os.environ["KV_REST_API_READ_ONLY_TOKEN"] = os.getenv("STORAGE_KV_REST_API_READ_ONLY_TOKEN")

# Инициализируем базу (теперь она увидит ключи)
try:
    kv = KV()
except Exception as e:
    print(f"KV Error: {e}")
    kv = None

CRYPTO_PAY_TOKEN = '519389:AAnFdMg1D8ywsfVEd0aA02B8872Zzz61ATO'

@app.route('/api/get_balance/<user_id>', methods=['GET'])
def get_balance(user_id):
    if not kv:
        return jsonify({"balance": 0.0, "stars": 0, "db": "offline"}), 200
    try:
        user_data = kv.get(f"user:{user_id}")
        if not user_data:
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
        return jsonify({"error": "crypto_bot_err", "details": r}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Для проверки работоспособности в браузере
@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "db_connected": kv is not None}), 200
