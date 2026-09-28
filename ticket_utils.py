"""
Utility functions for ticket management
"""
import discord


def owner_tag(user_id: int) -> str:
    """Generate owner tag for ticket topic"""
    return f"ticket-owner:{user_id}"


def get_ticket_info(channel: discord.TextChannel) -> dict:
    """Extract ticket info from channel topic"""
    topic = channel.topic or ""
    info = {"owner_id": 0, "category": "Unknown", "priority": "Medium", "item": None, "quantity": None, "claimed_by": None}
    
    for part in topic.split("|"):
        part = part.strip()
        if part.startswith("ticket-owner:"):
            info["owner_id"] = int(part.split(":")[1])
        elif part.startswith("category:"):
            info["category"] = part.split(":")[1]
        elif part.startswith("priority:"):
            info["priority"] = part.split(":")[1]
        elif part.startswith("item:"):
            info["item"] = part.split(":")[1]
        elif part.startswith("quantity:"):
            info["quantity"] = part.split(":")[1]
        elif part.startswith("claimed:"):
            info["claimed_by"] = int(part.split(":")[1])
    
    return info
