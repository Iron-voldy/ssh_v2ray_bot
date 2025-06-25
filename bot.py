import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict
import io
import urllib.parse
import traceback

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)
from telegram.error import TelegramError

# Import our modules
from config import *
from db import db
from generator import generator, SERVICE_PAYLOADS
from qrgen import qr_generator, qr_card_generator
from utils import (
    rate_limiter, ConfigFormatter, MessageValidator, 
    SecurityUtils, TimeUtils, stats_collector, rate_limit
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO)
)
logger = logging.getLogger(__name__)

# Create SERVICE_PACKAGES mapping from SERVICE_PAYLOADS
SERVICE_PACKAGES = {}
for key, payload_data in SERVICE_PAYLOADS.items():
    SERVICE_PACKAGES[key] = {
        "name": payload_data["name"],
        "hosts": [payload_data["host"]] if payload_data["host"] != "www.google.com" else ["*"],
        "description": payload_data["description"],
        "emoji": payload_data["name"][0] if payload_data["name"] else "🔧"
    }

class SSHVPNBot:
    def __init__(self):
        self.application = None
        self.formatter = ConfigFormatter()
        
    def initialize(self):
        """Initialize the bot - synchronous version"""
        try:
            if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
                raise ValueError("BOT_TOKEN not set properly in environment variables")
            
            # Create application with explicit settings for Python 3.13 compatibility
            self.application = (
                Application.builder()
                .token(BOT_TOKEN)
                .concurrent_updates(True)
                .build()
            )
            logger.info("Bot application created successfully")
            
        except Exception as e:
            logger.error(f"Error initializing bot: {e}")
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
                    logger.info(f"Referral detected: {referrer_id} -> {user_id}")
                except Exception as e:
                    logger.warning(f"Invalid referral code: {e}")
            
            # Add user to database
            is_new_user = db.add_user(user_id, username, referrer_id)
            
            # Create inline keyboard
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
            
            # Welcome message with speed test info
            welcome_text = MESSAGES["welcome"]
            
            if is_new_user and referrer_id:
                welcome_text += f"\n\n✅ You were referred by user {referrer_id}. They earned a point!"
            
            if self.is_admin(user_id):
                welcome_text += "\n\n" + MESSAGES["admin_welcome"]
            
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text("Sorry, something went wrong. Please try again.")

    @rate_limit('generate_config')
    async def generate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /generate command"""
        try:
            user_id = update.effective_user.id
            
            # Admins get unlimited access
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
                "• **SSH** - Secure Shell access + CLI speed tests\n"
                "• **V2Ray** - Service-specific proxy with speed test optimization\n"
                "• **Random** - Let me choose for you\n\n"
                f"⚡ **All configs now include speed test optimization!**{admin_note}",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in generate command: {e}")
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
                callback_data=f"admin_test_{service_key}"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "👑 **Admin Testing Panel**\n\n"
            "Select any service to generate unlimited test configs with speed test optimization:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

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
            
            text = f"""
💰 **Your Points Summary**

**Current Points:** {points}
**Free Config Used:** {'Yes ✅' if free_used else 'No ❌'}
**Total Configs Generated:** {total_configs}
**Successful Referrals:** {referrals}

**Earn More Points:**
• 🔗 Refer friends: +{POINTS_CONFIG['referral']} point each
• 📢 Join sponsor channels: +{POINTS_CONFIG['channel_join']} points

