"""
Ticket control buttons module
"""
import discord
from config import SUPPORT_ROLE_ID
from embed_utils import create_embed
from ticket_utils import owner_tag, get_ticket_info


class SupportTicketControlView(discord.ui.View):
    """View for support tickets (without Order Done button)"""
    def __init__(self):
        super().__init__(timeout=None)

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
                    await interaction.response.edit_message(view=None)
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
            await interaction.response.edit_message(view=None)
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
                    await interaction.response.edit_message(view=None)
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
            await interaction.response.edit_message(view=None)
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

    @discord.ui.button(label="Order Done", emoji="✅", style=discord.ButtonStyle.green, custom_id="purchase:order_done")
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
            
            embed = create_embed(
                title="🎉 Order Completed!",
                description=f"Your order has been completed! Please rate your experience:",
                color=discord.Color.green(),
                message_type="rating"
            )
            await interaction.response.send_message(f"{owner.mention}", embed=embed, view=RatingView())
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
