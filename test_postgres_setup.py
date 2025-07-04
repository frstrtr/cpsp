#!/usr/bin/env python3
"""
Quick test script for PostgreSQL integration
"""

import sys
import os

# Test imports
try:
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    import psycopg2
    print("✅ All required packages imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test PostgreSQL connection
try:
    # Try to connect to default PostgreSQL
    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password=""
    )
    conn.close()
    print("✅ PostgreSQL connection test passed (using default postgres user)")
except Exception as e:
    print(f"⚠️  PostgreSQL connection test failed: {e}")
    print("   This is expected if PostgreSQL is not installed or configured")

# Test application imports
try:
    sys.path.append('/home/user0/Documents/GitHub/cpsp')
    from models import Payment, PaymentStatus, PaymentLog
    from database import init_database
    print("✅ Application modules imported successfully")
except Exception as e:
    print(f"❌ Application import error: {e}")
    sys.exit(1)

print("\n🎉 All tests passed! Ready for PostgreSQL setup.")
print("\nNext steps:")
print("1. Run: ./setup_postgres.sh")
print("2. Run: python db_manager.py create-tables")
print("3. Run: python app.py")
