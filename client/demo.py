#!/usr/bin/env python3
"""
Demo script showing client-side address management workflow
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tron_address_manager import TronAddressManager
import json

def demo_workflow():
    """Demonstrate the complete client-side workflow"""
    print("🚀 TRON Address Management Demo")
    print("=" * 50)
    
    # Initialize manager
    manager = TronAddressManager("demo_addresses.db")
    
    # Step 1: Create demo addresses
    print("\n📝 Step 1: Creating demo addresses...")
    addresses = manager.create_demo_addresses(5, "DemoWallet")
    print(f"Created {len(addresses)} demo addresses")
    
    # Step 2: Show statistics
    print("\n📊 Step 2: Current statistics...")
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"   {key.replace('_', ' ').title()}: {value}")
    
    # Step 3: Create payment requests
    print("\n💳 Step 3: Creating payment requests...")
    payments = [
        {"amount": 25.50, "order_id": "DEMO_ORDER_001", "callback": "https://webhook.site/demo1"},
        {"amount": 100.00, "order_id": "DEMO_ORDER_002", "callback": "https://webhook.site/demo2"},
        {"amount": 75.25, "order_id": "DEMO_ORDER_003", "callback": "https://webhook.site/demo3"},
    ]
    
    created_payments = []
    for payment_data in payments:
        payment = manager.create_payment_request(
            payment_data["amount"],
            payment_data["order_id"],
            payment_data["callback"],
            f"Demo payment for {payment_data['order_id']}"
        )
        if payment:
            created_payments.append(payment)
            print(f"   ✅ Created payment: {payment['order_id']} -> {payment['address']}")
        else:
            print(f"   ❌ Failed to create payment: {payment_data['order_id']}")
    
    # Step 4: List addresses and payments
    print("\n📋 Step 4: Current addresses...")
    addresses = manager.list_addresses()
    for addr in addresses[:3]:  # Show first 3
        status = "🔴 Used" if addr['is_used'] else "🟢 Available"
        print(f"   {addr['address'][:20]}... | {addr['label']} | {status}")
    
    print(f"\n💳 Step 5: Payment requests...")
    payments = manager.list_payments()
    for payment in payments:
        print(f"   {payment['order_id']} | {payment['expected_amount']} USDT | {payment['status']}")
    
    # Step 6: Export for monitoring service
    print("\n📤 Step 6: Exporting for monitoring service...")
    filename = manager.export_for_monitoring_service("demo_monitoring_export.json")
    print(f"   Exported to: {filename}")
    
    # Show the exported data
    with open(filename, 'r', encoding='utf-8') as f:
        exported_data = json.load(f)
    print(f"   Contains {len(exported_data)} pending payments ready for monitoring")
    
    # Step 7: Updated statistics
    print("\n📊 Step 7: Final statistics...")
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"   {key.replace('_', ' ').title()}: {value}")
    
    print("\n✅ Demo completed!")
    print("\nNext steps:")
    print("1. Use 'python payment_integration.py health' to check the monitoring service")
    print("2. Use 'python payment_integration.py batch --file demo_monitoring_export.json' to send payments")
    print("3. Monitor payments with the main service API")
    
    return filename

if __name__ == '__main__':
    demo_workflow()
