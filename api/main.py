import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- НАСТРОЙКИ SUPABASE (Бери из настроек проекта) ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- ТОКЕНЫ ---
CRYPTO_PAY_TOKEN = '519389:AAnFdMg1D8ywsfVEd0aA02B8872Zzz61ATO'
BOT_TOKEN = '8451029637:AAHF6jJdQ98QhYRRsJxH_wuktMeE5QctT-I'
BASE_CRYPTO_URL = "https://pay.crypt.bot/api"

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_user_from_db(user_id):
    # Ищем юзера в Supabase
    res = supabase.table('users').select("*").eq('user_id', user_id).execute()
    if res.data:
        return res.data[0]
    # Если нет - создаем
    new_user = {"user_id": int(user_id), "balance": 0.0, "stars": 0, "points": 0}
    supabase.table('users').insert(new_user).execute()
    return new_user

# --- ПОЛУЧЕНИЕ БАЛАНСА ---
@app.route('/api/get_balance/<user_id>', methods=['GET'])
def get_balance(user_id):
    try:
        user = get_user_from_db(user_id)
        return jsonify(user), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- ЛОГИКА TON (CRYPTO BOT) ---
@app.route('/api/crypto-webhook', methods=['POST'])
def crypto_webhook():
    update = request.json
    if update and update.get('update_type') == 'invoice_paid':
        payload_data = update.get('payload', {})
        user_id = payload_data.get('payload') 
        amount = float(payload_data.get('amount'))
        
        user = get_user_from_db(user_id)
        new_balance = round(float(user.get('balance', 0)) + amount, 2)
        
        supabase.table('users').update({"balance": new_balance}).eq('user_id', user_id).execute()
        print(f"TON зачислен юзеру {user_id}")
    return "OK", 200

# --- ЛОГИКА TELEGRAM STARS ---
@app.route('/api/telegram-webhook', methods=['POST'])
def telegram_webhook():
    update = request.json
    
    # 1. Ответ на Pre-checkout
    if "pre_checkout_query" in update:
        query_id = update["pre_checkout_query"]["id"]
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerPreCheckoutQuery", 
                      json={"pre_checkout_query_id": query_id, "ok": True})
        return "OK", 200
        
    # 2. Зачисление Звёзд
    if "message" in update and "successful_payment" in update["message"]:
        payment = update["message"]["successful_payment"]
        user_id = str(payment.get('invoice_payload'))
        stars_amount = int(payment["total_amount"])
        
        user = get_user_from_db(user_id)
        new_stars = int(user.get('stars', 0)) + stars_amount
        
        supabase.table('users').update({"stars": new_stars}).eq('user_id', user_id).execute()
        print(f"Звезды ({stars_amount}) зачислены юзеру {user_id}")
            
    return "OK", 200

@app.route('/api/create_stars_pay', methods=['POST'])
def create_stars_pay():
    data = request.json
    uid = str(data.get('user_id'))
    amount = int(data.get('amount'))
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/createInvoiceLink"
    payload = {
        "title": "Пополнение звёзд",
        "description": f"Пополнение на {amount} звёзд",
        "payload": uid,
        "currency": "XTR",
        "prices": [{"label": "Stars", "amount": amount}]
    }
    r = requests.post(url, json=payload).json()
    return jsonify({"pay_url": r['result']}) if r.get('ok') else (jsonify({"error": "err"}), 400)

if __name__ == '__main__':
    app.run(port=5000)