**Point Value:**
• 1 point = 1 config generation{admin_status}
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("🔗 Get Referral Link", callback_data="refer"),
                    InlineKeyboardButton("📢 Join Channels", callback_data="join")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in points command: {e}")
            await update.message.reply_text("Sorry, something went wrong. Please try again.")

    # Callback Query Handlers
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        try:
            data = query.data
            logger.info(f"Button callback: {data} from user {query.from_user.id}")
            
            if data == "generate":
                await self.handle_generate_callback(query, context)
            elif data.startswith("gen_"):
                await self.handle_config_generation(query, context)
            elif data.startswith("service_"):
                await self.handle_service_selection(query, context)
            elif data.startswith("admin_test_"):
                await self.handle_admin_test(query, context)
            elif data == "admin_panel":
                await self.handle_admin_panel(query, context)
            elif data == "points":
                await self.handle_points_callback(query, context)
            elif data == "refer":
                await self.handle_refer_callback(query, context)
            elif data == "join":
                await self.handle_join_callback(query, context)
            elif data == "check_channels":
                await self.handle_check_channels(query, context)
            elif data == "stats":
                await self.handle_stats_callback(query, context)
            elif data == "help":
                await self.handle_help_callback(query, context)
            elif data == "qr_referral":
                await self.handle_qr_referral(query, context)
            elif data.startswith("qr_config"):
                await self.handle_qr_config(query, context)
            elif data == "main_menu":
                await self.handle_main_menu(query, context)
            else:
                logger.warning(f"Unknown callback data: {data}")
                await query.edit_message_text("Unknown action. Please try again.")
                
        except Exception as e:
            logger.error(f"Error in button callback: {e}")
            logger.error(traceback.format_exc())
            try:
                await query.edit_message_text("Sorry, something went wrong. Please try again.")
            except:
                pass

    # Add all the other methods here (keeping them the same as before)
    async def handle_generate_callback(self, query, context):
        """Handle generate config callback"""
        user_id = query.from_user.id
        
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
            "• **SSH** - Secure Shell access + CLI speed tests\n"
            "• **V2Ray** - Service-specific proxy with speed test optimization\n"
            "• **Random** - Let me choose for you\n\n"
            f"⚡ **All configs include speed test optimization!**{admin_note}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_config_generation(self, query, context):
        """Handle config generation with service selection"""
        user_id = query.from_user.id
        config_type = query.data.replace("gen_", "")
        
        if config_type == "v2ray":
            await self.show_service_selection(query, context)
        else:
            await self.generate_config_direct(query, context, config_type)

    async def show_service_selection(self, query, context):
        """Show service package selection"""
        keyboard = []
        
        row = []
        for service_key, service_data in SERVICE_PACKAGES.items():
            if len(row) == 2:
                keyboard.append(row)
                row = []
            
            row.append(InlineKeyboardButton(
                service_data["name"],
                callback_data=f"service_{service_key}"
            ))
        
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="generate")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📦 **Select Service Package:**\n\n"
            "Choose the service you want to use with this V2Ray config:\n\n"
            "Each package is optimized for specific apps/websites and includes speed test support!\n\n"
            "⚡ **New Feature**: All packages now route speed test sites directly for better performance!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_service_selection(self, query, context):
        """Handle service package selection"""
        user_id = query.from_user.id
        service_key = query.data.replace("service_", "")
        
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

    async def generate_service_config(self, query, context, service_key, is_admin_test=False):
        """Generate V2Ray config for specific service"""
        user_id = query.from_user.id
        
        service_name = SERVICE_PACKAGES[service_key]["name"]
        admin_prefix = "👑 **Admin Testing** - " if is_admin_test else ""
        
        await query.edit_message_text(
            f"{admin_prefix}🔄 **Generating {service_name} Configuration...**\n\n"
            "Creating optimized V2Ray config with:\n"
            "• Speed test optimization enabled\n"
            "• Direct routing for speed test sites\n"
            "• TCP optimization for performance\n"
            "• HTTP Injector compatibility\n\n"
            "Please wait a moment..."
        )
        
        try:
            if not is_admin_test and not self.is_admin(user_id):
                check_result = db.can_generate_config(user_id)
                if not check_result["can_generate"]:
                    await query.edit_message_text("❌ Unable to generate config. Please check your points.")
                    return
                
                if check_result["use_free"]:
                    db.use_free_config(user_id)
                    points_remaining = check_result["points_after"]
                else:
                    db.deduct_points(user_id, POINTS_CONFIG["config_cost"])
                    points_remaining = check_result["points_after"]
            else:
                points_remaining = "Unlimited (Admin)" if self.is_admin(user_id) else "∞"
            
            config_data = generator.generate_service_config(service_key)
            
            if not config_data:
                await query.edit_message_text(
                    "❌ **Generation Failed**\n\n"
                    f"Sorry, we couldn't generate a config for {service_name} right now.\n\n"
                    f"💡 {'No points were deducted.' if not is_admin_test else 'Admin testing - try another service.'}"
                )
                return
            
            if not is_admin_test:
                db.save_config(user_id, config_data["type"], str(config_data))
                stats_collector.update_config_stats(config_data["type"])
            
            formatted_config = self.format_service_config(config_data, service_key)
            
            admin_note = "\n\n👑 **Admin Test Mode** - Config generated for testing purposes." if is_admin_test else ""
            
            success_message = f"""
✅ **{service_name} Generated Successfully!**

Points remaining: **{points_remaining}**

📋 **Configuration Details:**
{formatted_config}

⚡ **Speed Test Information:**
{self.get_speed_test_info(config_data)}

🔧 **Setup Instructions:**
1. Copy the VMess link above
2. Open HTTP Injector app
3. Go to Config → Import → VMess
4. Paste the link and save
5. Use the payload for optimal performance
6. For speed tests, try the recommended alternatives!{admin_note}
"""
            
            keyboard = []
            if not is_admin_test:
                keyboard.extend([
                    [InlineKeyboardButton("📱 Generate QR Code", callback_data=f"qr_config_{config_data['type']}")],
                    [InlineKeyboardButton("🔄 Generate Another", callback_data="generate")]
                ])
            else:
                keyboard.extend([
                    [InlineKeyboardButton("🧪 Test Another Service", callback_data="admin_test_all")],
                    [InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")]
                ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(success_message, reply_markup=reply_markup, parse_mode='Markdown')
            
            context.user_data['last_config'] = config_data
            
        except Exception as e:
            logger.error(f"Error generating service config: {e}")
            logger.error(traceback.format_exc())
            await query.edit_message_text(
                "❌ **Generation Failed**\n\n"
                f"An error occurred while generating your {service_name} config.\n"
                "Please try again later."
            )

    def get_speed_test_info(self, config_data):
        """Get speed test information for config"""
        if config_data.get("speed_test_support"):
            alternatives = config_data.get("speed_test_alternatives", [])
            optimization_notes = config_data.get("optimization_notes", [])
            
            info = "**Speed Test Optimizations Applied:**\n"
            for note in optimization_notes:
                info += f"• {note}\n"
            
            info += "\n**Recommended Speed Test Sites:**\n"
            for alt in alternatives:
                info += f"• {alt}\n"
            
            return info
        else:
            return "Speed test optimization not available for this config type."

    def format_service_config(self, config_data, service_key):
        """Format service-specific config for display"""
        try:
            service_info = SERVICE_PACKAGES.get(service_key, {
                "name": "Custom Service",
                "description": "Custom configuration",
                "hosts": ["*"],
                "emoji": "🔧"
            })
        except:
            service_info = {
                "name": "Custom Service", 
                "description": "Custom configuration",
                "hosts": ["*"],
                "emoji": "🔧"
            }
        
        if config_data.get("type") in ["VMess", "VLess"]:
            return f"""
🚀 **{service_info["name"]} Configuration**

**Service Package:** {service_info["emoji"]} {service_info["name"]}
**Optimized For:** {service_info["description"]}
**Config Type:** {config_data.get("type")}

**VMess Link for HTTP Injector:**
```
{config_data.get("link", "N/A")}
```

**Payload for HTTP Injector:**
```
{config_data.get("payload", "No payload available")}
```

**Transport:** {config_data.get("config", {}).get("net", "tcp")} (Optimized for speed tests)
**Multiplexing:** Disabled (Better for speed tests)
**Direct Routing:** Enabled for speed test domains
"""
        else:
            return self.formatter.format_config(config_data)

    # Add remaining methods...
    async def handle_admin_panel(self, query, context):
        """Handle admin panel"""
        user_id = query.from_user.id
        if not self.is_admin(user_id):
            await query.answer("❌ Admin access required.", show_alert=True)
            return
        
        await query.edit_message_text(
            "👑 **Admin Control Panel**\n\n"
            "**Admin Privileges:**\n"
            "✅ Unlimited config generation\n"
            "✅ Test all service packages\n"
            "✅ Speed test optimization enabled\n\n"
            "Use /admin_test to test service packages.",
            parse_mode='Markdown'
        )

    # Simplified versions of other handlers...
    async def handle_points_callback(self, query, context):
        """Handle points callback"""
        await query.edit_message_text("Use /points command to check your points.")

    async def handle_refer_callback(self, query, context):
        """Handle referral callback"""
        user_id = query.from_user.id
        referral_code = SecurityUtils.encode_referral_data(user_id)
        referral_link = f"https://t.me/{BOT_USERNAME}?start={referral_code}"
        
        text = f"""
🔗 **Your Referral Link**

Share this link with friends to earn points!

**Your Link:**
```
{referral_link}
```

**Rewards:**
• You earn +{POINTS_CONFIG['referral']} point for each friend who joins
"""
        
        await query.edit_message_text(text, parse_mode='Markdown')

    async def handle_join_callback(self, query, context):
        """Handle join channels callback"""
        await query.edit_message_text("📢 Join our sponsor channels to earn points!")

    async def handle_check_channels(self, query, context):
        """Handle channel membership verification"""
        user_id = query.from_user.id
        success = db.add_points(user_id, POINTS_CONFIG['channel_join'], "Joined channels")
        
        if success:
            db.set_channels_joined(user_id, True)
            await query.edit_message_text(f"🎉 You earned +{POINTS_CONFIG['channel_join']} points!")
        else:
            await query.edit_message_text("❌ Error awarding points.")

    async def handle_stats_callback(self, query, context):
        """Handle statistics callback"""
        await query.edit_message_text("📊 **Bot Statistics**\n\nBot is running successfully!")

    async def handle_help_callback(self, query, context):
        """Handle help callback"""
        await query.edit_message_text(MESSAGES["help"], parse_mode='Markdown')

    async def handle_qr_referral(self, query, context):
        """Handle QR code generation for referral"""
        await query.edit_message_text("📱 QR code generation coming soon!")

    async def handle_qr_config(self, query, context):
        """Handle QR code generation for config"""
        await query.edit_message_text("📱 QR code generation coming soon!")

    async def handle_main_menu(self, query, context):
        """Handle main menu callback"""
        await query.edit_message_text("🏠 **Main Menu**\n\nUse /start to see the main menu.")

    async def generate_config_direct(self, query, context, config_type):
        """Generate SSH or auto config directly"""
        user_id = query.from_user.id
        
        await query.edit_message_text("🔄 **Generating configuration...**\n\nPlease wait...")
        
        try:
            if not self.is_admin(user_id):
                check_result = db.can_generate_config(user_id)
                if not check_result["can_generate"]:
                    await query.edit_message_text("❌ Unable to generate config. Please check your points.")
                    return
                
                if check_result["use_free"]:
                    db.use_free_config(user_id)
                    points_remaining = check_result["points_after"]
                else:
                    db.deduct_points(user_id, POINTS_CONFIG["config_cost"])
                    points_remaining = check_result["points_after"]
            else:
                points_remaining = "Unlimited (Admin)"
            
            config_data = generator.generate_config(config_type)
            
            if not config_data:
                await query.edit_message_text(
                    "❌ **Generation Failed**\n\n"
                    "Sorry, we couldn't generate a config right now. Please try again later.\n\n"
                    "💡 No points were deducted."
                )
                return
            
            db.save_config(user_id, config_data["type"], str(config_data))
            stats_collector.update_config_stats(config_data["type"])
            
            formatted_config = self.formatter.format_config(config_data)
            
            speed_test_note = ""
            if config_data.get("speed_test_note"):
                speed_test_note = f"\n\n⚡ **Speed Test Tip:**\n{config_data['speed_test_note']}"
            
            success_message = MESSAGES["generation_success"].format(
                points=points_remaining,
                config=formatted_config
            ) + speed_test_note
            
            keyboard = [
                [InlineKeyboardButton("🔄 Generate Another", callback_data="generate")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(success_message, reply_markup=reply_markup, parse_mode='Markdown')
            
            context.user_data['last_config'] = config_data
            
        except Exception as e:
            logger.error(f"Error generating config: {e}")
            logger.error(traceback.format_exc())
            await query.edit_message_text(
                "❌ **Generation Failed**\n\n"
                "An error occurred while generating your config. Please try again later."
            )
    
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
        logger.error(f"Exception while handling an update: {context.error}")
        logger.error(traceback.format_exc())

    def run(self):
        """Run the bot"""
        try:
            self.initialize()
            self.setup_handlers()
            
            logger.info("Starting Enhanced SSH/V2Ray Service Bot (Python 3.13 Compatible)...")
            
            # Use simpler polling configuration for Python 3.13 compatibility
            self.application.run_polling(
                poll_interval=1.0,
                timeout=30,
                bootstrap_retries=3,
                read_timeout=30,
                write_timeout=30,
                connect_timeout=30,
                pool_timeout=5,
                drop_pending_updates=True
            )
            
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            logger.error(traceback.format_exc())
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
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    main()