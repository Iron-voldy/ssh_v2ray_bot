import requests
from bs4 import BeautifulSoup
import random
import string
import json
import base64
import re
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import time
import uuid
import urllib3

# Disable SSL warnings for providers with certificate issues
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service-specific payloads for HTTP Injector
SERVICE_PAYLOADS = {
    "youtube": {
        "name": "🎥 YouTube Package",
        "payload": "GET / HTTP/1.1[crlf]Host: www.youtube.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "www.youtube.com",
        "host": "www.youtube.com",
        "description": "Optimized for YouTube streaming"
    },
    "whatsapp": {
        "name": "📱 WhatsApp Package", 
        "payload": "GET / HTTP/1.1[crlf]Host: www.whatsapp.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "www.whatsapp.com",
        "host": "www.whatsapp.com",
        "description": "Optimized for WhatsApp messaging"
    },
    "zoom": {
        "name": "📹 Zoom Package",
        "payload": "GET / HTTP/1.1[crlf]Host: zoom.us[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "zoom.us", 
        "host": "zoom.us",
        "description": "Optimized for Zoom video calls"
    },
    "facebook": {
        "name": "📘 Facebook Package",
        "payload": "GET / HTTP/1.1[crlf]Host: www.facebook.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "www.facebook.com",
        "host": "www.facebook.com", 
        "description": "Optimized for Facebook social media"
    },
    "instagram": {
        "name": "📷 Instagram Package",
        "payload": "GET / HTTP/1.1[crlf]Host: www.instagram.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "www.instagram.com",
        "host": "www.instagram.com",
        "description": "Optimized for Instagram content"
    },
    "tiktok": {
        "name": "🎵 TikTok Package",
        "payload": "GET / HTTP/1.1[crlf]Host: www.tiktok.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "www.tiktok.com",
        "host": "www.tiktok.com",
        "description": "Optimized for TikTok videos"
    },
    "netflix": {
        "name": "🎬 Netflix Package",
        "payload": "GET / HTTP/1.1[crlf]Host: www.netflix.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "www.netflix.com",
        "host": "www.netflix.com",
        "description": "Optimized for Netflix streaming"
    },
    "gaming": {
        "name": "🎮 Gaming Package",
        "payload": "GET / HTTP/1.1[crlf]Host: discord.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "discord.com",
        "host": "discord.com",
        "description": "Optimized for online gaming"
    },
    "general": {
        "name": "🌐 General Package",
        "payload": "GET / HTTP/1.1[crlf]Host: www.google.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "www.google.com", 
        "host": "www.google.com",
        "description": "General internet browsing"
    }
}

class ConfigGenerator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        # Disable SSL verification for problematic providers
        self.session.verify = False
        
    def generate_username(self, length: int = 8) -> str:
        """Generate random username"""
        return "user" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def generate_password(self, length: int = 12) -> str:
        """Generate random password"""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choices(chars, k=length))

class SSHGenerator(ConfigGenerator):
    def __init__(self):
        super().__init__()
        
    def create_speedssh_account(self) -> Optional[Dict]:
        """Create SSH account from SpeedSSH"""
        try:
            # Try different SpeedSSH servers
            servers = ['sg1', 'us1', 'de1', 'uk1']
            
            for server in servers:
                try:
                    url = "https://speedssh.com/create-ssh-server/{}".format(server)
                    username = self.generate_username()
                    password = self.generate_password()
                    
                    payload = {
                        'username': username,
                        'password': password,
                        'server': server
                    }
                    
                    response = self.session.post(url, data=payload, timeout=30)
                    
                    if response.status_code == 200:
                        # Try to extract info from response
                        if 'success' in response.text.lower() or username in response.text:
                            return {
                                "type": "SSH",
                                "host": "{}.speedssh.com".format(server),
                                "port": 22,
                                "username": username,
                                "password": password,
                                "created_at": datetime.utcnow().isoformat(),
                                "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                                "server": server
                            }
                except Exception as e:
                    logger.error("SpeedSSH server {} failed: {}".format(server, e))
                    continue
                    
        except Exception as e:
            logger.error("Error creating SpeedSSH account: {}".format(e))
            
        return None
    
    def generate_ssh_config(self) -> Optional[Dict]:
        """Generate SSH config from available providers"""
        try:
            config = self.create_speedssh_account()
            if config:
                return config
        except Exception as e:
            logger.error("SSH generation failed: {}".format(e))
                
        return None

