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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigGenerator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
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
            url = "https://speedssh.com/create-ssh-server/sg1"
            username = self.generate_username()
            password = self.generate_password()
            
            # Get the form first
            response = self.session.get("https://speedssh.com/ssh-server/singapore")
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find CSRF token if needed
            csrf_token = None
            csrf_input = soup.find('input', {'name': '_token'})
            if csrf_input:
                csrf_token = csrf_input.get('value')
            
            payload = {
                'username': username,
                'password': password,
                'server': 'sg1'
            }
            
            if csrf_token:
                payload['_token'] = csrf_token
            
            # Create account
            response = self.session.post(url, data=payload, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract account details
                account_info = self.extract_ssh_info(soup, username, password)
                if account_info:
                    return account_info
                    
        except Exception as e:
            logger.error(f"Error creating SpeedSSH account: {e}")
            
        return None
    
    def extract_ssh_info(self, soup: BeautifulSoup, username: str, password: str) -> Optional[Dict]:
        """Extract SSH info from HTML"""
        try:
            # Look for SSH details in various possible locations
            info_div = soup.find('div', class_='ssh-detail') or \
                      soup.find('div', class_='account-detail') or \
                      soup.find('div', class_='server-info')
            
            if info_div:
                text = info_div.get_text(separator='\n')
                
                # Extract server info using regex
                host_match = re.search(r'Host[:\s]+([^\s\n]+)', text, re.IGNORECASE)
                port_match = re.search(r'Port[:\s]+(\d+)', text, re.IGNORECASE)
                
                host = host_match.group(1) if host_match else "sg1.speedssh.com"
                port = int(port_match.group(1)) if port_match else 22
                
                return {
                    "type": "SSH",
                    "host": host,
                    "port": port,
                    "username": username,
                    "password": password,
                    "created_at": datetime.utcnow().isoformat(),
                    "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                    "raw_info": text
                }
                
        except Exception as e:
            logger.error(f"Error extracting SSH info: {e}")
            
        return None
    
    def create_fastssh_account(self) -> Optional[Dict]:
        """Create SSH account from FastSSH (Alternative provider)"""
        try:
            url = "https://fastssh.com/create-ssh-server/sg"
            username = self.generate_username()
            password = self.generate_password()
            
            payload = {
                'username': username,
                'password': password,
                'country': 'SG'
            }
            
            response = self.session.post(url, data=payload, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                return self.extract_ssh_info(soup, username, password)
                
        except Exception as e:
            logger.error(f"Error creating FastSSH account: {e}")
            
        return None
    
    def generate_ssh_config(self) -> Optional[Dict]:
        """Generate SSH config from available providers"""
        providers = [
            self.create_speedssh_account,
            self.create_fastssh_account
        ]
        
        for provider in providers:
            try:
                config = provider()
                if config:
                    return config
                time.sleep(2)  # Rate limiting
            except Exception as e:
                logger.error(f"Provider failed: {e}")
                continue
                
        return None

class V2RayGenerator(ConfigGenerator):
    def __init__(self):
        super().__init__()
        
    def create_vmess_config(self) -> Optional[Dict]:
        """Create VMess configuration"""
        try:
            # Generate VMess config
            vmess_config = {
                "v": "2",
                "ps": f"Free-VMess-{random.randint(1000, 9999)}",
                "add": "free.v2rayfree.com",
                "port": "443",
                "id": str(uuid.uuid4()),
                "aid": "0",
                "net": "ws",
                "type": "none",
                "host": "free.v2rayfree.com",
                "path": "/path",
                "tls": "tls"
            }
            
            # Encode to VMess link
            vmess_json = json.dumps(vmess_config)
            vmess_link = "vmess://" + base64.b64encode(vmess_json.encode()).decode()
            
            return {
                "type": "VMess",
                "config": vmess_config,
                "link": vmess_link,
                "qr_data": vmess_link,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(days=3)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating VMess config: {e}")
            
        return None
    
    def create_vless_config(self) -> Optional[Dict]:
        """Create VLess configuration"""
        try:
            server_id = str(uuid.uuid4())
            server_host = "free.v2rayfree.com"
            server_port = "443"
            
            vless_link = f"vless://{server_id}@{server_host}:{server_port}?type=ws&security=tls&path=/path&host={server_host}#Free-VLess-{random.randint(1000, 9999)}"
            
            return {
                "type": "VLess",
                "link": vless_link,
                "qr_data": vless_link,
                "server": server_host,
                "port": server_port,
                "id": server_id,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(days=3)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating VLess config: {e}")
            
        return None
    
    def scrape_free_v2ray(self) -> Optional[Dict]:
        """Scrape free V2Ray configs from public providers"""
        try:
            # This is a placeholder - implement actual scraping based on available providers
            urls = [
                "https://v2rayfree.com/free-vmess",
                "https://free-ss.site/",
            ]
            
            for url in urls:
                try:
                    response = self.session.get(url, timeout=30)
                    if response.status_code == 200:
                        # Parse and extract configs
                        config = self.parse_v2ray_page(response.text)
                        if config:
                            return config
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping V2Ray configs: {e}")
            
        return None
    
    def parse_v2ray_page(self, html: str) -> Optional[Dict]:
        """Parse V2Ray config page"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for VMess/VLess links
            vmess_pattern = r'vmess://[A-Za-z0-9+/=]+'
            vless_pattern = r'vless://[^\s<>"]+'
            
            vmess_matches = re.findall(vmess_pattern, html)
            vless_matches = re.findall(vless_pattern, html)
            
            if vmess_matches:
                return {
                    "type": "VMess",
                    "link": vmess_matches[0],
                    "qr_data": vmess_matches[0],
                    "created_at": datetime.utcnow().isoformat(),
                    "expires_at": (datetime.utcnow() + timedelta(days=1)).isoformat()
                }
            elif vless_matches:
                return {
                    "type": "VLess", 
                    "link": vless_matches[0],
                    "qr_data": vless_matches[0],
                    "created_at": datetime.utcnow().isoformat(),
                    "expires_at": (datetime.utcnow() + timedelta(days=1)).isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error parsing V2Ray page: {e}")
            
        return None

    def generate_v2ray_config(self) -> Optional[Dict]:
        """Generate V2Ray config from available methods"""
        methods = [
            self.scrape_free_v2ray,
            self.create_vmess_config,
            self.create_vless_config
        ]
        
        for method in methods:
            try:
                config = method()
                if config:
                    return config
                time.sleep(2)  # Rate limiting
            except Exception as e:
                logger.error(f"V2Ray method failed: {e}")
                continue
                
        return None

# Main generator class
class MainGenerator:
    def __init__(self):
        self.ssh_gen = SSHGenerator()
        self.v2ray_gen = V2RayGenerator()
    
    def generate_config(self, config_type: str = "auto") -> Optional[Dict]:
        """Generate config based on type"""
        try:
            if config_type.lower() in ["ssh", "auto"]:
                config = self.ssh_gen.generate_ssh_config()
                if config:
                    return config
                    
            if config_type.lower() in ["v2ray", "vmess", "vless", "auto"]:
                config = self.v2ray_gen.generate_v2ray_config()
                if config:
                    return config
                    
            # If auto and nothing worked, try creating demo configs
            if config_type.lower() == "auto":
                return self.create_demo_config()
                
        except Exception as e:
            logger.error(f"Error generating config: {e}")
            
        return None
    
    def create_demo_config(self) -> Dict:
        """Create demo config when providers fail"""
        username = self.ssh_gen.generate_username()
        password = self.ssh_gen.generate_password()
        
        return {
            "type": "SSH",
            "host": "demo.freehost.com",
            "port": 22,
            "username": username,
            "password": password,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "note": "Demo config - providers temporarily unavailable"
        }

# Import uuid for V2Ray
import uuid

# Global generator instance
generator = MainGenerator()