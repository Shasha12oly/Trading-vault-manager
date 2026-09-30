"""
Professional Store System - Price lists and store management
"""
import discord
from discord import app_commands
from config import SUPPORT_ROLE_ID
from embed_utils import create_embed


# Store data storage
STORE_CONFIG_FILE = "store_config.json"

# Thumbnail URL for all store embeds
STORE_THUMBNAIL_URL = "https://cdn.discordapp.com/attachments/1552924354902368276/1553365915263967282/Gemini_Generated_Image_tapx94tapx94tapx.png?ex=6abaf67e&is=6ab9a4fe&hm=d7b0862c65057e2492f2f19f1a5f14b7b06a9564a8dce734c1204ba16182fb34"

import json
import os


def load_store_config():
    if os.path.exists(STORE_CONFIG_FILE):
        with open(STORE_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_store_config(config):
    with open(STORE_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


# Load store configuration
STORE_CONFIG = load_store_config()


# Sample cape data (can be customized)
DEFAULT_CAPE_STORE_DATA = {
    "items": [
        {"name": "Builder Cape Code", "emoji": "🪵", "inr": 40, "usd": 0.40, "image": ""},
        {"name": "Home Cape Code", "emoji": "🏡", "inr": 55, "usd": 0.55, "image": ""},
        {"name": "Copper Cape Code", "emoji": "🧱", "inr": 69, "usd": 0.69, "image": ""},
        {"name": "Menace Cape Code", "emoji": "😈", "inr": 105, "usd": 1.05, "image": ""},
        {"name": "Purple Heart Cape", "emoji": "💜", "inr": 750, "usd": 7.50, "image": ""},
        {"name": "Moonlight Cape", "emoji": "🌙", "inr": 6500, "usd": 65.00, "image": ""},
        {"name": "Experience Cape", "emoji": "🧪", "inr": 3800, "usd": 38.00, "image": ""},
        {"name": "Followers Cape", "emoji": "👾", "inr": 19900, "usd": 199.00, "image": ""},
    ],
    "conversion_rate": "1$ = 100 Rs (Conversion Charge)",
    "store_name": "Trading Vault Capes",
    "description": "Premium Minecraft Capes at Best Prices"
}

# Load cape data from store config
def load_cape_data():
    config = load_store_config()
    if "capes" in config:
        return config["capes"]
    else:
        return DEFAULT_CAPE_STORE_DATA

CAPE_STORE_DATA = load_cape_data()

# Load decoration data from store config
def load_decoration_data():
    config = load_store_config()
    if "decoration" in config:
        return config["decoration"]
    else:
        return {
            "items": [],
            "conversion_rate": "Via Gift • Affordable Prices",
            "store_name": "Trading Vault Discord Decorations",
            "description": "Avatar Decorations, Nameplates, Profile Effects"
        }

DECORATION_STORE_DATA = load_decoration_data()

# Load boosts data from store config
def load_boosts_data():
    config = load_store_config()
    if "boosts" in config:
        return config["boosts"]
    else:
        return {
            "items": [],
            "conversion_rate": "₹100 = $1 USD",
            "store_name": "Trading Vault Server Boosts",
            "description": "High-quality Discord Server Boosts at affordable prices"
        }

BOOSTS_STORE_DATA = load_boosts_data()

# Load nitro data from store config
def load_nitro_data():
    config = load_store_config()
    if "nitro" in config:
        return config["nitro"]
    else:
        return {
            "items": [],
            "conversion_rate": "Full Access • Fast Delivery",
            "store_name": "Trading Vault Discord Nitro",
            "description": "High-quality Discord Nitros at affordable prices"
        }

NITRO_STORE_DATA = load_nitro_data()

# Load minecraft data from store config
def load_minecraft_data():
    config = load_store_config()
    if "minecraft" in config:
        return config["minecraft"]
    else:
        return {
            "items": [],
            "conversion_rate": "Full Access • Secure Delivery",
            "store_name": "Trading Vault MC Accounts & Codes",
            "description": "Minecraft access and official items",
            "account_features": []
        }

MINECRAFT_STORE_DATA = load_minecraft_data()


def create_nitro_embed(store_data: dict, banner_config: dict = None, banner_url: str = None) -> discord.Embed:
    """Create the exact nitro embed format requested by user"""
    
    # Load store config for additional settings
    config = load_store_config()
    
    # Create the nitro embed description in the exact format requested
    description = f" Looking to level up your Discord Profile? We now offer high-quality Discord Nitros at affordable prices!\n"
    description += f"━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    description += f"🔮Nitro ID\n\n"
    
    # Add items
    for item in store_data["items"]:
        name = item["name"]
        emoji = item["emoji"]
        inr_price = item["inr"]
        usd_price = item["usd"]
        
        description += f"☄️ {name}\n"
        description += f"☄️ Fa\n"
        description += f"☄️ Price - ₹{inr_price}/${usd_price:.2f}\n\n"
    
    description += f"━━━━━━━━━━━━━━━━━━━━━\n"
    description += f"✨ Why Choose Us?\n"
    
    # Use the exact why choose text for nitro (without Via Gift)
    description += f"✅ Fast Delivery\n"
    description += f"✅ Affordable Prices\n"
    description += f"✅ Trusted Service\n"
    description += f"✅ Friendly Support\n"
    description += f"✅ Secure Transactions\n"
    
    description += f"━━━━━━━━━━━━━━━━━━━━━\n"
    
    # Add call to action (as requested)
    description += f"📩 Ready to order? Open a <#1552991700543340604> and our team will assist you as quickly as possible.\n\n"
    
    # Add footer (hardcoded purple heart for nitro)
    description += f"💜 Thank you for choosing Trading Vault!"
    
    # Create the embed
    embed = discord.Embed(
        title="🎉 Discord Nitro ID Now Available!",
        description=description,
        color=discord.Color.from_rgb(0, 255, 255)  # Aqua #00FFFF
    )
    
    # Add thumbnail
    embed.set_thumbnail(url=STORE_THUMBNAIL_URL)
    
    # Add banner if provided
    if banner_url and banner_config.get("banner_enabled", True):
        embed.set_image(url=banner_url)
    
    # Add footer
    embed.set_footer(text="Made by Shashank Sharma")
    
    return embed


def create_decoration_embed(store_data: dict, banner_config: dict = None, banner_url: str = None) -> discord.Embed:
    """Create the exact decoration embed format requested by user"""
    
    # Load store config for additional settings
    config = load_store_config()
    
    # Create the decoration embed description in the exact format requested
    description = f"━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Add items
    for item in store_data["items"]:
        emoji = item["emoji"]
        discord_price = item.get("discord_price", "")
        inr_price = item["inr"]
        usd_price = item["usd"]
        
        description += f"{emoji} {discord_price} in Discord Store ➔ {inr_price} INR / ${usd_price:.2f} USD\n"
    
    description += f"\n━━━━━━━━━━━━━━━━━━━━━\n"
    description += f"✨ Why Choose Us?\n"
    
    # Use the exact why choose text for decoration (includes Via Gift)
    description += f"✅ Fast Delivery\n"
    description += f"✅ Via Gift\n"
    description += f"✅ Affordable Prices\n"
    description += f"✅ Trusted Service\n"
    description += f"✅ Friendly Support\n"
    description += f"✅ Secure Transactions\n"
    
    description += f"━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Add call to action (as requested - with envelope emoji)
    description += f"📩 Ready to order? Open a <#1552991700543340604> and our team will assist you as quickly as possible.\n\n"
    
    # Add footer (hardcoded purple heart for decoration)
    description += f"💜 Thank you for choosing Trading Vault!"
    
    # Create the embed
    embed = discord.Embed(
        title="💜 AVATAR DECORATION / NAMEPLATE / PROFILE EFFECTS",
        description=description,
        color=discord.Color.from_rgb(0, 255, 255)  # Aqua color
    )
    
    # Add thumbnail
    embed.set_thumbnail(url=STORE_THUMBNAIL_URL)
    
    # Add banner if provided
    if banner_url and banner_config.get("banner_enabled", True):
        embed.set_image(url=banner_url)
    
    # Add footer
    embed.set_footer(text="Made by Shashank Sharma")
    
    return embed


def create_boosts_embed(store_data: dict, banner_config: dict = None, banner_url: str = None) -> discord.Embed:
    """Create the exact boosts embed format requested by user"""
    
    # Load store config for additional settings
    config = load_store_config()
    
    # Create the boosts embed description in the exact format requested
    description = f"💎 Looking to level up your Discord server? We now offer high-quality Discord Server Boosts at affordable prices!\n"
    description += f"━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    description += f"💜 Boost Packages (at ₹100 = $1 USD)\n\n"
    
    # Add items
    for item in store_data["items"]:
        name = item["name"]
        emoji = item["emoji"]
        inr_price = item["inr"]
        usd_price = item["usd"]
        
        description += f"🚀 {name} - ₹{inr_price}/{usd_price:.2f}$\n"
    
    description += f"\n━━━━━━━━━━━━━━━━━━━━━\n"
    description += f"✨ Why Choose Us?\n"
    
    # Use the exact why choose text for boosts (with emojis)
    description += f"✅ Fast Delivery\n"
    description += f"✅ Affordable Prices\n"
    description += f"✅ Trusted Service\n"
    description += f"✅ Friendly Support\n"
    description += f"✅ Secure Transactions\n"
    
    description += f"━━━━━━━━━━━━━━━━━━━━━\n"
    
    # Add call to action (as requested - with envelope emoji)
    description += f"📩 Ready to order? Open a <#1552991700543340604> and our team will assist you as quickly as possible.\n\n"
    
    # Add footer (as requested - with purple heart emoji)
    description += f"💜 Thank you for choosing Trading Vault!"
    
    # Create the embed
    embed = discord.Embed(
        title="🚀 Discord Server Boosts Now Available!",
        description=description,
        color=discord.Color.from_rgb(0, 255, 255)  # Aqua color
    )
    
    # Add thumbnail
    embed.set_thumbnail(url=STORE_THUMBNAIL_URL)
    
    # Add banner if provided
    if banner_url and banner_config.get("banner_enabled", True):
        embed.set_image(url=banner_url)
    
    # Add footer
    embed.set_footer(text="Made by Shashank Sharma")
    
    return embed


def create_price_list_embed(store_data: dict, store_name: str = "Capes Store", banner_config: dict = None, banner_url: str = None) -> discord.Embed:
    """Create a professional price list embed with optional banner config"""
    
    # Load store config for additional settings
    config = load_store_config()
    
    # Use banner config if provided, otherwise use default
    if banner_config is None:
        banner_config = {
            "title": "💳 PRICE LIST",
            "show_why_choose": True,
            "show_conversion_rate": True,
            "banner_enabled": True
        }
    
    # Create the price list text
    price_list = ""
    mcfa_items = []
    
    for item in store_data["items"]:
        name = item["name"]
        emoji = item["emoji"]
        inr_price = item["inr"]
        usd_price = item["usd"]
        
        # Handle section headers
        if item.get("is_section_header"):
            price_list += f"\n**{emoji} {name}**\n\n"
            continue
        
        # Handle decoration items differently (they have discord_price)
        if "discord_price" in item:
            price_list += f"{emoji} {item['discord_price']} in Discord Store ➔ {emoji} INR: ₹{inr_price} / USD: ${usd_price:.2f}\n"
        # Handle minecraft items with MCFA section
        elif item.get("section") == "mcfa":
            mcfa_items.append(item)
        # Handle minecraft items (they have bulk_discount)
        elif "bulk_discount" in item:
            price_list += f"{emoji} {name}\n"
            price_list += f"USD - ${usd_price:.2f}\n"
            price_list += f"INR - ₹{inr_price}rs\n\n"
            if item.get("bulk_discount"):
                price_list += f"{item['bulk_discount']}\n\n"
        # Handle boosts and nitro (simpler format)
        elif store_name == "Trading Vault Server Boosts" or store_name == "Trading Vault Discord Nitro":
            price_list += f"{emoji} {name}\n"
            price_list += f"Price - ₹{inr_price}/${usd_price:.2f}\n\n"
        # Standard cape format
        else:
            price_list += f"{emoji} {name.upper()}\n"
            price_list += f"├ INR: ₹{inr_price}\n"
            price_list += f"└ USD: ${usd_price:.2f}\n\n"
    
    # Add MCFA items section after the header
    if mcfa_items:
        for item in mcfa_items:
            name = item["name"]
            emoji = item["emoji"]
            inr_price = item["inr"]
            usd_price = item["usd"]
            
            price_list += f"{emoji} {name}\n"
            price_list += f"USD - ${usd_price:.2f}\n"
            price_list += f"INR - ₹{inr_price}rs\n\n"
        
        # Add bulk message once at the end for MCFA items
        if store_data.get("mcfa_bulk_message"):
            price_list += f"{store_data['mcfa_bulk_message']}\n\n"
    
    # Create the embed
    embed = create_embed(
        title=banner_config.get("title", "💳 PRICE LIST"),
        description=price_list,
        color=discord.Color.from_rgb(0, 255, 255),  # Aqua #00FFFF
        message_type="general",
        show_banner=False  # We'll handle banner manually
    )
    
    # Add thumbnail
    embed.set_thumbnail(url=STORE_THUMBNAIL_URL)
    
    # Add store-specific banner if provided
    if banner_url and banner_config.get("banner_enabled", True):
        embed.set_image(url=banner_url)
    
    # Add why choose section if enabled
    if banner_config.get("show_why_choose", True):
        why_choose = config.get("why_choose_text", """╭─── 👑 WHY CHOOSE TRADING VAULT? ───╮
│  ⚡ Instant & Automated Delivery
│  💎 100% Legit & Tested Codes
│  🛡️ Fully Safe & Secure Deals
│  💬 24/7 Active Staff Support
╰─────────────────────────────────────╯""")
        embed.add_field(name="✨ Why Choose Us?", value=why_choose, inline=False)
    
    # Add call to action
    cta = config.get("call_to_action", "🛒 Ready to order? Open a <#1552991700543340604> and our team will assist you as quickly as possible.")
    embed.add_field(name="� How to Purchase", value=cta, inline=False)
    
    # Add conversion rate if enabled
    if banner_config.get("show_conversion_rate", True):
        embed.add_field(name="💱 Payment Info", value=store_data.get("conversion_rate", "1$ = 100 Rs"), inline=False)
    
    # Add account features for minecraft if enabled
    if banner_config.get("show_account_features", False) and "account_features" in store_data:
        features_text = "\n".join(store_data["account_features"])
        embed.add_field(name="🔐 Full Access Gives You:", value=features_text, inline=False)
    
    # Add custom footer
    footer_text = config.get("footer_text", "✨ Thank you for choosing Trading Vault!")
    embed.set_footer(text=footer_text)
    
    return embed


def create_cape_card_embed(item: dict, store_data: dict) -> discord.Embed:
    """Create an individual cape card with image"""
    
    name = item["name"]
    emoji = item["emoji"]
    inr_price = item["inr"]
    usd_price = item["usd"]
    image_url = item.get("image", "")
    
    # Create pricing text
    pricing = f"├ INR: ₹{inr_price}\n└ USD: ${usd_price:.2f}"
    
    # Create the embed (no banner for individual cape cards)
    embed = create_embed(
        title=f"{emoji} {name.upper()}",
        description=pricing,
        color=discord.Color.from_rgb(0, 255, 255),  # Aqua #00FFFF
        message_type="general",
        show_banner=False
    )
    
    # Add thumbnail
    embed.set_thumbnail(url=STORE_THUMBNAIL_URL)
    
    # Add cape image if available
    if image_url:
        embed.set_image(url=image_url)
    
    # Add purchase info
    embed.add_field(
        name="🛒 How to Purchase",
        value="Open a ticket in <#1552991700543340604> to buy this cape!",
        inline=False
    )
    
    embed.set_footer(text="✨ Trading Vault — Premium Minecraft Capes")
    
    return embed


async def post_cape_cards(interaction: discord.Interaction, channel: discord.TextChannel):
    """Post individual cape cards with images to a channel"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can post to store channels.", ephemeral=True)
        return
    
    # Reload store config to get latest data
    global CAPE_STORE_DATA, STORE_CONFIG
    STORE_CONFIG = load_store_config()
    CAPE_STORE_DATA = load_cape_data()
    store_data = CAPE_STORE_DATA
    
    # Clear old messages (optional - keep last 20 messages)
    try:
        async for message in channel.history(limit=20):
            if message.author == interaction.client.user:
                await message.delete()
    except Exception as e:
        print(f"Error clearing old messages: {e}")
    
    # Post individual cape cards
    for item in store_data["items"]:
        embed = create_cape_card_embed(item, store_data)
        await channel.send(embed=embed)
    
    # Post the footer info with configurable banner
    cape_footer_config = STORE_CONFIG.get("banner_configs", {}).get("capes_footer", {
        "title": "💳 STORE INFORMATION",
        "show_why_choose": True,
        "show_conversion_rate": True,
        "banner_enabled": True
    })
    
    # Get cape-specific banner URL if available
    cape_banner_url = store_data.get("banner_url")
    
    footer_embed = create_embed(
        title=cape_footer_config.get("title", "💳 STORE INFORMATION"),
        description="Store information and payment details",
        color=discord.Color.from_rgb(0, 255, 255),  # Aqua #00FFFF
        message_type="general",
        show_banner=False  # We'll handle banner manually
    )
    
    # Add thumbnail
    footer_embed.set_thumbnail(url=STORE_THUMBNAIL_URL)
    
    # Add cape-specific banner if available and enabled
    if cape_banner_url and cape_footer_config.get("banner_enabled", True):
        footer_embed.set_image(url=cape_banner_url)
    
    # Add why choose section if enabled
    if cape_footer_config.get("show_why_choose", True):
        why_choose = STORE_CONFIG.get("why_choose_text", """╭─── 👑 WHY CHOOSE TRADING VAULT? ───╮
│  ⚡ Instant & Automated Delivery
│  💎 100% Legit & Tested Codes
│  🛡️ Fully Safe & Secure Deals
│  💬 24/7 Active Staff Support
╰─────────────────────────────────────╯""")
        footer_embed.add_field(name="👑 WHY CHOOSE TRADING VAULT?", value=why_choose, inline=False)
    
    # Add conversion rate if enabled
    if cape_footer_config.get("show_conversion_rate", True):
        footer_embed.add_field(name="💱 Conversion Rate", value=store_data.get("conversion_rate", "1$ = 100 Rs"), inline=False)
    
    # Add call to action
    cta = STORE_CONFIG.get("call_to_action", "🛒 Ready to order? Open a <#1552991700543340604> and our team will assist you as quickly as possible.")
    footer_embed.add_field(name="🛒 How to Purchase", value=cta, inline=False)
    
    # Add custom footer
    footer_text = STORE_CONFIG.get("footer_text", "✨ Thank you for choosing Trading Vault — Your #1 Minecraft Market!")
    footer_embed.set_footer(text=footer_text)
    
    await channel.send(embed=footer_embed)
    
    await interaction.response.send_message(f"Cape cards posted to {channel.mention}!", ephemeral=True)


async def post_price_list(interaction: discord.Interaction, channel: discord.TextChannel, store_type: str = "capes"):
    """Post price list to a store channel"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can post to store channels.", ephemeral=True)
        return
    
    # Load store data based on type
    if store_type == "capes":
        store_data = CAPE_STORE_DATA
        banner_config = STORE_CONFIG.get("banner_configs", {}).get("capes_style_1")
        banner_url = store_data.get("banner_url")
    elif store_type == "decoration":
        store_data = DECORATION_STORE_DATA
        banner_config = STORE_CONFIG.get("banner_configs", {}).get("decoration_style_1")
        banner_url = store_data.get("banner_url")
    elif store_type == "boosts":
        store_data = BOOSTS_STORE_DATA
        banner_config = STORE_CONFIG.get("banner_configs", {}).get("boosts_style_1")
        banner_url = store_data.get("banner_url")
    elif store_type == "nitro":
        store_data = NITRO_STORE_DATA
        banner_config = STORE_CONFIG.get("banner_configs", {}).get("nitro_style_1")
        banner_url = store_data.get("banner_url")
    elif store_type == "minecraft":
        store_data = MINECRAFT_STORE_DATA
        banner_config = STORE_CONFIG.get("banner_configs", {}).get("minecraft_style_1")
        banner_url = store_data.get("banner_url")
    else:
        # Load from file if exists
        config = load_store_config()
        if store_type in config:
            store_data = config[store_type]
            banner_config = None
            banner_url = store_data.get("banner_url")
        else:
            await interaction.response.send_message(f"Store data for '{store_type}' not found.", ephemeral=True)
            return
    
    # Special handling for nitro - use custom embed format
    if store_type == "nitro":
        try:
            nitro_embed = create_nitro_embed(store_data, banner_config, banner_url)
            await channel.send(embed=nitro_embed)
            await interaction.response.send_message(f"Nitro shop embed posted to {channel.mention}!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error posting nitro embed: {str(e)}", ephemeral=True)
        return
    
    # Special handling for decoration - use custom embed format
    if store_type == "decoration":
        try:
            decoration_embed = create_decoration_embed(store_data, banner_config, banner_url)
            await channel.send(embed=decoration_embed)
            await interaction.response.send_message(f"Decoration shop embed posted to {channel.mention}!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error posting decoration embed: {str(e)}", ephemeral=True)
        return
    
    # Special handling for boosts - use custom embed format
    if store_type == "boosts":
        try:
            boosts_embed = create_boosts_embed(store_data, banner_config, banner_url)
            await channel.send(embed=boosts_embed)
            await interaction.response.send_message(f"Boosts shop embed posted to {channel.mention}!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error posting boosts embed: {str(e)}", ephemeral=True)
        return
    
    # Create and send the embed for other store types
    store_name = store_data.get("store_name", f"{store_type.capitalize()} Store")
    embed = create_price_list_embed(store_data, store_name, banner_config, banner_url)
    
    try:
        await channel.send(embed=embed)
        await interaction.response.send_message(f"Price list posted to {channel.mention}!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error posting price list: {str(e)}", ephemeral=True)


async def setstorechannel_command(interaction: discord.Interaction, channel: discord.TextChannel, store_type: str):
    """Set a store channel for a specific store type"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can set store channels.", ephemeral=True)
        return
    
    config = load_store_config()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in config:
        config[guild_id] = {}
    
    config[guild_id][f"{store_type}_channel"] = channel.id
    save_store_config(config)
    
    embed = create_embed(
        title="✅ Store Channel Set",
        description=f"{store_type.capitalize()} store channel has been set to {channel.mention}",
        color=discord.Color.from_rgb(0, 255, 255)  # Aqua #00FFFF
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def updatepricelist_command(interaction: discord.Interaction, store_type: str = "capes"):
    """Update and repost price list to the configured store channel"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can update price lists.", ephemeral=True)
        return
    
    config = load_store_config()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in config or f"{store_type}_channel" not in config[guild_id]:
        await interaction.response.send_message(f"{store_type.capitalize()} store channel not configured. Use /setstorechannel first.", ephemeral=True)
        return
    
    channel_id = config[guild_id][f"{store_type}_channel"]
    channel = interaction.guild.get_channel(channel_id)
    
    if not channel:
        await interaction.response.send_message("Store channel not found.", ephemeral=True)
        return
    
    # Load store data and banner config
    if store_type == "capes":
        store_data = CAPE_STORE_DATA
        banner_config = config.get("banner_configs", {}).get("capes_style_1")
        banner_url = store_data.get("banner_url")
    elif store_type == "decoration":
        store_data = DECORATION_STORE_DATA
        banner_config = config.get("banner_configs", {}).get("decoration_style_1")
        banner_url = store_data.get("banner_url")
    elif store_type == "boosts":
        store_data = BOOSTS_STORE_DATA
        banner_config = config.get("banner_configs", {}).get("boosts_style_1")
        banner_url = store_data.get("banner_url")
    elif store_type == "nitro":
        store_data = NITRO_STORE_DATA
        banner_config = config.get("banner_configs", {}).get("nitro_style_1")
        banner_url = store_data.get("banner_url")
    elif store_type == "minecraft":
        store_data = MINECRAFT_STORE_DATA
        banner_config = config.get("banner_configs", {}).get("minecraft_style_1")
        banner_url = store_data.get("banner_url")
    else:
        config = load_store_config()
        if store_type in config:
            store_data = config[store_type]
            banner_config = None
            banner_url = store_data.get("banner_url")
        else:
            await interaction.response.send_message(f"Store data for '{store_type}' not found.", ephemeral=True)
            return
    
    # Special handling for nitro - use custom embed format
    if store_type == "nitro":
        try:
            # Clear old messages (optional - keep last 10 messages)
            async for message in channel.history(limit=10):
                if message.author == interaction.client.user:
                    await message.delete()
            
            nitro_embed = create_nitro_embed(store_data, banner_config, banner_url)
            await channel.send(embed=nitro_embed)
            await interaction.response.send_message(f"Nitro shop embed updated in {channel.mention}!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error updating nitro embed: {str(e)}", ephemeral=True)
        return
    
    # Special handling for decoration - use custom embed format
    if store_type == "decoration":
        try:
            # Clear old messages (optional - keep last 10 messages)
            async for message in channel.history(limit=10):
                if message.author == interaction.client.user:
                    await message.delete()
            
            decoration_embed = create_decoration_embed(store_data, banner_config, banner_url)
            await channel.send(embed=decoration_embed)
            await interaction.response.send_message(f"Decoration shop embed updated in {channel.mention}!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error updating decoration embed: {str(e)}", ephemeral=True)
        return
    
    # Special handling for boosts - use custom embed format
    if store_type == "boosts":
        try:
            # Clear old messages (optional - keep last 10 messages)
            async for message in channel.history(limit=10):
                if message.author == interaction.client.user:
                    await message.delete()
            
            boosts_embed = create_boosts_embed(store_data, banner_config, banner_url)
            await channel.send(embed=boosts_embed)
            await interaction.response.send_message(f"Boosts shop embed updated in {channel.mention}!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error updating boosts embed: {str(e)}", ephemeral=True)
        return
    
    # Create and send the embed for other store types
    store_name = store_data.get("store_name", f"{store_type.capitalize()} Store")
    embed = create_price_list_embed(store_data, store_name, banner_config, banner_url)
    
    try:
        # Clear old messages (optional - keep last 10 messages)
        async for message in channel.history(limit=10):
            if message.author == interaction.client.user:
                await message.delete()
        
        await channel.send(embed=embed)
        await interaction.response.send_message(f"Price list updated in {channel.mention}!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error updating price list: {str(e)}", ephemeral=True)


