"""
Welcomer system module - Welcome messages for new members
"""
import discord
from discord import app_commands
import json
import os
from config import SUPPORT_ROLE_ID
from embed_utils import create_embed

# Welcome configuration storage
WELCOME_CONFIG_FILE = "welcome_config.json"


def load_welcome_config():
    if os.path.exists(WELCOME_CONFIG_FILE):
        with open(WELCOME_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_welcome_config(config):
    with open(WELCOME_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)


async def send_welcome(member):
    """Send welcome message to new member"""
    config = load_welcome_config()
    guild_id = str(member.guild.id)
    
    if guild_id not in config:
        return
    
    guild_config = config[guild_id]
    
    if not guild_config.get("enabled", False):
        return
    
    welcome_channel_id = guild_config.get("channel_id")
    if not welcome_channel_id:
        return
    
    welcome_channel = member.guild.get_channel(welcome_channel_id)
    if not welcome_channel:
        return
    
    # Get welcome message
    welcome_message = guild_config.get("message", "Welcome {user} to {server}! We're glad to have you here!")
    
    # Replace placeholders
    welcome_message = welcome_message.replace("{user}", member.mention)
    welcome_message = welcome_message.replace("{server}", member.guild.name)
    welcome_message = welcome_message.replace("{count}", str(member.guild.member_count))
    
    # Send welcome message
    if guild_config.get("use_embed", True):
        embed = create_embed(
            title="🎉 Welcome!",
            description=welcome_message,
            color=discord.Color.green(),
            message_type="general"
        )
        
        # Add user avatar if available
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        
        await welcome_channel.send(embed=embed)
    else:
        await welcome_channel.send(welcome_message)
    
    # Send DM if enabled
    if guild_config.get("send_dm", False):
        dm_message = guild_config.get("dm_message", "Thanks for joining {server}! If you have any questions, feel free to ask.")
        dm_message = dm_message.replace("{user}", member.mention)
        dm_message = dm_message.replace("{server}", member.guild.name)
        
        try:
            if guild_config.get("dm_use_embed", True):
                dm_embed = create_embed(
                    title="👋 Welcome!",
                    description=dm_message,
                    color=discord.Color.blue(),
                    message_type="general"
                )
                await member.send(embed=dm_embed)
            else:
                await member.send(dm_message)
        except discord.Forbidden:
            pass


async def send_goodbye(member):
    """Send goodbye message when member leaves"""
    config = load_welcome_config()
    guild_id = str(member.guild.id)
    
    if guild_id not in config:
        return
    
    guild_config = config[guild_id]
    
    if not guild_config.get("goodbye_enabled", False):
        return
    
    goodbye_channel_id = guild_config.get("goodbye_channel_id")
    if not goodbye_channel_id:
        return
    
    goodbye_channel = member.guild.get_channel(goodbye_channel_id)
    if not goodbye_channel:
        return
    
    # Get goodbye message
    goodbye_message = guild_config.get("goodbye_message", "Goodbye {user}! We'll miss you.")
    
    # Replace placeholders
    goodbye_message = goodbye_message.replace("{user}", member.mention)
    goodbye_message = goodbye_message.replace("{server}", member.guild.name)
    
    # Send goodbye message
    if guild_config.get("goodbye_use_embed", True):
        embed = create_embed(
            title="👋 Goodbye!",
            description=goodbye_message,
            color=discord.Color.red(),
            message_type="general"
        )
        await goodbye_channel.send(embed=embed)
    else:
        await goodbye_channel.send(goodbye_message)


# Configuration commands
async def setwelcomemessage_command(interaction: discord.Interaction, message: str):
    """Set the welcome message"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can set welcome messages.", ephemeral=True)
        return
    
    config = load_welcome_config()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in config:
        config[guild_id] = {}
    
    config[guild_id]["message"] = message
    save_welcome_config(config)
    
    embed = create_embed(
        title="✅ Welcome Message Set",
        description=f"Welcome message has been set to:\n\n{message}",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def setwelcomerchannel_command(interaction: discord.Interaction, channel: discord.TextChannel):
    """Set the welcome channel"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can set welcome channels.", ephemeral=True)
        return
    
    config = load_welcome_config()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in config:
        config[guild_id] = {}
    
    config[guild_id]["channel_id"] = channel.id
    config[guild_id]["enabled"] = True
    save_welcome_config(config)
    
    embed = create_embed(
        title="✅ Welcome Channel Set",
        description=f"Welcome channel has been set to {channel.mention}",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def togglewelcome_command(interaction: discord.Interaction):
    """Toggle welcome messages on/off"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can toggle welcome messages.", ephemeral=True)
        return
    
    config = load_welcome_config()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in config:
        config[guild_id] = {}
    
    current_state = config[guild_id].get("enabled", False)
    config[guild_id]["enabled"] = not current_state
    save_welcome_config(config)
    
    status = "enabled" if config[guild_id]["enabled"] else "disabled"
    embed = create_embed(
        title="✅ Welcome Messages Toggled",
        description=f"Welcome messages are now **{status}**",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def setgoodbyemessage_command(interaction: discord.Interaction, message: str):
    """Set the goodbye message"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can set goodbye messages.", ephemeral=True)
        return
    
    config = load_welcome_config()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in config:
        config[guild_id] = {}
    
    config[guild_id]["goodbye_message"] = message
    config[guild_id]["goodbye_enabled"] = True
    save_welcome_config(config)
    
    embed = create_embed(
        title="✅ Goodbye Message Set",
        description=f"Goodbye message has been set to:\n\n{message}",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def setgoodbyechannel_command(interaction: discord.Interaction, channel: discord.TextChannel):
    """Set the goodbye channel"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can set goodbye channels.", ephemeral=True)
        return
    
    config = load_welcome_config()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in config:
        config[guild_id] = {}
    
    config[guild_id]["goodbye_channel_id"] = channel.id
    config[guild_id]["goodbye_enabled"] = True
    save_welcome_config(config)
    
    embed = create_embed(
        title="✅ Goodbye Channel Set",
        description=f"Goodbye channel has been set to {channel.mention}",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def togglegoodbye_command(interaction: discord.Interaction):
    """Toggle goodbye messages on/off"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can toggle goodbye messages.", ephemeral=True)
        return
    
    config = load_welcome_config()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in config:
        config[guild_id] = {}
    
    current_state = config[guild_id].get("goodbye_enabled", False)
    config[guild_id]["goodbye_enabled"] = not current_state
    save_welcome_config(config)
    
    status = "enabled" if config[guild_id]["goodbye_enabled"] else "disabled"
    embed = create_embed(
        title="✅ Goodbye Messages Toggled",
        description=f"Goodbye messages are now **{status}**",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def welcomeconfig_command(interaction: discord.Interaction):
    """Show current welcome configuration"""
    config = load_welcome_config()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in config:
        embed = create_embed(
            title="⚙️ Welcome Configuration",
            description="Welcome system is not configured for this server.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    guild_config = config[guild_id]
    
    embed = create_embed(
        title="⚙️ Welcome Configuration",
        description="Current welcome system settings:",
        color=discord.Color.blue(),
        fields=[
            ("Welcome Enabled", "✅ Yes" if guild_config.get("enabled", False) else "❌ No", True),
            ("Welcome Channel", f"<#{guild_config.get('channel_id')}>" if guild_config.get("channel_id") else "Not set", True),
            ("Goodbye Enabled", "✅ Yes" if guild_config.get("goodbye_enabled", False) else "❌ No", True),
            ("Goodbye Channel", f"<#{guild_config.get('goodbye_channel_id')}>" if guild_config.get("goodbye_channel_id") else "Not set", True),
            ("Welcome Message", guild_config.get("message", "Not set")[:100] + "..." if len(guild_config.get("message", "")) > 100 else guild_config.get("message", "Not set"), False),
            ("Goodbye Message", guild_config.get("goodbye_message", "Not set")[:100] + "..." if len(guild_config.get("goodbye_message", "")) > 100 else guild_config.get("goodbye_message", "Not set"), False)
        ]
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
