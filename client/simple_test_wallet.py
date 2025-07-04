#!/usr/bin/env python3
"""
Simple test wallet creation
"""

import sqlite3

# Create database and table
conn = sqlite3.connect("test_wallet.db")
cursor = conn.cursor()

# Create table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS wallets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        address TEXT UNIQUE NOT NULL,
        private_key TEXT NOT NULL,
        mnemonic_phrase TEXT,
        derivation_path TEXT,
        label TEXT
    )
''')

# Insert test wallet
cursor.execute('''
    INSERT INTO wallets (
        address, private_key, mnemonic_phrase, derivation_path, label
    ) VALUES (?, ?, ?, ?, ?)
''', (
    'TR8NY6G729eHHx4vP9DoRg1iqAEBzq8hpK',
    'f8258721551e0ce5ab143eabc55d58f4e78668f43f3c9e84d7bedae026a1eab9',
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
    "m/44'/195'/0'/0/0",
    "Test Wallet"
))

conn.commit()
wallet_id = cursor.lastrowid
conn.close()

print(f"Test wallet created with ID: {wallet_id}")
print("Verifying...")

# Verify
conn = sqlite3.connect("test_wallet.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM wallets WHERE id = ?", (wallet_id,))
result = cursor.fetchone()
conn.close()

if result:
    print(f"✅ Verification successful:")
    print(f"   ID: {result[0]}")
    print(f"   Address: {result[1]}")
    print(f"   Mnemonic: {result[3]}")
    print(f"   Derivation: {result[4]}")
else:
    print("❌ Verification failed")
