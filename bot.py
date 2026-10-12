
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
AVANCE_ANNONCE = 10
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

async def envoyer_message(events, maintenant):
    global salon_events

    if not events:
        print("❌ Aucun événement à afficher.")
        return False

    if salon_events is None:
        try:
            salon_events = await bot.fetch_channel(
                EVENT_SALON_ID
            )
        except discord.HTTPException as erreur:
            print(f"❌ Salon introuvable : {erreur}")
            return False

    embeds = [
        creer_embed(event, maintenant)
        for event in events
    ]

    contenu = (
        f"<@&{EVENT_PING_ROLE_ID}>\n\n"
        f"🔥 **STEAL THE BRAINROT**\n\n"
        f"Voici les prochains events :"
    )

    try:
        await salon_events.send(
            content=contenu,
            embeds=embeds,
            allowed_mentions=discord.AllowedMentions(
                roles=True
            )
        )

        print(
            "✅ Message envoyé : "
            + " / ".join(
                event["nom"] for event in events
            )
        )

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
        cle
        for cle in horaires_annonces
        if cle[0] < limite.isoformat()
    }

    horaires_annonces.difference_update(anciennes_cles)

    # Regrouper les événements qui commencent à la même heure
    groupes = {}

    for event in occurrences:
        cle = cle_event(event)
        groupes.setdefault(cle[:2], []).append(event)

    for cle_horaire, events_meme_horaire in groupes.items():
        debut = events_meme_horaire[0]["debut"]

        moment_annonce = debut - timedelta(
            minutes=AVANCE_ANNONCE
        )

        cles = [
            cle_event(event)
            for event in events_meme_horaire
        ]

        if all(cle in horaires_annonces for cle in cles):
            continue

        if moment_annonce <= maintenant < debut:
            affiches = list(events_meme_horaire)

            futurs = [
                event
                for event in occurrences
                if event["debut"] > debut
            ]

            for event in futurs:
                if len(affiches) >= 2:
                    break

                affiches.append(event)

            succes = await envoyer_message(
                affiches[:2],
                maintenant
            )

            if succes:
                horaires_annonces.update(cles)


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
    print(f"🔔 Event Ping : {EVENT_PING_ROLE_ID}")
    print("🕐 Fuseau : Europe/Paris")
    print(f"⏱️ Events : {DUREE_EVENT} minutes")
    print(f"🧊 Chill Hour : {DUREE_CHILL} minutes")
    print(f"📣 Annonces : {AVANCE_ANNONCE} minutes avant")

    if not demarrage_effectue:
        try:
            salon_events = await bot.fetch_channel(
                EVENT_SALON_ID
            )

            maintenant = datetime.now(PARIS)
            occurrences = obtenir_occurrences()

            # Envoyer immédiatement les deux prochains événements
            events_demarrage = obtenir_deux_events(
                occurrences,
                maintenant
            )

            succes = await envoyer_message(
                events_demarrage,
                maintenant
            )

            if succes:
                print("✅ Message de démarrage envoyé !")

                # Éviter de répéter immédiatement les mêmes créneaux
                for event in events_demarrage:
                    horaires_annonces.add(
                        cle_event(event)
                    )
            else:
                print(
                    "❌ Le message de démarrage n'a pas pu être envoyé."
                )

            demarrage_effectue = True

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
