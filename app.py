import os
import uuid
import time
import requests
import re
from flask import Flask, request, jsonify
from threading import Thread
from dotenv import load_dotenv
import logging

# Загрузка переменных окружения из .env файла
load_dotenv()

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
app.logger.setLevel(logging.INFO)

# --- Конфигурация ---
# Адрес контракта USDT (TRC20) на TRON Mainnet
USDT_TRC20_CONTRACT_ADDRESS = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
# Базовый URL для TronGrid API
TRONGRID_API_BASE_URL = "https://api.trongrid.io/v1"
# API ключ TronGrid (если есть, иначе может быть ограничение по запросам)
TRONGRID_API_KEY = os.getenv("TRONGRID_API_KEY")

# Интервал опроса блокчейна (в секундах)
POLLING_INTERVAL_SECONDS = int(os.getenv("POLLING_INTERVAL_SECONDS", "10"))

# Максимальное время жизни платежного запроса (в секундах) - 24 часа
MAX_PAYMENT_LIFETIME_SECONDS = 24 * 60 * 60

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

def is_valid_tron_address(address):
    """
    Простая валидация TRON адреса.
    TRON адрес должен начинаться с 'T' и быть длиной 34 символа.
    """
    if not address or not isinstance(address, str):
        return False
    
    # TRON адрес должен начинаться с 'T' и быть длиной 34 символа
    if len(address) != 34 or not address.startswith('T'):
        return False
    
    # Проверяем, что остальные символы - это base58 символы
    base58_pattern = re.compile(r'^[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]+$')
    return bool(base58_pattern.match(address[1:]))

