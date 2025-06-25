#!/usr/bin/env python3
"""
Quick fix script for Python 3.13 compatibility issues
This script updates python-telegram-bot and other dependencies
"""

import subprocess
import sys
import os

def run_command(command):
    """Run a command and return success status"""
    try:
        print(f"Running: {command}")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ Success: {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {command}")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("🔧 Fixing Python 3.13 compatibility issues...")
    print("=" * 50)
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️ Warning: Not in a virtual environment")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return
    
    # Update pip first
    print("\n1. Updating pip...")
    run_command("python -m pip install --upgrade pip")
    
    # Uninstall problematic version
    print("\n2. Uninstalling old python-telegram-bot...")
    run_command("pip uninstall python-telegram-bot -y")
    
    # Install compatible version
    print("\n3. Installing Python 3.13 compatible version...")
    if not run_command("pip install python-telegram-bot==21.0.1"):
        print("Trying alternative version...")
        run_command("pip install python-telegram-bot==20.8")
    
    # Install other dependencies
    print("\n4. Installing other dependencies...")
    dependencies = [
        "pymongo==4.6.1",
        "requests==2.31.0", 
        "beautifulsoup4==4.12.2",
        "python-dotenv==1.0.0",
        "httpx==0.25.2",
        "Pillow>=10.0.0",
        "qrcode[pil]==7.4.2",
        "lxml>=4.9.0",
        "cryptography>=41.0.0",
        "typing-extensions>=4.0.0"
    ]
    
    for dep in dependencies:
        run_command(f"pip install {dep}")
    
    print("\n5. Verifying installation...")
    try:
        import telegram
        print(f"✅ python-telegram-bot version: {telegram.__version__}")
    except ImportError as e:
        print(f"❌ Failed to import telegram: {e}")
        return
    
    # Test other imports
    test_imports = ["pymongo", "requests", "bs4", "qrcode", "PIL", "httpx"]
    for module in test_imports:
        try:
            __import__(module)
            print(f"✅ {module}: OK")
        except ImportError:
            print(f"❌ {module}: Failed")
    
    print("\n" + "=" * 50)
    print("🎉 Fix completed!")
    print("\nNext steps:")
    print("1. Update your requirements.txt with the new versions")
    print("2. Use the updated bot.py file")
    print("3. Run: python start.py")
    print("\nIf you still get errors, try:")
    print("- pip install --force-reinstall python-telegram-bot==21.0.1")
    print("- Or use Python 3.11 instead of 3.13")

if __name__ == "__main__":
    main()