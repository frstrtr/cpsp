#!/usr/bin/env python3
"""
Demo script showing mnemonic wallet generation and QR code features

This demo runs without external dependencies and shows:
1. Simple wallet generation (demo mode)
2. Text-based QR code generation
3. Mnemonic phrase concepts
4. Export formats

Usage: python demo_mnemonic_qr.py
"""

import json
import secrets
from datetime import datetime
from typing import Dict, List

def generate_demo_mnemonic(word_count: int = 12) -> str:
    """Generate a demo mnemonic phrase (not BIP39 compliant, for demo only)"""
    # Common English words for demo purposes
    words = [
        "abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract",
        "absurd", "abuse", "access", "accident", "account", "accuse", "achieve", "acid",
        "acoustic", "acquire", "across", "action", "actor", "actress", "actual", "adapt",
        "add", "addict", "address", "adjust", "admit", "adult", "advance", "advice",
        "aerobic", "affair", "afford", "afraid", "again", "agent", "agree", "ahead",
        "aim", "air", "airport", "aisle", "alarm", "album", "alcohol", "alert",
        "alien", "all", "alley", "allow", "almost", "alone", "alpha", "already",
        "also", "alter", "always", "amateur", "amazing", "among", "amount", "amused",
        "analyst", "anchor", "ancient", "anger", "angle", "angry", "animal", "ankle"
    ]
    
    # Randomly select words for demo
    selected_words = []
    for _ in range(word_count):
        word = words[secrets.randbelow(len(words))]
        selected_words.append(word)
    
    return " ".join(selected_words)

def generate_demo_wallet() -> Dict:
    """Generate a demo TRON wallet"""
    # Generate a demo TRON address (format TR followed by 32 characters)
    address_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    address = "TR" + "".join(secrets.choice(address_chars) for _ in range(32))
    
    # Generate demo private key (64 hex characters)
    private_key = secrets.token_hex(32)
    
    # Generate demo mnemonic
    mnemonic = generate_demo_mnemonic()
    
    return {
        'address': address,
        'private_key': private_key,
        'mnemonic_phrase': mnemonic,
        'derivation_path': "m/44'/195'/0'/0/0",
        'created_at': datetime.now().isoformat()
    }

def create_text_qr(data: str, title: str = "QR Code") -> str:
    """Create a simple text-based QR code representation"""
    lines = []
    
    # Calculate width based on data length
    content_width = max(len(data), len(title) + 4)
    total_width = content_width + 6
    
    # Top border
    lines.append("█" * total_width)
    lines.append("█" + " " * (total_width - 2) + "█")
    
    # Title
    title_padding = (content_width - len(title)) // 2
    title_line = "█  " + " " * title_padding + title + " " * (content_width - title_padding - len(title)) + "  █"
    lines.append(title_line)
    
    lines.append("█" + " " * (total_width - 2) + "█")
    
    # Data (split into chunks)
    chunk_size = content_width - 4
    data_chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
    
    for chunk in data_chunks:
        padding = (content_width - len(chunk)) // 2
        line = "█  " + " " * padding + chunk + " " * (content_width - padding - len(chunk)) + "  █"
        lines.append(line)
    
    # Bottom border
    lines.append("█" + " " * (total_width - 2) + "█")
    lines.append("█" * total_width)
    
    return "\n".join(lines)

def demo_wallet_generation():
    """Demonstrate wallet generation with mnemonic phrases"""
    print("🔐 TRON Mnemonic Wallet Generation Demo")
    print("=" * 60)
    
    # Generate demo wallets
    wallets = []
    for i in range(3):
        wallet = generate_demo_wallet()
        wallets.append(wallet)
        
        print(f"\n📱 Demo Wallet #{i+1}")
        print("-" * 40)
        print(f"Address: {wallet['address']}")
        print(f"Mnemonic: {wallet['mnemonic_phrase']}")
        print(f"Derivation: {wallet['derivation_path']}")
        print(f"Created: {wallet['created_at']}")
    
    return wallets

def demo_qr_codes(wallets: List[Dict]):
    """Demonstrate QR code generation for wallets"""
    print("\n\n📱 QR Code Generation Demo")
    print("=" * 60)
    
    wallet = wallets[0]  # Use first wallet for demo
    
    # Address QR (for receiving payments)
    print("\n1️⃣ Address QR Code (for receiving payments):")
    print(create_text_qr(wallet['address'], "TRON ADDRESS"))
    
    # Mnemonic QR (for wallet recovery)
    print("\n2️⃣ Mnemonic QR Code (for wallet recovery):")
    print(create_text_qr(wallet['mnemonic_phrase'], "MNEMONIC PHRASE"))
    
    # Private key QR (for wallet import)
    print("\n3️⃣ Private Key QR Code (for wallet import):")
    print(create_text_qr(wallet['private_key'], "PRIVATE KEY"))