def is_valid_url(url):
    """
    Простая валидация URL для callback.
    """
    if not url or not isinstance(url, str):
        return False
    
    url_pattern = re.compile(
        r'^https?://'  # http:// или https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...или ip
        r'(?::\d+)?'  # опциональный порт
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(url_pattern.match(url))

def cleanup_expired_payments():
    """
    Удаляет истекшие платежные запросы из памяти.
    """
    current_time = time.time()
    expired_payments = []
    
    for payment_id, payment_info in payments_to_watch.items():
        if current_time - payment_info['created_at'] > MAX_PAYMENT_LIFETIME_SECONDS:
            expired_payments.append(payment_id)
    
    for payment_id in expired_payments:
        app.logger.info("Removing expired payment: %s", payment_id)
        del payments_to_watch[payment_id]

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
        app.logger.error("Error fetching TRC20 transactions for %s: %s", address, e)
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
        app.logger.info("Callback sent successfully to %s for payment %s", 
                       callback_url, payload.get('order_id'))
    except requests.exceptions.RequestException as e:
        app.logger.error("Error sending callback to %s: %s", callback_url, e)

def monitor_tron_addresses():
    """
    Фоновая задача для мониторинга TRON-адресов.
    Периодически опрашивает TronGrid на наличие новых транзакций.
    """
    app.logger.info("Starting TRON address monitor...")
    while True:
        try:
            # Очистка истекших платежей
            cleanup_expired_payments()
            
            # Копируем словарь, чтобы избежать ошибок изменения во время итерации
            current_payments = list(payments_to_watch.items())
            
            if not current_payments:
                app.logger.debug("No payments to monitor, sleeping...")
                time.sleep(POLLING_INTERVAL_SECONDS)
                continue
            
            for payment_id, payment_info in current_payments:
                if payment_info['status'] == 'pending':
                    try:
                        process_pending_payment(payment_id, payment_info)
                    except (requests.exceptions.RequestException, ValueError) as e:
                        app.logger.error("Error processing payment %s: %s", payment_id, e)
                        
        except Exception as e:
            app.logger.error("Error in monitor thread: %s", e)
            
        time.sleep(POLLING_INTERVAL_SECONDS) # Ждем перед следующим циклом опроса

def process_pending_payment(payment_id, payment_info):
    """
    Обрабатывает один ожидающий платеж.
    """
    wallet_address = payment_info['wallet_address']
    expected_amount_usdt = payment_info['expected_amount_usdt']
    callback_url = payment_info['callback_url']
    order_id = payment_info['order_id']
    
    # Используем timestamp создания запроса как min_timestamp для получения только новых транзакций
    min_timestamp_for_check = payment_info.get('last_checked_timestamp', 0)
    
    app.logger.debug("Checking transactions for %s (order_id: %s) since %s", 
                    wallet_address, order_id, min_timestamp_for_check)
    
    transactions = get_trc20_transactions(wallet_address, min_timestamp=min_timestamp_for_check)
    
    if transactions is None:
        app.logger.warning("Could not retrieve transactions for %s. Retrying later.", wallet_address)
        return

    for tx in transactions:
        # Убедимся, что это входящая транзакция на нужный адрес и нужный контракт
        if tx.get('to') == wallet_address and tx.get('token_info', {}).get('address') == USDT_TRC20_CONTRACT_ADDRESS:
            # Сумма в TronGrid API для TRC20 часто возвращается как строка с полным количеством децималов
            amount_raw = int(tx.get('value', 0))
            token_decimals = tx.get('token_info', {}).get('decimals', 6) # USDT обычно имеет 6 децималов
            
            received_amount_usdt = amount_raw / (10 ** token_decimals)
            
            # Проверяем, соответствует ли полученная сумма ожидаемой
            # Используем небольшую дельту для сравнения чисел с плавающей точкой
            if abs(received_amount_usdt - expected_amount_usdt) < 0.000001: # 0.000001 USDT
                app.logger.info("Matching payment found for order_id: %s", order_id)
                
                # Обновляем статус платежа
                payments_to_watch[payment_id].update({
                    'status': 'completed',
                    'transaction_hash': tx.get('transaction_id'),
                    'received_amount_usdt': received_amount_usdt,
                    'completed_at': time.time()
                })

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

    # Обновляем last_checked_timestamp для следующего цикла
    payments_to_watch[payment_id]['last_checked_timestamp'] = int(time.time() * 1000) # в миллисекундах

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
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON or empty request body"}), 400

        wallet_address = data.get('wallet_address')
        expected_amount_usdt = data.get('expected_amount_usdt')
        callback_url = data.get('callback_url')
        order_id = data.get('order_id')

        # Валидация обязательных полей
        if not all([wallet_address, expected_amount_usdt, callback_url, order_id]):
            return jsonify({"error": "Missing required fields: wallet_address, expected_amount_usdt, callback_url, order_id"}), 400
        
        # Валидация суммы
        if not isinstance(expected_amount_usdt, (int, float)) or expected_amount_usdt <= 0:
            return jsonify({"error": "expected_amount_usdt must be a positive number"}), 400
        
        # Валидация минимальной суммы (например, 0.01 USDT)
        if expected_amount_usdt < 0.01:
            return jsonify({"error": "expected_amount_usdt must be at least 0.01 USDT"}), 400
        
        # Валидация максимальной суммы (например, 1,000,000 USDT)
        if expected_amount_usdt > 1000000:
            return jsonify({"error": "expected_amount_usdt cannot exceed 1,000,000 USDT"}), 400
        
        # Валидация TRON адреса
        if not is_valid_tron_address(wallet_address):
            return jsonify({"error": "Invalid TRON wallet address format"}), 400
        
        # Валидация callback URL
        if not is_valid_url(callback_url):
            return jsonify({"error": "Invalid callback URL format"}), 400
        
        # Валидация order_id
        if not isinstance(order_id, str) or len(order_id.strip()) == 0:
            return jsonify({"error": "order_id must be a non-empty string"}), 400
        
        if len(order_id) > 100:
            return jsonify({"error": "order_id cannot exceed 100 characters"}), 400
        
        # Проверка уникальности order_id
        for existing_payment in payments_to_watch.values():
            if existing_payment['order_id'] == order_id and existing_payment['status'] == 'pending':
                return jsonify({"error": "order_id already exists with pending status"}), 409

        payment_id = str(uuid.uuid4())
        payments_to_watch[payment_id] = {
            'wallet_address': wallet_address,
            'expected_amount_usdt': float(expected_amount_usdt),
            'callback_url': callback_url,
            'order_id': order_id.strip(),
            'status': 'pending',
            'transaction_hash': None,
            'received_amount_usdt': None,
            'created_at': time.time(),
            'last_checked_timestamp': int(time.time() * 1000) # Инициализируем для первого опроса
        }

        app.logger.info("Payment watch created: %s for %s expecting %s USDT (order_id: %s)", 
                       payment_id, wallet_address, expected_amount_usdt, order_id)
        return jsonify({
            "payment_id": payment_id,
            "status": "watching",
            "message": "Payment watch created successfully. Waiting for transaction.",
            "expires_at": time.time() + MAX_PAYMENT_LIFETIME_SECONDS
        }), 201
        
    except (ValueError, TypeError, KeyError) as e:
        app.logger.error("Invalid input for payment creation: %s", e)
        return jsonify({"error": "Invalid input data"}), 400
    except Exception as e:
        app.logger.error("Error creating payment: %s", e)
        return jsonify({"error": "Internal server error"}), 500

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

@app.route('/health', methods=['GET'])
def health_check():
    """
    Эндпоинт для проверки здоровья сервиса.
    """
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "active_payments": len([p for p in payments_to_watch.values() if p['status'] == 'pending']),
        "total_payments": len(payments_to_watch)
    }), 200

@app.route('/stats', methods=['GET'])
def get_stats():
    """
    Эндпоинт для получения статистики сервиса.
    """
    pending_count = len([p for p in payments_to_watch.values() if p['status'] == 'pending'])
    completed_count = len([p for p in payments_to_watch.values() if p['status'] == 'completed'])
    
    return jsonify({
        "pending_payments": pending_count,
        "completed_payments": completed_count,
        "total_payments": len(payments_to_watch),
        "uptime_seconds": time.time(),
        "polling_interval": POLLING_INTERVAL_SECONDS
    }), 200

# --- Запуск приложения и монитора ---

if __name__ == '__main__':
    # Запускаем фоновый монитор в отдельном потоке
    # В продакшене лучше использовать Celery/RQ или другие системы очередей/воркеров
    monitor_thread = Thread(target=monitor_tron_addresses, daemon=True)
    monitor_thread.start()

    # Запускаем Flask приложение
    app.run(debug=True, host='0.0.0.0', port=5000)
