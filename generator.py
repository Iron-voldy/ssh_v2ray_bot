import requests
from bs4 import BeautifulSoup
import random
import string
import json
import base64
import re
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta, timezone
import time
import uuid
import urllib3
from urllib.parse import urljoin, urlparse

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
        "description": "Optimized for YouTube streaming with speed test support",
        "direct_domains": ["googlevideo.com", "youtube.com", "ytimg.com"]
    },
    "whatsapp": {
        "name": "📱 WhatsApp Package", 
        "payload": "GET / HTTP/1.1[crlf]Host: web.whatsapp.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "web.whatsapp.com",
        "host": "web.whatsapp.com",
        "description": "Optimized for WhatsApp messaging with speed test support",
        "direct_domains": ["whatsapp.com", "whatsapp.net", "wa.me"]
    },
    "zoom": {
        "name": "📹 Zoom Package",
        "payload": "GET / HTTP/1.1[crlf]Host: zoom.us[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "zoom.us", 
        "host": "zoom.us",
        "description": "Optimized for Zoom video calls with speed test support",
        "direct_domains": ["zoom.us", "zoomgov.com", "zoomcdn.com"]
    },
    "facebook": {
        "name": "📘 Facebook Package",
        "payload": "GET / HTTP/1.1[crlf]Host: www.facebook.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "www.facebook.com",
        "host": "www.facebook.com", 
        "description": "Optimized for Facebook social media with speed test support",
        "direct_domains": ["facebook.com", "fbcdn.net", "fb.com"]
    },
    "instagram": {
        "name": "📷 Instagram Package",
        "payload": "GET / HTTP/1.1[crlf]Host: www.instagram.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "www.instagram.com",
        "host": "www.instagram.com",
        "description": "Optimized for Instagram content with speed test support",
        "direct_domains": ["instagram.com", "cdninstagram.com", "ig.me"]
    },
    "tiktok": {
        "name": "🎵 TikTok Package",
        "payload": "GET / HTTP/1.1[crlf]Host: www.tiktok.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "www.tiktok.com",
        "host": "www.tiktok.com",
        "description": "Optimized for TikTok videos with speed test support",
        "direct_domains": ["tiktok.com", "tiktokcdn.com", "musical.ly"]
    },
    "netflix": {
        "name": "🎬 Netflix Package",
        "payload": "GET / HTTP/1.1[crlf]Host: www.netflix.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "www.netflix.com",
        "host": "www.netflix.com",
        "description": "Optimized for Netflix streaming with speed test support",
        "direct_domains": ["netflix.com", "nflxvideo.net", "nflximg.net"]
    },
    "telegram": {
        "name": "✈️ Telegram Package",
        "payload": "GET / HTTP/1.1[crlf]Host: web.telegram.org[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "web.telegram.org",
        "host": "web.telegram.org",
        "description": "Optimized for Telegram Web with speed test support",
        "direct_domains": ["telegram.org", "telegram.me", "t.me"]
    },
    "speedtest": {
        "name": "⚡ Speed Test Package",
        "payload": "GET / HTTP/1.1[crlf]Host: openspeedtest.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "openspeedtest.com",
        "host": "openspeedtest.com",
        "description": "Optimized for speed testing (uses OpenSpeedTest)",
        "direct_domains": ["speedtest.net", "fast.com", "openspeedtest.com", "librespeed.org"]
    },
    "all_sites": {
        "name": "🌐 All Sites Package",
        "payload": "GET / HTTP/1.1[crlf]Host: www.google.com[crlf]Connection: upgrade[crlf]Upgrade: websocket[crlf][crlf]",
        "sni": "www.google.com",
        "host": "www.google.com",
        "description": "Universal access with speed test optimization",
        "direct_domains": ["speedtest.net", "fast.com", "openspeedtest.com", "librespeed.org"]
    }
}

