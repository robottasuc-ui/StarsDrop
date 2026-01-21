import os
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    # Проверяем, видит ли сервер ключи от базы
    kv_check = "OK" if os.getenv("STORAGE_KV_URL") or os.getenv("KV_URL") else "MISSING"
    return jsonify({
        "status": "online",
        "message": "Backend is working!",
        "database_keys": kv_check
    }), 200

@app.route('/get_balance/<user_id>')
def get_balance(user_id):
    return jsonify({"balance": 100.0, "stars": 0, "note": "Test mode"}), 200
