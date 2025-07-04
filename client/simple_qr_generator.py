#!/usr/bin/env python3
"""
Simple QR Code Generator for TRON Wallets

This utility creates text-based QR codes that can be displayed in terminals
or converted to images using external tools. This is useful when PIL/qrcode
libraries are not available.

Usage:
    python simple_qr_generator.py --data "TGj1Ej1qRzL9feLTLhjwgxXF4Ct6GTWg2U"
    python simple_qr_generator.py --wallet-id 123
    python simple_qr_generator.py --mnemonic "word1 word2 word3..."
"""

import argparse
import json
import sqlite3
import sys
from typing import Dict, Optional

def create_text_qr(data: str, border: int = 2) -> str:
    """Create a simple text-based QR code representation"""
    # This is a simplified QR code representation using ASCII
    # For actual QR codes, use the qrcode library
    
    lines = []
    
    # Add border
    for _ in range(border):
        lines.append("█" * (len(data) + 2 * border + 4))
    
    # Add data representation
    lines.append("█" + " " * (border + 1) + "QR CODE" + " " * (border + 1) + "█")
    lines.append("█" + " " * (len(data) + 2 * border + 2) + "█")
    
    # Split data into chunks and create visual representation
    chunk_size = 20
    data_chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
    
    for chunk in data_chunks:
        padding = " " * (border + 1)
        line = "█" + padding + chunk.ljust(chunk_size) + padding + "█"
        lines.append(line)
    
    lines.append("█" + " " * (len(data) + 2 * border + 2) + "█")
    
    # Add border
    for _ in range(border):
        lines.append("█" * (len(data) + 2 * border + 4))
    
    return "\n".join(lines)

def create_wallet_qr_info(wallet: Dict) -> Dict[str, str]:
    """Create QR code data for different wallet components"""
    qr_data = {}
    
    # Address QR (for receiving payments)
    if wallet.get('address'):
        qr_data['address'] = wallet['address']
    
    # Private key QR (for importing wallet)
    if wallet.get('private_key'):
        qr_data['private_key'] = wallet['private_key']
    
    # Mnemonic QR (for wallet recovery)
    if wallet.get('mnemonic_phrase'):
        qr_data['mnemonic'] = wallet['mnemonic_phrase']
    
    # Complete wallet info JSON
    wallet_json = {
        'address': wallet.get('address'),
        'privateKey': wallet.get('private_key'),
        'mnemonic': wallet.get('mnemonic_phrase'),
        'derivationPath': wallet.get('derivation_path')
    }
    qr_data['complete'] = json.dumps(wallet_json, separators=(',', ':'))
    
    return qr_data

def get_wallet_from_db(wallet_id: int, db_path: str = "mnemonic_wallets.db") -> Optional[Dict]:
    """Get wallet data from database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM wallets WHERE id = ?', (wallet_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        
        conn.close()
        return None
    except sqlite3.Error:
        return None

def generate_import_urls(wallet: Dict) -> Dict[str, str]:
    """Generate URLs for importing wallet into different applications"""
    urls = {}
    
    # TronLink import URL format
    if wallet.get('private_key'):
        # Note: This is a hypothetical format - actual TronLink may use different schemes
        tronlink_url = f"tronlink://import?privateKey={wallet['private_key']}"
        urls['tronlink'] = tronlink_url
    
    # Generic wallet import format
    if wallet.get('address') and wallet.get('private_key'):
        generic_data = {
            'address': wallet['address'],
            'privateKey': wallet['private_key'],
            'network': 'mainnet'
        }
        urls['generic'] = f"wallet://import?data={json.dumps(generic_data)}"
    
    return urls

def main():
    parser = argparse.ArgumentParser(description='Simple QR Code Generator for TRON Wallets')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--data', help='Raw data to encode in QR code')
    group.add_argument('--wallet-id', type=int, help='Wallet ID from database')
    group.add_argument('--mnemonic', help='Mnemonic phrase to encode')
    group.add_argument('--address', help='TRON address to encode')
    
    parser.add_argument('--type', choices=['address', 'private_key', 'mnemonic', 'complete', 'all'],
                       default='all', help='Type of QR code to generate for wallet')
    parser.add_argument('--border', type=int, default=2, help='Border size for text QR code')
    parser.add_argument('--export-urls', action='store_true', help='Also show import URLs')
    parser.add_argument('--db-path', default='mnemonic_wallets.db', help='Database path')
    
    args = parser.parse_args()
    
    try:
        if args.data:
            # Generate QR for raw data
            print("Text QR Code:")
            print("=" * 50)
            print(create_text_qr(args.data, args.border))
            print("=" * 50)
            print(f"Data: {args.data}")
        
        elif args.wallet_id:
            # Generate QR for wallet from database
            wallet = get_wallet_from_db(args.wallet_id, args.db_path)
            if not wallet:
                print(f"Wallet {args.wallet_id} not found in database")
                return 1
            
            print(f"QR Codes for Wallet {args.wallet_id}")
            print("=" * 60)
            
            qr_data = create_wallet_qr_info(wallet)
            
            if args.type == 'all':
                types_to_show = qr_data.keys()
            else:
                types_to_show = [args.type] if args.type in qr_data else []
            
            for qr_type in types_to_show:
                if qr_type in qr_data:
                    print(f"\n{qr_type.upper()} QR Code:")
                    print("-" * 40)
                    print(create_text_qr(qr_data[qr_type], args.border))
                    print(f"Data: {qr_data[qr_type]}")
            
            if args.export_urls:
                urls = generate_import_urls(wallet)
                if urls:
                    print("\nImport URLs:")
                    print("-" * 40)
                    for url_type, url in urls.items():
                        print(f"{url_type}: {url}")
        
        elif args.mnemonic:
            # Generate QR for mnemonic phrase
            print("Mnemonic Phrase QR Code:")
            print("=" * 50)
            print(create_text_qr(args.mnemonic, args.border))
            print("=" * 50)
            print(f"Mnemonic: {args.mnemonic}")
        
        elif args.address:
            # Generate QR for TRON address
            print("TRON Address QR Code:")
            print("=" * 50)
            print(create_text_qr(args.address, args.border))
            print("=" * 50)
            print(f"Address: {args.address}")
        
        # Instructions for converting to actual QR codes
        print("\nTo create actual QR codes:")
        print("1. Install qrcode library: pip install qrcode[pil]")
        print("2. Use: python -m qrcode 'your_data_here' > qrcode.png")
        print("3. Or use online QR generators with the data above")
        
    except (ValueError, sqlite3.Error, json.JSONDecodeError) as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
