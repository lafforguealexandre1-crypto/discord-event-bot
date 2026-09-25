import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_ID = 1519087155412992011
EVENT_SALON_ID = 1543989597900513291
EVENT_PING_ROLE_ID = 1533879468681330698

PARIS = ZoneInfo("Europe/Paris")

DUREE_EVENT = 20
ANNONCE_AVANT = 10

HORAIRES_EVENTS = {
    "SUMMER": ["02:00", "08:00", "14:00", "20:00"],
    "MAGICAL": ["02:30", "08:30", "14:30", "20:30"],
    "VOID": ["07:00", "15:00", "23:00"],
    "JUNGLE": ["04:00", "10:00", "16:00", "22:00"],
    "TOKYO": ["17:00"],
    "AQUA": ["17:30"],
    "GOTHIC": ["19:00"],
    "HEAVEN": ["21:00", "23:30"]
}

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

annonces_envoyees = set()


def creer_datetime(date_base, heure):
    heures, minutes = map(int, heure.split(":"))

    return datetime(
        date_base.year,
        date_base.month,
        date_base.day,
        heures,
        minutes,
        0,
        0,
        tzinfo=PARIS
    )


def obtenir_occurrences():
    maintenant = datetime.now(PARIS)

    occurrences = []

    for jour_offset in range(3):

        jour = maintenant + timedelta(
            days=jour_offset
        )

        for nom_event, horaires in HORAIRES_EVENTS.items():

            for heure in horaires:

                debut = creer_datetime(
                    jour,
                    heure
                )

                fin = debut + timedelta(
                    minutes=DUREE_EVENT
                )

                if fin > maintenant:

                    occurrences.append({
                        "nom": nom_event,
                        "heure": heure,
                        "debut": debut,
                        "fin": fin
                    })

    occurrences.sort(
        key=lambda event: event["debut"]
    )

    return occurrences


def creer_embed(event):
    maintenant = datetime.now(PARIS)

    debut = event["debut"]
    fin = event["fin"]

    timestamp_debut = int(
        debut.timestamp()
    )

    timestamp_fin = int(
        fin.timestamp()
    )

    en_cours = debut <= maintenant < fin

    embed = discord.Embed(
        colour=discord.Colour.red()
    )

    if bot.user:

        embed.set_author(
            name=bot.user.name,
            icon_url=bot.user.display_avatar.url
        )

    if en_cours:

        embed.description = (
            f"**<t:{timestamp_debut}:t> → "
            f"<t:{timestamp_fin}:t> "
            f"(<t:{timestamp_fin}:R>)**\n\n"
            f"**{event['nom']}**\n\n"
            f"Length: 20m 00s\n\n"
            f"Ends <t:{timestamp_fin}:R>\n\n"
            f"**LIVE now**"
        )

    else:

        embed.description = (
            f"**<t:{timestamp_debut}:t> "
            f"(<t:{timestamp_debut}:R>)**\n\n"
            f"**{event['nom']}**\n\n"
            f"Length: 20m 00s\n\n"
            f"Starts <t:{timestamp_debut}:R>"
        )

    return embed


async def envoyer_message(premier, deuxieme, raison):

    salon = bot.get_channel(
        EVENT_SALON_ID
    )

    if salon is None:

        print(
            f"❌ Salon introuvable : {EVENT_SALON_ID}"
        )

        return

    cle = (
        f"{premier['nom']}-"
        f"{premier['debut'].strftime('%Y%m%d%H%M')}"
    )

    if cle in annonces_envoyees:
        return

    try:

        await salon.send(
            content=f"<@&{EVENT_PING_ROLE_ID}>",
            embeds=[
                creer_embed(premier),
                creer_embed(deuxieme)
            ],
            allowed_mentions=discord.AllowedMentions(
                roles=True
            )
        )

        annonces_envoyees.add(cle)

        print(
            f"✅ Message envoyé : "
            f"{premier['nom']} → "
            f"{deuxieme['nom']} | {raison}"
        )

    except discord.Forbidden:

        print(
            "❌ Le bot n'a pas la permission "
            "d'envoyer dans ce salon."
        )

    except Exception as erreur:

        print(
            f"❌ Erreur d'envoi : {erreur}"
        )


@tasks.loop(seconds=5)
async def verifier_evenements():

    maintenant = datetime.now(PARIS)

    occurrences = obtenir_occurrences()

    if len(occurrences) < 2:
        return

    premier = occurrences[0]
    deuxieme = occurrences[1]

    moment_annonce = (
        premier["debut"]
        - timedelta(
            minutes=ANNONCE_AVANT
        )
    )

    cle = (
        f"{premier['nom']}-"
        f"{premier['debut'].strftime('%Y%m%d%H%M')}"
    )

    # Annonce 10 minutes avant
    if (
        moment_annonce
        <= maintenant
        < premier["debut"]
    ):

        if cle not in annonces_envoyees:

            await envoyer_message(
                premier,
                deuxieme,
                "10 minutes avant"
            )

        return

    # Si le bot redémarre pendant un event,
    # il détecte qu'il est déjà en cours.
    if (
        premier["debut"]
        <= maintenant
        < premier["fin"]
    ):

        if cle not in annonces_envoyees:

            await envoyer_message(
                premier,
                deuxieme,
                "event déjà en direct"
            )


@bot.event
async def on_ready():

    print(
        "======================================"
    )

    print(
        f"🤖 Bot connecté : {bot.user}"
    )

    print(
        "🕒 Heure Paris : "
        f"{datetime.now(PARIS).strftime('%d/%m/%Y %H:%M:%S')}"
    )

    print(
        f"📢 Salon : {EVENT_SALON_ID}"
    )

    print(
        f"🔔 Ping Event : {EVENT_PING_ROLE_ID}"
    )

    print(
        "📢 Annonce : 10 minutes avant"
    )

    print(
        "⏳ Durée : 20 minutes"
    )

    print(
        "📦 2 embeds par message"
    )

    print(
        "🌴 JUNGLE : 04:00 / 10:00 / 16:00 / 22:00"
    )

    print(
        "☀️ SUMMER : 02:00 / 08:00 / 14:00 / 20:00"
    )

    print(
        "✨ MAGICAL : 02:30 / 08:30 / 14:30 / 20:30"
    )

    print(
        "🌌 VOID : 07:00 / 15:00 / 23:00"
    )

    print(
        "🗼 TOKYO : 17:00"
    )

    print(
        "🌊 AQUA : 17:30"
    )

    print(
        "🖤 GOTHIC : 19:00"
    )

    print(
        "☁️ HEAVEN : 21:00 / 23:30"
    )

    print(
        "======================================"
    )

    salon = bot.get_channel(
        EVENT_SALON_ID
    )

    if salon:

        print(
            f"✅ Salon trouvé : #{salon.name}"
        )

    else:

        print(
            "❌ Salon introuvable"
        )

    if not verifier_evenements.is_running():

        verifier_evenements.start()

        print(
            "✅ Système Events activé !"
        )


if not TOKEN:

    print(
        "❌ DISCORD_TOKEN manquant."
    )

else:

    print(
        "🚀 Démarrage du bot..."
    )

    bot.run(
        TOKEN,
        reconnect=True
    )
