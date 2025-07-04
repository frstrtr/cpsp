# Client-Side TRON Address Management

This folder contains client-side tools for generating and managing TRON addresses for payment processing, including advanced wallet generation with mnemonic phrases and QR code export capabilities.

## Files

### `tron_address_manager.py`
Main script for managing TRON addresses and payment requests locally.

**Features:**
- Create demo addresses for testing
- Add real TRON addresses you control
- Create payment requests with unique addresses
- Export pending payments for the monitoring service
- Local SQLite database for persistence

**Usage:**
```bash
# Create demo addresses for testing
python tron_address_manager.py create-demo --count 5

# Add a real address you control
python tron_address_manager.py add-real TGj1Ej1qRzL9feLTLhjwgxXF4Ct6GTWg2U --label "My Wallet"

# Create a payment request
python tron_address_manager.py payment --amount 25.50 --order-id "ORDER123" --callback "https://mysite.com/webhook"

# List all addresses
python tron_address_manager.py list-addresses

# Export pending payments for monitoring service
python tron_address_manager.py export-monitoring
```

### `payment_integration.py`
Integration script for connecting with the main payment monitoring service.

**Features:**
- Send payment requests to the monitoring service
- Check payment status
- Batch process multiple payments
- Service health checks

**Usage:**
```bash
# Check if monitoring service is running
python payment_integration.py health

# Send a specific payment request
python payment_integration.py send --payment-id 123

# Check payment status by order ID
python payment_integration.py check --order-id ORDER123

# Send all pending payments in batch
python payment_integration.py batch --file monitoring_requests.json
```

### `mnemonic_wallet_generator.py` ⭐ NEW

Advanced wallet generator with BIP39 mnemonic phrases, HD wallet derivation, and QR code export.

**Features:**

- Generate BIP39 compatible mnemonic phrases (12 words)
- HD wallet derivation using BIP44 standard
- Export QR codes for easy wallet import
- Multiple export formats (TronLink, generic, mnemonic-only)
- Encrypted backup files
- Batch wallet generation

**Usage:**

```bash
# Generate new wallets with mnemonic phrases
python mnemonic_wallet_generator.py generate --count 5 --label "Main Wallets"

# Generate wallets and export QR codes immediately
python mnemonic_wallet_generator.py generate --count 3 --export-qr

# Restore wallets from existing mnemonic phrase
python mnemonic_wallet_generator.py restore "word1 word2 word3 ... word12" --count 10

# Export QR codes for specific wallet
python mnemonic_wallet_generator.py export-qr 123 --dir ./wallet_qr_codes

# List all generated wallets
python mnemonic_wallet_generator.py list

# Create backup file
python mnemonic_wallet_generator.py backup --dir ./backups

# Export wallet for import into TronLink or other wallets
python mnemonic_wallet_generator.py export-import 123 --format tronlink
```

### `real_qr_generator.py` ⭐ NEW

Professional QR code generator that creates real, scannable QR code images (PNG format).

**Features:**

- Generate real QR code images (PNG format) for addresses, private keys, mnemonic phrases
- Multiple visual styles: default, rounded, circle, square, bars
- Custom labels and wallet import sheets
- Batch generation for multiple wallets
- Integration with wallet database
- Works with system-installed qrcode and PIL libraries

**Visual Styles:**

- `default`: Standard QR code with square modules
- `rounded`: Smooth rounded corners for modern look
- `circle`: Circular modules for elegant appearance
- `square`: Bold square modules with spacing
- `bars`: Horizontal bar pattern for unique style

**Usage:**

```bash
# Generate QR for any data with default style
python real_qr_generator.py --data "TGj1Ej1qRzL9feLTLhjwgxXF4Ct6GTWg2U" --output address_qr.png

# Generate QR with custom style and label
python real_qr_generator.py --data "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t" --style rounded --label "Main Address" --output styled_qr.png

# Generate all QR types for a wallet from database
python real_qr_generator.py --wallet-id 123 --output-dir wallet_qr_codes/

# Generate wallet import sheet with all information
python real_qr_generator.py --wallet-id 123 --import-sheet --output-dir import_sheets/

# Batch generate QR codes for multiple wallets
python real_qr_generator.py --batch-wallets 1,2,3,4,5 --output-dir batch_qr/

# Generate QR for mnemonic phrase with custom styling
python real_qr_generator.py --mnemonic "word1 word2 word3 ... word12" --style circle --label "Recovery Phrase" --output mnemonic_qr.png
```

