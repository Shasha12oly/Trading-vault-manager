"""
Professional Discord Ticket Bot (discord.py 2.x)

Features:
- Support Ticket System (General Support, Account Issue)
- Purchase Ticket System (Capes, Minecraft Accounts, Discord Nitro, Boosts, Discord Decoration)
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
import io
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands
import json
import os.path

# Load environment variables
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
SUPPORT_ROLE_ID = int(os.getenv("SUPPORT_ROLE_ID", "0"))
CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID", "0"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))
THUMBNAIL_URL = os.getenv("THUMBNAIL_URL", "")
BANNER_URL = os.getenv("BANNER_URL", "")
SYNC_GUILD_ID = int(os.getenv("SYNC_GUILD_ID", "0"))
INR_QR_URL = os.getenv("INR_QR_URL", "")
LTC_QR_URL = os.getenv("LTC_QR_URL", "")
INR_WALLET_ADDRESS = os.getenv("INR_WALLET_ADDRESS", "")
LTC_WALLET_ADDRESS = os.getenv("LTC_WALLET_ADDRESS", "")
RATING_CHANNEL_ID = int(os.getenv("RATING_CHANNEL_ID", "0"))
VOUCH_CHANNEL_ID = int(os.getenv("VOUCH_CHANNEL_ID", "0"))

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


if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found in environment variables")
if SUPPORT_ROLE_ID == 0:
    raise ValueError("SUPPORT_ROLE_ID not found in environment variables")
if CATEGORY_ID == 0:
    raise ValueError("TICKET_CATEGORY_ID not found in environment variables")

intents = discord.Intents.default()
intents.message_content = True  # Required for ! commands
intents.members = True


class TicketBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(OpenTicketView())
        self.add_view(PurchaseView())
        self.add_view(ConfirmCloseView())
        self.add_view(PaymentMethodView())
        self.add_view(RatingView())
        
        # Sync commands globally or to specific guild for faster updates
        if SYNC_GUILD_ID:
            self.tree.copy_global_to(guild=discord.Object(SYNC_GUILD_ID))
            await self.tree.sync(guild=discord.Object(SYNC_GUILD_ID))
        else:
            await self.tree.sync()


bot = TicketBot()

# Vouch data storage
VOUCHES_FILE = "vouches.json"

def load_vouches():
    if os.path.exists(VOUCHES_FILE):
        with open(VOUCHES_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_vouches(vouches):
    with open(VOUCHES_FILE, 'w') as f:
        json.dump(vouches, f, indent=4)

def owner_tag(user_id: int) -> str:
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
    
    # Determine banner visibility
    if show_banner is not None:
        # Explicit override takes precedence
        should_show_banner = show_banner
    else:
        # Use message type setting, fallback to general
        should_show_banner = BANNER_SETTINGS.get(message_type, BANNER_SETTINGS["general"])
    
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


class OpenTicketModal(discord.ui.Modal, title="Create Ticket"):
    def __init__(self, category: str):
        super().__init__()
        self.category = category
        self.priority = "medium"  # Default priority for members

    subject = discord.ui.TextInput(
        label="Subject",
        placeholder="Brief description of your issue",
        max_length=100,
        required=True
    )

    description = discord.ui.TextInput(
        label="Description",
        style=discord.TextStyle.long,
        placeholder="Please describe your issue in detail...",
        max_length=2000,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await create_ticket(
            interaction,
            self.category,
            self.priority,
            self.subject.value,
            self.description.value,
            from_modal=True
        )


class OpenTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="General Support", emoji="📧", style=discord.ButtonStyle.danger, custom_id="ticket:general")
    async def general_support(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = OpenTicketModal("general")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Claim Giveaway", emoji="🎁", style=discord.ButtonStyle.primary, custom_id="ticket:giveaway")
    async def claim_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = OpenTicketModal("giveaway")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Enquiry", emoji="📖", style=discord.ButtonStyle.success, custom_id="ticket:enquiry")
    async def enquiry(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = OpenTicketModal("enquiry")
        await interaction.response.send_modal(modal)


async def create_ticket(interaction: discord.Interaction, category: str, priority: str, subject: str, description: str, from_modal: bool = False):
    guild = interaction.guild
    category_channel = guild.get_channel(CATEGORY_ID)
    support_role = guild.get_role(SUPPORT_ROLE_ID)

    if not category_channel:
        if from_modal:
            await interaction.followup.send(
                "Ticket category not found. Please contact an administrator to configure the bot.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Ticket category not found. Please contact an administrator to configure the bot.",
                ephemeral=True
            )
        return

    if not support_role:
        if from_modal:
            await interaction.followup.send(
                "Support role not found. Please contact an administrator to configure the bot.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Support role not found. Please contact an administrator to configure the bot.",
                ephemeral=True
            )
        return

    # Check for existing tickets
    for ch in category_channel.text_channels:
        if ch.topic and owner_tag(interaction.user.id) in ch.topic:
            if from_modal:
                await interaction.followup.send(
                    f"You already have an open ticket: {ch.mention}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"You already have an open ticket: {ch.mention}",
                    ephemeral=True
                )
            return

    # Category display names and colors
    category_names = {
        "general": "General Support",
        "giveaway": "Claim Giveaway",
        "enquiry": "Enquiry"
    }
    
    category_colors = {
        "general": discord.Color.red(),
        "giveaway": discord.Color.blurple(),
        "enquiry": discord.Color.green()
    }

    member_perms = discord.PermissionOverwrite(
        view_channel=True,
        send_messages=True,
        read_message_history=True,
        attach_files=True,
        embed_links=True
    )
    
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: member_perms,
        support_role: member_perms,
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            manage_channels=True,
            read_message_history=True
        ),
    }

    # Create channel with descriptive name
    channel_name = f"ticket-{category}-{interaction.user.name}"[:90]
    topic = f"{owner_tag(interaction.user.id)} | category:{category} | priority:{priority}"
    
    channel = await guild.create_text_channel(
        name=channel_name,
        category=category_channel,
        topic=topic,
        overwrites=overwrites,
    )

    # Create professional embed
    embed = create_embed(
        title=f"🎫 Ticket Created - {subject}",
        description=f"**Category:** {category_names.get(category, category)}\n\n**Description:**\n{description}",
        color=category_colors.get(category, discord.Color.blue()),
        message_type="ticket_creation",
        fields=[
            ("Category", category_names.get(category, category), True),
            ("Status", "🟢 Open", True)
        ]
    )

    # Send welcome message
    await channel.send(
        content=f"{interaction.user.mention} {support_role.mention}",
        embed=embed,
        view=TicketControlView(channel)
    )

    # DM the user
    try:
        dm_embed = create_embed(
            title="Ticket Created",
            description=f"Your ticket has been created successfully!\n\n**Channel:** {channel.mention}\n**Subject:** {subject}",
            color=discord.Color.green()
        )
        await interaction.user.send(embed=dm_embed)
    except discord.Forbidden:
        pass

    if from_modal:
        await interaction.followup.send(
            f"Your ticket has been created: {channel.mention}",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"Your ticket has been created: {channel.mention}",
            ephemeral=True
        )


class PurchaseSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Capes",
                description="Click to Buy...",
                emoji="🦅",
                value="capes"
            ),
            discord.SelectOption(
                label="Minecraft Accounts",
                description="Click to Buy...",
                emoji="⛏️",
                value="minecraft"
            ),
            discord.SelectOption(
                label="Discord Nitro",
                description="Click to Buy...",
                emoji="💎",
                value="nitro"
            ),
            discord.SelectOption(
                label="Boosts",
                description="Click to Buy...",
                emoji="🚀",
                value="boosts"
            ),
            discord.SelectOption(
                label="Discord Decoration",
                description="Click to Buy...",
                emoji="🎨",
                value="decoration"
            ),
        ]
        super().__init__(
            placeholder="Select What you want to buy",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="purchase:select"
        )

    async def callback(self, interaction: discord.Interaction):
        item = self.values[0]
        await create_purchase_ticket(interaction, item)


class PurchaseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PurchaseSelect())


class PurchaseModal(discord.ui.Modal, title="Purchase Details"):
    def __init__(self, item: str):
        super().__init__()
        self.item = item

    quantity = discord.ui.TextInput(
        label="Quantity",
        placeholder="How many would you like to purchase?",
        max_length=10,
        required=True
    )

    payment_method = discord.ui.TextInput(
        label="Payment Method",
        placeholder="e.g., PayPal, Crypto, etc.",
        max_length=50,
        required=True
    )

    additional_info = discord.ui.TextInput(
        label="Additional Information",
        style=discord.TextStyle.long,
        placeholder="Any specific requirements or details...",
        max_length=1000,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await process_purchase(
            interaction,
            self.item,
            self.quantity.value,
            self.payment_method.value,
            self.additional_info.value,
            from_modal=True
        )


async def create_purchase_ticket(interaction: discord.Interaction, item: str):
    modal = PurchaseModal(item)
    await interaction.response.send_modal(modal)


async def process_purchase(interaction: discord.Interaction, item: str, quantity: str, payment_method: str, additional_info: str, from_modal: bool = False):
    guild = interaction.guild
    category_channel = guild.get_channel(CATEGORY_ID)
    support_role = guild.get_role(SUPPORT_ROLE_ID)

    if not category_channel:
        if from_modal:
            await interaction.followup.send(
                "Ticket category not found. Please contact an administrator to configure the bot.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Ticket category not found. Please contact an administrator to configure the bot.",
                ephemeral=True
            )
        return

    if not support_role:
        if from_modal:
            await interaction.followup.send(
                "Support role not found. Please contact an administrator to configure the bot.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Support role not found. Please contact an administrator to configure the bot.",
                ephemeral=True
            )
        return

    # Check for existing tickets
    for ch in category_channel.text_channels:
        if ch.topic and owner_tag(interaction.user.id) in ch.topic:
            if from_modal:
                await interaction.followup.send(
                    f"You already have an open ticket: {ch.mention}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"You already have an open ticket: {ch.mention}",
                    ephemeral=True
                )
            return

    member_perms = discord.PermissionOverwrite(
        view_channel=True,
        send_messages=True,
        read_message_history=True,
        attach_files=True,
        embed_links=True
    )
    
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: member_perms,
        support_role: member_perms,
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            manage_channels=True,
            read_message_history=True
        ),
    }

    # Create channel
    channel_name = f"purchase-{item}-{interaction.user.name}"[:90]
    topic = f"{owner_tag(interaction.user.id)} | category:purchase | item:{item} | quantity:{quantity}"
    
    channel = await guild.create_text_channel(
        name=channel_name,
        category=category_channel,
        topic=topic,
        overwrites=overwrites,
    )

    # Create purchase embed
    item_names = {
        "capes": "Capes",
        "minecraft": "Minecraft Accounts",
        "nitro": "Discord Nitro",
        "boosts": "Boosts",
        "decoration": "Discord Decoration"
    }

    embed = create_embed(
        title=f"🛒 Purchase Ticket - {item_names.get(item, item)}",
        description=f"**Item:** {item_names.get(item, item)}\n**Quantity:** {quantity}\n**Payment Method:** {payment_method}",
        color=discord.Color.gold(),
        message_type="purchase_creation",
        fields=[
            ("Payment Method", payment_method, True),
            ("Quantity", quantity, True),
            ("Status", "⏳ Pending Payment", True)
        ]
    )

    if additional_info:
        embed.add_field(name="Additional Info", value=additional_info, inline=False)

    # Send welcome message with payment info
    payment_info = create_embed(
        title="💳 Payment Information",
        description="**You have to pay first before getting Your order**\n\nPlease complete your payment to proceed with your order.\n\nOnce payment is confirmed, your item will be delivered within the specified timeframe.",
        color=discord.Color.green(),
        message_type="payment_info",
        fields=[
            ("Delivery Time", "Usually within 1-24 hours after payment confirmation", False),
            ("Support", "If you have any questions, ping the support team", False),
            ("Payment Methods", "Type `!Payment` to see available payment options", False)
        ]
    )

    await channel.send(
        content=f"{interaction.user.mention} {support_role.mention}",
        embed=embed,
        view=TicketControlView(channel)
    )
    await channel.send(embed=payment_info, view=None)

    # DM the user
    try:
        dm_embed = create_embed(
            title="Purchase Ticket Created",
            description=f"Your purchase ticket has been created successfully!\n\n**Channel:** {channel.mention}\n**Item:** {item_names.get(item, item)}\n**Quantity:** {quantity}\n\nPlease proceed to the channel to complete your payment.",
            color=discord.Color.gold()
        )
        await interaction.user.send(embed=dm_embed)
    except discord.Forbidden:
        pass

    if from_modal:
        await interaction.followup.send(
            f"Your purchase ticket has been created: {channel.mention}",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"Your purchase ticket has been created: {channel.mention}",
            ephemeral=True
        )


class TicketControlView(discord.ui.View):
    def __init__(self, channel=None):
        super().__init__(timeout=None)
        self.channel = channel
        # Only add Order Done button for purchase tickets
        if channel:
            info = get_ticket_info(channel)
            if info.get("category") == "purchase":
                self.add_item(self.order_done_button)

    @discord.ui.button(label="Claim Ticket", emoji="✋", style=discord.ButtonStyle.green, custom_id="ticket:claim")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            channel = interaction.channel
            info = get_ticket_info(channel)
            is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
            
            if not is_staff:
                await interaction.response.send_message(
                    "Only staff can claim tickets.",
                    ephemeral=True
                )
                return

            # Handle unclaim if already claimed by this user
            if info["claimed_by"]:
                if info["claimed_by"] == interaction.user.id:
                    # Unclaim the ticket
                    parts = channel.topic.split("|")
                    new_parts = [part for part in parts if not part.strip().startswith("claimed:")]
                    new_topic = "|".join(new_parts).strip()
                    
                    await channel.edit(topic=new_topic)
                    
                    # Send a new message
                    embed = create_embed(
                        title="🔓 Ticket Unclaimed",
                        description=f"This ticket has been unclaimed by {interaction.user.mention}",
                        color=discord.Color.orange(),
                        message_type="ticket_controls"
                    )
                    await interaction.response.edit_message(view=None)
                    await channel.send(embed=embed)
                    return
                else:
                    await interaction.response.send_message(
                        "This ticket is already claimed by another staff member.",
                        ephemeral=True
                    )
                    return

            # Claim the ticket
            new_topic = channel.topic
            if new_topic:
                new_topic += f" | claimed:{interaction.user.id}"
            else:
                new_topic = f"{owner_tag(info['owner_id'])} | claimed:{interaction.user.id}"
            
            await channel.edit(topic=new_topic)
            
            # Send a new message
            embed = create_embed(
                title="✋ Ticket Claimed",
                description=f"This ticket has been claimed by {interaction.user.mention}",
                color=discord.Color.green(),
                message_type="ticket_controls"
            )
            await interaction.response.edit_message(view=None)
            await channel.send(embed=embed)
        except discord.NotFound:
            await interaction.response.send_message("This ticket channel no longer exists.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Close Ticket", emoji="🔒", style=discord.ButtonStyle.red, custom_id="ticket:close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            channel = interaction.channel
            info = get_ticket_info(channel)
            is_owner = info["owner_id"] == interaction.user.id
            is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
            
            if not (is_owner or is_staff):
                await interaction.response.send_message(
                    "You don't have permission to close this ticket.",
                    ephemeral=True
                )
                return

            embed = create_embed(
                title="Confirm Close",
                description="Are you sure you want to close this ticket? This action cannot be undone.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, view=ConfirmCloseView(), ephemeral=True)
        except discord.NotFound:
            await interaction.response.send_message("This ticket channel no longer exists.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Order Done", emoji="✅", style=discord.ButtonStyle.green, custom_id="ticket:order_done")
    async def order_done_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            channel = interaction.channel
            info = get_ticket_info(channel)
            is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
            
            if not is_staff:
                await interaction.response.send_message(
                    "Only staff can mark orders as done.",
                    ephemeral=True
                )
                return
            
            if not info.get("owner_id"):
                await interaction.response.send_message(
                    "This is not a valid ticket.",
                    ephemeral=True
                )
                return
            
            owner = interaction.guild.get_member(info["owner_id"])
            if not owner:
                await interaction.response.send_message(
                    "Ticket owner not found.",
                    ephemeral=True
                )
                return
            
            embed = create_embed(
                title="🎉 Order Completed!",
                description=f"Your order has been completed! Please rate your experience:",
                color=discord.Color.green(),
                message_type="rating"
            )
            await interaction.response.send_message(f"{owner.mention}", embed=embed, view=RatingView())
        except discord.NotFound:
            await interaction.response.send_message("This ticket channel no longer exists.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)


class PaymentMethodView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="INR (UPI/Paytm)", style=discord.ButtonStyle.green, custom_id="payment:inr")
    async def inr_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_payment_details(interaction, "inr")

    @discord.ui.button(label="LTC (Litecoin)", style=discord.ButtonStyle.blurple, custom_id="payment:ltc")
    async def ltc_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_payment_details(interaction, "ltc")


async def show_payment_details(interaction: discord.Interaction, method: str):
    if method == "inr":
        embed = create_embed(
            title="💳 INR Payment Details",
            description="Scan the QR code or use the wallet address below to make your payment.",
            color=discord.Color.green(),
            message_type="payment_info",
            fields=[
                ("Wallet Address", INR_WALLET_ADDRESS if INR_WALLET_ADDRESS else "Contact staff for details", False),
                ("Note", "Please send screenshot of payment after completion", False)
            ]
        )
        if INR_QR_URL:
            embed.set_image(url=INR_QR_URL)
    else:  # ltc
        embed = create_embed(
            title="💳 LTC (Litecoin) Payment Details",
            description="Scan the QR code or use the wallet address below to make your payment.",
            color=discord.Color.blue(),
            message_type="payment_info",
            fields=[
                ("Wallet Address", LTC_WALLET_ADDRESS if LTC_WALLET_ADDRESS else "Contact staff for details", False),
                ("Note", "Please send screenshot of payment after completion", False)
            ]
        )
        if LTC_QR_URL:
            embed.set_image(url=LTC_QR_URL)
    
    await interaction.response.edit_message(embed=embed, view=None)


class RatingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⭐", style=discord.ButtonStyle.red, custom_id="rating:1", emoji="😞")
    async def rate_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await submit_rating(interaction, 1)

    @discord.ui.button(label="⭐⭐", style=discord.ButtonStyle.red, custom_id="rating:2", emoji="😕")
    async def rate_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await submit_rating(interaction, 2)

    @discord.ui.button(label="⭐⭐⭐", style=discord.ButtonStyle.blurple, custom_id="rating:3", emoji="😐")
    async def rate_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await submit_rating(interaction, 3)

    @discord.ui.button(label="⭐⭐⭐⭐", style=discord.ButtonStyle.green, custom_id="rating:4", emoji="🙂")
    async def rate_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await submit_rating(interaction, 4)

    @discord.ui.button(label="⭐⭐⭐⭐⭐", style=discord.ButtonStyle.green, custom_id="rating:5", emoji="😄")
    async def rate_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await submit_rating(interaction, 5)


async def submit_rating(interaction: discord.Interaction, rating: int):
    channel = interaction.channel
    info = get_ticket_info(channel)
    
    if not info.get("owner_id"):
        await interaction.response.send_message("This is not a valid ticket.", ephemeral=True)
        return
    
    owner = interaction.guild.get_member(info["owner_id"])
    if not owner:
        await interaction.response.send_message("Ticket owner not found.", ephemeral=True)
        return
    
    # Send rating to rating channel
    if RATING_CHANNEL_ID:
        rating_channel = interaction.guild.get_channel(RATING_CHANNEL_ID)
        if rating_channel:
            stars = "⭐" * rating
            rating_embed = create_embed(
                title="⭐ New Rating Received",
                description=f"**User:** {owner.mention}\n**Rating:** {stars} ({rating}/5)\n**Ticket:** {channel.mention}",
                color=discord.Color.gold(),
                message_type="rating"
            )
            await rating_channel.send(embed=rating_embed)
    
    # Update response
    embed = create_embed(
        title="✅ Rating Submitted",
        description=f"Thank you for your rating! {stars} ({rating}/5)",
        color=discord.Color.green(),
        message_type="rating"
    )
    await interaction.response.edit_message(embed=embed, view=None)
    
    # Send confirmation in ticket
    await channel.send(f"{owner.mention} Thank you for your feedback! Your rating has been recorded.")


class ConfirmCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Yes, Close Ticket", style=discord.ButtonStyle.danger, custom_id="confirm:close")
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await close_ticket_final(interaction)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="cancel:close")
    async def cancel_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Close cancelled.", view=None, embed=None)


async def close_ticket_final(interaction: discord.Interaction):
    channel = interaction.channel
    info = get_ticket_info(channel)
    owner = interaction.guild.get_member(info["owner_id"])
    
    await interaction.response.edit_message(content="Closing ticket and saving transcript...", view=None, embed=None)

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
        claimed_member = interaction.guild.get_member(info['claimed_by'])
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
        log = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log:
            log_embed = create_embed(
                title="🔒 Ticket Closed",
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

    await channel.delete(reason=f"Closed by {interaction.user}")


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
    global BANNER_SETTINGS
    
    message_type = message_type.lower()
    
    if message_type == "all":
        # Toggle all settings
        new_state = not BANNER_SETTINGS["general"]
        for key in BANNER_SETTINGS:
            BANNER_SETTINGS[key] = new_state
            update_env_var(f"BANNER_{key.upper()}", "true" if new_state else "false")
        
        status = "enabled" if new_state else "disabled"
        embed = create_embed(
            title="✅ All Banner Settings Toggled",
            description=f"Banners are now **{status}** for all message types.",
            color=discord.Color.green()
        )
    elif message_type in BANNER_SETTINGS:
        # Toggle specific setting
        BANNER_SETTINGS[message_type] = not BANNER_SETTINGS[message_type]
        update_env_var(f"BANNER_{message_type.upper()}", "true" if BANNER_SETTINGS[message_type] else "false")
        
        status = "enabled" if BANNER_SETTINGS[message_type] else "disabled"
        embed = create_embed(
            title="✅ Banner Setting Toggled",
            description=f"Banners for **{message_type}** messages are now **{status}**.",
            color=discord.Color.green()
        )
    else:
        # Show available options
        available_types = ", ".join(BANNER_SETTINGS.keys()) + ", all"
        embed = create_embed(
            title="❌ Invalid Message Type",
            description=f"Available message types: {available_types}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
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
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can generate vouch requests.", ephemeral=True)
        return
    
    if VOUCH_CHANNEL_ID == 0:
        await interaction.response.send_message("Vouch channel not configured. Please set it with /setvouchchannel", ephemeral=True)
        return
    
    vouch_channel = interaction.guild.get_channel(VOUCH_CHANNEL_ID)
    if not vouch_channel:
        await interaction.response.send_message("Vouch channel not found.", ephemeral=True)
        return
    
    embed = create_embed(
        title="📝 Vouch Request",
        description=f"{user.mention}, please write your vouch message below:\n\n**Item:** {item}\n**Price:** {price}\n\nFormat: `+vouch @bot {item} {price}`",
        color=discord.Color.blue(),
        message_type="vouch"
    )
    
    await vouch_channel.send(embed=embed)
    
    response_embed = create_embed(
        title="✅ Vouch Request Generated",
        description=f"Vouch request sent to {vouch_channel.mention} for {user.mention}",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=response_embed, ephemeral=True)


@bot.event
async def on_message(message):
    # Process commands
    await bot.process_commands(message)
    
    # Check for vouch messages
    if message.channel.id == VOUCH_CHANNEL_ID and VOUCH_CHANNEL_ID != 0:
        if message.content.startswith("+vouch"):
            parts = message.content.split()
            if len(parts) >= 4:
                # Format: +vouch @bot item price
                try:
                    user = message.author
                    item = parts[2]
                    price = parts[3]
                    
                    # Add vouch to data
                    vouches = load_vouches()
                    user_id_str = str(user.id)
                    
                    if user_id_str not in vouches:
                        vouches[user_id_str] = {"vouches": []}
                    
                    vouches[user_id_str]["vouches"].append({
                        "item": item,
                        "price": price,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "message_id": message.id
                    })
                    
                    save_vouches(vouches)
                    
                    # React with checkmark
                    await message.add_reaction("✅")
                    
                except Exception as e:
                    print(f"Error processing vouch: {e}")


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


@bot.command(name="Payment")
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


@bot.tree.command(name="vouch", description="View vouch information for a user")
async def vouch_command(interaction: discord.Interaction, member: discord.Member = None):
    """View vouch information for a user"""
    if member is None:
        member = interaction.user
    
    vouches = load_vouches()
    user_id_str = str(member.id)
    
    if user_id_str not in vouches or not vouches[user_id_str].get("vouches"):
        embed = create_embed(
            title="📊 Vouch Information",
            description=f"{member.mention} has no vouches yet.",
            color=discord.Color.blue(),
            message_type="vouch"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
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
    await interaction.response.send_message(embed=embed, ephemeral=True)


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


@bot.tree.command(name="leaderboard", description="Show top vouched users")
async def leaderboard_command(interaction: discord.Interaction):
    """Show top vouched users"""
    vouches = load_vouches()
    
    if not vouches:
        await interaction.response.send_message("No vouch data available yet.", ephemeral=True)
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
        member = interaction.guild.get_member(entry["user_id"])
        member_name = member.name if member else f"User {entry['user_id']}"
        description += f"**{i}.** {member_name}\n   📊 {entry['total_vouches']} vouches\n\n"
    
    embed = create_embed(
        title="🏆 Vouch Leaderboard",
        description=description or "No vouches yet.",
        color=discord.Color.gold(),
        message_type="vouch"
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="myvouches", description="View your own vouches")
async def myvouches_slash_command(interaction: discord.Interaction):
    """View your own vouches"""
    vouches = load_vouches()
    user_id_str = str(interaction.user.id)
    
    if user_id_str not in vouches or not vouches[user_id_str].get("vouches"):
        embed = create_embed(
            title="📊 My Vouches",
            description="You have no vouches yet.",
            color=discord.Color.blue(),
            message_type="vouch"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
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
    await interaction.response.send_message(embed=embed, ephemeral=True)


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


if __name__ == "__main__":
    bot.run(TOKEN)
