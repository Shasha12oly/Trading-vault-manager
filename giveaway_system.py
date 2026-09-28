"""
Giveaway system module - Full giveaway hosting functionality
"""
import discord
from discord import app_commands
from datetime import datetime, timezone, timedelta
import random
from config import SUPPORT_ROLE_ID
from embed_utils import create_embed


# Giveaway data storage
GIVEAWAYS = {}


class GiveawayModal(discord.ui.Modal, title="Create Giveaway"):
    prize = discord.ui.TextInput(
        label="Prize",
        placeholder="What are you giving away?",
        max_length=100,
        required=True
    )

    winners_count = discord.ui.TextInput(
        label="Number of Winners",
        placeholder="e.g., 1",
        max_length=5,
        required=True
    )

    duration = discord.ui.TextInput(
        label="Duration (in minutes)",
        placeholder="e.g., 60 for 1 hour",
        max_length=10,
        required=True
    )

    description = discord.ui.TextInput(
        label="Description (optional)",
        style=discord.TextStyle.long,
        placeholder="Additional details about the giveaway...",
        max_length=500,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await create_giveaway(
            interaction,
            self.prize.value,
            self.winners_count.value,
            self.duration.value,
            self.description.value
        )


class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id: str):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id

    @discord.ui.button(label="🎉 Enter Giveaway", style=discord.ButtonStyle.green, custom_id="giveaway:enter")
    async def enter_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        await enter_giveaway(interaction, self.giveaway_id)


async def create_giveaway(interaction: discord.Interaction, prize: str, winners_count: str, duration: str, description: str = None):
    """Create a new giveaway"""
    try:
        winners_count = int(winners_count)
        duration_minutes = int(duration)
    except ValueError:
        await interaction.followup.send("Invalid winners count or duration. Please use numbers.", ephemeral=True)
        return

    if winners_count < 1:
        await interaction.followup.send("Winners count must be at least 1.", ephemeral=True)
        return

    if duration_minutes < 1:
        await interaction.followup.send("Duration must be at least 1 minute.", ephemeral=True)
        return

    end_time = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
    giveaway_id = f"{interaction.channel.id}-{datetime.now(timezone.utc).timestamp()}"

    GIVEAWAYS[giveaway_id] = {
        "prize": prize,
        "winners_count": winners_count,
        "end_time": end_time,
        "description": description,
        "host": interaction.user.id,
        "channel": interaction.channel.id,
        "participants": [],
        "message_id": None,
        "ended": False
    }

    embed = create_embed(
        title="🎉 GIVEAWAY TIME! 🎉",
        description=f"**Prize:** {prize}\n**Winners:** {winners_count}\n**Ends:** <t:{int(end_time.timestamp())}:R>\n**Hosted by:** {interaction.user.mention}",
        color=discord.Color.gold(),
        message_type="general",
        fields=[
            ("Participants", "0", True),
            ("Status", "🟢 Active", True)
        ]
    )

    if description:
        embed.add_field(name="Description", value=description, inline=False)

    view = GiveawayView(giveaway_id)
    message = await interaction.channel.send(embed=embed, view=view)
    
    GIVEAWAYS[giveaway_id]["message_id"] = message.id

    await interaction.followup.send(f"Giveaway created successfully! Ends in {duration_minutes} minutes.", ephemeral=True)


async def enter_giveaway(interaction: discord.Interaction, giveaway_id: str):
    """Enter a giveaway"""
    if giveaway_id not in GIVEAWAYS:
        await interaction.response.send_message("This giveaway no longer exists.", ephemeral=True)
        return

    giveaway = GIVEAWAYS[giveaway_id]

    if giveaway["ended"]:
        await interaction.response.send_message("This giveaway has already ended.", ephemeral=True)
        return

    if datetime.now(timezone.utc) > giveaway["end_time"]:
        # Will be handled by the giveaway checker
        await interaction.response.send_message("This giveaway has ended.", ephemeral=True)
        return

    if interaction.user.id in giveaway["participants"]:
        await interaction.response.send_message("You have already entered this giveaway!", ephemeral=True)
        return

    giveaway["participants"].append(interaction.user.id)

    # Update the embed
    channel = interaction.guild.get_channel(giveaway["channel"])
    message = await channel.fetch_message(giveaway["message_id"])
    
    embed = message.embeds[0]
    embed.set_field_at(0, name="Participants", value=str(len(giveaway["participants"])), inline=True)
    await message.edit(embed=embed)

    await interaction.response.send_message("You have successfully entered the giveaway! 🎉", ephemeral=True)


async def end_giveaway_logic(giveaway_id: str, bot):
    """End a giveaway and pick winners"""
    if giveaway_id not in GIVEAWAYS:
        return

    giveaway = GIVEAWAYS[giveaway_id]
    giveaway["ended"] = True

    channel = bot.get_channel(giveaway["channel"])
    if not channel:
        return

    message = await channel.fetch_message(giveaway["message_id"])
    
    if not giveaway["participants"]:
        embed = create_embed(
            title="🎉 Giveaway Ended",
            description=f"**Prize:** {giveaway['prize']}\n\nNo one entered the giveaway! 😢",
            color=discord.Color.red(),
            message_type="general"
        )
        await message.edit(embed=embed, view=None)
        del GIVEAWAYS[giveaway_id]
        return

    # Pick winners
    winners = random.sample(giveaway["participants"], min(giveaway["winners_count"], len(giveaway["participants"])))
    winner_mentions = [f"<@{winner_id}>" for winner_id in winners]

    embed = create_embed(
        title="🎉 Giveaway Ended",
        description=f"**Prize:** {giveaway['prize']}\n**Winners:** {', '.join(winner_mentions)}\n**Total Participants:** {len(giveaway['participants'])}",
        color=discord.Color.green(),
        message_type="general"
    )

    await message.edit(embed=embed, view=None)
    await channel.send(f"🎉 Congratulations {', '.join(winner_mentions)}! You won the giveaway: **{giveaway['prize']}**!")

    del GIVEAWAYS[giveaway_id]


async def check_giveaways(bot):
    """Check for ended giveaways and end them"""
    current_time = datetime.now(timezone.utc)
    to_end = []

    for giveaway_id, giveaway in GIVEAWAYS.items():
        if not giveaway["ended"] and current_time > giveaway["end_time"]:
            to_end.append(giveaway_id)

    for giveaway_id in to_end:
        await end_giveaway_logic(giveaway_id, bot)


# Helper functions for commands
async def giveaway_command(interaction: discord.Interaction):
    """Create a new giveaway"""
    modal = GiveawayModal()
    await interaction.response.send_modal(modal)


async def endgiveaway_command(interaction: discord.Interaction, message_id: str):
    """End a giveaway manually"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can end giveaways.", ephemeral=True)
        return

    # Find the giveaway by message ID
    for giveaway_id, giveaway in GIVEAWAYS.items():
        if str(giveaway["message_id"]) == message_id:
            await end_giveaway_logic(giveaway_id, interaction.client)
            await interaction.response.send_message("Giveaway ended successfully!", ephemeral=True)
            return

    await interaction.response.send_message("Giveaway not found with that message ID.", ephemeral=True)


async def reroll_command(interaction: discord.Interaction, message_id: str):
    """Reroll a giveaway winner"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can reroll giveaways.", ephemeral=True)
        return

    # This would need to store ended giveaways for reroll functionality
    await interaction.response.send_message("Reroll functionality coming soon!", ephemeral=True)
