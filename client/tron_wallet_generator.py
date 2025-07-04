#!/usr/bin/env python3
"""
Enhanced TRON Wallet Generator with Mnemonic Phrases and QR Codes

This script generates TRON wallets with:
1. Mnemonic phrases (BIP39)
2. HD wallet derivation (BIP44)
3. QR codes for easy wallet import
4. Backup files with all wallet information

Usage:
    python tron_wallet_generator.py generate --count 5
    python tron_wallet_generator.py generate-hd --mnemonic "your mnemonic phrase" --count 10
    python tron_wallet_generator.py export-qr --wallet-id 123
    python tron_wallet_generator.py backup --format json
"""

import os
import json
import sqlite3
import hashlib
import secrets
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import base64

# Try to import optional dependencies
try:
    import qrcode
    from PIL import Image, ImageDraw, ImageFont
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

try:
    from mnemonic import Mnemonic
    MNEMONIC_AVAILABLE = True
except ImportError:
    MNEMONIC_AVAILABLE = False

try:
    from hdwallet import HDWallet
    from hdwallet.symbols import TRX
    HD_WALLET_AVAILABLE = True
except ImportError:
    HD_WALLET_AVAILABLE = False

try:
    import base58
    from ecdsa import SigningKey, SECP256k1
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

class TronWalletGenerator:
    """Advanced TRON wallet generator with mnemonic and QR support"""
    
    def __init__(self, db_path: str = "tron_wallets.db"):
        self.db_path = db_path
        self.init_database()
        
        # Initialize mnemonic generator
        if MNEMONIC_AVAILABLE:
            self.mnemo = Mnemonic("english")
        
        # Check dependencies
        self.check_dependencies()
    
    def check_dependencies(self):
        """Check which features are available based on installed packages"""
        missing = []
        
        if not QR_AVAILABLE:
            missing.append("qrcode[pil] and Pillow (for QR code generation)")
        
        if not MNEMONIC_AVAILABLE:
            missing.append("mnemonic (for BIP39 mnemonic phrases)")
        
        if not HD_WALLET_AVAILABLE:
            missing.append("hdwallet (for HD wallet derivation)")
        
        if not CRYPTO_AVAILABLE:
            missing.append("base58 and ecdsa (for cryptographic operations)")
        
        if missing:
            print("⚠️  Some features are not available. Install missing packages:")
            for package in missing:
                print(f"   - {package}")
            print("\n   Run: pip install -r requirements.txt")
    
    def init_database(self):
        """Initialize SQLite database for storing wallets"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT UNIQUE NOT NULL,
                private_key TEXT NOT NULL,
                public_key TEXT NOT NULL,
                mnemonic TEXT,
                derivation_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                label TEXT,
                is_used BOOLEAN DEFAULT FALSE,
                balance_usdt REAL DEFAULT 0.0,
                qr_code_path TEXT,
                backup_exported BOOLEAN DEFAULT FALSE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mnemonic_seeds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mnemonic TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                wallet_count INTEGER DEFAULT 0,
                label TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_wallets_address ON wallets(address)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_wallets_used ON wallets(is_used)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_wallets_mnemonic ON wallets(mnemonic)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mnemonic_seeds_mnemonic ON mnemonic_seeds(mnemonic)')
        
        conn.commit()
        conn.close()
    
    def generate_mnemonic(self, strength: int = 128) -> str:
        """Generate a new BIP39 mnemonic phrase"""
        if not MNEMONIC_AVAILABLE:
            # Fallback to simple word generation
            words = [
                "abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract",
                "absurd", "abuse", "access", "accident", "account", "accuse", "achieve", "acid",
                "acoustic", "acquire", "across", "act", "action", "actor", "actress", "actual"
            ]
            import random
            return " ".join(random.choices(words, k=12))
        
        return self.mnemo.generate(strength=strength)
    
    def validate_mnemonic(self, mnemonic: str) -> bool:
        """Validate a BIP39 mnemonic phrase"""
        if not MNEMONIC_AVAILABLE:
            # Basic validation - check word count
            words = mnemonic.strip().split()
            return len(words) in [12, 15, 18, 21, 24]
        
        return self.mnemo.check(mnemonic)
    
    def derive_wallet_from_mnemonic(self, mnemonic: str, index: int = 0) -> Dict[str, str]:
        """Derive a TRON wallet from mnemonic using HD derivation"""
        if not HD_WALLET_AVAILABLE:
            # Fallback: Use mnemonic as seed for deterministic generation
            seed = hashlib.pbkdf2_hmac('sha512', mnemonic.encode(), b'tron', 2048, 64)
            index_bytes = index.to_bytes(4, 'big')
            wallet_seed = hashlib.sha256(seed + index_bytes).digest()[:32]
            
            return self.generate_wallet_from_seed(wallet_seed, mnemonic, f"m/44'/195'/{index}'/0/0")
        
        # Use proper HD wallet derivation
        hdwallet = HDWallet(symbol=TRX)
        hdwallet.from_mnemonic(mnemonic=mnemonic)
        
        # TRON derivation path: m/44'/195'/0'/0/{index}
        derivation_path = f"m/44'/195'/0'/0/{index}"
        hdwallet.from_path(path=derivation_path)
        
        return {
            'address': hdwallet.p2pkh_address(),
            'private_key': hdwallet.private_key(),
            'public_key': hdwallet.public_key(),
            'mnemonic': mnemonic,
            'derivation_path': derivation_path
        }
    
    def generate_wallet_from_seed(self, seed: bytes, mnemonic: str, derivation_path: str) -> Dict[str, str]:
        """Generate wallet from seed (fallback method)"""
        if not CRYPTO_AVAILABLE:
            # Demo mode - generate fake data
            fake_address = f"T{''.join(secrets.choice('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz') for _ in range(33))}"
            return {
                'address': fake_address,
                'private_key': seed.hex(),
                'public_key': hashlib.sha256(seed).hexdigest(),
                'mnemonic': mnemonic,
                'derivation_path': derivation_path
            }
        
        # Generate using ECDSA
        private_key = seed
        sk = SigningKey.from_string(private_key, curve=SECP256k1)
        public_key = sk.verifying_key.to_string("compressed")
        
        # Convert to TRON address (simplified)
        address_hash = hashlib.sha3_256(public_key[1:]).digest()[-20:]
        address_with_prefix = bytes([0x41]) + address_hash
        
        # Calculate checksum
        hash1 = hashlib.sha256(address_with_prefix).digest()
        hash2 = hashlib.sha256(hash1).digest()
        checksum = hash2[:4]
        
        # Encode address
        full_address = address_with_prefix + checksum
        address = base58.b58encode(full_address).decode('utf-8')
        
        return {
            'address': address,
            'private_key': private_key.hex(),
            'public_key': public_key.hex(),
            'mnemonic': mnemonic,
            'derivation_path': derivation_path
        }
    
    def generate_wallet_with_mnemonic(self, mnemonic: Optional[str] = None, index: int = 0, label: Optional[str] = None) -> Dict[str, str]:
        """Generate a wallet with mnemonic phrase"""
        if mnemonic is None:
            mnemonic = self.generate_mnemonic()
        
        if not self.validate_mnemonic(mnemonic):
            raise ValueError("Invalid mnemonic phrase")
        
        wallet_data = self.derive_wallet_from_mnemonic(mnemonic, index)
        wallet_data['label'] = label or f"HD_Wallet_{index}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return wallet_data
    
    def store_wallet(self, wallet_data: Dict[str, str]) -> bool:
        """Store wallet in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Store mnemonic if new
            if wallet_data.get('mnemonic'):
                cursor.execute('''
                    INSERT OR IGNORE INTO mnemonic_seeds (mnemonic, label)
                    VALUES (?, ?)
                ''', (wallet_data['mnemonic'], wallet_data.get('label', 'Generated')))
                
                # Update wallet count for this mnemonic
                cursor.execute('''
                    UPDATE mnemonic_seeds 
                    SET wallet_count = wallet_count + 1 
                    WHERE mnemonic = ?
                ''', (wallet_data['mnemonic'],))
            
            # Store wallet
            cursor.execute('''
                INSERT INTO wallets (address, private_key, public_key, mnemonic, derivation_path, label)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                wallet_data['address'],
                wallet_data['private_key'],
                wallet_data['public_key'],
                wallet_data.get('mnemonic'),
                wallet_data.get('derivation_path'),
                wallet_data['label']
            ))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            print(f"⚠️  Wallet already exists: {wallet_data['address']}")
            return False
        except Exception as e:
            print(f"❌ Error storing wallet: {e}")
            return False
    
    def generate_qr_code(self, wallet_id: int, output_dir: str = "qr_codes") -> Optional[str]:
        """Generate QR code for wallet import"""
        if not QR_AVAILABLE:
            print("❌ QR code generation not available. Install: pip install qrcode[pil] Pillow")
            return None
        
        # Get wallet data
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT address, private_key, mnemonic, derivation_path, label
            FROM wallets WHERE id = ?
        ''', (wallet_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            print(f"❌ Wallet ID {wallet_id} not found")
            return None
        
        address, private_key, mnemonic, derivation_path, label = result
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate multiple QR codes
        qr_files = []
        
        # 1. Address QR Code
        qr_address = qrcode.QRCode(version=1, box_size=10, border=5)
        qr_address.add_data(address)
        qr_address.make(fit=True)
        
        img_address = qr_address.make_image(fill_color="black", back_color="white")
        address_file = os.path.join(output_dir, f"wallet_{wallet_id}_address.png")
        img_address.save(address_file)
        qr_files.append(address_file)
        
        # 2. Private Key QR Code (for wallet import)
        qr_private = qrcode.QRCode(version=1, box_size=10, border=5)
        qr_private.add_data(private_key)
        qr_private.make(fit=True)
        
        img_private = qr_private.make_image(fill_color="black", back_color="white")
        private_file = os.path.join(output_dir, f"wallet_{wallet_id}_private_key.png")
        img_private.save(private_file)
        qr_files.append(private_file)
        
        # 3. Mnemonic QR Code (if available)
        if mnemonic:
            qr_mnemonic = qrcode.QRCode(version=1, box_size=10, border=5)
            qr_mnemonic.add_data(mnemonic)
            qr_mnemonic.make(fit=True)
            
            img_mnemonic = qr_mnemonic.make_image(fill_color="black", back_color="white")
            mnemonic_file = os.path.join(output_dir, f"wallet_{wallet_id}_mnemonic.png")
            img_mnemonic.save(mnemonic_file)
            qr_files.append(mnemonic_file)
        
        # Update database with QR code path
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE wallets SET qr_code_path = ? WHERE id = ?
        ''', (output_dir, wallet_id))
        conn.commit()
        conn.close()
        
        print(f"✅ Generated QR codes for wallet {wallet_id}:")
        for qr_file in qr_files:
            print(f"   - {qr_file}")
        
        return output_dir
    
    def export_wallet_backup(self, wallet_ids: Optional[List[int]] = None, format_type: str = "json") -> str:
        """Export wallet backup file"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if wallet_ids:
            placeholders = ','.join('?' * len(wallet_ids))
            query = f'''
                SELECT id, address, private_key, public_key, mnemonic, derivation_path, 
                       label, created_at, is_used, balance_usdt
                FROM wallets WHERE id IN ({placeholders})
            '''
            cursor.execute(query, wallet_ids)
        else:
            cursor.execute('''
                SELECT id, address, private_key, public_key, mnemonic, derivation_path, 
                       label, created_at, is_used, balance_usdt
                FROM wallets
            ''')
        
        results = cursor.fetchall()
        conn.close()
        
        wallets = []
        for result in results:
            wallets.append({
                'id': result[0],
                'address': result[1],
                'private_key': result[2],
                'public_key': result[3],
                'mnemonic': result[4],
                'derivation_path': result[5],
                'label': result[6],
                'created_at': result[7],
                'is_used': bool(result[8]),
                'balance_usdt': result[9]
            })
        
        # Create backup data
        backup_data = {
            'backup_info': {
                'created_at': datetime.now().isoformat(),
                'wallet_count': len(wallets),
                'format_version': '1.0'
            },
            'wallets': wallets
        }
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"tron_wallet_backup_{timestamp}.{format_type}"
        
        if format_type.lower() == "json":
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        # Mark wallets as backed up
        if wallet_ids:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(wallet_ids))
            cursor.execute(f'''
                UPDATE wallets SET backup_exported = TRUE WHERE id IN ({placeholders})
            ''', wallet_ids)
            conn.commit()
            conn.close()
        
        return filename
    
    def list_wallets(self, unused_only: bool = False) -> List[Dict[str, str]]:
        """List wallets with their information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT id, address, label, mnemonic, derivation_path, created_at, 
                   is_used, balance_usdt, qr_code_path, backup_exported
            FROM wallets
        '''
        
        if unused_only:
            query += ' WHERE is_used = FALSE'
        
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        
        wallets = []
        for result in results:
            wallets.append({
                'id': result[0],
                'address': result[1],
                'label': result[2],
                'mnemonic': result[3][:20] + "..." if result[3] else None,
                'derivation_path': result[4],
                'created_at': result[5],
                'is_used': bool(result[6]),
                'balance_usdt': result[7],
                'qr_code_path': result[8],
                'backup_exported': bool(result[9])
            })
        
        return wallets

def main():
    parser = argparse.ArgumentParser(
        description='Advanced TRON Wallet Generator with Mnemonic and QR Support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate wallets with new mnemonics
  python tron_wallet_generator.py generate --count 5

  # Generate wallets from existing mnemonic
  python tron_wallet_generator.py generate-hd --mnemonic "word1 word2 ... word12" --count 10

  # Generate QR codes for a wallet
  python tron_wallet_generator.py export-qr --wallet-id 123

  # Create backup file
  python tron_wallet_generator.py backup --format json

  # List all wallets
  python tron_wallet_generator.py list
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate wallets with new mnemonics
    gen_parser = subparsers.add_parser('generate', help='Generate wallets with new mnemonics')
    gen_parser.add_argument('--count', type=int, default=1, help='Number of wallets to generate')
    gen_parser.add_argument('--label', type=str, default='Generated', help='Label prefix for wallets')
    
    # Generate from existing mnemonic
    hd_parser = subparsers.add_parser('generate-hd', help='Generate HD wallets from mnemonic')
    hd_parser.add_argument('--mnemonic', required=True, help='BIP39 mnemonic phrase')
    hd_parser.add_argument('--count', type=int, default=1, help='Number of wallets to derive')
    hd_parser.add_argument('--start-index', type=int, default=0, help='Starting derivation index')
    hd_parser.add_argument('--label', type=str, help='Label prefix for wallets')
    
    # Export QR codes
    qr_parser = subparsers.add_parser('export-qr', help='Generate QR codes for wallet')
    qr_parser.add_argument('--wallet-id', type=int, required=True, help='Wallet ID to generate QR for')
    qr_parser.add_argument('--output-dir', type=str, default='qr_codes', help='Output directory for QR codes')
    
    # Backup wallets
    backup_parser = subparsers.add_parser('backup', help='Export wallet backup')
    backup_parser.add_argument('--wallet-ids', type=int, nargs='+', help='Specific wallet IDs to backup')
    backup_parser.add_argument('--format', choices=['json'], default='json', help='Backup format')
    
    # List wallets
    list_parser = subparsers.add_parser('list', help='List wallets')
    list_parser.add_argument('--unused-only', action='store_true', help='Show only unused wallets')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    generator = TronWalletGenerator()
    
    if args.command == 'generate':
        print(f"🔄 Generating {args.count} wallet(s) with new mnemonics...")
        
        for i in range(args.count):
            try:
                wallet_data = generator.generate_wallet_with_mnemonic(
                    label=f"{args.label}_{i+1:03d}"
                )
                
                if generator.store_wallet(wallet_data):
                    print(f"✅ Generated wallet {i+1}/{args.count}:")
                    print(f"   Address: {wallet_data['address']}")
                    print(f"   Mnemonic: {wallet_data['mnemonic'][:50]}...")
                else:
                    print(f"❌ Failed to store wallet {i+1}/{args.count}")
            except Exception as e:
                print(f"❌ Error generating wallet {i+1}: {e}")
    
    elif args.command == 'generate-hd':
        if not generator.validate_mnemonic(args.mnemonic):
            print("❌ Invalid mnemonic phrase")
            return
        
        print(f"🔄 Generating {args.count} HD wallets from mnemonic...")
        
        for i in range(args.count):
            index = args.start_index + i
            try:
                wallet_data = generator.generate_wallet_with_mnemonic(
                    mnemonic=args.mnemonic,
                    index=index,
                    label=f"{args.label or 'HD'}_{index:03d}"
                )
                
                if generator.store_wallet(wallet_data):
                    print(f"✅ Generated HD wallet {i+1}/{args.count}:")
                    print(f"   Address: {wallet_data['address']}")
                    print(f"   Path: {wallet_data['derivation_path']}")
                else:
                    print(f"❌ Failed to store wallet {i+1}/{args.count}")
            except Exception as e:
                print(f"❌ Error generating HD wallet {i+1}: {e}")
    
    elif args.command == 'export-qr':
        output_dir = generator.generate_qr_code(args.wallet_id, args.output_dir)
        if not output_dir:
            exit(1)
    
    elif args.command == 'backup':
        filename = generator.export_wallet_backup(args.wallet_ids, args.format)
        print(f"✅ Wallet backup exported to: {filename}")
    
    elif args.command == 'list':
        wallets = generator.list_wallets(args.unused_only)
        if wallets:
            print(f"\n📋 {'Unused ' if args.unused_only else ''}Wallets:")
            print("-" * 100)
            for wallet in wallets:
                status = "🔴 Used" if wallet['is_used'] else "🟢 Available"
                qr_status = "📱 QR" if wallet['qr_code_path'] else "❌ No QR"
                backup_status = "💾 Backed up" if wallet['backup_exported'] else "⚠️ Not backed up"
                
                print(f"ID: {wallet['id']} | {wallet['address']} | {wallet['label']}")
                print(f"   {status} | {qr_status} | {backup_status}")
                if wallet['mnemonic']:
                    print(f"   Mnemonic: {wallet['mnemonic']}")
                print()
        else:
            print("No wallets found.")

if __name__ == '__main__':
    main()
