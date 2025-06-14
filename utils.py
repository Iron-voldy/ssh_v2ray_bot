import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import re
from functools import wraps
import hashlib
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple rate limiter for bot functions"""
    
    def __init__(self):
        self.requests = {}
        self.limits = {
            'generate_config': {'calls': 3, 'window': 60},  # 3 calls per minute
            'referral_check': {'calls': 5, 'window': 60},   # 5 calls per minute
            'channel_check': {'calls': 10, 'window': 60}    # 10 calls per minute
        }
    
    def is_allowed(self, user_id: int, action: str) -> bool:
        """Check if user is allowed to perform action"""
        try:
            current_time = time.time()
            key = f"{user_id}_{action}"
            
            if action not in self.limits:
                return True
            
            limit_config = self.limits[action]
            window = limit_config['window']
            max_calls = limit_config['calls']
            
            # Clean old entries
            if key in self.requests:
                self.requests[key] = [
                    timestamp for timestamp in self.requests[key]
                    if current_time - timestamp < window
                ]
            else:
                self.requests[key] = []
            
            # Check if under limit
            if len(self.requests[key]) < max_calls:
                self.requests[key].append(current_time)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            return True  # Allow by default if error

def rate_limit(action: str):
    """Decorator for rate limiting"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user_id from args (assuming it's first arg after self/update)
            user_id = None
            for arg in args:
                if hasattr(arg, 'effective_user') and hasattr(arg.effective_user, 'id'):
                    user_id = arg.effective_user.id
                    break
                elif isinstance(arg, int) and arg > 0:
                    user_id = arg
                    break
            
            if user_id and not rate_limiter.is_allowed(user_id, action):
                logger.warning(f"Rate limit exceeded for user {user_id} on action {action}")
                return None
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

class ConfigFormatter:
    """Format configuration data for display"""
    
    @staticmethod
    def format_ssh_config(config_data: Dict) -> str:
        """Format SSH config for display"""
        try:
            host = config_data.get('host', 'N/A')
            port = config_data.get('port', 'N/A')
            username = config_data.get('username', 'N/A')
            password = config_data.get('password', 'N/A')
            expires = config_data.get('expires_at', 'N/A')
            
            if expires != 'N/A':
                expires = expires[:10]  # Just date part
            
            formatted = f"""
🔐 **SSH Configuration**

**Server Details:**
• Host: `{host}`
• Port: `{port}`
• Username: `{username}`
• Password: `{password}`

**Connection Commands:**
```bash
ssh {username}@{host} -p {port}
```

**Expires:** {expires}

⚠️ **Important:** Save this information securely. This message will not be shown again.
"""
            return formatted.strip()
            
        except Exception as e:
            logger.error(f"Error formatting SSH config: {e}")
            return "Error formatting configuration"
    
    @staticmethod
    def format_v2ray_config(config_data: Dict) -> str:
        """Format V2Ray config for display"""
        try:
            config_type = config_data.get('type', 'V2Ray')
            link = config_data.get('link', 'N/A')
            server = config_data.get('server', 'N/A')
            port = config_data.get('port', 'N/A')
            expires = config_data.get('expires_at', 'N/A')
            
            if expires != 'N/A':
                expires = expires[:10]  # Just date part
            
            formatted = f"""
🚀 **{config_type} Configuration**

**Server Details:**
• Server: `{server}`
• Port: `{port}`
• Type: {config_type}

**Import Link:**
```
{link}
```

**Instructions:**
1. Copy the link above
2. Import in your V2Ray client
3. Connect and enjoy!

**Expires:** {expires}

💡 **Tip:** Use the QR code for easier import
"""
            return formatted.strip()
            
        except Exception as e:
            logger.error(f"Error formatting V2Ray config: {e}")
            return "Error formatting configuration"
    
    @staticmethod
    def format_config(config_data: Dict) -> str:
        """Format any config type"""
        config_type = config_data.get('type', '').lower()
        
        if config_type == 'ssh':
            return ConfigFormatter.format_ssh_config(config_data)
        elif config_type in ['vmess', 'vless', 'v2ray']:
            return ConfigFormatter.format_v2ray_config(config_data)
        else:
            return f"Configuration: {json.dumps(config_data, indent=2)}"

