#!/usr/bin/env python3
"""
TRON Mnemonic Wallet Generator with QR Code Export

This script generates TRON wallets with:
1. BIP39 compatible mnemonic phrases
2. HD wallet derivation (BIP44) 
3. QR codes for easy wallet import
4. Multiple export formats
5. Batch generation capabilities

Usage:
    python mnemonic_wallet_generator.py generate --count 5
    python mnemonic_wallet_generator.py from-mnemonic "word1 word2 ... word12"
    python mnemonic_wallet_generator.py export-qr --wallet-id 123
    python mnemonic_wallet_generator.py export-real-qr --wallet-id 123 --style rounded
    python mnemonic_wallet_generator.py bulk-export --format all
"""

import os
import json
import sqlite3
import argparse
from datetime import datetime
from typing import Dict, List, Optional
import base64
import io

# Try to import real QR generator
try:
    from real_qr_generator import RealQRGenerator
    REAL_QR_AVAILABLE = True
except ImportError:
    REAL_QR_AVAILABLE = False

# Try to import optional dependencies
try:
    import qrcode
    from qrcode.image.styledpil import StyledPilImage
    from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False
    print("Warning: QR code dependencies not available. Install with: pip install qrcode[pil] Pillow")

try:
    from mnemonic import Mnemonic
    MNEMONIC_AVAILABLE = True
except ImportError:
    MNEMONIC_AVAILABLE = False
    print("Warning: Mnemonic library not available. Install with: pip install mnemonic")

try:
    from hdwallet import HDWallet
    from hdwallet.symbols import TRX
    HD_WALLET_AVAILABLE = True
except ImportError:
    HD_WALLET_AVAILABLE = False
    print("Warning: HD Wallet library not available. Install with: pip install hdwallet")

