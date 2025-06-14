import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, SquareModuleDrawer
from qrcode.image.styles.colorfills import SolidFillColorMask
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import logging
from typing import Optional, Union

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
                        style: str = "default",
                        logo_path: Optional[str] = None) -> Optional[bytes]:
        """
        Generate QR code with various styling options
        
        Args:
            data: Data to encode in QR code
            filename: Optional filename to save QR code
            style: Style type ('default', 'rounded', 'colored')
            logo_path: Optional path to logo image to embed
            
        Returns:
            QR code image as bytes
        """
        try:
            qr = qrcode.QRCode(**self.default_config)
            qr.add_data(data)
            qr.make(fit=True)
            
            # Generate based on style
            if style == "rounded":
                img = qr.make_image(
                    image_factory=StyledPilImage,
                    module_drawer=RoundedModuleDrawer(),
                    fill_color="black",
                    back_color="white"
                )
            elif style == "colored":
                img = qr.make_image(
                    image_factory=StyledPilImage,
                    module_drawer=SquareModuleDrawer(),
                    color_mask=SolidFillColorMask(
                        back_color=(255, 255, 255),  # White background
                        front_color=(0, 100, 200)    # Blue foreground
                    )
                )
            else:
                # Default style
                img = qr.make_image(fill_color="black", back_color="white")
            
            # Add logo if provided
            if logo_path:
                img = self.add_logo_to_qr(img, logo_path)
            
            # Convert to bytes
            img_bytes = self.image_to_bytes(img)
            
            # Save if filename provided
            if filename:
                img.save(filename)
                logger.info(f"QR code saved as {filename}")
            
            return img_bytes
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return None
    
    def add_logo_to_qr(self, qr_img: Image.Image, logo_path: str) -> Image.Image:
        """Add logo to center of QR code"""
        try:
            logo = Image.open(logo_path)
            
            # Calculate logo size (10% of QR code)
            qr_width, qr_height = qr_img.size
            logo_size = min(qr_width, qr_height) // 10
            
            # Resize logo
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Create circular mask for logo
            mask = Image.new("L", (logo_size, logo_size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, logo_size, logo_size), fill=255)
            
            # Apply mask to logo
            logo.putalpha(mask)
            
            # Calculate position (center)
            logo_pos = (
                (qr_width - logo_size) // 2,
                (qr_height - logo_size) // 2
            )
            
            # Paste logo onto QR code
            qr_img.paste(logo, logo_pos, logo)
            
            return qr_img
            
        except Exception as e:
            logger.error(f"Error adding logo to QR code: {e}")
            return qr_img
    
    def image_to_bytes(self, img: Image.Image, format: str = "PNG") -> bytes:
        """Convert PIL Image to bytes"""
        try:
            img_buffer = io.BytesIO()
            img.save(img_buffer, format=format)
            img_buffer.seek(0)
            return img_buffer.getvalue()
        except Exception as e:
            logger.error(f"Error converting image to bytes: {e}")
            return b""
    
    def generate_config_qr(self, config_data: dict) -> Optional[bytes]:
        """Generate QR code specifically for VPN configs"""
        try:
            config_type = config_data.get("type", "").lower()
            
            if config_type in ["vmess", "vless"]:
                # Use the direct link for V2Ray configs
                qr_data = config_data.get("link", "")
                style = "colored"
            elif config_type == "ssh":
                # Create SSH connection string
                host = config_data.get("host", "")
                port = config_data.get("port", 22)
                username = config_data.get("username", "")
                password = config_data.get("password", "")
                
                qr_data = f"ssh://{username}:{password}@{host}:{port}"
                style = "default"
            else:
                # Fallback to JSON
                import json
                qr_data = json.dumps(config_data, indent=2)
                style = "rounded"
            
            if not qr_data:
                logger.error("No data to encode in QR code")
                return None
                
            return self.generate_qr_code(qr_data, style=style)
            
        except Exception as e:
            logger.error(f"Error generating config QR code: {e}")
            return None
    
    def generate_referral_qr(self, bot_username: str, user_id: int) -> Optional[bytes]:
        """Generate QR code for referral link"""
        try:
            referral_link = f"https://t.me/{bot_username}?start={user_id}"
            return self.generate_qr_code(referral_link, style="colored")
        except Exception as e:
            logger.error(f"Error generating referral QR code: {e}")
            return None
    
    def generate_channel_qr(self, channel_url: str) -> Optional[bytes]:
        """Generate QR code for channel link"""
        try:
            return self.generate_qr_code(channel_url, style="rounded")
        except Exception as e:
            logger.error(f"Error generating channel QR code: {e}")
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
                # Try to load a font
                font_title = ImageFont.truetype("arial.ttf", 24)
                font_text = ImageFont.truetype("arial.ttf", 16)
            except:
                # Fallback to default font
                font_title = ImageFont.load_default()
                font_text = ImageFont.load_default()
            
            # Draw title
            title = f"{config_data.get('type', 'Config').upper()} Configuration"
            title_bbox = draw.textbbox((0, 0), title, font=font_title)
            title_x = (card_width - (title_bbox[2] - title_bbox[0])) // 2
            draw.text((title_x, 10), title, fill="black", font=font_title)
            
            # Draw config details
            y_offset = qr_y + qr_size + 30
            
            config_type = config_data.get("type", "").lower()
            if config_type == "ssh":
                details = [
                    f"Server: {config_data.get('host', 'N/A')}",
                    f"Port: {config_data.get('port', 'N/A')}",
                    f"Username: {config_data.get('username', 'N/A')}",
                    f"Password: {config_data.get('password', 'N/A')}"
                ]
            elif config_type in ["vmess", "vless"]:
                details = [
                    f"Type: {config_type.upper()}",
                    f"Server: {config_data.get('server', 'N/A')}",
                    f"Port: {config_data.get('port', 'N/A')}",
                    "Scan QR code to import"
                ]
            else:
                details = ["Scan QR code for configuration"]
            
            for detail in details:
                detail_bbox = draw.textbbox((0, 0), detail, font=font_text)
                detail_x = (card_width - (detail_bbox[2] - detail_bbox[0])) // 2
                draw.text((detail_x, y_offset), detail, fill="black", font=font_text)
                y_offset += 30
            
            # Add expiry info
            expires_at = config_data.get("expires_at", "")
            if expires_at:
                expiry_text = f"Expires: {expires_at[:10]}"  # Just the date part
                expiry_bbox = draw.textbbox((0, 0), expiry_text, font=font_text)
                expiry_x = (card_width - (expiry_bbox[2] - expiry_bbox[0])) // 2
                draw.text((expiry_x, y_offset + 20), expiry_text, fill="red", font=font_text)
            
            # Convert to bytes
            return self.qr_gen.image_to_bytes(card)
            
        except Exception as e:
            logger.error(f"Error creating config card: {e}")
            return None

# Global instances
qr_generator = QRCodeGenerator()
qr_card_generator = QRCodeWithText()