
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
# Rôle mentionné selon l'événement annoncé
EVENT_ROLE_IDS = {
    "VOID": 1534297189373706330,
    "RAVE": 1540835935560794284,
    "UNDERWATER": 1540835675723800586,  # Aqua
    "MAGICAL": 1534297229030850570,
    "TOKYO": 1540836263915946045,
    "GOTHIC": 1534297341756969071,
    "HEAVEN": 1540836636911476736,
    "ADMIN MACHINE": 1535755520135266374,
    "SUMMER": 1534297254918230289,
    "JUNGLE": 1548429410238201906,
    "HALLOWEEN": 1561364317096517702,  # Halloween V2
    "CHILL HOUR": 1561722453955322086,
}

PARIS = ZoneInfo("Europe/Paris")

DUREE_EVENT = 20
DUREE_CHILL = 60
JOURS_CALCUL = 4


# =========================================================
# HORAIRES QUOTIDIENS DES EVENTS
# Tous les événements sont avancés d'une heure.
# =========================================================

HORAIRES_EVENTS = [
    ("GOTHIC", "02:00", DUREE_EVENT),
    ("UNDERWATER", "02:00", DUREE_EVENT),
    ("VOID", "03:00", DUREE_EVENT),
    ("RAVE", "03:30", DUREE_EVENT),
    ("HALLOWEEN", "04:00", DUREE_EVENT),
    ("MAGICAL", "05:00", DUREE_EVENT),
    ("SUMMER", "05:30", DUREE_EVENT),
    ("CHILL HOUR", "05:30", DUREE_CHILL),
    ("ADMIN MACHINE", "06:30", DUREE_EVENT),
    ("GOTHIC", "07:00", DUREE_EVENT),
    ("VOID", "08:00", DUREE_EVENT),
    ("RAVE", "09:30", DUREE_EVENT),
    ("HALLOWEEN", "10:00", DUREE_EVENT),
    ("TOKYO", "11:00", DUREE_EVENT),
    ("UNDERWATER", "11:30", DUREE_EVENT),
    ("CHILL HOUR", "11:30", DUREE_CHILL),
    ("JUNGLE", "14:30", DUREE_EVENT),
    ("HALLOWEEN", "16:00", DUREE_EVENT),
    ("MAGICAL", "17:00", DUREE_EVENT),
    ("SUMMER", "17:30", DUREE_EVENT),
    ("CHILL HOUR", "17:30", DUREE_CHILL),
    ("HALLOWEEN", "18:00", DUREE_EVENT),
    ("ADMIN MACHINE", "18:30", DUREE_EVENT),
    ("GOTHIC", "19:00", DUREE_EVENT),
    ("TOKYO", "20:00", DUREE_EVENT),
    ("JUNGLE", "20:30", DUREE_EVENT),
    ("HEAVEN", "21:00", DUREE_EVENT),
    ("RAVE", "21:30", DUREE_EVENT),
    ("HALLOWEEN", "22:00", DUREE_EVENT),
    ("VOID", "23:00", DUREE_EVENT),
    ("HEAVEN", "23:30", DUREE_EVENT),
    ("CHILL HOUR", "23:30", DUREE_CHILL),
    ("ADMIN MACHINE", "00:30", DUREE_EVENT),
]


# =========================================================
# INITIALISATION DISCORD
# =========================================================

intents = discord.Intents.default()
bot = discord.Client(intents=intents)

salon_events = None
demarrage_effectue = False
horaires_annonces = set()


# =========================================================
# CRÉER UNE DATE EN HEURE DE PARIS
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
# OBTENIR LES OCCURRENCES DES EVENTS
# =========================================================

def obtenir_occurrences():
    maintenant = datetime.now(PARIS)
    occurrences = []

    for jour_offset in range(JOURS_CALCUL):
        date_base = (
            maintenant.date()
            + timedelta(days=jour_offset)
        )

        for index, (nom, heure, duree) in enumerate(
            HORAIRES_EVENTS
        ):
            debut = creer_datetime(date_base, heure)

            # L'événement de 00:30 correspond au lendemain
            # du dernier événement de la journée précédente.
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
# IDENTIFIANT UNIQUE D'UN EVENT
# =========================================================

def cle_event(event):
    return (
        event["debut"].date().isoformat(),
        event["debut"].strftime("%H:%M"),
        event["index"]
    )


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

    actifs.sort(
        key=lambda event: (
            event["debut"],
            event["index"]
        )
    )

    return actifs[0]


# =========================================================
# TROUVER LES DEUX EVENTS À AFFICHER
# =========================================================

def obtenir_deux_events(occurrences, maintenant):
    event_en_cours = obtenir_event_en_cours(
        occurrences,
        maintenant
    )

    futurs = [
        event
        for event in occurrences
        if event["debut"] > maintenant
    ]

    if event_en_cours:
        resultat = [event_en_cours]

        if futurs:
            resultat.append(futurs[0])

        return resultat

    return futurs[:2]


# =========================================================
# CRÉER UN EMBED DISCORD
# =========================================================