class ConfigGenerator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        })
        # Disable SSL verification for problematic providers
        self.session.verify = False
        # Set timeout
        self.timeout = 30
        
    def generate_username(self, length: int = 8) -> str:
        """Generate random username"""
        prefix = random.choice(['user', 'ssh', 'vpn', 'net', 'free'])
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length-len(prefix)))
        return prefix + suffix
    
    def generate_password(self, length: int = 12) -> str:
        """Generate random password"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=length))

class SSHGenerator(ConfigGenerator):
    def __init__(self):
        super().__init__()
        
    def create_speedssh_account(self) -> Optional[Dict]:
        """Create SSH account from SpeedSSH with improved error handling"""
        servers = [
            {'code': 'sg1', 'host': 'sg1.speedssh.com', 'port': 22},
            {'code': 'us1', 'host': 'us1.speedssh.com', 'port': 22},
            {'code': 'de1', 'host': 'de1.speedssh.com', 'port': 22},
            {'code': 'uk1', 'host': 'uk1.speedssh.com', 'port': 22}
        ]
        
        for server in servers:
            try:
                logger.info(f"Attempting to create SpeedSSH account on {server['code']}")
                
                # Generate credentials
                username = self.generate_username()
                password = self.generate_password()
                
                # First get the creation page to extract any tokens/forms
                create_url = f"https://speedssh.com/create-ssh-server/{server['code']}"
                
                try:
                    response = self.session.get(create_url, timeout=self.timeout)
                    if response.status_code != 200:
                        logger.warning(f"SpeedSSH {server['code']} page returned {response.status_code}")
                        continue
                except Exception as e:
                    logger.error(f"Failed to access SpeedSSH {server['code']}: {e}")
                    continue
                
                # Parse the form
                soup = BeautifulSoup(response.text, 'html.parser')
                form = soup.find('form')
                
                if not form:
                    logger.warning(f"No form found on SpeedSSH {server['code']}")
                    continue
                
                # Prepare form data
                form_data = {
                    'username': username,
                    'password': password,
                    'server': server['code']
                }
                
                # Extract hidden fields if any
                for hidden in soup.find_all('input', type='hidden'):
                    name = hidden.get('name')
                    value = hidden.get('value', '')
                    if name:
                        form_data[name] = value
                
                # Submit form
                try:
                    form_action = form.get('action', create_url)
                    if not form_action.startswith('http'):
                        form_action = urljoin(create_url, form_action)
                    
                    submit_response = self.session.post(
                        form_action, 
                        data=form_data, 
                        timeout=self.timeout,
                        allow_redirects=True
                    )
                    
                    if submit_response.status_code in [200, 201, 302]:
                        # Check if creation was successful
                        response_text = submit_response.text.lower()
                        success_indicators = [
                            'success', 'created', 'account', username.lower(), 
                            'ssh', 'generated', 'active', 'ready'
                        ]
                        
                        if any(indicator in response_text for indicator in success_indicators):
                            logger.info(f"Successfully created SpeedSSH account on {server['code']}")
                            return {
                                "type": "SSH",
                                "host": server['host'],
                                "port": server['port'],
                                "username": username,
                                "password": password,
                                "created_at": datetime.now(timezone.utc).isoformat(),
                                "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                                "server": server['code'],
                                "provider": "SpeedSSH",
                                "speed_test_note": "SSH Speed Test Commands:\n• speedtest-cli\n• curl -s https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py | python3\n• wget -O /dev/null http://speedtest.wdc01.softlayer.com/downloads/test100.zip"
                            }
                    
                except Exception as e:
                    logger.error(f"Failed to submit form to SpeedSSH {server['code']}: {e}")
                    continue
                    
            except Exception as e:
                logger.error(f"SpeedSSH server {server['code']} failed: {e}")
                continue
                
        logger.warning("All SpeedSSH servers failed")
        return None
    
    def create_fastssh_account(self) -> Optional[Dict]:
        """Create SSH account from FastSSH"""
        servers = [
            {'code': 'sg', 'host': 'sg.fastssh.com', 'port': 22},
            {'code': 'us', 'host': 'us.fastssh.com', 'port': 22},
            {'code': 'de', 'host': 'de.fastssh.com', 'port': 22}
        ]
        
        for server in servers:
            try:
                logger.info(f"Attempting to create FastSSH account on {server['code']}")
                
                username = self.generate_username()
                password = self.generate_password()
                
                url = f"https://fastssh.com/create-ssh-server/{server['code']}"
                
                form_data = {
                    'username': username,
                    'password': password,
                    'server': server['code']
                }
                
                response = self.session.post(url, data=form_data, timeout=self.timeout)
                
                if response.status_code == 200:
                    response_text = response.text.lower()
                    if any(word in response_text for word in ['success', 'created', username.lower()]):
                        logger.info(f"Successfully created FastSSH account on {server['code']}")
                        return {
                            "type": "SSH",
                            "host": server['host'],
                            "port": server['port'],
                            "username": username,
                            "password": password,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                            "server": server['code'],
                            "provider": "FastSSH",
                            "speed_test_note": "SSH Speed Test Commands:\n• speedtest-cli\n• curl -s https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py | python3"
                        }
                        
            except Exception as e:
                logger.error(f"FastSSH server {server['code']} failed: {e}")
                continue
                
        return None
    
    def create_opentunnel_account(self) -> Optional[Dict]:
        """Create SSH account from OpenTunnel"""
        servers = [
            {'code': 'sg', 'host': 'sg.opentunnel.net', 'port': 22},
            {'code': 'us', 'host': 'us.opentunnel.net', 'port': 22},
            {'code': 'de', 'host': 'de.opentunnel.net', 'port': 22}
        ]
        
        for server in servers:
            try:
                logger.info(f"Attempting to create OpenTunnel account on {server['code']}")
                
                username = self.generate_username()
                password = self.generate_password()
                
                url = f"https://opentunnel.net/create-ssh-server/{server['code']}"
                
                form_data = {
                    'username': username,
                    'password': password,
                    'server': server['code']
                }
                
                response = self.session.post(url, data=form_data, timeout=self.timeout)
                
                if response.status_code == 200:
                    response_text = response.text.lower()
                    if any(word in response_text for word in ['success', 'created', username.lower()]):
                        logger.info(f"Successfully created OpenTunnel account on {server['code']}")
                        return {
                            "type": "SSH",
                            "host": server['host'],
                            "port": server['port'],
                            "username": username,
                            "password": password,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                            "server": server['code'],
                            "provider": "OpenTunnel",
                            "speed_test_note": "SSH Speed Test Commands:\n• speedtest-cli\n• curl -s https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py | python3"
                        }
                        
            except Exception as e:
                logger.error(f"OpenTunnel server {server['code']} failed: {e}")
                continue
                
        return None
    
    def generate_ssh_config(self) -> Optional[Dict]:
        """Generate SSH config from available providers"""
        try:
            # Try SpeedSSH first
            config = self.create_speedssh_account()
            if config:
                return config
            
            # Try FastSSH as backup
            config = self.create_fastssh_account()
            if config:
                return config
            
            # Try OpenTunnel as last resort
            config = self.create_opentunnel_account()
            if config:
                return config
                
        except Exception as e:
            logger.error(f"SSH generation failed: {e}")
        
        # Return demo config if all fail
        return self.create_demo_ssh_config()
    
    def create_demo_ssh_config(self) -> Dict:
        """Create demo SSH config"""
        username = self.generate_username()
        password = self.generate_password()
        
        return {
            "type": "SSH",
            "host": "demo.speedssh.com",
            "port": 22,
            "username": username,
            "password": password,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            "server": "demo",
            "provider": "Demo",
            "note": "Demo config - For testing purposes only",
            "speed_test_note": "SSH Speed Test Commands:\n• speedtest-cli\n• curl -s https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py | python3\n• wget -O /dev/null http://speedtest.wdc01.softlayer.com/downloads/test100.zip"
        }

class V2RayGenerator(ConfigGenerator):
    def __init__(self):
        super().__init__()
        
    def get_working_servers(self) -> List[Dict]:
        """Get list of working V2Ray servers with speed test optimization"""
        return [
            {
                "add": "cf.090227.xyz",
                "port": "443",
                "net": "tcp",
                "path": "/",
                "tls": "tls",
                "type": "none",
                "priority": 1
            },
            {
                "add": "discord.com", 
                "port": "443",
                "net": "tcp",
                "path": "/",
                "tls": "tls", 
                "type": "none",
                "priority": 2
            },
            {
                "add": "www.speedtest.net",
                "port": "443",
                "net": "tcp",
                "path": "/speedtest",
                "tls": "tls",
                "type": "none",
                "priority": 3
            },
            {
                "add": "fast.com",
                "port": "443", 
                "net": "tcp",
                "path": "/",
                "tls": "tls",
                "type": "none",
                "priority": 4
            },
            {
                "add": "www.google.com",
                "port": "443",
                "net": "ws",
                "path": "/speedtest",
                "tls": "tls",
                "type": "none",
                "priority": 5
            }
        ]
    
    def create_optimized_vmess(self, service: str = "all_sites") -> Optional[Dict]:
        """Create VMess config optimized for specific service with speed test support"""
        try:
            service_config = SERVICE_PAYLOADS.get(service, SERVICE_PAYLOADS["all_sites"])
            working_servers = self.get_working_servers()
            
            # Sort by priority
            working_servers.sort(key=lambda x: x.get('priority', 999))
            
            for server_config in working_servers:
                try:
                    # Generate UUID
                    config_uuid = str(uuid.uuid4())
                    
                    # Create VMess config
                    vmess_config = {
                        "v": "2",
                        "ps": f"{service_config['name']} - SpeedTest Optimized",
                        "add": server_config["add"],
                        "port": server_config["port"], 
                        "id": config_uuid,
                        "aid": "0",
                        "net": server_config["net"],
                        "type": "none",
                        "host": service_config["host"],
                        "path": server_config["path"],
                        "tls": server_config["tls"],
                        "sni": service_config["sni"]
                    }
                    
                    # Encode to VMess link
                    vmess_json = json.dumps(vmess_config, separators=(',', ':'))
                    vmess_link = "vmess://" + base64.b64encode(vmess_json.encode()).decode()
                    
                    # Create V2Ray client config with routing
                    v2ray_client_config = self.create_v2ray_client_config(vmess_config, service_config)
                    
                    config_data = {
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
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                        "injector_instructions": "Import VMess link in HTTP Injector and use provided payload",
                        "speed_test_support": True,
                        "speed_test_alternatives": [
                            "https://openspeedtest.com/ (VPN-friendly)",
                            "https://librespeed.org/ (Open source)",
                            "fast.com (Netflix speed test)",
                            "Mobile speed test apps work better"
                        ],
                        "optimization_notes": [
                            "TCP transport for better speed test performance",
                            "Disabled multiplexing for accurate measurements", 
                            "Direct routing for speed test domains",
                            "Port 8080 routed directly for Speedtest.net"
                        ]
                    }
                    
                    logger.info(f"Successfully created VMess config for {service} using {server_config['add']}")
                    return config_data
                        
                except Exception as e:
                    logger.error(f"Server {server_config['add']} failed for service {service}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error creating optimized VMess config: {e}")
            
        return None
    
    def create_v2ray_client_config(self, vmess_config: Dict, service_config: Dict) -> Dict:
        """Create V2Ray client configuration with routing"""
        return {
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

    def generate_v2ray_config(self, service: str = "all_sites") -> Optional[Dict]:
        """Generate V2Ray config for specific service"""
        try:
            config = self.create_optimized_vmess(service)
            if config:
                return config
        except Exception as e:
            logger.error(f"V2Ray generation failed: {e}")
        
        # Return demo config if generation fails
        return self.create_demo_v2ray_config(service)
    
    def create_demo_v2ray_config(self, service_key: str) -> Dict:
        """Create demo V2Ray config when providers fail"""
        service_config = SERVICE_PAYLOADS.get(service_key, SERVICE_PAYLOADS["all_sites"])
        
        vmess_config = {
            "v": "2",
            "ps": f"{service_config['name']} - Demo SpeedTest",
            "add": "demo.v2ray.com",
            "port": "443",
            "id": str(uuid.uuid4()),
            "aid": "0", 
            "net": "tcp",
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
            "server": "demo.v2ray.com",
            "port": "443",
            "host": service_config["host"],
            "sni": service_config["sni"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            "injector_instructions": "Demo config - Import VMess link in HTTP Injector",
            "speed_test_support": True,
            "speed_test_alternatives": [
                "https://openspeedtest.com/ (VPN-friendly)",
                "https://librespeed.org/ (Open source)",
                "fast.com (Netflix speed test)",
                "Mobile apps work better than web versions"
            ],
            "note": "Demo config - For testing purposes only"
        }

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
            config_type = config_type.lower()
            
            if config_type in ["ssh", "auto"]:
                config = self.ssh_gen.generate_ssh_config()
                if config:
                    return config
                    
            if config_type in ["v2ray", "vmess", "vless", "auto"]:
                config = self.v2ray_gen.generate_v2ray_config(service)
                if config:
                    return config
                    
            # If auto and nothing worked, try creating demo configs
            if config_type == "auto":
                return self.create_demo_config()
                
        except Exception as e:
            logger.error(f"Error generating config: {e}")
            
        return None
    
    def generate_service_config(self, service_key: str) -> Optional[Dict]:
        """Generate service-specific V2Ray config"""
        try:
            logger.info(f"Generating service config for: {service_key}")
            
            if service_key not in SERVICE_PAYLOADS:
                logger.warning(f"Unknown service key: {service_key}")
                service_key = "all_sites"
            
            config = self.v2ray_gen.generate_v2ray_config(service_key)
            
            if config:
                logger.info(f"Successfully generated {service_key} config")
                return config
            else:
                logger.warning(f"Failed to generate config for service: {service_key}")
                return self.v2ray_gen.create_demo_v2ray_config(service_key)
                
        except Exception as e:
            logger.error(f"Error generating service config for {service_key}: {e}")
            return self.v2ray_gen.create_demo_v2ray_config(service_key)
    
    def create_demo_config(self) -> Dict:
        """Create demo SSH config when all providers fail"""
        return self.ssh_gen.create_demo_ssh_config()

# Global generator instance
generator = MainGenerator()