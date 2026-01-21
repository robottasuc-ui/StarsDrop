import os
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import requests
from vercel_kv import KV

app = Flask(__name__)
# Разрешаем запросы со всех доменов и любые заголовки
CORS(app, resources={r"/*": {"origins": "*"}})

# Принудительная настройка переменных для Vercel KV
if os.getenv("STORAGE_KV_URL"):
    os.environ["KV_URL"] = os.getenv("STORAGE_KV_URL")
    os.environ["KV_REST_API_URL"] = os.getenv("STORAGE_KV_REST_API_URL")
    os.environ["KV_REST_API_TOKEN"] = os.getenv("STORAGE_KV_REST_API_TOKEN")
    os.environ["KV_REST_API_READ_ONLY_TOKEN"] = os.getenv("STORAGE_KV_REST_API_READ_ONLY_TOKEN")

# Инициализация базы
try:
    kv = KV()
except Exception as e:
    print(f"KV Init Error: {e}")

CRYPTO_PAY_TOKEN = '519389:AAnFdMg1D8ywsfVEd0aA02B8872Zzz61ATO'

@app.route('/')
def home():
    return "Backend is Active", 200

@app.route('/get_balance/<user_id>', methods=['GET', 'OPTIONS'])
def get_balance(user_id):
    if request.method == 'OPTIONS':
        return _build_cors_prelight_response()
    try:
        key = f"user:{user_id}"
        user_data = kv.get(key) or {"balance": 0.0, "stars": 0}
        return _corsify_actual_response(jsonify(user_data))
    except Exception as e:
        return _corsify_actual_response(jsonify({"balance": 0.0, "stars": 0, "error": str(e)}))

@app.route('/create_pay', methods=['POST', 'OPTIONS'])
def create_pay():
    if request.method == 'OPTIONS':
        return _build_cors_prelight_response()
    
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
            return _corsify_actual_response(jsonify(r['result']))
        return _corsify_actual_response(jsonify({"error": "crypto_bot_err"}), 500)
    except Exception as e:
        return _corsify_actual_response(jsonify({"error": str(e)}), 500)

# Функции для исправления CORS (чтобы браузер не блокировал запросы)
def _build_cors_prelight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response
