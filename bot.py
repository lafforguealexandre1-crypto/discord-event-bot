import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord
from discord.ext import tasks
from dotenv import load_dotenv


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_ID = 1519087155412992011
EVENT_SALON_ID = 1543989597900513291
EVENT_PING_ROLE_ID = 1553145917476180048

PARIS = ZoneInfo("Europe/Paris")

DUREE_EVENT = 20
DUREE_CHILL = 60


# =========================================================
# HORAIRES DES EVENTS
# =========================================================

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
    ("SUMMER", "14:00", DUREE_EVENT),
    ("GOTHIC", "14:30", DUREE_EVENT),
    ("JUNGLE", "16:00", DUREE_EVENT),
    ("CHILL HOUR", "16:30", DUREE_CHILL),
    ("UNDERWATER", "17:00", DUREE_EVENT),
    ("CHILL HOUR", "17:30", DUREE_CHILL),
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


# =========================================================
# NOMS AFFICHÉS
# =========================================================

NOMS_EVENTS = {
    "SUMMER": "SUMMER",
    "MAGICAL": "MAGICAL",
    "VOID": "VOID",
    "RAVE": "RAVE",
    "JUNGLE": "JUNGLE",
    "TOKYO": "TOKYO",
    "UNDERWATER": "UNDERWATER",
    "GOTHIC": "GOTHIC",
    "HEAVEN": "HEAVEN",
    "ADMIN MACHINE": "ADMIN MACHINE",
    "CHILL HOUR": "CHILL HOUR",
}


# =========================================================
# DISCORD
# =========================================================

intents = discord.Intents.default()

bot = discord.Client(intents=intents)

paire_actuelle = None
dernier_message = None


# =========================================================
# CRÉER UNE DATE
# =========================================================

def creer_datetime(date_base, heure):
    heures, minutes = map(int, heure.split(":"))

    return datetime(
        date_base.year,
        date_base.month,
        date_base.day,
        heures,
        minutes,
        tzinfo=PARIS
    )


# =========================================================
# OBTENIR TOUS LES EVENTS
# =========================================================

def obtenir_occurrences():
    maintenant = datetime.now(PARIS)

    occurrences = []

    for jour_offset in range(4):
        date_base = maintenant.date() + timedelta(days=jour_offset)

        for index, (nom, heure, duree) in enumerate(HORAIRES_EVENTS):

            debut = creer_datetime(date_base, heure)

            # 00:30 appartient au jour suivant
            if heure == "00:30":
                debut += timedelta(days=1)

            fin = debut + timedelta(minutes=duree)

            occurrences.append({
                "nom": nom,
                "debut": debut,
                "fin": fin,
                "duree": duree,
                "index": index
            })

    occurrences.sort(
        key=lambda event: (
            event["debut"],
            event["index"]
        )
    )

    return occurrences


# =========================================================
# TROUVER LES 2 PROCHAINS EVENTS
# =========================================================

def obtenir_prochains_events(occurrences, maintenant):

    futurs = [
        event
        for event in occurrences
        if event["debut"] > maintenant
    ]

    return futurs[:2]


# =========================================================
# TROUVER L'EVENT EN COURS
# =========================================================

def obtenir_event_en_cours(occurrences, maintenant):

    actifs = [
        event
        for event in occurrences
        if event["debut"] <= maintenant < event["fin"]
    ]

    if not actifs:
        return None

    actifs.sort(key=lambda event: event["debut"])

    return actifs[0]


# =========================================================
# FORMATER LE TEMPS
# =========================================================

def temps_restant(depart, maintenant):

    secondes = int((depart - maintenant).total_seconds())

    if secondes < 0:
        secondes = 0

    minutes = secondes // 60

    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"

    heures = minutes // 60
    minutes_restantes = minutes % 60

    if minutes_restantes == 0:
        return f"{heures} heure{'s' if heures != 1 else ''}"

    return (
        f"{heures} heure{'s' if heures != 1 else ''} "
        f"{minutes_restantes} minute{'s' if minutes_restantes != 1 else ''}"
    )


# =========================================================
# EMBED D'UN EVENT
# =========================================================

