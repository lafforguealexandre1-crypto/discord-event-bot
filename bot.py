import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord
from discord.ext import tasks
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_ID = 1519087155412992011
EVENT_SALON_ID = 1543989597900513291
EVENT_PING_ROLE_ID = 1533879468681330698

PARIS = ZoneInfo("Europe/Paris")

ANNONCE_AVANT = 10
DUREE_EVENT = 20
DUREE_CHILL = 60


HORAIRES_EVENTS = [
    ("GOTHIC", "02:00", DUREE_EVENT),
    ("SUMMER", "02:00", DUREE_EVENT),
    ("GOTHIC", "02:30", DUREE_EVENT),
    ("RAVE", "03:30", DUREE_EVENT),
    ("JUNGLE", "04:00", DUREE_EVENT),
    ("TOKYO", "05:00", DUREE_EVENT),
    ("UNDERWATER", "05:30", DUREE_EVENT),
    ("CHILL HOUR", "05:30", DUREE_CHILL),
    ("ADMIN MACHINE", "06:30", DUREE_EVENT),
    ("GOTHIC", "07:00", DUREE_EVENT),
    ("SUMMER", "08:00", DUREE_EVENT),
    ("RAVE", "09:30", DUREE_EVENT),
    ("JUNGLE", "10:00", DUREE_EVENT),
    ("TOKYO", "11:00", DUREE_EVENT),
    ("UNDERWATER", "11:30", DUREE_EVENT),
    ("CHILL HOUR", "11:30", DUREE_CHILL),
    ("JUNGLE", "13:00", DUREE_EVENT),
    ("CRYSTAL", "14:00", DUREE_EVENT),
    ("GOTHIC", "14:30", DUREE_EVENT),
    ("JUNGLE", "16:00", DUREE_EVENT),
    ("CHILL HOUR", "16:30", DUREE_CHILL),
    ("UNDERWATER", "17:00", DUREE_EVENT),
    ("HEAVEN", "17:30", DUREE_EVENT),
    ("ADMIN MACHINE", "18:30", DUREE_EVENT),
    ("GOTHIC", "19:00", DUREE_EVENT),
    ("SUMMER", "20:00", DUREE_EVENT),
    ("MAGICAL", "20:30", DUREE_EVENT),
    ("HEAVEN", "21:00", DUREE_EVENT),
    ("JUNGLE", "22:00", DUREE_EVENT),
    ("VOID", "23:00", DUREE_EVENT),
    ("HEAVEN", "23:30", DUREE_EVENT),
    ("CHILL HOUR", "23:30", DUREE_CHILL),
    ("ADMIN MACHINE", "00:30", DUREE_EVENT),
]


intents = discord.Intents.default()

bot = discord.Client(
    intents=intents
)

annonces_envoyees = set()


def creer_datetime(date_base, heure):
    heures, minutes = map(
        int,
        heure.split(":")
    )

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

        for index, (nom, heure, duree) in enumerate(
            HORAIRES_EVENTS
        ):

            debut = creer_datetime(
                jour,
                heure
            )

            fin = debut + timedelta(
                minutes=duree
            )

            if fin > maintenant:

                occurrences.append({
                    "index": index,
                    "nom": nom,
                    "heure": heure,
                    "duree": duree,
                    "debut": debut,
                    "fin": fin
                })

    occurrences.sort(
        key=lambda event: (
            event["debut"],
            event["index"]
        )
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

    en_cours = (
        debut <= maintenant < fin
    )

    if event["duree"] == DUREE_CHILL:
        duree_texte = "Length: 1h 00m 00s"
    else:
        duree_texte = "Length: 20m 00s"

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
            f"{duree_texte}\n\n"
            f"Ends <t:{timestamp_fin}:R>\n\n"
            f"**LIVE now**"
        )

    else:

        embed.description = (
            f"**<t:{timestamp_debut}:t> "
            f"(<t:{timestamp_debut}:R>)**\n\n"
            f"**{event['nom']}**\n\n"
            f"{duree_texte}\n\n"
            f"Starts <t:{timestamp_debut}:R>"
        )

    return embed


async def envoyer_message(
    premier,
    deuxieme,
    raison
):

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
            content=(
                f"<@&{EVENT_PING_ROLE_ID}>"
            ),
            embeds=[
                creer_embed(premier),
                creer_embed(deuxieme)
            ],
            allowed_mentions=discord.AllowedMentions(
                roles=True
            )
        )

        annonces_envoyees.add(
            cle
        )

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

    cle = (
        f"{premier['nom']}-"
        f"{premier['debut'].strftime('%Y%m%d%H%M')}"
    )

    moment_annonce = (
        premier["debut"]
        - timedelta(
            minutes=ANNONCE_AVANT
        )
    )

    # =========================================
    # ANNONCE 10 MINUTES AVANT
    # =========================================

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

    # =========================================
    # SI LE BOT REDEMARRE PENDANT UN EVENT
    # =========================================

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
        "⏳ Events normaux : 20 minutes"
    )

    print(
        "🕐 Chill Hour : 1 heure"
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
