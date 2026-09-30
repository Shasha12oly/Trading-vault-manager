"""
Ticket control buttons module
"""
import discord
from config import SUPPORT_ROLE_ID
from embed_utils import create_embed
from ticket_utils import owner_tag, get_ticket_info


class VouchButton(discord.ui.Button):
    """Vouch button that can be added to different ticket views"""
    def __init__(self):
        super().__init__(label="📝 Vouch", emoji="📝", style=discord.ButtonStyle.blurple, custom_id="ticket:vouch")

    async def callback(self, interaction: discord.Interaction):
        """Generate vouch code for user"""
        try:
            from vouch_system import vouch_button_handler
            await vouch_button_handler(interaction)
        except Exception as e:
            await interaction.response.send_message(f"Error generating vouch: {str(e)}", ephemeral=True)


class SupportTicketControlView(discord.ui.View):
    """View for support tickets (without Order Done button)"""
    def __init__(self, category: str = "general"):
        super().__init__(timeout=None)
        self.category = category
        # Only add vouch button for giveaway claim tickets
        if category == "giveaway":
            self.add_item(VouchButton())

    @discord.ui.button(label="Claim Ticket", emoji="✋", style=discord.ButtonStyle.green, custom_id="support:claim")
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
                    await interaction.response.edit_message(view=self)
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
            await interaction.response.edit_message(view=self)
            await channel.send(embed=embed)
        except discord.NotFound:
            await interaction.response.send_message("This ticket channel no longer exists.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Close Ticket", emoji="🔒", style=discord.ButtonStyle.red, custom_id="support:close")
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


class PurchaseTicketControlView(discord.ui.View):
    """View for purchase tickets (with Order Done button)"""
    def __init__(self):
        super().__init__(timeout=None)
        # Add vouch button for all purchase tickets
        self.add_item(VouchButton())

    @discord.ui.button(label="Claim Ticket", emoji="✋", style=discord.ButtonStyle.green, custom_id="purchase:claim")
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
                    await interaction.response.edit_message(view=self)
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
            await interaction.response.edit_message(view=self)
            await channel.send(embed=embed)
        except discord.NotFound:
            await interaction.response.send_message("This ticket channel no longer exists.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Close Ticket", emoji="🔒", style=discord.ButtonStyle.red, custom_id="purchase:close")
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

    @discord.ui.button(label="💳 Payment", emoji="💳", style=discord.ButtonStyle.blurple, custom_id="purchase:payment")
    async def payment_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show payment options"""
        try:
            from payment_system import PaymentMethodView
            from embed_utils import create_embed
            
            embed = create_embed(
                title="💳 Select Payment Method",
                description="Choose your preferred payment method to see the QR code and wallet details.",
                color=discord.Color.from_rgb(0, 255, 255),  # Aqua #00FFFF
                message_type="payment_info"
            )
            await interaction.response.send_message(embed=embed, view=PaymentMethodView())
        except Exception as e:
            await interaction.response.send_message(f"Error showing payment options: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Order Complete", emoji="✅", style=discord.ButtonStyle.green, custom_id="purchase:order_done")
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
            
            # Import here to avoid circular dependency
            from rating_system import RatingView
            from datetime import datetime, timezone
            
            # Create professional rating request embed
            rating_request = discord.Embed(
                title="🎉 Order Completed Successfully!",
                description="Your order has been completed and delivered. We'd love to hear about your experience!",
                color=discord.Color.from_rgb(0, 255, 255),  # Aqua #00FFFF
                timestamp=datetime.now(timezone.utc)
            )
            
            rating_request.add_field(
                name="⭐ Rate Your Experience",
                value="Please take a moment to rate our service. Your feedback helps us improve!",
                inline=False
            )
            
            rating_request.add_field(
                name="📝 Leave a Review",
                value="You can also share your detailed experience in the review (optional).",
                inline=False
            )
            
            rating_request.add_field(
                name="💬 Questions?",
                value="If you have any questions or concerns, feel free to ask in this ticket.",
                inline=False
            )
            
            rating_request.set_footer(text="Trading Vault • Professional Service")
            rating_request.set_thumbnail(url=owner.avatar.url if owner.avatar else None)
            
            await interaction.response.send_message(f"{owner.mention}", embed=rating_request, view=RatingView())
        except discord.NotFound:
            await interaction.response.send_message("This ticket channel no longer exists.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)


class ConfirmCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Yes, Close Ticket", style=discord.ButtonStyle.danger, custom_id="confirm:close")
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        from ticket_close import close_ticket_final
        await close_ticket_final(interaction)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="cancel:close")
    async def cancel_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Close cancelled.", view=None, embed=None)
