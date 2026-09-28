"""
Rating system module
"""
import discord
from config import RATING_CHANNEL_ID
from embed_utils import create_embed
from ticket_utils import get_ticket_info


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
    stars = "⭐" * rating
    embed = create_embed(
        title="✅ Rating Submitted",
        description=f"Thank you for your rating! {stars} ({rating}/5)",
        color=discord.Color.green(),
        message_type="rating"
    )
    await interaction.response.edit_message(embed=embed, view=None)
    
    # Send confirmation in ticket
    await channel.send(f"{owner.mention} Thank you for your feedback! Your rating has been recorded.")
