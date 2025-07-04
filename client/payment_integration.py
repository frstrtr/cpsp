#!/usr/bin/env python3
"""
Payment Service Integration Script

This script integrates the client-side address manager with the main payment
monitoring service. It can:
1. Send payment requests to the monitoring service
2. Check payment status
3. Batch process multiple payments

Usage:
    python payment_integration.py send --payment-id 123
    python payment_integration.py check --order-id ORDER123
    python payment_integration.py batch --file monitoring_requests.json
"""

import json
import requests
import argparse
from typing import Dict, List, Optional
from tron_address_manager import TronAddressManager

class PaymentServiceIntegration:
    """Integration with the main TRON payment monitoring service"""
    
    def __init__(self, service_url: str = "http://localhost:5000"):
        self.service_url = service_url.rstrip('/')
        self.manager = TronAddressManager()
    
    def send_payment_request(self, payment_data: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Send a payment request to the monitoring service"""
        url = f"{self.service_url}/create_payment"
        
        try:
            response = requests.post(url, json=payment_data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error sending payment request: {e}")
            return None
    
    def check_payment_status(self, payment_id: str) -> Optional[Dict[str, str]]:
        """Check payment status from the monitoring service"""
        url = f"{self.service_url}/payment_status/{payment_id}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error checking payment status: {e}")
            return None
    
    def check_service_health(self) -> Optional[Dict[str, str]]:
        """Check if the monitoring service is healthy"""
        url = f"{self.service_url}/health"
        
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Service health check failed: {e}")
            return None
    
    def send_payment_by_id(self, payment_id: str) -> bool:
        """Send a specific payment request by local payment ID"""
        # Get payment from local database
        payments = self.manager.list_payments('pending')
        payment = next((p for p in payments if p['payment_id'] == payment_id), None)
        
        if not payment:
            print(f"❌ Payment ID {payment_id} not found or not pending")
            return False
        
        # Prepare request data
        request_data = {
            'wallet_address': payment['address'],
            'expected_amount_usdt': float(payment['expected_amount']),
            'callback_url': payment['callback_url'] or 'https://example.com/webhook',
            'order_id': payment['order_id']
        }
        
        print(f"🔄 Sending payment request for order {payment['order_id']}...")
        
        # Send to monitoring service
        result = self.send_payment_request(request_data)
        
        if result:
            print(f"✅ Payment request sent successfully:")
            print(f"   Service Payment ID: {result.get('payment_id')}")
            print(f"   Status: {result.get('status')}")
            print(f"   Message: {result.get('message')}")
            return True
        else:
            print(f"❌ Failed to send payment request")
            return False
    
    def batch_send_payments(self, filename: str) -> Dict[str, int]:
        """Send multiple payment requests from a JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                payments = json.load(f)
        except Exception as e:
            print(f"❌ Error reading file {filename}: {e}")
            return {'sent': 0, 'failed': 0}
        
        if not isinstance(payments, list):
            print(f"❌ File must contain a JSON array of payment requests")
            return {'sent': 0, 'failed': 0}
        
        print(f"🔄 Sending {len(payments)} payment requests...")
        
        sent = 0
        failed = 0
        
        for i, payment in enumerate(payments, 1):
            print(f"Processing payment {i}/{len(payments)}: {payment.get('order_id', 'Unknown')}")
            
            result = self.send_payment_request(payment)
            if result:
                print(f"   ✅ Sent successfully (Service ID: {result.get('payment_id')})")
                sent += 1
            else:
                print(f"   ❌ Failed to send")
                failed += 1
        
        print(f"\n📊 Batch Results: {sent} sent, {failed} failed")
        return {'sent': sent, 'failed': failed}
    
    def find_payment_by_order_id(self, order_id: str) -> Optional[Dict[str, str]]:
        """Find a local payment by order ID"""
        payments = self.manager.list_payments()
        return next((p for p in payments if p['order_id'] == order_id), None)

def main():
    parser = argparse.ArgumentParser(
        description='Payment Service Integration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check if monitoring service is running
  python payment_integration.py health

  # Send a specific payment request
  python payment_integration.py send --payment-id 123

  # Check payment status by order ID
  python payment_integration.py check --order-id ORDER123

  # Send all pending payments in batch
  python payment_integration.py batch --file monitoring_requests.json

  # Check service statistics
  python payment_integration.py stats
        """
    )
    
    parser.add_argument('--service-url', default='http://localhost:5000', 
                       help='Base URL of the monitoring service')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Health check
    subparsers.add_parser('health', help='Check monitoring service health')
    
    # Send payment
    send_parser = subparsers.add_parser('send', help='Send payment request to monitoring service')
    send_parser.add_argument('--payment-id', required=True, help='Local payment ID to send')
    
    # Check status
    check_parser = subparsers.add_parser('check', help='Check payment status')
    check_group = check_parser.add_mutually_exclusive_group(required=True)
    check_group.add_argument('--payment-id', help='Service payment ID')
    check_group.add_argument('--order-id', help='Order ID to look up')
    
    # Batch send
    batch_parser = subparsers.add_parser('batch', help='Send multiple payments from file')
    batch_parser.add_argument('--file', required=True, help='JSON file with payment requests')
    
    # Service stats
    subparsers.add_parser('stats', help='Get monitoring service statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    integration = PaymentServiceIntegration(args.service_url)
    
    if args.command == 'health':
        print("🔄 Checking monitoring service health...")
        health = integration.check_service_health()
        if health:
            print("✅ Service is healthy:")
            print(f"   Status: {health.get('status')}")
            print(f"   Active Payments: {health.get('active_payments')}")
            print(f"   Total Payments: {health.get('total_payments')}")
            print(f"   Database: {health.get('database')}")
        else:
            print("❌ Service is not accessible")
    
    elif args.command == 'send':
        success = integration.send_payment_by_id(args.payment_id)
        if not success:
            exit(1)
    
    elif args.command == 'check':
        if args.payment_id:
            # Check by service payment ID
            print(f"🔄 Checking payment status for ID {args.payment_id}...")
            status = integration.check_payment_status(args.payment_id)
            if status:
                print("✅ Payment status:")
                print(f"   Order ID: {status.get('order_id')}")
                print(f"   Address: {status.get('wallet_address')}")
                print(f"   Expected: {status.get('expected_amount_usdt')} USDT")
                print(f"   Status: {status.get('status')}")
                if status.get('transaction_hash'):
                    print(f"   Transaction: {status.get('transaction_hash')}")
            else:
                print("❌ Payment not found or service error")
        
        elif args.order_id:
            # Find local payment first, then check service
            payment = integration.find_payment_by_order_id(args.order_id)
            if payment:
                print(f"✅ Found local payment for order {args.order_id}:")
                print(f"   Local Payment ID: {payment['payment_id']}")
                print(f"   Address: {payment['address']}")
                print(f"   Expected: {payment['expected_amount']} USDT")
                print(f"   Status: {payment['status']}")
            else:
                print(f"❌ No local payment found for order ID: {args.order_id}")
    
    elif args.command == 'batch':
        results = integration.batch_send_payments(args.file)
        if results['failed'] > 0:
            exit(1)
    
    elif args.command == 'stats':
        print("🔄 Getting service statistics...")
        try:
            response = requests.get(f"{integration.service_url}/stats", timeout=10)
            response.raise_for_status()
            stats = response.json()
            print("✅ Service statistics:")
            print(f"   Total Payments: {stats.get('total_payments', 0)}")
            print(f"   Pending: {stats.get('pending_payments', 0)}")
            print(f"   Completed: {stats.get('completed_payments', 0)}")
            print(f"   Failed: {stats.get('failed_payments', 0)}")
            print(f"   Polling Interval: {stats.get('polling_interval', 0)}s")
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")

if __name__ == '__main__':
    main()
