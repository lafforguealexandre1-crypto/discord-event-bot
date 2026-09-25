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
    "SUMMER": ["14:00", "20:00"],
    "MAGICAL": ["14:30", "20:30"],
    "VOID": ["15:00", "23:00"],
    "JUNGLE": ["16:00", "22:00"],
    "TOKYO": ["17:00"],
    "AQUA": ["17:30"],
    "ADMIN MACHINE": ["18:30", "00:30"],
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

        jour = maintenant + timedelta(days=jour_offset)

        for nom_event, horaires in HORAIRES_EVENTS.items():

            for heure in horaires:

                debut = creer_datetime(jour, heure)
                fin = debut + timedelta(minutes=DUREE_EVENT)

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

    timestamp_debut = int(debut.timestamp())
    timestamp_fin = int(fin.timestamp())

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


async def envoyer_paire(premier, deuxieme, raison):

    salon = bot.get_channel(EVENT_SALON_ID)

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
            f"✅ {premier['nom']} → "
            f"{deuxieme['nom']} | {raison}"
        )

    except discord.Forbidden:

        print(
            "❌ Le bot n'a pas la permission "
            "d'envoyer dans ce salon."
        )

    except Exception as erreur:

        print(
            f"❌ Erreur : {erreur}"
        )


async def verifier_events():

    maintenant = datetime.now(PARIS)

    occurrences = obtenir_occurrences()

    if len(occurrences) < 2:
        return

    premier = occurrences[0]
    deuxieme = occurrences[1]

    cle = (
        f"{premier['nom']}-"
        f"{premier['debut'].strftime('%Y%m%d%H%M')}"
    )

    # =========================================
    # 1. ANNONCE 10 MINUTES AVANT
    # =========================================

    moment_annonce = (
        premier["debut"]
        - timedelta(minutes=ANNONCE_AVANT)
    )

    if (
        moment_annonce <= maintenant
        < premier["debut"]
    ):

        await envoyer_paire(
            premier,
            deuxieme,
            "10 minutes avant"
        )

        return

    # =========================================
    # 2. SI L'EVENT EST ACTUELLEMENT LIVE
    # =========================================

    if (
        premier["debut"]
        <= maintenant
        < premier["fin"]
    ):

        if cle not in annonces_envoyees:

            await envoyer_paire(
                premier,
                deuxieme,
                "event déjà LIVE"
            )

        return

    # =========================================
    # 3. SI LE PREMIER EVENT EST TERMINE
    # =========================================

    if maintenant >= premier["fin"]:

        if cle not in annonces_envoyees:

            await envoyer_paire(
                premier,
                deuxieme,
                "event précédent terminé"
            )


@tasks.loop(seconds=5)
async def boucle_events():

    await verifier_events()


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
        f"🔔 Event Ping : {EVENT_PING_ROLE_ID}"
    )

    print(
        "📢 Annonce : 10 minutes avant"
    )

    print(
        "📦 2 embeds par message"
    )

    print(
        "🔄 Nouveau message après chaque event"
    )

    print(
        "🌴 JUNGLE : 16:00 / 22:00"
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

    if not boucle_events.is_running():

        boucle_events.start()

        print(
            "✅ Système Events activé !"
        )


if not TOKEN:

    print(
        "❌ DISCORD_TOKEN introuvable."
    )

else:

    print(
        "🚀 Démarrage du bot..."
    )

    bot.run(
        TOKEN,
        reconnect=True
    )
