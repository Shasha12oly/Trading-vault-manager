"""
Professional Discord Bot (discord.py 2.x)

Features:
- Support Ticket System (General Support, Account Issue)
- Purchase Ticket System (Capes, Minecraft Accounts, Discord Nitro, Boosts, Discord Decoration)
- Giveaway System (Host giveaways with multiple winners)
- Invite Tracker (Track who invited whom)
- Welcomer System (Welcome/goodbye messages)
- Priority system (Low, Medium, High)
- Close confirmation dialog
- Reopen closed tickets
- User DM notifications
- Professional embed styling
- Transcript logging

Setup:
  pip install -U discord.py python-dotenv
  Copy .env.example to .env and fill in your values
  Run: python ticket_bot.py
  Then, in your server, run /ticketpanel for support or /purchasepanel for purchases.
"""
import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timezone
import io
import asyncio

# Import configuration
from config import (
    TOKEN, SUPPORT_ROLE_ID, CATEGORY_ID, LOG_CHANNEL_ID, SYNC_GUILD_ID,
    RATING_CHANNEL_ID, VOUCH_CHANNEL_ID, THUMBNAIL_URL, BANNER_URL,
    INR_QR_URL, LTC_QR_URL, INR_WALLET_ADDRESS, LTC_WALLET_ADDRESS,
    BANNER_SETTINGS, update_env_var, ENABLE_GIVEAWAYS, ENABLE_INVITE_TRACKER, ENABLE_WELCOMER,
    toggle_banner_setting, set_banner_setting, INVITE_ANNOUNCEMENT_CHANNEL_ID
)

# Import utilities
from embed_utils import create_embed
from ticket_utils import owner_tag, get_ticket_info

# Import systems
from support_system import OpenTicketView
from purchase_system import PurchaseView
from ticket_controls import SupportTicketControlView, PurchaseTicketControlView, ConfirmCloseView
from payment_system import PaymentMethodView
from rating_system import RatingView
from vouch_system import load_vouches, save_vouches, process_vouch_message, get_vouch_info, get_leaderboard, generate_vouch_request
from ticket_close import close_ticket_final
from ticket_management import create_ticket
from giveaway_system import giveaway_command, endgiveaway_command, reroll_command, check_giveaways, listgiveaways_command
from invite_tracker import track_invites, check_invite_join, check_invite_leave, invitestats_command, inviteleaderboard_command, whoinvited_command, setinvitechannel_command
from welcomer_system import send_welcome, send_goodbye, setwelcomemessage_command, setwelcomerchannel_command, togglewelcome_command, setgoodbyemessage_command, setgoodbyechannel_command, togglegoodbye_command, welcomeconfig_command, togglestyledwelcome_command, setwelcomeimage_command, setthumbnailimage_command

intents = discord.Intents.default()
intents.message_content = True  # Required for ! commands
intents.members = True
intents.invites = True  # Required for invite tracking


class TicketBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(OpenTicketView())
        self.add_view(PurchaseView())
        self.add_view(ConfirmCloseView())
        self.add_view(PaymentMethodView())
        self.add_view(RatingView())
        self.add_view(SupportTicketControlView())
        self.add_view(PurchaseTicketControlView())
        
        # Start giveaway checker task if enabled
        if ENABLE_GIVEAWAYS:
            self.giveaway_checker.start()
        
        # Sync commands globally or to specific guild for faster updates
        if SYNC_GUILD_ID:
            self.tree.copy_global_to(guild=discord.Object(SYNC_GUILD_ID))
            await self.tree.sync(guild=discord.Object(SYNC_GUILD_ID))
        else:
            await self.tree.sync()


bot = TicketBot()


# Giveaway checker task
@tasks.loop(minutes=1)
async def giveaway_checker():
    """Check for ended giveaways every minute"""
    await check_giveaways(bot)


@giveaway_checker.before_loop
async def before_giveaway_checker():
    """Wait for bot to be ready before starting task"""
    await bot.wait_until_ready()


# Attach the task to the bot instance
TicketBot.giveaway_checker = giveaway_checker


# ============ BOT COMMANDS ============

@bot.tree.command(name="ticketpanel", description="Post the support ticket panel in this channel")
@app_commands.default_permissions(administrator=True)
async def ticketpanel(interaction: discord.Interaction):
    embed = create_embed(
        title="🎫 Support Ticket System",
        description="Welcome to our support system! Please select a category below to open a ticket.\n\nOur team will respond as soon as possible.",
        color=discord.Color.from_rgb(88, 101, 242),
        message_type="panel",
        fields=[
            ("Available Categories", "• 📧 General Support\n• 🎁 Claim Giveaway\n• 📖 Enquiry", False),
            ("Response Time", "Staff typically respond within 24 hours", False)
        ]
    )
    
    await interaction.channel.send(embed=embed, view=OpenTicketView())
    await interaction.response.send_message("Support ticket panel posted successfully.", ephemeral=True)


