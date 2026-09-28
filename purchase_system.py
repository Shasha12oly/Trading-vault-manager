"""
Purchase ticket system module
"""
import discord
from config import CATEGORY_ID, SUPPORT_ROLE_ID, INR_QR_URL, LTC_QR_URL, INR_WALLET_ADDRESS, LTC_WALLET_ADDRESS
from embed_utils import create_embed
from ticket_utils import owner_tag


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
    """Process a purchase ticket"""
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

    # Import here to avoid circular dependency
    from ticket_controls import PurchaseTicketControlView

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
        view=PurchaseTicketControlView()
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
