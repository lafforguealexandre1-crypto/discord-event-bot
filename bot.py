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
EVENT_ROLE_ID = 1553145917476180048

PARIS = ZoneInfo("Europe/Paris")

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
    ("GOTHIC", "14:30", DUREE_EVENT),
    ("JUNGLE", "16:00", DUREE_EVENT),
    ("CHILL HOUR", "16:30", DUREE_CHILL),
    ("TOKYO", "17:00", DUREE_EVENT),
    ("UNDERWATER", "17:30", DUREE_EVENT),
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

paire_actuelle = None


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

    for jour_offset in range(4):
        jour = (
            maintenant
            + timedelta(days=jour_offset)
        ).date()

        for index, (nom, heure, duree) in enumerate(
            HORAIRES_EVENTS
        ):
            date_event = jour

            # 00:30 appartient au jour suivant
            # du planning qui commence à 02:00.
            if heure == "00:30":
                date_event = jour + timedelta(days=1)

            debut = creer_datetime(
                datetime(
                    date_event.year,
                    date_event.month,
                    date_event.day,
                    tzinfo=PARIS
                ),
                heure
            )

            fin = (
                debut
                + timedelta(minutes=duree)
            )

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


def creer_cle(event):
    return (
        f"{event['nom']}-"
        f"{event['debut'].strftime('%Y%m%d%H%M')}"
    )


def obtenir_paire_actuelle(occurrences, maintenant):
    actifs = [
        event
        for event in occurrences
        if event["debut"] <= maintenant < event["fin"]
    ]

    actifs.sort(
        key=lambda event: (
            event["debut"],
            event["index"]
        )
    )

    if len(actifs) >= 2:
        return (
            actifs[0],
            actifs[1]
        )

    if len(actifs) == 1:
        futurs = [
            event
            for event in occurrences
            if event["debut"] > maintenant
        ]

        if futurs:
            return (
                actifs[0],
                futurs[0]
            )

        return None

    futurs = [
        event
        for event in occurrences
        if event["debut"] > maintenant
    ]

    if len(futurs) >= 2:
        return (
            futurs[0],
            futurs[1]
        )

    return None


def paire_est_terminee(paire, maintenant):
    if paire is None:
        return False

    premier, deuxieme = paire

    return (
        premier["fin"] <= maintenant
        and deuxieme["fin"] <= maintenant
    )


def obtenir_prochaine_paire(occurrences, paire, maintenant):
    if paire is None:
        return None

    _, deuxieme = paire

    suivants = [
        event
        for event in occurrences
        if event["debut"] >= deuxieme["fin"]
    ]

    if len(suivants) < 2:
        return None

    return (
        suivants[0],
        suivants[1]
    )


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


async def envoyer_message(paire, raison):
    if paire is None:
        return

    premier, deuxieme = paire

    salon = bot.get_channel(
        EVENT_SALON_ID
    )

    if salon is None:
        print(
            f"❌ Salon introuvable : {EVENT_SALON_ID}"
        )
        return

    try:
        await salon.send(
            content=f"<@&{EVENT_ROLE_ID}>",
            embeds=[
                creer_embed(premier),
                creer_embed(deuxieme)
            ],
            allowed_mentions=discord.AllowedMentions(
                roles=True
            )
        )

        print(
            f"✅ Message envoyé : "
            f"{premier['nom']} → "
            f"{deuxieme['nom']} | {raison}"
        )

    except discord.Forbidden:
        print(
            "❌ Le bot n'a pas la permission "
            "de mentionner ce rôle ou d'envoyer "
            "dans ce salon."
        )

    except Exception as erreur:
        print(
            f"❌ Erreur d'envoi : {erreur}"
        )


@tasks.loop(seconds=5)
async def verifier_evenements():
    global paire_actuelle

    maintenant = datetime.now(PARIS)

    occurrences = obtenir_occurrences()

    # Première initialisation :
    # on détecte simplement les 2 events actuels/suivants
    # sans envoyer de message inutile au démarrage.
    if paire_actuelle is None:
        paire_actuelle = obtenir_paire_actuelle(
            occurrences,
            maintenant
        )

        if paire_actuelle:
            print(
                "ℹ️ Paire actuelle : "
                f"{paire_actuelle[0]['nom']} → "
                f"{paire_actuelle[1]['nom']}"
            )

        return

    # On attend que LES DEUX events du message actuel
    # soient complètement terminés.
    if not paire_est_terminee(
        paire_actuelle,
        maintenant
    ):
        return

    prochaine_paire = obtenir_prochaine_paire(
        occurrences,
        paire_actuelle,
        maintenant
    )

    if prochaine_paire is None:
        return

    ancienne_paire = paire_actuelle

    paire_actuelle = prochaine_paire

    await envoyer_message(
        paire_actuelle,
        f"{ancienne_paire[0]['nom']} + "
        f"{ancienne_paire[1]['nom']} terminés"
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
        f"🔔 Rôle Event : {EVENT_ROLE_ID}"
    )

    print(
        "📢 Annonce : après la fin des 2 events"
    )

    print(
        "⏳ Events normaux : 20 minutes"
    )

    print(
        "🕐 Chill Hour : 1 heure"
    )

    print(
        "🌙 Gestion de minuit : activée"
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
