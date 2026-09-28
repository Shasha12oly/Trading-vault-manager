"""
Vouch system module
"""
import json
import os
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


async def process_vouch_message(message: discord.Message):
    """Process vouch messages in the vouch channel"""
    if message.content.startswith("+vouch"):
        parts = message.content.split()
        if len(parts) >= 4:
            # Format: +vouch @bot item price
            try:
                user = message.author
                item = parts[2]
                price = parts[3]
                
                # Add vouch to data
                vouches = load_vouches()
                user_id_str = str(user.id)
                
                if user_id_str not in vouches:
                    vouches[user_id_str] = {"vouches": []}
                
                vouches[user_id_str]["vouches"].append({
                    "item": item,
                    "price": price,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "message_id": message.id
                })
                
                save_vouches(vouches)
                
                # React with checkmark
                await message.add_reaction("✅")
                
            except Exception as e:
                print(f"Error processing vouch: {e}")


async def get_vouch_info(interaction: discord.Interaction, member: discord.Member = None):
    """Get vouch information for a user"""
    if member is None:
        member = interaction.user
    
    vouches = load_vouches()
    user_id_str = str(member.id)
    
    if user_id_str not in vouches or not vouches[user_id_str].get("vouches"):
        embed = create_embed(
            title="📊 Vouch Information",
            description=f"{member.mention} has no vouches yet.",
            color=discord.Color.blue(),
            message_type="vouch"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    user_vouches = vouches[user_id_str]
    vouch_list = user_vouches["vouches"]
    
    embed = create_embed(
        title="📊 Vouch Information",
        description=f"**User:** {member.mention}\n**Total Vouches:** {len(vouch_list)}",
        color=discord.Color.gold(),
        message_type="vouch",
        fields=[
            ("Recent Vouches", "\n".join([f"✅ {v['item']} - {v['price']}" for v in vouch_list[-5:]]), False)
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
        if data.get("vouches"):
            leaderboard.append({
                "user_id": int(user_id_str),
                "total_vouches": len(data["vouches"])
            })
    
    # Sort by total vouches
    leaderboard.sort(key=lambda x: x["total_vouches"], reverse=True)
    top_10 = leaderboard[:10]
    
    description = ""
    for i, entry in enumerate(top_10, 1):
        member = interaction.guild.get_member(entry["user_id"])
        member_name = member.name if member else f"User {entry['user_id']}"
        description += f"**{i}.** {member_name}\n   📊 {entry['total_vouches']} vouches\n\n"
    
    embed = create_embed(
        title="🏆 Vouch Leaderboard",
        description=description or "No vouches yet.",
        color=discord.Color.gold(),
        message_type="vouch"
    )
    await interaction.response.send_message(embed=embed)


async def generate_vouch_request(interaction: discord.Interaction, user: discord.Member, item: str, price: str):
    """Generate a vouch request for a user"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can generate vouch requests.", ephemeral=True)
        return
    
    if VOUCH_CHANNEL_ID == 0:
        await interaction.response.send_message("Vouch channel not configured. Please set it with /setvouchchannel", ephemeral=True)
        return
    
    vouch_channel = interaction.guild.get_channel(VOUCH_CHANNEL_ID)
    if not vouch_channel:
        await interaction.response.send_message("Vouch channel not found.", ephemeral=True)
        return
    
    embed = create_embed(
        title="📝 Vouch Request",
        description=f"{user.mention}, please write your vouch message below:\n\n**Item:** {item}\n**Price:** {price}\n\nFormat: `+vouch @bot {item} {price}`",
        color=discord.Color.blue(),
        message_type="vouch"
    )
    
    await vouch_channel.send(embed=embed)
    
    response_embed = create_embed(
        title="✅ Vouch Request Generated",
        description=f"Vouch request sent to {vouch_channel.mention} for {user.mention}",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=response_embed, ephemeral=True)
