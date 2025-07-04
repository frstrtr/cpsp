# PostgreSQL Migration Guide

## Overview

The TRON USDT Payment Monitor has been upgraded from in-memory storage to PostgreSQL for improved reliability, scalability, and data persistence.

## New Features

### Database Storage
- **Persistent Data**: Payment data survives application restarts
- **ACID Compliance**: Reliable transactions and data consistency
- **Scalability**: Handle thousands of payments efficiently
- **Advanced Queries**: Complex reporting and analytics capabilities

### Enhanced Logging
- **Payment Events**: Detailed logging of all payment lifecycle events
- **Debugging**: Better troubleshooting capabilities
- **Audit Trail**: Complete history of payment processing

### Improved Monitoring
- **Database Health**: Connection status and performance metrics
- **Advanced Statistics**: Detailed payment analytics
- **Historical Data**: Long-term payment tracking

## Installation

### Prerequisites

1. **PostgreSQL 12+**
2. **Python 3.7+**
3. **pip packages**: See requirements.txt

### Quick Setup

```bash
# 1. Run PostgreSQL setup script
./setup_postgres.sh

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Initialize database tables
python db_manager.py create-tables

# 4. Test the setup
python db_manager.py test

# 5. Start the application
python app.py
```

### Manual Setup

#### 1. Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download from https://www.postgresql.org/download/windows/

#### 2. Create Database and User

```sql
-- Connect as postgres user
sudo -u postgres psql

-- Create database
CREATE DATABASE tron_payments;

-- Create user
CREATE USER tron_user WITH PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE tron_payments TO tron_user;

-- Exit
\q
```

#### 3. Configure Environment

Update your `.env` file:
```env
DATABASE_URL=postgresql://tron_user:your_secure_password@localhost:5432/tron_payments
```

#### 4. Initialize Database

```bash
python db_manager.py create-tables
```

## Database Schema

### Tables

#### `payments`
| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(36) | Primary key (UUID) |
| wallet_address | VARCHAR(34) | TRON wallet address |
| expected_amount_usdt | NUMERIC(18,6) | Expected payment amount |
| callback_url | TEXT | Webhook URL |
| order_id | VARCHAR(100) | Unique order identifier |
| status | ENUM | Payment status (pending/completed/failed/expired) |
| transaction_hash | VARCHAR(64) | TRON transaction hash |
| received_amount_usdt | NUMERIC(18,6) | Actual received amount |
| created_at | TIMESTAMP | Payment creation time |
| completed_at | TIMESTAMP | Payment completion time |
| last_checked_timestamp | BIGINT | Last blockchain check time |
| callback_attempts | INTEGER | Number of callback attempts |
| last_callback_attempt | TIMESTAMP | Last callback attempt time |
| callback_success | BOOLEAN | Callback success status |

#### `payment_logs`
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| payment_id | VARCHAR(36) | Foreign key to payments |
| event_type | VARCHAR(50) | Event type (created/checking/completed/etc.) |
| message | TEXT | Event message |
| metadata | JSON | Additional event data |
| created_at | TIMESTAMP | Log entry creation time |

### Indexes

- `payments.wallet_address` - Fast lookup by wallet
- `payments.order_id` - Unique constraint and fast lookup
- `payments.status` - Filter by payment status
- `payments.created_at` - Time-based queries
- `payment_logs.payment_id` - Fast log retrieval
- `payment_logs.event_type` - Filter by event type

## Database Management

### Using db_manager.py

The `db_manager.py` script provides comprehensive database management:

```bash
# Create/update database tables
python db_manager.py create-tables

# Show database statistics
python db_manager.py stats

# Test database connection
python db_manager.py test

# Clean up old logs (older than 30 days)
python db_manager.py cleanup-logs --days 30

# Export all payments to JSON
python db_manager.py export --file backup.json

# Reset database (WARNING: deletes all data)
python db_manager.py reset
```

### Manual Database Operations

#### Connect to Database
```bash
psql postgresql://tron_user:password@localhost:5432/tron_payments
```

#### Common Queries
```sql
-- Show payment statistics
SELECT 
    status, 
    COUNT(*) as count,
    SUM(expected_amount_usdt) as total_amount
FROM payments 
GROUP BY status;

-- Recent payments
SELECT id, order_id, status, created_at, expected_amount_usdt
FROM payments 
ORDER BY created_at DESC 
LIMIT 10;

-- Failed callback attempts
SELECT id, order_id, callback_attempts, last_callback_attempt
FROM payments 
WHERE callback_success = false AND status = 'completed';

-- Payment processing time analysis
SELECT 
    AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) as avg_processing_seconds
FROM payments 
WHERE status = 'completed';
```

