# Deployment Guide - TRON USDT Payment Monitor

## Quick Start

### 1. Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd cpsp

# Run the setup script
./start.sh
```

### 2. Manual Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env

# Run the application
python app.py
```

### 3. Test the Service

```bash
# Run API tests
python test_api.py

# Or open test interface
open test_interface.html
```

## Production Deployment

### Option 1: Docker (Recommended)

1. **Create Dockerfile:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
```

2. **Create docker-compose.yml:**
```yaml
version: '3.8'
services:
  tron-payment-monitor:
    build: .
    ports:
      - "5000:5000"
    environment:
      - TRONGRID_API_KEY=${TRONGRID_API_KEY}
      - POLLING_INTERVAL_SECONDS=10
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

3. **Deploy:**
```bash
# Add gunicorn to requirements.txt
echo "gunicorn" >> requirements.txt

# Build and run
docker-compose up -d
```

### Option 2: Traditional Server

1. **Install on Ubuntu/Debian:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv nginx -y

# Create application user
sudo useradd -m -s /bin/bash tronpay
sudo su - tronpay

# Clone and setup
git clone <repository-url> /home/tronpay/app
cd /home/tronpay/app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt gunicorn

# Create .env file
cp .env.example .env
# Edit .env with your settings
```

2. **Create systemd service:**
```bash
sudo nano /etc/systemd/system/tron-payment-monitor.service
```

```ini
[Unit]
Description=TRON USDT Payment Monitor
After=network.target

[Service]
Type=exec
User=tronpay
Group=tronpay
WorkingDirectory=/home/tronpay/app
ExecStart=/home/tronpay/app/.venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

3. **Configure Nginx:**
```bash
sudo nano /etc/nginx/sites-available/tron-payment-monitor
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

4. **Enable and start services:**
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/tron-payment-monitor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Start application
sudo systemctl daemon-reload
sudo systemctl enable tron-payment-monitor
sudo systemctl start tron-payment-monitor

# Check status
sudo systemctl status tron-payment-monitor
```

### Option 3: Cloud Platforms

#### Heroku
```bash
# Install Heroku CLI
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Deploy
heroku create your-app-name
heroku config:set TRONGRID_API_KEY=your_key_here
git push heroku main
```

#### Railway
```bash
# Add railway.json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn app:app"
  }
}
```

#### DigitalOcean App Platform
```yaml
# .do/app.yaml
name: tron-payment-monitor
services:
- name: web
  source_dir: /
  github:
    repo: your-username/your-repo
    branch: main
  run_command: gunicorn app:app
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: TRONGRID_API_KEY
    value: your_key_here
    type: SECRET
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TRONGRID_API_KEY` | TronGrid API key for higher limits | None |
| `POLLING_INTERVAL_SECONDS` | How often to check blockchain | 10 |
| `FLASK_ENV` | Flask environment (development/production) | development |
| `FLASK_DEBUG` | Enable Flask debug mode | True |

## Monitoring and Logging

### 1. Application Logs
```bash
# View logs in development
tail -f app.log

# View logs in production (systemd)
sudo journalctl -u tron-payment-monitor -f

# View logs in Docker
docker-compose logs -f
```

### 2. Health Monitoring
```bash
# Simple health check script
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)
if [ $response != "200" ]; then
    echo "Service is down! HTTP $response"
    # Send alert (email, Slack, etc.)
fi
```

### 3. Log Rotation
```bash
# Create logrotate config
sudo nano /etc/logrotate.d/tron-payment-monitor
```

```
/home/tronpay/app/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    postrotate
        systemctl reload tron-payment-monitor
    endscript
}
```

## Security Considerations

### 1. API Security
- Use HTTPS in production
- Implement API key authentication
- Add rate limiting
- Validate all inputs

### 2. Server Security
```bash
# Update firewall
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw --force enable

# Automatic updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 3. SSL Certificate (Let's Encrypt)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Backup and Recovery

### 1. Configuration Backup
```bash
# Backup important files
tar -czf backup-$(date +%Y%m%d).tar.gz \
    .env \
    app.py \
    requirements.txt
```

### 2. Database Migration (Future)
When migrating to a database, backup payment data:
```bash
# Example with PostgreSQL
pg_dump payment_monitor > backup.sql
```

## Performance Optimization

### 1. Gunicorn Configuration
```python
# gunicorn.conf.py
bind = "0.0.0.0:5000"
workers = 2
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
```

### 2. Nginx Optimization
```nginx
# Add to nginx config
location /static {
    alias /home/tronpay/app/static;
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# Compression
gzip on;
gzip_types text/plain application/json;
```

## Troubleshooting

### Common Issues

1. **Service won't start:**
```bash
# Check logs
sudo journalctl -u tron-payment-monitor -n 50

# Check syntax
python app.py --check-syntax
```

2. **API not responding:**
```bash
# Check if port is open
netstat -tlnp | grep 5000

# Test locally
curl http://localhost:5000/health
```

3. **TronGrid API errors:**
```bash
# Check API key
curl -H "TRON-PRO-API-KEY: your_key" \
  https://api.trongrid.io/v1/accounts/TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t/transactions/trc20
```

4. **High memory usage:**
```bash
# Monitor memory
htop
# Or use process-specific monitoring
ps aux | grep python
```

## Scaling Considerations

For high-volume applications:

1. **Use Redis for caching**
2. **Implement database storage**
3. **Add load balancing**
4. **Use message queues (RabbitMQ/Redis)**
5. **Implement horizontal scaling**
6. **Add monitoring (Prometheus/Grafana)**

## Support

- Check logs first
- Review the troubleshooting section
- Open GitHub issues with full error details
- Include environment information and steps to reproduce
