"""
Payment system module
"""
import discord
from config import INR_QR_URL, LTC_QR_URL, INR_WALLET_ADDRESS, LTC_WALLET_ADDRESS
from embed_utils import create_embed


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
