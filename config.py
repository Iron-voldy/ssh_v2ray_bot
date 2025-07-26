import os
from typing import List, Dict

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "7802887189:AAFFMqLcNPYT2oX7s0DieOGdmqFWk7M1VdI")
BOT_USERNAME = os.getenv("BOT_USERNAME", "Genarate_ssh_bot")

# Database Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://hasindutwm:20020224Ha@cluster0.dtfgi1z.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.getenv("DB_NAME", "sshbot")

# Admin Configuration
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "1234523543")
try:
    ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_STR.split(",") if x.strip()]
except ValueError:
    ADMIN_IDS = [1234523543]  # Default admin ID

# Sponsor Channels - Updated with actual channel info from env
CHANNELS = [
    {
        "id": int(os.getenv("CHANNEL_1_ID", "-1002614174192")),
        "name": os.getenv("CHANNEL_1_NAME", "💡 SoloBot Labs™"),
        "url": os.getenv("CHANNEL_1_URL", "https://t.me/solo_bot_labs")
    },
    {
        "id": int(os.getenv("CHANNEL_2_ID", "-1001641168678")),
        "name": os.getenv("CHANNEL_2_NAME", "⚜️ it's me ℍ𝕒𝕤𝕚𝕟𝕕𝕦 ⚜️"),
        "url": os.getenv("CHANNEL_2_URL", "https://t.me/Its_Me_Hasindu")
    }
]

# Points Configuration
POINTS_CONFIG = {
    "initial_coins": 0,     # Initial coins for new users
    "referral": 3,           # Points for each successful referral
    "channel_join": 5,       # Points for joining all channels
    "daily_bonus": 1,        # Daily bonus points (future feature)
    "config_cost": 5         # Points required to generate config
}

# Provider URLs - Updated with more reliable providers
SSH_PROVIDERS = [
    {
        "name": "SpeedSSH",
        "url": "https://speedssh.com/create-ssh-server/sg1",
        "active": True,
        "servers": ["sg1", "us1", "de1", "uk1"]
    },
    {
        "name": "FastSSH", 
        "url": "https://fastssh.com/create-ssh-server/sg",
        "active": True,
        "servers": ["sg", "us", "de", "uk"]
    },
    {
        "name": "OpenTunnel",
        "url": "https://opentunnel.net/create-ssh-server",
        "active": True,
        "servers": ["sg", "us", "de", "fr"]
    }
]

V2RAY_PROVIDERS = [
    {
        "name": "V2RayFree",
        "url": "https://v2rayfree.com/free-vmess",
        "active": True
    },
    {
        "name": "VPNJantit",
        "url": "https://vpnjantit.com/free-vmess",
        "active": True
    }
]

# Rate Limiting
RATE_LIMIT = {
    "requests_per_minute": 5,
    "max_configs_per_day": 10,
    "admin_unlimited": True
}

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# HTTP Client Configuration (Alternative to aiohttp)
HTTP_CONFIG = {
    "timeout": 30,
    "max_retries": 3,
    "backoff_factor": 0.3,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Messages
MESSAGES = {
    "welcome": """
🔐 **SSH/V2Ray Config Generator Bot**

Welcome! You get **{initial_coins} FREE coins** to start!

⚡ **Available File Types:**
• 🔐 SSH - Secure Shell tunneling
• 🚀 V2Ray - Advanced proxy configurations
• 📦 Service Packages: YouTube, WhatsApp, Zoom, Netflix & more

💰 **Credit System:**
• Each file costs **{config_cost} coins**
• New users get **{initial_coins} coins** FREE

🎯 **Earn More Coins:**
• 🔗 Refer friends: +{referral} coins each
• 📢 Join both channels: +{channel_join} coins

**Commands:**
/generate - Generate SSH/V2Ray file
/points - Check your coins
/help - Show help
""".format(**POINTS_CONFIG),
    
    "insufficient_points": """
❌ **Insufficient Coins!**

You need **{cost}** coins to generate a file.
Current coins: **{current}**

💡 **Earn coins by:**
• 🔗 Referring friends: +{referral} coins each
• 📢 Joining both sponsor channels: +{channel_join} coins

Use the buttons below to earn more coins!
""",
    
    "join_channels": """
📢 **Join Sponsor Channels**

Please join **ALL** channels below to earn **{points}** points:

{channel_list}

After joining all channels, click "✅ I Joined All Channels" to verify and claim your points!

💡 **Tips:**
• You must join ALL channels to get points
• Points are awarded once per user
• Use earned points to generate configs
""",
    
    "generation_success": """
✅ **Config Generated Successfully!**

Points remaining: **{points}**

📋 **Configuration Details:**
{config}

💡 **Important Notes:**
• Save this config safely - it won't be shown again!
• Config expires after 24-48 hours
• Generate new configs if old ones stop working

⚡ **Speed Test Tip:**
Try OpenSpeedTest.com or LibreSpeed.org for VPN-friendly speed tests!
""",

    "admin_welcome": """
👑 **Admin Panel Access**

Welcome, Admin! You have unlimited access to all bot features:

✅ **Admin Privileges:**
• Unlimited config generation
• Test all service packages
• Credit management system
• User management tools
• Access detailed statistics
• Speed test optimization enabled
• No rate limiting

**Admin Commands:**
/admin_credits - Get 1000 testing credits
/give_credits <user_id> <amount> - Give credits to any user
/check_user <user_id> - View user details
/admin_test - Test service packages

Use the Admin Panel button below for quick access!
""",

    "help": """
❓ **Help & Support**

**🔐 SSH Configs:**
• Use with Termux, ConnectBot, or SSH clients
• Connection: `ssh username@host -p port`
• Speed test: Use speedtest-cli or curl commands

**🚀 V2Ray Configs:**
• Compatible with HTTP Injector, V2RayNG
• Import VMess links directly
• Use provided payloads for HTTP Injector

**📱 HTTP Injector Setup:**
1. Install HTTP Injector app
2. Config → Import → VMess
3. Paste VMess link
4. Use provided payload
5. Connect and browse

**⚡ Speed Test Features:**
• Direct routing for speed test sites
• VPN-friendly: OpenSpeedTest.com, LibreSpeed.org
• Command line tools for SSH configs
• Mobile apps work better than web versions

**💰 Earning Points:**
• 1 FREE config for new users
• Refer friends: +{referral} point each
• Join channels: +{channel_join} points total

**🆘 Troubleshooting:**
• Generate new configs if old ones stop working
• Try different service packages
• Use alternative speed test sites
• Check your internet connection

**📞 Support:**
Join our channels for help and updates!
""".format(**POINTS_CONFIG)
}

# Speed Test Configuration
SPEED_TEST_CONFIG = {
    "enabled": True,
    "direct_domains": [
        "speedtest.net",
        "fast.com",
        "openspeedtest.com", 
        "librespeed.org",
        "speedof.me",
        "testmy.net"
    ],
    "direct_ports": [8080, 8081],
    "optimization_enabled": True
}

# Service Package Descriptions
SERVICE_DESCRIPTIONS = {
    "youtube": "Perfect for YouTube streaming and video content",
    "whatsapp": "Optimized for WhatsApp messaging and calls",
    "zoom": "Best for Zoom video conferencing",
    "facebook": "Facebook and Meta services",
    "instagram": "Instagram browsing and stories",
    "tiktok": "TikTok video streaming",
    "netflix": "Netflix and video streaming",
    "telegram": "Telegram messaging",
    "speedtest": "Speed testing and network diagnostics",
    "all_sites": "Universal access to all websites"
}