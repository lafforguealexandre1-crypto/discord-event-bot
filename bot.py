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

# ID du rôle à mentionner pour chaque événement
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
# HORAIRES QUOTIDIENS DES ÉVÉNEMENTS
# Gothic est bien à 01:00. Aqua est nommé UNDERWATER dans le code.
# =========================================================

HORAIRES_EVENTS = [
    ("GOTHIC", "01:00", DUREE_EVENT),
    ("UNDERWATER", "01:00", DUREE_EVENT),
    ("VOID", "02:00", DUREE_EVENT),
    ("RAVE", "02:30", DUREE_EVENT),
    ("HALLOWEEN", "03:00", DUREE_EVENT),
    ("MAGICAL", "04:00", DUREE_EVENT),
    ("SUMMER", "04:30", DUREE_EVENT),
    ("CHILL HOUR", "04:30", DUREE_CHILL),
    ("ADMIN MACHINE", "05:30", DUREE_EVENT),
    ("GOTHIC", "06:00", DUREE_EVENT),
    ("VOID", "07:00", DUREE_EVENT),
    ("RAVE", "08:30", DUREE_EVENT),
    ("HALLOWEEN", "09:00", DUREE_EVENT),
    ("TOKYO", "10:00", DUREE_EVENT),
    ("UNDERWATER", "10:30", DUREE_EVENT),
    ("CHILL HOUR", "10:30", DUREE_CHILL),
    ("JUNGLE", "13:30", DUREE_EVENT),
    ("HALLOWEEN", "15:00", DUREE_EVENT),
    ("MAGICAL", "16:00", DUREE_EVENT),
    ("SUMMER", "16:30", DUREE_EVENT),
    ("CHILL HOUR", "16:30", DUREE_CHILL),
    ("HALLOWEEN", "17:00", DUREE_EVENT),
    ("ADMIN MACHINE", "17:30", DUREE_EVENT),
    ("GOTHIC", "18:00", DUREE_EVENT),
    ("TOKYO", "19:00", DUREE_EVENT),
    ("JUNGLE", "19:30", DUREE_EVENT),
    ("HEAVEN", "20:00", DUREE_EVENT),
    ("RAVE", "20:30", DUREE_EVENT),
    ("HALLOWEEN", "21:00", DUREE_EVENT),
    ("VOID", "22:00", DUREE_EVENT),
    ("HEAVEN", "22:30", DUREE_EVENT),
    ("CHILL HOUR", "22:30", DUREE_CHILL),
    ("ADMIN MACHINE", "23:30", DUREE_EVENT),
]

# =========================================================
# INITIALISATION DISCORD
# =========================================================

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
salon_events = None
horaires_annonces = set()
message_demarrage_envoye = False


def creer_datetime(date_base, heure):
    heures, minutes = map(int, heure.split(":"))
    return datetime(
        date_base.year, date_base.month, date_base.day,
        heures, minutes, tzinfo=PARIS
    )


def obtenir_occurrences():
    maintenant = datetime.now(PARIS)
    occurrences = []

    for jour_offset in range(JOURS_CALCUL):
        date_base = maintenant.date() + timedelta(days=jour_offset)

        for index, (nom, heure, duree) in enumerate(HORAIRES_EVENTS):
            debut = creer_datetime(date_base, heure)
            # 23:30 est suivi de l'événement prévu à 00:30 le lendemain
            # dans l'ancien planning; dans ce planning, le dernier horaire est 23:30.
            fin = debut + timedelta(minutes=duree)
            occurrences.append({
                "nom": nom,
                "debut": debut,
                "fin": fin,
                "duree": duree,
                "index": index,
            })

    occurrences.sort(key=lambda event: (event["debut"], event["index"]))
    return occurrences


def cle_creneau(debut):
    # Une clé par date et heure : les événements simultanés seront regroupés.
    return debut.date().isoformat(), debut.strftime("%H:%M")


def creer_embed(event, maintenant):
    debut_ts = int(event["debut"].timestamp())
    fin_ts = int(event["fin"].timestamp())
    embed = discord.Embed(
        title=f"{event['nom']} | <t:{debut_ts}:t> ➜ <t:{fin_ts}:t>",
        color=discord.Color.red(),
    )
    embed.description = (
        f"**{event['nom']}**\n"
        f"Length: {event['duree']}m 00s\n\n"
        f"**Starts**\n<t:{debut_ts}:R>\n\n"
        f"**Fin**\n<t:{fin_ts}:R>"
    )
    if event["debut"] <= maintenant < event["fin"]:
        embed.description += "\n\n**🔴 LIVE now**"
    return embed


