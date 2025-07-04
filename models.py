"""
Database models for TRON USDT Payment Monitor
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import enum

db = SQLAlchemy()

class PaymentStatus(enum.Enum):
    """Enum for payment status"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"

class Payment(db.Model):
    """
    Model for storing payment watch requests
    """
    __tablename__ = 'payments'
    
    # Primary key
    id = db.Column(db.String(36), primary_key=True)  # UUID
    
    # Payment details
    wallet_address = db.Column(db.String(34), nullable=False, index=True)
    expected_amount_usdt = db.Column(db.Numeric(precision=18, scale=6), nullable=False)
    callback_url = db.Column(db.Text, nullable=False)
    order_id = db.Column(db.String(100), nullable=False, unique=True, index=True)
    
    # Status tracking
    status = db.Column(db.Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING, index=True)
    transaction_hash = db.Column(db.String(64), nullable=True, index=True)
    received_amount_usdt = db.Column(db.Numeric(precision=18, scale=6), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    last_checked_timestamp = db.Column(db.BigInteger, nullable=False)  # Milliseconds since epoch
    
    # Metadata
    callback_attempts = db.Column(db.Integer, nullable=False, default=0)
    last_callback_attempt = db.Column(db.DateTime, nullable=True)
    callback_success = db.Column(db.Boolean, nullable=False, default=False)
    
    def __repr__(self):
        return f'<Payment {self.id}: {self.order_id} - {self.status.value}>'
    
    def to_dict(self, include_internal=False):
        """
        Convert payment to dictionary
        :param include_internal: Include internal fields like callback_url
        """
        data = {
            'id': self.id,
            'wallet_address': self.wallet_address,
            'expected_amount_usdt': float(self.expected_amount_usdt),
            'order_id': self.order_id,
            'status': self.status.value,
            'transaction_hash': self.transaction_hash,
            'received_amount_usdt': float(self.received_amount_usdt) if self.received_amount_usdt else None,
            'created_at': self.created_at.timestamp(),
            'completed_at': self.completed_at.timestamp() if self.completed_at else None,
        }
        
        if include_internal:
            data.update({
                'callback_url': self.callback_url,
                'last_checked_timestamp': self.last_checked_timestamp,
                'callback_attempts': self.callback_attempts,
                'last_callback_attempt': self.last_callback_attempt.timestamp() if self.last_callback_attempt else None,
                'callback_success': self.callback_success,
            })
        
        return data
    
    @classmethod
    def get_pending_payments(cls):
        """Get all pending payments"""
        return cls.query.filter_by(status=PaymentStatus.PENDING).all()
    
    @classmethod
    def get_expired_payments(cls, max_age_seconds=86400):  # 24 hours default
        """Get payments that should be expired"""
        cutoff_time = datetime.utcnow().timestamp() - max_age_seconds
        return cls.query.filter(
            cls.status == PaymentStatus.PENDING,
            cls.created_at < datetime.utcfromtimestamp(cutoff_time)
        ).all()
    
    def mark_completed(self, transaction_hash, received_amount):
        """Mark payment as completed"""
        self.status = PaymentStatus.COMPLETED
        self.transaction_hash = transaction_hash
        self.received_amount_usdt = received_amount
        self.completed_at = datetime.utcnow()
    
    def mark_expired(self):
        """Mark payment as expired"""
        self.status = PaymentStatus.EXPIRED
    
    def mark_failed(self):
        """Mark payment as failed"""
        self.status = PaymentStatus.FAILED
    
    def increment_callback_attempt(self):
        """Increment callback attempt counter"""
        self.callback_attempts += 1
        self.last_callback_attempt = datetime.utcnow()
    
    def mark_callback_success(self):
        """Mark callback as successful"""
        self.callback_success = True

class PaymentLog(db.Model):
    """
    Model for logging payment events and debugging
    """
    __tablename__ = 'payment_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.String(36), db.ForeignKey('payments.id'), nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)  # created, checked, completed, failed, etc.
    message = db.Column(db.Text, nullable=True)
    event_metadata = db.Column(db.JSON, nullable=True)  # Store additional JSON data
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relationship
    payment = db.relationship('Payment', backref=db.backref('logs', lazy=True, cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<PaymentLog {self.id}: {self.payment_id} - {self.event_type}>'
    
    @classmethod
    def log_event(cls, payment_id, event_type, message=None, event_metadata=None):
        """Create a new log entry"""
        log = cls(
            payment_id=payment_id,
            event_type=event_type,
            message=message,
            event_metadata=event_metadata
        )
        db.session.add(log)
        return log