class MessageValidator:
    """Validate user inputs and messages"""
    
    @staticmethod
    def is_valid_username(username: str) -> bool:
        """Validate Telegram username"""
        if not username:
            return False
        # Remove @ if present
        username = username.lstrip('@')
        # Check pattern: 5-32 chars, alphanumeric + underscore
        pattern = r'^[a-zA-Z0-9_]{5,32}$'
        return bool(re.match(pattern, username))
    
    @staticmethod
    def is_valid_user_id(user_id: Any) -> bool:
        """Validate user ID"""
        try:
            user_id = int(user_id)
            return 0 < user_id < 10**12  # Reasonable range for Telegram user IDs
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 1000) -> str:
        """Sanitize user input"""
        if not isinstance(text, str):
            return ""
        
        # Remove potentially dangerous characters
        text = re.sub(r'[<>&"]', '', text)
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length]
        
        return text.strip()

class SecurityUtils:
    """Security related utilities"""
    
    @staticmethod
    def hash_user_id(user_id: int, salt: str = "bot_salt_2024") -> str:
        """Create hash of user ID for analytics"""
        try:
            combined = f"{user_id}_{salt}"
            return hashlib.sha256(combined.encode()).hexdigest()[:16]
        except Exception:
            return "unknown"
    
    @staticmethod
    def is_admin(user_id: int, admin_ids: List[int]) -> bool:
        """Check if user is admin"""
        return user_id in admin_ids
    
    @staticmethod
    def encode_referral_data(user_id: int) -> str:
        """Encode referral data"""
        try:
            data = f"ref_{user_id}_{int(time.time())}"
            encoded = base64.b64encode(data.encode()).decode()
            return encoded[:10]  # Shortened for convenience
        except Exception:
            return str(user_id)
    
    @staticmethod
    def decode_referral_data(encoded: str) -> Optional[int]:
        """Decode referral data"""
        try:
            # Try direct int conversion first (backward compatibility)
            return int(encoded)
        except ValueError:
            try:
                # Try base64 decode
                decoded = base64.b64decode(encoded.encode()).decode()
                if decoded.startswith("ref_"):
                    parts = decoded.split("_")
                    if len(parts) >= 2:
                        return int(parts[1])
            except Exception:
                pass
        return None

class TimeUtils:
    """Time and date utilities"""
    
    @staticmethod
    def get_readable_time(dt: datetime) -> str:
        """Convert datetime to readable format"""
        try:
            return dt.strftime("%Y-%m-%d %H:%M UTC")
        except Exception:
            return "Unknown"
    
    @staticmethod
    def time_until_expiry(expires_at: str) -> str:
        """Get human readable time until expiry"""
        try:
            expiry_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            now = datetime.utcnow()
            
            if expiry_dt <= now:
                return "Expired"
            
            diff = expiry_dt - now
            days = diff.days
            hours = diff.seconds // 3600
            
            if days > 0:
                return f"{days} day(s)"
            elif hours > 0:
                return f"{hours} hour(s)"
            else:
                return "Less than 1 hour"
                
        except Exception:
            return "Unknown"
    
    @staticmethod
    def is_expired(expires_at: str) -> bool:
        """Check if config has expired"""
        try:
            expiry_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            return datetime.utcnow() >= expiry_dt
        except Exception:
            return False

class StatsCollector:
    """Collect and format statistics"""
    
    def __init__(self):
        self.stats = {
            'total_configs': 0,
            'ssh_configs': 0,
            'v2ray_configs': 0,
            'total_users': 0,
            'active_users': 0,
            'referrals': 0
        }
    
    def update_config_stats(self, config_type: str):
        """Update config generation stats"""
        self.stats['total_configs'] += 1
        if config_type.lower() == 'ssh':
            self.stats['ssh_configs'] += 1
        elif config_type.lower() in ['vmess', 'vless', 'v2ray']:
            self.stats['v2ray_configs'] += 1
    
    def update_user_stats(self, total_users: int, active_users: int):
        """Update user statistics"""
        self.stats['total_users'] = total_users
        self.stats['active_users'] = active_users
    
    def update_referral_stats(self, referrals: int):
        """Update referral statistics"""
        self.stats['referrals'] = referrals
    
    def get_stats_message(self) -> str:
        """Get formatted stats message"""
        return f"""
📊 **Bot Statistics**

**Users:**
• Total Users: {self.stats['total_users']:,}
• Active Users: {self.stats['active_users']:,}
• Successful Referrals: {self.stats['referrals']:,}

**Configurations:**
• Total Generated: {self.stats['total_configs']:,}
• SSH Configs: {self.stats['ssh_configs']:,}
• V2Ray Configs: {self.stats['v2ray_configs']:,}

**Success Rate:** {self.get_success_rate():.1f}%
"""
    
    def get_success_rate(self) -> float:
        """Calculate success rate"""
        if self.stats['total_users'] == 0:
            return 0.0
        return (self.stats['total_configs'] / self.stats['total_users']) * 100

# Global instances
rate_limiter = RateLimiter()
stats_collector = StatsCollector()