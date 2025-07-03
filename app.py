import os
import uuid
import time
import requests
import json
from flask import Flask, request, jsonify
from threading import Thread
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

app = Flask(__name__)

# --- Конфигурация ---
# Адрес контракта USDT (TRC20) на TRON Mainnet
USDT_TRC20_CONTRACT_ADDRESS = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
# Базовый URL для TronGrid API
TRONGRID_API_BASE_URL = "https://api.trongrid.io/v1"
# API ключ TronGrid (если есть, иначе может быть ограничение по запросам)
TRONGRID_API_KEY = os.getenv("TRONGRID_API_KEY")

# Интервал опроса блокчейна (в секундах)
POLLING_INTERVAL_SECONDS = 10

# --- Хранение данных (в памяти для MVP, заменить на БД в продакшене) ---
# Словарь для хранения запросов на отслеживание платежей
# payment_id: {
#   'wallet_address': '...',
#   'expected_amount_usdt': float,
#   'callback_url': '...',
#   'order_id': '...',
#   'status': 'pending' | 'completed' | 'failed',
#   'transaction_hash': '...',
#   'received_amount_usdt': float,
#   'created_at': timestamp,
#   'last_checked_block': int # Для оптимизации, чтобы не проверять старые транзакции
# }
payments_to_watch = {}

# --- Вспомогательные функции ---

