# API Examples for TRON USDT Payment Monitor

## Prerequisites

Make sure the service is running on `http://localhost:5000`

```bash
./start.sh
```

## 1. Check Service Health

```bash
curl -X GET http://localhost:5000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": 1672531200.123,
  "active_payments": 0,
  "total_payments": 0
}
```

## 2. Get Service Statistics

```bash
curl -X GET http://localhost:5000/stats
```

## 3. Create Payment Watch

### Basic Example

```bash
curl -X POST http://localhost:5000/create_payment \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
    "expected_amount_usdt": 10.50,
    "callback_url": "https://webhook.site/your-unique-url-here",
    "order_id": "ORDER_123456"
  }'
```

### Using webhook.site for Testing

1. Go to https://webhook.site
2. Copy your unique URL (e.g., `https://webhook.site/8f7c4e2a-1234-5678-9abc-def012345678`)
3. Use it as `callback_url`:

```bash
curl -X POST http://localhost:5000/create_payment \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "TLPsV2meGxAiUjYnt5DMZCjPJW5dwD9XaB",
    "expected_amount_usdt": 5.0,
    "callback_url": "https://webhook.site/8f7c4e2a-1234-5678-9abc-def012345678",
    "order_id": "TEST_ORDER_001"
  }'
```

**Expected Response:**
```json
{
  "payment_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "status": "watching",
  "message": "Payment watch created successfully. Waiting for transaction.",
  "expires_at": 1672617600
}
```

## 4. Check Payment Status

```bash
curl -X GET http://localhost:5000/payment_status/a1b2c3d4-e5f6-7890-1234-567890abcdef
```

**Pending Payment Response:**
```json
{
  "wallet_address": "TLPsV2meGxAiUjYnt5DMZCjPJW5dwD9XaB",
  "expected_amount_usdt": 5.0,
  "order_id": "TEST_ORDER_001",
  "status": "pending",
  "transaction_hash": null,
  "received_amount_usdt": null,
  "created_at": 1672531200.123
}
```

**Completed Payment Response:**
```json
{
  "wallet_address": "TLPsV2meGxAiUjYnt5DMZCjPJW5dwD9XaB",
  "expected_amount_usdt": 5.0,
  "order_id": "TEST_ORDER_001",
  "status": "completed",
  "transaction_hash": "abc123def456...",
  "received_amount_usdt": 5.0,
  "created_at": 1672531200.123,
  "completed_at": 1672531500.789
}
```

## 5. Test with Python

### Using requests library

```python
import requests
import json
import time

API_BASE = "http://localhost:5000"

# 1. Check health
response = requests.get(f"{API_BASE}/health")
print("Health:", response.json())

# 2. Create payment watch
payment_data = {
    "wallet_address": "TLPsV2meGxAiUjYnt5DMZCjPJW5dwD9XaB",
    "expected_amount_usdt": 7.25,
    "callback_url": "https://webhook.site/your-unique-url",
    "order_id": f"ORDER_{int(time.time())}"
}

response = requests.post(f"{API_BASE}/create_payment", json=payment_data)
payment_result = response.json()
print("Payment created:", payment_result)

if response.status_code == 201:
    payment_id = payment_result["payment_id"]
    
    # 3. Check payment status
    status_response = requests.get(f"{API_BASE}/payment_status/{payment_id}")
    print("Payment status:", status_response.json())
```

## 6. Testing Real Payments

**⚠️ Warning:** Use testnet or small amounts for testing!

For testing with real transactions:

1. Use a TRON wallet that you control
2. Send the exact USDT amount to the monitored address
3. Watch the logs and webhook for confirmation

### TRON Testnet

For safer testing, consider using TRON Shasta Testnet:
- Get test TRX from: https://shasta.tronex.io
- Use Shasta TronGrid API: `https://api.shasta.trongrid.io`

## 7. Error Handling Examples

### Invalid Wallet Address
```bash
curl -X POST http://localhost:5000/create_payment \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "invalid_address",
    "expected_amount_usdt": 10.0,
    "callback_url": "https://webhook.site/test",
    "order_id": "ORDER_123"
  }'
```

**Response:**
```json
{
  "error": "Invalid TRON wallet address format"
}
```

### Missing Fields
```bash
curl -X POST http://localhost:5000/create_payment \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
  }'
```

**Response:**
```json
{
  "error": "Missing required fields: wallet_address, expected_amount_usdt, callback_url, order_id"
}
```

### Payment Not Found
```bash
curl -X GET http://localhost:5000/payment_status/non-existent-id
```

**Response:**
```json
{
  "error": "Payment ID not found"
}
```

## 8. Webhook Payload

When a payment is detected, your callback URL will receive:

```json
{
  "payment_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "order_id": "TEST_ORDER_001",
  "wallet_address": "TLPsV2meGxAiUjYnt5DMZCjPJW5dwD9XaB",
  "currency": "USDT_TRC20",
  "expected_amount_usdt": 5.0,
  "received_amount_usdt": 5.0,
  "transaction_hash": "abc123def456789...",
  "block_timestamp": 1672531500789,
  "status": "completed"
}
```

## 9. Monitoring Multiple Payments

You can create multiple payment watches simultaneously:

```bash
# Payment 1
curl -X POST http://localhost:5000/create_payment \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
    "expected_amount_usdt": 10.0,
    "callback_url": "https://webhook.site/url1",
    "order_id": "ORDER_001"
  }'

# Payment 2
curl -X POST http://localhost:5000/create_payment \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "TLPsV2meGxAiUjYnt5DMZCjPJW5dwD9XaB",
    "expected_amount_usdt": 25.50,
    "callback_url": "https://webhook.site/url2",
    "order_id": "ORDER_002"
  }'
```

## Tips

1. **Use unique order IDs** to avoid conflicts
2. **Test webhook URLs** before creating payment watches
3. **Monitor service logs** for debugging
4. **Check TronGrid API limits** if you have many payments
5. **Set up proper error handling** in your webhook endpoint
