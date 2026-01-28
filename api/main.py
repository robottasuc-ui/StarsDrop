import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client

app = Flask(__name__)
CORS(app)

# Настройки Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Токены
CRYPTO_PAY_TOKEN = '519389:AAnFdMg1D8ywsfVEd0aA02B8872Zzz61ATO'
BOT_TOKEN = '8451029637:AAHF6jJdQ98QhYRRsJxH_wuktMeE5QctT-I'

# --- ПОЛУЧЕНИЕ/СОЗДАНИЕ ЮЗЕРА ---
def get_or_create_user(user_id):
    res = supabase.table('users').select("*").eq('user_id', user_id).execute()
    if res.data:
        return res.data[0]
    new_user = {"user_id": int(user_id), "balance": 0.0, "stars": 0, "points": 0}
    supabase.table('users').insert(new_user).execute()
    return new_user

# --- СОЗДАНИЕ ОПЛАТЫ TON ---
@app.route('/api/create_pay', methods=['POST'])
def create_pay():
    try:
        data = request.json
        uid = str(data.get('user_id'))
        amount = data.get('amount')
        
        url = "https://pay.crypt.bot/api/createInvoice"
        payload = {
            "asset": "TON",
            "amount": str(amount),
            "payload": uid,
            "description": "Пополнение баланса TON"
        }
        headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}
        
        r = requests.post(url, json=payload, headers=headers).json()
        if r.get('ok'):
            # Возвращаем ссылку так, как её ждет твой фронтенд
            return jsonify({"pay_url": r['result']['bot_invoice_url']}), 200
        return jsonify({"error": "crypto_bot_err", "details": r}), 400
    except Exception as e:
        return jsonify({"error": str(e)} Prime), 500

# --- СОЗДАНИЕ ОПЛАТЫ ЗВЁЗДАМИ ---
@app.route('/api/create_stars_pay', methods=['POST'])
def create_stars_pay():
    try:
        data = request.json
        uid = str(data.get('user_id'))
        amount = int(data.get('amount'))
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/createInvoiceLink"
        payload = {
            "title": "Пополнение звёзд",
            "description": f"Зачисление {amount} XTR на баланс",
            "payload": uid,
            "provider_token": "", # ОБЯЗАТЕЛЬНО для звезд
            "currency": "XTR",
            "prices": [{"label": "Stars", "amount": amount}]
        }
        
        r = requests.post(url, json=payload).json()
        if r.get('ok'):
            return jsonify({"pay_url": r['result']}), 200
        return jsonify({"error": "telegram_api_err", "details": r}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- ВЕБХУКИ ОСТАЮТСЯ ТАКИМИ ЖЕ ---
@app.route('/api/crypto-webhook', methods=['POST'])
def crypto_webhook():
    update = request.json
    if update.get('update_type') == 'invoice_paid':
        p = update.get('payload', {})
        uid, amt = p.get('payload'), float(p.get('amount'))
        u = get_or_create_user(uid)
        new_bal = round(float(u.get('balance', 0.0)) + amt, 2)
        supabase.table('users').update({"balance": new_bal}).eq('user_id', uid).execute()
    return "OK", 200

@app.route('/api/telegram-webhook', methods=['POST'])
def telegram_webhook():
    update = request.json
    if "pre_checkout_query" in update:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerPreCheckoutQuery", 
                      json={"pre_checkout_query_id": update["pre_checkout_query"]["id"], "ok": True})
    if "message" in update and "successful_payment" in update["message"]:
        pay = update["message"]["successful_payment"]
        uid, amt = pay.get('invoice_payload'), int(pay["total_amount"])
        u = get_or_create_user(uid)
        new_stars = int(u.get('stars', 0)) + amt
        supabase.table('users').update({"stars": new_stars}).eq('user_id', uid).execute()
    return "OK", 200

@app.route('/api/get_balance/<user_id>', methods=['GET'])
def get_balance(user_id):
    user = get_or_create_user(user_id)
    return jsonify(user), 200

if __name__ == '__main__':
    app.run(port=5000)
