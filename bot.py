import os
import random
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import database

load_dotenv(Path(__file__).parent / ".env")

# ---------------------------------------------------------------------------
# Bot setup
# ---------------------------------------------------------------------------

PREFIX = "g"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# help_command=None disables discord.py's built-in help so only `g help` is used.
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)


# ---------------------------------------------------------------------------
# Shared response builders (used by both prefix and slash commands)
# ---------------------------------------------------------------------------

def build_rank_embed(member: discord.Member, guild: discord.Guild) -> discord.Embed:
    """Build the embed shown by the rank command."""
    user = database.get_user(member.id, guild.id)
    rank_position = database.get_rank(member.id, guild.id)
    xp_needed = database.xp_for_level(user["level"] + 1)

    embed = discord.Embed(
        title=f"{member.display_name}'s Rank",
        color=discord.Color.blurple(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Level", value=str(user["level"]), inline=True)
    embed.add_field(name="XP", value=f"{user['xp']} / {xp_needed}", inline=True)
    embed.add_field(name="Server Rank", value=f"#{rank_position}", inline=True)
    return embed


def build_leaderboard_embed(guild: discord.Guild) -> discord.Embed | str:
    """Build the embed for the leaderboard, or a plain string if nobody has XP yet."""
    entries = database.get_leaderboard(guild.id)

    if not entries:
        return "No one has earned XP yet."

    lines = []
    medals = ("🥇", "🥈", "🥉")

    for index, entry in enumerate(entries, start=1):
        member = guild.get_member(entry["user_id"])
        name = member.display_name if member else f"User {entry['user_id']}"
        prefix = medals[index - 1] if index <= 3 else f"**{index}.**"
        lines.append(f"{prefix} {name} — Level {entry['level']} ({entry['xp']} XP)")

    return discord.Embed(
        title=f"{guild.name} Leaderboard",
        description="\n".join(lines),
        color=discord.Color.gold(),
    )


def build_help_embed() -> discord.Embed:
    """
    Build the help embed by reading every registered command on the bot.

    To add a new command later:
      1. Create a @bot.hybrid_command with a `help="..."` description.
      2. It will automatically appear here — no manual list to update.
    """
    embed = discord.Embed(
        title="Leveling Bot — Command Help",
        description=(
            f"**Prefix:** `{PREFIX} <command>`\n"
            f"**Slash:** `/<command>`\n\n"
            "Earn XP by chatting (60-second cooldown between gains)."
        ),
        color=discord.Color.blurple(),
    )

    # Sort commands alphabetically for a consistent help menu.
    for command in sorted(bot.commands, key=lambda cmd: cmd.name):
        if command.hidden:
            continue

        description = command.help or "No description provided."
        embed.add_field(
            name=f"`{PREFIX} {command.name}`  ·  `/{command.name}`",
            value=description,
            inline=False,
        )

    embed.set_footer(text="Tip: hybrid commands work with both prefix and slash.")
    return embed


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

@bot.event
async def on_ready():
    database.init_db()
    await bot.tree.sync()
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Slash commands synced.")


@bot.event
async def on_message(message: discord.Message):
    """Award XP for messages and route prefix commands (e.g. g help)."""
    if message.author.bot or message.guild is None:
        return

    xp_gain = random.randint(15, 25)
    result = database.try_add_xp(message.author.id, message.guild.id, xp_gain)

    if result and result["leveled_up"]:
        await message.channel.send(
            f"GG {message.author.mention}, you reached level **{result['level']}**!"
        )

    # Required so prefix commands like `g help` are processed.
    await bot.process_commands(message)


# ---------------------------------------------------------------------------
# Commands — hybrid_command registers BOTH `g <name>` and `/<name>`
#
# When adding a new command, copy one of the blocks below and set:
#   - name (implicit from function name)
#   - help= "short description"  ← shown in `g help`
#   - description= "..."         ← shown in Discord's slash command UI
# ---------------------------------------------------------------------------

@bot.hybrid_command(
    name="help",
    help="Show every available command and what it does.",
    description="Show every available command and what it does.",
)
async def help_command(ctx: commands.Context):
    await ctx.send(embed=build_help_embed())


@bot.hybrid_command(
    name="rank",
    help="View your XP, level, and server rank.",
    description="View your XP, level, and server rank.",
)
@app_commands.describe(member="The member to check (defaults to you)")
async def rank(ctx: commands.Context, member: discord.Member | None = None):
    target = member or ctx.author
    await ctx.send(embed=build_rank_embed(target, ctx.guild))


@bot.hybrid_command(
    name="leaderboard",
    help="View the top 10 members by XP in this server.",
    description="View the top 10 members by XP in this server.",
)
async def leaderboard(ctx: commands.Context):
    response = build_leaderboard_embed(ctx.guild)
    if isinstance(response, str):
        await ctx.send(response)
    else:
        await ctx.send(embed=response)


# ---------------------------------------------------------------------------
# Run the bot
# ---------------------------------------------------------------------------

token = (os.getenv("DISCORD_TOKEN") or "").strip().strip('"').strip("'")
if not token or token == "your_bot_token_here":
    raise RuntimeError(
        "DISCORD_TOKEN is missing or still set to the placeholder in leveling-bot/.env"
    )

try:
    bot.run(token)
except discord.LoginFailure:
    raise SystemExit(
        "Login failed: invalid bot token.\n"
        "Reset the token in the Discord Developer Portal (Bot → Reset Token),\n"
        "paste the new token into leveling-bot/.env, and run again."
    ) from None

@bot.hybrid_command(
    name="mycommand",
    help="Short description shown in g help.",
    description="Short description shown in Discord's slash menu.",
)
async def mycommand(ctx: commands.Context):
    await ctx.send("Hello!")