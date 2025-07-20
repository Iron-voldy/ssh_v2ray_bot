from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import logging
from typing import Optional, Dict, List
from config import MONGO_URI, DB_NAME

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        try:
            self.client = MongoClient(MONGO_URI)
            self.db = self.client[DB_NAME]
            self.users = self.db.users
            self.configs = self.db.configs
            self.stats = self.db.stats
            
            # Create indexes for better performance
            self.users.create_index("user_id", unique=True)
            self.configs.create_index([("user_id", 1), ("created_at", -1)])
            
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def add_user(self, user_id: int, username: str = None, referrer_id: int = None) -> bool:
        """Add new user to database"""
        try:
            from config import POINTS_CONFIG
            user_data = {
                "user_id": user_id,
                "username": username,
                "points": POINTS_CONFIG["initial_coins"],  # Give 10 coins to start
                "referrer_id": referrer_id,
                "referred_users": [],
                "free_used": False,
                "joined_channels": False,
                "total_configs": 0,
                "last_config": None,
                "created_at": datetime.now(timezone.utc),
                "last_active": datetime.now(timezone.utc)
            }
            
            # Check if user exists
            if self.users.find_one({"user_id": user_id}):
                return False
                
            self.users.insert_one(user_data)
            
            # Award referrer if exists
            if referrer_id and referrer_id != user_id:
                self.add_referral(referrer_id, user_id)
                
            logger.info(f"New user added: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            return False

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user data"""
        try:
            user = self.users.find_one({"user_id": user_id})
            if user:
                # Update last active
                self.users.update_one(
                    {"user_id": user_id},
                    {"$set": {"last_active": datetime.now(timezone.utc)}}
                )
            return user
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    def add_points(self, user_id: int, points: int, reason: str = "") -> bool:
        """Add points to user"""
        try:
            result = self.users.update_one(
                {"user_id": user_id},
                {
                    "$inc": {"points": points},
                    "$set": {"last_active": datetime.now(timezone.utc)}
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Added {points} points to user {user_id} - {reason}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error adding points to user {user_id}: {e}")
            return False

    def set_points(self, user_id: int, points: int, reason: str = "Admin action") -> bool:
        """Set exact points for user (admin function)"""
        try:
            result = self.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "points": points,
                        "last_active": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Set {points} points for user {user_id} - {reason}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error setting points for user {user_id}: {e}")
            return False

    def give_admin_credits(self, admin_id: int, amount: int = 1000) -> bool:
        """Give admin user testing credits"""
        try:
            # First ensure admin user exists
            if not self.users.find_one({"user_id": admin_id}):
                self.add_user(admin_id, "admin", None)
            
            # Give admin credits
            result = self.users.update_one(
                {"user_id": admin_id},
                {
                    "$set": {
                        "points": amount,
                        "last_active": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Gave admin {admin_id} testing credits: {amount}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error giving admin credits to {admin_id}: {e}")
            return False

    def deduct_points(self, user_id: int, points: int) -> bool:
        """Deduct points from user"""
        try:
            user = self.get_user(user_id)
            if not user or user["points"] < points:
                return False
                
            result = self.users.update_one(
                {"user_id": user_id},
                {
                    "$inc": {"points": -points},
                    "$set": {"last_active": datetime.now(timezone.utc)}
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error deducting points from user {user_id}: {e}")
            return False

    def use_free_config(self, user_id: int) -> bool:
        """Mark free config as used"""
        try:
            result = self.users.update_one(
                {"user_id": user_id, "free_used": False},
                {"$set": {"free_used": True}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error using free config for user {user_id}: {e}")
            return False

    def add_referral(self, referrer_id: int, referred_id: int) -> bool:
        """Add referral and award points"""
        try:
            from config import POINTS_CONFIG
            # Check if referral already exists
            referrer = self.users.find_one({"user_id": referrer_id})
            if not referrer or referred_id in referrer.get("referred_users", []):
                return False
                
            # Add to referrer's list and award points
            result = self.users.update_one(
                {"user_id": referrer_id},
                {
                    "$push": {"referred_users": referred_id},
                    "$inc": {"points": POINTS_CONFIG["referral"]}  # Award 3 points
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Referral added: {referrer_id} -> {referred_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error adding referral {referrer_id} -> {referred_id}: {e}")
            return False

    def set_channels_joined(self, user_id: int, joined: bool = True) -> bool:
        """Mark user as having joined channels"""
        try:
            result = self.users.update_one(
                {"user_id": user_id},
                {"$set": {"joined_channels": joined}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error setting channels joined for user {user_id}: {e}")
            return False

    def save_config(self, user_id: int, config_type: str, config_data: str) -> bool:
        """Save generated config"""
        try:
            config_entry = {
                "user_id": user_id,
                "config_type": config_type,
                "config_data": config_data,
                "created_at": datetime.now(timezone.utc)
            }
            
            self.configs.insert_one(config_entry)
            
            # Update user stats
            self.users.update_one(
                {"user_id": user_id},
                {
                    "$inc": {"total_configs": 1},
                    "$set": {"last_config": datetime.now(timezone.utc)}
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving config for user {user_id}: {e}")
            return False

    def get_user_configs(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's config history"""
        try:
            configs = list(self.configs.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(limit))
            return configs
        except Exception as e:
            logger.error(f"Error getting configs for user {user_id}: {e}")
            return []

    def get_user_stats(self) -> Dict:
        """Get overall user statistics"""
        try:
            total_users = self.users.count_documents({})
            active_users = self.users.count_documents({
                "last_active": {"$gte": datetime.now(timezone.utc) - timedelta(days=7)}
            })
            total_configs = self.configs.count_documents({})
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "total_configs": total_configs
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}

    def can_generate_config(self, user_id: int) -> Dict[str, any]:
        """Check if user can generate config"""
        try:
            from config import POINTS_CONFIG
            user = self.get_user(user_id)
            if not user:
                return {"can_generate": False, "reason": "User not found"}
                
            # Check points (no free configs, all cost 5 coins)
            cost = POINTS_CONFIG["config_cost"]
            if user["points"] >= cost:
                return {"can_generate": True, "use_free": False, "points_after": user["points"] - cost}
                
            return {
                "can_generate": False, 
                "reason": "insufficient_points",
                "current_points": user["points"]
            }
            
        except Exception as e:
            logger.error(f"Error checking config generation for user {user_id}: {e}")
            return {"can_generate": False, "reason": "database_error"}

# Global database instance
db = Database()