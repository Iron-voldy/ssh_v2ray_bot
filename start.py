#!/usr/bin/env python3
"""
SSH/V2Ray Config Generator Bot Startup Script
This script handles initialization, health checks, and graceful startup
"""

import os
import sys
import time
import logging
import asyncio
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def setup_logging():
    """Setup logging configuration"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('bot.log', mode='a', encoding='utf-8')
        ]
    )
    
    # Reduce noise from some libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set"""
    logger = logging.getLogger(__name__)
    
    required_vars = [
        'BOT_TOKEN',
        'BOT_USERNAME',
        'MONGO_URI',
        'DB_NAME',
        'ADMIN_IDS'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file or environment configuration")
        return False
    
    # Validate BOT_TOKEN format
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token or ':' not in bot_token or len(bot_token) < 40:
        logger.error("Invalid BOT_TOKEN format. Please check your token.")
        return False
    
    # Validate MONGO_URI format
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri or not mongo_uri.startswith(('mongodb://', 'mongodb+srv://')):
        logger.error("Invalid MONGO_URI format. Please check your database connection string.")
        return False
    
    logger.info("Environment validation passed ✅")
    return True

def check_dependencies():
    """Check if all required dependencies are available"""
    logger = logging.getLogger(__name__)
    
    # Updated list without aiohttp - using httpx instead
    required_modules = [
        'telegram',
        'pymongo',
        'requests',
        'beautifulsoup4',
        'qrcode',
        'PIL',
        'dotenv',
        'httpx'  # Using httpx instead of aiohttp
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            if module == 'beautifulsoup4':
                import bs4
            elif module == 'PIL':
                import PIL
            elif module == 'dotenv':
                import dotenv
            else:
                __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        logger.error(f"Missing required modules: {', '.join(missing_modules)}")
        logger.error("Please install them using: pip install -r requirements.txt")
        return False
    
    logger.info("Dependency check passed ✅")
    return True

def test_database_connection():
    """Test database connection"""
    logger = logging.getLogger(__name__)
    
    try:
        from pymongo import MongoClient
        mongo_uri = os.getenv('MONGO_URI')
        db_name = os.getenv('DB_NAME')
        
        logger.info("Testing database connection...")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        
        # Test database access
        db = client[db_name]
        db.test_collection.find_one()
        
        logger.info("Database connection successful ✅")
        client.close()
        return True
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.error("Please check your MONGO_URI and database accessibility")
        return False

def test_telegram_connection():
    """Test Telegram bot token"""
    logger = logging.getLogger(__name__)
    
    try:
        import requests
        bot_token = os.getenv('BOT_TOKEN')
        
        logger.info("Testing Telegram bot token...")
        
        # Test bot token with getMe API call
        response = requests.get(
            f"https://api.telegram.org/bot{bot_token}/getMe",
            timeout=10
        )
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                username = bot_info['result']['username']
                logger.info(f"Telegram bot connection successful ✅ (@{username})")
                return True
        
        logger.error("Invalid bot token or Telegram API error")
        logger.error(f"Response: {response.status_code} - {response.text}")
        return False
        
    except Exception as e:
        logger.error(f"Telegram connection test failed: {e}")
        return False

def initialize_database():
    """Initialize database collections and indexes"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Initializing database...")
        from db import db
        
        # The db module will handle initialization in its __init__
        # This is just to trigger the connection and index creation
        db.get_user_stats()
        
        logger.info("Database initialization completed ✅")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def test_config_generation():
    """Test config generation functionality"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Testing config generation...")
        from generator import generator
        
        # Test if generator can be imported and initialized
        services = generator.get_available_services()
        if services and len(services) > 0:
            logger.info(f"Config generator ready with {len(services)} service packages ✅")
            return True
        else:
            logger.warning("Config generator has no services available")
            return False
        
    except Exception as e:
        logger.error(f"Config generation test failed: {e}")
        return False

def main():
    """Main startup function"""
    print("🚀 Starting SSH/V2Ray Config Generator Bot...")
    print("=" * 60)
    
    # Setup logging
    logger = setup_logging()
    logger.info("Bot startup initiated")
    
    # Run health checks
    checks = [
        ("Environment Variables", check_environment),
        ("Dependencies", check_dependencies),
        ("Database Connection", test_database_connection),
        ("Telegram Connection", test_telegram_connection),
        ("Database Initialization", initialize_database),
        ("Config Generation", test_config_generation)
    ]
    
    for check_name, check_func in checks:
        logger.info(f"Running {check_name} check...")
        if not check_func():
            logger.error(f"❌ {check_name} check failed!")
            logger.error("Bot startup aborted. Please fix the issues above.")
            
            # Provide specific help for common issues
            if check_name == "Dependencies":
                logger.info("\n💡 Quick fixes:")
                logger.info("- Run: pip install httpx python-telegram-bot pymongo requests beautifulsoup4")
                logger.info("- Or: pip install -r requirements.txt")
            elif check_name == "Database Connection":
                logger.info("\n💡 Database help:")
                logger.info("- Check your MONGO_URI in .env file")
                logger.info("- Ensure MongoDB Atlas allows connections from your IP")
                logger.info("- Test connection manually with MongoDB Compass")
            elif check_name == "Telegram Connection":
                logger.info("\n💡 Telegram help:")
                logger.info("- Check your BOT_TOKEN in .env file")
                logger.info("- Get a new token from @BotFather if needed")
                logger.info("- Ensure token format: 123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
            
            sys.exit(1)
        time.sleep(0.5)  # Small delay for readability
    
    logger.info("All startup checks passed! 🎉")
    logger.info("=" * 60)
    
    # Display startup summary
    print("\n✅ **Bot Status:**")
    print("• Environment: Ready")
    print("• Dependencies: Installed")
    print("• Database: Connected")
    print("• Telegram API: Authenticated")
    print("• Config Generator: Loaded")
    print("• Service Packages: Available")
    print("\n🚀 Starting bot application...")
    
    # Import and start the bot
    try:
        from bot import main as bot_main
        logger.info("Starting bot application...")
        bot_main()
        
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
        print("\n👋 Bot stopped by user. Goodbye!")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error during bot execution: {e}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"\n❌ Fatal error: {e}")
        print("Check bot.log for detailed error information.")
        sys.exit(1)

if __name__ == "__main__":
    main()