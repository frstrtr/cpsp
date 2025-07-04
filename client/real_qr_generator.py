#!/usr/bin/env python3
"""
Enhanced Real QR Code Generator for TRON Wallets

This script generates actual QR code images using the qrcode library.
It can create QR codes for addresses, private keys, mnemonic phrases,
and complete wallet data with various styling options.

Usage:
    python real_qr_generator.py --address "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t" --output address_qr.png
    python real_qr_generator.py --wallet-id 123 --type all --output-dir qr_codes/
    python real_qr_generator.py --mnemonic "word1 word2 ... word12" --style rounded --output mnemonic.png
"""

import os
import json
import sqlite3
import argparse
import sys
from typing import Dict, List, Optional

try:
    import qrcode
    from qrcode.image.styledpil import StyledPilImage
    from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, CircleModuleDrawer, SquareModuleDrawer, VerticalBarsDrawer
    from PIL import Image, ImageDraw, ImageFont
    QR_AVAILABLE = True
except ImportError as e:
    QR_AVAILABLE = False
    print(f"Error: QR code dependencies not available: {e}")
    print("Install with: sudo apt install python3-qrcode python3-pil")
    sys.exit(1)

class RealQRCodeGenerator:
    """Generate real QR code images for TRON wallets"""
    
    def __init__(self, db_path: str = "mnemonic_wallets.db"):
        self.db_path = db_path
    
    def get_wallet_from_db(self, wallet_id: int) -> Optional[Dict]:
        """Get wallet data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
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
    
    def create_qr_code(self, data: str, style: str = "default", error_correction: str = "M") -> qrcode.QRCode:
        """Create a QR code object with specified style"""
        
        # Set error correction level
        error_levels = {
            "L": qrcode.constants.ERROR_CORRECT_L,  # ~7%
            "M": qrcode.constants.ERROR_CORRECT_M,  # ~15%
            "Q": qrcode.constants.ERROR_CORRECT_Q,  # ~25%
            "H": qrcode.constants.ERROR_CORRECT_H   # ~30%
        }
        
        qr = qrcode.QRCode(
            version=1,  # Auto-adjust size
            error_correction=error_levels.get(error_correction, qrcode.constants.ERROR_CORRECT_M),
            box_size=10,
            border=4,
        )
        
        qr.add_data(data)
        qr.make(fit=True)
        
        return qr
    
    def create_styled_image(self, qr: qrcode.QRCode, style: str = "default") -> Image.Image:
        """Create styled QR code image"""
        
        if style == "rounded":
            img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer()
            )
        elif style == "circle":
            img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=CircleModuleDrawer()
            )
        elif style == "square":
            img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=SquareModuleDrawer()
            )
        elif style == "bars":
            img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=VerticalBarsDrawer()
            )
        else:  # default
            img = qr.make_image(fill_color="black", back_color="white")
        
        return img
    
    def add_label_to_image(self, img: Image.Image, label: str, subtitle: str = "") -> Image.Image:
        """Add text label below QR code"""
        try:
            # Create new image with space for text
            img_width, img_height = img.size
            text_height = 100  # Space for text
            new_height = img_height + text_height
            
            # Create new image with white background
            new_img = Image.new('RGB', (img_width, new_height), 'white')
            
            # Paste QR code at top
            new_img.paste(img, (0, 0))
            
            # Add text
            draw = ImageDraw.Draw(new_img)
            
            # Try to use a system font, fallback to default
            try:
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            except (OSError, IOError):
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Calculate text positions
            text_y_start = img_height + 10
            
            # Draw main label
            label_bbox = draw.textbbox((0, 0), label, font=font_large)
            label_width = label_bbox[2] - label_bbox[0]
            label_x = (img_width - label_width) // 2
            draw.text((label_x, text_y_start), label, fill="black", font=font_large)
            
            # Draw subtitle if provided
            if subtitle:
                subtitle_bbox = draw.textbbox((0, 0), subtitle, font=font_small)
                subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
                subtitle_x = (img_width - subtitle_width) // 2
                draw.text((subtitle_x, text_y_start + 25), subtitle, fill="gray", font=font_small)
            
            return new_img
            
        except Exception:
            # If anything goes wrong, return original image
            return img
    
    def generate_wallet_qr_codes(self, wallet_id: int, output_dir: str = "qr_codes", 
                                 style: str = "default", with_labels: bool = True) -> Dict[str, str]:
        """Generate QR codes for all wallet components"""
        
        wallet = self.get_wallet_from_db(wallet_id)
        if not wallet:
            raise ValueError(f"Wallet {wallet_id} not found in database")
        
        os.makedirs(output_dir, exist_ok=True)
        generated_files = {}
        
        # 1. Address QR (for receiving payments)
        if wallet.get('address'):
            qr = self.create_qr_code(wallet['address'])
            img = self.create_styled_image(qr, style)
            
            if with_labels:
                img = self.add_label_to_image(img, "TRON Address", "For receiving payments")
            
            address_file = os.path.join(output_dir, f"wallet_{wallet_id}_address.png")
            img.save(address_file)
            generated_files['address'] = address_file
        
        # 2. Private Key QR (for importing wallet)
        if wallet.get('private_key'):
            qr = self.create_qr_code(wallet['private_key'], error_correction="H")  # Higher error correction for private keys
            img = self.create_styled_image(qr, style)
            
            if with_labels:
                img = self.add_label_to_image(img, "Private Key", "⚠️ Keep absolutely private!")
            
            private_key_file = os.path.join(output_dir, f"wallet_{wallet_id}_private_key.png")
            img.save(private_key_file)
            generated_files['private_key'] = private_key_file
        
        # 3. Mnemonic QR (for wallet recovery)
        if wallet.get('mnemonic_phrase'):
            qr = self.create_qr_code(wallet['mnemonic_phrase'], error_correction="H")
            img = self.create_styled_image(qr, style)
            
            if with_labels:
                img = self.add_label_to_image(img, "Mnemonic Phrase", "For wallet recovery")
            
            mnemonic_file = os.path.join(output_dir, f"wallet_{wallet_id}_mnemonic.png")
            img.save(mnemonic_file)
            generated_files['mnemonic'] = mnemonic_file
        
        # 4. Complete wallet info JSON QR
        wallet_info = {
            'address': wallet.get('address'),
            'privateKey': wallet.get('private_key'),
            'mnemonic': wallet.get('mnemonic_phrase'),
            'derivationPath': wallet.get('derivation_path'),
            'network': 'mainnet'
        }
        
        wallet_json = json.dumps(wallet_info, separators=(',', ':'))
        qr = self.create_qr_code(wallet_json, error_correction="H")
        img = self.create_styled_image(qr, style)
        
        if with_labels:
            img = self.add_label_to_image(img, "Complete Wallet", "Full import data")
        
        complete_file = os.path.join(output_dir, f"wallet_{wallet_id}_complete.png")
        img.save(complete_file)
        generated_files['complete'] = complete_file
        
        return generated_files
    
    def generate_single_qr(self, data: str, output_file: str, style: str = "default", 
                          label: str = "", subtitle: str = "", error_correction: str = "M") -> str:
        """Generate a single QR code with custom data"""
        
        qr = self.create_qr_code(data, error_correction=error_correction)
        img = self.create_styled_image(qr, style)
        
        if label:
            img = self.add_label_to_image(img, label, subtitle)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        
        img.save(output_file)
        return output_file
    
    def create_wallet_import_sheet(self, wallet_id: int, output_file: str = None) -> str:
        """Create a single image with multiple QR codes for wallet import"""
        
        wallet = self.get_wallet_from_db(wallet_id)
        if not wallet:
            raise ValueError(f"Wallet {wallet_id} not found in database")
        
        if not output_file:
            output_file = f"wallet_{wallet_id}_import_sheet.png"
        
        # Generate individual QR codes
        qr_codes = []
        labels = []
        
        if wallet.get('address'):
            qr = self.create_qr_code(wallet['address'])
            img = self.create_styled_image(qr, "rounded")
            qr_codes.append(img)
            labels.append("Address")
        
        if wallet.get('mnemonic_phrase'):
            qr = self.create_qr_code(wallet['mnemonic_phrase'], error_correction="H")
            img = self.create_styled_image(qr, "rounded")
            qr_codes.append(img)
            labels.append("Mnemonic")
        
        if wallet.get('private_key'):
            qr = self.create_qr_code(wallet['private_key'], error_correction="H")
            img = self.create_styled_image(qr, "rounded")
            qr_codes.append(img)
            labels.append("Private Key")
        
        if not qr_codes:
            raise ValueError("No valid data found for QR code generation")
        
        # Create combined image
        qr_size = qr_codes[0].size[0]
        padding = 20
        title_height = 60
        label_height = 30
        
        # Calculate grid dimensions
        cols = min(len(qr_codes), 3)  # Max 3 columns
        rows = (len(qr_codes) + cols - 1) // cols  # Ceiling division
        
        sheet_width = cols * qr_size + (cols + 1) * padding
        sheet_height = title_height + rows * (qr_size + label_height + padding) + padding
        
        # Create sheet
        sheet = Image.new('RGB', (sheet_width, sheet_height), 'white')
        draw = ImageDraw.Draw(sheet)
        
        # Add title
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except (OSError, IOError):
            title_font = ImageFont.load_default()
            label_font = ImageFont.load_default()
        
        title = f"TRON Wallet Import Sheet (ID: {wallet_id})"
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (sheet_width - title_width) // 2
        draw.text((title_x, 20), title, fill="black", font=title_font)
        
        # Add QR codes
        for i, (qr_img, label) in enumerate(zip(qr_codes, labels)):
            row = i // cols
            col = i % cols
            
            x = padding + col * (qr_size + padding)
            y = title_height + row * (qr_size + label_height + padding) + padding
            
            # Paste QR code
            sheet.paste(qr_img, (x, y))
            
            # Add label
            label_bbox = draw.textbbox((0, 0), label, font=label_font)
            label_width = label_bbox[2] - label_bbox[0]
            label_x = x + (qr_size - label_width) // 2
            draw.text((label_x, y + qr_size + 5), label, fill="black", font=label_font)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        
        sheet.save(output_file)
        return output_file

def main():
    if not QR_AVAILABLE:
        print("QR code library is not available. Exiting.")
        return 1
    
    parser = argparse.ArgumentParser(description='Real QR Code Generator for TRON Wallets')
    
    # Data source options
    data_group = parser.add_mutually_exclusive_group(required=True)
    data_group.add_argument('--data', help='Raw data to encode in QR code')
    data_group.add_argument('--wallet-id', type=int, help='Wallet ID from database')
    data_group.add_argument('--address', help='TRON address to encode')
    data_group.add_argument('--mnemonic', help='Mnemonic phrase to encode')
    data_group.add_argument('--private-key', help='Private key to encode')
    
    # Output options
    parser.add_argument('--output', help='Output file path (for single QR codes)')
    parser.add_argument('--output-dir', default='qr_codes', help='Output directory (for multiple QR codes)')
    
    # QR code options
    parser.add_argument('--type', choices=['address', 'private_key', 'mnemonic', 'complete', 'all'],
                       default='all', help='Type of QR code to generate for wallet')
    parser.add_argument('--style', choices=['default', 'rounded', 'circle', 'square', 'bars'],
                       default='rounded', help='QR code style')
    parser.add_argument('--error-correction', choices=['L', 'M', 'Q', 'H'], default='M',
                       help='Error correction level (L=7%%, M=15%%, Q=25%%, H=30%%)')
    
    # Additional options
    parser.add_argument('--label', help='Label to add below QR code')
    parser.add_argument('--subtitle', help='Subtitle to add below label')
    parser.add_argument('--no-labels', action='store_true', help='Don\'t add automatic labels')
    parser.add_argument('--import-sheet', action='store_true', help='Create wallet import sheet with multiple QR codes')
    parser.add_argument('--db-path', default='mnemonic_wallets.db', help='Database path')
    
    args = parser.parse_args()
    
    generator = RealQRCodeGenerator(args.db_path)
    
    try:
        if args.wallet_id:
            if args.import_sheet:
                # Create import sheet
                sheet_file = args.output or f"wallet_{args.wallet_id}_import_sheet.png"
                output_file = generator.create_wallet_import_sheet(args.wallet_id, sheet_file)
                print(f"Import sheet created: {output_file}")
            else:
                # Generate QR codes for wallet
                if args.type == 'all':
                    qr_files = generator.generate_wallet_qr_codes(
                        args.wallet_id, 
                        args.output_dir, 
                        args.style, 
                        not args.no_labels
                    )
                    print(f"Generated QR codes for wallet {args.wallet_id}:")
                    for qr_type, filename in qr_files.items():
                        print(f"  {qr_type}: {filename}")
                else:
                    # Generate single type
                    wallet = generator.get_wallet_from_db(args.wallet_id)
                    if not wallet:
                        print(f"Wallet {args.wallet_id} not found")
                        return 1
                    
                    data_map = {
                        'address': wallet.get('address'),
                        'private_key': wallet.get('private_key'),
                        'mnemonic': wallet.get('mnemonic_phrase'),
                        'complete': json.dumps({
                            'address': wallet.get('address'),
                            'privateKey': wallet.get('private_key'),
                            'mnemonic': wallet.get('mnemonic_phrase'),
                            'derivationPath': wallet.get('derivation_path')
                        })
                    }
                    
                    data = data_map.get(args.type)
                    if not data:
                        print(f"No {args.type} data found for wallet {args.wallet_id}")
                        return 1
                    
                    output_file = args.output or os.path.join(args.output_dir, f"wallet_{args.wallet_id}_{args.type}.png")
                    label = args.label or args.type.replace('_', ' ').title()
                    
                    generated_file = generator.generate_single_qr(
                        data, output_file, args.style, label, args.subtitle, args.error_correction
                    )
                    print(f"Generated QR code: {generated_file}")
        
        else:
            # Generate single QR code from provided data
            if args.data:
                data = args.data
                default_label = "QR Code"
            elif args.address:
                data = args.address
                default_label = "TRON Address"
            elif args.mnemonic:
                data = args.mnemonic
                default_label = "Mnemonic Phrase"
            elif args.private_key:
                data = args.private_key
                default_label = "Private Key"
            
            if not args.output:
                print("Output file is required for single QR code generation")
                return 1
            
            label = args.label or default_label
            generated_file = generator.generate_single_qr(
                data, args.output, args.style, label, args.subtitle, args.error_correction
            )
            print(f"Generated QR code: {generated_file}")
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
