import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- НАСТРОЙКИ (Берутся из переменных Vercel) ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

CRYPTO_PAY_TOKEN = '519389:AAnFdMg1D8ywsfVEd0aA02B8872Zzz61ATO'
BOT_TOKEN = '8451029637:AAHF6jJdQ98QhYRRsJxH_wuktMeE5QctT-I'
BASE_CRYPTO_URL = "https://pay.crypt.bot/api"

# --- ПОЛУЧЕНИЕ ИЛИ СОЗДАНИЕ ЮЗЕРА ---
def get_or_create_user(user_id):
    res = supabase.table('users').select("*").eq('user_id', user_id).execute()
    if res.data:
        return res.data[0]
    
    new_user = {"user_id": int(user_id), "balance": 0.0, "stars": 0, "points": 0}
    supabase.table('users').insert(new_user).execute()
    return new_user

# --- ПОЛУЧЕНИЕ БАЛАНСА ---
@app.route('/api/get_balance/<user_id>', methods=['GET'])
def get_balance(user_id):
    try:
        user = get_or_create_user(user_id)
        return jsonify(user), 200
    except Exception as e:
        return jsonify({"balance": 0.0, "stars": 0, "error": str(e)}), 200

# --- ЛОГИКА TON (CRYPTO BOT) ---
@app.route('/api/create_pay', methods=['POST'])
def create_pay():
    data = request.json
    uid = str(data.get('user_id'))
    amount = data.get('amount')
    payload = {"asset": "TON", "amount": str(amount), "payload": uid, "description": "Пополнение TON"}
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}
    r = requests.post(f"{BASE_CRYPTO_URL}/createInvoice", json=payload, headers=headers).json()
    if r.get('ok'):
        res = r['result']
        res['pay_url'] = res.get('bot_invoice_url')
        return jsonify(res), 200
    return jsonify({"error": "err"}), 400

@app.route('/api/crypto-webhook', methods=['POST'])
def crypto_webhook():
    update = request.json
    if update.get('update_type') == 'invoice_paid':
        p = update.get('payload', {})
        uid = p.get('payload')
        amount = float(p.get('amount'))
        
        user = get_or_create_user(uid)
        new_bal = round(float(user.get('balance', 0.0)) + amount, 2)
        supabase.table('users').update({"balance": new_bal}).eq('user_id', uid).execute()
    return "OK", 200

# --- ЛОГИКА TELEGRAM STARS ---
@app.route('/api/create_stars_pay', methods=['POST'])
def create_stars_pay():
    data = request.json
    uid = str(data.get('user_id'))
    amount = int(data.get('amount'))
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/createInvoiceLink"
    payload = {"title": "Звёзды", "description": "Пополнение", "payload": uid, "currency": "XTR", "prices": [{"label": "Stars", "amount": amount}]}
    r = requests.post(url, json=payload).json()
    return jsonify({"pay_url": r['result']}) if r.get('ok') else (jsonify({"error": "err"}), 400)

@app.route('/api/telegram-webhook', methods=['POST'])
def telegram_webhook():
    update = request.json
    if "pre_checkout_query" in update:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerPreCheckoutQuery", 
                      json={"pre_checkout_query_id": update["pre_checkout_query"]["id"], "ok": True})
    
    if "message" in update and "successful_payment" in update["message"]:
        pay = update["message"]["successful_payment"]
        uid = pay.get('invoice_payload')
        amount = int(pay["total_amount"])
        
        user = get_or_create_user(uid)
        new_stars = int(user.get('stars', 0)) + amount
        supabase.table('users').update({"stars": new_stars}).eq('user_id', uid).execute()
    return "OK", 200

if __name__ == '__main__':
    app.run(port=5000)
