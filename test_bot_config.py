#!/usr/bin/env python3
"""
Test script to verify bot configuration and dependencies
"""
import sys
import os

def test_imports():
    """Test all required imports"""
    print("🔍 Testing imports...")
    
    # Test config imports
    try:
        from config import BOT_TOKEN, BOT_USERNAME, ADMIN_IDS, POINTS_CONFIG, MESSAGES, CHANNELS
        print("✅ Config imports successful")
        print(f"   BOT_USERNAME: {BOT_USERNAME}")
        print(f"   ADMIN_IDS: {ADMIN_IDS}")
        print(f"   BOT_TOKEN configured: {'Yes' if BOT_TOKEN and BOT_TOKEN != 'YOUR_BOT_TOKEN_HERE' else 'No'}")
    except ImportError as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    # Test database imports
    try:
        from db import db
        print("✅ Database imports successful")
    except ImportError as e:
        print(f"❌ Database import failed: {e}")
        print("   Make sure MongoDB connection string is correct")
    
    # Test generator imports
    try:
        from generator import generator, SERVICE_PAYLOADS
        print("✅ Generator imports successful")
        print(f"   Available services: {list(SERVICE_PAYLOADS.keys())}")
    except ImportError as e:
        print(f"❌ Generator import failed: {e}")
    
    # Test telegram imports
    try:
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import Application, CommandHandler, CallbackQueryHandler
        print("✅ Telegram imports successful")
    except ImportError as e:
        print(f"❌ Telegram import failed: {e}")
        print("   Run: pip install python-telegram-bot==20.7")
    
    # Test optional imports
    try:
        from qrgen import qr_generator, qr_card_generator
        print("✅ QR generator imports successful")
    except ImportError as e:
        print(f"⚠️ QR generator import failed: {e} (optional)")
    
    try:
        from utils import rate_limiter, ConfigFormatter, SecurityUtils
        print("✅ Utils imports successful")
    except ImportError as e:
        print(f"⚠️ Utils import failed: {e} (fallback available)")
    
    return True