class V2RayGenerator(ConfigGenerator):
    def __init__(self):
        super().__init__()
        
    def create_service_specific_vmess(self, service: str = "general") -> Optional[Dict]:
        """Create VMess config optimized for specific service"""
        try:
            # Get service configuration
            service_config = SERVICE_PAYLOADS.get(service, SERVICE_PAYLOADS["general"])
            
            # Working V2Ray servers
            working_servers = [
                {
                    "add": "cf.090227.xyz",
                    "port": "443",
                    "net": "ws",
                    "path": "/",
                    "tls": "tls"
                },
                {
                    "add": "discord.com", 
                    "port": "443",
                    "net": "ws", 
                    "path": "/linkws",
                    "tls": "tls"
                },
                {
                    "add": "www.speedtest.net",
                    "port": "443",
                    "net": "ws",
                    "path": "/",
                    "tls": "tls"
                }
            ]
            
            # Try each server
            for server_config in working_servers:
                try:
                    # Test if server responds
                    test_response = self.session.get("https://{}".format(server_config["add"]), timeout=10)
                    if test_response.status_code in [200, 301, 302, 403, 404]:  # Server is reachable
                        
                        vmess_config = {
                            "v": "2",
                            "ps": "{} - {}".format(service_config["name"], random.randint(1000, 9999)),
                            "add": server_config["add"],
                            "port": server_config["port"], 
                            "id": str(uuid.uuid4()),
                            "aid": "0",
                            "net": server_config["net"],
                            "type": "none",
                            "host": service_config["host"],  # Use service-specific host
                            "path": server_config["path"],
                            "tls": server_config["tls"],
                            "sni": service_config["sni"]  # Add SNI for service
                        }
                        
                        vmess_json = json.dumps(vmess_config)
                        vmess_link = "vmess://" + base64.b64encode(vmess_json.encode()).decode()
                        
                        return {
                            "type": "VMess",
                            "service": service,
                            "service_name": service_config["name"],
                            "description": service_config["description"],
                            "config": vmess_config,
                            "link": vmess_link,
                            "qr_data": vmess_link,
                            "payload": service_config["payload"],
                            "server": server_config["add"],
                            "port": server_config["port"],
                            "host": service_config["host"],
                            "sni": service_config["sni"],
                            "created_at": datetime.utcnow().isoformat(),
                            "expires_at": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                            "injector_instructions": "Use this config in HTTP Injector with the provided payload"
                        }
                        
                except Exception as e:
                    logger.error("Server {} not reachable: {}".format(server_config["add"], e))
                    continue
                    
        except Exception as e:
            logger.error("Error creating service-specific VMess config: {}".format(e))
            
        return None

    def generate_v2ray_config(self, service: str = "general") -> Optional[Dict]:
        """Generate V2Ray config for specific service"""
        try:
            config = self.create_service_specific_vmess(service)
            if config:
                return config
        except Exception as e:
            logger.error("V2Ray generation failed: {}".format(e))
                
        return None

# Main generator class
class MainGenerator:
    def __init__(self):
        self.ssh_gen = SSHGenerator()
        self.v2ray_gen = V2RayGenerator()
    
    def get_available_services(self) -> Dict[str, Dict]:
        """Get list of available services"""
        return SERVICE_PAYLOADS
    
    def generate_config(self, config_type: str = "auto", service: str = "general") -> Optional[Dict]:
        """Generate config based on type and service"""
        try:
            if config_type.lower() in ["ssh", "auto"]:
                config = self.ssh_gen.generate_ssh_config()
                if config:
                    return config
                    
            if config_type.lower() in ["v2ray", "vmess", "vless", "auto"]:
                config = self.v2ray_gen.generate_v2ray_config(service)
                if config:
                    return config
                    
            # If auto and nothing worked, try creating demo configs
            if config_type.lower() == "auto":
                return self.create_demo_config()
                
        except Exception as e:
            logger.error("Error generating config: {}".format(e))
            
        return None
    
    def create_demo_config(self) -> Dict:
        """Create demo config when providers fail"""
        username = self.ssh_gen.generate_username()
        password = self.ssh_gen.generate_password()
        
        return {
            "type": "SSH",
            "host": "demo.example.com",
            "port": 22,
            "username": username,
            "password": password,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "note": "Demo config - Please try again later for real configs"
        }

# Global generator instance
generator = MainGenerator()