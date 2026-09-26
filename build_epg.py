import copy
import gzip
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict

SOURCE_URL = (
    "https://epgshare01.online/epgshare01/"
    "epg_ripper_DE1.xml.gz"
)

OUTPUT_FILE = "epg.xml.gz"

aliases = defaultdict(set)


def add(source_id, *names):
    for name in names:
        name = name.strip()

        if not name:
            continue

        aliases[source_id].add(name)

        # Manche Apps/Listen benutzen zusätzlich "DE: "
        if not name.startswith("DE: "):
            aliases[source_id].add("DE: " + name)


def qualities(source_id, name, values):
    for quality in values:
        add(source_id, f"{name} {quality}")


# ============================================================
# SKY BUNDESLIGA
# ============================================================

for n in range(1, 11):

    source = f"Sky.Sport.Bundesliga.{n}.de"

    qualities(
        source,
        f"Bndliga {n}",
        ("FHD", "HD", "SD", "Mobile"),
    )

    qualities(
        source,
        f"Bundesliga {n}",
        ("FHD", "HD", "SD", "Mobile"),
    )


# Zusatzvarianten Bundesliga 1

add(
    "Sky.Sport.Bundesliga.1.de",

    "Bndliga 1 UHD",
    "Bndliga 1 FEED",

    "Bundesliga 1 UHD",
    "Bundesliga 1 FEED",
)


# Separater UHD-/4K-Sender

add(
    "Sky.Sport.Bundesliga.UHD.de",

    "Bndliga UHD",
    "Bndliga 4K",

    "Bundesliga UHD",
    "Bundesliga 4K",

    "Sky Bundesliga UHD",
    "Sky Bundesliga 4K",
)


add(
    "Sky.Sport.Bundesliga.de",

    "Bndliga",
    "Bundesliga",
    "Sky Bundesliga",
)


# ============================================================
# SKY SPORT
# ============================================================

for n in range(1, 11):

    source = f"Sky.Sport.{n}.de"

    qualities(
        source,
        f"Sky Sport {n}",
        ("FHD", "HD", "SD", "Mobile"),
    )


qualities(
    "Sky.Sport.F1.de",
    "Sky Sport F1",
    ("FHD", "HD"),
)

qualities(
    "Sky.Sport.Golf.de",
    "Sky Sport Golf",
    ("FHD", "HD"),
)

qualities(
    "Sky.Sport.Mix.de",
    "Sky Sport Mix",
    ("FHD", "HD"),
)

qualities(
    "Sky.Sport.News.de",
    "Sky Sport News",
    ("FHD", "HD"),
)

qualities(
    "Sky.Sport.Premier.League.de",
    "Sky Sport Premier League",
    ("FHD", "HD"),
)

qualities(
    "Sky.Sport.Tennis.de",
    "Sky Sport Tennis",
    ("FHD", "HD"),
)

qualities(
    "Sky.Sport.Top.Event.de",
    "Sky Sport Top Event",
    ("FHD", "HD"),
)

add(
    "Sky.Sport.UHD.de",
    "Sky Sport UHD",
    "Sky Sport 4K",
)


# ============================================================
# DAZN
# ============================================================

for n in (1, 2):

    source = f"DAZN.{n}.de"

    qualities(
        source,
        f"DAZN {n}",
        ("FHD", "HD", "SD"),
    )

    add(
        source,
        f"DAZN {n} Vip",
        f"DAZN {n} VIP",
    )


add(
    "DAZN.de",
    "DAZN",
)


# ============================================================
# SKY CINEMA
# ============================================================

qualities(
    "Sky.Cinema.Action.HD.de",
    "Sky Cinema Action",
    ("FHD", "HD"),
)

qualities(
    "Sky.Cinema.Premiere.HD.de",
    "Sky Cinema Premiere",
    ("FHD", "HD"),
)

qualities(
    "Sky.Cinema.Classics.HD.de",
    "Sky Cinema Classics",
    ("FHD", "HD"),
)


# Family heißt seit Mai 2026 Feelgood

qualities(
    "Sky.Cinema.Family.HD.de",
    "Sky Cinema Feelgood",
    ("FHD", "HD"),
)


# Highlights heißt seit Mai 2026 Blockbuster

qualities(
    "Sky.Cinema.Highlights.HD.de",
    "Sky Cinema Blockbuster",
    ("FHD", "HD"),
)


# ============================================================
# SKY ENTERTAINMENT
# ============================================================

qualities(
    "Sky.One.de",
    "Sky One",
    ("FHD", "HD"),
)

qualities(
    "Sky.One.de",
    "Sky ONE",
    ("FHD", "HD"),
)

qualities(
    "Sky.Atlantic.HD.de",
    "Sky Atlantic",
    ("FHD", "HD"),
)

qualities(
    "Sky.Crime.de",
    "Sky Crime",
    ("FHD", "HD"),
)

