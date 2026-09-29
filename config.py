"""
Configuration module for the ticket bot
"""
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Banner configuration file
BANNER_CONFIG_FILE = "banner_config.json"


def load_banner_config():
    """Load banner settings from JSON file or use defaults"""
    if os.path.exists(BANNER_CONFIG_FILE):
        try:
            with open(BANNER_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading banner config: {e}")
    
    # Default settings
    return {
        "ticket_creation": os.getenv("BANNER_TICKET_CREATION", "true").lower() == "true",
        "purchase_creation": os.getenv("BANNER_PURCHASE_CREATION", "true").lower() == "true",
        "ticket_controls": os.getenv("BANNER_TICKET_CONTROLS", "true").lower() == "true",
        "payment_info": os.getenv("BANNER_PAYMENT_INFO", "true").lower() == "true",
        "rating": os.getenv("BANNER_RATING", "true").lower() == "true",
        "vouch": os.getenv("BANNER_VOUCH", "true").lower() == "true",
        "config": os.getenv("BANNER_CONFIG", "true").lower() == "true",
        "panel": os.getenv("BANNER_PANEL", "true").lower() == "true",
        "general": os.getenv("BANNER_GENERAL", "true").lower() == "true",
    }


def save_banner_config(config):
    """Save banner settings to JSON file"""
    try:
        with open(BANNER_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving banner config: {e}")


# Bot Configuration
TOKEN = os.getenv("DISCORD_TOKEN")
SUPPORT_ROLE_ID = int(os.getenv("SUPPORT_ROLE_ID", "0"))
CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID", "0"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))
SYNC_GUILD_ID = int(os.getenv("SYNC_GUILD_ID", "0"))
RATING_CHANNEL_ID = int(os.getenv("RATING_CHANNEL_ID", "0"))
VOUCH_CHANNEL_ID = int(os.getenv("VOUCH_CHANNEL_ID", "0"))

# Image URLs
THUMBNAIL_URL = os.getenv("THUMBNAIL_URL", "")
BANNER_URL = os.getenv("BANNER_URL", "")
INR_QR_URL = os.getenv("INR_QR_URL", "")
LTC_QR_URL = os.getenv("LTC_QR_URL", "")

# Payment Details
INR_WALLET_ADDRESS = os.getenv("INR_WALLET_ADDRESS", "")
LTC_WALLET_ADDRESS = os.getenv("LTC_WALLET_ADDRESS", "")

# Banner settings for different message types (loaded from file)
def get_banner_settings():
    """Get current banner settings"""
    return load_banner_config()


# Load banner settings
BANNER_SETTINGS = load_banner_config()

# Validation
if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found in environment variables")
if SUPPORT_ROLE_ID == 0:
    raise ValueError("SUPPORT_ROLE_ID not found in environment variables")
if CATEGORY_ID == 0:
    raise ValueError("TICKET_CATEGORY_ID not found in environment variables")

# Feature toggles (optional, can be set in .env)
ENABLE_GIVEAWAYS = os.getenv("ENABLE_GIVEAWAYS", "true").lower() == "true"
ENABLE_INVITE_TRACKER = os.getenv("ENABLE_INVITE_TRACKER", "true").lower() == "true"
ENABLE_WELCOMER = os.getenv("ENABLE_WELCOMER", "true").lower() == "true"

# Invite announcement channel
INVITE_ANNOUNCEMENT_CHANNEL_ID = int(os.getenv("INVITE_ANNOUNCEMENT_CHANNEL_ID", "0"))


def update_env_var(key: str, value: str):
    """Update a value in the .env file"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    try:
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        with open(env_path, 'w') as f:
            for line in lines:
                if line.startswith(f"{key}="):
                    f.write(f"{key}={value}\n")
                else:
                    f.write(line)
    except Exception as e:
        print(f"Error updating .env file: {e}")


def toggle_banner_setting(setting_name: str):
    """Toggle a banner setting and save to file"""
    global BANNER_SETTINGS
    if setting_name in BANNER_SETTINGS:
        BANNER_SETTINGS[setting_name] = not BANNER_SETTINGS[setting_name]
        save_banner_config(BANNER_SETTINGS)
        return BANNER_SETTINGS[setting_name]
    return None


def set_banner_setting(setting_name: str, value: bool):
    """Set a banner setting to a specific value and save to file"""
    global BANNER_SETTINGS
    if setting_name in BANNER_SETTINGS:
        BANNER_SETTINGS[setting_name] = value
        save_banner_config(BANNER_SETTINGS)
        return BANNER_SETTINGS[setting_name]
    return None
