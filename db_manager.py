#!/usr/bin/env python3
"""
Database management script for TRON USDT Payment Monitor
"""

import os
import sys
import argparse
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from database import init_database, create_tables, get_database_stats, cleanup_old_logs
from models import db, Payment, PaymentStatus, PaymentLog

def setup_app():
    """Setup Flask app for database operations"""
    app = Flask(__name__)
    init_database(app)
    return app

def create_db_tables(app):
    """Create all database tables"""
    print("🏗️  Creating database tables...")
    try:
        with app.app_context():
            db.create_all()
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    return True

def show_stats(app):
    """Show database statistics"""
    print("📊 Database Statistics:")
    print("-" * 30)
    
    try:
        with app.app_context():
            stats = get_database_stats()
            
            if 'error' in stats:
                print(f"❌ Error getting stats: {stats['error']}")
                return
                
            print(f"Total Payments: {stats['total_payments']}")
            print(f"Pending: {stats['pending_payments']}")
            print(f"Completed: {stats['completed_payments']}")
            print(f"Failed: {stats['failed_payments']}")
            print(f"Expired: {stats['expired_payments']}")
            
            # Show recent payments
            recent_payments = db.session.query(Payment).order_by(Payment.created_at.desc()).limit(5).all()
            
            if recent_payments:
                print("\n📋 Recent Payments:")
                for payment in recent_payments:
                    print(f"  {payment.id[:8]}... | {payment.order_id} | {payment.status.value} | {payment.created_at}")
            
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")

def cleanup_logs(app, days=30):
    """Clean up old logs"""
    print(f"🧹 Cleaning up logs older than {days} days...")
    
    try:
        with app.app_context():
            count = cleanup_old_logs(days)
            print(f"✅ Cleaned up {count} old log entries")
    except Exception as e:
        print(f"❌ Error cleaning up logs: {e}")

def test_connection(app):
    """Test database connection"""
    print("🧪 Testing database connection...")
    
    try:
        with app.app_context():
            # Try a simple query
            from sqlalchemy import text
            result = db.session.execute(text("SELECT 1")).fetchone()
            if result[0] == 1:
                print("✅ Database connection successful!")
                return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    return False

def reset_database(app):
    """Reset database (drop and recreate all tables)"""
    print("⚠️  WARNING: This will delete ALL data!")
    confirm = input("Type 'yes' to confirm: ")
    
    if confirm.lower() != 'yes':
        print("❌ Operation cancelled")
        return
    
    print("🗑️  Dropping all tables...")
    try:
        with app.app_context():
            db.drop_all()
            print("✅ All tables dropped")
            
            print("🏗️  Creating tables...")
            db.create_all()
            print("✅ Tables recreated successfully!")
            
    except Exception as e:
        print(f"❌ Error resetting database: {e}")

def export_payments(app, filename=None):
    """Export payments to JSON file"""
    if not filename:
        filename = f"payments_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    print(f"📤 Exporting payments to {filename}...")
    
    try:
        import json
        
        with app.app_context():
            payments = db.session.query(Payment).all()
            
            export_data = {
                'export_date': datetime.now().isoformat(),
                'total_payments': len(payments),
                'payments': [payment.to_dict(include_internal=True) for payment in payments]
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            print(f"✅ Exported {len(payments)} payments to {filename}")
            
    except Exception as e:
        print(f"❌ Error exporting payments: {e}")

def main():
    parser = argparse.ArgumentParser(description='Database management for TRON Payment Monitor')
    parser.add_argument('command', choices=[
        'create-tables', 'stats', 'test', 'reset', 'cleanup-logs', 'export'
    ], help='Command to execute')
    parser.add_argument('--days', type=int, default=30, help='Days to keep for cleanup (default: 30)')
    parser.add_argument('--file', type=str, help='Filename for export')
    
    args = parser.parse_args()
    
    # Setup Flask app
    app = setup_app()
    
    if args.command == 'create-tables':
        create_db_tables(app)
    elif args.command == 'stats':
        show_stats(app)
    elif args.command == 'test':
        test_connection(app)
    elif args.command == 'reset':
        reset_database(app)
    elif args.command == 'cleanup-logs':
        cleanup_logs(app, args.days)
    elif args.command == 'export':
        export_payments(app, args.file)

if __name__ == '__main__':
    main()
