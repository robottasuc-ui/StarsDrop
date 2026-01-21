import os
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import requests
from vercel_kv import KV

app = Flask(__name__)
# Включаем CORS правильно, чтобы он сам обрабатывал OPTIONS запросы
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Проброс ключей базы
if os.getenv("STORAGE_KV_URL"):
    os.environ["KV_URL"] = os.getenv("STORAGE_KV_URL")
    os.environ["KV_REST_API_URL"] = os.getenv("STORAGE_KV_REST_API_URL")
    os.environ["KV_REST_API_TOKEN"] = os.getenv("STORAGE_KV_REST_API_TOKEN")

# Инициализация базы
kv = KV()

CRYPTO_PAY_TOKEN = '519389:AAnFdMg1D8ywsfVEd0aA02B8872Zzz61ATO'

@app.route('/api/')
def home():
    return jsonify({"status": "active", "info": "StarsDrop API"}), 200

# ВАЖНО: Добавили /api/ в начало пути
@app.route('/api/get_balance/<user_id>', methods=['GET'])
def get_balance(user_id):
    try:
        key = f"user:{user_id}"
        # Исправлено: если данных нет, возвращаем структуру, чтобы фронт не падал
        user_data = kv.get(key)
        if not user_data:
            user_data = {"balance": 0.0, "stars": 0}
        return jsonify(user_data), 200
    except Exception as e:
        return jsonify({"balance": 0.0, "stars": 0, "error": str(e)}), 200

# ВАЖНО: Добавили /api/ в начало пути
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
