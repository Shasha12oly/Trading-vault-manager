"""
Configuration module for the ticket bot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

# Banner settings for different message types
BANNER_SETTINGS = {
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
