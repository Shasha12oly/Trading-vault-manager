"""
UPI Payment Gateway Discord Bot Integration
Integrates UPI payment gateway with existing Discord bot
"""
import discord
from discord import app_commands
from discord.ext import commands
import requests
import os
from dotenv import load_dotenv
from config import SUPPORT_ROLE_ID
from embed_utils import create_embed

load_dotenv()

# Payment Gateway URL (update this with your Render URL)
PAYMENT_GATEWAY_URL = os.getenv("PAYMENT_GATEWAY_URL", "http://localhost:5001")


class UPIPaymentModal(discord.ui.Modal, title="Create UPI Payment"):
    """Modal for creating UPI payments"""
    amount = discord.ui.TextInput(
        label="Amount (₹)",
        placeholder="Enter amount in INR",
        max_length=10,
        required=True
    )

    order_id = discord.ui.TextInput(
        label="Order ID",
        placeholder="e.g., CAPE-001",
        max_length=50,
        required=True
    )

    notes = discord.ui.TextInput(
        label="Additional Notes",
        style=discord.TextStyle.long,
        placeholder="Any additional information...",
        max_length=200,
        required=False
    )

    def __init__(self, user_id: int, user_name: str):
        super().__init__()
        self.user_id = user_id
        self.user_name = user_name

    async def on_submit(self, interaction: discord.Interaction):
        """Create payment via API"""
        await interaction.response.defer(ephemeral=True)

        try:
            # Call payment gateway API
            response = requests.post(
                f"{PAYMENT_GATEWAY_URL}/api/create_payment",
                json={
                    "order_id": self.order_id.value,
                    "user_id": self.user_id,
                    "user_name": self.user_name,
                    "amount": self.amount.value,
                    "currency": "INR",
                    "notes": self.notes.value
                },
                timeout=10
            )

            data = response.json()

            if data.get('success'):
                payment_id = data['payment_id']
                payment_url = f"{PAYMENT_GATEWAY_URL}/payment/{payment_id}"

                embed = create_embed(
                    title="💳 UPI Payment Created",
                    description=f"Your payment link has been generated!\n\n**Amount:** ₹{data['amount']}\n**Payment ID:** {payment_id}",
                    color=discord.Color.green(),
                    message_type="general",
                    fields=[
                        ("Payment Link", f"[Click here to pay]({payment_url})", False),
                        ("Instructions", "1. Click the link above\n2. Scan QR code or use UPI app\n3. Complete payment\n4. Wait for verification", False)
                    ]
                )

                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(
                    f"Error creating payment: {data.get('error', 'Unknown error')}",
                    ephemeral=True
                )

        except requests.exceptions.RequestException as e:
            await interaction.followup.send(
                f"Error connecting to payment gateway: {str(e)}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"Error: {str(e)}",
                ephemeral=True
            )


class UPIPaymentView(discord.ui.View):
    """View for UPI payment integration"""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💳 Create UPI Payment", emoji="💳", style=discord.ButtonStyle.green, custom_id="upi:create_payment")
    async def create_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show modal to create UPI payment"""
        modal = UPIPaymentModal(interaction.user.id, interaction.user.name)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="📊 Check Payment Status", emoji="📊", style=discord.ButtonStyle.blurple, custom_id="upi:check_status")
    async def check_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show modal to check payment status"""
        modal = PaymentStatusModal()
        await interaction.response.send_modal(modal)


