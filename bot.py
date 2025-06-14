import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict
import io

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

class SSHVPNBot:
    def __init__(self):
        self.application = None
        self.formatter = ConfigFormatter()
        
    async def initialize(self):
        """Initialize the bot"""
        try:
            self.application = Application.builder().token(BOT_TOKEN).build()
            
            # Set bot commands
            commands = [
                BotCommand("start", "Start the bot and get welcome message"),
                BotCommand("generate", "Generate SSH/V2Ray configuration"),
                BotCommand("points", "Check your current points"),
                BotCommand("refer", "Get your referral link"),
                BotCommand("join", "Join channels to earn points"),
                BotCommand("history", "View your config history"),
                BotCommand("help", "Show help message"),
            ]
            
            await self.application.bot.set_my_commands(commands)
            logger.info("Bot commands set successfully")
            
        except Exception as e:
            logger.error(f"Error initializing bot: {e}")
            raise

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
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Welcome message
            welcome_text = MESSAGES["welcome"]
            if is_new_user and referrer_id:
                welcome_text += f"\n\n✅ You were referred by user {referrer_id}. They earned a point!"
            
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
            
            await update.message.reply_text(
                "🔧 **Choose Configuration Type:**\n\n"
                "• **SSH** - Secure Shell access\n"
                "• **V2Ray** - VMess/VLess proxy\n"
                "• **Random** - Let me choose for you",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in generate command: {e}")
            await update.message.reply_text("Sorry, something went wrong. Please try again.")

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
            
            text = f"""
💰 **Your Points Summary**

**Current Points:** {points}
**Free Config Used:** {'Yes' ✅ if free_used else 'No ❌'}
**Total Configs Generated:** {total_configs}
**Successful Referrals:** {referrals}

**Earn More Points:**
• 🔗 Refer friends: +{POINTS_CONFIG['referral']} point each
• 📢 Join sponsor channels: +{POINTS_CONFIG['channel_join']} points

**Point Value:**
• 1 point = 1 config generation
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

    async def refer_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /refer command"""
        try:
            user_id = update.effective_user.id
            user = db.get_user(user_id)
            
            if not user:
                await update.message.reply_text("Please use /start first to register.")
                return
            
            # Create referral link
            referral_code = SecurityUtils.encode_referral_data(user_id)
            referral_link = f"https://t.me/{BOT_USERNAME}?start={referral_code}"
            
            referrals_count = len(user.get("referred_users", []))
            
            text = f"""
🔗 **Your Referral Program**

**Your Referral Link:**
`{referral_link}`

**Share this link to earn points!**

**Stats:**
• Successful Referrals: {referrals_count}
• Points Earned: {referrals_count * POINTS_CONFIG['referral']}
• Reward per Referral: {POINTS_CONFIG['referral']} point(s)

**How it works:**
1. Share your link with friends
2. When they join using your link, you both benefit
3. You get {POINTS_CONFIG['referral']} point(s) per referral
4. Use points to generate more configs

💡 **Tip:** Share in groups, social media, or with friends!
"""
            
            keyboard = [
                [InlineKeyboardButton("📱 Share Link", url=f"https://t.me/share/url?url={referral_link}")],
                [InlineKeyboardButton("📊 QR Code", callback_data="qr_referral")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in refer command: {e}")
            await update.message.reply_text("Sorry, something went wrong. Please try again.")

    @rate_limit('channel_check')
    async def join_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /join command"""
        try:
            user_id = update.effective_user.id
            user = db.get_user(user_id)
            
            if not user:
                await update.message.reply_text("Please use /start first to register.")
                return
            
            if user.get("joined_channels", False):
                await update.message.reply_text(
                    "✅ You have already claimed your channel joining bonus!\n\n"
                    "💡 You can still earn points by referring friends."
                )
                return
            
            # Check if user is member of all channels
            all_joined = True
            failed_channels = []
            
            for channel in CHANNELS:
                try:
                    member = await context.bot.get_chat_member(channel["id"], user_id)
                    if member.status in ['left', 'kicked']:
                        all_joined = False
                        failed_channels.append(channel)
                except Exception as e:
                    logger.warning(f"Could not check membership for channel {channel['id']}: {e}")
                    all_joined = False
                    failed_channels.append(channel)
            
            if all_joined:
                # Award points
                points_awarded = POINTS_CONFIG["channel_join"]
                db.add_points(user_id, points_awarded, "channel_join_bonus")
                db.set_channels_joined(user_id, True)
                
                await update.message.reply_text(
                    f"🎉 **Congratulations!**\n\n"
                    f"You've earned **{points_awarded} points** for joining all sponsor channels!\n\n"
                    f"Use /generate to create your configs or /points to check your balance.",
                    parse_mode='Markdown'
                )
            else:
                # Show channels to join
                channel_list = ""
                keyboard = []
                
                for i, channel in enumerate(CHANNELS):
                    channel_list += f"{i+1}. {channel['name']}\n"
                    keyboard.append([InlineKeyboardButton(
                        f"📢 Join {channel['name']}", 
                        url=channel.get('url', f"https://t.me/c/{abs(channel['id'])}")
                    )])
                
                keyboard.append([InlineKeyboardButton("✅ Check Membership", callback_data="check_channels")])
                
                text = MESSAGES["join_channels"].format(
                    points=POINTS_CONFIG["channel_join"],
                    channel_list=channel_list
                )
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in join command: {e}")
            await update.message.reply_text("Sorry, something went wrong. Please try again.")

    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /history command"""
        try:
            user_id = update.effective_user.id
            configs = db.get_user_configs(user_id, limit=5)
            
            if not configs:
                await update.message.reply_text(
                    "📜 **Configuration History**\n\n"
                    "You haven't generated any configs yet.\n"
                    "Use /generate to create your first configuration!"
                )
                return
            
            text = "📜 **Your Last 5 Configurations**\n\n"
            
            for i, config in enumerate(configs, 1):
                config_type = config.get("config_type", "Unknown")
                created_at = config.get("created_at", datetime.utcnow())
                
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at)
                
                formatted_date = TimeUtils.get_readable_time(created_at)
                text += f"{i}. **{config_type}** - {formatted_date}\n"
            
            text += f"\n💡 **Total Configs Generated:** {len(configs)}"
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in history command: {e}")
            await update.message.reply_text("Sorry, something went wrong. Please try again.")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🤖 **SSH/V2Ray Config Generator Bot Help**

**Available Commands:**
• `/start` - Start the bot and get welcome message
• `/generate` - Generate SSH/V2Ray configuration
• `/points` - Check your current points balance
• `/refer` - Get your referral link to earn points
• `/join` - Join sponsor channels for bonus points
• `/history` - View your configuration history
• `/help` - Show this help message

**How to Earn Points:**
🔗 **Referrals:** Invite friends using your referral link
📢 **Channels:** Join all sponsor channels

**Supported Config Types:**
🔐 **SSH** - Secure Shell access for servers
🚀 **V2Ray** - VMess/VLess proxy configurations

**Features:**
• 1 FREE configuration for new users
• Point-based system for additional configs
• QR codes for easy import
• Configuration history tracking
• Referral rewards program

**Need Support?**
Contact: @YourSupportUsername

**Bot Version:** 1.0
**Last Updated:** June 2025
"""
        
        await update.message.reply_text(help_text, parse_mode='Markdown')

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
                
        except Exception as e:
            logger.error(f"Error in button callback: {e}")
            await query.edit_message_text("Sorry, something went wrong. Please try again.")

    async def handle_generate_callback(self, query, context):
        """Handle generate config callback"""
        user_id = query.from_user.id
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
        
        await query.edit_message_text(
            "🔧 **Choose Configuration Type:**\n\n"
            "• **SSH** - Secure Shell access\n"
            "• **V2Ray** - VMess/VLess proxy\n"
            "• **Random** - Let me choose for you",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_config_generation(self, query, context):
        """Handle actual config generation"""
        user_id = query.from_user.id
        config_type = query.data.replace("gen_", "")
        
        # Show generating message
        await query.edit_message_text("🔄 **Generating your configuration...**\n\nPlease wait a moment...")
        
        try:
            # Check if user can generate
            check_result = db.can_generate_config(user_id)
            if not check_result["can_generate"]:
                await query.edit_message_text("❌ Unable to generate config. Please check your points.")
                return
            
            # Generate config
            config_data = generator.generate_config(config_type)
            
            if not config_data:
                await query.edit_message_text(
                    "❌ **Generation Failed**\n\n"
                    "Sorry, we couldn't generate a config right now. Please try again later.\n\n"
                    "💡 No points were deducted."
                )
                return
            
            # Deduct points or mark free as used
            if check_result["use_free"]:
                db.use_free_config(user_id)
                points_remaining = check_result["points_after"]
            else:
                db.deduct_points(user_id, POINTS_CONFIG["config_cost"])
                points_remaining = check_result["points_after"]
            
            # Save config to database
            db.save_config(user_id, config_data["type"], str(config_data))
            
            # Update stats
            stats_collector.update_config_stats(config_data["type"])
            
            # Format config for display
            formatted_config = self.formatter.format_config(config_data)
            
            success_message = MESSAGES["generation_success"].format(
                points=points_remaining,
                config=formatted_config
            )
            
            # Create keyboard with QR option
            keyboard = [
                [InlineKeyboardButton("📱 Generate QR Code", callback_data=f"qr_config_{config_data['type']}")],
                [InlineKeyboardButton("🔄 Generate Another", callback_data="generate")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(success_message, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Store config temporarily for QR generation
            context.user_data['last_config'] = config_data
            
        except Exception as e:
            logger.error(f"Error generating config: {e}")
            await query.edit_message_text(
                "❌ **Generation Failed**\n\n"
                "An error occurred while generating your config. Please try again later."
            )

    async def handle_points_callback(self, query, context):
        """Handle points check callback"""
        user_id = query.from_user.id
        user = db.get_user(user_id)
        
        if not user:
            await query.edit_message_text("Please use /start first to register.")
            return
        
        points = user["points"]
        free_used = user["free_used"]
        total_configs = user["total_configs"]
        referrals = len(user.get("referred_users", []))
        
        text = f"""
💰 **Your Points Summary**

**Current Points:** {points}
**Free Config Used:** {'Yes' ✅ if free_used else 'No ❌'}
**Total Configs Generated:** {total_configs}
**Successful Referrals:** {referrals}

**Earn More Points:**
• 🔗 Refer friends: +{POINTS_CONFIG['referral']} point each
• 📢 Join sponsor channels: +{POINTS_CONFIG['channel_join']} points
"""
        
        keyboard = [
            [
                InlineKeyboardButton("🔗 Get Referral Link", callback_data="refer"),
                InlineKeyboardButton("📢 Join Channels", callback_data="join")
            ],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_refer_callback(self, query, context):
        """Handle referral callback"""
        user_id = query.from_user.id
        user = db.get_user(user_id)
        
        if not user:
            await query.edit_message_text("Please use /start first to register.")
            return
        
        referral_code = SecurityUtils.encode_referral_data(user_id)
        referral_link = f"https://t.me/{BOT_USERNAME}?start={referral_code}"
        referrals_count = len(user.get("referred_users", []))
        
        text = f"""
🔗 **Your Referral Program**

**Your Referral Link:**
`{referral_link}`

**Stats:**
• Successful Referrals: {referrals_count}
• Points Earned: {referrals_count * POINTS_CONFIG['referral']}
• Reward per Referral: {POINTS_CONFIG['referral']} point(s)

**How it works:**
1. Share your link with friends
2. When they join, you both benefit
3. You get {POINTS_CONFIG['referral']} point(s) per referral
"""
        
        keyboard = [
            [InlineKeyboardButton("📱 Share Link", url=f"https://t.me/share/url?url={referral_link}")],
            [InlineKeyboardButton("📊 QR Code", callback_data="qr_referral")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_join_callback(self, query, context):
        """Handle join channels callback"""
        # This is similar to join_command but adapted for callback
        user_id = query.from_user.id
        user = db.get_user(user_id)
        
        if not user:
            await query.edit_message_text("Please use /start first to register.")
            return
        
        if user.get("joined_channels", False):
            await query.edit_message_text(
                "✅ You have already claimed your channel joining bonus!\n\n"
                "💡 You can still earn points by referring friends."
            )
            return
        
        # Show channels to join
        channel_list = ""
        keyboard = []
        
        for i, channel in enumerate(CHANNELS):
            channel_list += f"{i+1}. {channel['name']}\n"
            keyboard.append([InlineKeyboardButton(
                f"📢 Join {channel['name']}", 
                url=channel.get('url', f"https://t.me/c/{abs(channel['id'])}")
            )])
        
        keyboard.append([InlineKeyboardButton("✅ Check Membership", callback_data="check_channels")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")])
        
        text = MESSAGES["join_channels"].format(
            points=POINTS_CONFIG["channel_join"],
            channel_list=channel_list
        )
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_check_channels(self, query, context):
        """Check if user joined all channels"""
        user_id = query.from_user.id
        
        # Similar logic to join_command
        all_joined = True
        for channel in CHANNELS:
            try:
                member = await context.bot.get_chat_member(channel["id"], user_id)
                if member.status in ['left', 'kicked']:
                    all_joined = False
                    break
            except Exception:
                all_joined = False
                break
        
        if all_joined:
            points_awarded = POINTS_CONFIG["channel_join"]
            db.add_points(user_id, points_awarded, "channel_join_bonus")
            db.set_channels_joined(user_id, True)
            
            await query.edit_message_text(
                f"🎉 **Congratulations!**\n\n"
                f"You've earned **{points_awarded} points** for joining all sponsor channels!\n\n"
                f"Use the menu below to generate configs or check your balance.",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "❌ **Not all channels joined**\n\n"
                "Please make sure you've joined ALL sponsor channels before checking again.\n\n"
                "💡 Tip: Click on each channel link and join them.",
                parse_mode='Markdown'
            )

    async def handle_stats_callback(self, query, context):
        """Handle stats callback"""
        try:
            db_stats = db.get_user_stats()
            stats_collector.update_user_stats(
                db_stats.get("total_users", 0),
                db_stats.get("active_users", 0)
            )
            
            stats_text = stats_collector.get_stats_message()
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            await query.edit_message_text("Sorry, couldn't load statistics right now.")

    async def handle_help_callback(self, query, context):
        """Handle help callback"""
        help_text = """
🤖 **Quick Help**

**Commands:**
• Generate configs with /generate
• Check points with /points  
• Get referral link with /refer
• Join channels with /join

**Earn Points:**
🔗 Refer friends (+{referral} points each)
📢 Join channels (+{channel_join} points)

**Need more help?**
Use /help for detailed information.
""".format(**POINTS_CONFIG)
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_qr_referral(self, query, context):
        """Generate QR code for referral link"""
        try:
            user_id = query.from_user.id
            qr_bytes = qr_generator.generate_referral_qr(BOT_USERNAME, user_id)
            
            if qr_bytes:
                await query.message.reply_photo(
                    photo=io.BytesIO(qr_bytes),
                    caption="📱 **Referral QR Code**\n\nShare this QR code for others to scan and join using your referral link!",
                    parse_mode='Markdown'
                )
            else:
                await query.answer("Sorry, couldn't generate QR code.", show_alert=True)
                
        except Exception as e:
            logger.error(f"Error generating referral QR: {e}")
            await query.answer("Error generating QR code.", show_alert=True)

    async def handle_qr_config(self, query, context):
        """Generate QR code for config"""
        try:
            config_data = context.user_data.get('last_config')
            if not config_data:
                await query.answer("No recent config found. Generate a new one first.", show_alert=True)
                return
            
            # Generate QR card
            qr_bytes = qr_card_generator.create_config_card(config_data)
            
            if qr_bytes:
                config_type = config_data.get('type', 'Config')
                await query.message.reply_photo(
                    photo=io.BytesIO(qr_bytes),
                    caption=f"📱 **{config_type} QR Code**\n\nScan this QR code to import your configuration!",
                    parse_mode='Markdown'
                )
            else:
                await query.answer("Sorry, couldn't generate QR code.", show_alert=True)
                
        except Exception as e:
            logger.error(f"Error generating config QR: {e}")
            await query.answer("Error generating QR code.", show_alert=True)

    async def handle_main_menu(self, query, context):
        """Return to main menu"""
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
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🏠 **Main Menu**\n\nChoose an option below:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    # Admin Commands
    async def admin_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to get detailed stats"""
        user_id = update.effective_user.id
        if not SecurityUtils.is_admin(user_id, ADMIN_IDS):
            return
        
        try:
            db_stats = db.get_user_stats()
            
            admin_text = f"""
👑 **Admin Statistics**

**Users:**
• Total Users: {db_stats.get('total_users', 0):,}
• Active Users (7 days): {db_stats.get('active_users', 0):,}

**Configurations:**
• Total Generated: {db_stats.get('total_configs', 0):,}

**System:**
• Bot Uptime: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
• Database Status: ✅ Connected

**Recent Activity:**
Use /admin_users for user management.
"""
            
            await update.message.reply_text(admin_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in admin stats: {e}")
            await update.message.reply_text("Error retrieving admin stats.")

    def setup_handlers(self):
        """Setup all command and callback handlers"""
        app = self.application
        
        # Command handlers
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("generate", self.generate_command))
        app.add_handler(CommandHandler("points", self.points_command))
        app.add_handler(CommandHandler("refer", self.refer_command))
        app.add_handler(CommandHandler("join", self.join_command))
        app.add_handler(CommandHandler("history", self.history_command))
        app.add_handler(CommandHandler("help", self.help_command))
        
        # Admin commands
        app.add_handler(CommandHandler("admin_stats", self.admin_stats_command))
        
        # Callback query handler
        app.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Error handler
        app.add_error_handler(self.error_handler)
        
        logger.info("All handlers registered successfully")

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        # Try to send error message to user if possible
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ An error occurred. Please try again later."
                )
            except Exception:
                pass

    async def run(self):
        """Run the bot"""
        try:
            await self.initialize()
            self.setup_handlers()
            
            logger.info("Starting SSH/V2Ray Config Bot...")
            await self.application.run_polling()
            
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            raise

# Main execution
async def main():
    bot = SSHVPNBot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise