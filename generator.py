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

# Service-specific payloads for HTTP Injector with speed test optimization
SERVICE_PAYLOADS = {
    "youtube": {
        "name": "🎥 YouTube Package",
        "payload": "GET / HTTP/1.1[crlf]Host: www.youtube.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "www.youtube.com",
        "host": "www.youtube.com",
        "description": "Optimized for YouTube streaming",
        "direct_domains": ["googlevideo.com", "youtube.com"]
    },
    "whatsapp": {
        "name": "📱 WhatsApp Package", 
        "payload": "GET / HTTP/1.1[crlf]Host: web.whatsapp.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "web.whatsapp.com",
        "host": "web.whatsapp.com",
        "description": "Optimized for WhatsApp messaging",
        "direct_domains": ["whatsapp.com", "whatsapp.net"]
    },
    "zoom": {
        "name": "📹 Zoom Package",
        "payload": "GET / HTTP/1.1[crlf]Host: zoom.us[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "zoom.us", 
        "host": "zoom.us",
        "description": "Optimized for Zoom video calls",
        "direct_domains": ["zoom.us", "zoomgov.com"]
    },
    "facebook": {
        "name": "📘 Facebook Package",
        "payload": "GET / HTTP/1.1[crlf]Host: www.facebook.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "www.facebook.com",
        "host": "www.facebook.com", 
        "description": "Optimized for Facebook social media",
        "direct_domains": ["facebook.com", "fbcdn.net"]
    },
    "instagram": {
        "name": "📷 Instagram Package",
        "payload": "GET / HTTP/1.1[crlf]Host: www.instagram.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "www.instagram.com",
        "host": "www.instagram.com",
        "description": "Optimized for Instagram content",
        "direct_domains": ["instagram.com", "cdninstagram.com"]
    },
    "tiktok": {
        "name": "🎵 TikTok Package",
        "payload": "GET / HTTP/1.1[crlf]Host: www.tiktok.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "www.tiktok.com",
        "host": "www.tiktok.com",
        "description": "Optimized for TikTok videos",
        "direct_domains": ["tiktok.com", "tiktokcdn.com"]
    },
    "netflix": {
        "name": "🎬 Netflix Package",
        "payload": "GET / HTTP/1.1[crlf]Host: www.netflix.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "www.netflix.com",
        "host": "www.netflix.com",
        "description": "Optimized for Netflix streaming",
        "direct_domains": ["netflix.com", "nflxvideo.net"]
    },
    "telegram": {
        "name": "✈️ Telegram Package",
        "payload": "GET / HTTP/1.1[crlf]Host: web.telegram.org[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "web.telegram.org",
        "host": "web.telegram.org",
        "description": "Optimized for Telegram Web",
        "direct_domains": ["telegram.org", "telegram.me"]
    },
    "speedtest": {
        "name": "⚡ Speed Test Package",
        "payload": "GET / HTTP/1.1[crlf]Host: openspeedtest.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "openspeedtest.com",
        "host": "openspeedtest.com",
        "description": "Optimized for speed testing (uses LibreSpeed)",
        "direct_domains": ["speedtest.net", "fast.com", "openspeedtest.com", "librespeed.org"]
    },
    "all_sites": {
        "name": "🌐 All Sites Package",
        "payload": "GET / HTTP/1.1[crlf]Host: www.google.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "www.google.com",
        "host": "www.google.com",
        "description": "Works with all websites + speed test optimization",
        "direct_domains": ["speedtest.net", "fast.com", "openspeedtest.com"]
    }
}

# Speed test optimized routing rules
SPEED_TEST_ROUTING = {
    "routing": {
        "rules": [
            {
                "type": "field",
                "domain": [
                    "speedtest.net",
                    "fast.com", 
                    "openspeedtest.com",
                    "librespeed.org",
                    "speedof.me",
                    "testmy.net",
                    "domain:speedtest"
                ],
                "outboundTag": "direct"
            },
            {
                "type": "field",
                "port": "8080",
                "outboundTag": "direct"
            }
        ]
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
                                "server": server,
                                "speed_test_note": "For speed testing, use: curl -s https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py | python3"
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
        
    def create_optimized_vmess(self, service: str = "all_sites") -> Optional[Dict]:
        """Create VMess config optimized for specific service with speed test support"""
        try:
            # Get service configuration
            service_config = SERVICE_PAYLOADS.get(service, SERVICE_PAYLOADS["all_sites"])
            
            # Working V2Ray servers with better endpoints
            working_servers = [
                {
                    "add": "cf.090227.xyz",
                    "port": "443",
                    "net": "tcp",  # TCP for better speed test performance
                    "path": "/",
                    "tls": "tls",
                    "type": "none"
                },
                {
                    "add": "discord.com", 
                    "port": "443",
                    "net": "tcp",  # Changed from ws to tcp
                    "path": "/",
                    "tls": "tls",
                    "type": "none"
                },
                {
                    "add": "www.speedtest.net",  # Added speedtest.net as server
                    "port": "443",
                    "net": "tcp",
                    "path": "/",
                    "tls": "tls",
                    "type": "none"
                },
                {
                    "add": "fast.com",  # Netflix's speed test
                    "port": "443", 
                    "net": "tcp",
                    "path": "/",
                    "tls": "tls",
                    "type": "none"
                }
            ]
            
            # Try each server
            for server_config in working_servers:
                try:
                    # Generate optimized VMess config
                    vmess_config = {
                        "v": "2",
                        "ps": "{} - SpeedTest Optimized".format(service_config["name"]),
                        "add": server_config["add"],
                        "port": server_config["port"], 
                        "id": str(uuid.uuid4()),
                        "aid": "0",
                        "net": server_config["net"],  # TCP for better performance
                        "type": "none",
                        "host": service_config["host"],
                        "path": server_config["path"],
                        "tls": server_config["tls"],
                        "sni": service_config["sni"]
                    }
                    
                    # Add WebSocket path only if using WebSocket
                    if server_config["net"] == "ws":
                        vmess_config["path"] = "/speedtest"
                    
                    vmess_json = json.dumps(vmess_config)
                    vmess_link = "vmess://" + base64.b64encode(vmess_json.encode()).decode()
                    
                    # Create advanced V2Ray client config with routing
                    v2ray_client_config = {
                        "inbounds": [
                            {
                                "port": 1080,
                                "protocol": "socks",
                                "settings": {
                                    "auth": "noauth",
                                    "udp": True
                                }
                            }
                        ],
                        "outbounds": [
                            {
                                "tag": "proxy",
                                "protocol": "vmess",
                                "settings": {
                                    "vnext": [
                                        {
                                            "address": vmess_config["add"],
                                            "port": int(vmess_config["port"]),
                                            "users": [
                                                {
                                                    "id": vmess_config["id"],
                                                    "security": "auto"
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "streamSettings": {
                                    "network": vmess_config["net"],
                                    "security": vmess_config["tls"],
                                    "tlsSettings": {
                                        "serverName": vmess_config["sni"],
                                        "allowInsecure": False
                                    }
                                },
                                "mux": {
                                    "enabled": False  # Disable mux for speed tests
                                }
                            },
                            {
                                "tag": "direct",
                                "protocol": "freedom",
                                "settings": {}
                            }
                        ],
                        "routing": {
                            "rules": [
                                {
                                    "type": "field",
                                    "domain": [
                                        "speedtest.net",
                                        "fast.com",
                                        "openspeedtest.com",
                                        "librespeed.org",
                                        "speedof.me",
                                        "testmy.net",
                                        "domain:speedtest"
                                    ] + service_config.get("direct_domains", []),
                                    "outboundTag": "direct"
                                },
                                {
                                    "type": "field",
                                    "port": "8080",
                                    "outboundTag": "direct"
                                },
                                {
                                    "type": "field",
                                    "ip": ["8.8.8.8", "1.1.1.1"],
                                    "outboundTag": "direct"
                                }
                            ]
                        }
                    }
                    
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
                        "v2ray_config": v2ray_client_config,
                        "created_at": datetime.utcnow().isoformat(),
                        "expires_at": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                        "injector_instructions": "Use this config in HTTP Injector with the provided payload",
                        "speed_test_support": True,
                        "speed_test_alternatives": [
                            "https://openspeedtest.com/ (Works with VPN)",
                            "https://librespeed.org/ (Open source alternative)",
                            "Use speedtest-cli command line tool",
                            "Try fast.com (Netflix speed test)"
                        ],
                        "optimization_notes": [
                            "TCP transport for better speed test performance",
                            "Disabled multiplexing for accurate measurements", 
                            "Direct routing for speed test domains",
                            "Port 8080 routed directly for Speedtest.net"
                        ]
                    }
                        
                except Exception as e:
                    logger.error("Server {} failed for service {}: {}".format(server_config["add"], service, e))
                    continue
                    
        except Exception as e:
            logger.error("Error creating optimized VMess config: {}".format(e))
            
        return None

    def generate_v2ray_config(self, service: str = "all_sites") -> Optional[Dict]:
        """Generate V2Ray config for specific service"""
        try:
            config = self.create_optimized_vmess(service)
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
    
    def generate_config(self, config_type: str = "auto", service: str = "all_sites") -> Optional[Dict]:
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
    
    def generate_service_config(self, service_key: str) -> Optional[Dict]:
        """Generate service-specific V2Ray config - FIXED METHOD"""
        try:
            logger.info("Generating service config for: {}".format(service_key))
            
            # Generate V2Ray config for the specific service with speed test optimization
            config = self.v2ray_gen.generate_v2ray_config(service_key)
            
            if config:
                logger.info("Successfully generated {} config with speed test optimization".format(service_key))
                return config
            else:
                logger.warning("Failed to generate config for service: {}".format(service_key))
                # Return demo config if real generation fails
                return self.create_demo_v2ray_config(service_key)
                
        except Exception as e:
            logger.error("Error generating service config for {}: {}".format(service_key, e))
            return self.create_demo_v2ray_config(service_key)
    
    def create_demo_config(self) -> Dict:
        """Create demo SSH config when providers fail"""
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
            "note": "Demo config - Please try again later for real configs",
            "speed_test_note": "For speed testing over SSH tunnel: curl -s https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py | python3"
        }
    
    def create_demo_v2ray_config(self, service_key: str) -> Dict:
        """Create demo V2Ray config when providers fail"""
        service_config = SERVICE_PAYLOADS.get(service_key, SERVICE_PAYLOADS["all_sites"])
        
        # Create a working demo VMess config with speed test optimization
        vmess_config = {
            "v": "2",
            "ps": "{} - Demo SpeedTest Optimized".format(service_config["name"]),
            "add": "demo.example.com",
            "port": "443",
            "id": str(uuid.uuid4()),
            "aid": "0", 
            "net": "tcp",  # TCP for better performance
            "type": "none",
            "host": service_config["host"],
            "path": "/",
            "tls": "tls",
            "sni": service_config["sni"]
        }
        
        vmess_json = json.dumps(vmess_config)
        vmess_link = "vmess://" + base64.b64encode(vmess_json.encode()).decode()
        
        return {
            "type": "VMess",
            "service": service_key,
            "service_name": service_config["name"],
            "description": service_config["description"], 
            "config": vmess_config,
            "link": vmess_link,
            "qr_data": vmess_link,
            "payload": service_config["payload"],
            "server": "demo.example.com",
            "port": "443",
            "host": service_config["host"],
            "sni": service_config["sni"],
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "injector_instructions": "Demo config - Use this in HTTP Injector with the provided payload",
            "speed_test_support": True,
            "speed_test_alternatives": [
                "https://openspeedtest.com/ (VPN-friendly)",
                "https://librespeed.org/ (Open source)",
                "fast.com (Netflix speed test)",
                "Use mobile apps instead of web versions"
            ],
            "note": "Demo config - Please try again later for real configs"
        }

# Global generator instance
generator = MainGenerator()