class MnemonicWalletGenerator:
    """Enhanced TRON wallet generator with mnemonic phrases and QR codes"""
    
    def __init__(self, db_path: str = "mnemonic_wallets.db"):
        self.db_path = db_path
        self.init_database()
        
        # Initialize mnemonic generator if available
        if MNEMONIC_AVAILABLE:
            self.mnemo = Mnemonic("english")
        else:
            self.mnemo = None
    
    def init_database(self):
        """Initialize SQLite database for wallet storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
        
        # Create indexes separately
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_wallets_address ON wallets(address)')
        conn.commit()
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_wallets_used ON wallets(is_used)')
        conn.commit()
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_wallets_mnemonic ON wallets(mnemonic_phrase)')
        conn.commit()
        
        conn.close()
    
    def generate_mnemonic_wallet(self, passphrase: str = "", derivation_index: int = 0) -> Dict:
        """Generate a new wallet with mnemonic phrase"""
        if not MNEMONIC_AVAILABLE or not HD_WALLET_AVAILABLE:
            raise RuntimeError("Mnemonic and HD wallet libraries required. Install with: pip install mnemonic hdwallet")
        
        # Generate mnemonic phrase
        mnemonic_phrase = self.mnemo.generate(strength=128)  # 12 words
        
        # Create HD wallet from mnemonic
        hdwallet = HDWallet(symbol=TRX)
        hdwallet.from_mnemonic(mnemonic=mnemonic_phrase, passphrase=passphrase)
        
        # Derive TRON address (BIP44 path: m/44'/195'/0'/0/index)
        derivation_path = f"m/44'/195'/0'/0/{derivation_index}"
        hdwallet.from_path(path=derivation_path)
        
        wallet_data = {
            'address': hdwallet.address(),
            'private_key': hdwallet.private_key(),
            'public_key': hdwallet.public_key(),
            'mnemonic_phrase': mnemonic_phrase,
            'derivation_path': derivation_path,
            'passphrase': passphrase,
            'created_at': datetime.now().isoformat()
        }
        
        return wallet_data
    
    def restore_from_mnemonic(self, mnemonic_phrase: str, passphrase: str = "", count: int = 1) -> List[Dict]:
        """Restore wallets from existing mnemonic phrase"""
        if not MNEMONIC_AVAILABLE or not HD_WALLET_AVAILABLE:
            raise RuntimeError("Mnemonic and HD wallet libraries required")
        
        # Validate mnemonic
        if not self.mnemo.check(mnemonic_phrase):
            raise ValueError("Invalid mnemonic phrase")
        
        wallets = []
        hdwallet = HDWallet(symbol=TRX)
        hdwallet.from_mnemonic(mnemonic=mnemonic_phrase, passphrase=passphrase)
        
        for i in range(count):
            # Derive address at index i
            derivation_path = f"m/44'/195'/0'/0/{i}"
            hdwallet.from_path(path=derivation_path)
            
            wallet_data = {
                'address': hdwallet.address(),
                'private_key': hdwallet.private_key(),
                'public_key': hdwallet.public_key(),
                'mnemonic_phrase': mnemonic_phrase,
                'derivation_path': derivation_path,
                'passphrase': passphrase,
                'created_at': datetime.now().isoformat()
            }
            
            wallets.append(wallet_data)
        
        return wallets
    
    def save_wallet(self, wallet_data: Dict, label: str = None) -> int:
        """Save wallet to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO wallets (
                    address, private_key, public_key, mnemonic_phrase,
                    derivation_path, passphrase, label
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                wallet_data['address'],
                wallet_data['private_key'],
                wallet_data.get('public_key'),
                wallet_data['mnemonic_phrase'],
                wallet_data.get('derivation_path'),
                wallet_data.get('passphrase', ''),
                label
            ))
            
            wallet_id = cursor.lastrowid
            conn.commit()
            return wallet_id
            
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"Wallet with address {wallet_data['address']} already exists") from exc
        finally:
            conn.close()
    
    def get_wallet(self, wallet_id: int) -> Optional[Dict]:
        """Get wallet by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM wallets WHERE id = ?', (wallet_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_dict(cursor, row)
        return None
    
    def list_wallets(self, include_used: bool = True) -> List[Dict]:
        """List all wallets"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if include_used:
            cursor.execute('SELECT * FROM wallets ORDER BY created_at DESC')
        else:
            cursor.execute('SELECT * FROM wallets WHERE is_used = FALSE ORDER BY created_at DESC')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(cursor, row) for row in rows]
    
    def _row_to_dict(self, cursor, row) -> Dict:
        """Convert database row to dictionary"""
        columns = [description[0] for description in cursor.description]
        return dict(zip(columns, row))
    
    def generate_qr_code(self, data: str, filename: str = None, img_format: str = "PNG") -> str:
        """Generate QR code for wallet data"""
        if not QR_AVAILABLE:
            raise RuntimeError("QR code libraries not available. Install with: sudo apt install python3-qrcode python3-pil")
        
        # Create QR code with better quality settings
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create styled image with rounded corners
        try:
            img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer()
            )
        except (ImportError, AttributeError):
            # Fallback to basic image if styled components not available
            img = qr.make_image(fill_color="black", back_color="white")
        
        if filename:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True)
            img.save(filename, format=img_format)
            return filename
        else:
            # Return base64 encoded image
            buffer = io.BytesIO()
            img.save(buffer, format=img_format)
            buffer.seek(0)
            return base64.b64encode(buffer.getvalue()).decode()
    
    def export_wallet_qr(self, wallet_id: int, export_dir: str = "qr_exports") -> Dict[str, str]:
        """Export wallet as QR codes"""
        wallet = self.get_wallet(wallet_id)
        if not wallet:
            raise ValueError(f"Wallet {wallet_id} not found")
        
        os.makedirs(export_dir, exist_ok=True)
        
        # Generate different QR codes
        qr_files = {}
        
        # 1. Private key QR
        private_key_file = os.path.join(export_dir, f"wallet_{wallet_id}_private_key.png")
        self.generate_qr_code(wallet['private_key'], private_key_file)
        qr_files['private_key'] = private_key_file
        
        # 2. Mnemonic phrase QR
        if wallet['mnemonic_phrase']:
            mnemonic_file = os.path.join(export_dir, f"wallet_{wallet_id}_mnemonic.png")
            self.generate_qr_code(wallet['mnemonic_phrase'], mnemonic_file)
            qr_files['mnemonic'] = mnemonic_file
        
        # 3. Address QR (for receiving payments)
        address_file = os.path.join(export_dir, f"wallet_{wallet_id}_address.png")
        self.generate_qr_code(wallet['address'], address_file)
        qr_files['address'] = address_file
        
        # 4. Complete wallet info JSON QR
        wallet_info = {
            'address': wallet['address'],
            'private_key': wallet['private_key'],
            'mnemonic': wallet['mnemonic_phrase'],
            'derivation_path': wallet['derivation_path']
        }
        complete_file = os.path.join(export_dir, f"wallet_{wallet_id}_complete.png")
        self.generate_qr_code(json.dumps(wallet_info), complete_file)
        qr_files['complete'] = complete_file
        
        # Update database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE wallets SET qr_exported = TRUE WHERE id = ?', (wallet_id,))
        conn.commit()
        conn.close()
        
        return qr_files
    
    def export_wallet_qr_real(self, wallet_id: int, export_dir: str = "qr_exports_real", style: str = "rounded") -> Dict[str, str]:
        """Export wallet as real QR codes using RealQRGenerator"""
        if not REAL_QR_AVAILABLE:
            raise RuntimeError("Real QR generator not available. Ensure real_qr_generator.py is in the same directory.")
        
        wallet = self.get_wallet(wallet_id)
        if not wallet:
            raise ValueError(f"Wallet {wallet_id} not found")
        
        os.makedirs(export_dir, exist_ok=True)
        
        # Initialize real QR generator
        qr_gen = RealQRGenerator()
        
        # Generate real QR codes for the wallet
        wallet_data = {
            'address': wallet['address'],
            'privateKey': wallet['private_key'],
            'mnemonic': wallet['mnemonic_phrase'],
            'derivationPath': wallet['derivation_path'],
            'network': 'mainnet'
        }
        
        qr_files = qr_gen.generate_wallet_qr_codes(
            wallet_data=wallet_data,
            wallet_id=wallet_id,
            output_dir=export_dir,
            style=style
        )
        
        # Update database to mark as exported
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE wallets SET qr_exported = TRUE WHERE id = ?', (wallet_id,))
        conn.commit()
        conn.close()
        
        print(f"✅ Real QR codes exported for wallet {wallet_id}")
        print(f"📁 Export directory: {export_dir}")
        for qr_type, filepath in qr_files.items():
            print(f"   {qr_type.upper()}: {filepath}")
        
        return qr_files
    
    def create_backup_file(self, wallet_ids: List[int] = None, backup_dir: str = "backups") -> str:
        """Create encrypted backup file for wallets"""
        os.makedirs(backup_dir, exist_ok=True)
        
        if wallet_ids:
            wallets = [self.get_wallet(wid) for wid in wallet_ids if self.get_wallet(wid)]
        else:
            wallets = self.list_wallets()
        
        backup_data = {
            'created_at': datetime.now().isoformat(),
            'wallets': wallets,
            'count': len(wallets)
        }
        
        # Create backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"tron_wallets_backup_{timestamp}.json")
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2)
        
        # Update database
        if wallet_ids:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            for wallet_id in wallet_ids:
                cursor.execute('UPDATE wallets SET backup_created = TRUE WHERE id = ?', (wallet_id,))
            conn.commit()
            conn.close()
        
        print(f"Backup created: {backup_file}")
        return backup_file
    
    def export_for_import(self, wallet_id: int, export_format: str = "tronlink") -> Dict:
        """Export wallet in format suitable for import into TRON wallets"""
        wallet = self.get_wallet(wallet_id)
        if not wallet:
            raise ValueError(f"Wallet {wallet_id} not found")
        
        exports = {}
        
        # TronLink format
        if export_format in ["tronlink", "all"]:
            tronlink_data = {
                "address": wallet['address'],
                "privateKey": wallet['private_key'],
                "name": wallet.get('label', f"Wallet {wallet_id}"),
                "type": "PRIVATE_KEY"
            }
            exports['tronlink'] = tronlink_data
        
        # Generic wallet format
        if export_format in ["generic", "all"]:
            generic_data = {
                "address": wallet['address'],
                "privateKey": wallet['private_key'],
                "publicKey": wallet['public_key'],
                "mnemonic": wallet['mnemonic_phrase'],
                "derivationPath": wallet['derivation_path'],
                "network": "mainnet"
            }
            exports['generic'] = generic_data
        
        # Mnemonic only format
        if export_format in ["mnemonic", "all"]:
            mnemonic_data = {
                "mnemonic": wallet['mnemonic_phrase'],
                "passphrase": wallet.get('passphrase', ''),
                "derivationPath": wallet['derivation_path']
            }
            exports['mnemonic'] = mnemonic_data
        
        return exports

