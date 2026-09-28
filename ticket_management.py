"""
Ticket management module - handles creation of both support and purchase tickets
"""
import discord
from config import CATEGORY_ID, SUPPORT_ROLE_ID
from embed_utils import create_embed
from ticket_utils import owner_tag


async def create_ticket(interaction: discord.Interaction, category: str, priority: str, subject: str, description: str, from_modal: bool = False):
    """Create a support ticket"""
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

    # Import here to avoid circular dependency
    from ticket_controls import SupportTicketControlView

    # Send welcome message
    await channel.send(
        content=f"{interaction.user.mention} {support_role.mention}",
        embed=embed,
        view=SupportTicketControlView()
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
