import os
from typing import List, Dict

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
BOT_USERNAME = os.getenv("BOT_USERNAME", "ssh_v2ray_bot")

# Database Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://username:password@cluster.mongodb.net/")
DB_NAME = os.getenv("DB_NAME", "sshbot")

# Admin Configuration
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "123456789")
try:
    ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_STR.split(",") if x.strip()]
except ValueError:
    ADMIN_IDS = [123456789]  # Default admin ID

# Sponsor Channels (Replace with your actual channel IDs)
CHANNELS = [
    {"id": -1001234567890, "name": "Tech Channel", "url": "https://t.me/tech_channel"},
    {"id": -1009876543210, "name": "VPN Updates", "url": "https://t.me/vpn_updates"}
]

# Points Configuration
POINTS_CONFIG = {
    "referral": 1,          # Points for each successful referral
    "channel_join": 2,      # Points for joining all channels
    "daily_bonus": 1,       # Daily bonus points (future feature)
    "config_cost": 1        # Points required to generate config
}

# Provider URLs (Add more as needed)
SSH_PROVIDERS = [
    {
        "name": "SpeedSSH",
        "url": "https://speedssh.com/create-ssh-server/sg1",
        "active": True
    },
    {
        "name": "FastSSH", 
        "url": "https://fastssh.com/create-ssh-server/sg",
        "active": True
    }
]

V2RAY_PROVIDERS = [
    {
        "name": "V2RayFree",
        "url": "https://v2rayfree.com/free-vmess",
        "active": True
    }
]

# Rate Limiting
RATE_LIMIT = {
    "requests_per_minute": 5,
    "max_configs_per_day": 10
}

# Messages
MESSAGES = {
    "welcome": """
🔐 **SSH/V2Ray Config Generator Bot**

Welcome! You get **1 FREE** config generation.

🎯 **How to earn more points:**
• 🔗 Refer friends: +{referral} point each
• 📢 Join sponsor channels: +{channel_join} points

**Commands:**
/generate - Generate SSH/V2Ray config
/points - Check your points
/refer - Get referral link
/join - Join channels for points
/help - Show this help

**Supported configs:** SSH, VMess, VLess
""".format(**POINTS_CONFIG),
    
    "insufficient_points": """
❌ **Insufficient Points!**

You need **{cost}** point(s) to generate a config.
Current points: **{current}**

💡 **Earn points by:**
• 🔗 Referring friends: +{referral} points each
• 📢 Joining sponsor channels: +{channel_join} points

Use /refer to get your referral link!
""",
    
    "join_channels": """
📢 **Join Sponsor Channels**

Please join **ALL** channels below to earn **{points}** points:

{channel_list}

After joining, use /join to verify and claim your points!
""",
    
    "generation_success": """
✅ **Config Generated Successfully!**

Points remaining: **{points}**

📋 **Config Details:**
{config}

💡 Save this config safely - it won't be shown again!
"""
}