def creer_embed(event, maintenant):
    debut = event["debut"]
    fin = event["fin"]

    debut_ts = int(debut.timestamp())
    fin_ts = int(fin.timestamp())

    embed = discord.Embed(
        title=f"<t:{debut_ts}:t> ➜ <t:{fin_ts}:t>",
        color=discord.Color.red()
    )

    embed.description = (
        f"**{event['nom']}**\n"
        f"Length: {event['duree']}m 00s\n\n"
        f"**Starts**\n"
        f"<t:{debut_ts}:R>\n\n"
        f"**Fin**\n"
        f"<t:{fin_ts}:R>"
    )

    if debut <= maintenant < fin:
        embed.description += "\n\n**🔴 LIVE now**"

    return embed


# =========================================================
# ENVOYER UN MESSAGE DISCORD
# =========================================================

async def envoyer_message(event, maintenant):
    global salon_events

    if event is None:
        print("❌ Aucun événement à afficher.")
        return False

    if salon_events is None:
        try:
            salon_events = await bot.fetch_channel(EVENT_SALON_ID)
        except discord.HTTPException as erreur:
            print(f"❌ Salon introuvable : {erreur}")
            return False

    role_id = EVENT_ROLE_IDS.get(event["nom"])
    if role_id is None:
        print(f"❌ Aucun rôle configuré pour {event['nom']}.")
        contenu = f"🔥 **STEAL THE BRAINROT**\n\nL'événement **{event['nom']}** commence !"
        mentions = discord.AllowedMentions.none()
    else:
        contenu = (
            f"<@&{role_id}>\n\n"
            f"🔥 **STEAL THE BRAINROT**\n\n"
            f"L'événement **{event['nom']}** commence !"
        )
        mentions = discord.AllowedMentions(roles=True)

    try:
        await salon_events.send(
            content=contenu,
            embed=creer_embed(event, maintenant),
            allowed_mentions=mentions
        )
        print(f"✅ Message envoyé pour : {event['nom']}")
        return True

    except discord.Forbidden:
        print(
            "❌ Permissions insuffisantes dans le salon. "
            "Vérifie que le bot peut voir le salon et envoyer des messages."
        )
        return False

    except discord.HTTPException as erreur:
        print(f"❌ Erreur Discord : {erreur}")
        return False


# =========================================================
# BOUCLE AUTOMATIQUE DES ANNONCES
# =========================================================

@tasks.loop(seconds=5)
async def verifier_events():
    maintenant = datetime.now(PARIS)
    occurrences = obtenir_occurrences()

    # Nettoyer les anciens créneaux
    limite = maintenant.date() - timedelta(days=2)
    anciennes_cles = {
        cle for cle in horaires_annonces if cle[0] < limite.isoformat()
    }
    horaires_annonces.difference_update(anciennes_cles)

    # Chaque événement est annoncé séparément, à son heure de début.
    # La petite fenêtre de 10 secondes permet de tenir compte du cycle de 5 s.
    for event in occurrences:
        cle = cle_event(event)
        debut = event["debut"]

        if cle in horaires_annonces:
            continue

        if debut <= maintenant < debut + timedelta(seconds=10):
            succes = await envoyer_message(event, maintenant)
            if succes:
                horaires_annonces.add(cle)


# =========================================================
# GESTION DES ERREURS
# =========================================================

@verifier_events.error
async def verifier_events_error(erreur):
    print(f"❌ Erreur de la boucle : {erreur}")


# =========================================================
# DÉMARRAGE DU BOT
# =========================================================

@bot.event
async def on_ready():
    global salon_events
    global demarrage_effectue

    print(f"🤖 Bot connecté : {bot.user}")
    print(f"🏠 Serveur : {GUILD_ID}")
    print(f"📢 Salon : {EVENT_SALON_ID}")
    print("🔔 Rôles par événement configurés")
    print("🕐 Fuseau : Europe/Paris")
    print(f"⏱️ Events : {DUREE_EVENT} minutes")
    print(f"🧊 Chill Hour : {DUREE_CHILL} minutes")
    print("📣 Annonces : à l'heure de début, sans annonce 10 minutes avant")

    if not demarrage_effectue:
        try:
            salon_events = await bot.fetch_channel(EVENT_SALON_ID)
            maintenant = datetime.now(PARIS)
            occurrences = obtenir_occurrences()

            # Au démarrage, afficher les deux prochains événements,
            # chacun dans son propre message avec son rôle associé.
            events_demarrage = obtenir_deux_events(occurrences, maintenant)
            for event in events_demarrage:
                await envoyer_message(event, maintenant)

            demarrage_effectue = True
            print("✅ Messages de démarrage traités.")

        except discord.HTTPException as erreur:
            print(f"❌ Erreur au démarrage : {erreur}")

    if not verifier_events.is_running():
        verifier_events.start()
        print("✅ Système automatique activé !")


# =========================================================
# LANCEMENT DU BOT
# =========================================================

if not TOKEN:
    raise ValueError(
        "DISCORD_TOKEN est introuvable. "
        "Vérifie les variables d'environnement Railway."
    )

bot.run(TOKEN, reconnect=True)
