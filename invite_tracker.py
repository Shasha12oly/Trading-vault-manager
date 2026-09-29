"""
Invite tracker module - Track who invited whom
"""
import discord
from discord import app_commands
import json
import os
from datetime import datetime, timezone
from config import SUPPORT_ROLE_ID, INVITE_ANNOUNCEMENT_CHANNEL_ID
from embed_utils import create_embed

# Invite data storage
INVITES_FILE = "invites.json"


def load_invites():
    if os.path.exists(INVITES_FILE):
        with open(INVITES_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_invites(invites):
    with open(INVITES_FILE, 'w') as f:
        json.dump(invites, f, indent=4)


# Track invites per server
SERVER_INVITES = {}
SERVER_DATA = {}


async def track_invites(guild):
    """Track all invites in a server"""
    try:
        invites = {}
        async for invite in guild.invites():
            invites[invite.code] = {
                "uses": invite.uses,
                "inviter_id": invite.inviter.id if invite.inviter else None,
                "url": invite.url
            }
        SERVER_INVITES[guild.id] = invites
        print(f"Tracked {len(invites)} invites for {guild.name}")
        return invites
    except discord.Forbidden:
        print(f"Missing permissions to track invites for {guild.name}")
        return {}
    except Exception as e:
        print(f"Error tracking invites for {guild.name}: {e}")
        return {}


async def check_invite_join(member):
    """Check who invited a new member"""
    guild = member.guild
    
    # Get current invites
    current_invites = await track_invites(guild)
    
    # Get old invites
    old_invites = SERVER_INVITES.get(guild.id, {})
    
    # Find which invite was used
    invite_code = None
    inviter_id = None
    
    for code, data in current_invites.items():
        if code in old_invites:
            if data["uses"] > old_invites[code]["uses"]:
                invite_code = code
                inviter_id = data["inviter_id"]
                break
        else:
            # New invite created
            if data["uses"] > 0:
                invite_code = code
                inviter_id = data["inviter_id"]
                break
    
    # Store the invite data
    server_data = load_invites()
    if str(guild.id) not in server_data:
        server_data[str(guild.id)] = {"invites": {}, "members": {}}
    
    server_data[str(guild.id)]["members"][str(member.id)] = {
        "inviter_id": inviter_id,
        "invite_code": invite_code,
        "joined_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Update inviter stats
    if inviter_id:
        if str(inviter_id) not in server_data[str(guild.id)]["invites"]:
            server_data[str(guild.id)]["invites"][str(inviter_id)] = {
                "total_invites": 0,
                "valid_invites": 0,
                "invalid_invites": 0
            }
        server_data[str(guild.id)]["invites"][str(inviter_id)]["total_invites"] += 1
        server_data[str(guild.id)]["invites"][str(inviter_id)]["valid_invites"] += 1
        print(f"User {member.name} invited by {inviter_id} using code {invite_code}")
        
        # Send announcement to invite channel if configured
        if INVITE_ANNOUNCEMENT_CHANNEL_ID:
            try:
                invite_channel = guild.get_channel(INVITE_ANNOUNCEMENT_CHANNEL_ID)
                if invite_channel:
                    inviter = guild.get_member(inviter_id)
                    inviter_name = inviter.name if inviter else f"User {inviter_id}"
                    inviter_mention = inviter.mention if inviter else f"<@{inviter_id}>"
                    
                    total_invites = server_data[str(guild.id)]["invites"][str(inviter_id)]["total_invites"]
                    
                    announcement_message = f"{member.mention} has been invited by {inviter_mention} and has now {total_invites} invites."
                    await invite_channel.send(announcement_message)
            except Exception as e:
                print(f"Error sending invite announcement: {e}")
    else:
        print(f"User {member.name} joined without tracking (no invite code found)")
    
    save_invites(server_data)
    
    return inviter_id, invite_code


async def check_invite_leave(member):
    """Handle member leaving - mark invite as potentially invalid"""
    server_data = load_invites()
    guild_id = str(member.guild.id)
    
    if guild_id in server_data and str(member.id) in server_data[guild_id]["members"]:
        inviter_id = server_data[guild_id]["members"][str(member.id)]["inviter_id"]
        
        if inviter_id:
            if str(inviter_id) in server_data[guild_id]["invites"]:
                server_data[guild_id]["invites"][str(inviter_id)]["invalid_invites"] += 1
        
        del server_data[guild_id]["members"][str(member.id)]
        save_invites(server_data)


async def get_invite_stats(interaction: discord.Interaction, member: discord.Member = None):
    """Get invite statistics for a member"""
    if member is None:
        member = interaction.user
    
    server_data = load_invites()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in server_data or str(member.id) not in server_data[guild_id]["invites"]:
        embed = create_embed(
            title="📊 Invite Statistics",
            description=f"{member.mention} has no invite data yet.",
            color=discord.Color.blue(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    stats = server_data[guild_id]["invites"][str(member.id)]
    
    embed = create_embed(
        title="📊 Invite Statistics",
        description=f"**User:** {member.mention}",
        color=discord.Color.gold(),
        message_type="general",
        fields=[
            ("Total Invites", str(stats["total_invites"]), True),
            ("Valid Invites", str(stats["valid_invites"]), True),
            ("Left Members", str(stats["invalid_invites"]), True)
        ]
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def get_invite_leaderboard(interaction: discord.Interaction):
    """Get invite leaderboard"""
    server_data = load_invites()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in server_data or not server_data[guild_id]["invites"]:
        await interaction.response.send_message("No invite data available yet.", ephemeral=True)
        return
    
    # Calculate leaderboard
    leaderboard = []
    for user_id_str, stats in server_data[guild_id]["invites"].items():
        leaderboard.append({
            "user_id": int(user_id_str),
            "total_invites": stats["total_invites"],
            "valid_invites": stats["valid_invites"]
        })
    
    # Sort by valid invites
    leaderboard.sort(key=lambda x: x["valid_invites"], reverse=True)
    top_10 = leaderboard[:10]
    
    description = ""
    for i, entry in enumerate(top_10, 1):
        member = interaction.guild.get_member(entry["user_id"])
        member_name = member.name if member else f"User {entry['user_id']}"
        description += f"**{i}.** {member_name}\n   📊 {entry['valid_invites']} valid invites ({entry['total_invites']} total)\n\n"
    
    embed = create_embed(
        title="🏆 Invite Leaderboard",
        description=description or "No invites yet.",
        color=discord.Color.gold(),
        message_type="general"
    )
    await interaction.response.send_message(embed=embed)


async def get_inviter_info(interaction: discord.Interaction, member: discord.Member = None):
    """Get who invited a member"""
    if member is None:
        member = interaction.user
    
    server_data = load_invites()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in server_data or str(member.id) not in server_data[guild_id]["members"]:
        embed = create_embed(
            title="🔍 Inviter Information",
            description=f"Could not find inviter information for {member.mention}.",
            color=discord.Color.red(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    member_data = server_data[guild_id]["members"][str(member.id)]
    inviter_id = member_data["inviter_id"]
    
    if inviter_id:
        inviter = interaction.guild.get_member(inviter_id)
        inviter_name = inviter.name if inviter else f"User {inviter_id}"
        
        embed = create_embed(
            title="🔍 Inviter Information",
            description=f"**Member:** {member.mention}\n**Invited by:** {inviter.mention if inviter else inviter_name}\n**Invite Code:** {member_data['invite_code'] or 'Unknown'}\n**Joined:** {member_data['joined_at']}",
            color=discord.Color.green(),
            message_type="general"
        )
    else:
        embed = create_embed(
            title="🔍 Inviter Information",
            description=f"**Member:** {member.mention}\n**Invited by:** Unknown (joined via direct link or vanity URL)",
            color=discord.Color.orange(),
            message_type="general"
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


# Command wrappers
async def invitestats_command(interaction: discord.Interaction, member: discord.Member = None):
    """Get invite statistics for a member"""
    await get_invite_stats(interaction, member)


async def inviteleaderboard_command(interaction: discord.Interaction):
    """Get invite leaderboard"""
    await get_invite_leaderboard(interaction)


async def whoinvited_command(interaction: discord.Interaction, member: discord.Member = None):
    """Get who invited a member"""
    await get_inviter_info(interaction, member)


async def setinvitechannel_command(interaction: discord.Interaction, channel: discord.TextChannel):
    """Set the invite announcement channel"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can set invite announcement channels.", ephemeral=True)
        return
    
    from config import update_env_var
    update_env_var("INVITE_ANNOUNCEMENT_CHANNEL_ID", str(channel.id))
    
    embed = create_embed(
        title="✅ Invite Announcement Channel Set",
        description=f"Invite announcements will now be sent to {channel.mention}",
        color=discord.Color.green(),
        message_type="general"
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
