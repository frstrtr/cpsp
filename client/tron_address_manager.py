#!/usr/bin/env python3
"""
TRON Address Manager for Client-Side Payment Processing

This script manages TRON addresses for receiving payments. It provides:
1. Address generation and storage
2. Payment request creation
3. Integration with the main payment monitoring service

Note: This is a simplified version for demonstration. For production use,
implement proper ECDSA cryptography with libraries like 'ecdsa' or 'tronpy'.
"""

import json
import sqlite3
import hashlib
import secrets
import argparse
import random
import string
from datetime import datetime
from typing import Dict, List, Optional

class TronAddressManager:
    """Manage TRON addresses for payment processing"""
    
    def __init__(self, db_path: str = "tron_addresses.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for storing addresses"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT UNIQUE NOT NULL,
                label TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_used BOOLEAN DEFAULT FALSE,
                balance_usdt REAL DEFAULT 0.0,
                payment_count INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL,
                expected_amount REAL NOT NULL,
                received_amount REAL DEFAULT 0.0,
                status TEXT DEFAULT 'pending',
                order_id TEXT UNIQUE,
                transaction_hash TEXT,
                callback_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (address) REFERENCES addresses (address)
            )
        ''')
        
        # Create indexes separately
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_addresses_address ON addresses(address)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_addresses_used ON addresses(is_used)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)')
        
        conn.commit()
        conn.close()
    
    def generate_demo_address(self, seed: Optional[str] = None) -> str:
        """
        Generate a demo TRON address for testing purposes.
        
        WARNING: This is for demonstration only! In production, use proper
        cryptographic libraries like 'tronpy' or implement real ECDSA.
        """
        if seed:
            # Use seed for deterministic generation (for testing)
            hash_obj = hashlib.sha256(seed.encode())
            random.seed(int(hash_obj.hexdigest()[:8], 16))
        
        # TRON addresses start with 'T' and are 34 characters long
        # This is a demo format - real addresses use base58 encoding
        chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
        random_part = ''.join(random.choices(chars, k=33))
        return f"T{random_part}"
    
    def add_real_address(self, address: str, label: Optional[str] = None) -> bool:
        """Add a real TRON address that you control"""
        if not self.validate_address_format(address):
            print(f"❌ Invalid TRON address format: {address}")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO addresses (address, label)
                VALUES (?, ?)
            ''', (address, label or f"Real_{datetime.now().strftime('%Y%m%d_%H%M%S')}"))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            print(f"⚠️  Address already exists: {address}")
            return False
        except Exception as e:
            print(f"❌ Error storing address: {e}")
            return False
    
    def validate_address_format(self, address: str) -> bool:
        """Basic TRON address format validation"""
        return (
            isinstance(address, str) and
            address.startswith('T') and
            len(address) == 34 and
            all(c in '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz' 
                for c in address[1:])
        )
    
    def create_demo_addresses(self, count: int, label_prefix: str = "Demo") -> List[str]:
        """Create multiple demo addresses for testing"""
        created = []
        
        for i in range(count):
            label = f"{label_prefix}_{i+1:03d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            seed = f"{label}_{secrets.token_hex(8)}"
            address = self.generate_demo_address(seed)
            
            if self.add_real_address(address, label):
                created.append(address)
                print(f"✅ Created demo address {i+1}/{count}: {address}")
            else:
                print(f"❌ Failed to create demo address {i+1}/{count}")
        
        return created
    
    def get_unused_address(self) -> Optional[Dict[str, str]]:
        """Get an unused address from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT address, label, created_at
            FROM addresses
            WHERE is_used = FALSE
            ORDER BY created_at ASC
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'address': result[0],
                'label': result[1],
                'created_at': result[2]
            }
        return None
    
    def mark_address_used(self, address: str) -> bool:
        """Mark an address as used"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE addresses
            SET is_used = TRUE
            WHERE address = ?
        ''', (address,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def create_payment_request(self, 
                             amount: float, 
                             order_id: str, 
                             callback_url: Optional[str] = None, 
                             notes: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Create a payment request using an unused address"""
        # Validate inputs
        if amount <= 0:
            print("❌ Amount must be positive")
            return None
        
        if not order_id or not order_id.strip():
            print("❌ Order ID is required")
            return None
        
        # Get unused address
        address_data = self.get_unused_address()
        if not address_data:
            print("❌ No unused addresses available. Add more addresses first.")
            return None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create payment record
            cursor.execute('''
                INSERT INTO payments (address, expected_amount, order_id, callback_url, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (address_data['address'], amount, order_id.strip(), callback_url, notes))
            
            payment_id = cursor.lastrowid
            
            # Mark address as used
            self.mark_address_used(address_data['address'])
            
            conn.commit()
            conn.close()
            
            return {
                'payment_id': str(payment_id),
                'address': address_data['address'],
                'expected_amount': str(amount),
                'order_id': order_id.strip(),
                'callback_url': callback_url or '',
                'label': address_data['label'],
                'created_at': datetime.now().isoformat()
            }
            
        except sqlite3.IntegrityError:
            print(f"❌ Order ID already exists: {order_id}")
            return None
        except Exception as e:
            print(f"❌ Error creating payment request: {e}")
            return None
    
    def list_addresses(self, unused_only: bool = False) -> List[Dict[str, str]]:
        """List addresses with their status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT address, label, created_at, is_used, balance_usdt, payment_count
            FROM addresses
        '''
        
        if unused_only:
            query += ' WHERE is_used = FALSE'
        
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        
        addresses = []
        for result in results:
            addresses.append({
                'address': result[0],
                'label': result[1],
                'created_at': result[2],
                'is_used': bool(result[3]),
                'balance_usdt': result[4],
                'payment_count': result[5]
            })
        
        return addresses
    
    def list_payments(self, status: Optional[str] = None) -> List[Dict[str, str]]:
        """List payment requests"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT p.id, p.address, p.expected_amount, p.received_amount, 
                   p.status, p.order_id, p.transaction_hash, p.callback_url,
                   p.created_at, p.completed_at, p.notes, a.label
            FROM payments p
            LEFT JOIN addresses a ON p.address = a.address
        '''
        
        if status:
            query += ' WHERE p.status = ?'
            cursor.execute(query, (status,))
        else:
            cursor.execute(query)
        
        query += ' ORDER BY p.created_at DESC'
        
        results = cursor.fetchall()
        conn.close()
        
        payments = []
        for result in results:
            payments.append({
                'payment_id': str(result[0]),
                'address': result[1],
                'expected_amount': result[2],
                'received_amount': result[3],
                'status': result[4],
                'order_id': result[5],
                'transaction_hash': result[6] or '',
                'callback_url': result[7] or '',
                'created_at': result[8],
                'completed_at': result[9] or '',
                'notes': result[10] or '',
                'address_label': result[11] or ''
            })
        
        return payments
    
    def export_for_monitoring_service(self, filename: Optional[str] = None) -> str:
        """Export pending payments in format for the main monitoring service"""
        pending_payments = self.list_payments('pending')
        
        # Convert to format expected by main service
        monitoring_requests = []
        for payment in pending_payments:
            monitoring_requests.append({
                'wallet_address': payment['address'],
                'expected_amount_usdt': float(payment['expected_amount']),
                'callback_url': payment['callback_url'] or 'https://example.com/webhook',
                'order_id': payment['order_id']
            })
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"monitoring_requests_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(monitoring_requests, f, indent=2)
        
        return filename
    
    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about addresses and payments"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Address statistics
        cursor.execute('SELECT COUNT(*) FROM addresses')
        total_addresses = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM addresses WHERE is_used = TRUE')
        used_addresses = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM addresses WHERE is_used = FALSE')
        unused_addresses = cursor.fetchone()[0]
        
        # Payment statistics
        cursor.execute('SELECT COUNT(*) FROM payments')
        total_payments = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM payments WHERE status = "completed"')
        completed_payments = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM payments WHERE status = "pending"')
        pending_payments = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(received_amount) FROM payments WHERE status = "completed"')
        total_received = cursor.fetchone()[0] or 0.0
        
        conn.close()
        
        return {
            'total_addresses': total_addresses,
            'used_addresses': used_addresses,
            'unused_addresses': unused_addresses,
            'total_payments': total_payments,
            'completed_payments': completed_payments,
            'pending_payments': pending_payments,
            'total_received_usdt': total_received
        }

def main():
    parser = argparse.ArgumentParser(
        description='TRON Address Manager for Payment Processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create demo addresses for testing
  python tron_address_manager.py create-demo --count 5

  # Add a real address you control
  python tron_address_manager.py add-real TGj1Ej1qRzL9feLTLhjwgxXF4Ct6GTWg2U --label "My Wallet"

  # Create a payment request
  python tron_address_manager.py payment --amount 25.50 --order-id "ORDER123" --callback "https://mysite.com/webhook"

  # List all addresses
  python tron_address_manager.py list-addresses

  # Export pending payments for monitoring service
  python tron_address_manager.py export-monitoring
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create demo addresses
    demo_parser = subparsers.add_parser('create-demo', help='Create demo addresses for testing')
    demo_parser.add_argument('--count', type=int, default=1, help='Number of demo addresses to create')
    demo_parser.add_argument('--label', type=str, default='Demo', help='Label prefix for addresses')
    
    # Add real address
    real_parser = subparsers.add_parser('add-real', help='Add a real TRON address you control')
    real_parser.add_argument('address', help='TRON address (starts with T, 34 characters)')
    real_parser.add_argument('--label', type=str, help='Label for the address')
    
    # Create payment request
    payment_parser = subparsers.add_parser('payment', help='Create payment request')
    payment_parser.add_argument('--amount', type=float, required=True, help='Expected payment amount in USDT')
    payment_parser.add_argument('--order-id', type=str, required=True, help='Unique order ID')
    payment_parser.add_argument('--callback', type=str, help='Callback URL for webhook notifications')
    payment_parser.add_argument('--notes', type=str, help='Additional notes for the payment')
    
    # List addresses
    list_addr_parser = subparsers.add_parser('list-addresses', help='List stored addresses')
    list_addr_parser.add_argument('--unused-only', action='store_true', help='Show only unused addresses')
    
    # List payments
    list_pay_parser = subparsers.add_parser('list-payments', help='List payment requests')
    list_pay_parser.add_argument('--status', choices=['pending', 'completed', 'failed'], help='Filter by status')
    
    # Export for monitoring
    export_parser = subparsers.add_parser('export-monitoring', help='Export pending payments for monitoring service')
    export_parser.add_argument('--filename', type=str, help='Output filename')
    
    # Statistics
    subparsers.add_parser('stats', help='Show statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = TronAddressManager()
    
    if args.command == 'create-demo':
        print(f"🔄 Creating {args.count} demo address(es)...")
        created = manager.create_demo_addresses(args.count, args.label)
        print(f"✅ Successfully created {len(created)} demo addresses")
        print("⚠️  WARNING: Demo addresses are for testing only!")
    
    elif args.command == 'add-real':
        if manager.add_real_address(args.address, args.label):
            print(f"✅ Added real address: {args.address}")
        else:
            print(f"❌ Failed to add address: {args.address}")
    
    elif args.command == 'payment':
        payment = manager.create_payment_request(
            args.amount, args.order_id, args.callback, args.notes
        )
        if payment:
            print("✅ Payment request created:")
            print(f"   Payment ID: {payment['payment_id']}")
            print(f"   Address: {payment['address']}")
            print(f"   Expected Amount: {payment['expected_amount']} USDT")
            print(f"   Order ID: {payment['order_id']}")
            if payment['callback_url']:
                print(f"   Callback URL: {payment['callback_url']}")
        else:
            print("❌ Failed to create payment request")
    
    elif args.command == 'list-addresses':
        addresses = manager.list_addresses(args.unused_only)
        if addresses:
            print(f"\n📋 {'Unused ' if args.unused_only else 'All '}Addresses:")
            print("-" * 80)
            for addr in addresses:
                status = "🔴 Used" if addr['is_used'] else "🟢 Available"
                print(f"{addr['address']} | {addr['label']} | {status}")
        else:
            print("No addresses found.")
    
    elif args.command == 'list-payments':
        payments = manager.list_payments(args.status)
        if payments:
            print(f"\n💳 {'All' if not args.status else args.status.title()} Payments:")
            print("-" * 100)
            for payment in payments:
                print(f"ID: {payment['payment_id']} | Order: {payment['order_id']} | "
                      f"Amount: {payment['expected_amount']} USDT | Status: {payment['status']}")
        else:
            print("No payments found.")
    
    elif args.command == 'export-monitoring':
        filename = manager.export_for_monitoring_service(args.filename)
        print(f"✅ Pending payments exported to: {filename}")
        print("You can now use this file with the main monitoring service.")
    
    elif args.command == 'stats':
        stats = manager.get_statistics()
        print("\n📊 Statistics:")
        print("-" * 40)
        print(f"Total Addresses: {stats['total_addresses']}")
        print(f"Used Addresses: {stats['used_addresses']}")
        print(f"Unused Addresses: {stats['unused_addresses']}")
        print(f"Total Payments: {stats['total_payments']}")
        print(f"Completed Payments: {stats['completed_payments']}")
        print(f"Pending Payments: {stats['pending_payments']}")
        print(f"Total Received: {stats['total_received_usdt']:.6f} USDT")

if __name__ == '__main__':
    main()