### `simple_qr_generator.py`

Text-based QR code generator that works without image dependencies (fallback option).

**Features:**

- Text-based QR code representation for terminals
- Generate QR codes for addresses, private keys, mnemonic phrases
- Import URL generation for wallet applications
- Works without PIL/qrcode libraries (fallback when real_qr_generator.py is not available)

**Usage:**

```bash
# Generate text QR for any data (when image libraries are not available)
python simple_qr_generator.py --data "TGj1Ej1qRzL9feLTLhjwgxXF4Ct6GTWg2U"

# Generate text QR for wallet from database
python simple_qr_generator.py --wallet-id 123 --type address
```

### `wallet_import_export.py`
Simple wallet import/export utility for environments without full cryptography dependencies.

### `requirements.txt`
Python dependencies for production-grade cryptography and QR code generation.

## Quick Start Guide ⭐ NEW

### Try the Real QR Code Generator

```bash
# 1. Install system QR code dependencies (Ubuntu/Debian)
sudo apt update && sudo apt install python3-qrcode python3-pil

# 2. Create a test wallet
python create_test_wallet.py

# 3. Run the complete demo
python demo_real_qr.py

# 4. Generate QR codes for any TRON address
python real_qr_generator.py --data "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t" --style rounded --label "My Address" --output my_address_qr.png

# 5. Generate all QR types for a wallet
python real_qr_generator.py --wallet-id 1 --output-dir wallet_qr/

# 6. Create a complete wallet import sheet
python real_qr_generator.py --wallet-id 1 --import-sheet --output-dir import_sheet/
```

## Setup

### 1. Basic Setup (Demo Mode)
```bash
# No additional dependencies needed for demo mode
python tron_address_manager.py create-demo --count 10
python simple_qr_generator.py --data "demo_address"
```

### 2. Advanced Setup (Mnemonic + QR Codes)
```bash
# Install all dependencies for full functionality
pip install -r requirements.txt

# Generate wallets with mnemonic phrases and QR codes
python mnemonic_wallet_generator.py generate --count 5 --export-qr

# Create QR codes for existing wallets
python mnemonic_wallet_generator.py export-qr 1
```

### 3. Production Setup (Real Addresses)
```bash
# For production with cryptographically secure wallets
pip install -r requirements.txt

# Generate production wallets
python mnemonic_wallet_generator.py generate --count 20 --label "Production"

# Create encrypted backups
python mnemonic_wallet_generator.py backup
```

## Workflow

### 1. Generate Wallets with Mnemonic Phrases
```bash
# Generate wallets with mnemonic phrases for recovery
python mnemonic_wallet_generator.py generate --count 10 --label "CustomerWallets"

# Restore wallets from existing mnemonic (useful for multi-device setup)
python mnemonic_wallet_generator.py restore "abandon abandon abandon ... art" --count 5
```

### 2. Export QR Codes for Easy Import

```bash
# Export professional QR code images (recommended)
python real_qr_generator.py --wallet-id 123 --output-dir wallet_qr_codes/

# Export with custom styling
python real_qr_generator.py --wallet-id 123 --style rounded --output-dir styled_qr/

# Generate complete wallet import sheet
python real_qr_generator.py --wallet-id 123 --import-sheet --output-dir import_sheets/

# Or use simple text QR codes (fallback)
python simple_qr_generator.py --wallet-id 123 --type all
```

### 3. Create Payment Requests (Traditional Method)
```bash
# Create individual payment requests using address manager
python tron_address_manager.py payment \
  --amount 100.00 \
  --order-id "ORDER001" \
  --callback "https://mysite.com/webhook/payment" \
  --notes "Customer payment for order 001"
```

### 4. Export for Monitoring
```bash
# Export pending payments to send to monitoring service
python tron_address_manager.py export-monitoring --filename payments_to_monitor.json
```

### 4. Send to Monitoring Service
```bash
# Send all pending payments to the monitoring service
python payment_integration.py batch --file payments_to_monitor.json

# Or send individual payments
python payment_integration.py send --payment-id 123
```

### 5. Check Status
```bash
# Check individual payment status
python payment_integration.py check --order-id ORDER001

# Check service health
python payment_integration.py health
```

## Advanced Features ⭐ NEW

### Mnemonic Phrase Wallet Generation

The `mnemonic_wallet_generator.py` script provides industry-standard BIP39 mnemonic phrase wallet generation:

