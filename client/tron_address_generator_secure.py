#!/usr/bin/env python3
"""
Enhanced TRON Address Generator with Real Cryptography

This version uses proper ECDSA cryptography for production-grade security.
"""

import os
import json
import sqlite3
import hashlib
import secrets
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

try:
    import base58
    from ecdsa import SigningKey, SECP256k1
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️  WARNING: Production cryptography libraries not available!")
    print("   Install with: pip install base58 ecdsa")
    print("   Falling back to demonstration mode (NOT SECURE)")

class TronAddressGeneratorSecure:
    """Production-grade TRON address generator with proper cryptography"""
    
    def __init__(self, db_path: str = "tron_addresses.db"):
        self.db_path = db_path
        if not CRYPTO_AVAILABLE:
            print("❌ Cannot run in secure mode without cryptography libraries")
            raise ImportError("Required libraries: base58, ecdsa")
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
                payment_count INTEGER DEFAULT 0,
                derivation_path TEXT,
                checksum TEXT
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
                callback_url TEXT,
                notes TEXT,
                FOREIGN KEY (address) REFERENCES addresses (address)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_addresses_address ON addresses(address);
            CREATE INDEX IF NOT EXISTS idx_addresses_used ON addresses(is_used);
            CREATE INDEX IF NOT EXISTS idx_payments_address ON payments(address);
            CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
            CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id);
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_private_key(self) -> bytes:
        """Generate a cryptographically secure private key"""
        return secrets.token_bytes(32)
    
    def private_key_to_public_key(self, private_key: bytes) -> bytes:
        """Convert private key to public key using proper ECDSA"""
        sk = SigningKey.from_string(private_key, curve=SECP256k1)
        vk = sk.verifying_key
        return vk.to_string("compressed")
    
    def public_key_to_address(self, public_key: bytes) -> str:
        """Convert public key to TRON address"""
        # Use Keccak-256 hash (same as Ethereum)
        import sha3
        keccak = sha3.keccak_256()
        keccak.update(public_key[1:])  # Remove the 0x04 prefix for uncompressed keys
        hash_result = keccak.digest()
        
        # Take last 20 bytes
        address_bytes = hash_result[-20:]
        
        # Add TRON prefix (0x41)
        address_with_prefix = bytes([0x41]) + address_bytes
        
        # Calculate checksum
        hash1 = hashlib.sha256(address_with_prefix).digest()
        hash2 = hashlib.sha256(hash1).digest()
        checksum = hash2[:4]
        
        # Combine address and checksum
        full_address = address_with_prefix + checksum
        
        # Encode in base58
        return base58.b58encode(full_address).decode('utf-8')
    
    def generate_address(self, label: Optional[str] = None) -> Dict[str, str]:
        """Generate a new TRON address with private key"""
        # Generate private key
        private_key = self.generate_private_key()
        
        # Derive public key using proper ECDSA
        public_key = self.private_key_to_public_key(private_key)
        
        # Generate address
        address = self.public_key_to_address(public_key)
        
        # Convert to hex strings for storage
        private_key_hex = private_key.hex()
        public_key_hex = public_key.hex()
        
        # Generate checksum for verification
        checksum = hashlib.sha256(f"{address}{private_key_hex}".encode()).hexdigest()[:16]
        
        return {
            'address': address,
            'private_key': private_key_hex,
            'public_key': public_key_hex,
            'checksum': checksum,
            'label': label or f"Generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
    
    def validate_address(self, address: str) -> bool:
        """Validate TRON address format and checksum"""
        try:
            if not address.startswith('T') or len(address) != 34:
                return False
            
            # Decode base58
            decoded = base58.b58decode(address)
            if len(decoded) != 25:
                return False
            
            # Verify checksum
            address_part = decoded[:-4]
            checksum_part = decoded[-4:]
            
            hash1 = hashlib.sha256(address_part).digest()
            hash2 = hashlib.sha256(hash1).digest()
            expected_checksum = hash2[:4]
            
            return checksum_part == expected_checksum
        except:
            return False
    
    def store_address(self, address_data: Dict[str, str]) -> bool:
        """Store generated address in database"""
        try:
            # Validate address before storing
            if not self.validate_address(address_data['address']):
                print(f"❌ Invalid address format: {address_data['address']}")
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO addresses (address, private_key, public_key, label, checksum)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                address_data['address'],
                address_data['private_key'],
                address_data['public_key'],
                address_data['label'],
                address_data['checksum']
            ))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            print(f"⚠️  Address already exists: {address_data['address']}")
            return False
        except Exception as e:
            print(f"❌ Error storing address: {e}")
            return False
    
    def generate_and_store_addresses(self, count: int, label_prefix: str = "Generated") -> List[Dict[str, str]]:
        """Generate multiple addresses and store them"""
        generated = []
        print(f"🔄 Generating {count} secure TRON address(es)...")
        
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
            SELECT address, private_key, public_key, label, created_at, checksum
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
                'created_at': result[4],
                'checksum': result[5]
            }
        return None
    
    def create_payment_request(self, amount: float, order_id: str, callback_url: Optional[str] = None, label: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Create a payment request using an unused address"""
        address_data = self.get_unused_address()
        
        if not address_data:
            print("❌ No unused addresses available. Generate more addresses first.")
            return None
        
        # Store payment request
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO payments (address, expected_amount, order_id, callback_url, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (address_data['address'], amount, order_id, callback_url, label))
        
        payment_id = cursor.lastrowid
        
        # Mark address as used
        cursor.execute('''
            UPDATE addresses
            SET is_used = TRUE
            WHERE address = ?
        ''', (address_data['address'],))
        
        conn.commit()
        conn.close()
        
        return {
            'payment_id': str(payment_id),
            'address': address_data['address'],
            'expected_amount': amount,
            'order_id': order_id,
            'callback_url': callback_url,
            'label': label or address_data['label']
        }
    
    def export_for_monitoring(self, filename: Optional[str] = None) -> str:
        """Export addresses in format suitable for payment monitoring service"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.address, p.expected_amount, p.order_id, p.callback_url, 
                   a.label, p.created_at, p.id as payment_id
            FROM payments p
            JOIN addresses a ON p.address = a.address
            WHERE p.status = 'pending'
            ORDER BY p.created_at DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        monitoring_data = []
        for result in results:
            monitoring_data.append({
                'wallet_address': result[0],
                'expected_amount_usdt': result[1],
                'order_id': result[2],
                'callback_url': result[3] or 'https://example.com/webhook',
                'label': result[4],
                'created_at': result[5],
                'payment_id': result[6]
            })
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"pending_payments_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(monitoring_data, f, indent=2)
        
        return filename

# Add a simple fallback for demonstration
class SimpleTronAddressGenerator:
    """Simple demo version when crypto libraries aren't available"""
    
    def __init__(self, db_path: str = "tron_addresses_demo.db"):
        print("⚠️  WARNING: Running in DEMO mode - NOT suitable for production!")
        self.db_path = db_path
    
    def generate_demo_address(self) -> str:
        """Generate a demo TRON address (not cryptographically secure)"""
        # Generate a deterministic but random-looking demo address
        import random
        import string
        
        # Demo addresses always start with 'T' followed by 33 random characters
        chars = string.ascii_letters + string.digits
        random_part = ''.join(random.choices(chars, k=33))
        return f"T{random_part}"
    
    def create_demo_payment(self, amount: float, order_id: str) -> Dict[str, str]:
        """Create a demo payment for testing"""
        demo_address = self.generate_demo_address()
        return {
            'payment_id': f"demo_{order_id}",
            'address': demo_address,
            'expected_amount': amount,
            'order_id': order_id,
            'note': "DEMO MODE - Not a real address"
        }

def main():
    parser = argparse.ArgumentParser(description='TRON Address Generator for Payment Processing')
    parser.add_argument('--demo', action='store_true', help='Run in demo mode without crypto libraries')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate addresses command
    gen_parser = subparsers.add_parser('generate', help='Generate new TRON addresses')
    gen_parser.add_argument('--count', type=int, default=1, help='Number of addresses to generate')
    gen_parser.add_argument('--label', type=str, help='Label prefix for generated addresses')
    
    # Create payment command
    payment_parser = subparsers.add_parser('payment', help='Create payment request')
    payment_parser.add_argument('--amount', type=float, required=True, help='Expected payment amount in USDT')
    payment_parser.add_argument('--order-id', type=str, required=True, help='Unique order ID')
    payment_parser.add_argument('--callback', type=str, help='Callback URL for webhook')
    payment_parser.add_argument('--label', type=str, help='Label for the payment')
    
    # Export for monitoring
    export_parser = subparsers.add_parser('export-monitoring', help='Export pending payments for monitoring')
    export_parser.add_argument('--filename', type=str, help='Output filename')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Choose generator based on availability and user preference
    if args.demo or not CRYPTO_AVAILABLE:
        if args.command in ['generate', 'payment']:
            print("🔄 Running in demo mode...")
            demo_gen = SimpleTronAddressGenerator()
            
            if args.command == 'payment':
                result = demo_gen.create_demo_payment(args.amount, args.order_id)
                print("✅ Demo payment created:")
                for key, value in result.items():
                    print(f"   {key}: {value}")
            else:
                print("Demo mode only supports 'payment' command")
        else:
            print("❌ Demo mode has limited functionality")
        return
    
    # Use secure generator
    try:
        generator = TronAddressGeneratorSecure()
    except ImportError:
        print("❌ Cannot run secure mode. Install requirements:")
        print("   pip install -r requirements.txt")
        return
    
    if args.command == 'generate':
        label = args.label or "Generated"
        generated = generator.generate_and_store_addresses(args.count, label)
        print(f"✅ Successfully generated {len(generated)} secure addresses")
    
    elif args.command == 'payment':
        payment = generator.create_payment_request(args.amount, args.order_id, args.callback, args.label)
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
    
    elif args.command == 'export-monitoring':
        filename = generator.export_for_monitoring(args.filename)
        print(f"✅ Pending payments exported to: {filename}")

if __name__ == '__main__':
    main()