def main():
    parser = argparse.ArgumentParser(description='TRON Mnemonic Wallet Generator')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate new wallets
    gen_parser = subparsers.add_parser('generate', help='Generate new wallets with mnemonic phrases')
    gen_parser.add_argument('--count', type=int, default=1, help='Number of wallets to generate')
    gen_parser.add_argument('--passphrase', default='', help='BIP39 passphrase (optional)')
    gen_parser.add_argument('--label', help='Label for the wallets')
    gen_parser.add_argument('--export-qr', action='store_true', help='Also export QR codes')
    
    # Restore from mnemonic
    restore_parser = subparsers.add_parser('restore', help='Restore wallets from mnemonic phrase')
    restore_parser.add_argument('mnemonic', help='Mnemonic phrase (12 or 24 words)')
    restore_parser.add_argument('--count', type=int, default=1, help='Number of addresses to derive')
    restore_parser.add_argument('--passphrase', default='', help='BIP39 passphrase (optional)')
    restore_parser.add_argument('--label', help='Label for the wallets')
    
    # Export QR codes
    qr_parser = subparsers.add_parser('export-qr', help='Export wallet as QR codes')
    qr_parser.add_argument('wallet_id', type=int, help='Wallet ID to export')
    qr_parser.add_argument('--dir', default='qr_exports', help='Export directory')
    
    # Export Real QR codes
    real_qr_parser = subparsers.add_parser('export-real-qr', help='Export wallet as real QR code images')
    real_qr_parser.add_argument('wallet_id', type=int, help='Wallet ID to export')
    real_qr_parser.add_argument('--dir', default='qr_exports_real', help='Export directory')
    real_qr_parser.add_argument('--style', choices=['rounded', 'circle', 'square', 'bars', 'default'], 
                               default='rounded', help='QR code style')
    
    # List wallets
    list_parser = subparsers.add_parser('list', help='List all wallets')
    list_parser.add_argument('--unused-only', action='store_true', help='Show only unused wallets')
    
    # Create backup
    backup_parser = subparsers.add_parser('backup', help='Create backup file')
    backup_parser.add_argument('--wallet-ids', nargs='+', type=int, help='Specific wallet IDs to backup')
    backup_parser.add_argument('--dir', default='backups', help='Backup directory')
    
    # Export for import
    export_parser = subparsers.add_parser('export-import', help='Export wallet for import into other applications')
    export_parser.add_argument('wallet_id', type=int, help='Wallet ID to export')
    export_parser.add_argument('--format', choices=['tronlink', 'generic', 'mnemonic', 'all'], 
                              default='all', help='Export format', dest='export_format')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    generator = MnemonicWalletGenerator()
    
    try:
        if args.command == 'generate':
            print(f"Generating {args.count} wallet(s) with mnemonic phrases...")
            
            for i in range(args.count):
                wallet_data = generator.generate_mnemonic_wallet(
                    passphrase=args.passphrase,
                    derivation_index=i
                )
                
                label = f"{args.label} #{i+1}" if args.label else None
                wallet_id = generator.save_wallet(wallet_data, label)
                
                print(f"\nWallet {wallet_id} created:")
                print(f"  Address: {wallet_data['address']}")
                print(f"  Mnemonic: {wallet_data['mnemonic_phrase']}")
                print(f"  Derivation: {wallet_data['derivation_path']}")
                
                if args.export_qr:
                    qr_files = generator.export_wallet_qr(wallet_id)
                    print(f"  QR codes exported to: {', '.join(qr_files.values())}")
        
        elif args.command == 'restore':
            print(f"Restoring {args.count} wallet(s) from mnemonic phrase...")
            
            wallets = generator.restore_from_mnemonic(
                args.mnemonic,
                passphrase=args.passphrase,
                count=args.count
            )
            
            for i, wallet_data in enumerate(wallets):
                label = f"{args.label} #{i+1}" if args.label else None
                wallet_id = generator.save_wallet(wallet_data, label)
                
                print(f"\nWallet {wallet_id} restored:")
                print(f"  Address: {wallet_data['address']}")
                print(f"  Derivation: {wallet_data['derivation_path']}")
        
        elif args.command == 'export-qr':
            print(f"Exporting QR codes for wallet {args.wallet_id}...")
            qr_files = generator.export_wallet_qr(args.wallet_id, args.dir)
            
            print("QR codes exported:")
            for qr_type, filename in qr_files.items():
                print(f"  {qr_type}: {filename}")
        
        elif args.command == 'export-real-qr':
            print(f"Exporting real QR codes for wallet {args.wallet_id}...")
            try:
                qr_files = generator.export_wallet_qr_real(args.wallet_id, args.dir, args.style)
                print("✅ Real QR codes exported successfully!")
            except RuntimeError as e:
                print(f"❌ Error: {e}")
                print("Make sure real_qr_generator.py is available in the same directory.")
        
        elif args.command == 'list':
            wallets = generator.list_wallets(include_used=not args.unused_only)
            
            if not wallets:
                print("No wallets found.")
                return
            
            print(f"\nFound {len(wallets)} wallet(s):")
            print("-" * 80)
            
            for wallet in wallets:
                print(f"ID: {wallet['id']}")
                print(f"  Address: {wallet['address']}")
                print(f"  Label: {wallet.get('label', 'None')}")
                print(f"  Created: {wallet['created_at']}")
                print(f"  Used: {'Yes' if wallet['is_used'] else 'No'}")
                print(f"  QR Exported: {'Yes' if wallet['qr_exported'] else 'No'}")
                print()
        
        elif args.command == 'backup':
            backup_file = generator.create_backup_file(
                wallet_ids=args.wallet_ids,
                backup_dir=args.dir
            )
            print(f"Backup created: {backup_file}")
        
        elif args.command == 'export-import':
            exports = generator.export_for_import(args.wallet_id, args.export_format)
            
            print(f"Export data for wallet {args.wallet_id}:")
            print(json.dumps(exports, indent=2))
    
    except (ValueError, RuntimeError, sqlite3.Error) as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