async def envoyer_message_evenements(evenements, maintenant):
    """Envoie un seul message pour tous les événements qui commencent ensemble."""
    global salon_events

    if not evenements:
        return False

    if salon_events is None:
        try:
            salon_events = await bot.fetch_channel(EVENT_SALON_ID)
        except discord.HTTPException as erreur:
            print(f"❌ Salon introuvable : {erreur}")
            return False

    role_mentions = []
    noms = []
    embeds = []
    for event in evenements:
        noms.append(event["nom"])
        role_id = EVENT_ROLE_IDS.get(event["nom"])
        if role_id is not None:
            role_mentions.append(f"<@&{role_id}>")
        else:
            print(f"⚠️ Aucun rôle configuré pour {event['nom']}.")
        embeds.append(creer_embed(event, maintenant))

    contenu = " ".join(role_mentions)
    contenu += "\n\n🔥 **STEAL THE BRAINROT**\n\n"
    if len(evenements) == 1:
        contenu += f"L'événement **{noms[0]}** commence !"
    else:
        contenu += "Les événements suivants commencent !\n"
        contenu += "\n".join(f"• **{nom}**" for nom in noms)

    # Discord accepte au maximum 10 embeds par message.
    # Les horaires normaux ont bien moins de 10 événements simultanés.
    try:
        await salon_events.send(
            content=contenu,
            embeds=embeds[:10],
            allowed_mentions=discord.AllowedMentions(roles=True),
        )
        print(f"✅ Message envoyé : {', '.join(noms)}")
        return True
    except discord.Forbidden:
        print("❌ Permissions insuffisantes : vérifie les permissions du salon.")
    except discord.HTTPException as erreur:
        print(f"❌ Erreur Discord : {erreur}")
    return False


@tasks.loop(seconds=5)
async def verifier_events():
    maintenant = datetime.now(PARIS)
    occurrences = obtenir_occurrences()

    # Regroupe les événements par date et heure de début.
    groupes = {}
    for event in occurrences:
        groupes.setdefault(cle_creneau(event["debut"]), []).append(event)

    limite = (maintenant.date() - timedelta(days=2)).isoformat()
    horaires_annonces.difference_update(
        cle for cle in list(horaires_annonces) if cle[0] < limite
    )

    for cle, evenements in groupes.items():
        debut = evenements[0]["debut"]
        if cle in horaires_annonces:
            continue

        # Envoi à l'heure prévue; fenêtre courte pour compenser le cycle de 5 secondes.
        if debut <= maintenant < debut + timedelta(seconds=10):
            succes = await envoyer_message_evenements(evenements, maintenant)
            if succes:
                horaires_annonces.add(cle)


@verifier_events.error
async def verifier_events_error(erreur):
    print(f"❌ Erreur de la boucle : {erreur}")


@bot.event
async def on_ready():
    global salon_events, message_demarrage_envoye
    print(f"🤖 Bot connecté : {bot.user}")
    print(f"🏠 Serveur configuré : {GUILD_ID}")
    print(f"📢 Salon des annonces : {EVENT_SALON_ID}")
    print("🔔 Mentions de rôles spécifiques par événement activées")
    print("🕐 Fuseau horaire : Europe/Paris")
    print("📣 Annonces uniquement à l'heure de début")
    print("📩 Un seul message par horaire; événements simultanés regroupés")

    try:
        salon_events = await bot.fetch_channel(EVENT_SALON_ID)
    except discord.HTTPException as erreur:
        print(f"❌ Impossible de récupérer le salon : {erreur}")
        salon_events = None

    # Envoie un seul message de confirmation à chaque démarrage du processus.
    # Si Discord reconnecte simplement le bot, ne renvoie pas ce message.
    if salon_events is not None and not message_demarrage_envoye:
        try:
            await salon_events.send(
                "✅ **Mise à jour du bot effectuée !**\n"
                "🤖 Le bot a démarré correctement et les annonces sont activées.\n"
                "⏰ Les événements seront annoncés à leur heure prévue.",
                allowed_mentions=discord.AllowedMentions.none(),
            )
            message_demarrage_envoye = True
            print("✅ Message de démarrage envoyé.")
        except discord.Forbidden:
            print("❌ Le bot n'a pas la permission d'envoyer le message de démarrage.")
        except discord.HTTPException as erreur:
            print(f"❌ Échec du message de démarrage : {erreur}")

    # Aucun événement futur n'est annoncé au démarrage.
    # La boucle attend l'heure prévue du prochain événement.
    if not verifier_events.is_running():
        verifier_events.start()
        print("✅ Système automatique activé !")


if not TOKEN:
    raise ValueError(
        "DISCORD_TOKEN est introuvable. Vérifie les variables d'environnement Railway."
    )

bot.run(TOKEN, reconnect=True)