def demo_export_formats(wallets: List[Dict]):
    """Demonstrate various export formats"""
    print("\n\n📤 Export Format Demo")
    print("=" * 60)
    
    wallet = wallets[0]
    
    # TronLink format
    tronlink_export = {
        "address": wallet['address'],
        "privateKey": wallet['private_key'],
        "name": "Demo Wallet",
        "type": "PRIVATE_KEY"
    }
    
    print("\n1️⃣ TronLink Import Format:")
    print(json.dumps(tronlink_export, indent=2))
    
    # Generic wallet format
    generic_export = {
        "address": wallet['address'],
        "privateKey": wallet['private_key'],
        "mnemonic": wallet['mnemonic_phrase'],
        "derivationPath": wallet['derivation_path'],
        "network": "mainnet"
    }
    
    print("\n2️⃣ Generic Wallet Format:")
    print(json.dumps(generic_export, indent=2))
    
    # Mnemonic-only format
    mnemonic_export = {
        "mnemonic": wallet['mnemonic_phrase'],
        "derivationPath": wallet['derivation_path'],
        "passphrase": ""
    }
    
    print("\n3️⃣ Mnemonic Recovery Format:")
    print(json.dumps(mnemonic_export, indent=2))

def demo_security_features():
    """Demonstrate security features and best practices"""
    print("\n\n🔒 Security Features Demo")
    print("=" * 60)
    
    print("\n1️⃣ Mnemonic Phrase Security:")
    print("   ✅ 12-word BIP39 compatible phrases")
    print("   ✅ Cryptographically secure random generation")
    print("   ✅ Optional passphrase protection")
    print("   ✅ Offline generation capability")
    
    print("\n2️⃣ Private Key Security:")
    print("   ✅ 256-bit entropy")
    print("   ✅ ECDSA secp256k1 compatibility")
    print("   ✅ Secure deletion after use")
    
    print("\n3️⃣ QR Code Security:")
    print("   ✅ Separate QR codes for different purposes")
    print("   ✅ Address QR (safe to share publicly)")
    print("   ✅ Private key QR (keep absolutely private)")
    print("   ✅ Mnemonic QR (for backup purposes only)")

def demo_integration_workflow():
    """Demonstrate integration with main payment service"""
    print("\n\n🔄 Integration Workflow Demo")
    print("=" * 60)
    
    print("\n1️⃣ Wallet Generation:")
    print("   python mnemonic_wallet_generator.py generate --count 10")
    
    print("\n2️⃣ QR Code Export:")
    print("   python mnemonic_wallet_generator.py export-qr 123")
    
    print("\n3️⃣ Address Integration:")
    print("   python tron_address_manager.py add-real [ADDRESS] --label 'Generated'")
    
    print("\n4️⃣ Payment Request:")
    print("   python tron_address_manager.py payment --amount 100 --order-id ORD001")
    
    print("\n5️⃣ Monitoring Service:")
    print("   python payment_integration.py batch --file requests.json")

def main():
    """Run the complete demo"""
    print("🚀 TRON Mnemonic Wallet & QR Code Demo")
    print("🔒 Advanced Client-Side Address Management")
    print("=" * 80)
    
    # 1. Wallet generation demo
    wallets = demo_wallet_generation()
    
    # 2. QR code demo
    demo_qr_codes(wallets)
    
    # 3. Export formats demo
    demo_export_formats(wallets)
    
    # 4. Security features demo
    demo_security_features()
    
    # 5. Integration workflow demo
    demo_integration_workflow()
    
    print("\n\n💡 Next Steps:")
    print("=" * 40)
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Generate real wallets: python mnemonic_wallet_generator.py generate --count 5")
    print("3. Export QR codes: python mnemonic_wallet_generator.py export-qr 1")
    print("4. Create backups: python mnemonic_wallet_generator.py backup")
    print("5. Integrate with payment service")
    
    print("\n⚠️  Security Notes:")
    print("=" * 40)
    print("• Demo wallets are NOT cryptographically secure")
    print("• Use production tools for real cryptocurrency")
    print("• Store mnemonic phrases securely offline")
    print("• Never share private keys or mnemonic phrases")
    print("• Create encrypted backups of wallet data")

if __name__ == '__main__':
    main()
