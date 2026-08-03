import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} commande(s) synchronisée(s).")
    except Exception as e:
        print(f"Erreur de synchronisation : {e}")


@bot.tree.command(
    name="events",
    description="Affiche les prochains événements"
)
async def events(interaction: discord.Interaction):

    embed = discord.Embed(
        title="Steal the Brainrot events",
        description=(
            "🟣 **Gothic** — Active maintenant\n"
            "⚽ **Football** — Prochain dans 1 heure\n"
            "🔵 **Aqua** — Prochain dans 2 heures\n"
            "🟢 **Neon** — Prochain dans 5 heures\n"
            "⚫ **Void** — Prochain dans 8 heures\n"
            "✨ **Magical** — Prochain dans 3 heures\n"
            "☁️ **Heaven** — Prochain dans 4 heures"
        ),
        color=discord.Color.blue()
    )

    await interaction.response.send_message(embed=embed)


if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN n'est pas configuré.")

bot.run(TOKEN)
