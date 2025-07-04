# TRON USDT Payment Monitor

A Flask-based application that monitors TRON blockchain for USDT (TRC20) payments and provides webhook notifications when payments are received.

## ✨ New: PostgreSQL Support

**Major Update**: The application now uses PostgreSQL for persistent data storage instead of in-memory storage, providing:

- **Data Persistence**: Payment data survives application restarts
- **Improved Reliability**: ACID transactions and data consistency  
- **Better Scalability**: Handle thousands of payments efficiently
- **Enhanced Logging**: Detailed audit trail of all payment events
- **Advanced Analytics**: Rich reporting and statistics capabilities

> 📖 **Migration Guide**: See [POSTGRESQL_MIGRATION.md](POSTGRESQL_MIGRATION.md) for detailed upgrade instructions.

## ⚠️ Production Ready

This version is **production-ready** with enterprise-grade features:

- ✅ PostgreSQL database with proper indexing
- ✅ Comprehensive error handling and logging
- ✅ Connection pooling and performance optimization
- ✅ Data persistence and backup capabilities
- ✅ Advanced monitoring and statistics
- ✅ 100% API compatibility maintained

## Features

- ✅ Monitor specific TRON wallet addresses for incoming USDT (TRC20) payments
- ✅ Real-time payment verification against expected amounts
- ✅ Webhook callbacks when payments are confirmed
- ✅ RESTful API for creating payment watches and checking status
- ✅ Background monitoring with configurable polling intervals
- ✅ Input validation and error handling
- ✅ Health check and statistics endpoints
- ✅ Test interface for easy testing
- ✅ **Client-side address management with mnemonic phrases** ⭐ NEW
- ✅ **QR code generation for wallet import** ⭐ NEW
- ✅ **BIP39/BIP44 HD wallet support** ⭐ NEW

## Client-Side Tools ⭐ NEW

The `/client` folder contains advanced tools for wallet generation and address management:

- **Mnemonic Wallet Generator**: BIP39 compatible wallet generation with 12-word recovery phrases
- **QR Code Export**: Generate QR codes for easy wallet import into mobile applications
- **HD Wallet Support**: BIP44 hierarchical deterministic wallet derivation
- **Multiple Export Formats**: Compatible with TronLink and other TRON wallets
- **Payment Integration**: Seamless integration with the main monitoring service

See [client/README.md](client/README.md) for complete documentation and examples.

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
POLLING_INTERVAL_SECONDS=10
```

Get your free TronGrid API key at: https://www.trongrid.io/

## Usage

### Starting the Service

```bash
python app.py
```

The service will start on `http://localhost:5000`

### Test Interface

Open `test_interface.html` in your browser for a user-friendly interface to test the API.

### API Endpoints

#### 1. Create Payment Watch

**POST** `/create_payment`

Create a new payment watch request.

```json
{
    "wallet_address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
    "expected_amount_usdt": 12.34,
    "callback_url": "https://your-service.com/webhook/payment_received",
    "order_id": "YOUR_UNIQUE_ORDER_ID"
}
```

**Response:**
```json
{
    "payment_id": "uuid-v4-string",
    "status": "watching",
    "message": "Payment watch created successfully. Waiting for transaction.",
    "expires_at": 1672531200
}
```

#### 2. Check Payment Status

**GET** `/payment_status/<payment_id>`

Get the current status of a payment watch.

**Response:**
```json
{
    "wallet_address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
    "expected_amount_usdt": 12.34,
    "order_id": "YOUR_UNIQUE_ORDER_ID",
    "status": "completed",
    "transaction_hash": "abc123...",
    "received_amount_usdt": 12.34,
    "created_at": 1672531200,
    "completed_at": 1672531500
}
```

#### 3. Health Check

**GET** `/health`

Check service health and get basic statistics.

#### 4. Statistics

**GET** `/stats`

Get detailed service statistics.

### Webhook Callback

When a payment is detected, the service will send a POST request to your callback URL:

```json
{
    "payment_id": "uuid-v4-string",
    "order_id": "YOUR_UNIQUE_ORDER_ID",
    "wallet_address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
    "currency": "USDT_TRC20",
    "expected_amount_usdt": 12.34,
    "received_amount_usdt": 12.34,
    "transaction_hash": "abc123...",
    "block_timestamp": 1672531500,
    "status": "completed"
}
```

## Testing

### Using Webhook.site

1. Go to https://webhook.site and copy your unique URL
2. Use this URL as your `callback_url` when creating payment watches
3. You'll see the webhook calls in real-time

### Example with cURL

```bash
# Create a payment watch
curl -X POST http://localhost:5000/create_payment \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
    "expected_amount_usdt": 10.50,
    "callback_url": "https://webhook.site/your-unique-url",
    "order_id": "ORDER_123456"
  }'

# Check payment status
curl http://localhost:5000/payment_status/your-payment-id

# Check service health
curl http://localhost:5000/health
```

## Configuration

Environment variables in `.env`:

- `TRONGRID_API_KEY`: Your TronGrid API key (optional)
- `POLLING_INTERVAL_SECONDS`: How often to check for new transactions (default: 10)
- `FLASK_ENV`: Flask environment (development/production)
- `FLASK_DEBUG`: Enable Flask debug mode (True/False)

## Production Considerations

This MVP is suitable for testing and small-scale applications. For production use, consider these improvements:

### 🔄 Database
- Replace in-memory storage with PostgreSQL, MySQL, or MongoDB
- Add proper indexing for performance
- Implement data persistence and backup

### 🚀 Scalability
- Use Redis for caching and session storage
- Implement horizontal scaling with load balancers
- Separate monitoring service from API service

### 🔐 Security
- Add API authentication (API keys, JWT tokens)
- Implement rate limiting
- Add HTTPS/TLS encryption
- Input sanitization and SQL injection protection

### 📊 Monitoring & Logging
- Centralized logging (ELK stack, CloudWatch)
- Application monitoring (Prometheus, Grafana)
- Error tracking (Sentry)
- Performance monitoring (APM tools)

### 🔧 DevOps
- Containerization with Docker
- CI/CD pipelines
- Infrastructure as Code (Terraform)
- Auto-scaling and health checks

### 🌐 Blockchain
- Use WebSocket connections instead of polling
- Implement confirmation waiting (multiple blocks)
- Add support for multiple cryptocurrencies
- Handle blockchain reorganizations

### 🛡️ Reliability
- Implement retry mechanisms with exponential backoff
- Circuit breaker pattern for external API calls
- Dead letter queues for failed webhooks
- Graceful degradation strategies

## Troubleshooting

### Common Issues

1. **API Rate Limiting**: Get a TronGrid API key for higher limits
2. **Webhook Timeouts**: Ensure your callback URL is accessible and responds quickly
3. **Transaction Not Found**: TRON transactions may take time to be indexed by TronGrid

### Logs

The application logs important events. Check the console output for:
- Payment watch creation
- Transaction detection
- Webhook delivery status
- API errors

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs
3. Open an issue on GitHub

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
