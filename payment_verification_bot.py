"""
Payment Verification System for Discord Bot
Allows verifiers to accept/decline payments directly from Discord
"""
import discord
from discord import app_commands
from discord.ext import commands
import requests
import os
from dotenv import load_dotenv
from config import VERIFIER_ROLE_ID, PAYMENT_GATEWAY_URL, SUPPORT_ROLE_ID
from embed_utils import create_embed

load_dotenv()


class PaymentVerificationView(discord.ui.View):
    """View for payment verification buttons"""
    def __init__(self, payment_id: str):
        super().__init__(timeout=None)
        self.payment_id = payment_id

    @discord.ui.button(label="✅ Accept Payment", emoji="✅", style=discord.ButtonStyle.green, custom_id="payment:accept")
    async def accept_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Accept/verify payment"""
        # Check if user has verifier role
        is_verifier = any(r.id == VERIFIER_ROLE_ID for r in interaction.user.roles)
        is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
        
        if not (is_verifier or is_staff):
            await interaction.response.send_message(
                "You don't have permission to verify payments.",
                ephemeral=True
            )
            return
        
        # Show modal for verification details
        modal = PaymentAcceptModal(self.payment_id, interaction.user.id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="❌ Decline Payment", emoji="❌", style=discord.ButtonStyle.red, custom_id="payment:decline")
    async def decline_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Decline/reject payment"""
        # Check if user has verifier role
        is_verifier = any(r.id == VERIFIER_ROLE_ID for r in interaction.user.roles)
        is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
        
        if not (is_verifier or is_staff):
            await interaction.response.send_message(
                "You don't have permission to verify payments.",
                ephemeral=True
            )
            return
        
        # Show modal for rejection reason
        modal = PaymentDeclineModal(self.payment_id, interaction.user.id)
        await interaction.response.send_modal(modal)