```bash
# Generate wallets with 12-word mnemonic phrases
python mnemonic_wallet_generator.py generate --count 5 --label "Production Wallets"

# Restore wallets from existing mnemonic (for multi-device setup)
python mnemonic_wallet_generator.py restore "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about" --count 10

# List all generated wallets
python mnemonic_wallet_generator.py list

# Create encrypted backup
python mnemonic_wallet_generator.py backup --dir secure_backups
```

### QR Code Export

Export wallet information as QR codes for easy import into mobile wallets:

```bash
# Professional QR code images (recommended - requires qrcode and PIL)
python real_qr_generator.py --wallet-id 123 --output-dir wallet_qr_codes/

# QR codes with custom styling
python real_qr_generator.py --wallet-id 123 --style rounded --label "Wallet 123" --output-dir styled_qr/

# Complete wallet import sheet with all QR codes
python real_qr_generator.py --wallet-id 123 --import-sheet --output-dir import_sheets/

# Batch generate QR codes for multiple wallets
python real_qr_generator.py --batch-wallets 1,2,3,4,5 --output-dir batch_qr/

# Export QR codes from mnemonic wallet generator (also uses real QR if available)
python mnemonic_wallet_generator.py export-qr 123 --dir wallet_qr_codes

# Create simple text-based QR codes (fallback - no dependencies required)
python simple_qr_generator.py --wallet-id 123 --type all

# Generate QR for any custom data
python real_qr_generator.py --data "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t" --style circle --label "Custom Address"
```

### Wallet Import Formats

Export wallets in formats compatible with popular TRON wallets:

```bash
# Export for TronLink wallet
python mnemonic_wallet_generator.py export-import 123 --format tronlink

# Export all supported formats
python mnemonic_wallet_generator.py export-import 123 --format all

# Export mnemonic-only format
python mnemonic_wallet_generator.py export-import 123 --format mnemonic
```

### Enhanced Security Features

1. **BIP39 Mnemonic Phrases**: Industry-standard 12-word recovery phrases
2. **HD Wallet Derivation**: BIP44 hierarchical deterministic wallets
3. **Passphrase Support**: Optional additional passphrase protection
4. **Multiple Export Formats**: Compatible with major TRON wallets
5. **Encrypted Backups**: JSON backup files with all wallet data

## Enhanced Dependencies

### Core Dependencies (always available)
- `sqlite3` (built-in with Python)
- `json` (built-in with Python)

### Optional Dependencies (enhanced features)
- `mnemonic` - BIP39 mnemonic phrase generation
- `hdwallet` - HD wallet derivation (BIP44 standard)
- `qrcode[pil]` - Professional QR code generation
- `Pillow` - Image processing for QR codes
- `cryptography` - Enhanced cryptographic security
- `ecdsa` - Elliptic curve digital signatures

### Installation Options

```bash
# Install all dependencies for full functionality
pip install -r requirements.txt

# Or install specific feature sets
pip install mnemonic hdwallet  # Mnemonic and HD wallet features
pip install qrcode[pil] Pillow  # QR code generation

# For Ubuntu/Debian - install system packages for QR code generation
sudo apt update && sudo apt install python3-qrcode python3-pil
```

## Demo Scripts

### `demo_real_qr.py` ⭐ NEW

Comprehensive demonstration of all real QR code generation features.

**Features:**

- Showcases all visual styles (default, rounded, circle, square, bars)
- Demonstrates batch QR code generation
- Shows wallet import sheet creation
- Tests integration with wallet database

**Usage:**

```bash
# Run complete demo of real QR code features
python demo_real_qr.py

# The demo will:
# 1. Test QR code library availability
# 2. Generate sample QR codes with all styles
# 3. Create QR codes for a test wallet from database
# 4. Generate wallet import sheets
# 5. Show file locations and scanning instructions
```

### `create_test_wallet.py` ⭐ NEW

Utility script to create test wallets in the database for testing QR code generation.

**Usage:**

```bash
# Create a test wallet with predefined mnemonic
python create_test_wallet.py

# Creates wallet with ID 1 in mnemonic_wallets.db for testing
```

## Security Best Practices

### Mnemonic Phrase Security
1. **Never share mnemonic phrases** - They provide full wallet access
2. **Store offline** - Keep backup copies in secure physical locations
3. **Use passphrases** - Add extra security with BIP39 passphrases
4. **Test recovery** - Verify mnemonic phrases work before using wallets