async def storeinfo_command(interaction: discord.Interaction):
    """Show store configuration information"""
    config = load_store_config()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in config:
        embed = create_embed(
            title="🏪 Store Configuration",
            description="No store channels configured yet.",
            color=discord.Color.from_rgb(0, 255, 255)  # Aqua #00FFFF
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    guild_config = config[guild_id]
    
    description = "Configured store channels:\n\n"
    for key, channel_id in guild_config.items():
        channel = interaction.guild.get_channel(channel_id)
        if channel:
            description += f"**{key.replace('_', ' ').title()}:** {channel.mention}\n"
        else:
            description += f"**{key.replace('_', ' ').title()}:** Invalid channel\n"
    
    embed = create_embed(
        title="🏪 Store Configuration",
        description=description,
        color=discord.Color.from_rgb(0, 255, 255)  # Aqua #00FFFF
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def setcapeimage_command(interaction: discord.Interaction, cape_name: str, image_url: str):
    """Set image URL for a specific cape"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can set cape images.", ephemeral=True)
        return
    
    # Load current store config
    global CAPE_STORE_DATA, STORE_CONFIG
    STORE_CONFIG = load_store_config()
    cape_data = STORE_CONFIG.get("capes", DEFAULT_CAPE_STORE_DATA)
    
    # Find the cape in the data
    cape_found = False
    for item in cape_data["items"]:
        if item["name"].lower() == cape_name.lower():
            item["image"] = image_url
            cape_found = True
            break
    
    if not cape_found:
        available_capes = ", ".join([item["name"] for item in cape_data["items"]])
        await interaction.response.send_message(
            f"Cape '{cape_name}' not found. Available capes: {available_capes}", 
            ephemeral=True
        )
        return
    
    # Save to config file
    STORE_CONFIG["capes"] = cape_data
    save_store_config(STORE_CONFIG)
    
    # Update global variable
    CAPE_STORE_DATA = cape_data
    
    embed = create_embed(
        title="✅ Cape Image Set",
        description=f"Image for '{cape_name}' has been set successfully!",
        color=discord.Color.from_rgb(0, 255, 255)  # Aqua #00FFFF
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def reloadstoreconfig_command(interaction: discord.Interaction):
    """Reload store configuration from file"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can reload store configuration.", ephemeral=True)
        return
    
    # Reload all store data
    global CAPE_STORE_DATA, DECORATION_STORE_DATA, BOOSTS_STORE_DATA, NITRO_STORE_DATA, MINECRAFT_STORE_DATA, STORE_CONFIG
    STORE_CONFIG = load_store_config()
    CAPE_STORE_DATA = load_cape_data()
    DECORATION_STORE_DATA = load_decoration_data()
    BOOSTS_STORE_DATA = load_boosts_data()
    NITRO_STORE_DATA = load_nitro_data()
    MINECRAFT_STORE_DATA = load_minecraft_data()
    
    embed = create_embed(
        title="✅ Store Configuration Reloaded",
        description="All store data has been reloaded from store_config.json",
        color=discord.Color.from_rgb(0, 255, 255)  # Aqua #00FFFF
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def setstorebanner_command(interaction: discord.Interaction, store_type: str, banner_url: str):
    """Set banner image URL for a specific store type"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can set store banners.", ephemeral=True)
        return
    
    # Validate store type
    valid_store_types = ["capes", "decoration", "boosts", "nitro", "minecraft"]
    if store_type not in valid_store_types:
        await interaction.response.send_message(
            f"Invalid store type. Valid types: {', '.join(valid_store_types)}",
            ephemeral=True
        )
        return
    
    # Load current store config
    config = load_store_config()
    
    # Set banner URL for the specified store type
    if store_type in config:
        config[store_type]["banner_url"] = banner_url
    else:
        await interaction.response.send_message(f"Store data for '{store_type}' not found in config.", ephemeral=True)
        return
    
    # Save to config file
    save_store_config(config)
    
    # Reload the specific store data
    global CAPE_STORE_DATA, DECORATION_STORE_DATA, BOOSTS_STORE_DATA, NITRO_STORE_DATA, MINECRAFT_STORE_DATA, STORE_CONFIG
    STORE_CONFIG = config
    
    if store_type == "capes":
        CAPE_STORE_DATA = load_cape_data()
    elif store_type == "decoration":
        DECORATION_STORE_DATA = load_decoration_data()
    elif store_type == "boosts":
        BOOSTS_STORE_DATA = load_boosts_data()
    elif store_type == "nitro":
        NITRO_STORE_DATA = load_nitro_data()
    elif store_type == "minecraft":
        MINECRAFT_STORE_DATA = load_minecraft_data()
    
    embed = create_embed(
        title="✅ Store Banner Set",
        description=f"Banner image for **{store_type.capitalize()}** store has been set successfully!",
        color=discord.Color.from_rgb(0, 255, 255),  # Aqua #00FFFF
        fields=[
            ("Store Type", store_type.capitalize(), True),
            ("Banner URL", banner_url[:50] + "..." if len(banner_url) > 50 else banner_url, False)
        ]
    )
    embed.set_image(url=banner_url)
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def getstorebanner_command(interaction: discord.Interaction, store_type: str = None):
    """View current banner settings for stores"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can view store banner settings.", ephemeral=True)
        return
    
    config = load_store_config()
    
    if store_type:
        # Show specific store banner
        valid_store_types = ["capes", "decoration", "boosts", "nitro", "minecraft"]
        if store_type not in valid_store_types:
            await interaction.response.send_message(
                f"Invalid store type. Valid types: {', '.join(valid_store_types)}",
                ephemeral=True
            )
            return
        
        if store_type in config:
            banner_url = config[store_type].get("banner_url", "Not set")
            store_name = config[store_type].get("store_name", store_type.capitalize())
            
            embed = create_embed(
                title=f"🖼️ {store_name} Banner",
                description=f"Current banner settings for **{store_type.capitalize()}** store:",
                color=discord.Color.from_rgb(0, 255, 255),  # Aqua #00FFFF
                fields=[
                    ("Banner URL", banner_url[:50] + "..." if len(banner_url) > 50 else banner_url, False)
                ]
            )
            
            if banner_url and banner_url != "Not set":
                embed.set_image(url=banner_url)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(f"Store data for '{store_type}' not found.", ephemeral=True)
    else:
        # Show all store banners
        description = ""
        valid_store_types = ["capes", "decoration", "boosts", "nitro", "minecraft"]
        
        for store in valid_store_types:
            if store in config:
                banner_url = config[store].get("banner_url", "Not set")
                status = "✅ Set" if banner_url and banner_url != "Not set" else "❌ Not set"
                description += f"**{store.capitalize()}:** {status}\n"
                if banner_url and banner_url != "Not set":
                    description += f"   URL: {banner_url[:40]}...\n\n"
                else:
                    description += "\n"
        
        embed = create_embed(
            title="🖼️ All Store Banners",
            description=description or "No store data found.",
            color=discord.Color.from_rgb(0, 255, 255)  # Aqua #00FFFF
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)