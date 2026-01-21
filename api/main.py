from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)  # Разрешаем HTML-ке стучаться к серверу

# --- НАСТРОЙКИ ---
CRYPTO_PAY_TOKEN = '519389:AAnFdMg1D8ywsfVEd0aA02B8872Zzz61ATO'
ADMIN_ID = '8015661230'  # Чтобы бот писал тебе о подарках
BOT_TOKEN = '8451029637:AAHF6jJdQ98QhYRRsJxH_wuktMeE5QctT-I' # Для уведомлений

# Временная база данных (в реале лучше юзать SQLite/MongoDB)
users_db = {}

# 1. Создание счета в CryptoBot
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
        "description": f"Пополнение баланса StarsDrop для {uid}"
    }
    
    try:
        r = requests.post(url, json=payload, headers=headers).json()
        if r['ok']:
            return jsonify({
                "pay_url": r['result']['pay_url'],
                "invoice_id": r['result']['invoice_id']
            })
    except:
        pass
    return jsonify({"error": "API Error"}), 500

# 2. Проверка оплаты
@app.route('/check_pay/<invoice_id>', methods=['GET'])
def check_pay(invoice_id):
    url = f"https://pay.crypt.bot/api/getInvoices?invoice_ids={invoice_id}"
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}
    
    r = requests.get(url, headers=headers).json()
    if r['ok'] and r['result']['items'][0]['status'] == 'paid':
        inv = r['result']['items'][0]
        # Тут логика начисления баланса в твою БД
        return jsonify({"paid": True, "amount": inv['amount']})
    
    return jsonify({"paid": False})

# 3. Уведомление о подарке Stars (Ручная проверка)
@app.route('/notify_gift', methods=['POST'])
def notify_gift():
    data = request.json
    uid = data.get('user_id')
    username = data.get('username')
    
    # Отправляем сообщение тебе в бота
    msg = f"🎁 НОВЫЙ ПОДАРОК!\nЮзер: @{username}\nID: {uid}\nЖдет начисления Stars!"
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={ADMIN_ID}&text={msg}")
    
    return jsonify({"status": "sent"})

# 4. Получение баланса
@app.route('/get_balance/<user_id>', methods=['GET'])
def get_balance(user_id):
    # Заглушка, тут должен быть запрос к БД
    return jsonify({"balance": 0.00, "stars": 0})

if __name__ == '__main__':
    # На хостинге порт берется из переменной окружения
    import os
    port = int(os.environ.get("PORT", 5000))

    app.run(host='0.0.0.0', port=port)
