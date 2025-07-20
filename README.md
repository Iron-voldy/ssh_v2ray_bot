# 🔐 SSH/V2Ray Config Generator Bot

A complete Telegram bot that generates SSH tunnels and V2Ray proxy configurations for unrestricted internet access. Users can browse any website without restrictions using the generated files.

## ✨ Features

### 💰 Credit System
- **10 FREE coins** for new users
- **5 coins** required per file generation
- No free trials - all generations cost coins

### 🎯 Earning System
- **Referrals**: +3 coins for each friend who joins using your link
- **Channel Joining**: +5 coins for joining both sponsor channels
- **Sustainable Economy**: Encourages user engagement and growth

### 🔧 File Types Available

#### 1. SSH Tunnels
- Secure Shell access for terminal users
- Compatible with Termux, ConnectBot, PuTTY
- Provides command-line internet access
- Includes speed test optimization

#### 2. V2Ray Configurations
- Advanced proxy configurations
- Compatible with HTTP Injector app
- Service-specific optimizations
- VMess protocol support

### 📦 Service Packages (V2Ray)

1. **🎥 YouTube Package** - Optimized for video streaming
2. **📱 WhatsApp Package** - Perfect for messaging & calls
3. **📹 Zoom Package** - Best for video conferencing
4. **📘 Facebook Package** - Social media browsing
5. **📷 Instagram Package** - Photo sharing & stories
6. **🎵 TikTok Package** - Short video streaming
7. **🎬 Netflix Package** - Movies & TV shows
8. **✈️ Telegram Package** - Messaging optimization
9. **⚡ Speed Test Package** - Network speed testing
10. **🌐 All Sites Package** - Universal website access

## 🚀 How It Works

### For Users:
1. Start the bot with `/start`
2. Get 10 free coins automatically
3. Choose file type (SSH or V2Ray)
4. Select service package (for V2Ray)
5. Receive generated file
6. Use file in compatible app
7. Enjoy unrestricted internet access!

### For Earning Coins:
1. **Refer Friends**: Share your referral link (+3 coins each)
2. **Join Channels**: Join both sponsor channels (+5 coins)
3. **Generate Files**: Use coins to create access files

## 📱 Compatible Apps

### For SSH Files:
- **Termux** (Android terminal)
- **ConnectBot** (Android SSH client)
- **PuTTY** (Desktop SSH client)
- **JuiceSSH** (Mobile SSH client)

### For V2Ray Files:
- **HTTP Injector** (Primary recommendation)
- **V2RayNG** (Android V2Ray client)
- **V2Ray clients** (Various platforms)

## 🛠️ Setup Instructions

### Prerequisites
```bash
pip install -r requirements.txt
```

### Configuration
1. Update `config.py` with your bot token
2. Set MongoDB connection string
3. Configure admin IDs
4. Set sponsor channel information

### Environment Variables
```bash
BOT_TOKEN=your_telegram_bot_token
MONGO_URI=your_mongodb_connection_string
ADMIN_IDS=your_admin_user_ids
```

### Running the Bot
```bash
python3 bot.py
```

## 🔧 Bot Commands

- `/start` - Start the bot and get welcome message
- `/generate` - Generate SSH or V2Ray files
- `/points` - Check your current coin balance
- `/help` - Get help and usage instructions

## 💡 How Users Use Generated Files

### SSH Files:
1. Install Termux or SSH client
2. Use provided credentials to connect
3. Run: `ssh username@host -p port`
4. Enter password when prompted
5. Browse internet via terminal

### V2Ray Files:
1. Download HTTP Injector app
2. Open app → Config → Import → VMess
3. Paste the VMess link
4. Use provided payload
5. Connect and browse freely

## 🌟 Key Benefits

- **Unrestricted Access**: Browse any website without limitations
- **Multiple Protocols**: SSH and V2Ray support
- **Service Optimization**: Packages optimized for specific apps
- **Speed Test Ready**: Built-in speed testing optimization
- **User-Friendly**: Simple interface with clear instructions
- **Sustainable Model**: Credit system encourages engagement

## 🔒 Security Features

- Secure credential generation
- Encrypted connections (TLS/SSL)
- No logging of user browsing
- Regular server rotation
- Speed test optimization

## 📊 Admin Features

- Unlimited file generation
- User statistics monitoring
- Service package testing
- Database management
- Error monitoring

## 🎯 Target Use Cases

1. **Bypassing Internet Restrictions**: Access blocked websites
2. **Privacy Protection**: Secure browsing with encrypted tunnels
3. **Geographic Content Access**: Access region-locked content
4. **Speed Testing**: Network performance analysis
5. **Development Testing**: Test applications through proxies

## 📈 Business Model

- **Freemium**: 10 free coins for new users
- **Referral Growth**: Viral growth through referral rewards
- **Channel Integration**: Sponsor channel promotion
- **Sustainable**: Credit system prevents abuse

## 🔄 File Lifecycle

1. **Generation**: Files created with 24-48 hour validity
2. **Usage**: Compatible with multiple applications
3. **Expiration**: Automatic cleanup after expiry
4. **Renewal**: Users generate new files as needed

## ⚡ Performance Optimization

- **Speed Test Integration**: Direct routing for speed test sites
- **Service-Specific Routing**: Optimized paths for each service
- **Multiple Servers**: Automatic failover between providers
- **Connection Optimization**: TCP/WebSocket optimization

Your bot is now complete and ready to provide unrestricted internet access to users worldwide! 🌍