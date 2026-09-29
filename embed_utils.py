"""
Embed utilities for the ticket bot
"""
import discord
from datetime import datetime, timezone
from config import THUMBNAIL_URL, BANNER_URL, get_banner_settings


def create_embed(title: str, description: str, color: discord.Color = None, message_type: str = "general", show_banner: bool = None, **kwargs) -> discord.Embed:
    """Create a professional embed with consistent styling
    
    Args:
        title: Embed title
        description: Embed description
        color: Embed color
        message_type: Type of message for banner settings (ticket_creation, purchase_creation, etc.)
        show_banner: Override banner setting (True/False) if provided
        **kwargs: Additional parameters (fields, thumbnail, etc.)
    """
    if color is None:
        color = discord.Color.from_rgb(54, 57, 62)  # Professional dark gray
    
    # Get current banner settings dynamically
    banner_settings = get_banner_settings()
    
    # Determine banner visibility
    if show_banner is not None:
        # Explicit override takes precedence
        should_show_banner = show_banner
    else:
        # Use message type setting, fallback to general
        should_show_banner = banner_settings.get(message_type, banner_settings["general"])
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.set_footer(text="Made by Shashank Sharma", icon_url=None)
    
    # Add thumbnail if URL is provided
    if THUMBNAIL_URL:
        embed.set_thumbnail(url=THUMBNAIL_URL)
    
    # Add banner image if URL is provided and should_show_banner is True
    if BANNER_URL and should_show_banner:
        embed.set_image(url=BANNER_URL)
    
    # Override thumbnail if specifically provided in kwargs
    if "thumbnail" in kwargs:
        embed.set_thumbnail(url=kwargs["thumbnail"])
    
    if "fields" in kwargs:
        for name, value, inline in kwargs["fields"]:
            embed.add_field(name=name, value=value, inline=inline)
    
    return embed