class PaymentStatusModal(discord.ui.Modal, title="Check Payment Status"):
    """Modal for checking payment status"""
    payment_id = discord.ui.TextInput(
        label="Payment ID",
        placeholder="Enter payment ID (e.g., PAY2024...)",
        max_length=50,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Check payment status via API"""
        await interaction.response.defer(ephemeral=True)

        try:
            # Call payment gateway API
            response = requests.get(
                f"{PAYMENT_GATEWAY_URL}/api/payment/{self.payment_id.value}",
                timeout=10
            )

            data = response.json()

            if data.get('success'):
                payment = data['payment']
                status = payment['status'].capitalize()
                status_emoji = {
                    'pending': '⏳',
                    'verified': '✅',
                    'rejected': '❌'
                }.get(payment['status'], '❓')

                embed = create_embed(
                    title=f"📊 Payment Status - {status_emoji} {status}",
                    description=f"**Payment ID:** {payment['payment_id']}\n**Amount:** ₹{payment['amount']}\n**Status:** {status}",
                    color=discord.Color.blue() if payment['status'] == 'pending' else (
                        discord.Color.green() if payment['status'] == 'verified' else discord.Color.red()
                    ),
                    message_type="general",
                    fields=[
                        ("Order ID", payment['order_id'], True),
                        ("Created", payment['created_at'][:19], True),
                        ("Verified At", payment['verified_at'][:19] if payment['verified_at'] else 'N/A', True)
                    ]
                )

                if payment['upi_transaction_id']:
                    embed.add_field(name="UPI Transaction ID", value=payment['upi_transaction_id'], inline=False)

                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(
                    f"Payment not found: {data.get('error', 'Unknown error')}",
                    ephemeral=True
                )

        except requests.exceptions.RequestException as e:
            await interaction.followup.send(
                f"Error connecting to payment gateway: {str(e)}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"Error: {str(e)}",
                ephemeral=True
            )


# Add this view to your existing ticket controls
def add_upi_payment_to_purchase_view():
    """Add UPI payment button to purchase ticket controls"""
    from ticket_controls import PurchaseTicketControlView

    # Add UPI payment button to existing view
    original_init = PurchaseTicketControlView.__init__

    def new_init(self):
        original_init(self)
        # Add UPI payment button
        self.add_item(discord.ui.Button(
            label="💳 UPI Payment",
            emoji="💳",
            style=discord.ButtonStyle.green,
            custom_id="upi:create_payment"
        ))

    PurchaseTicketControlView.__init__ = new_init


# Setup function to be called in ticket_bot.py
def setup_upi_integration(bot):
    """Setup UPI payment integration with bot"""
    # Add persistent view
    bot.add_view(UPIPaymentView())

    # Add slash command for creating payments
    @bot.tree.command(name="upipayment", description="Create a UPI payment")
    async def upi_payment_command(interaction: discord.Interaction):
        """Create UPI payment"""
        modal = UPIPaymentModal(interaction.user.id, interaction.user.name)
        await interaction.response.send_modal(modal)

    # Add slash command for checking payment status
    @bot.tree.command(name="paymentstatus", description="Check payment status")
    @app_commands.describe(payment_id="Payment ID to check")
    async def payment_status_command(interaction: discord.Interaction, payment_id: str):
        """Check payment status"""
        await interaction.response.defer(ephemeral=True)

        try:
            response = requests.get(
                f"{PAYMENT_GATEWAY_URL}/api/payment/{payment_id}",
                timeout=10
            )

            data = response.json()

            if data.get('success'):
                payment = data['payment']
                status = payment['status'].capitalize()
                status_emoji = {
                    'pending': '⏳',
                    'verified': '✅',
                    'rejected': '❌'
                }.get(payment['status'], '❓')

                embed = create_embed(
                    title=f"📊 Payment Status - {status_emoji} {status}",
                    description=f"**Payment ID:** {payment['payment_id']}\n**Amount:** ₹{payment['amount']}\n**Status:** {status}",
                    color=discord.Color.blue() if payment['status'] == 'pending' else (
                        discord.Color.green() if payment['status'] == 'verified' else discord.Color.red()
                    ),
                    message_type="general"
                )

                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(
                    f"Payment not found: {data.get('error', 'Unknown error')}",
                    ephemeral=True
                )

        except Exception as e:
            await interaction.followup.send(
                f"Error: {str(e)}",
                ephemeral=True
            )
