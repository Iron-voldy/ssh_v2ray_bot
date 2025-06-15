import qrcode
from PIL import Image, ImageDraw, ImageFont
import io
import json
import logging
from typing import Optional

# Configure logging  
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QRCodeGenerator:
    def __init__(self):
        self.default_config = {
            'version': 1,
            'error_correction': qrcode.constants.ERROR_CORRECT_L,
            'box_size': 10,
            'border': 4,
        }
        
    def generate_qr_code(self, 
                        data: str, 
                        filename: Optional[str] = None,
                        fill_color: str = "black",
                        back_color: str = "white") -> Optional[bytes]:
        """
        Generate QR code with basic styling
        
        Args:
            data: Data to encode in QR code
            filename: Optional filename to save QR code
            fill_color: QR code color
            back_color: Background color
            
        Returns:
            QR code image as bytes
        """
        try:
            qr = qrcode.QRCode(**self.default_config)
            qr.add_data(data)
            qr.make(fit=True)
            
            # Generate QR code image
            img = qr.make_image(fill_color=fill_color, back_color=back_color)
            
            # Convert to bytes
            img_bytes = self.image_to_bytes(img)
            
            # Save if filename provided
            if filename:
                img.save(filename)
                logger.info("QR code saved as {}".format(filename))
            
            return img_bytes
            
        except Exception as e:
            logger.error("Error generating QR code: {}".format(e))
            return None
    
    def image_to_bytes(self, img: Image.Image, format: str = "PNG") -> bytes:
        """Convert PIL Image to bytes"""
        try:
            img_buffer = io.BytesIO()
            img.save(img_buffer, format=format)
            img_buffer.seek(0)
            return img_buffer.getvalue()
        except Exception as e:
            logger.error("Error converting image to bytes: {}".format(e))
            return b""
    
    def generate_config_qr(self, config_data: dict) -> Optional[bytes]:
        """Generate QR code specifically for VPN configs"""
        try:
            config_type = config_data.get("type", "").lower()
            
            if config_type in ["vmess", "vless"]:
                # Use the direct link for V2Ray configs
                qr_data = config_data.get("link", "")
                fill_color = "blue"
            elif config_type == "ssh":
                # Create SSH connection string
                host = config_data.get("host", "")
                port = config_data.get("port", 22)
                username = config_data.get("username", "")
                password = config_data.get("password", "")
                
                qr_data = "ssh://{}:{}@{}:{}".format(username, password, host, port)
                fill_color = "black"
            else:
                # Fallback to JSON
                qr_data = json.dumps(config_data, indent=2)
                fill_color = "green"
            
            if not qr_data:
                logger.error("No data to encode in QR code")
                return None
                
            return self.generate_qr_code(qr_data, fill_color=fill_color)
            
        except Exception as e:
            logger.error("Error generating config QR code: {}".format(e))
            return None
    
    def generate_referral_qr(self, bot_username: str, user_id: int) -> Optional[bytes]:
        """Generate QR code for referral link"""
        try:
            referral_link = "https://t.me/{}?start={}".format(bot_username, user_id)
            return self.generate_qr_code(referral_link, fill_color="purple")
        except Exception as e:
            logger.error("Error generating referral QR code: {}".format(e))
            return None
    
    def generate_channel_qr(self, channel_url: str) -> Optional[bytes]:
        """Generate QR code for channel link"""
        try:
            return self.generate_qr_code(channel_url, fill_color="orange")
        except Exception as e:
            logger.error("Error generating channel QR code: {}".format(e))
            return None

class QRCodeWithText:
    """Generate QR codes with additional text information"""
    
    def __init__(self):
        self.qr_gen = QRCodeGenerator()
        
    def create_config_card(self, config_data: dict) -> Optional[bytes]:
        """Create a card with QR code and config information"""
        try:
            # Generate QR code
            qr_bytes = self.qr_gen.generate_config_qr(config_data)
            if not qr_bytes:
                return None
            
            # Load QR image
            qr_img = Image.open(io.BytesIO(qr_bytes))
            
            # Create card background
            card_width = 800
            card_height = 600
            card = Image.new("RGB", (card_width, card_height), "white")
            
            # Resize QR code
            qr_size = 300
            qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
            
            # Position QR code
            qr_x = (card_width - qr_size) // 2
            qr_y = 50
            card.paste(qr_img, (qr_x, qr_y))
            
            # Add text information
            draw = ImageDraw.Draw(card)
            
            try:
                # Try to load a system font
                font_title = ImageFont.truetype("arial.ttf", 24)
                font_text = ImageFont.truetype("arial.ttf", 16)
            except:
                try:
                    # Try alternative fonts
                    font_title = ImageFont.truetype("calibri.ttf", 24)
                    font_text = ImageFont.truetype("calibri.ttf", 16)
                except:
                    # Fallback to default font
                    font_title = ImageFont.load_default()
                    font_text = ImageFont.load_default()
            
            # Draw title
            title = "{} Configuration".format(config_data.get('type', 'Config').upper())
            
            # Get text size using textbbox (compatible method)
            try:
                title_bbox = draw.textbbox((0, 0), title, font=font_title)
                title_width = title_bbox[2] - title_bbox[0]
            except:
                # Fallback for older Pillow versions
                title_width = len(title) * 12  # Approximate
            
            title_x = (card_width - title_width) // 2
            draw.text((title_x, 10), title, fill="black", font=font_title)
            
            # Draw config details
            y_offset = qr_y + qr_size + 30
            
            config_type = config_data.get("type", "").lower()
            if config_type == "ssh":
                details = [
                    "Server: {}".format(config_data.get('host', 'N/A')),
                    "Port: {}".format(config_data.get('port', 'N/A')),
                    "Username: {}".format(config_data.get('username', 'N/A')),
                    "Password: {}".format(config_data.get('password', 'N/A'))
                ]
            elif config_type in ["vmess", "vless"]:
                details = [
                    "Type: {}".format(config_type.upper()),
                    "Server: {}".format(config_data.get('server', 'N/A')),
                    "Port: {}".format(config_data.get('port', 'N/A')),
                    "Scan QR code to import"
                ]
            else:
                details = ["Scan QR code for configuration"]
            
            for detail in details:
                try:
                    detail_bbox = draw.textbbox((0, 0), detail, font=font_text)
                    detail_width = detail_bbox[2] - detail_bbox[0]
                except:
                    detail_width = len(detail) * 8  # Approximate
                
                detail_x = (card_width - detail_width) // 2
                draw.text((detail_x, y_offset), detail, fill="black", font=font_text)
                y_offset += 30
            
            # Add expiry info
            expires_at = config_data.get("expires_at", "")
            if expires_at:
                expiry_text = "Expires: {}".format(expires_at[:10])  # Just the date part
                try:
                    expiry_bbox = draw.textbbox((0, 0), expiry_text, font=font_text)
                    expiry_width = expiry_bbox[2] - expiry_bbox[0]
                except:
                    expiry_width = len(expiry_text) * 8
                
                expiry_x = (card_width - expiry_width) // 2
                draw.text((expiry_x, y_offset + 20), expiry_text, fill="red", font=font_text)
            
            # Convert to bytes
            return self.qr_gen.image_to_bytes(card)
            
        except Exception as e:
            logger.error("Error creating config card: {}".format(e))
            return None

# Global instances
qr_generator = QRCodeGenerator()
qr_card_generator = QRCodeWithText()