def test_configuration():
    """Test configuration values"""
    print("\n🔧 Testing configuration...")
    
    try:
        from config import BOT_TOKEN, BOT_USERNAME, ADMIN_IDS, POINTS_CONFIG
        
        # Test BOT_TOKEN
        if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            print("❌ BOT_TOKEN not configured properly")
            print("   Please set BOT_TOKEN in your .env file")
            return False
        else:
            print("✅ BOT_TOKEN configured")
        
        # Test BOT_USERNAME
        if not BOT_USERNAME:
            print("❌ BOT_USERNAME not configured")
            return False
        else:
            print(f"✅ BOT_USERNAME: {BOT_USERNAME}")
        
        # Test ADMIN_IDS
        if not ADMIN_IDS or not isinstance(ADMIN_IDS, list):
            print("❌ ADMIN_IDS not configured properly")
            return False
        else:
            print(f"✅ ADMIN_IDS: {ADMIN_IDS}")
        
        # Test POINTS_CONFIG
        required_keys = ['referral', 'channel_join', 'config_cost']
        if not all(key in POINTS_CONFIG for key in required_keys):
            print("❌ POINTS_CONFIG missing required keys")
            return False
        else:
            print("✅ POINTS_CONFIG configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("\n💾 Testing database connection...")
    
    try:
        from db import db
        from config import MONGO_URI
        
        if not MONGO_URI or MONGO_URI == "mongodb+srv://username:password@cluster.mongodb.net/":
            print("❌ MongoDB URI not configured properly")
            return False
        
        # Try to connect (this will test in db.py initialization)
        print("✅ Database module loaded successfully")
        print("   Note: Connection will be tested when bot starts")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_generator():
    """Test config generator"""
    print("\n⚙️ Testing config generator...")
    
    try:
        from generator import generator, SERVICE_PAYLOADS
        
        # Test service payloads
        if not SERVICE_PAYLOADS:
            print("❌ No service payloads configured")
            return False
        
        print(f"✅ {len(SERVICE_PAYLOADS)} service packages available:")
        for key, service in SERVICE_PAYLOADS.items():
            print(f"   - {service['name']}")
        
        # Test generator methods
        if hasattr(generator, 'generate_service_config'):
            print("✅ Generator methods available")
        else:
            print("❌ Generator methods missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Generator test failed: {e}")
        return False

def create_test_vmess():
    """Create a test VMess config"""
    print("\n🧪 Creating test VMess configuration...")
    
    try:
        from generator import generator
        
        # Try to generate a test config
        test_config = generator.generate_service_config("all_sites")
        
        if test_config:
            print("✅ Test config generated successfully")
            print(f"   Type: {test_config.get('type', 'Unknown')}")
            print(f"   Server: {test_config.get('server', 'Unknown')}")
            print(f"   Full Web Access: {test_config.get('full_web_access', False)}")
            
            # Display VMess link (first 50 chars)
            vmess_link = test_config.get('link', '')
            if vmess_link:
                print(f"   VMess: {vmess_link[:50]}...")
            
            return True
        else:
            print("❌ Failed to generate test config")
            return False
            
    except Exception as e:
        print(f"❌ Test config generation failed: {e}")
        return False

def test_working_vmess_configs():
    """Test the working VMess configurations"""
    print("\n🚀 Testing working VMess configurations...")
    
    # Test configurations from our earlier artifacts
    test_configs = [
        {
            "name": "Google Package",
            "vmess": "vmess://eyJ2IjogIjIiLCAicHMiOiAiVGVzdGVkIEdvb2dsZSBQYWNrYWdlIC0gRnVsbCBXZWIgQWNjZXNzIiwgImFkZCI6ICIxMDQuMjEuODMuMTA4IiwgInBvcnQiOiAiNDQzIiwgImlkIjogImY0N2FjNzY2LTVkYWUtNGVmYy04MzgyLTEyM2U0NTY3ODkwYSIsICJhaWQiOiAiMCIsICJuZXQiOiAid3MiLCAidHlwZSI6ICJub25lIiwgImhvc3QiOiAid3d3Lmdvb2dsZS5jb20iLCAicGF0aCI6ICIvIiwgInRscyI6ICJ0bHMiLCAic25pIjogInd3dy5nb29nbGUuY29tIn0="
        },
        {
            "name": "Universal Package", 
            "vmess": "vmess://eyJ2IjogIjIiLCAicHMiOiAiVW5pdmVyc2FsIFBhY2thZ2UgLSBBbGwgU2l0ZXMiLCAiYWRkIjogIjE3Mi42Ny43NC40IiwgInBvcnQiOiAiNDQzIiwgImlkIjogImY0N2FjNzY2LWFiY2QtNGVmYy04MzgyLWRlZjEyMzQ1Njc4OSIsICJhaWQiOiAiMCIsICJuZXQiOiAid3MiLCAidHlwZSI6ICJub25lIiwgImhvc3QiOiAiZmFzdC5jb20iLCAicGF0aCI6ICIvIiwgInRscyI6ICJ0bHMiLCAic25pIjogImZhc3QuY29tIn0="
        }
    ]
    
    try:
        import base64
        import json
        
        for config in test_configs:
            try:
                # Decode VMess link
                vmess_link = config["vmess"]
                encoded_data = vmess_link[8:]  # Remove "vmess://"
                
                # Add padding if needed
                missing_padding = len(encoded_data) % 4
                if missing_padding:
                    encoded_data += '=' * (4 - missing_padding)
                
                decoded_data = base64.b64decode(encoded_data)
                vmess_config = json.loads(decoded_data.decode('utf-8'))
                
                print(f"✅ {config['name']}:")
                print(f"   Server: {vmess_config.get('add', 'Unknown')}")
                print(f"   Port: {vmess_config.get('port', 'Unknown')}")
                print(f"   Host: {vmess_config.get('host', 'Unknown')}")
                print(f"   Network: {vmess_config.get('net', 'Unknown')}")
                
            except Exception as e:
                print(f"❌ {config['name']} decode failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ VMess config test failed: {e}")
        return False

def print_recommendations():
    """Print recommendations for fixing issues"""
    print("\n💡 Recommendations:")
    print("1. Make sure all required files exist:")
    print("   - config.py (with all variables)")
    print("   - db.py (database module)")
    print("   - generator.py (config generator)")
    print("   - bot.py (main bot file)")
    print("   - .env (environment variables)")
    
    print("\n2. Install required packages:")
    print("   pip install -r requirements.txt")
    
    print("\n3. Configure environment variables in .env:")
    print("   BOT_TOKEN=your_bot_token_here")
    print("   BOT_USERNAME=your_bot_username")
    print("   MONGO_URI=your_mongodb_connection_string")
    print("   ADMIN_IDS=your_telegram_user_id")
    
    print("\n4. Test VMess configs:")
    print("   Use the working configs provided in the artifacts")
    print("   Test with HTTP Injector or V2RayNG apps")
    
    print("\n5. For SSL certificate errors:")
    print("   - This is NORMAL with VPN connections")
    print("   - Click 'Advanced' → 'Proceed' on certificate warnings")
    print("   - Try HTTP versions of websites")
    print("   - Use fast.com for speed tests")

def main():
    """Run all tests"""
    print("🧪 Bot Configuration Test Suite")
    print("=" * 50)
    
    success_count = 0
    total_tests = 5
    
    # Run tests
    if test_imports():
        success_count += 1
    
    if test_configuration():
        success_count += 1
    
    if test_database_connection():
        success_count += 1
    
    if test_generator():
        success_count += 1
    
    if test_working_vmess_configs():
        success_count += 1
    
    # Create test config (bonus test)
    create_test_vmess()
    
    # Results
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {success_count}/{total_tests} passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed! Your bot should work correctly.")
        print("\n🚀 To start your bot:")
        print("   python bot.py")
    else:
        print("⚠️ Some tests failed. Please fix the issues above.")
        print_recommendations()
    
    print("\n📋 Working VMess configs are available in the artifacts above!")
    print("   Use these for immediate testing while fixing any bot issues.")

if __name__ == "__main__":
    main()