@bot.tree.command(name="purchasepanel", description="Post the purchase ticket panel in this channel")
@app_commands.default_permissions(administrator=True)
async def purchasepanel(interaction: discord.Interaction):
    embed = create_embed(
        title="🛒 Purchase Ticket System",
        description="**How to Purchase:**\n1. Select the item you want to buy from the dropdown\n2. Fill in the purchase details\n3. Complete payment in the ticket channel\n4. Receive your item after payment confirmation\n\n**Payment & Delivery:**\n• Multiple payment methods accepted\n• Fast delivery within 1-24 hours\n• Secure and reliable service",
        color=discord.Color.gold(),
        message_type="panel",
        fields=[
            ("Available Items", "• Capes\n• Minecraft Accounts\n• Discord Nitro\n• Boosts\n• Discord Decoration", False),
            ("Support", "Contact staff if you have any questions", False)
        ]
    )
    
    await interaction.channel.send(embed=embed, view=PurchaseView())
    await interaction.response.send_message("Purchase panel posted successfully.", ephemeral=True)


@bot.tree.command(name="sync", description="Sync bot commands with Discord (admin only)")
@app_commands.default_permissions(administrator=True)
async def sync(interaction: discord.Interaction):
    """Force sync bot commands"""
    # Defer the response since sync can take time
    await interaction.response.defer(ephemeral=True)
    
    try:
        if SYNC_GUILD_ID:
            synced = await bot.tree.sync(guild=discord.Object(SYNC_GUILD_ID))
        else:
            synced = await bot.tree.sync()
        embed = create_embed(
            title="✅ Commands Synced",
            description=f"Successfully synced {len(synced)} commands",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        try:
            embed = create_embed(
                title="❌ Sync Failed",
                description=f"Error syncing commands: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except:
            await interaction.followup.send(f"Sync failed: {str(e)}", ephemeral=True)


@bot.tree.command(name="clearglobal", description="Clear all global commands to fix duplicates (admin only)")
@app_commands.default_permissions(administrator=True)
async def clearglobal(interaction: discord.Interaction):
    """Clear all global commands"""
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Clear all global commands
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        
        embed = create_embed(
            title="✅ Global Commands Cleared",
            description="All global commands have been cleared. Please restart the bot and use /sync to sync guild commands only.",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        try:
            embed = create_embed(
                title="❌ Clear Failed",
                description=f"Error clearing global commands: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except:
            await interaction.followup.send(f"Clear failed: {str(e)}", ephemeral=True)


@bot.tree.command(name="config", description="Configure bot settings (admin only)")
@app_commands.default_permissions(administrator=True)
async def config(interaction: discord.Interaction):
    """Show current configuration"""
    try:
        embed = create_embed(
            title="⚙️ Bot Configuration",
            description="Current bot settings:",
            color=discord.Color.blue(),
            message_type="config",
            fields=[
                ("Support Role ID", str(SUPPORT_ROLE_ID), True),
                ("Ticket Category ID", str(CATEGORY_ID), True),
                ("Log Channel ID", str(LOG_CHANNEL_ID), True),
                ("Rating Channel ID", str(RATING_CHANNEL_ID), True),
                ("Vouch Channel ID", str(VOUCH_CHANNEL_ID), True),
                ("Thumbnail URL", THUMBNAIL_URL if THUMBNAIL_URL else "Not set", False),
                ("Banner URL", BANNER_URL if BANNER_URL else "Not set", False),
                ("INR QR URL", INR_QR_URL if INR_QR_URL else "Not set", False),
                ("LTC QR URL", LTC_QR_URL if LTC_QR_URL else "Not set", False),
                ("INR Wallet", INR_WALLET_ADDRESS if INR_WALLET_ADDRESS else "Not set", False),
                ("LTC Wallet", LTC_WALLET_ADDRESS if LTC_WALLET_ADDRESS else "Not set", False)
            ]
        )
        
        # Add banner settings as a separate field
        banner_settings_text = "\n".join([
            f"• Ticket Creation: {'✅' if BANNER_SETTINGS['ticket_creation'] else '❌'}",
            f"• Purchase Creation: {'✅' if BANNER_SETTINGS['purchase_creation'] else '❌'}",
            f"• Ticket Controls: {'✅' if BANNER_SETTINGS['ticket_controls'] else '❌'}",
            f"• Payment Info: {'✅' if BANNER_SETTINGS['payment_info'] else '❌'}",
            f"• Rating: {'✅' if BANNER_SETTINGS['rating'] else '❌'}",
            f"• Vouch: {'✅' if BANNER_SETTINGS['vouch'] else '❌'}",
            f"• Panels: {'✅' if BANNER_SETTINGS['panel'] else '❌'}",
            f"• General: {'✅' if BANNER_SETTINGS['general'] else '❌'}",
        ])
        embed.add_field(name="Banner Settings", value=banner_settings_text, inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except discord.InteractionResponded:
        # If already responded, try to follow up
        try:
            await interaction.followup.send("Configuration already sent.", ephemeral=True)
        except:
            pass
    except Exception as e:
        try:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)
        except:
            pass


@bot.tree.command(name="setcategory", description="Set the ticket category ID (admin only)")
@app_commands.default_permissions(administrator=True)
async def setcategory(interaction: discord.Interaction, category_id: str):
    """Set the category where tickets are created"""
    global CATEGORY_ID
    try:
        CATEGORY_ID = int(category_id)
        # Update .env file
        update_env_var("TICKET_CATEGORY_ID", category_id)
        
        embed = create_embed(
            title="✅ Category Updated",
            description=f"Ticket category ID has been set to `{category_id}`",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except ValueError:
        await interaction.response.send_message("Invalid category ID. Please provide a valid number.", ephemeral=True)


@bot.tree.command(name="setrole", description="Set the support role ID (admin only)")
@app_commands.default_permissions(administrator=True)
async def setrole(interaction: discord.Interaction, role_id: str):
    """Set the support/staff role"""
    global SUPPORT_ROLE_ID
    try:
        SUPPORT_ROLE_ID = int(role_id)
        # Update .env file
        update_env_var("SUPPORT_ROLE_ID", role_id)
        
        embed = create_embed(
            title="✅ Support Role Updated",
            description=f"Support role ID has been set to `{role_id}`",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except ValueError:
        await interaction.response.send_message("Invalid role ID. Please provide a valid number.", ephemeral=True)


@bot.tree.command(name="setlogchannel", description="Set the log channel ID (admin only)")
@app_commands.default_permissions(administrator=True)
async def setlogchannel(interaction: discord.Interaction, channel_id: str):
    """Set the channel for ticket transcripts"""
    global LOG_CHANNEL_ID
    try:
        LOG_CHANNEL_ID = int(channel_id)
        # Update .env file
        update_env_var("LOG_CHANNEL_ID", channel_id)
        
        embed = create_embed(
            title="✅ Log Channel Updated",
            description=f"Log channel ID has been set to `{channel_id}`",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except ValueError:
        await interaction.response.send_message("Invalid channel ID. Please provide a valid number.", ephemeral=True)


@bot.tree.command(name="setthumbnail", description="Set the thumbnail image URL (admin only)")
@app_commands.default_permissions(administrator=True)
async def setthumbnail(interaction: discord.Interaction, url: str):
    """Set the thumbnail image for embeds"""
    global THUMBNAIL_URL
    THUMBNAIL_URL = url
    # Update .env file
    update_env_var("THUMBNAIL_URL", url)
    
    embed = create_embed(
        title="✅ Thumbnail Updated",
        description=f"Thumbnail image has been set to the provided URL",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=url)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="setbanner", description="Set the banner image URL (admin only)")
@app_commands.default_permissions(administrator=True)
async def setbanner(interaction: discord.Interaction, url: str):
    """Set the banner image for embeds"""
    global BANNER_URL
    BANNER_URL = url
    # Update .env file
    update_env_var("BANNER_URL", url)
    
    embed = create_embed(
        title="✅ Banner Updated",
        description=f"Banner image has been set to the provided URL",
        color=discord.Color.green()
    )
    embed.set_image(url=url)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="togglebanner", description="Toggle banner visibility for specific message types (admin only)")
@app_commands.default_permissions(administrator=True)
@app_commands.choices(
    message_type=[
        app_commands.Choice(name="Ticket Creation", value="ticket_creation"),
        app_commands.Choice(name="Purchase Creation", value="purchase_creation"),
        app_commands.Choice(name="Ticket Controls", value="ticket_controls"),
        app_commands.Choice(name="Payment Info", value="payment_info"),
        app_commands.Choice(name="Rating", value="rating"),
        app_commands.Choice(name="Vouch", value="vouch"),
        app_commands.Choice(name="Panel", value="panel"),
        app_commands.Choice(name="General", value="general"),
        app_commands.Choice(name="All", value="all"),
    ]
)
async def togglebanner(interaction: discord.Interaction, message_type: str):
    """Toggle banner visibility for specific message types
    
    Args:
        message_type: Type of message (ticket_creation, purchase_creation, ticket_controls, payment_info, rating, vouch, panel, general, all)
    """
    from config import BANNER_SETTINGS as current_settings
    
    message_type = message_type.lower()
    
    if message_type == "all":
        # Toggle all settings
        new_state = not current_settings["general"]
        for key in current_settings:
            set_banner_setting(key, new_state)
        
        status = "enabled" if new_state else "disabled"
        embed = create_embed(
            title="✅ All Banner Settings Toggled",
            description=f"Banners are now **{status}** for all message types.",
            color=discord.Color.green()
        )
    elif message_type in current_settings:
        # Toggle specific setting
        new_state = toggle_banner_setting(message_type)
        
        status = "enabled" if new_state else "disabled"
        embed = create_embed(
            title="✅ Banner Setting Toggled",
            description=f"Banners for **{message_type}** messages are now **{status}**.",
            color=discord.Color.green()
        )
    else:
        # Show available options
        available_types = ", ".join(current_settings.keys()) + ", all"
        embed = create_embed(
            title="❌ Invalid Message Type",
            description=f"Available message types: {available_types}",
            color=discord.Color.red()
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="bannersettings", description="View current banner settings")
async def bannersettings(interaction: discord.Interaction):
    """View current banner settings"""
    from config import BANNER_SETTINGS as current_settings
    
    settings_text = ""
    for setting, enabled in current_settings.items():
        status = "✅ Enabled" if enabled else "❌ Disabled"
        settings_text += f"**{setting}:** {status}\n"
    
    embed = create_embed(
        title="🎨 Banner Settings",
        description=settings_text,
        color=discord.Color.blue(),
        message_type="general"
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="setinrqr", description="Set INR QR code URL (admin only)")
@app_commands.default_permissions(administrator=True)
async def setinrqr(interaction: discord.Interaction, url: str):
    """Set the INR QR code URL"""
    global INR_QR_URL
    INR_QR_URL = url
    update_env_var("INR_QR_URL", url)
    
    embed = create_embed(
        title="✅ INR QR Code Updated",
        description=f"INR QR code has been set to the provided URL",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="setltcqr", description="Set LTC QR code URL (admin only)")
@app_commands.default_permissions(administrator=True)
async def setltcqr(interaction: discord.Interaction, url: str):
    """Set the LTC QR code URL"""
    global LTC_QR_URL
    LTC_QR_URL = url
    update_env_var("LTC_QR_URL", url)
    
    embed = create_embed(
        title="✅ LTC QR Code Updated",
        description=f"LTC QR code has been set to the provided URL",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="setinrwallet", description="Set INR wallet address (admin only)")
@app_commands.default_permissions(administrator=True)
async def setinrwallet(interaction: discord.Interaction, address: str):
    """Set the INR wallet address"""
    global INR_WALLET_ADDRESS
    INR_WALLET_ADDRESS = address
    update_env_var("INR_WALLET_ADDRESS", address)
    
    embed = create_embed(
        title="✅ INR Wallet Updated",
        description=f"INR wallet address has been set",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="setltcwallet", description="Set LTC wallet address (admin only)")
@app_commands.default_permissions(administrator=True)
async def setltcwallet(interaction: discord.Interaction, address: str):
    """Set the LTC wallet address"""
    global LTC_WALLET_ADDRESS
    LTC_WALLET_ADDRESS = address
    update_env_var("LTC_WALLET_ADDRESS", address)
    
    embed = create_embed(
        title="✅ LTC Wallet Updated",
        description=f"LTC wallet address has been set",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="setratingchannel", description="Set rating channel ID (admin only)")
@app_commands.default_permissions(administrator=True)
async def setratingchannel(interaction: discord.Interaction, channel_id: str):
    """Set the channel for ratings"""
    global RATING_CHANNEL_ID
    try:
        RATING_CHANNEL_ID = int(channel_id)
        update_env_var("RATING_CHANNEL_ID", channel_id)
        
        embed = create_embed(
            title="✅ Rating Channel Updated",
            description=f"Rating channel ID has been set to `{channel_id}`",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except ValueError:
        await interaction.response.send_message("Invalid channel ID. Please provide a valid number.", ephemeral=True)


@bot.tree.command(name="setvouchchannel", description="Set vouch channel ID (admin only)")
@app_commands.default_permissions(administrator=True)
async def setvouchchannel(interaction: discord.Interaction, channel_id: str):
    """Set the channel for vouches"""
    global VOUCH_CHANNEL_ID
    try:
        VOUCH_CHANNEL_ID = int(channel_id)
        update_env_var("VOUCH_CHANNEL_ID", channel_id)
        
        embed = create_embed(
            title="✅ Vouch Channel Updated",
            description=f"Vouch channel ID has been set to `{channel_id}`",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except ValueError:
        await interaction.response.send_message("Invalid channel ID. Please provide a valid number.", ephemeral=True)


@bot.tree.command(name="vouch_gen", description="Generate a vouch request (staff only)")
@app_commands.default_permissions(administrator=True)
async def vouch_gen(interaction: discord.Interaction, user: discord.Member, item: str, price: str):
    """Generate a vouch request for a user"""
    await generate_vouch_request(interaction, user, item, price)


@bot.tree.command(name="vouch", description="View vouch information for a user")
async def vouch_command(interaction: discord.Interaction, member: discord.Member = None):
    """View vouch information for a user"""
    await get_vouch_info(interaction, member)


@bot.tree.command(name="leaderboard", description="Show top vouched users")
async def leaderboard_command(interaction: discord.Interaction):
    """Show top vouched users"""
    await get_leaderboard(interaction)


@bot.tree.command(name="myvouches", description="View your own vouches")
async def myvouches_slash_command(interaction: discord.Interaction):
    """View your own vouches"""
    await get_vouch_info(interaction, interaction.user)


@bot.tree.command(name="claimed", description="View all claimed tickets (staff only)")
@app_commands.default_permissions(administrator=True)
async def claimed(interaction: discord.Interaction):
    """View all currently claimed tickets"""
    guild = interaction.guild
    category = guild.get_channel(CATEGORY_ID)
    
    if not category:
        await interaction.response.send_message("Ticket category not found.", ephemeral=True)
        return
    
    claimed_tickets = []
    
    for channel in category.text_channels:
        info = get_ticket_info(channel)
        if info.get("claimed_by"):
            claimed_member = guild.get_member(info["claimed_by"])
            owner = guild.get_member(info["owner_id"])
            
            claimed_tickets.append({
                "channel": channel,
                "claimed_by": claimed_member,
                "owner": owner,
                "category": info["category"],
                "priority": info.get("priority", "N/A"),
                "item": info.get("item", "N/A")
            })
    
    if not claimed_tickets:
        embed = create_embed(
            title="📋 Claimed Tickets",
            description="No tickets are currently claimed.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Create description with claimed tickets
    description = f"**Total Claimed: {len(claimed_tickets)}**\n\n"
    for i, ticket in enumerate(claimed_tickets, 1):
        claimed_name = ticket["claimed_by"].name if ticket["claimed_by"] else "Unknown"
        owner_name = ticket["owner"].name if ticket["owner"] else "Unknown"
        
        if ticket["category"] == "purchase":
            item_info = f"Item: {ticket['item']}"
        else:
            item_info = f"Priority: {ticket['priority']}"
        
        description += f"**{i}.** {ticket['channel'].mention}\n"
        description += f"   👤 Owner: {owner_name}\n"
        description += f"   ✋ Claimed by: {claimed_name}\n"
        description += f"   📂 {item_info}\n\n"
    
    embed = create_embed(
        title="📋 Claimed Tickets",
        description=description,
        color=discord.Color.blue()
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="reopen", description="Reopen a closed ticket (staff only)")
@app_commands.default_permissions(administrator=True)
async def reopen(interaction: discord.Interaction, channel: discord.TextChannel):
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can reopen tickets.", ephemeral=True)
        return

    # Check if channel exists and is a ticket
    if not channel.topic or "ticket-owner:" not in channel.topic:
        await interaction.response.send_message("This is not a valid ticket channel.", ephemeral=True)
        return

    info = get_ticket_info(channel)
    owner = interaction.guild.get_member(info["owner_id"])
    
    # Restore permissions
    support_role = interaction.guild.get_role(SUPPORT_ROLE_ID)
    member_perms = discord.PermissionOverwrite(
        view_channel=True,
        send_messages=True,
        read_message_history=True,
        attach_files=True,
        embed_links=True
    )
    
    await channel.set_permissions(interaction.guild.default_role, view_channel=False)
    await channel.set_permissions(owner, overwrite=member_perms)
    await channel.set_permissions(support_role, overwrite=member_perms)
    
    embed = create_embed(
        title="🔓 Ticket Reopened",
        description=f"This ticket has been reopened by {interaction.user.mention}",
        color=discord.Color.green()
    )
    
    await channel.send(content=f"{owner.mention if owner else ''} {support_role.mention}", embed=embed)
    
    # DM the owner
    if owner:
        try:
            dm_embed = create_embed(
                title="Ticket Reopened",
                description=f"Your ticket **{channel.name}** has been reopened.",
                color=discord.Color.green()
            )
            await owner.send(embed=dm_embed)
        except discord.Forbidden:
            pass
    
    await interaction.response.send_message(f"Ticket {channel.mention} has been reopened.", ephemeral=True)


@bot.tree.command(name="closeallticket", description="Close all tickets (admin only)")
@app_commands.default_permissions(administrator=True)
async def closeallticket(interaction: discord.Interaction):
    """Close all tickets in the ticket category"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can close all tickets.", ephemeral=True)
        return

    guild = interaction.guild
    category = guild.get_channel(CATEGORY_ID)
    
    if not category:
        await interaction.response.send_message("Ticket category not found.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    closed_count = 0
    failed_count = 0
    
    for channel in category.text_channels:
        if channel.topic and "ticket-owner:" in channel.topic:
            try:
                info = get_ticket_info(channel)
                owner = guild.get_member(info["owner_id"])
                
                # Build transcript
                lines = []
                lines.append("=" * 50)
                lines.append(f"Ticket: {channel.name}")
                lines.append(f"Category: {info['category']}")
                if info['category'] == 'purchase':
                    lines.append(f"Item: {info.get('item', 'Unknown')}")
                    lines.append(f"Quantity: {info.get('quantity', 'Unknown')}")
                elif info.get('priority'):
                    lines.append(f"Priority: {info['priority']}")
                if info['claimed_by']:
                    claimed_member = guild.get_member(info['claimed_by'])
                    lines.append(f"Claimed by: {claimed_member.name if claimed_member else 'Unknown'} ({info['claimed_by']})")
                lines.append(f"Owner: {owner.name if owner else 'Unknown'} ({info['owner_id']})")
                lines.append(f"Closed by: {interaction.user}")
                lines.append(f"Closed at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
                lines.append("=" * 50)
                lines.append("")
                
                async for m in channel.history(limit=None, oldest_first=True):
                    ts = m.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    text = m.content or ""
                    if m.attachments:
                        text += " " + " ".join(f"[Attachment: {a.filename}]({a.url})" for a in m.attachments)
                    lines.append(f"[{ts}] {m.author}: {text}")
                
                transcript = io.BytesIO("\n".join(lines).encode("utf-8"))

                # Send to log channel
                if LOG_CHANNEL_ID:
                    log = guild.get_channel(LOG_CHANNEL_ID)
                    if log:
                        log_embed = create_embed(
                            title="🔒 Ticket Closed (Bulk)",
                            description=f"**Ticket:** {channel.name}\n**Closed by:** {interaction.user.mention}",
                            color=discord.Color.red()
                        )
                        await log.send(embed=log_embed, file=discord.File(transcript, filename=f"{channel.name}-transcript.txt"))

                # DM the owner
                if owner:
                    try:
                        if info['category'] == 'purchase':
                            dm_embed = create_embed(
                                title="Purchase Ticket Closed",
                                description=f"Your purchase ticket **{channel.name}** has been closed by {interaction.user.mention}.\n\nIf you need to make another purchase, please open a new ticket.",
                                color=discord.Color.gold()
                            )
                        else:
                            dm_embed = create_embed(
                                title="Ticket Closed",
                                description=f"Your ticket **{channel.name}** has been closed by {interaction.user.mention}.\n\nIf you need further assistance, please open a new ticket.",
                                color=discord.Color.red()
                            )
                        await owner.send(embed=dm_embed)
                    except discord.Forbidden:
                        pass

                await channel.delete(reason=f"Bulk closed by {interaction.user}")
                closed_count += 1
            except Exception as e:
                print(f"Error closing ticket {channel.name}: {e}")
                failed_count += 1
    
    embed = create_embed(
        title="✅ Bulk Close Complete",
        description=f"Successfully closed {closed_count} ticket(s)",
        color=discord.Color.green()
    )
    if failed_count > 0:
        embed.add_field(name="Failed", value=f"{failed_count} ticket(s) could not be closed", inline=False)
    
    await interaction.followup.send(embed=embed, ephemeral=True)


# ============ PREFIX COMMANDS ============

@bot.command(name="payment")
async def payment_command(ctx):
    """Show payment options"""
    # Check if user is in a ticket channel
    info = get_ticket_info(ctx.channel)
    if not info.get("owner_id"):
        await ctx.send("This command can only be used in ticket channels.")
        return
    
    embed = create_embed(
        title="💳 Select Payment Method",
        description="Choose your preferred payment method to see the QR code and wallet details.",
        color=discord.Color.gold(),
        message_type="payment_info"
    )
    await ctx.send(embed=embed, view=PaymentMethodView())


@bot.command(name="order")
async def order_command(ctx, action: str = None):
    """Order management commands"""
    if action is None:
        await ctx.send("Usage: `!order done` - Mark order as complete and request rating")
        return
    
    if action.lower() == "done":
        # Check if user is staff
        is_staff = any(r.id == SUPPORT_ROLE_ID for r in ctx.author.roles)
        if not is_staff:
            await ctx.send("Only staff can mark orders as done.")
            return
        
        # Check if in a ticket channel
        info = get_ticket_info(ctx.channel)
        if not info.get("owner_id"):
            await ctx.send("This command can only be used in ticket channels.")
            return
        
        owner = ctx.guild.get_member(info["owner_id"])
        if not owner:
            await ctx.send("Ticket owner not found.")
            return
        
        embed = create_embed(
            title="🎉 Order Completed!",
            description=f"Your order has been completed! Please rate your experience:",
            color=discord.Color.green(),
            message_type="rating"
        )
        await ctx.send(f"{owner.mention}", embed=embed, view=RatingView())
    else:
        await ctx.send("Unknown action. Usage: `!order done`")


@bot.command(name="vouch")
async def vouch_prefix_command(ctx, member: discord.Member = None):
    """Prefix command for vouch (alias)"""
    if member is None:
        member = ctx.author
    
    vouches = load_vouches()
    user_id_str = str(member.id)
    
    if user_id_str not in vouches or not vouches[user_id_str].get("vouches"):
        embed = create_embed(
            title="📊 Vouch Information",
            description=f"{member.mention} has no vouches yet.",
            color=discord.Color.blue(),
            message_type="vouch"
        )
        await ctx.send(embed=embed)
        return
    
    user_vouches = vouches[user_id_str]
    vouch_list = user_vouches["vouches"]
    
    embed = create_embed(
        title="📊 Vouch Information",
        description=f"**User:** {member.mention}\n**Total Vouches:** {len(vouch_list)}",
        color=discord.Color.gold(),
        message_type="vouch",
        fields=[
            ("Recent Vouches", "\n".join([f"✅ {v['item']} - {v['price']}" for v in vouch_list[-5:]]), False)
        ]
    )
    await ctx.send(embed=embed)


@bot.command(name="myvouches")
async def myvouches_command(ctx):
    """View your own vouches"""
    vouches = load_vouches()
    user_id_str = str(ctx.author.id)
    
    if user_id_str not in vouches or not vouches[user_id_str].get("vouches"):
        embed = create_embed(
            title="📊 My Vouches",
            description="You have no vouches yet.",
            color=discord.Color.blue(),
            message_type="vouch"
        )
        await ctx.send(embed=embed)
        return
    
    user_vouches = vouches[user_id_str]
    vouch_list = user_vouches["vouches"]
    
    embed = create_embed(
        title="📊 My Vouches",
        description=f"**Total Vouches:** {len(vouch_list)}",
        color=discord.Color.gold(),
        message_type="vouch",
        fields=[
            ("My Vouches", "\n".join([f"✅ {v['item']} - {v['price']}" for v in vouch_list]), False)
        ]
    )
    await ctx.send(embed=embed)


@bot.command(name="leaderboard")
async def leaderboard_prefix_command(ctx):
    """Prefix command for leaderboard (alias)"""
    vouches = load_vouches()
    
    if not vouches:
        await ctx.send("No vouch data available yet.")
        return
    
    # Calculate leaderboard
    leaderboard = []
    for user_id_str, data in vouches.items():
        if data.get("vouches"):
            leaderboard.append({
                "user_id": int(user_id_str),
                "total_vouches": len(data["vouches"])
            })
    
    # Sort by total vouches
    leaderboard.sort(key=lambda x: x["total_vouches"], reverse=True)
    top_10 = leaderboard[:10]
    
    description = ""
    for i, entry in enumerate(top_10, 1):
        member = ctx.guild.get_member(entry["user_id"])
        member_name = member.name if member else f"User {entry['user_id']}"
        description += f"**{i}.** {member_name}\n   📊 {entry['total_vouches']} vouches\n\n"
    
    embed = create_embed(
        title="🏆 Vouch Leaderboard",
        description=description or "No vouches yet.",
        color=discord.Color.gold(),
        message_type="vouch"
    )
    await ctx.send(embed=embed)


# ============ GIVEAWAY COMMANDS ============

@bot.tree.command(name="giveaway", description="Create a new giveaway (admin only)")
@app_commands.default_permissions(administrator=True)
async def giveaway(interaction: discord.Interaction):
    """Create a new giveaway"""
    if not ENABLE_GIVEAWAYS:
        await interaction.response.send_message("Giveaway system is disabled.", ephemeral=True)
        return
    await giveaway_command(interaction)


@bot.tree.command(name="endgiveaway", description="End a giveaway manually (admin only)")
@app_commands.default_permissions(administrator=True)
async def endgiveaway(interaction: discord.Interaction, giveaway_id: str):
    """End a giveaway manually"""
    if not ENABLE_GIVEAWAYS:
        await interaction.response.send_message("Giveaway system is disabled.", ephemeral=True)
        return
    await endgiveaway_command(interaction, giveaway_id)


@bot.tree.command(name="reroll", description="Reroll a giveaway winner (admin only)")
@app_commands.default_permissions(administrator=True)
async def reroll(interaction: discord.Interaction, giveaway_id: str):
    """Reroll a giveaway winner"""
    if not ENABLE_GIVEAWAYS:
        await interaction.response.send_message("Giveaway system is disabled.", ephemeral=True)
        return
    await reroll_command(interaction, giveaway_id)


@bot.tree.command(name="listgiveaways", description="List all giveaways")
async def listgiveaways(interaction: discord.Interaction):
    """List all giveaways"""
    if not ENABLE_GIVEAWAYS:
        await interaction.response.send_message("Giveaway system is disabled.", ephemeral=True)
        return
    await listgiveaways_command(interaction)


# ============ INVITE TRACKER COMMANDS ============

@bot.tree.command(name="invitestats", description="View invite statistics for a user")
async def invitestats(interaction: discord.Interaction, member: discord.Member = None):
    """View invite statistics for a user"""
    if not ENABLE_INVITE_TRACKER:
        await interaction.response.send_message("Invite tracker is disabled.", ephemeral=True)
        return
    await invitestats_command(interaction, member)


@bot.tree.command(name="inviteleaderboard", description="View invite leaderboard")
async def inviteleaderboard(interaction: discord.Interaction):
    """View invite leaderboard"""
    if not ENABLE_INVITE_TRACKER:
        await interaction.response.send_message("Invite tracker is disabled.", ephemeral=True)
        return
    await inviteleaderboard_command(interaction)


@bot.tree.command(name="whoinvited", description="Check who invited a user")
async def whoinvited(interaction: discord.Interaction, member: discord.Member = None):
    """Check who invited a user"""
    if not ENABLE_INVITE_TRACKER:
        await interaction.response.send_message("Invite tracker is disabled.", ephemeral=True)
        return
    await whoinvited_command(interaction, member)


@bot.tree.command(name="setinvitechannel", description="Set the invite announcement channel (admin only)")
@app_commands.default_permissions(administrator=True)
async def setinvitechannel(interaction: discord.Interaction, channel: discord.TextChannel):
    """Set the invite announcement channel"""
    if not ENABLE_INVITE_TRACKER:
        await interaction.response.send_message("Invite tracker is disabled.", ephemeral=True)
        return
    await setinvitechannel_command(interaction, channel)


# ============ WELCOMER COMMANDS ============

@bot.tree.command(name="setwelcomemessage", description="Set the welcome message (admin only)")
@app_commands.default_permissions(administrator=True)
async def setwelcomemessage(interaction: discord.Interaction, message: str):
    """Set the welcome message"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await setwelcomemessage_command(interaction, message)


@bot.tree.command(name="setwelcomerchannel", description="Set the welcome channel (admin only)")
@app_commands.default_permissions(administrator=True)
async def setwelcomerchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    """Set the welcome channel"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await setwelcomerchannel_command(interaction, channel)


@bot.tree.command(name="togglewelcome", description="Toggle welcome messages on/off (admin only)")
@app_commands.default_permissions(administrator=True)
async def togglewelcome(interaction: discord.Interaction):
    """Toggle welcome messages on/off"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await togglewelcome_command(interaction)


@bot.tree.command(name="setgoodbyemessage", description="Set the goodbye message (admin only)")
@app_commands.default_permissions(administrator=True)
async def setgoodbyemessage(interaction: discord.Interaction, message: str):
    """Set the goodbye message"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await setgoodbyemessage_command(interaction, message)


@bot.tree.command(name="setgoodbyechannel", description="Set the goodbye channel (admin only)")
@app_commands.default_permissions(administrator=True)
async def setgoodbyechannel(interaction: discord.Interaction, channel: discord.TextChannel):
    """Set the goodbye channel"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await setgoodbyechannel_command(interaction, channel)


@bot.tree.command(name="togglegoodbye", description="Toggle goodbye messages on/off (admin only)")
@app_commands.default_permissions(administrator=True)
async def togglegoodbye(interaction: discord.Interaction):
    """Toggle goodbye messages on/off"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await togglegoodbye_command(interaction)


@bot.tree.command(name="welcomeconfig", description="View welcome configuration (admin only)")
@app_commands.default_permissions(administrator=True)
async def welcomeconfig(interaction: discord.Interaction):
    """View welcome configuration"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await welcomeconfig_command(interaction)


@bot.tree.command(name="togglestyledwelcome", description="Toggle styled welcome messages (admin only)")
@app_commands.default_permissions(administrator=True)
async def togglestyledwelcome(interaction: discord.Interaction):
    """Toggle styled welcome messages"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await togglestyledwelcome_command(interaction)


@bot.tree.command(name="setwelcomeimage", description="Set the welcome banner image URL (admin only)")
@app_commands.default_permissions(administrator=True)
async def setwelcomeimage(interaction: discord.Interaction, image_url: str):
    """Set the welcome banner image URL"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await setwelcomeimage_command(interaction, image_url)


@bot.tree.command(name="setthumbnailimage", description="Set the welcome thumbnail image URL (admin only)")
@app_commands.default_permissions(administrator=True)
async def setthumbnailimage(interaction: discord.Interaction, image_url: str):
    """Set the welcome thumbnail image URL"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await setthumbnailimage_command(interaction, image_url)


# ============ BOT EVENTS ============

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Support Role ID: {SUPPORT_ROLE_ID}")
    print(f"Category ID: {CATEGORY_ID}")
    print(f"Log Channel ID: {LOG_CHANNEL_ID}")
    print(f"Rating Channel ID: {RATING_CHANNEL_ID}")
    print("------")
    
    # Set bot status
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="Made by Shashank Sharma"))
    
    # Track invites for all servers
    for guild in bot.guilds:
        await track_invites(guild)


@bot.event
async def on_message(message):
    # Process commands
    await bot.process_commands(message)
    
    # Check for vouch messages
    if message.channel.id == VOUCH_CHANNEL_ID and VOUCH_CHANNEL_ID != 0:
        await process_vouch_message(message)


@bot.event
async def on_member_join(member):
    # Handle invite tracking if enabled
    if ENABLE_INVITE_TRACKER:
        await check_invite_join(member)
    
    # Handle welcome message if enabled
    if ENABLE_WELCOMER:
        await send_welcome(member)


@bot.event
async def on_member_remove(member):
    # Handle invite tracking if enabled
    if ENABLE_INVITE_TRACKER:
        await check_invite_leave(member)
    
    # Handle goodbye message if enabled
    if ENABLE_WELCOMER:
        await send_goodbye(member)


@bot.event
async def on_guild_join(guild):
    # Track invites when bot joins a new server if enabled
    if ENABLE_INVITE_TRACKER:
        await track_invites(guild)


if __name__ == "__main__":
    bot.run(TOKEN)
