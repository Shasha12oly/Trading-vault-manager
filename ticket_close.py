"""
Ticket closing module - handles ticket closing with transcripts
"""
import io
import discord
from datetime import datetime, timezone
from config import LOG_CHANNEL_ID
from embed_utils import create_embed
from ticket_utils import get_ticket_info


async def close_ticket_final(interaction: discord.Interaction):
    channel = interaction.channel
    info = get_ticket_info(channel)
    owner = interaction.guild.get_member(info["owner_id"])
    
    await interaction.response.edit_message(content="Closing ticket and saving transcript...", view=None, embed=None)

    # Build transcript
    lines = []
    lines.append("=" * 50)
    lines.append(f"Ticket: {channel.name}")
    lines.append(f"Category: {info['category']}")
    if info['category'] == 'purchase':
        lines.append(f"Item: {info.get('item', 'Unknown')}")
        lines.append(f"Quantity: {info.get('quantity', 'Unknown')}")
    elif info.get('priority'):
        lines.append(f"Priority: {info['priority']}")
    if info['claimed_by']:
        claimed_member = interaction.guild.get_member(info['claimed_by'])
        lines.append(f"Claimed by: {claimed_member.name if claimed_member else 'Unknown'} ({info['claimed_by']})")
    lines.append(f"Owner: {owner.name if owner else 'Unknown'} ({info['owner_id']})")
    lines.append(f"Closed by: {interaction.user}")
    lines.append(f"Closed at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("=" * 50)
    lines.append("")
    
    async for m in channel.history(limit=None, oldest_first=True):
        ts = m.created_at.strftime("%Y-%m-%d %H:%M:%S")
        text = m.content or ""
        if m.attachments:
            text += " " + " ".join(f"[Attachment: {a.filename}]({a.url})" for a in m.attachments)
        lines.append(f"[{ts}] {m.author}: {text}")
    
    transcript = io.BytesIO("\n".join(lines).encode("utf-8"))

    # Send to log channel
    if LOG_CHANNEL_ID:
        log = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log:
            log_embed = create_embed(
                title="🔒 Ticket Closed",
                description=f"**Ticket:** {channel.name}\n**Closed by:** {interaction.user.mention}",
                color=discord.Color.red()
            )
            await log.send(embed=log_embed, file=discord.File(transcript, filename=f"{channel.name}-transcript.txt"))

    # DM the owner
    if owner:
        try:
            if info['category'] == 'purchase':
                dm_embed = create_embed(
                    title="Purchase Ticket Closed",
                    description=f"Your purchase ticket **{channel.name}** has been closed by {interaction.user.mention}.\n\nIf you need to make another purchase, please open a new ticket.",
                    color=discord.Color.gold()
                )
            else:
                dm_embed = create_embed(
                    title="Ticket Closed",
                    description=f"Your ticket **{channel.name}** has been closed by {interaction.user.mention}.\n\nIf you need further assistance, please open a new ticket.",
                    color=discord.Color.red()
                )
            await owner.send(embed=dm_embed)
        except discord.Forbidden:
            pass

    await channel.delete(reason=f"Closed by {interaction.user}")