### Private Key Management
1. **Generate offline** - Use air-gapped computers for production wallets
2. **Encrypt storage** - Use proper encryption for private key files
3. **Limited exposure** - Only export private keys when necessary
4. **Secure deletion** - Properly wipe temporary files

### QR Code Security
1. **Secure storage** - QR code images contain sensitive data
2. **Limited sharing** - Only share address QR codes publicly
3. **Screen protection** - Be careful when displaying QR codes
4. **Temporary files** - Clean up QR code images after use

## Complete Integration Workflow

### 1. Initial Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Generate production wallets
python mnemonic_wallet_generator.py generate --count 20 --label "CustomerPayments"

# Create backups
python mnemonic_wallet_generator.py backup
```

### 2. Address Management Integration
```bash
# Export wallet addresses to address manager
python mnemonic_wallet_generator.py list > wallet_list.txt

# Add addresses to payment system (manual step - copy addresses)
python tron_address_manager.py add-real [ADDRESS] --label "Generated Wallet"
```

### 3. Payment Request Creation
```bash
# Create payment requests using generated addresses
python tron_address_manager.py payment --amount 100.00 --order-id "ORDER001" --callback "https://example.com/webhook"

# Export for monitoring service
python tron_address_manager.py export-monitoring
```

### 4. Customer Wallet Import

```bash
# Generate professional QR codes for customer wallet import (recommended)
python real_qr_generator.py --wallet-id 123 --output-dir customer_qr/

# Generate complete wallet import sheet with styling
python real_qr_generator.py --wallet-id 123 --import-sheet --style rounded --output-dir import_sheets/

# Or create simple text QR codes (fallback)
python simple_qr_generator.py --wallet-id 123 --export-urls
```

### 5. Monitoring and Status
```bash
# Send to monitoring service
python payment_integration.py batch --file monitoring_requests.json

# Check payment status
python payment_integration.py check --order-id ORDER001
```

## Database Structure for Enhanced Features

### Mnemonic Wallets Database (`mnemonic_wallets.db`)
```sql
CREATE TABLE wallets (
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
);
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Install missing dependencies with `pip install -r requirements.txt`
2. **QR Code Generation Fails**: Ensure PIL/Pillow is installed correctly
3. **Mnemonic Validation Errors**: Verify word list and spelling
4. **Database Locked**: Close other applications using the database file
5. **Permission Errors**: Ensure write access to output directories

### Debug Mode

Enable verbose output for troubleshooting:
```bash
# Add debug flag to any command
python mnemonic_wallet_generator.py generate --count 1 --debug

# Check database contents
python -c "import sqlite3; conn = sqlite3.connect('mnemonic_wallets.db'); print(conn.execute('SELECT COUNT(*) FROM wallets').fetchone())"
```

## Notes

- **Mnemonic phrases are cryptographically secure** and suitable for production use
- **QR codes contain sensitive information** - handle appropriately
- **HD wallet derivation follows BIP44 standard** for maximum compatibility
- **All tools maintain backwards compatibility** with existing address manager
- **Database files contain sensitive data** - implement proper security measures
- **Real QR code generator creates PNG images** - requires qrcode and PIL libraries
- **Simple QR code generator provides text fallback** - works without image dependencies

## Generated Files and Directories

The real QR code generator creates the following file structure:

```text
client/
├── real_qr_generator.py          # Main QR generator script
├── demo_real_qr.py               # Demo script
├── create_test_wallet.py         # Test wallet utility
├── mnemonic_wallets.db           # Wallet database
├── demo_wallet_qr/               # Demo QR codes
│   ├── address_qr_default.png
│   ├── address_qr_rounded.png
│   ├── address_qr_circle.png
│   ├── address_qr_square.png
│   └── address_qr_bars.png
├── qr_test/                      # Test wallet QR codes
│   ├── wallet_1_address.png
│   ├── wallet_1_private_key.png
│   ├── wallet_1_mnemonic.png
│   └── wallet_1_import_sheet.png
└── enhanced_qr/                  # Mnemonic generator QR output
    └── wallet_*.png
```

**QR Code File Naming Convention:**

- `wallet_{id}_address.png` - Address QR code
- `wallet_{id}_private_key.png` - Private key QR code
- `wallet_{id}_mnemonic.png` - Mnemonic phrase QR code
- `wallet_{id}_import_sheet.png` - Complete wallet import sheet

**Security Note:** All generated QR code PNG files contain sensitive wallet information. Store securely and delete after use if not needed permanently.