def get_trc20_transactions(address, min_timestamp=0):
    """
    Получает TRC20 транзакции для данного адреса с TronGrid API.
    :param address: Адрес TRON для проверки.
    :param min_timestamp: Минимальная временная метка для фильтрации транзакций (в миллисекундах).
    :return: Список транзакций или None в случае ошибки.
    """
    url = f"{TRONGRID_API_BASE_URL}/accounts/{address}/transactions/trc20"
    headers = {}
    if TRONGRID_API_KEY:
        headers["TRON-PRO-API-KEY"] = TRONGRID_API_KEY

    params = {
        "only_confirmed": True,  # Только подтвержденные транзакции
        "limit": 50,             # Максимальное количество транзакций за запрос
        "order_by": "block_timestamp,desc", # Сортировка по убыванию времени блока
        "min_timestamp": min_timestamp # Фильтр по минимальной временной метке
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()  # Вызовет исключение для HTTP ошибок (4xx или 5xx)
        data = response.json()
        return data.get("data", [])
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching TRC20 transactions for {address}: {e}")
        return None

def send_callback(callback_url, payload):
    """
    Отправляет HTTP POST коллбэк на указанный URL.
    :param callback_url: URL для отправки коллбэка.
    :param payload: Данные для отправки в JSON формате.
    """
    try:
        response = requests.post(callback_url, json=payload, timeout=5)
        response.raise_for_status()
        app.logger.info(f"Callback sent successfully to {callback_url} for payment {payload.get('order_id')}")
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error sending callback to {callback_url}: {e}")

def monitor_tron_addresses():
    """
    Фоновая задача для мониторинга TRON-адресов.
    Периодически опрашивает TronGrid на наличие новых транзакций.
    """
    app.logger.info("Starting TRON address monitor...")
    while True:
        # Копируем словарь, чтобы избежать ошибок изменения во время итерации
        current_payments = list(payments_to_watch.items())
        
        for payment_id, payment_info in current_payments:
            if payment_info['status'] == 'pending':
                wallet_address = payment_info['wallet_address']
                expected_amount_usdt = payment_info['expected_amount_usdt']
                callback_url = payment_info['callback_url']
                order_id = payment_info['order_id']
                
                # Используем timestamp создания запроса как min_timestamp для получения только новых транзакций
                # Или можно хранить last_checked_timestamp в payment_info
                min_timestamp_for_check = payment_info.get('last_checked_timestamp', 0)
                
                app.logger.info(f"Checking transactions for {wallet_address} (order_id: {order_id}) since {min_timestamp_for_check}")
                
                transactions = get_trc20_transactions(wallet_address, min_timestamp=min_timestamp_for_check)
                
                if transactions is None:
                    app.logger.warning(f"Could not retrieve transactions for {wallet_address}. Retrying later.")
                    continue

                found_transaction = False
                for tx in transactions:
                    # Убедимся, что это входящая транзакция на нужный адрес и нужный контракт
                    if tx.get('to') == wallet_address and tx.get('token_info', {}).get('address') == USDT_TRC20_CONTRACT_ADDRESS:
                        # Сумма в TronGrid API для TRC20 часто возвращается как строка с полным количеством децималов
                        # Например, 1 USDT = 1000000. Нужно преобразовать.
                        amount_raw = int(tx.get('value', 0))
                        token_decimals = tx.get('token_info', {}).get('decimals', 6) # USDT обычно имеет 6 децималов
                        
                        received_amount_usdt = amount_raw / (10 ** token_decimals)
                        
                        # Проверяем, соответствует ли полученная сумма ожидаемой
                        # Используем небольшую дельту для сравнения чисел с плавающей точкой
                        if abs(received_amount_usdt - expected_amount_usdt) < 0.000001: # Например, 0.000001 USDT
                            app.logger.info(f"Matching payment found for order_id: {order_id}")
                            
                            # Обновляем статус платежа
                            payments_to_watch[payment_id].update({
                                'status': 'completed',
                                'transaction_hash': tx.get('transaction_id'),
                                'received_amount_usdt': received_amount_usdt,
                                'completed_at': time.time()
                            })
                            found_transaction = True

                            # Отправляем коллбэк
                            callback_payload = {
                                "payment_id": payment_id,
                                "order_id": order_id,
                                "wallet_address": wallet_address,
                                "currency": "USDT_TRC20",
                                "expected_amount_usdt": expected_amount_usdt,
                                "received_amount_usdt": received_amount_usdt,
                                "transaction_hash": tx.get('transaction_id'),
                                "block_timestamp": tx.get('block_timestamp'),
                                "status": "completed"
                            }
                            send_callback(callback_url, callback_payload)
                            break # Нашли нужную транзакцию, можно перейти к следующему платежу

                # Обновляем last_checked_timestamp для следующего цикла, чтобы не проверять старые транзакции
                # Если транзакций не было, или не нашли, все равно обновляем, чтобы не повторять старые запросы
                # Берем текущее время, чтобы в следующий раз проверять только новые транзакции
                payments_to_watch[payment_id]['last_checked_timestamp'] = int(time.time() * 1000) # в миллисекундах
                
        time.sleep(POLLING_INTERVAL_SECONDS) # Ждем перед следующим циклом опроса

# --- API Эндпоинты ---

@app.route('/create_payment', methods=['POST'])
def create_payment():
    """
    Эндпоинт для создания запроса на отслеживание платежа.
    Принимает:
    {
        "wallet_address": "Txxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "expected_amount_usdt": 12.34,
        "callback_url": "https://your-service.com/webhook/payment_received",
        "order_id": "YOUR_UNIQUE_ORDER_ID_FROM_YOUR_SYSTEM"
    }
    """
    data = request.get_json()

    wallet_address = data.get('wallet_address')
    expected_amount_usdt = data.get('expected_amount_usdt')
    callback_url = data.get('callback_url')
    order_id = data.get('order_id')

    # Простая валидация входных данных
    if not all([wallet_address, expected_amount_usdt, callback_url, order_id]):
        return jsonify({"error": "Missing required fields"}), 400
    
    if not isinstance(expected_amount_usdt, (int, float)) or expected_amount_usdt <= 0:
        return jsonify({"error": "expected_amount_usdt must be a positive number"}), 400
    
    # Можно добавить более строгую валидацию адреса TRON и URL

    payment_id = str(uuid.uuid4())
    payments_to_watch[payment_id] = {
        'wallet_address': wallet_address,
        'expected_amount_usdt': float(expected_amount_usdt),
        'callback_url': callback_url,
        'order_id': order_id,
        'status': 'pending',
        'transaction_hash': None,
        'received_amount_usdt': None,
        'created_at': time.time(),
        'last_checked_timestamp': int(time.time() * 1000) # Инициализируем для первого опроса
    }

    app.logger.info(f"Payment watch created: {payment_id} for {wallet_address} expecting {expected_amount_usdt} USDT")
    return jsonify({
        "payment_id": payment_id,
        "status": "watching",
        "message": "Payment watch created successfully. Waiting for transaction."
    }), 201

@app.route('/payment_status/<payment_id>', methods=['GET'])
def get_payment_status(payment_id):
    """
    Эндпоинт для проверки статуса платежа.
    """
    payment_info = payments_to_watch.get(payment_id)
    if not payment_info:
        return jsonify({"error": "Payment ID not found"}), 404
    
    # Возвращаем копию, чтобы избежать случайных изменений извне
    status_info = payment_info.copy()
    # Удаляем внутренние поля, которые не должны быть видны клиенту
    status_info.pop('callback_url', None)
    status_info.pop('last_checked_timestamp', None)

    return jsonify(status_info), 200

# --- Запуск приложения и монитора ---

if __name__ == '__main__':
    # Запускаем фоновый монитор в отдельном потоке
    # В продакшене лучше использовать Celery/RQ или другие системы очередей/воркеров
    monitor_thread = Thread(target=monitor_tron_addresses, daemon=True)
    monitor_thread.start()

    # Запускаем Flask приложение
    app.run(debug=True, host='0.0.0.0', port=5000)
