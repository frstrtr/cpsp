"""
Database configuration and utilities
"""

import os
from flask import Flask
from flask_migrate import Migrate

def init_database(app: Flask):
    """
    Initialize database with the Flask application
    """
    # Database configuration
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        # Default to local PostgreSQL for development
        database_url = 'postgresql://postgres:password@localhost:5432/tron_payments'
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'pool_recycle': 120,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # Initialize extensions
    from models import db
    db.init_app(app)
    
    # Initialize migrations
    migrate = Migrate(app, db)
    
    return db, migrate

def create_tables(app: Flask):
    """
    Create all database tables
    """
    from models import db
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

def get_database_stats():
    """
    Get database statistics
    """
    from models import db, Payment, PaymentStatus
    
    try:
        total_payments = db.session.query(Payment).count()
        pending_payments = db.session.query(Payment).filter_by(status=PaymentStatus.PENDING).count()
        completed_payments = db.session.query(Payment).filter_by(status=PaymentStatus.COMPLETED).count()
        failed_payments = db.session.query(Payment).filter_by(status=PaymentStatus.FAILED).count()
        expired_payments = db.session.query(Payment).filter_by(status=PaymentStatus.EXPIRED).count()
        
        return {
            'total_payments': total_payments,
            'pending_payments': pending_payments,
            'completed_payments': completed_payments,
            'failed_payments': failed_payments,
            'expired_payments': expired_payments
        }
    except Exception as e:
        return {'error': str(e)}

def cleanup_old_logs(days_to_keep=30):
    """
    Clean up old payment logs to prevent database bloat
    """
    from models import db, PaymentLog
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    
    try:
        old_logs = db.session.query(PaymentLog).filter(
            PaymentLog.created_at < cutoff_date
        ).all()
        
        count = len(old_logs)
        for log in old_logs:
            db.session.delete(log)
        
        db.session.commit()
        return count
    except Exception as e:
        db.session.rollback()
        raise e
