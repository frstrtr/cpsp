#!/usr/bin/env python3
"""
Simple TRON Wallet Import/Export Utility

This utility creates wallet import files and simple text-based QR codes
for importing wallets into TRON applications.
"""

import json
import sqlite3
import hashlib
import secrets
import argparse
from datetime import datetime
from typing import Dict, List, Optional

class TronWalletImportExport:
    """Simple wallet import/export without heavy dependencies"""
    
    def __init__(self, db_path: str = "tron_wallets_simple.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT UNIQUE NOT NULL,
                private_key TEXT NOT NULL,
                mnemonic_words TEXT,
                derivation_info TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                label TEXT,
                is_used BOOLEAN DEFAULT FALSE,
                exported BOOLEAN DEFAULT FALSE
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_wallets_address ON wallets(address)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_wallets_used ON wallets(is_used)')
        
        conn.commit()
        conn.close()
    
    def generate_simple_mnemonic(self, word_count: int = 12) -> str:
        """Generate a simple mnemonic-like phrase (not BIP39 compliant)"""
        # Simple word list for demo purposes
        words = [
            "apple", "brave", "chair", "dance", "eagle", "frame", "grace", "house",
            "image", "judge", "knife", "light", "mouse", "noise", "ocean", "piano",
            "queen", "river", "stone", "table", "uncle", "voice", "water", "xerus",
            "young", "zebra", "angel", "bench", "cloud", "dream", "earth", "flame",
            "glass", "heart", "ivory", "jewel", "kite", "lemon", "magic", "night",
            "olive", "peace", "quest", "radio", "smile", "tiger", "unity", "valley",
            "wheat", "xenon", "yield", "zephyr", "bread", "coral", "delta", "ember"
        ]
        
        # Generate deterministic but random-looking words
        seed = secrets.token_bytes(32)
        selected_words = []
        
        for i in range(word_count):
            # Use seed + index to deterministically select words
            word_seed = hashlib.sha256(seed + i.to_bytes(4, 'big')).digest()
            word_index = int.from_bytes(word_seed[:4], 'big') % len(words)
            selected_words.append(words[word_index])
        
        return " ".join(selected_words)
    
    def generate_demo_wallet_from_mnemonic(self, mnemonic: str, index: int = 0) -> Dict[str, str]:
        """Generate a demo wallet from mnemonic phrase"""
        # Create deterministic seed from mnemonic + index
        seed_input = f"{mnemonic}:{index}".encode('utf-8')
        seed = hashlib.pbkdf2_hmac('sha256', seed_input, b'tron_demo', 10000, 32)
        
        # Generate private key from seed
        private_key = seed.hex()
        
        # Generate demo address (not cryptographically valid)
        address_seed = hashlib.sha256(seed + b'address').digest()
        # TRON addresses are base58, start with 'T', 34 chars
        chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
        address_chars = []
        
        for i in range(33):
            byte_index = i % len(address_seed)
            char_index = address_seed[byte_index] % len(chars)
            address_chars.append(chars[char_index])
        
        address = 'T' + ''.join(address_chars)
        
        return {
            'address': address,
            'private_key': private_key,
            'mnemonic': mnemonic,
            'derivation_path': f"m/44'/195'/0'/0/{index}"
        }
    
    def store_wallet(self, wallet_data: Dict[str, str], label: str = None) -> bool:
        """Store wallet in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO wallets (address, private_key, mnemonic_words, derivation_info, label)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                wallet_data['address'],
                wallet_data['private_key'],
                wallet_data.get('mnemonic'),
                wallet_data.get('derivation_path'),
                label or f"Wallet_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            ))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"Error storing wallet: {e}")
            return False
    
    def create_text_qr(self, data: str, label: str = "QR Code") -> str:
        """Create a simple text-based QR code representation"""
        # This is a simplified visual representation
        lines = [
            f"=== {label} ===",
            "█████████████████████████",
            "█                       █",
            f"█  {data[:21]}  █",
            "█                       █",
            "█████████████████████████",
            "",
            f"Data: {data}",
            "",
            "To scan: Use any QR scanner app",
            "To import: Copy the data above"
        ]
        
        return "\n".join(lines)
    
    def export_wallet_for_import(self, wallet_id: int, output_dir: str = "wallet_exports") -> Optional[str]:
        """Export wallet in formats suitable for import"""
        import os
        
        # Get wallet data
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT address, private_key, mnemonic_words, derivation_info, label
            FROM wallets WHERE id = ?
        ''', (wallet_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            print(f"Wallet ID {wallet_id} not found")
            return None
        
        address, private_key, mnemonic, derivation_path, label = result
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Create export data
        export_data = {
            'wallet_info': {
                'label': label,
                'address': address,
                'created_at': datetime.now().isoformat(),
                'export_format': 'tron_wallet_v1'
            },
            'import_data': {
                'address': address,
                'private_key': private_key,
                'mnemonic': mnemonic,
                'derivation_path': derivation_path
            },
            'import_instructions': {
                'tronlink': [
                    "1. Open TronLink wallet",
                    "2. Go to Settings > Import Wallet",
                    "3. Choose 'Private Key' or 'Mnemonic'",
                    "4. Enter the corresponding data below"
                ],
                'trust_wallet': [
                    "1. Open Trust Wallet",
                    "2. Tap '+' to add wallet",
                    "3. Select 'I already have a wallet'",
                    "4. Choose 'TRON (TRX)'",
                    "5. Enter mnemonic phrase"
                ]
            }
        }
        
        # Save JSON export
        json_file = os.path.join(output_dir, f"wallet_{wallet_id}_export.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
        
        # Create text file with QR-like representations
        text_file = os.path.join(output_dir, f"wallet_{wallet_id}_import.txt")
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(f"TRON Wallet Import Data\n")
            f.write(f"=" * 50 + "\n\n")
            f.write(f"Wallet Label: {label}\n")
            f.write(f"Address: {address}\n\n")
            
            # Private Key section
            f.write(self.create_text_qr(private_key, "Private Key"))
            f.write("\n\n")
            
            # Mnemonic section (if available)
            if mnemonic:
                f.write(self.create_text_qr(mnemonic, "Mnemonic Phrase"))
                f.write("\n\n")
            
            # Address section
            f.write(self.create_text_qr(address, "Wallet Address"))
            f.write("\n\n")
            
            # Instructions
            f.write("IMPORT INSTRUCTIONS:\n")
            f.write("-" * 20 + "\n\n")
            f.write("For TronLink:\n")
            for i, instruction in enumerate(export_data['import_instructions']['tronlink'], 1):
                f.write(f"{i}. {instruction}\n")
            
            f.write("\nFor Trust Wallet:\n")
            for i, instruction in enumerate(export_data['import_instructions']['trust_wallet'], 1):
                f.write(f"{i}. {instruction}\n")
            
            f.write(f"\nIMPORTANT SECURITY NOTES:\n")
            f.write(f"- Keep this file secure and private\n")
            f.write(f"- Never share your private key or mnemonic\n")
            f.write(f"- Delete this file after importing\n")
            f.write(f"- This is for demo purposes only\n")
        
        # Update database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE wallets SET exported = TRUE WHERE id = ?', (wallet_id,))
        conn.commit()
        conn.close()
        
        print(f"✅ Wallet export created:")
        print(f"   JSON: {json_file}")
        print(f"   Text: {text_file}")
        
        return output_dir
    
    def create_batch_wallets(self, count: int, use_same_mnemonic: bool = False, label_prefix: str = "Demo") -> List[int]:
        """Create multiple wallets for testing"""
        created_ids = []
        base_mnemonic = None
        
        if use_same_mnemonic:
            base_mnemonic = self.generate_simple_mnemonic()
            print(f"Using base mnemonic: {base_mnemonic[:30]}...")
        
        for i in range(count):
            if use_same_mnemonic:
                wallet_data = self.generate_demo_wallet_from_mnemonic(base_mnemonic, i)
            else:
                mnemonic = self.generate_simple_mnemonic()
                wallet_data = self.generate_demo_wallet_from_mnemonic(mnemonic, 0)
            
            label = f"{label_prefix}_{i+1:03d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if self.store_wallet(wallet_data, label):
                # Get the ID of the just-created wallet
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM wallets WHERE address = ?', (wallet_data['address'],))
                wallet_id = cursor.fetchone()[0]
                conn.close()
                
                created_ids.append(wallet_id)
                print(f"✅ Created wallet {i+1}/{count}: ID {wallet_id} - {wallet_data['address']}")
            else:
                print(f"❌ Failed to create wallet {i+1}/{count}")
        
        return created_ids
    
    def list_wallets(self) -> List[Dict[str, str]]:
        """List all wallets"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, address, label, mnemonic_words, created_at, is_used, exported
            FROM wallets ORDER BY created_at DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        wallets = []
        for result in results:
            wallets.append({
                'id': result[0],
                'address': result[1],
                'label': result[2],
                'mnemonic_preview': result[3][:30] + "..." if result[3] else "None",
                'created_at': result[4],
                'is_used': bool(result[5]),
                'exported': bool(result[6])
            })
        
        return wallets

def main():
    parser = argparse.ArgumentParser(
        description='Simple TRON Wallet Import/Export Utility',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create demo wallets
  python wallet_import_export.py create --count 5

  # Create wallets from same mnemonic (HD-like)
  python wallet_import_export.py create --count 10 --same-mnemonic

  # Export wallet for import into other apps
  python wallet_import_export.py export --wallet-id 123

  # List all wallets
  python wallet_import_export.py list
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create wallets
    create_parser = subparsers.add_parser('create', help='Create demo wallets')
    create_parser.add_argument('--count', type=int, default=1, help='Number of wallets to create')
    create_parser.add_argument('--same-mnemonic', action='store_true', help='Use same mnemonic for all wallets (HD-like)')
    create_parser.add_argument('--label', type=str, default='Demo', help='Label prefix for wallets')
    
    # Export wallet
    export_parser = subparsers.add_parser('export', help='Export wallet for import')
    export_parser.add_argument('--wallet-id', type=int, required=True, help='Wallet ID to export')
    export_parser.add_argument('--output-dir', type=str, default='wallet_exports', help='Output directory')
    
    # List wallets
    subparsers.add_parser('list', help='List all wallets')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    utility = TronWalletImportExport()
    
    if args.command == 'create':
        print(f"🔄 Creating {args.count} demo wallet(s)...")
        created_ids = utility.create_batch_wallets(args.count, args.same_mnemonic, args.label)
        print(f"✅ Created {len(created_ids)} wallets")
        print(f"💡 Use 'python {__file__} export --wallet-id <ID>' to create import files")
    
    elif args.command == 'export':
        output_dir = utility.export_wallet_for_import(args.wallet_id, args.output_dir)
        if output_dir:
            print(f"💡 Import the wallet using the files in {output_dir}")
        else:
            exit(1)
    
    elif args.command == 'list':
        wallets = utility.list_wallets()
        if wallets:
            print(f"\n📋 Wallets ({len(wallets)} total):")
            print("-" * 100)
            for wallet in wallets:
                status = "🔴 Used" if wallet['is_used'] else "🟢 Available"
                export_status = "📁 Exported" if wallet['exported'] else "⚪ Not exported"
                print(f"ID: {wallet['id']:3d} | {wallet['address']} | {wallet['label']}")
                print(f"      {status} | {export_status} | Mnemonic: {wallet['mnemonic_preview']}")
                print()
        else:
            print("No wallets found.")

if __name__ == '__main__':
    main()
