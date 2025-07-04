#!/usr/bin/env python3
"""
Real QR Code Demo for TRON Wallets

This demo shows the enhanced QR code generation capabilities using the qrcode library.
It demonstrates:
1. Creating real QR code images
2. Different QR code styles
3. Wallet import sheets
4. Custom labeling and styling

Usage: python demo_real_qr.py
"""

import os
import subprocess
import sys

def check_dependencies():
    """Check if QR code libraries are available"""
    try:
        import qrcode  # noqa: F401
        from PIL import Image  # noqa: F401
        return True
    except ImportError:
        return False

def run_demo():
    """Run the real QR code generation demo"""
    
    print("🎨 Real QR Code Generation Demo")
    print("=" * 60)
    
    if not check_dependencies():
        print("❌ QR code dependencies not available!")
        print("Install with: sudo apt install python3-qrcode python3-pil")
        return 1
    
    print("✅ QR code libraries are available")
    print()
    
    # Demo data
    demo_address = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    demo_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    
    print("📱 Demo 1: Basic QR Code Generation")
    print("-" * 40)
    
    # Generate basic QR codes
    demos = [
        {
            "data": demo_address,
            "output": "demo_address_basic.png",
            "style": "default",
            "label": "TRON Address",
            "subtitle": "Basic style"
        },
        {
            "data": demo_address,
            "output": "demo_address_rounded.png", 
            "style": "rounded",
            "label": "TRON Address",
            "subtitle": "Rounded style"
        },
        {
            "data": demo_mnemonic,
            "output": "demo_mnemonic_circle.png",
            "style": "circle", 
            "label": "Recovery Phrase",
            "subtitle": "Circle style"
        }
    ]
    
    for demo in demos:
        cmd = [
            "python3", "real_qr_generator.py",
            "--data", demo["data"],
            "--output", demo["output"],
            "--style", demo["style"],
            "--label", demo["label"],
            "--subtitle", demo["subtitle"]
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"✅ Generated: {demo['output']} ({demo['style']} style)")
            else:
                print(f"❌ Failed to generate {demo['output']}: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout generating {demo['output']}")
        except Exception as e:
            print(f"❌ Error generating {demo['output']}: {e}")
    
    print()
    print("📱 Demo 2: Wallet QR Code Generation")
    print("-" * 40)
    
    # Create test wallet if it doesn't exist
    try:
        result = subprocess.run(["python3", "create_test_wallet.py"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Test wallet ready")
        else:
            print(f"⚠️ Wallet creation result: {result.stdout}")
    except Exception as e:
        print(f"⚠️ Wallet creation: {e}")
    
    # Generate all QR codes for wallet
    wallet_demos = [
        {
            "args": ["--wallet-id", "1", "--output-dir", "demo_wallet_qr/", "--style", "rounded"],
            "description": "All wallet QR codes (rounded style)"
        },
        {
            "args": ["--wallet-id", "1", "--import-sheet", "--output", "demo_import_sheet.png"],
            "description": "Wallet import sheet"
        },
        {
            "args": ["--wallet-id", "1", "--type", "address", "--output", "demo_wallet_address_only.png", "--style", "square"],
            "description": "Address QR only (square style)"
        }
    ]
    
    for demo in wallet_demos:
        cmd = ["python3", "real_qr_generator.py"] + demo["args"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"✅ {demo['description']}")
                if result.stdout.strip():
                    print(f"   {result.stdout.strip()}")
            else:
                print(f"❌ Failed: {demo['description']}")
                if result.stderr:
                    print(f"   Error: {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout: {demo['description']}")
        except Exception as e:
            print(f"❌ Error: {demo['description']}: {e}")
    
    print()
    print("📱 Demo 3: Different Styles Showcase")
    print("-" * 40)
    
    styles = ["default", "rounded", "circle", "square", "bars"]
    
    for style in styles:
        cmd = [
            "python3", "real_qr_generator.py",
            "--address", demo_address,
            "--output", f"demo_style_{style}.png",
            "--style", style,
            "--label", f"Style: {style.title()}",
            "--subtitle", "TRON Address QR"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                print(f"✅ Generated {style} style QR code")
            else:
                print(f"❌ Failed to generate {style} style")
        except Exception as e:
            print(f"❌ Error with {style} style: {e}")
    
    print()
    print("📁 Generated Files Summary")
    print("-" * 40)
    
    # List all generated PNG files
    try:
        result = subprocess.run(["find", ".", "-name", "*.png", "-type", "f"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            files = sorted(result.stdout.strip().split('\n'))
            for i, file in enumerate(files, 1):
                file_size = os.path.getsize(file) if os.path.exists(file) else 0
                print(f"{i:2d}. {file} ({file_size:,} bytes)")
        else:
            print("No PNG files found")
    except Exception as e:
        print(f"Error listing files: {e}")
    
    print()
    print("💡 Usage Examples")
    print("-" * 40)
    print("1. Generate address QR:")
    print("   python3 real_qr_generator.py --address 'TR...' --output addr.png")
    print()
    print("2. Generate wallet QR codes:")
    print("   python3 real_qr_generator.py --wallet-id 1 --output-dir qr/")
    print()
    print("3. Create import sheet:")
    print("   python3 real_qr_generator.py --wallet-id 1 --import-sheet --output sheet.png")
    print()
    print("4. Custom style:")
    print("   python3 real_qr_generator.py --data 'test' --output test.png --style rounded")
    print()
    print("🎯 All QR codes are now real images that can be scanned!")
    print("📱 Use any QR code scanner or wallet app to import addresses/keys")
    
    return 0

if __name__ == "__main__":
    sys.exit(run_demo())
