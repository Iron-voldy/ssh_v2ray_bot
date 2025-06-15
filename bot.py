import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict
import io
import urllib.parse

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)
from telegram.error import TelegramError

# Import our modules
from config import *
from db import db
from generator import generator
from qrgen import qr_generator, qr_card_generator
from utils import (
    rate_limiter, ConfigFormatter, MessageValidator, 
    SecurityUtils, TimeUtils, stats_collector, rate_limit
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Service packages configuration
SERVICE_PACKAGES = {
    "youtube": {
        "name": "🎥 YouTube Package",
        "hosts": ["www.youtube.com", "m.youtube.com", "youtube.com", "youtu.be"],
        "description": "Optimized for YouTube streaming",
        "emoji": "🎥"
    },
    "whatsapp": {
        "name": "💬 WhatsApp Package", 
        "hosts": ["web.whatsapp.com", "whatsapp.com", "wa.me"],
        "description": "Optimized for WhatsApp messaging",
        "emoji": "💬"
    },
    "zoom": {
        "name": "📹 Zoom Package",
        "hosts": ["zoom.us", "us02web.zoom.us", "us04web.zoom.us"],
        "description": "Optimized for Zoom video calls",
        "emoji": "📹"
    },
    "facebook": {
        "name": "📘 Facebook Package",
        "hosts": ["www.facebook.com", "m.facebook.com", "facebook.com"],
        "description": "Optimized for Facebook browsing",
        "emoji": "📘"
    },
    "instagram": {
        "name": "📸 Instagram Package",
        "hosts": ["www.instagram.com", "instagram.com"],
        "description": "Optimized for Instagram browsing",
        "emoji": "📸"
    },
    "tiktok": {
        "name": "🎵 TikTok Package",
        "hosts": ["www.tiktok.com", "tiktok.com"],
        "description": "Optimized for TikTok videos",
        "emoji": "🎵"
    },
    "netflix": {
        "name": "🎬 Netflix Package",
        "hosts": ["www.netflix.com", "netflix.com"],
        "description": "Optimized for Netflix streaming",
        "emoji": "🎬"
    },
    "telegram": {
        "name": "✈️ Telegram Package",
        "hosts": ["web.telegram.org", "telegram.org"],
        "description": "Optimized for Telegram Web",
        "emoji": "✈️"
    },
    "all_sites": {
        "name": "🌐 All Sites Package",
        "hosts": ["*"],
        "description": "Works with all websites",
        "emoji": "🌐"
    }
}

class SSHVPNBot:
    def __init__(self):
        self.application = None
        self.formatter = ConfigFormatter()
        
    def initialize(self):
        """Initialize the bot - synchronous version"""
        try:
            self.application = Application.builder().token(BOT_TOKEN).build()
            logger.info("Bot application created successfully")
            
        except Exception as e:
            logger.error("Error initializing bot: {}".format(e))
            raise

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return SecurityUtils.is_admin(user_id, ADMIN_IDS)

    # Command Handlers
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            user = update.effective_user
            user_id = user.id
            username = user.username
            
            # Extract referral code
            referrer_id = None
            if context.args:
                try:
                    referrer_id = SecurityUtils.decode_referral_data(context.args[0])
                except Exception:
                    pass
            
            # Add user to database
            is_new_user = db.add_user(user_id, username, referrer_id)
            
            # Create inline keyboard with admin options for admins
            keyboard = [
                [
                    InlineKeyboardButton("🔐 Generate Config", callback_data="generate"),
                    InlineKeyboardButton("🎯 My Points", callback_data="points")
                ],
                [
                    InlineKeyboardButton("🔗 Refer Friends", callback_data="refer"),
                    InlineKeyboardButton("📢 Join Channels", callback_data="join")
                ],
                [
                    InlineKeyboardButton("📊 Statistics", callback_data="stats"),
                    InlineKeyboardButton("❓ Help", callback_data="help")
                ]
            ]
            
            # Add admin options if user is admin
            if self.is_admin(user_id):
                keyboard.append([
                    InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")
                ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Welcome message
            welcome_text = MESSAGES["welcome"]
            if is_new_user and referrer_id:
                welcome_text += "\n\n✅ You were referred by user {}. They earned a point!".format(referrer_id)
            
            if self.is_admin(user_id):
                welcome_text += "\n\n👑 **Admin Access Detected** - Unlimited testing available!"
            
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error("Error in start command: {}".format(e))
            await update.message.reply_text("Sorry, something went wrong. Please try again.")

    @rate_limit('generate_config')
    async def generate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /generate command"""
        try:
            user_id = update.effective_user.id
            
            # Admins get unlimited access
            if not self.is_admin(user_id):
                # Check if user can generate config
                check_result = db.can_generate_config(user_id)
                
                if not check_result["can_generate"]:
                    if check_result["reason"] == "insufficient_points":
                        text = MESSAGES["insufficient_points"].format(
                            cost=POINTS_CONFIG["config_cost"],
                            current=check_result["current_points"],
                            **POINTS_CONFIG
                        )
                    else:
                        text = "❌ Unable to generate config. Please try again later."
                    
                    keyboard = [
                        [InlineKeyboardButton("🔗 Refer Friends", callback_data="refer")],
                        [InlineKeyboardButton("📢 Join Channels", callback_data="join")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                    return
            
            # Show config type selection
            keyboard = [
                [
                    InlineKeyboardButton("🔐 SSH Config", callback_data="gen_ssh"),
                    InlineKeyboardButton("🚀 V2Ray Config", callback_data="gen_v2ray")
                ],
                [InlineKeyboardButton("🎲 Random Config", callback_data="gen_auto")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            admin_note = "\n\n👑 **Admin Mode: Unlimited Testing**" if self.is_admin(user_id) else ""
            
            await update.message.reply_text(
                "🔧 **Choose Configuration Type:**\n\n"
                "• **SSH** - Secure Shell access\n"
                "• **V2Ray** - Service-specific proxy configs\n"
                "• **Random** - Let me choose for you{}".format(admin_note),
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error("Error in generate command: {}".format(e))
            await update.message.reply_text("Sorry, something went wrong. Please try again.")

    async def admin_test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin-only command for unlimited testing"""
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Admin access required.")
            return
            
        keyboard = []
        for service_key, service_data in SERVICE_PACKAGES.items():
            keyboard.append([InlineKeyboardButton(
                service_data["name"], 
                callback_data="admin_test_{}".format(service_key)
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "👑 **Admin Testing Panel**\n\n"
            "Select any service to generate unlimited test configs:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    # Continue with existing command handlers...
    async def points_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /points command"""
        try:
            user_id = update.effective_user.id
            user = db.get_user(user_id)
            
            if not user:
                await update.message.reply_text("Please use /start first to register.")
                return
            
            points = user["points"]
            free_used = user["free_used"]
            total_configs = user["total_configs"]
            referrals = len(user.get("referred_users", []))
            
            admin_status = "\n\n👑 **Admin Status**: Unlimited Access" if self.is_admin(user_id) else ""
            
            text = """
💰 **Your Points Summary**

**Current Points:** {}
**Free Config Used:** {}
**Total Configs Generated:** {}
**Successful Referrals:** {}

**Earn More Points:**
• 🔗 Refer friends: +{} point each
• 📢 Join sponsor channels: +{} points

**Point Value:**
• 1 point = 1 config generation{}
""".format(
                points,
                'Yes ✅' if free_used else 'No ❌',
                total_configs,
                referrals,
                POINTS_CONFIG['referral'],
                POINTS_CONFIG['channel_join'],
                admin_status
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("🔗 Get Referral Link", callback_data="refer"),
                    InlineKeyboardButton("📢 Join Channels", callback_data="join")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error("Error in points command: {}".format(e))
            await update.message.reply_text("Sorry, something went wrong. Please try again.")

    # Callback Query Handlers
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        try:
            if query.data == "generate":
                await self.handle_generate_callback(query, context)
            elif query.data.startswith("gen_"):
                await self.handle_config_generation(query, context)
            elif query.data.startswith("service_"):
                await self.handle_service_selection(query, context)
            elif query.data.startswith("admin_test_"):
                await self.handle_admin_test(query, context)
            elif query.data == "admin_panel":
                await self.handle_admin_panel(query, context)
            elif query.data == "points":
                await self.handle_points_callback(query, context)
            elif query.data == "refer":
                await self.handle_refer_callback(query, context)
            elif query.data == "join":
                await self.handle_join_callback(query, context)
            elif query.data == "check_channels":
                await self.handle_check_channels(query, context)
            elif query.data == "stats":
                await self.handle_stats_callback(query, context)
            elif query.data == "help":
                await self.handle_help_callback(query, context)
            elif query.data == "qr_referral":
                await self.handle_qr_referral(query, context)
            elif query.data.startswith("qr_config"):
                await self.handle_qr_config(query, context)
            elif query.data == "main_menu":
                await self.handle_main_menu(query, context)
                
        except Exception as e:
            logger.error("Error in button callback: {}".format(e))
            await query.edit_message_text("Sorry, something went wrong. Please try again.")

    async def handle_generate_callback(self, query, context):
        """Handle generate config callback"""
        user_id = query.from_user.id
        
        # Admins bypass point checking
        if not self.is_admin(user_id):
            check_result = db.can_generate_config(user_id)
            
            if not check_result["can_generate"]:
                if check_result["reason"] == "insufficient_points":
                    text = MESSAGES["insufficient_points"].format(
                        cost=POINTS_CONFIG["config_cost"],
                        current=check_result["current_points"],
                        **POINTS_CONFIG
                    )
                else:
                    text = "❌ Unable to generate config. Please try again later."
                
                keyboard = [
                    [InlineKeyboardButton("🔗 Refer Friends", callback_data="refer")],
                    [InlineKeyboardButton("📢 Join Channels", callback_data="join")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                return
        
        keyboard = [
            [
                InlineKeyboardButton("🔐 SSH Config", callback_data="gen_ssh"),
                InlineKeyboardButton("🚀 V2Ray Config", callback_data="gen_v2ray")
            ],
            [InlineKeyboardButton("🎲 Random Config", callback_data="gen_auto")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        admin_note = "\n\n👑 **Admin Mode: Unlimited**" if self.is_admin(user_id) else ""
        
        await query.edit_message_text(
            "🔧 **Choose Configuration Type:**\n\n"
            "• **SSH** - Secure Shell access\n"
            "• **V2Ray** - Service-specific proxy\n"
            "• **Random** - Let me choose for you{}".format(admin_note),
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_config_generation(self, query, context):
        """Handle config generation with service selection"""
        user_id = query.from_user.id
        config_type = query.data.replace("gen_", "")
        
        if config_type == "v2ray":
            # Show service selection for V2Ray
            await self.show_service_selection(query, context)
        else:
            # Generate SSH or auto config directly
            await self.generate_config_direct(query, context, config_type)

    async def show_service_selection(self, query, context):
        """Show service package selection"""
        keyboard = []
        
        # Create keyboard with service options
        row = []
        for service_key, service_data in SERVICE_PACKAGES.items():
            if len(row) == 2:  # 2 buttons per row
                keyboard.append(row)
                row = []
            
            row.append(InlineKeyboardButton(
                service_data["name"],
                callback_data="service_{}".format(service_key)
            ))
        
        if row:  # Add remaining buttons
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="generate")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📦 **Select Service Package:**\n\n"
            "Choose the service you want to use with this V2Ray config:\n\n"
            "Each package is optimized for specific apps/websites and works perfectly with HTTP Injector!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_service_selection(self, query, context):
        """Handle service package selection"""
        user_id = query.from_user.id
        service_key = query.data.replace("service_", "")
        
        # Store selected service in context
        context.user_data['selected_service'] = service_key
        
        await self.generate_service_config(query, context, service_key, is_admin_test=False)

    async def handle_admin_test(self, query, context):
        """Handle admin testing"""
        user_id = query.from_user.id
        if not self.is_admin(user_id):
            await query.answer("❌ Admin access required.", show_alert=True)
            return
            
        service_key = query.data.replace("admin_test_", "")
        context.user_data['selected_service'] = service_key
        
        await self.generate_service_config(query, context, service_key, is_admin_test=True)

    async def handle_admin_panel(self, query, context):
        """Handle admin panel"""
        user_id = query.from_user.id
        if not self.is_admin(user_id):
            await query.answer("❌ Admin access required.", show_alert=True)
            return
        
        keyboard = [
            [
                InlineKeyboardButton("🧪 Test All Services", callback_data="admin_test_all"),
                InlineKeyboardButton("📊 Detailed Stats", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton("👥 User Management", callback_data="admin_users"),
                InlineKeyboardButton("⚙️ Bot Settings", callback_data="admin_settings")
            ],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get quick stats
        db_stats = db.get_user_stats()
        
        await query.edit_message_text(
            "👑 **Admin Control Panel**\n\n"
            "**Quick Stats:**\n"
            "• Total Users: {:,}\n"
            "• Active Users: {:,}\n"
            "• Total Configs: {:,}\n\n"
            "**Admin Privileges:**\n"
            "✅ Unlimited config generation\n"
            "✅ Test all service packages\n"
            "✅ Access user management\n"
            "✅ View detailed analytics".format(
                db_stats.get('total_users', 0),
                db_stats.get('active_users', 0),
                db_stats.get('total_configs', 0)
            ),
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def generate_service_config(self, query, context, service_key, is_admin_test=False):
        """Generate V2Ray config for specific service"""
        user_id = query.from_user.id
        
        # Show generating message
        service_name = SERVICE_PACKAGES[service_key]["name"]
        admin_prefix = "👑 **Admin Testing** - " if is_admin_test else ""
        
        await query.edit_message_text(
            "{}🔄 **Generating {} Configuration...**\n\n"
            "Creating optimized V2Ray config for HTTP Injector...\n"
            "Please wait a moment...".format(admin_prefix, service_name)
        )
        
        try:
            # For non-admins, check points and deduct
            if not is_admin_test and not self.is_admin(user_id):
                check_result = db.can_generate_config(user_id)
                if not check_result["can_generate"]:
                    await query.edit_message_text("❌ Unable to generate config. Please check your points.")
                    return
                
                # Deduct points or mark free as used
                if check_result["use_free"]:
                    db.use_free_config(user_id)
                    points_remaining = check_result["points_after"]
                else:
                    db.deduct_points(user_id, POINTS_CONFIG["config_cost"])
                    points_remaining = check_result["points_after"]
            else:
                points_remaining = "Unlimited (Admin)" if self.is_admin(user_id) else "∞"
            
            # Generate service-specific config
            config_data = generator.generate_service_config(service_key)
            
            if not config_data:
                await query.edit_message_text(
                    "❌ **Generation Failed**\n\n"
                    "Sorry, we couldn't generate a config for {} right now.\n\n"
                    "💡 {}".format(
                        service_name,
                        "No points were deducted." if not is_admin_test else "Admin testing - try another service."
                    )
                )
                return
            
            # Save config to database (except for admin tests)
            if not is_admin_test:
                db.save_config(user_id, config_data["type"], str(config_data))
                stats_collector.update_config_stats(config_data["type"])
            
            # Format config for display
            formatted_config = self.format_service_config(config_data, service_key)
            
            admin_note = "\n\n👑 **Admin Test Mode** - Config generated for testing purposes." if is_admin_test else ""
            
            success_message = """
✅ **{} Generated Successfully!**

Points remaining: **{}**

📋 **Configuration Details:**
{}

🔧 **HTTP Injector Setup:**
1. Copy the VMess link above
2. Open HTTP Injector app
3. Go to Config → Import → VMess
4. Paste the link and save
5. Connect and enjoy {}!{}
""".format(
                service_name,
                points_remaining,
                formatted_config,
                SERVICE_PACKAGES[service_key]["description"].lower(),
                admin_note
            )
            
            # Create keyboard with options
            keyboard = []
            if not is_admin_test:
                keyboard.extend([
                    [InlineKeyboardButton("📱 Generate QR Code", callback_data="qr_config_{}".format(config_data['type']))],
                    [InlineKeyboardButton("🔄 Generate Another", callback_data="generate")]
                ])
            else:
                keyboard.extend([
                    [InlineKeyboardButton("🧪 Test Another Service", callback_data="admin_test_all")],
                    [InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")]
                ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(success_message, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Store config temporarily for QR generation
            context.user_data['last_config'] = config_data
            
        except Exception as e:
            logger.error("Error generating service config: {}".format(e))
            await query.edit_message_text(
                "❌ **Generation Failed**\n\n"
                "An error occurred while generating your {} config.\n"
                "Please try again later.".format(service_name)
            )

    def format_service_config(self, config_data, service_key):
        """Format service-specific config for display"""
        service_info = SERVICE_PACKAGES[service_key]
        
        if config_data.get("type") in ["VMess", "VLess"]:
            return """
🚀 **{} Configuration**

**Service Package:** {}
**Optimized For:** {}
**Config Type:** {}

**VMess Link for HTTP Injector:**
```
{}
```

**Target Hosts:**
{}

**Setup Instructions:**
• Use with HTTP Injector or similar apps
• Import the VMess link above
• Works specifically for: {}
""".format(
                service_info["name"],
                service_info["emoji"] + " " + service_info["name"],
                service_info["description"],
                config_data.get("type"),
                config_data.get("link", "N/A"),
                "\n".join("• " + host for host in service_info["hosts"]),
                ", ".join(service_info["hosts"]) if service_info["hosts"] != ["*"] else "All websites"
            )
        else:
            return self.formatter.format_config(config_data)

    async def generate_config_direct(self, query, context, config_type):
        """Generate SSH or auto config directly"""
        user_id = query.from_user.id
        
        # Show generating message
        await query.edit_message_text("🔄 **Generating your configuration...**\n\nPlease wait a moment...")
        
        try:
            # Check if user can generate (unless admin)
            if not self.is_admin(user_id):
                check_result = db.can_generate_config(user_id)
                if not check_result["can_generate"]:
                    await query.edit_message_text("❌ Unable to generate config. Please check your points.")
                    return
                
                # Deduct points or mark free as used
                if check_result["use_free"]:
                    db.use_free_config(user_id)
                    points_remaining = check_result["points_after"]
                else:
                    db.deduct_points(user_id, POINTS_CONFIG["config_cost"])
                    points_remaining = check_result["points_after"]
            else:
                points_remaining = "Unlimited (Admin)"
            
            # Generate config
            config_data = generator.generate_config(config_type)
            
            if not config_data:
                await query.edit_message_text(
                    "❌ **Generation Failed**\n\n"
                    "Sorry, we couldn't generate a config right now. Please try again later.\n\n"
                    "💡 No points were deducted."
                )
                return
            
            # Save config to database
            db.save_config(user_id, config_data["type"], str(config_data))
            stats_collector.update_config_stats(config_data["type"])
            
            # Format config for display
            formatted_config = self.formatter.format_config(config_data)
            
            success_message = MESSAGES["generation_success"].format(
                points=points_remaining,
                config=formatted_config
            )
            
            # Create keyboard with QR option
            keyboard = [
                [InlineKeyboardButton("📱 Generate QR Code", callback_data="qr_config_{}".format(config_data['type']))],
                [InlineKeyboardButton("🔄 Generate Another", callback_data="generate")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(success_message, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Store config temporarily for QR generation
            context.user_data['last_config'] = config_data
            
        except Exception as e:
            logger.error("Error generating config: {}".format(e))
            await query.edit_message_text(
                "❌ **Generation Failed**\n\n"
                "An error occurred while generating your config. Please try again later."
            )

    # Add all other existing handlers (points, refer, join, etc.) here...
    # [The rest of the handlers remain the same as in your original code]
    
    def setup_handlers(self):
        """Setup all command and callback handlers"""
        app = self.application
        
        # Command handlers
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("generate", self.generate_command))
        app.add_handler(CommandHandler("points", self.points_command))
        app.add_handler(CommandHandler("admin_test", self.admin_test_command))
        
        # Callback query handler
        app.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Error handler
        app.add_error_handler(self.error_handler)
        
        logger.info("All handlers registered successfully")

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error("Exception while handling an update: {}".format(context.error))

    def run(self):
        """Run the bot"""
        try:
            self.initialize()
            self.setup_handlers()
            
            logger.info("Starting Enhanced SSH/V2Ray Service Bot...")
            
            self.application.run_polling(
                poll_interval=0.0,
                timeout=10,
                bootstrap_retries=5,
                read_timeout=5,
                write_timeout=5,
                connect_timeout=5,
                pool_timeout=1
            )
            
        except Exception as e:
            logger.error("Error running bot: {}".format(e))
            raise

# Main execution
def main():
    """Main function to run the bot"""
    try:
        bot = SSHVPNBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error("Fatal error: {}".format(e))
        raise

if __name__ == "__main__":
    main()