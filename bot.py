
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