def creer_embed(event, maintenant):

    debut = event["debut"]
    fin = event["fin"]

    nom = NOMS_EVENTS.get(
        event["nom"],
        event["nom"]
    )

    embed = discord.Embed(
        title=f"{debut.strftime('%H:%M')} ➜ {fin.strftime('%H:%M')}",
        color=discord.Color.red()
    )

    embed.add_field(
        name=nom,
        value=f"Length: {event['duree']}m 00s",
        inline=False
    )

    # -----------------------------------------------------
    # EVENT EN COURS
    # -----------------------------------------------------

    if debut <= maintenant < fin:

        embed.add_field(
            name="🔴 LIVE",
            value="L'event est en cours !",
            inline=False
        )

        embed.add_field(
            name="Fin",
            value=f"dans {temps_restant(fin, maintenant)}",
            inline=False
        )

    # -----------------------------------------------------
    # EVENT À VENIR
    # -----------------------------------------------------

    else:

        embed.add_field(
            name="Starts",
            value=f"dans {temps_restant(debut, maintenant)}",
            inline=False
        )

        embed.add_field(
            name="Fin",
            value=f"dans {temps_restant(fin, maintenant)}",
            inline=False
        )

    return embed


# =========================================================
# ENVOYER LE MESSAGE
# =========================================================

async def envoyer_message(events, maintenant):

    global dernier_message

    salon = bot.get_channel(EVENT_SALON_ID)

    if salon is None:
        print("❌ Salon introuvable.")
        return

    embeds = []

    for event in events:
        embeds.append(
            creer_embed(event, maintenant)
        )

    message = (
        f"<@&{EVENT_PING_ROLE_ID}>\n\n"
        f"🔥 **STEAL THE BRAINROT**\n\n"
        f"Voici les prochains events :"
    )

    try:

        dernier_message = await salon.send(
            content=message,
            embeds=embeds,
            allowed_mentions=discord.AllowedMentions(
                roles=True
            )
        )

        print(
            "📢 Message envoyé :",
            ", ".join(
                event["nom"]
                for event in events
            )
        )

    except Exception as e:

        print(
            f"❌ Erreur lors de l'envoi : {e}"
        )


# =========================================================
# BOUCLE DES EVENTS
# =========================================================

@tasks.loop(seconds=5)
async def verifier_events():

    global paire_actuelle

    maintenant = datetime.now(PARIS)

    occurrences = obtenir_occurrences()

    # -----------------------------------------------------
    # PREMIER LANCEMENT
    # -----------------------------------------------------

    if paire_actuelle is None:

        event_en_cours = obtenir_event_en_cours(
            occurrences,
            maintenant
        )

        if event_en_cours:

            futurs = [
                event
                for event in occurrences
                if event["debut"] > maintenant
            ]

            paire_actuelle = [
                event_en_cours
            ]

            if futurs:
                paire_actuelle.append(
                    futurs[0]
                )

        else:

            paire_actuelle = obtenir_prochains_events(
                occurrences,
                maintenant
            )

        return

    # -----------------------------------------------------
    # VÉRIFIER SI LES 2 EVENTS SONT TERMINÉS
    # -----------------------------------------------------

    if len(paire_actuelle) < 2:
        return

    deuxieme_event = paire_actuelle[1]

    if deuxieme_event["fin"] > maintenant:
        return

    # -----------------------------------------------------
    # CHERCHER LES 2 EVENTS SUIVANTS
    # -----------------------------------------------------

    derniers_fin = max(
        event["fin"]
        for event in paire_actuelle
    )

    prochains = [
        event
        for event in occurrences
        if event["debut"] >= derniers_fin
    ]

    prochains = prochains[:2]

    if len(prochains) < 2:
        return

    paire_actuelle = prochains

    # -----------------------------------------------------
    # ENVOYER LE NOUVEAU MESSAGE
    # -----------------------------------------------------

    await envoyer_message(
        paire_actuelle,
        maintenant
    )


# =========================================================
# BOT CONNECTÉ
# =========================================================

@bot.event
async def on_ready():

    print(
        f"🤖 Bot connecté : {bot.user}"
    )

    print(
        f"📢 Salon : {EVENT_SALON_ID}"
    )

    print(
        f"🔔 Event Ping : {EVENT_PING_ROLE_ID}"
    )

    print(
        "🕐 Fuseau horaire : Europe/Paris"
    )

    print(
        "⏱️ Events : 20 minutes"
    )

    print(
        "🧊 Chill Hour : 1 heure"
    )

    print(
        "📦 2 events par message"
    )

    print(
        "⏳ Le prochain message est envoyé "
        "uniquement après la fin des 2 events."
    )

    if not verifier_events.is_running():

        verifier_events.start()

        print(
            "✅ Système Events activé !"
        )


# =========================================================
# LANCEMENT
# =========================================================

if not TOKEN:

    raise ValueError(
        "❌ DISCORD_TOKEN est introuvable dans les variables Railway."
    )


bot.run(
    TOKEN,
    reconnect=True
)