## Migration from In-Memory Version

If you're upgrading from the in-memory version:

### 1. Backup Current Data
If your application is running with pending payments, note them down as they will be lost during migration.

### 2. Stop Application
```bash
# Stop the running application
pkill -f "python app.py"
```

### 3. Setup Database
```bash
./setup_postgres.sh
```

### 4. Update Code
The new version automatically uses PostgreSQL. No code changes needed in your integration.

### 5. Test Migration
```bash
python db_manager.py test
python test_api.py
```

## Performance Considerations

### Connection Pooling
The application uses SQLAlchemy connection pooling:

```python
# Default settings in database.py
'pool_size': 10,
'pool_recycle': 120,
'pool_pre_ping': True,
'max_overflow': 20
```

### Optimization Tips

1. **Indexes**: All critical fields are indexed
2. **Connection Reuse**: Persistent connections reduce overhead
3. **Query Optimization**: Use specific filters in queries
4. **Log Cleanup**: Regular cleanup prevents table bloat

### Monitoring Performance

```sql
-- Show table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size
FROM pg_tables 
WHERE schemaname = 'public';

-- Show active connections
SELECT COUNT(*) FROM pg_stat_activity WHERE datname = 'tron_payments';

-- Show slow queries (if enabled)
SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC;
```

## Backup and Recovery

### Automated Backups

Create a backup script:
```bash
#!/bin/bash
# backup_db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="tron_payments_backup_$DATE.sql"

pg_dump postgresql://tron_user:password@localhost:5432/tron_payments > $BACKUP_FILE

echo "Backup created: $BACKUP_FILE"

# Keep only last 7 days of backups
find . -name "tron_payments_backup_*.sql" -mtime +7 -delete
```

### Recovery

```bash
# Restore from backup
psql postgresql://tron_user:password@localhost:5432/tron_payments < backup_file.sql

# Or restore specific table
pg_restore -t payments backup_file.sql
```

## Security

### Database Security

1. **User Privileges**: Use dedicated user with minimal privileges
2. **Network Security**: Restrict database access to application server
3. **SSL/TLS**: Enable encrypted connections in production
4. **Regular Updates**: Keep PostgreSQL updated

### Application Security

1. **SQL Injection**: SQLAlchemy ORM prevents SQL injection
2. **Connection Strings**: Store credentials in environment variables
3. **Audit Logging**: All database operations are logged

## Troubleshooting

### Common Issues

#### Connection Errors
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check if database exists
sudo -u postgres psql -l | grep tron_payments

# Test connection
python db_manager.py test
```

#### Performance Issues
```bash
# Check database stats
python db_manager.py stats

# Monitor active connections
psql -c "SELECT COUNT(*) FROM pg_stat_activity WHERE datname = 'tron_payments';"
```

#### Data Issues
```bash
# Check for orphaned records
psql tron_payments -c "SELECT COUNT(*) FROM payment_logs pl LEFT JOIN payments p ON pl.payment_id = p.id WHERE p.id IS NULL;"

# Clean up old logs
python db_manager.py cleanup-logs --days 30
```

### Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `psycopg2.OperationalError: could not connect` | PostgreSQL not running | `sudo systemctl start postgresql` |
| `relation "payments" does not exist` | Tables not created | `python db_manager.py create-tables` |
| `FATAL: password authentication failed` | Wrong credentials | Check DATABASE_URL in .env |
| `too many connections` | Connection pool exhausted | Restart application or increase pool size |

## Production Deployment

### Database Configuration

For production, consider:

1. **Dedicated Database Server**: Separate database from application server
2. **Read Replicas**: For improved read performance
3. **Connection Pooling**: Use PgBouncer for connection management
4. **Monitoring**: Use tools like pg_stat_monitor
5. **Backup Strategy**: Automated daily backups with point-in-time recovery

### High Availability

1. **Master-Slave Setup**: For failover capability
2. **Load Balancing**: Distribute read queries
3. **Monitoring**: Database health checks
4. **Alerting**: Notify on connection issues or performance degradation

## API Changes

The API remains **100% compatible** with the previous version. No changes needed in client applications.

### New Features Available

1. **Enhanced Statistics**: More detailed payment analytics
2. **Better Error Handling**: Database connection status in health checks
3. **Audit Trail**: Complete payment history via logs
4. **Performance**: Faster queries with proper indexing

## Next Steps

1. **Set up monitoring**: Implement database monitoring
2. **Configure backups**: Set up automated backup system
3. **Performance tuning**: Monitor and optimize based on usage
4. **Scale planning**: Plan for horizontal scaling if needed

The PostgreSQL migration provides a solid foundation for production use and future scaling!
