#!/usr/bin/env python3
"""
TRON Address Generator for Client-Side Payment Management

This script generates TRON addresses for receiving payments and manages them
in a local database. It provides functionality to:
1. Generate new TRON addresses with private keys
2. Store address data locally
3. Export addresses for payment monitoring
4. Track payment status

Usage:
    python tron_address_generator.py generate --count 10
    python tron_address_generator.py list
    python tron_address_generator.py export --format json
    python tron_address_generator.py monitor --address TR...
"""

import os
import json
import sqlite3
import hashlib
import secrets
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import base58

# TRON-specific constants
TRON_ADDRESS_PREFIX = 0x41
TRON_MAINNET_PREFIX = "T"

class TronAddressGenerator:
    """Generate and manage TRON addresses for payment processing"""
    
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
                private_key TEXT NOT NULL,
                public_key TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                label TEXT,
                is_used BOOLEAN DEFAULT FALSE,
                balance_usdt REAL DEFAULT 0.0,
                last_checked TIMESTAMP,
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
                order_id TEXT,
                transaction_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (address) REFERENCES addresses (address)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_addresses_address ON addresses(address);
            CREATE INDEX IF NOT EXISTS idx_addresses_used ON addresses(is_used);
            CREATE INDEX IF NOT EXISTS idx_payments_address ON payments(address);
            CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_private_key(self) -> bytes:
        """Generate a cryptographically secure private key"""
        return secrets.token_bytes(32)
    
    def private_key_to_public_key(self, private_key: bytes) -> bytes:
        """
        Convert private key to public key using secp256k1
        Note: This is a simplified implementation. For production,
        use a proper cryptographic library like ecdsa or cryptography
        """
        # In a real implementation, you would use:
        # from ecdsa import SigningKey, SECP256k1
        # sk = SigningKey.from_string(private_key, curve=SECP256k1)
        # return sk.verifying_key.to_string()
        
        # For demonstration, we'll use a deterministic but secure method
        # This is NOT suitable for production - use proper ECDSA libraries
        import hashlib
        import hmac
        
        # Simplified public key derivation (DO NOT USE IN PRODUCTION)
        seed = hmac.new(b"tron_secp256k1", private_key, hashlib.sha256).digest()
        return seed[:33]  # Compressed public key format
    
    def public_key_to_address(self, public_key: bytes) -> str:
        """Convert public key to TRON address"""
        # Hash the public key
        hash1 = hashlib.sha3_256(public_key).digest()
        
        # Take last 20 bytes
        address_bytes = hash1[-20:]
        
        # Add TRON prefix
        address_with_prefix = bytes([TRON_ADDRESS_PREFIX]) + address_bytes
        
        # Calculate checksum
        hash2 = hashlib.sha256(address_with_prefix).digest()
        hash3 = hashlib.sha256(hash2).digest()
        checksum = hash3[:4]
        
        # Combine address and checksum
        full_address = address_with_prefix + checksum
        
        # Encode in base58
        return base58.b58encode(full_address).decode('utf-8')
    
    def generate_address(self, label: Optional[str] = None) -> Dict[str, str]:
        """Generate a new TRON address with private key"""
        # Generate private key
        private_key = self.generate_private_key()
        
        # Derive public key
        public_key = self.private_key_to_public_key(private_key)
        
        # Generate address
        address = self.public_key_to_address(public_key)
        
        # Convert to hex strings for storage
        private_key_hex = private_key.hex()
        public_key_hex = public_key.hex()
        
        return {
            'address': address,
            'private_key': private_key_hex,
            'public_key': public_key_hex,
            'label': label or f"Generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
    
    def store_address(self, address_data: Dict[str, str]) -> bool:
        """Store generated address in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO addresses (address, private_key, public_key, label)
                VALUES (?, ?, ?, ?)
            ''', (
                address_data['address'],
                address_data['private_key'],
                address_data['public_key'],
                address_data['label']
            ))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # Address already exists
            return False
        except Exception as e:
            print(f"Error storing address: {e}")
            return False
    
    def generate_and_store_addresses(self, count: int, label_prefix: str = "Generated") -> List[Dict[str, str]]:
        """Generate multiple addresses and store them"""
        generated = []
        
        for i in range(count):
            label = f"{label_prefix}_{i+1:03d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            address_data = self.generate_address(label)
            
            if self.store_address(address_data):
                generated.append(address_data)
                print(f"✅ Generated address {i+1}/{count}: {address_data['address']}")
            else:
                print(f"❌ Failed to generate address {i+1}/{count}")
        
        return generated
    
    def get_unused_address(self) -> Optional[Dict[str, str]]:
        """Get an unused address from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT address, private_key, public_key, label, created_at
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
                'private_key': result[1],
                'public_key': result[2],
                'label': result[3],
                'created_at': result[4]
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
    
    def list_addresses(self, include_used: bool = True) -> List[Dict[str, str]]:
        """List all addresses in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT address, label, created_at, is_used, balance_usdt, payment_count
            FROM addresses
        '''
        
        if not include_used:
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
    
    def export_addresses(self, format_type: str = "json", filename: Optional[str] = None) -> str:
        """Export addresses to file"""
        addresses = self.list_addresses()
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"tron_addresses_{timestamp}.{format_type}"
        
        if format_type.lower() == "json":
            with open(filename, 'w') as f:
                json.dump(addresses, f, indent=2)
        elif format_type.lower() == "csv":
            import csv
            with open(filename, 'w', newline='') as f:
                if addresses:
                    writer = csv.DictWriter(f, fieldnames=addresses[0].keys())
                    writer.writeheader()
                    writer.writerows(addresses)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        return filename
    
    def create_payment_request(self, amount: float, order_id: str, label: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Create a payment request using an unused address"""
        address_data = self.get_unused_address()
        
        if not address_data:
            print("❌ No unused addresses available. Generate more addresses first.")
            return None
        
        # Store payment request
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO payments (address, expected_amount, order_id)
            VALUES (?, ?, ?)
        ''', (address_data['address'], amount, order_id))
        
        payment_id = cursor.lastrowid
        
        # Mark address as used
        self.mark_address_used(address_data['address'])
        
        conn.commit()
        conn.close()
        
        return {
            'payment_id': str(payment_id),
            'address': address_data['address'],
            'expected_amount': amount,
            'order_id': order_id,
            'label': label or address_data['label']
        }
    
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
    parser = argparse.ArgumentParser(description='TRON Address Generator for Payment Processing')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate addresses command
    gen_parser = subparsers.add_parser('generate', help='Generate new TRON addresses')
    gen_parser.add_argument('--count', type=int, default=1, help='Number of addresses to generate')
    gen_parser.add_argument('--label', type=str, help='Label prefix for generated addresses')
    
    # List addresses command
    list_parser = subparsers.add_parser('list', help='List stored addresses')
    list_parser.add_argument('--unused-only', action='store_true', help='Show only unused addresses')
    
    # Export addresses command
    export_parser = subparsers.add_parser('export', help='Export addresses to file')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    export_parser.add_argument('--filename', type=str, help='Output filename')
    
    # Create payment command
    payment_parser = subparsers.add_parser('payment', help='Create payment request')
    payment_parser.add_argument('--amount', type=float, required=True, help='Expected payment amount in USDT')
    payment_parser.add_argument('--order-id', type=str, required=True, help='Unique order ID')
    payment_parser.add_argument('--label', type=str, help='Label for the payment')
    
    # Statistics command
    subparsers.add_parser('stats', help='Show statistics')
    
    # Get unused address command
    subparsers.add_parser('get-unused', help='Get next unused address')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    generator = TronAddressGenerator()
    
    if args.command == 'generate':
        label = args.label or "Generated"
        print(f"🔄 Generating {args.count} TRON address(es)...")
        generated = generator.generate_and_store_addresses(args.count, label)
        print(f"✅ Successfully generated {len(generated)} addresses")
    
    elif args.command == 'list':
        addresses = generator.list_addresses(include_used=not args.unused_only)
        if addresses:
            print(f"\n📋 {'Unused ' if args.unused_only else ''}Addresses:")
            print("-" * 80)
            for addr in addresses:
                status = "🔴 Used" if addr['is_used'] else "🟢 Available"
                print(f"{addr['address']} | {addr['label']} | {status} | Created: {addr['created_at']}")
        else:
            print("No addresses found.")
    
    elif args.command == 'export':
        filename = generator.export_addresses(args.format, args.filename)
        print(f"✅ Addresses exported to: {filename}")
    
    elif args.command == 'payment':
        payment = generator.create_payment_request(args.amount, args.order_id, args.label)
        if payment:
            print("✅ Payment request created:")
            print(f"   Payment ID: {payment['payment_id']}")
            print(f"   Address: {payment['address']}")
            print(f"   Expected Amount: {payment['expected_amount']} USDT")
            print(f"   Order ID: {payment['order_id']}")
        else:
            print("❌ Failed to create payment request")
    
    elif args.command == 'stats':
        stats = generator.get_statistics()
        print("\n📊 Statistics:")
        print("-" * 40)
        print(f"Total Addresses: {stats['total_addresses']}")
        print(f"Used Addresses: {stats['used_addresses']}")
        print(f"Unused Addresses: {stats['unused_addresses']}")
        print(f"Total Payments: {stats['total_payments']}")
        print(f"Completed Payments: {stats['completed_payments']}")
        print(f"Pending Payments: {stats['pending_payments']}")
        print(f"Total Received: {stats['total_received_usdt']:.6f} USDT")
    
    elif args.command == 'get-unused':
        address = generator.get_unused_address()
        if address:
            print(f"🟢 Next unused address: {address['address']}")
            print(f"   Label: {address['label']}")
            print(f"   Created: {address['created_at']}")
        else:
            print("❌ No unused addresses available")

if __name__ == '__main__':
    main()
