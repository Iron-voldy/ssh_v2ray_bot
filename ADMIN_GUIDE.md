# 👑 Admin Guide - SSH/V2Ray Bot

This guide explains how to use the admin features for testing and managing your Telegram bot.

## 🔐 Admin Access

### Setting Up Admin Access
1. Add your Telegram User ID to `ADMIN_IDS` in `config.py`
2. Restart the bot
3. Use `/start` to access admin features

### Admin Identification
- Your User ID appears in Telegram URL: `https://t.me/username` → Right-click → Copy Link
- Use a bot like @userinfobot to get your User ID
- Add multiple admin IDs separated by commas: `ADMIN_IDS = [123456789, 987654321]`

## 💰 Admin Credit Management

### Quick Testing Credits
```bash
/admin_credits
```
**What it does:**
- Gives you 1000 testing credits instantly
- Allows generation of 200 files (1000 ÷ 5 = 200)
- Perfect for comprehensive bot testing

### Give Credits to Users
```bash
/give_credits 123456789 100
```
**Parameters:**
- `123456789` = Target user ID
- `100` = Amount of credits (1-10000)

**Use cases:**
- Reward active users
- Compensate for bot issues
- Give promotional credits
- Help users who need more access

### Check User Information
```bash
/check_user 123456789
```
**Shows:**
- User ID and username
- Current credit balance
- Total files generated
- Referral count
- Channel membership status
- Registration and last active dates
- How many files they can generate

## 🧪 Testing Features

### Admin Panel Access
1. Use `/start` command
2. Click "👑 Admin Panel" button
3. Access all admin features from one place

### Testing Service Packages
```bash
/admin_test
```
**OR** use Admin Panel → "🧪 Test Service Packages"

**What you can test:**
- All 10 service packages
- SSH file generation
- V2Ray file generation
- File quality and functionality
- Speed test optimization
- VMess link generation
- HTTP Injector compatibility

### Unlimited Generation
- Admins bypass all credit requirements
- Generate unlimited files for testing
- Test all services without restrictions
- No rate limiting applies

## 📊 Bot Monitoring

### View Statistics
Use Admin Panel → "📊 View Bot Statistics"

**Displays:**
- Total registered users
- Active users (last 7 days)
- Total files generated
- System status
- Database connectivity

### Real-time Monitoring
- Check bot logs for errors
- Monitor file generation success rates
- Track user activity
- Verify service provider status

## 🔧 Bot Testing Checklist

### 1. Basic Functionality Test
- [ ] Bot responds to `/start`
- [ ] Welcome message appears correctly
- [ ] Admin panel is accessible
- [ ] Credit system works

### 2. Credit System Test
- [ ] New users get 10 initial coins
- [ ] File generation costs 5 coins
- [ ] Referral system awards 3 coins
- [ ] Channel join awards 5 coins
- [ ] Admin credits work properly

### 3. File Generation Test
- [ ] SSH files generate successfully
- [ ] V2Ray files generate successfully
- [ ] All 10 service packages work
- [ ] VMess links are valid
- [ ] Payloads are correct

### 4. Service Package Test
Test each package individually:
- [ ] 🎥 YouTube Package
- [ ] 📱 WhatsApp Package
- [ ] 📹 Zoom Package
- [ ] 📘 Facebook Package
- [ ] 📷 Instagram Package
- [ ] 🎵 TikTok Package
- [ ] 🎬 Netflix Package
- [ ] ✈️ Telegram Package
- [ ] ⚡ Speed Test Package
- [ ] 🌐 All Sites Package

### 5. User Management Test
- [ ] Referral links generate correctly
- [ ] Channel join verification works
- [ ] Credit deduction works properly
- [ ] User statistics are accurate

## 🚨 Troubleshooting

### Common Issues

**Bot not responding:**
- Check bot token in config.py
- Verify MongoDB connection
- Check server/hosting status

**File generation failing:**
- Test different service packages
- Check provider connectivity
- Verify generator.py is working

**Credits not working:**
- Check database connection
- Verify user exists in database
- Check admin permissions

**Admin commands not working:**
- Verify your User ID is in ADMIN_IDS
- Restart bot after config changes
- Check for syntax errors

### Debug Commands
```bash
# Check if admin detection works
/start  # Should show admin panel button

# Test credit system
/admin_credits  # Should give 1000 credits

# Verify file generation
/generate  # Should work without credit deduction

# Check user database
/check_user YOUR_USER_ID  # Should show your details
```

## 🎯 Testing Scenarios

### Scenario 1: New User Experience
1. Create test account (or ask friend)
2. Have them use `/start`
3. Verify they get 10 coins
4. Test file generation (should cost 5 coins)
5. Check referral system

### Scenario 2: Credit Earning
1. Test referral link sharing
2. Verify channel join rewards
3. Check credit calculations
4. Ensure proper deductions

### Scenario 3: File Quality
1. Generate SSH files
2. Test with Termux/SSH clients
3. Generate V2Ray files
4. Test with HTTP Injector
5. Verify internet access works

### Scenario 4: Service Packages
1. Test each package individually
2. Verify VMess links work
3. Check payloads are correct
4. Ensure speed test optimization

## 💡 Pro Tips

### Efficient Testing
- Use `/admin_credits` to get testing credits quickly
- Test in order: SSH → V2Ray → All packages
- Keep notes of any issues found
- Test with actual devices/apps when possible

### User Support
- Use `/check_user` to help users with issues
- Give credits for compensation with `/give_credits`
- Monitor user activity for patterns
- Address common issues proactively

### Maintenance
- Regularly check bot statistics
- Monitor file generation success rates
- Update service providers if needed
- Keep admin credits topped up for testing

## 🔄 Regular Maintenance Tasks

### Daily
- [ ] Check bot is responding
- [ ] Verify file generation works
- [ ] Monitor user registrations

### Weekly
- [ ] Test all service packages
- [ ] Check provider connectivity
- [ ] Review user statistics
- [ ] Update admin credits if needed

### Monthly
- [ ] Full system test
- [ ] Check database performance
- [ ] Review and update documentation
- [ ] Plan improvements

---

**Remember:** As an admin, you have powerful tools to manage the bot and help users. Use them responsibly to ensure the best user experience! 🚀