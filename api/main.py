from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# --- НАСТРОЙКИ ---
CRYPTO_PAY_TOKEN = '519389:AAnFdMg1D8ywsfVEd0aA02B8872Zzz61ATO'
ADMIN_ID = '8015661230'
BOT_TOKEN = '8451029637:AAHF6jJdQ98QhYRRsJxH_wuktMeE5QctT-I'

@app.route('/')
def home():
    return "Server is Live!", 200

@app.route('/create_pay', methods=['POST'])
def create_pay():
    data = request.json
    uid = data.get('user_id')
    amount = data.get('amount')
    
    url = "https://pay.crypt.bot/api/createInvoice"
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}
    payload = {
        "asset": "TON",
        "amount": str(amount),
        "description": f"Deposit for {uid}"
    }
    
    try:
        r = requests.post(url, json=payload, headers=headers)
        res_data = r.json()
        if res_data.get('ok'):
            return jsonify({
                "pay_url": res_data['result']['pay_url'],
                "invoice_id": res_data['result']['invoice_id']
            })
        return jsonify({"error": res_data.get('error')}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/check_pay/<invoice_id>')
def check_pay(invoice_id):
    url = f"https://pay.crypt.bot/api/getInvoices?invoice_ids={invoice_id}"
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}
    try:
        r = requests.get(url, headers=headers).json()
        if r['ok'] and r['result']['items']:
            status = r['result']['items'][0]['status']
            return jsonify({"paid": status == 'paid'})
        return jsonify({"paid": False})
    except:
        return jsonify({"paid": False}), 500

@app.route('/get_balance/<user_id>')
def get_balance(user_id):
    return jsonify({"balance": 0.00, "stars": 0})
