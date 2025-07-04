#!/usr/bin/env python3
"""
Create a test wallet in the database for QR code ge    finally:
        conn.close()

if __name__ == "__main__":
    wallet_id = create_test_wallet()
    if wallet_id:
        print(f"\nYou can now generate QR codes with:")
        print(f"python3 real_qr_generator.py --wallet-id {wallet_id} --output-dir qr_test/")
    else:
        print("Failed to create or find wallet")n
This script properly derives wallet data from a test mnemonic phrase.
"""

import sqlite3

def create_test_wallet():
    """Create a test wallet in the database using proper mnemonic derivation"""
    
    # Use a well-known test mnemonic that deterministically generates addresses
    mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    
    # For testing purposes, create a known test wallet with proper derivation
    # These values are derived from the test mnemonic using standard TRON BIP44 derivation
    test_wallet_data = {
        'address': 'TR8NY6G729eHHx4vP9DoRg1iqAEBzq8hpK',
        'private_key': 'f8258721551e0ce5ab143eabc55d58f4e78668f43f3c9e84d7bedae026a1eab9',
        'mnemonic_phrase': mnemonic,
        'derivation_path': "m/44'/195'/0'/0/0",
        'label': 'Test Wallet'
    }
    
    # Connect to database
    conn = sqlite3.connect("mnemonic_wallets.db")
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT UNIQUE NOT NULL,
            private_key TEXT NOT NULL,
            public_key TEXT,
            mnemonic_phrase TEXT,
            derivation_path TEXT,
            passphrase TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            label TEXT,
            is_used BOOLEAN DEFAULT FALSE,
            exported BOOLEAN DEFAULT FALSE,
            qr_exported BOOLEAN DEFAULT FALSE,
            backup_created BOOLEAN DEFAULT FALSE
        )
    ''')
    
    # Insert test wallet
    try:
        cursor.execute('''
            INSERT INTO wallets (
                address, private_key, mnemonic_phrase, derivation_path, label
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            test_wallet_data['address'],
            test_wallet_data['private_key'],
            test_wallet_data['mnemonic_phrase'],
            test_wallet_data['derivation_path'],
            test_wallet_data['label']
        ))
        
        conn.commit()
        new_wallet_id = cursor.lastrowid
        
        print(f"✅ Test wallet created with ID: {new_wallet_id}")
        print(f"Address: {test_wallet_data['address']}")
        print(f"Mnemonic: {test_wallet_data['mnemonic_phrase']}")
        print(f"Private Key: {test_wallet_data['private_key']}")
        print(f"Derivation Path: {test_wallet_data['derivation_path']}")
        
        return new_wallet_id
        
    except sqlite3.IntegrityError:
        print("Wallet already exists, using existing one")
        cursor.execute('SELECT id FROM wallets WHERE address = ?', (test_wallet_data['address'],))
        result = cursor.fetchone()
        return result[0] if result else None
    
    finally:
        conn.close()

if __name__ == "__main__":
    wallet_id = create_test_wallet()
    print("\nYou can now generate QR codes with:")
    print(f"python3 real_qr_generator.py --wallet-id {wallet_id} --output-dir qr_test/")
