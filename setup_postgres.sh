#!/bin/bash

# PostgreSQL Setup Script for TRON USDT Payment Monitor

echo "🐘 Setting up PostgreSQL for TRON Payment Monitor..."

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "📦 PostgreSQL not found. Installing..."
    
    # Update package list
    sudo apt update
    
    # Install PostgreSQL
    sudo apt install -y postgresql postgresql-contrib
    
    # Start and enable PostgreSQL
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    
    echo "✅ PostgreSQL installed successfully"
else
    echo "✅ PostgreSQL is already installed"
fi

# Check if PostgreSQL is running
if ! sudo systemctl is-active --quiet postgresql; then
    echo "🔄 Starting PostgreSQL..."
    sudo systemctl start postgresql
fi

# Set password for postgres user (only if not already set)
echo "🔐 Setting up database and user..."

# Switch to postgres user and create database and user
sudo -u postgres psql << EOF
-- Create database
CREATE DATABASE IF NOT EXISTS tron_payments;

-- Create user (modify password as needed)
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'tron_user') THEN
        CREATE USER tron_user WITH PASSWORD 'tron_password_2024';
    END IF;
END
\$\$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE tron_payments TO tron_user;

-- Connect to the database and grant schema privileges
\c tron_payments;
GRANT ALL ON SCHEMA public TO tron_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tron_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tron_user;

-- Show created database
\l tron_payments
EOF

if [ $? -eq 0 ]; then
    echo "✅ Database 'tron_payments' and user 'tron_user' created successfully"
else
    echo "❌ Error setting up database"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    
    # Update the database URL in .env
    sed -i 's|DATABASE_URL=postgresql://username:password@localhost:5432/tron_payments|DATABASE_URL=postgresql://tron_user:tron_password_2024@localhost:5432/tron_payments|g' .env
    
    echo "✅ .env file created with database configuration"
else
    echo "⚠️  .env file already exists. Please update DATABASE_URL manually:"
    echo "   DATABASE_URL=postgresql://tron_user:tron_password_2024@localhost:5432/tron_payments"
fi

# Test database connection
echo "🧪 Testing database connection..."
if command -v python3 &> /dev/null; then
    python3 << EOF
import psycopg2
try:
    conn = psycopg2.connect(
        host="localhost",
        database="tron_payments",
        user="tron_user",
        password="tron_password_2024"
    )
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print(f"✅ Database connection successful!")
    print(f"   PostgreSQL version: {version[0][:50]}...")
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    exit(1)
EOF
else
    echo "⚠️  Python3 not found. Please test the connection manually."
fi

echo ""
echo "🎉 PostgreSQL setup completed!"
echo ""
echo "📋 Database Information:"
echo "   Host: localhost"
echo "   Port: 5432"
echo "   Database: tron_payments"
echo "   Username: tron_user"
echo "   Password: tron_password_2024"
echo ""
echo "🔄 Next steps:"
echo "   1. Update your .env file with the correct DATABASE_URL"
echo "   2. Install Python dependencies: pip install -r requirements.txt"
echo "   3. Run the application: python app.py"
echo ""
echo "⚠️  Security Note: Change the default password in production!"
echo "   You can do this by running:"
echo "   sudo -u postgres psql -c \"ALTER USER tron_user PASSWORD 'your_secure_password';\""
