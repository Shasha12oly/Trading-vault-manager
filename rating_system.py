"""
Professional Rating system module with optional text reviews
"""
import discord
from discord import app_commands
from datetime import datetime, timezone
from config import RATING_CHANNEL_ID
from embed_utils import create_embed
from ticket_utils import get_ticket_info


class RatingModal(discord.ui.Modal, title="Leave a Review"):
    """Modal for optional text review"""
    review = discord.ui.TextInput(
        label="Your Review (Optional)",
        style=discord.TextStyle.long,
        placeholder="Share your experience with our service...",
        max_length=500,
        required=False
    )

    def __init__(self, rating: int):
        super().__init__()
        self.rating = rating

    async def on_submit(self, interaction: discord.Interaction):
        await submit_rating_with_review(interaction, self.rating, self.review.value)


class RatingView(discord.ui.View):
    """Professional rating view with star buttons"""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⭐", style=discord.ButtonStyle.red, custom_id="rating:1", emoji="😞")
    async def rate_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RatingModal(1)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="⭐⭐", style=discord.ButtonStyle.red, custom_id="rating:2", emoji="😕")
    async def rate_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RatingModal(2)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="⭐⭐⭐", style=discord.ButtonStyle.blurple, custom_id="rating:3", emoji="😐")
    async def rate_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RatingModal(3)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="⭐⭐⭐⭐", style=discord.ButtonStyle.green, custom_id="rating:4", emoji="🙂")
    async def rate_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RatingModal(4)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="⭐⭐⭐⭐⭐", style=discord.ButtonStyle.green, custom_id="rating:5", emoji="😄")
    async def rate_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RatingModal(5)
        await interaction.response.send_modal(modal)


def get_rating_emoji(rating: int) -> str:
    """Get appropriate emoji based on rating"""
    if rating == 1:
        return "😞"
    elif rating == 2:
        return "😕"
    elif rating == 3:
        return "😐"
    elif rating == 4:
        return "🙂"
    elif rating == 5:
        return "😄"
    return "⭐"


def get_rating_color(rating: int) -> discord.Color:
    """Get appropriate color based on rating"""
    if rating <= 2:
        return discord.Color.red()
    elif rating == 3:
        return discord.Color.blue()
    else:
        return discord.Color.green()


def get_rating_description(rating: int) -> str:
    """Get description based on rating"""
    descriptions = {
        1: "Poor - We're sorry to hear you had a bad experience.",
        2: "Fair - We'll work to improve our service.",
        3: "Good - Thanks for your feedback!",
        4: "Very Good - We're glad you had a positive experience!",
        5: "Excellent - Thank you for the amazing review!"
    }
    return descriptions.get(rating, "Thanks for your rating!")


async def submit_rating_with_review(interaction: discord.Interaction, rating: int, review: str = None):
    """Submit rating with optional text review"""
    channel = interaction.channel
    info = get_ticket_info(channel)
    
    if not info.get("owner_id"):
        await interaction.response.send_message("This is not a valid ticket.", ephemeral=True)
        return
    
    owner = interaction.guild.get_member(info["owner_id"])
    if not owner:
        await interaction.response.send_message("Ticket owner not found.", ephemeral=True)
        return
    
    # Create stars display
    stars = "⭐" * rating
    empty_stars = "☆" * (5 - rating)
    star_display = f"{stars}{empty_stars}"
    
    # Get rating details
    emoji = get_rating_emoji(rating)
    color = get_rating_color(rating)
    description = get_rating_description(rating)
    
    # Send professional rating to rating channel
    if RATING_CHANNEL_ID:
        rating_channel = interaction.guild.get_channel(RATING_CHANNEL_ID)
        if rating_channel:
            # Create professional rating embed
            rating_embed = discord.Embed(
                title=f"{emoji} New Customer Review",
                description=f"{star_display} **{rating}/5 Stars**",
                color=color,
                timestamp=datetime.now(timezone.utc)
            )
            
            rating_embed.add_field(name="Customer", value=f"{owner.mention} ({owner.name})", inline=True)
            rating_embed.add_field(name="Ticket", value=channel.mention, inline=True)
            rating_embed.add_field(name="Rating", value=f"{rating}/5 - {description}", inline=False)
            
            if review:
                rating_embed.add_field(name="📝 Review", value=f"*{review}*", inline=False)
            
            rating_embed.set_footer(text=f"Rating ID: {interaction.id} • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
            rating_embed.set_thumbnail(url=owner.avatar.url if owner.avatar else None)
            
            await rating_channel.send(embed=rating_embed)
    
    # Update the original message with professional confirmation
    confirm_embed = discord.Embed(
        title="✅ Review Submitted Successfully",
        description=f"{emoji} {star_display} **{rating}/5 Stars**\n\n{description}",
        color=discord.Color.green(),
        timestamp=datetime.now(timezone.utc)
    )
    
    confirm_embed.add_field(name="Thank You!", value="Your feedback helps us improve our service.", inline=False)
    if review:
        confirm_embed.add_field(name="Your Review", value=f"*{review}*", inline=False)
    
    confirm_embed.set_footer(text="Trading Vault • Professional Service")
    
    await interaction.response.edit_message(embed=confirm_embed, view=None)
    
    # Send professional confirmation in ticket
    ticket_confirm = discord.Embed(
        title="🎉 Order Completed & Reviewed",
        description=f"{owner.mention} has rated their experience: {star_display} ({rating}/5)",
        color=discord.Color.from_rgb(0, 255, 255),  # Aqua #00FFFF
        timestamp=datetime.now(timezone.utc)
    )
    
    if review:
        ticket_confirm.add_field(name="Customer Review", value=f"*{review}*", inline=False)
    
    ticket_confirm.add_field(name="Status", value="✅ Completed", inline=True)
    ticket_confirm.set_footer(text="Thank you for choosing Trading Vault!")
    
    await channel.send(embed=ticket_confirm)
