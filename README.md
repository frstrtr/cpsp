# TRON USDT Payment Monitor

A Flask-based application that monitors TRON blockchain for USDT (TRC20) payments and provides webhook notifications when payments are received.

## Features

- Monitor specific TRON wallet addresses for incoming USDT payments
- Real-time payment verification against expected amounts
- Webhook callbacks when payments are confirmed
- RESTful API for creating payment watches and checking status
- Background monitoring with configurable polling intervals

## Requirements

- Python 3.7+
- Flask
- python-dotenv
- requests

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd cpsp
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file for environment variables:
```bash
cp .env.example .env
```

5. Edit the `.env` file and add your TronGrid API key (optional but recommended):
```
TRONGRID_API_KEY=your_api_key_here
```

## Usage

### Starting the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

### API Endpoints

#### Create Payment Watch

**POST** `/create_payment`

Create a new payment monitoring request.

**Request Body:**
```json
{
    "wallet_address": "Txxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "expected_amount_usdt": 12.34,
    "callback_url": "https://your-service.com/webhook/payment_received",
    "order_id": "YOUR_UNIQUE_ORDER_ID"
}
```

**Response:**
```json
{
    "payment_id": "uuid-string",
    "status": "watching",
    "message": "Payment watch created successfully. Waiting for transaction."
}
```

#### Check Payment Status

**GET** `/payment_status/<payment_id>`

Check the status of a payment monitoring request.

**Response:**
```json
{
    "wallet_address": "Txxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "expected_amount_usdt": 12.34,
    "order_id": "YOUR_UNIQUE_ORDER_ID",
    "status": "completed",
    "transaction_hash": "transaction_hash_here",
    "received_amount_usdt": 12.34,
    "created_at": 1625097600.0,
    "completed_at": 1625097660.0
}
```

### Webhook Callback

When a payment is detected and verified, the application will send a POST request to the provided `callback_url` with the following payload:

```json
{
    "payment_id": "uuid-string",
    "order_id": "YOUR_UNIQUE_ORDER_ID",
    "wallet_address": "Txxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "currency": "USDT_TRC20",
    "expected_amount_usdt": 12.34,
    "received_amount_usdt": 12.34,
    "transaction_hash": "transaction_hash_here",
    "block_timestamp": 1625097660000,
    "status": "completed"
}
```

## Configuration

The application can be configured through environment variables or by modifying the constants in `app.py`:

- `TRONGRID_API_KEY`: TronGrid API key for increased rate limits
- `POLLING_INTERVAL_SECONDS`: How often to check for new transactions (default: 10 seconds)
- `USDT_TRC20_CONTRACT_ADDRESS`: USDT contract address on TRON (default: TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t)

## Security Considerations

- This is a minimal viable product (MVP) implementation
- Payment data is stored in memory and will be lost on application restart
- For production use, implement proper database storage
- Add authentication and rate limiting for API endpoints
- Validate wallet addresses and callback URLs more thoroughly
- Use proper logging and error handling
- Consider using task queues (like Celery/RQ) instead of background threads

## License

This project is provided as-is for educational and development purposes.

## Contributing

Pull requests and issues are welcome. Please ensure any contributions follow best practices for security and code quality.
