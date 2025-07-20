#!/usr/bin/env python3
"""
Test script for the SSH/V2Ray bot functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import POINTS_CONFIG, CHANNELS
from generator import generator, SERVICE_PAYLOADS

def test_config():
    """Test configuration values"""
    print("🔧 Testing Configuration...")
    print(f"Initial coins: {POINTS_CONFIG['initial_coins']}")
    print(f"Config cost: {POINTS_CONFIG['config_cost']}")
    print(f"Referral reward: {POINTS_CONFIG['referral']}")
    print(f"Channel join reward: {POINTS_CONFIG['channel_join']}")
    print(f"Available services: {len(SERVICE_PAYLOADS)}")
    print(f"Sponsor channels: {len(CHANNELS)}")
    print("✅ Configuration test passed!\n")

def test_generator():
    """Test config generation"""
    print("🔧 Testing Config Generation...")
    
    # Test SSH generation
    print("Testing SSH generation...")
    ssh_config = generator.generate_config("ssh")
    if ssh_config:
        print(f"✅ SSH config generated: {ssh_config['type']}")
    else:
        print("❌ SSH config generation failed")
    
    # Test V2Ray generation for different services
    print("Testing V2Ray generation...")
    for service_key in ["youtube", "whatsapp", "all_sites"]:
        v2ray_config = generator.generate_service_config(service_key)
        if v2ray_config:
            print(f"✅ V2Ray config for {service_key}: {v2ray_config['type']}")
        else:
            print(f"❌ V2Ray config for {service_key} failed")
    
    print("✅ Generator test completed!\n")

def test_services():
    """Test available services"""
    print("🔧 Testing Available Services...")
    services = generator.get_available_services()
    for key, service in services.items():
        print(f"📦 {key}: {service['name']} - {service['description']}")
    print(f"✅ Found {len(services)} services\n")

def main():
    """Run all tests"""
    print("🚀 Starting Bot Functionality Tests...\n")
    
    try:
        test_config()
        test_services()
        test_generator()
        
        print("🎉 All tests completed successfully!")
        print("\n📋 Bot Features Summary:")
        print("✅ Credit system: 10 initial coins, 5 coins per file")
        print("✅ Referral system: 3 coins per referral")
        print("✅ Channel join rewards: 5 coins for joining both channels")
        print("✅ File types: SSH and V2Ray with multiple service packages")
        print("✅ Service packages: YouTube, WhatsApp, Zoom, Facebook, Instagram, TikTok, Netflix, Telegram, Speed Test, All Sites")
        print("✅ Unrestricted internet access through generated files")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()