from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


# ---------------------------------------------------------------------------
# Helpers: embed builders
# ---------------------------------------------------------------------------


def build_warn_embed(
    member: discord.Member,
    moderator: discord.Member,
    reason: str | None,
) -> discord.Embed:
    embed = discord.Embed(
        title="⚠️ Member Warned",
        description=f"{member.mention} has received a warning.",
        color=discord.Color.orange(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Moderator", value=moderator.mention, inline=True)
    embed.add_field(
        name="Reason",
        value=reason or "No reason provided",
        inline=True,
    )
    embed.set_footer(text=f"User ID: {member.id}")
    return embed


def build_timeout_embed(
    member: discord.Member,
    moderator: discord.Member,
    duration: str,
    reason: str | None,
) -> discord.Embed:
    embed = discord.Embed(
        title="🔇 Member Timed Out",
        description=f"{member.mention} has been timed out for {duration}.",
        color=discord.Color.red(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Moderator", value=moderator.mention, inline=True)
    embed.add_field(
        name="Reason",
        value=reason or "No reason provided",
        inline=True,
    )
    embed.set_footer(text=f"User ID: {member.id}")
    return embed


def build_kick_embed(
    member: discord.Member,
    moderator: discord.Member,
    reason: str | None,
) -> discord.Embed:
    embed = discord.Embed(
        title="👢 Member Kicked",
        description=f"{member.mention} has been kicked from the server.",
        color=discord.Color.orange(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Moderator", value=moderator.mention, inline=True)
    embed.add_field(
        name="Reason",
        value=reason or "No reason provided",
        inline=True,
    )
    embed.set_footer(text=f"User ID: {member.id}")
    return embed


def build_ban_embed(
    member: discord.Member,
    moderator: discord.Member,
    reason: str | None,
) -> discord.Embed:
    embed = discord.Embed(
        title="🔨 Member Banned",
        description=f"{member.mention} has been banned from the server.",
        color=discord.Color.red(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Moderator", value=moderator.mention, inline=True)
    embed.add_field(
        name="Reason",
        value=reason or "No reason provided",
        inline=True,
    )
    embed.set_footer(text=f"User ID: {member.id}")
    return embed


def build_clear_embed(
    moderator: discord.Member,
    amount: int,
) -> discord.Embed:
    embed = discord.Embed(
        title="🧹 Messages Cleared",
        description=f"{amount} message(s) have been deleted in this channel.",
        color=discord.Color.blurple(),
    )
    embed.set_thumbnail(url=moderator.display_avatar.url)
    embed.set_footer(text=f"Moderator ID: {moderator.id}")
    return embed


# ---------------------------------------------------------------------------
# Moderation Cog
# ---------------------------------------------------------------------------


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="warn",
        help="Warn a member for breaking the rules.",
        description="Warn a member for breaking the rules.",
    )
    @app_commands.describe(member="The member to warn", reason="Reason for the warning")
    async def warn_cmd(self, ctx: commands.Context, member: discord.Member, *, reason: str | None = None):
        if not ctx.author.guild_permissions.moderate_members:
            await ctx.send("You don't have permission to warn members.", ephemeral=True)
            return

        await ctx.send(embed=build_warn_embed(member, ctx.author, reason))

    @commands.hybrid_command(
        name="timeout",
        help="Timeout a member for a given duration.",
        description="Timeout a member for a given duration.",
    )
    @app_commands.describe(
        member="The member to timeout",
        duration="Duration (e.g. 10m, 1h, 1d)",
        reason="Reason for the timeout",
    )
    async def timeout_cmd(
        self,
        ctx: commands.Context,
        member: discord.Member,
        duration: str,
        *,
        reason: str | None = None,
    ):
        if not ctx.author.guild_permissions.moderate_members:
            await ctx.send("You don't have permission to timeout members.", ephemeral=True)
            return

        unit = duration[-1].lower()
        try:
            value = int(duration[:-1])
        except ValueError:
            await ctx.send("Invalid duration format. Use e.g. `10m`, `1h`, `1d`.", ephemeral=True)
            return

        if unit == "m":
            seconds = value * 60
        elif unit == "h":
            seconds = value * 60 * 60
        elif unit == "d":
            seconds = value * 60 * 60 * 24
        else:
            await ctx.send("Invalid duration unit. Use m (minutes), h (hours), or d (days).", ephemeral=True)
            return

        await member.timeout(seconds, reason=reason)
        await ctx.send(embed=build_timeout_embed(member, ctx.author, duration, reason))

    @commands.hybrid_command(
        name="kick",
        help="Kick a member from the server.",
        description="Kick a member from the server.",
    )
    @app_commands.describe(member="The member to kick", reason="Reason for the kick")
    async def kick_cmd(self, ctx: commands.Context, member: discord.Member, *, reason: str | None = None):
        if not ctx.author.guild_permissions.kick_members:
            await ctx.send("You don't have permission to kick members.", ephemeral=True)
            return

        await member.kick(reason=reason)
        await ctx.send(embed=build_kick_embed(member, ctx.author, reason))

    @commands.hybrid_command(
        name="ban",
        help="Ban a member from the server.",
        description="Ban a member from the server.",
    )
    @app_commands.describe(member="The member to ban", reason="Reason for the ban")
    async def ban_cmd(self, ctx: commands.Context, member: discord.Member, *, reason: str | None = None):
        if not ctx.author.guild_permissions.ban_members:
            await ctx.send("You don't have permission to ban members.", ephemeral=True)
            return

        await member.ban(reason=reason, delete_message_days=0)
        await ctx.send(embed=build_ban_embed(member, ctx.author, reason))

    @commands.hybrid_command(
        name="clear",
        help="Clear a number of messages in this channel.",
        description="Clear a number of messages in this channel.",
    )
    @app_commands.describe(amount="Number of messages to delete (1–100)")
    async def clear_cmd(self, ctx: commands.Context, amount: int):
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send("You don't have permission to clear messages.", ephemeral=True)
            return

        if not (1 <= amount <= 100):
            await ctx.send("Amount must be between 1 and 100.", ephemeral=True)
            return

        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(embed=build_clear_embed(ctx.author, len(deleted)), delete_after=5)


# ---------------------------------------------------------------------------
# Setup function for extension
# ---------------------------------------------------------------------------


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))