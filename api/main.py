from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from vercel_kv import KV

app = Flask(__name__)
CORS(app)

# Подключаем твою базу Redis
kv = KV()

CRYPTO_PAY_TOKEN = '519389:AAnFdMg1D8ywsfVEd0aA02B8872Zzz61ATO'

@app.route('/')
def home():
    return "Server is Running", 200

@app.route('/get_balance/<user_id>')
def get_balance(user_id):
    try:
        key = f"user:{user_id}"
        user_data = kv.get(key) or {"balance": 0.0, "stars": 0}
        return jsonify(user_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/create_pay', methods=['POST'])
def create_pay():
    data = request.json
    uid = data.get('user_id')
    amount = data.get('amount')
    
    url = "https://pay.crypt.bot/api/createInvoice"
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}
    payload = {
        "asset": "TRX", 
        "amount": str(amount),
        "description": f"Deposit ID: {uid}"
    }
    
    try:
        r = requests.post(url, json=payload, headers=headers).json()
        if r.get('ok'):
            return jsonify(r['result'])
        return jsonify({"error": "crypto_bot_err"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/check_pay/<invoice_id>/<user_id>')
def check_pay(invoice_id, user_id):
    url = f"https://pay.crypt.bot/api/getInvoices?invoice_ids={invoice_id}"
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}
    
    try:
        r = requests.get(url, headers=headers).json()
        if r.get('ok') and r['result']['items']:
            inv = r['result']['items'][0]
            if inv['status'] == 'paid':
                key = f"user:{user_id}"
                history_key = f"paid_inv:{user_id}"
                
                paid_invoices = kv.get(history_key) or []
                if invoice_id not in paid_invoices:
                    current_data = kv.get(key) or {"balance": 0.0, "stars": 0}
                    current_data["balance"] = round(current_data["balance"] + float(inv['amount']), 2)
                    
                    paid_invoices.append(invoice_id)
                    kv.set(key, current_data)
                    kv.set(history_key, paid_invoices)
                    
                    return jsonify({"paid": True, "new_balance": current_data["balance"]})
                return jsonify({"paid": True, "message": "Already added"})
        return jsonify({"paid": False})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