qualities(
    "Sky.Documentaries.de",
    "Sky Documentaries",
    ("FHD", "HD"),
)

qualities(
    "Sky.Krimi.de",
    "Sky Krimi",
    ("FHD", "HD"),
)

qualities(
    "Sky.Nature.de",
    "Sky Nature",
    ("FHD", "HD"),
)

qualities(
    "Sky.Showcase.HD.de",
    "Sky Showcase",
    ("FHD", "HD"),
)

qualities(
    "Sky.Replay.HD.de",
    "Sky Replay",
    ("FHD", "HD"),
)


# ============================================================
# EUROSPORT
# ============================================================

qualities(
    "Eurosport.1.de",
    "Eurosport 1",
    ("FHD", "HD"),
)

qualities(
    "Eurosport.2.de",
    "Eurosport 2",
    ("FHD", "HD"),
)


# ============================================================
# SPORT1 / SPORTDIGITAL / ESPORTS
# ============================================================

qualities(
    "eSports1.de",
    "eSports 1",
    ("FHD", "HD"),
)

qualities(
    "eSports1.de",
    "eSports1",
    ("FHD", "HD"),
)


qualities(
    "SPORT1+.de",
    "Sport1+",
    ("FHD", "HD"),
)


add(
    "SPORT1.de",

    "Sport1 Vip",
    "Sport1 VIP",
    "Sport1 FHD",
    "Sport1 HD",
)


qualities(
    "sportdigital.Fussball.de",
    "Sport Digital",
    ("FHD", "HD"),
)

qualities(
    "sportdigital.Fussball.de",
    "Sportdigital Fussball",
    ("FHD", "HD"),
)


# ============================================================
# WEITERE SPORTKANÄLE
# ============================================================

add(
    "Auto.Motor.Sport.de",

    "Auto Motor und Sport",
    "Auto Motor & Sport",
)


qualities(
    "Motorvision.TV.de",
    "Motorvision TV",
    ("FHD", "HD"),
)


qualities(
    "More.than.Sports.TV.de",
    "More Than Sports TV",
    ("FHD", "HD"),
)


add(
    "MS.Sport.de",

    "MS SPORT",
    "MS Sport",
)


add(
    "DFB.Play.de",

    "DFB Play",
    "DFB PLAY",
)


# ============================================================
# MYTEAM TV 1 - 18
# ============================================================

for n in range(1, 19):

    source = f"Sport.{n}.-.myTeamTV.de"

    add(
        source,

        f"MyTeam TV - {n}",
        f"MyTeam TV {n}",

        f"myTeam TV - {n}",
        f"myTeamTV - {n}",
    )


# ============================================================
# AMAZON PRIME
# ============================================================

for name in (

    "AMAZON PRIME RAW",
    "AMAZON PRIME FHD",
    "AMAZON PRIME HD",
    "AMAZON PRIME SD",
    "AMAZON PRIME BACKUP",

):

    add(
        "Prime.HD.de",
        name,
    )


# ============================================================
# FILM / SERIEN - REGULÄRE TV-SENDER
# ============================================================

qualities(
    "Universal.Channel.HD.de",
    "Universal",
    ("FHD", "HD"),
)


add(
    "Silverline.de",
    "Silverline",
)


add(
    "KinoweltTV.de",

    "Kinowelt Tv",
    "Kinowelt TV",
)


add(
    "Tele.5.de",

    "TELE 5",
    "Tele 5",
)


qualities(
    "AXN.Black.de",
    "AXN Black",
    ("FHD", "HD"),
)


qualities(
    "AXN.White.de",
    "AXN White",
    ("FHD", "HD"),
)


qualities(
    "Warner.TV.Film.de",
    "Warner TV Film",
    ("FHD", "HD"),
)


qualities(
    "Warner.TV.Serie.de",
    "Warner TV Serie",
    ("FHD", "HD"),
)


qualities(
    "Warner.TV.Comedy.de",
    "Warner TV Comedy",
    ("FHD", "HD"),
)


# ============================================================
# DEUTSCHE STANDARD-SENDER
# ============================================================

common_channels = {

    "Das.Erste.de":
        "Das Erste",

    "ZDF.de":
        "ZDF",

    "RTL.de":
        "RTL",

    "RTLZWEI.de":
        "RTLZWEI",

    "VOX.de":
        "VOX",

    "ProSieben.de":
        "ProSieben",

    "SAT.1.de":
        "SAT.1",

    "kabel.eins.de":
        "Kabel Eins",

    "NITRO.de":
        "NITRO",

    "SUPER.RTL.de":
        "SUPER RTL",

    "DMAX.de":
        "DMAX",

    "TLC.de":
        "TLC",

    "sixx.de":
        "sixx",

    "ZDFneo.de":
        "ZDFneo",

    "ZDFinfo.de":
        "ZDFinfo",

    "3sat.de":
        "3sat",

    "ARTE.de":
        "ARTE",

    "ONE.de":
        "ONE",

    "
