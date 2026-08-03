import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

# =========================
# CONFIGURATION
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

TIMEZONE = ZoneInfo("Europe/Paris")

EVENTS = {
    "🟣 Gothic": {"hour": 14, "minute": 30, "every": 6},
    "☀️ Summer": {"hour": 16, "minute": 0, "every": 3},
    "💧 Aqua": {"hour": 17, "minute": 0, "every": 9},
    "🟢 Neon": {"hour": 14, "minute": 0, "every": 6},
    "✨ Magical": {"hour": 17, "minute": 30, "every": 5},
    "⚫ Void": {"hour": 23, "minute": 0, "every": 24},
}

DURATION = timedelta(minutes=20)

# =========================
# BOT
# =========================

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

message = None


def get_next_event(hour, minute, every_hours):
    """Trouve le prochain passage de l'événement."""
    now = datetime.now(TIMEZONE)

    start = now.replace(
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0
    )

    # Si le premier horaire du jour est déjà passé,
    # on avance par intervalles jusqu'au prochain.
    if now < start:
        return start

    elapsed = now - start
    intervals = int(elapsed.total_seconds() // (every_hours * 3600)) + 1

    return start + timedelta(hours=intervals * every_hours)


def get_event_status(hour, minute, every_hours):
    """Retourne si l'event est actif et son prochain horaire."""
    now = datetime.now(TIMEZONE)

    next_event = get_next_event(hour, minute, every_hours)

    # Cherche si l'événement actuel est en cours.
    previous = next_event - timedelta(hours=every_hours)

    if previous <= now < previous + DURATION:
        return True, previous

    return False, next_event


def discord_time(dt):
    """Transforme une date en timestamp Discord."""
    return f"<t:{int(dt.timestamp())}:R>"


def create_embed():
    embed = discord.Embed(
        title="🟦 Steal the Brainrot events",
        description="**Event schedule**",
        color=discord.Color.blue()
    )

    for name, data in EVENTS.items():
        active, event_time = get_event_status(
            data["hour"],
            data["minute"],
            data["every"]
        )

        if active:
            text = "🟢 **Active now!**"
        else:
            text = f"⏰ Next active {discord_time(event_time)}"

        embed.add_field(
            name=name,
            value=text,
            inline=False
        )

    now = datetime.now(TIMEZONE)

    embed.set_footer(
        text=f"Last update: {now.strftime('%H:%M:%S')} 🇫🇷"
    )

    return embed


@tasks.loop(seconds=30)
async def update_message():
    global message

    if message is None:
        return

    try:
        await message.edit(embed=create_embed())
    except discord.NotFound:
        message = None


@bot.event
async def on_ready():
    global message

    print(f"Connecté en tant que {bot.user}")

    channel = bot.get_channel(CHANNEL_ID)

    if channel is None:
        print("❌ CHANNEL_ID incorrect.")
        return

    # Cherche un ancien message du bot
    async for msg in channel.history(limit=50):
        if msg.author == bot.user:
            message = msg
            break

    # S'il n'existe pas, crée le message
    if message is None:
        message = await channel.send(embed=create_embed())

    # Lance la mise à jour
    if not update_message.is_running():
        update_message.start()


bot.run(TOKEN)