class PaymentAcceptModal(discord.ui.Modal, title="Accept Payment"):
    """Modal for accepting payment with verification details"""
    upi_transaction_id = discord.ui.TextInput(
        label="UPI Transaction ID (from your bank/UPI app)",
        placeholder="Enter the transaction ID from your bank statement",
        max_length=50,
        required=True
    )

    notes = discord.ui.TextInput(
        label="Verification Notes (optional)",
        style=discord.TextStyle.long,
        placeholder="Add any verification notes...",
        max_length=200,
        required=False
    )

    def __init__(self, payment_id: str, verifier_id: int):
        super().__init__()
        self.payment_id = payment_id
        self.verifier_id = verifier_id

    async def on_submit(self, interaction: discord.Interaction):
        """Submit payment acceptance"""
        await interaction.response.defer(ephemeral=True)

        try:
            # Call payment gateway API
            response = requests.post(
                f"{PAYMENT_GATEWAY_URL}/api/verify_payment",
                json={
                    "payment_id": self.payment_id,
                    "upi_transaction_id": self.upi_transaction_id.value,
                    "verified_by": self.verifier_id,
                    "notes": self.notes.value
                },
                timeout=10
            )

            data = response.json()

            if data.get('success'):
                embed = create_embed(
                    title="✅ Payment Verified",
                    description=f"Payment {self.payment_id} has been verified successfully!",
                    color=discord.Color.green(),
                    message_type="general"
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                # Try to notify the user (if we have their user ID)
                # This would require fetching payment details first
            else:
                await interaction.followup.send(
                    f"Error verifying payment: {data.get('error', 'Unknown error')}",
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


class PaymentDeclineModal(discord.ui.Modal, title="Decline Payment"):
    """Modal for declining payment with reason"""
    reason = discord.ui.TextInput(
        label="Rejection Reason",
        style=discord.TextStyle.long,
        placeholder="Explain why this payment is being declined...",
        max_length=500,
        required=True
    )

    def __init__(self, payment_id: str, verifier_id: int):
        super().__init__()
        self.payment_id = payment_id
        self.verifier_id = verifier_id

    async def on_submit(self, interaction: discord.Interaction):
        """Submit payment rejection"""
        await interaction.response.defer(ephemeral=True)

        try:
            # Call payment gateway API
            response = requests.post(
                f"{PAYMENT_GATEWAY_URL}/api/reject_payment",
                json={
                    "payment_id": self.payment_id,
                    "notes": self.reason.value
                },
                timeout=10
            )

            data = response.json()

            if data.get('success'):
                embed = create_embed(
                    title="❌ Payment Declined",
                    description=f"Payment {self.payment_id} has been declined.",
                    color=discord.Color.red(),
                    message_type="general",
                    fields=[
                        ("Reason", self.reason.value, False)
                    ]
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(
                    f"Error declining payment: {data.get('error', 'Unknown error')}",
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


# Command to check payment status
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
            status = payment['status'].replace('_', ' ').capitalize()
            status_emoji = {
                'pending': '⏳',
                'awaiting verification': '⏳',
                'verified': '✅',
                'rejected': '❌',
                'expired': '⏰'
            }.get(payment['status'], '❓')

            embed = create_embed(
                title=f"📊 Payment Status - {status_emoji} {status}",
                description=f"**Payment ID:** {payment['payment_id']}\n**Amount:** ₹{payment['amount']}\n**Status:** {status}",
                color=discord.Color.blue() if payment['status'] in ['pending', 'awaiting_verification'] else (
                    discord.Color.green() if payment['status'] == 'verified' else discord.Color.red()
                ),
                message_type="general",
                fields=[
                    ("Order ID", payment['order_id'], True),
                    ("User", f"{payment['user_name']} (ID: {payment['user_id']})", True),
                    ("Created", payment['created_at'][:19], True)
                ]
            )

            if payment.get('utr_number'):
                embed.add_field(name="UTR Number", value=payment['utr_number'], inline=True)

            if payment.get('upi_transaction_id'):
                embed.add_field(name="UPI Transaction ID", value=payment['upi_transaction_id'], inline=True)

            if payment.get('expires_at'):
                embed.add_field(name="Expires At", value=payment['expires_at'][:19], inline=True)

            # Add verification buttons if payment is awaiting verification
            if payment['status'] == 'awaiting_verification':
                embed.add_field(
                    name="Actions",
                    value="Use the buttons below to verify or decline this payment",
                    inline=False
                )
                await interaction.followup.send(embed=embed, view=PaymentVerificationView(payment_id), ephemeral=True)
            else:
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


# Setup function to be called in ticket_bot.py
def setup_payment_verification(bot):
    """Setup payment verification system with bot"""
    
    # Add persistent view
    bot.add_view(PaymentVerificationView("placeholder"))

    # Add slash command for checking payment status
    @bot.tree.command(name="paymentstatus", description="Check payment status")
    @app_commands.describe(payment_id="Payment ID to check")
    async def payment_status(interaction: discord.Interaction, payment_id: str):
        """Check payment status"""
        await payment_status_command(interaction, payment_id)

    # Add slash command for verifiers to list pending payments
    @bot.tree.command(name="pendingpayments", description="List all pending payments (verifier only)")
    async def pending_payments(interaction: discord.Interaction):
        """List pending payments"""
        is_verifier = any(r.id == VERIFIER_ROLE_ID for r in interaction.user.roles)
        is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
        
        if not (is_verifier or is_staff):
            await interaction.response.send_message(
                "You don't have permission to view pending payments.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            response = requests.get(
                f"{PAYMENT_GATEWAY_URL}/api/payments?status=awaiting_verification&limit=10",
                timeout=10
            )
            
            data = response.json()
            
            if data.get('success'):
                payments = data['payments']
                
                if not payments:
                    await interaction.followup.send("No pending payments found.", ephemeral=True)
                    return
                
                description = "**Pending Payments Awaiting Verification:**\n\n"
                for payment in payments:
                    description += f"**ID:** {payment['payment_id']}\n"
                    description += f"**User:** {payment['user_name']}\n"
                    description += f"**Amount:** ₹{payment['amount']}\n"
                    description += f"**UTR:** {payment.get('utr_number', 'N/A')}\n"
                    description += f"**Submitted:** {payment['utr_submitted_at'][:19] if payment.get('utr_submitted_at') else 'N/A'}\n\n"
                
                embed = create_embed(
                    title="📋 Pending Payments",
                    description=description,
                    color=discord.Color.orange(),
                    message_type="general"
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(
                    f"Error fetching payments: {data.get('error', 'Unknown error')}",
                    ephemeral=True
                )
                
        except Exception as e:
            await interaction.followup.send(
                f"Error: {str(e)}",
                ephemeral=True
            )
