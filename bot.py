$code = @'
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
    "GOTHIC": ["19:00"],
    "ADMIN MACHINE": ["18:30", "00:30"],
    "HEAVEN": ["21:00", "23:30"]
}

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

messages_envoyes = {}


def obtenir_salon():
    return bot.get_channel(EVENT_SALON_ID)


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

    en_cours = (
        debut <= maintenant < fin
    )

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


async def envoyer_message(
    premier,
    deuxieme,
    raison
):

    salon = obtenir_salon()

    if salon is None:

        print(
            f"❌ Salon introuvable : {EVENT_SALON_ID}"
        )

        return

    cle = (
        f"{premier['nom']}-"
        f"{premier['debut'].strftime('%Y%m%d%H%M')}"
    )

    if cle in messages_envoyes:

        return

    embed1 = creer_embed(
        premier
    )

    embed2 = creer_embed(
        deuxieme
    )

    try:

        message = await salon.send(
            content=f"<@&{EVENT_PING_ROLE_ID}>",
            embeds=[
                embed1,
                embed2
            ],
            allowed_mentions=discord.AllowedMentions(
                roles=True
            )
        )

        messages_envoyes[cle] = {
            "message": message,
            "premier": premier,
            "deuxieme": deuxieme
        }

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


async def mettre_a_jour_messages():

    maintenant = datetime.now(PARIS)

    for cle, info in list(
        messages_envoyes.items()
    ):

        premier = info["premier"]
        deuxieme = info["deuxieme"]

        embed1 = creer_embed(
            premier
        )

        embed2 = creer_embed(
            deuxieme
        )

        try:

            await info["message"].edit(
                embeds=[
                    embed1,
                    embed2
                ]
            )

        except discord.NotFound:

            messages_envoyes.pop(
                cle,
                None
            )

        except discord.HTTPException:

            pass


async def verifier_et_envoyer():

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

    # -----------------------------------------
    # CAS 1 : prochain event dans 10 minutes
    # -----------------------------------------

    moment_annonce = (
        premier["debut"]
        - timedelta(
            minutes=ANNONCE_AVANT
        )
    )

    if (
        moment_annonce
        <= maintenant
        < premier["debut"]
    ):

        await envoyer_message(
            premier,
            deuxieme,
            "10 minutes avant"
        )

        return

    # -----------------------------------------
    # CAS 2 : le premier event est actuellement LIVE
    # -----------------------------------------

    if (
        premier["debut"]
        <= maintenant
        < premier["fin"]
    ):

        # Si le bot a redémarré pendant l'event
        # et qu'aucun message n'existe encore,
        # on envoie quand même la paire.

        if cle not in messages_envoyes:

            await envoyer_message(
                premier,
                deuxieme,
                "event actuellement LIVE"
            )

        return

    # -----------------------------------------
    # CAS 3 : le premier event est terminé
    # -----------------------------------------
    #
    # Dans ce cas, occurrences[0] est automatiquement
    # le prochain event, et occurrences[1] celui d'après.
    #
    # On envoie immédiatement une nouvelle paire.

    if maintenant >= premier["fin"]:

        await envoyer_message(
            premier,
            deuxieme,
            "event précédent terminé"
        )


@tasks.loop(seconds=5)
async def boucle_events():

    await verifier_et_envoyer()

    await mettre_a_jour_messages()


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
        "⏳ Durée : 20 minutes"
    )

    print(
        "📦 2 embeds dans le même message"
    )

    print(
        "🔄 Nouveau message après chaque fin"
    )

    print(
        "🌴 JUNGLE : 16:00 / 22:00"
    )

    print(
        "======================================"
    )

    salon = obtenir_salon()

    if salon:

        print(
            f"✅ Salon trouvé : #{salon.name}"
        )

    else:

        print(
            "❌ Salon introuvable."
        )

    if not boucle_events.is_running():

        boucle_events.start()

        print(
            "✅ Système Events activé !"
        )


print(
    "🚀 Démarrage du bot..."
)

if not TOKEN:

    print(
        "❌ DISCORD_TOKEN introuvable dans .env"
    )

else:

    bot.run(
        TOKEN,
        reconnect=True
    )
'@

Set-Content -Path "bot.py" -Value $code -Encoding UTF8

Write-Host ""
Write-Host "======================================"
Write-Host "✅ BOT MIS A JOUR"
Write-Host "📢 Salon : 1543989597900513291"
Write-Host "📦 2 embeds par message"
Write-Host "📢 Annonce 10 minutes avant"
Write-Host "🔄 Nouveau message après chaque fin"
Write-Host "⏳ Durée : 20 minutes"
Write-Host "🌴 JUNGLE : 16:00 / 22:00"
Write-Host "🔔 @Event Ping"
Write-Host "🚫 Aucun lien Discord"
Write-Host "======================================"
Write-Host ""
Write-Host "🚀 Lancement..."
Write-Host ""

python bot.py
