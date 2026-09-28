"""
Support ticket system module
"""
import discord
from discord import app_commands
from config import CATEGORY_ID, SUPPORT_ROLE_ID
from embed_utils import create_embed
from ticket_utils import owner_tag


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
        from ticket_management import create_ticket  # Import here to avoid circular dependency
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
