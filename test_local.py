#!/usr/bin/env python3
"""
Local test script for Gmail Poller
This script helps test the Gmail poller locally with proper error handling
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("🔍 Checking prerequisites...")

    # Check Python
    try:
        result = subprocess.run([sys.executable, '--version'],
                              capture_output=True, text=True)
        print(f"✅ Python: {result.stdout.strip()}")
    except:
        print("❌ Python not found")
        return False

    # Check pip
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'],
                              capture_output=True, text=True)
        print(f"✅ pip: {result.stdout.strip().split()[1]}")
    except:
        print("❌ pip not found")
        return False

    # Check requirements.txt
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found")
        return False
    print("✅ requirements.txt found")

    # Check credentials.json
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found")
        print("   Please download from Google Cloud Console")
        return False
    print("✅ credentials.json found")

    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print(f"❌ Failed to install dependencies: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def setup_environment():
    """Set up the environment for testing"""
    print("\n🏗️ Setting up environment...")

    # Create directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    print("✅ Created data and logs directories")

    # Create .env if it doesn't exist
    if not os.path.exists('.env'):
        if os.path.exists('.env.local'):
            import shutil
            shutil.copy('.env.local', '.env')
            print("✅ Created .env from .env.local (local development config)")
        elif os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ Created .env from .env.example")
            print("   ⚠️ Please review and update .env with your settings")
        else:
            print("❌ No .env template found")
            return False
    else:
        print("✅ .env file exists")

    return True

def test_poller():
    """Test the Gmail poller"""
    print("\n🚀 Testing Gmail poller...")

    try:
        # Change to src directory and run poller
        os.chdir('src/orders/poller')
        result = subprocess.run([sys.executable, 'main.py'],
                              capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Poller executed successfully")
            print(f"   Output: {result.stdout}")
        else:
            print(f"❌ Poller failed with return code {result.returncode}")
            print(f"   Error: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error running poller: {e}")
        return False
    finally:
        os.chdir('../../')

    return True

def check_output():
    """Check the output files"""
    print("\n📋 Checking output files...")

    # Check emails.json
    if os.path.exists('data/emails.json'):
        try:
            with open('data/emails.json', 'r') as f:
                data = json.load(f)
            print(f"✅ Found {data.get('total_emails', 0)} emails in data/emails.json")
        except Exception as e:
            print(f"❌ Error reading emails.json: {e}")
    else:
        print("⚠️ No emails.json file found (expected if no new emails)")

    # Check logs
    log_file = 'logs/gmail_poller.log'
    if os.path.exists(log_file):
        print("✅ Log file created")
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
            print(f"   {len(lines)} log entries found")
        except Exception as e:
            print(f"❌ Error reading log file: {e}")
    else:
        print("⚠️ No log file found")

    return True

def main():
    """Main test function"""
    print("🧪 Gmail Poller Local Test")
    print("=" * 40)

    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above.")
        return False

    # Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies.")
        return False

    # Setup environment
    if not setup_environment():
        print("\n❌ Failed to setup environment.")
        return False

    # Test poller
    if not test_poller():
        print("\n❌ Poller test failed.")
        return False

    # Check output
    check_output()

    print("\n🎉 Local test completed!")
    print("\nNext steps:")
    print("1. Review the output in data/emails.json")
    print("2. Check the logs in logs/gmail_poller.log")
    print("3. Adjust .env settings as needed")
    print("4. Run 'python src/orders/poller/main.py' for subsequent tests")

    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)