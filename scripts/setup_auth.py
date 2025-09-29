#!/usr/bin/env python3
"""
Headless OAuth Setup Script for Gmail Poller
This script helps set up OAuth authentication for headless servers
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from orders.poller.gmail_client import GmailClient

def generate_auth_url():
    """Generate authorization URL for manual authentication"""
    print("🔐 Generating authorization URL...")

    try:
        client = GmailClient()
        auth_url = client.generate_auth_url()

        if auth_url:
            print("\n" + "="*80)
            print("📋 AUTHORIZATION URL")
            print("="*80)
            print(auth_url)
            print("="*80)
            print("\nInstructions:")
            print("1. Copy the URL above and open it in a browser")
            print("2. Sign in with your Google account")
            print("3. Grant permissions when prompted")
            print("4. Copy the authorization code from the page")
            print("5. Run this script again with --code <code>")
            print("\nExample:")
            print(f"python {__file__} --code '4/0Ab...'")
            print("="*80)

        return auth_url

    except Exception as e:
        print(f"❌ Failed to generate auth URL: {e}")
        return None

def setup_with_code(auth_code):
    """Setup authentication using authorization code"""
    print("🔑 Setting up authentication with code...")

    try:
        # Create data directory
        data_dir = './data'
        os.makedirs(data_dir, exist_ok=True)

        # Save auth code
        auth_code_file = os.path.join(data_dir, 'auth_code.txt')
        with open(auth_code_file, 'w') as f:
            f.write(auth_code)

        # Test authentication
        client = GmailClient(data_dir=data_dir)

        print("✅ Authentication successful!")
        print(f"📁 Auth code saved to: {auth_code_file}")

        # Test API access
        print("🧪 Testing API access...")
        emails = client.get_emails(max_results=1)
        print(f"✅ API access confirmed (found {len(emails)} emails)")

        # Export token for backup
        token_file = os.path.join(data_dir, 'exported_token.json')
        if client.export_token(token_file):
            print(f"📦 Token exported to: {token_file}")

        return True

    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

def import_token(token_file):
    """Import token from file"""
    print("📥 Importing token...")

    try:
        # Create data directory
        data_dir = './data'
        os.makedirs(data_dir, exist_ok=True)

        # Copy token file
        imported_token_file = os.path.join(data_dir, 'imported_token.json')
        import shutil
        shutil.copy2(token_file, imported_token_file)

        # Test authentication
        client = GmailClient(data_dir=data_dir)

        print("✅ Token import successful!")
        print(f"📁 Token imported to: {imported_token_file}")

        # Test API access
        print("🧪 Testing API access...")
        emails = client.get_emails(max_results=1)
        print(f"✅ API access confirmed (found {len(emails)} emails)")

        return True

    except Exception as e:
        print(f"❌ Token import failed: {e}")
        return False

def export_token():
    """Export current token"""
    print("📤 Exporting token...")

    try:
        client = GmailClient()
        output_file = './data/exported_token.json'

        if client.export_token(output_file):
            print(f"✅ Token exported to: {output_file}")
            return True
        else:
            print("❌ Failed to export token")
            return False

    except Exception as e:
        print(f"❌ Token export failed: {e}")
        return False

def check_setup():
    """Check current authentication setup"""
    print("🔍 Checking authentication setup...")

    data_dir = './data'
    files_to_check = [
        ('token.json', 'Active token'),
        ('auth_code.txt', 'Authorization code'),
        ('imported_token.json', 'Imported token'),
        ('exported_token.json', 'Exported token')
    ]

    found_files = []
    for filename, description in files_to_check:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            found_files.append((filename, description, size))

    if found_files:
        print(f"\n📁 Found {len(found_files)} authentication files:")
        for filename, description, size in found_files:
            print(f"  ✅ {filename} ({description}) - {size} bytes")

        # Test API access
        try:
            client = GmailClient()
            emails = client.get_emails(max_results=1)
            print(f"  ✅ API access working (found {len(emails)} emails)")
        except Exception as e:
            print(f"  ❌ API access failed: {e}")

    else:
        print("  ❌ No authentication files found")

    return len(found_files) > 0

def main():
    parser = argparse.ArgumentParser(description='Setup headless OAuth for Gmail Poller')
    parser.add_argument('--generate-url', action='store_true',
                       help='Generate authorization URL')
    parser.add_argument('--code', type=str,
                       help='Authorization code from Google')
    parser.add_argument('--import-token', type=str,
                       help='Import token from file')
    parser.add_argument('--export-token', action='store_true',
                       help='Export current token')
    parser.add_argument('--check', action='store_true',
                       help='Check current setup')

    args = parser.parse_args()

    if args.generate_url:
        generate_auth_url()
    elif args.code:
        setup_with_code(args.code)
    elif args.import_token:
        import_token(args.import_token)
    elif args.export_token:
        export_token()
    elif args.check:
        check_setup()
    else:
        # Show help
        print("🚀 Gmail Poller Headless OAuth Setup")
        print("=" * 50)
        print("\nFor headless servers (like Hetzner):")
        print("\n1. Generate authorization URL:")
        print(f"   python {__file__} --generate-url")
        print("\n2. Setup with authorization code:")
        print(f"   python {__file__} --code 'your_auth_code'")
        print("\n3. Import existing token:")
        print(f"   python {__file__} --import-token /path/to/token.json")
        print("\n4. Export current token:")
        print(f"   python {__file__} --export-token")
        print("\n5. Check setup:")
        print(f"   python {__file__} --check")

if __name__ == '__main__':
    main()