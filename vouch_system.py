"""
New Vouch System Module
Staff generates vouch codes for users to paste in vouch channel
"""
import json
import os
import random
from datetime import datetime, timezone
import discord
from discord import app_commands
from config import SUPPORT_ROLE_ID, VOUCH_CHANNEL_ID
from embed_utils import create_embed


# Vouch data storage
VOUCHES_FILE = "vouches.json"


def load_vouches():
    if os.path.exists(VOUCHES_FILE):
        with open(VOUCHES_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_vouches(vouches):
    with open(VOUCHES_FILE, 'w') as f:
        json.dump(vouches, f, indent=4)


def generate_vouch_code():
    """Generate a 12-digit random numeric vouch code"""
    return ''.join([str(random.randint(0, 9)) for _ in range(12)])


class VouchModal(discord.ui.Modal, title="Generate Vouch Code"):
    """Modal for staff to enter item and price for vouch"""
    item = discord.ui.TextInput(
        label="Item",
        placeholder="What was purchased?",
        max_length=100,
        required=True
    )

    price = discord.ui.TextInput(
        label="Price",
        placeholder="e.g., ₹500 or $5",
        max_length=50,
        required=True
    )

    def __init__(self, user_id: int, channel_id: int):
        super().__init__()
        self.user_id = user_id
        self.channel_id = channel_id

    async def on_submit(self, interaction: discord.Interaction):
        """Generate vouch code and send to user"""
        is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
        if not is_staff:
            await interaction.response.send_message("Only staff can generate vouch codes.", ephemeral=True)
            return

        # Generate vouch code
        vouch_code = generate_vouch_code()
        
        # Format: +Legit | code | item | price
        # Display "Giveaway" if price is 0
        display_price = "Giveaway" if self.price.value.strip() == "0" else self.price.value
        vouch_message = f"+Legit | {vouch_code} | {self.item.value} | {display_price}"
        
        # Save vouch data
        vouches = load_vouches()
        vouches[vouch_code] = {
            "user_id": self.user_id,
            "staff_id": interaction.user.id,
            "item": self.item.value,
            "price": self.price.value,  # Store original price
            "display_price": display_price,  # Store display price for showing
            "channel_id": self.channel_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "used": False
        }
        save_vouches(vouches)
        
        # Send embed with copiable code
        embed = create_embed(
            title="✅ Vouch Code Generated",
            description=f"Vouch code generated for <@{self.user_id}>. Please copy the message below and paste it in the vouch channel.",
            color=discord.Color.green(),
            message_type="general",
            fields=[
                ("📝 Item", self.item.value, True),
                ("💰 Price", display_price, True),
                ("🔢 Vouch Code", f"```{vouch_message}```", False)
            ]
        )
        
        embed.add_field(
            name="📋 Instructions",
            value=f"1. Copy the code above\n2. Go to <#{VOUCH_CHANNEL_ID}>\n3. Paste the code\n4. Bot will react with ✅ if valid\n\nFormat: `+Legit | code | item | price`",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def process_vouch_message(message: discord.Message):
    """Process vouch messages in the vouch channel"""
    # Check if message is in vouch channel
    if message.channel.id != VOUCH_CHANNEL_ID:
        return
    
    # Validate vouch format: +Legit | code | item | price (with spaces) or +Legit|code|item|price (without spaces)
    content = message.content.strip()
    
    # Try format with spaces first
    if content.startswith("+Legit |"):
        parts = [part.strip() for part in content.split("|")]
        if len(parts) != 4:
            await message.delete()
            await message.channel.send(f"❌ {message.author.mention}, invalid vouch format. Please use the format: +Legit | code | item | price", delete_after=10)
            return
    # Try format without spaces (backward compatibility)
    elif content.startswith("+Legit|"):
        parts = content.split("|")
        if len(parts) != 4:
            await message.delete()
            await message.channel.send(f"❌ {message.author.mention}, invalid vouch format. Please use the format: +Legit | code | item | price", delete_after=10)
            return
    else:
        await message.delete()
        await message.channel.send(f"❌ {message.author.mention}, invalid vouch format. Please use the format: +Legit | code | item | price", delete_after=10)
        return
    
    try:
        vouch_code = parts[1]
        item = parts[2]
        price = parts[3]
        
        # Check if vouch code exists and is unused
        vouches = load_vouches()
        if vouch_code not in vouches:
            await message.delete()
            await message.channel.send(f"❌ {message.author.mention}, invalid vouch code. Please use a valid code generated by staff.", delete_after=10)
            return
        
        vouch_data = vouches[vouch_code]
        
        # Check if vouch is already used
        if vouch_data["used"]:
            await message.delete()
            await message.channel.send(f"❌ {message.author.mention}, this vouch code has already been used.", delete_after=10)
            return
        
        # Check if the user is the intended recipient
        if vouch_data["user_id"] != message.author.id:
            await message.delete()
            await message.channel.send(f"❌ {message.author.mention}, this vouch code is not for you.", delete_after=10)
            return
        
        # Mark vouch as used
        vouches[vouch_code]["used"] = True
        vouches[vouch_code]["used_at"] = datetime.now(timezone.utc).isoformat()
        vouches[vouch_code]["used_by"] = message.author.id
        save_vouches(vouches)
        
        # React with checkmark
        await message.add_reaction("✅")
        
        # Add to user's vouch count
        user_id_str = str(message.author.id)
        if user_id_str not in vouches:
            vouches[user_id_str] = {"total_vouches": 0, "vouch_history": []}
        
        vouches[user_id_str]["total_vouches"] += 1
        # Display "Giveaway" if price is 0
        display_price = "Giveaway" if price.strip() == "0" else price
        vouches[user_id_str]["vouch_history"].append({
            "item": item,
            "price": price,  # Store original price
            "display_price": display_price,  # Store display price
            "code": vouch_code,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        save_vouches(vouches)
        
    except Exception as e:
        print(f"Error processing vouch: {e}")
        await message.delete()
        await message.channel.send(f"❌ Error processing vouch: {str(e)}", delete_after=10)


async def handle_vouch_channel_message(message: discord.Message):
    """Handle messages in vouch channel - only allow vouch codes"""
    if message.channel.id != VOUCH_CHANNEL_ID:
        return
    
    # Allow bot messages
    if message.author.bot:
        return
    
    # Process the vouch message
    await process_vouch_message(message)


async def get_vouch_info(interaction: discord.Interaction, member: discord.Member = None):
    """Get vouch information for a user"""
    if member is None:
        member = interaction.user
    
    vouches = load_vouches()
    user_id_str = str(member.id)
    
    if user_id_str not in vouches or vouches[user_id_str].get("total_vouches", 0) == 0:
        embed = create_embed(
            title="📊 Vouch Information",
            description=f"{member.mention} has no vouches yet.",
            color=discord.Color.blue(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    user_data = vouches[user_id_str]
    total_vouches = user_data.get("total_vouches", 0)
    vouch_history = user_data.get("vouch_history", [])
    
    # Display "Giveaway" if price is 0, otherwise use display_price or price
    recent_vouches = "\n".join([
        f"✅ {v['item']} - {v.get('display_price', 'Giveaway' if v['price'].strip() == '0' else v['price'])}" 
        for v in vouch_history[-5:]
    ])
    
    embed = create_embed(
        title="📊 Vouch Information",
        description=f"**User:** {member.mention}\n**Total Vouches:** {total_vouches}",
        color=discord.Color.from_rgb(0, 255, 255),  # Aqua #00FFFF
        message_type="general",
        fields=[
            ("Recent Vouches", recent_vouches or "No recent vouches", False)
        ]
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def get_leaderboard(interaction: discord.Interaction):
    """Get vouch leaderboard"""
    vouches = load_vouches()
    
    if not vouches:
        await interaction.response.send_message("No vouch data available yet.", ephemeral=True)
        return
    
    # Calculate leaderboard
    leaderboard = []
    for user_id_str, data in vouches.items():
        if user_id_str.isdigit():  # Skip vouch code entries
            total_vouches = data.get("total_vouches", 0)
            if total_vouches > 0:
                leaderboard.append({
                    "user_id": int(user_id_str),
                    "total_vouches": total_vouches
                })
    
    # Sort by total vouches
    leaderboard.sort(key=lambda x: x["total_vouches"], reverse=True)
    top_10 = leaderboard[:10]
    
    if not top_10:
        await interaction.response.send_message("No vouches yet.", ephemeral=True)
        return
    
    description = ""
    for i, entry in enumerate(top_10, 1):
        member = interaction.guild.get_member(entry["user_id"])
        member_name = member.name if member else f"User {entry['user_id']}"
        description += f"**{i}.** {member_name}\n   📊 {entry['total_vouches']} vouches\n\n"
    
    embed = create_embed(
        title="🏆 Vouch Leaderboard",
        description=description,
        color=discord.Color.from_rgb(0, 255, 255),  # Aqua #00FFFF
        message_type="general"
    )
    await interaction.response.send_message(embed=embed)


async def vouch_button_handler(interaction: discord.Interaction):
    """Handle vouch button click - show modal for staff"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can generate vouch codes.", ephemeral=True)
        return
    
    # Get ticket owner from channel topic
    channel = interaction.channel
    from ticket_utils import get_ticket_info
    info = get_ticket_info(channel)
    
    if not info.get("owner_id"):
        await interaction.response.send_message("This is not a valid ticket.", ephemeral=True)
        return
    
    # Show modal
    modal = VouchModal(info["owner_id"], channel.id)
    await interaction.response.send_modal(modal)
