#!/usr/bin/env python3

import copy
import gzip
import html
import re
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from io import BytesIO

OUTPUT_FILE = "epg.xml.gz"

# Hauptquelle. Weitere Quellen können später einfach ergänzt werden.
SOURCE_URLS = [
    "https://epgshare01.online/epgshare01/epg_ripper_DE1.xml.gz",
]

QUALITY_WORDS = {
    "hd", "fhd", "sd", "uhd", "4k", "mobile",
    "feed", "vip", "raw", "backup", "event", "only"
}


def clean_text(value):
    if not value:
        return ""
    old = value
    for _ in range(3):
        new = html.unescape(old)
        if new == old:
            break
        old = new
    return old


def normalize(value):
    value = clean_text(value)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        ch for ch in value
        if not unicodedata.combining(ch)
    ).lower()

    value = value.replace("&", " und ")
    value = value.replace("+", " plus ")
    value = value.replace("sportdigital", "sport digital")
    value = value.replace("eurosport", "euro sport")
    value = value.replace("bndliga", "bundesliga")
    value = value.replace("myteamtv", "myteam tv")

    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)

    words = [
        word for word in value.split()
        if word not in QUALITY_WORDS
    ]
    return " ".join(words).strip()


def channel_names(channel):
    result = []
    for node in channel.findall("display-name"):
        if node.text:
            result.append(clean_text(node.text).strip())
    return result


def fix_entities(root):
    visible_tags = {
        "display-name", "title", "sub-title",
        "desc", "category", "country",
        "language", "rating"
    }
    for elem in root.iter():
        if elem.tag in visible_tags and elem.text:
            elem.text = clean_text(elem.text)


def alias_id(name):
    slug = normalize(name).replace(" ", ".")
    slug = re.sub(r"[^a-z0-9.]+", "", slug).strip(".")
    return "vera." + (slug or "channel")


def download_xml(url):
    print(f"Lade EPG: {url}")
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (GitHub Actions EPG Builder)"
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()

    if url.lower().endswith(".gz"):
        with gzip.GzipFile(fileobj=BytesIO(data)) as gz:
            data = gz.read()

    root = ET.fromstring(data)
    fix_entities(root)
    return root


def merge_sources(urls):
    merged = ET.Element(
        "tv",
        {
            "generator-info-name": "Schalke-Fan my-epg",
            "generator-info-url": "https://github.com/Schalke-Fan/my-epg",
        },
    )

    seen_channels = set()
    seen_programmes = set()

    loaded = 0

    for url in urls:
        try:
            root = download_xml(url)
        except Exception as exc:
            print(f"WARNUNG: Quelle konnte nicht geladen werden: {url}")
            print(f"         {type(exc).__name__}: {exc}")
            continue

        loaded += 1

        for channel in root.findall("channel"):
            cid = channel.get("id")
            if not cid or cid in seen_channels:
                continue
            merged.append(copy.deepcopy(channel))
            seen_channels.add(cid)

        for programme in root.findall("programme"):
            cid = programme.get("channel")
            start = programme.get("start", "")
            stop = programme.get("stop", "")
            title_node = programme.find("title")
            title = title_node.text if title_node is not None and title_node.text else ""

            key = (cid, start, stop, title)
            if key in seen_programmes:
                continue

            merged.append(copy.deepcopy(programme))
            seen_programmes.add(key)

    if loaded == 0:
        raise RuntimeError("Keine EPG-Quelle konnte geladen werden.")

    return merged


# ---------------------------------------------------------------------
# Alias-Regeln
# ---------------------------------------------------------------------

ALIAS_REQUESTS = []


def add(source_candidates, *aliases, fallback=False, fallback_title=None):
    if source_candidates is None:
        source_candidates = []
    elif isinstance(source_candidates, str):
        source_candidates = [source_candidates]

    ALIAS_REQUESTS.append(
        {
            "sources": list(source_candidates),
            "aliases": list(aliases),
            "fallback": fallback,
            "fallback_title": fallback_title,
        }
    )


# ---------------------------------------------------------------------
# SKY BUNDESLIGA
# ---------------------------------------------------------------------

for n in range(1, 11):
    aliases = [
        f"Bndliga {n} FHD",
        f"Bndliga {n} HD",
        f"Bndliga {n} SD",
    ]

    if n <= 6:
        aliases.append(f"Bndliga {n} Mobile")

    if n == 1:
        aliases += [
            "Bndliga 1 UHD",
            "Bndliga 1 FEED",
            "Bndliga UHD",
            "Bndliga 4K",
        ]

    add(
        [
            f"Sky.Sport.Bundesliga.{n}.de",
            f"Sky Sport Bundesliga {n}",
            f"Sky Bundesliga {n}",
            f"Bundesliga {n}",
        ],
        *aliases,
        fallback=True,
    )


# ---------------------------------------------------------------------
# DAZN
# ---------------------------------------------------------------------

for n in (1, 2):
    add(
        [
            f"DAZN.{n}.de",
            f"DAZN {n}",
            f"DAZN{n}",
        ],
        f"DAZN {n} Vip",
        f"DAZN {n} FHD",
        f"DAZN {n} HD",
        f"DAZN {n} SD",
        fallback=True,
    )


# ---------------------------------------------------------------------
# SKY CINEMA / ENTERTAINMENT
# ---------------------------------------------------------------------

add(
    [
        "Sky.Cinema.Action.HD.de",
        "Sky Cinema Action HD",
        "Sky Cinema Action",
    ],
    "Sky Cinema Action HD",
    "Sky Cinema Action FHD",
    fallback=True,
)

# Sky Cinema Feelgood ist der Nachfolger von Sky Cinema Family.
add(
    [
        "Sky.Cinema.Family.HD.de",
        "Sky Cinema Family HD",
        "Sky Cinema Family",
        "Sky Cinema Feelgood",
        "Sky Cinema Feel Good",
    ],
    "Sky Cinema Feelgood HD",
    "Sky Cinema Feelgood FHD",
    fallback=True,
)

add(
    [
        "Sky.Cinema.Premiere.HD.de",
        "Sky Cinema Premiere HD",
        "Sky Cinema Premiere",
    ],
    "Sky Cinema Premiere HD",
    "Sky Cinema Premiere FHD",
    fallback=True,
)

# Sky Cinema Blockbuster ist der Nachfolger von Sky Cinema Highlights.
add(
    [
        "Sky.Cinema.Highlights.HD.de",
        "Sky Cinema Highlights HD",
        "Sky Cinema Highlights",
        "Sky Cinema Blockbuster",
    ],
    "Sky Cinema Blockbuster HD",
    "Sky Cinema Blockbuster FHD",
    fallback=True,
)

add(
    [
        "Sky.One.de",
        "Sky One",
    ],
    "Sky ONE HD",
    "Sky One FHD",
    fallback=True,
)

add(
    [
        "Sky.Atlantic.HD.de",
        "Sky Atlantic HD",
        "Sky Atlantic",
    ],
    "Sky Atlantic HD",
    "Sky Atlantic FHD",
    fallback=True,
)


# ---------------------------------------------------------------------
# SPORT
# ---------------------------------------------------------------------

SPORT_MAP = [
    (
        ["Eurosport.1.de", "Eurosport 1", "EuroSport 1"],
        ["Eurosport 1 FHD", "Eurosport 1 HD"],
    ),
    (
        ["Eurosport.2.de", "Eurosport 2", "EuroSport 2"],
        ["Eurosport 2 FHD", "Eurosport 2 HD", "EuroSport 2 Xtra HD"],
    ),
    (
        ["SPORT1.de", "SPORT1", "Sport1", "Sport 1"],
        ["Sport1 Vip", "Sport1 FHD", "Sport1 HD"],
    ),
    (
        ["SPORT1+.de", "SPORT1+", "Sport1+"],
        ["Sport1+ FHD", "Sport1+ HD"],
    ),
    (
        ["sportdigital.Fussball.de", "sportdigital FUSSBALL", "Sportdigital"],
        ["Sport Digital FHD", "Sport Digital HD"],
    ),
    (
        ["Auto.Motor.Sport.de", "Auto Motor Sport", "Auto Motor und Sport"],
        ["Auto Motor und Sport"],
    ),
    (
        ["Motorvision.TV.de", "Motorvision TV", "Motorvision"],
        ["Motorvision TV FHD", "Motorvision TV HD"],
    ),
    (
        ["More.than.Sports.TV.de", "More Than Sports TV"],
        ["More Than Sports TV FHD", "More Than Sports TV HD"],
    ),
    (
        ["eSports1.de", "eSports1", "eSports 1"],
        ["eSports 1 FHD", "eSports 1 HD"],
    ),
    (
        ["DFB.Play.de", "DFB Play"],
        ["DFB Play"],
    ),
    (
        ["MS.Sport.de", "MS Sport"],
        ["MS SPORT"],
    ),
]

for sources, aliases in SPORT_MAP:
    add(sources, *aliases, fallback=True)


# ---------------------------------------------------------------------
# REGULÄRE FILM-/SERIENSENDER
# ---------------------------------------------------------------------

REGULAR_MAP = [
    (["Tele.5.de", "TELE 5", "Tele 5"], ["TELE 5"]),
    (["Silverline.de", "Silverline"], ["Silverline"]),
    (["AXN.Black.de", "AXN Black"], ["AXN Black"]),
    (["AXN.White.de", "AXN White"], ["AXN White"]),
    (["Universal.Channel.HD.de", "Universal TV", "Universal"], ["Universal FHD"]),
    (["KinoweltTV.de", "Kinowelt TV", "Kinowelt"], ["Kinowelt Tv"]),
]

for sources, aliases in REGULAR_MAP:
    add(sources, *aliases, fallback=True)


# ---------------------------------------------------------------------
# WEITERE REGULÄRE SENDER MIT ECHTEM EPG
# ---------------------------------------------------------------------

EXTRA_REGULAR_MAP = [
    (
        ["RTL.Crime.de", "RTL Crime"],
        ["RTL Crime HD", "RTL Crime FHD"],
    ),
    (
        ["Warner.TV.Comedy.de", "Warner TV Comedy"],
        [
            "Warner Comedy HD",
            "Warner Comedy FHD",
            "Warner TV Comedy HD",
            "Warner TV Comedy FHD",
        ],
    ),
    (
        ["Warner.TV.Film.de", "Warner TV Film"],
        [
            "Warner Film HD",
            "Warner Film FHD",
            "Warner TV Film HD",
            "Warner TV Film FHD",
        ],
    ),
    (
        ["Warner.TV.Serie.de", "Warner TV Serie"],
        [
            "Warner Serie HD",
            "Warner Serie FHD",
            "Warner TV Serie HD",
            "Warner TV Serie FHD",
        ],
    ),
    (
        ["Sky.Showcase.HD.de", "sky.showcase.de", "Sky Showcase"],
        ["Sky Showcase HD", "Sky Showcase FHD"],
    ),
    (
        ["Sky.Replay.HD.de", "sky.replay.de", "Sky Replay"],
        ["Sky Replay HD", "Sky Replay FHD"],
    ),
    (
        ["Sky.Crime.de", "Sky Crime"],
        ["Sky Crime HD", "Sky Crime FHD"],
    ),
    (
        ["Sky.Documentaries.de", "Sky Documentaries"],
        ["Sky Documentaries HD", "Sky Documentaries FHD"],
    ),
    (
        ["Sky.Krimi.de", "Sky Krimi"],
        ["Sky Krimi HD", "Sky Krimi FHD"],
    ),
    (
        ["Sky.Nature.de", "Sky Nature"],
        ["Sky Nature HD", "Sky Nature FHD"],
    ),
    (
        ["13th.Street.Universal.de", "13th Street"],
        ["13th Street HD", "13th Street FHD"],
    ),
    (
        ["Discovery.HD.de", "Discovery"],
        ["Discovery HD", "Discovery FHD"],
    ),
    (
        ["SyFy.de", "SyFy"],
        ["SyFy HD", "SyFy FHD"],
    ),
    (
        ["Nat.Geo.HD.de", "National Geographic", "Nat Geo"],
        [
            "National Geographic HD",
            "National Geographic FHD",
            "Nat Geo HD",
            "Nat Geo FHD",
        ],
    ),
    (
        ["NAT.GEO.WILD.de", "Nat Geo Wild"],
        ["Nat Geo Wild HD", "Nat Geo Wild FHD"],
    ),
    (
        ["RTL.Living.de", "RTL Living"],
        ["RTL Living HD", "RTL Living FHD"],
    ),
    (
        ["RTL.Passion.de", "RTL Passion"],
        ["RTL Passion HD", "RTL Passion FHD"],
    ),
]

for sources, aliases in EXTRA_REGULAR_MAP:
    add(sources, *aliases, fallback=True)


# ---------------------------------------------------------------------
# MYTEAM TV / MAGENTA
# ---------------------------------------------------------------------

for n in range(1, 19):
    add(
        [
            f"Sport.{n}.-.myTeamTV.de",
            f"Sport {n} - myTeamTV",
            f"MyTeam TV {n}",
            f"MyTeamTV {n}",
        ],
        f"MyTeam TV - {n}",
        fallback=True,
    )

for n in (1, 2):
    # Wenn keine echte Golf-Quelle vorhanden ist, bleibt wenigstens
    # ein klar gekennzeichneter Platzhalter statt "EPG nicht verfügbar".
    add(
        [],
        f"MS GOLF {n} FHD",
        f"MS GOLF {n} HD",
        fallback=True,
        fallback_title=f"MS GOLF {n} – Eventkanal",
    )


# ---------------------------------------------------------------------
# DYN SPORT 1-25
#
# Diese Nummern sind providerseitige Eventkanäle. Es gibt aktuell keine
# verlässliche öffentliche Zuordnung "DYN SPORT 1 = konkretes Event".
# Daher KEINE erfundenen Spiele: nur klarer Platzhalter.
# ---------------------------------------------------------------------

for n in range(1, 26):
    add(
        [],
        f"DYN SPORT {n}",
        fallback=True,
        fallback_title=f"DYN SPORT {n} – Eventkanal",
    )


# ---------------------------------------------------------------------
# DEL2 EVENT 01-20
# ---------------------------------------------------------------------

for n in range(1, 21):
    add(
        [],
        f"DEL2 EVENT {n:02d}",
        fallback=True,
        fallback_title=f"DEL2 EVENT {n:02d} – Eventkanal",
    )


# ---------------------------------------------------------------------
# SKY SELECT PREMIERE 1-18
# ---------------------------------------------------------------------

add(
    [],
    "Sky Select Premiere Vitrine HD",
    fallback=True,
    fallback_title="Sky Select Premiere Vitrine",
)

for n in range(1, 19):
    add(
        [],
        f"Sky Select Premiere {n} FHD",
        fallback=True,
        fallback_title=f"Sky Select Premiere {n}",
    )


# ---------------------------------------------------------------------
# PROVIDER-EIGENE 24/7-SERIEN UND FILMREIHEN
# ---------------------------------------------------------------------

CUSTOM_NAMES = r"""
Squid Game 24/7
The Challenge - Premium 24/7
Breaking Bad 24/7
Sex Education - Premium 24/7
Sons of Anarchy 24/7
See - Reich der Blinden - Premium 24/7
The Flash - Premium 24/7
The Flash - 2 - Premium 24/7
Babylon Berlin - Premium 24/7
How I Met Your Mother 24/7
ALF 1 - Premium 24/7
ALF 2 - Premium 24/7
Die Simpsons - 1 - Premium 24/7
Die Simpsons - 2 - Premium 24/7
Die Simpsons - 3 - Premium 24/7
Die Simpsons - 4 - Premium 24/7
American Dad! - 1 - Premium 24/7
American Dad! - 2 - Premium 24/7
American Dad! - 3 - Premium 24/7
Family Guy - 1 - Premium 24/7
Family Guy - 2 - Premium 24/7
Family Guy - 3 - Premium 24/7
Rick and Morty - Premium 24/7
POKEMON 24/7
SpongeBob Schwammkopf 24/7
Futurama - 1 - Premium 24/7
Sex and The City 24/7
Sex and The City 24/7 2
Malcolm Mittendrin 24/7
TWO AND A HALF MEN*
Two and a Half Men 24/7***
Two and a Half Men 24/7
The Big Bang Theory 24/7
The Big Bang Theory
Seinfeld - 1 - Premium 24/7
Seinfeld - 2 - Premium 24/7
Fuller House - Premium 24/7
FRIENDS | S01 - S05 | Premium
FRIENDS | S06 - S10 | Premium
King of Queens 1 24/7
King of Queens 24/7 2
Roseanne 1 - Premium 24/7
Roseanne 2 - Premium 24/7
Roseanne 3 - Premium 24/7
Fear The Walking Dead 24/7
THE WALKING DEAD 24/7
Knight Rider - Premium 24/7
Der Bergdoktor 1 24/7
Der Bergdoktor 2 24/7
Der Bergdoktor 3 24/7
Verdacht Mord 24/7
The White Lotus 24/7
Peripherie 24/7
Bad Blood 24/7
Nick Für Ungut 24/7
Ragnarök 24/7
Der Kleine Prinz 24/7
Naruto 24/7
Alle hassen Chris 24/7
Altered Carbon 24/7
True Detective 24/7
Full House 24/7
Chicago Fire 24/7
Stranger Things 24/7
The Witcher 24/7
Bridgerton 24/7
Das Damengambit 24/7
Foundation 24/7
Game Of Thrones 24/7
Gomorrha 24/7
Haus des Geldes 24/7
Lupin 24/7
Snowpiercer - Premium 24/7
IZombie 24/7
Mr. Robot 24/7
Mr. Robot 2 24/7
Oz 24/7
Narcos 24/7
S.W.A.T. 24/7
Riverdale 24/7
Suits 24/7
The Night Shift 24/7
Tote Mädchen lügen nicht 24/7
Tribes of Europa 24/7
Van Helsing 24/7
BETTER CALL SAUL 24/7
SCRUBS 24/7
THE SHAMELESS 24/7
ALPHA HOUSE 24/7
COPPER JUSTICE IS BRUTAL 24/7
ALASKAN BUSH PEOPLE 24/7
EXPEDITION UNKNOWN 24/7
ELEMENTARY 24/7
STAR TREK PICARD 24/7
DIE LUDOLFS 24/7
EUPHORIA 24/7
ARCHIV 81 24/7
VAMPIRE DIARIES 24/7
DU WIRST MICH LIEBEN 24/7
BLINDSPOT 24/7
UNITED STATES OF AL 24/7
MALCOLM MITTENDRIN 2 24/7
MIKE & MOLLY 24/7
TWO AND A HALF MEN
BIG BANG THEORY
THE KING OF QUEENS
BROOKLYN NINE NINE
YOUNG SHELDON
MODERN FAMILY
SILICON VALLEY
THE OFFICE
ALLE LIEBE RAYMOND
ALLE HASSEN CHRIS
2 BROKE GIRLS
FALLOUT
DR. HOUSE
GILMORE GIRLS
COMMUNITY
SEATTLE FIREFIGHTERS
HAWAII FIVE-0
BALLERS
THE BLACKLIST
SUPERNATURAL
THE WALKING DEAD
FEAR THE WALKING DEAD
AMERICAN HORROR STORY
iZOMBIE
GRIMM
GAME OF THRONES
BREAKING BAD
THE SOPRANOS
NARCOS
HAUS DES GELDES
FBI
AKTE X
LOST
S.W.A.T.
SEAL TEAM
DE: 24
4 BLOCKS
COBRA KAI
IP MAN - 1
IP MAN - 2
BRUCE LEE
JAMES BOND 1
JAMES BOND 2
HARRY POTTER
DER HERR der RINGE
HOBBIT
DIE CHRONIKEN VON NARNIA
HALLOWEEN CLASSIC
HALLOWEEN REBOOT
TWILIGHT
HELLRAISER
UNDERWORLD
AMERICAN FIGHTER
A CHINESE GHOST STORY
FIFTY SHADES OF GREY
BEFORE MIDNIGHT
DIE WILDEN KERLE
WRONG TURN
EDGAR WALLACE
EDGAR WALLACE MIX
ROCKY
RAMBO
THE HUNGER GAMES
JURASSIC PARK
ALIEN
PREDATOR
MEN IN BLACK
TERMINATOR
MISSION IMPOSSIBLE
96 HOURS TAKEN
3 NINJA KIDS
THE FIGHTERS
MATRIX
JOHN WICK
THE DIVERGENT
THE TRANSPORTER
BOURNE
THE EQUALIZER
BATMAN
SUPERMAN
ASTERIX AND OBELIX
BACK TO THE FUTURE
FRIDAY
BAD BOYS
BIG MAMA'S HAUS
RUSH HOUR
OCEAN'S
DEATH RACE
xXx TRIPLE AGENT
FAST & FURIOUS
BLADE
FINAL DESTINATION
RESIDENT EVIL
SAW
JAWS
GOAL
INDIANA JONES
LETHAL WEAPON
DIE HARD
THE MUMMY
MAD MAX
NACHTS IM MUSEUM
HANGOVER
FACK JU GOHTE
HAROLD AND KUMAR
SCREAM
SCARY MOVIE
AMERICAN PIE
DER KAUFHAUS COP
POLICE ACADEMY
THE GODFATHER
PSYCHO
"""

for name in [
    line.strip()
    for line in CUSTOM_NAMES.splitlines()
    if line.strip()
]:
    add(
        [],
        name,
        fallback=True,
        fallback_title=name,
    )


# ---------------------------------------------------------------------
# VERA / REDBOX / MAX / KINOPORTAL
# ---------------------------------------------------------------------

for n in range(1, 14):
    add(
        [],
        f"SELECT FILME {n}",
        fallback=True,
        fallback_title=f"SELECT FILME {n}",
    )

for n in range(1, 11):
    add(
        [],
        f"Select Kino {n}",
        fallback=True,
        fallback_title=f"Select Kino {n}",
    )

VERA_KINO = r"""
Vera Kino Action 1
Vera Kino Action 2
Vera Kino Action 3
Vera Kino Western 1
Vera Kino Western 2
Vera Kino Komödie 1
Vera Kino Komödie 2
Vera Kino Komödie 3
Vera Kino Sci-Fi 1
Vera Kino Marvel
Vera Kino Horror 1
Vera Kino Thriller 1
Vera Kino Drama 1
Vera Kino Drama 2
Vera Kino Bollywood 1
Vera Kino Bollywood 2
Vera Kino Animation 1
"""

for name in [
    line.strip()
    for line in VERA_KINO.splitlines()
    if line.strip()
]:
    add(
        [],
        name,
        fallback=True,
        fallback_title=name,
    )

for n in range(1, 11):
    add(
        [],
        f"Vera Marvel {n}",
        fallback=True,
        fallback_title=f"Vera Marvel {n}",
    )

for n in range(1, 7):
    add(
        [],
        f"KinoPortal {n}",
        fallback=True,
        fallback_title=f"KinoPortal {n}",
    )

for n in range(1, 13):
    add(
        [],
        f"REDBOX Kino {n}",
        fallback=True,
        fallback_title=f"REDBOX Kino {n}",
    )

add([], "MAX Premiere HD", fallback=True, fallback_title="MAX Premiere")
for n in (2, 3):
    add(
        [],
        f"MAX Premiere {n} HD",
        fallback=True,
        fallback_title=f"MAX Premiere {n}",
    )

add([], "MAX KINO COLLECTION", fallback=True, fallback_title="MAX KINO COLLECTION")

for n in range(1, 6):
    add(
        [],
        f"MAX KINO {n}",
        fallback=True,
        fallback_title=f"MAX KINO {n}",
    )

add([], "MAX Plus HD", fallback=True, fallback_title="MAX Plus")

for n in range(1, 5):
    add(
        [],
        f"Max Select {n} 4K",
        fallback=True,
        fallback_title=f"Max Select {n}",
    )

for n in range(1, 8):
    add(
        [],
        f"MAX SELECT HD {n}",
        fallback=True,
        fallback_title=f"MAX SELECT HD {n}",
    )


# ---------------------------------------------------------------------
# EPG LADEN / INDEX
# ---------------------------------------------------------------------

root = merge_sources(SOURCE_URLS)

channels = root.findall("channel")
programmes = root.findall("programme")

channels_by_id = {}
normalized_to_ids = defaultdict(list)
programmes_by_channel = defaultdict(list)

for channel in channels:
    cid = channel.get("id")
    if not cid:
        continue

    channels_by_id[cid] = channel

    for name in channel_names(channel):
        key = normalize(name)
        if key:
            normalized_to_ids[key].append(cid)

    key = normalize(cid)
    if key:
        normalized_to_ids[key].append(cid)

for programme in programmes:
    cid = programme.get("channel")
    if cid:
        programmes_by_channel[cid].append(programme)


def score(query, cid):
    q = normalize(query)
    if not q:
        return -1

    names = channel_names(channels_by_id[cid]) + [cid]
    best = -1

    for name in names:
        c = normalize(name)

        if not c:
            continue

        if q == c:
            return 1000

        if q in c or c in q:
            best = max(best, 850 - abs(len(q) - len(c)))

        q_words = set(q.split())
        c_words = set(c.split())
        if q_words and c_words:
            common = len(q_words & c_words)
            union = len(q_words | c_words)
            if union:
                best = max(best, int((common / union) * 700))

    return best


def resolve(source_candidates):
    # 1. Exakter normalisierter Treffer
    for candidate in source_candidates:
        key = normalize(candidate)
        ids = normalized_to_ids.get(key, [])
        if ids:
            ids = sorted(
                set(ids),
                key=lambda cid: len(programmes_by_channel.get(cid, [])),
                reverse=True,
            )
            return ids[0]

    # 2. Sehr vorsichtige Ähnlichkeitssuche.
    # Hoher Schwellenwert, damit z.B. DYN nicht fälschlich Sky Sport bekommt.
    best_id = None
    best_score = -1

    for candidate in source_candidates:
        for cid in channels_by_id:
            current = score(candidate, cid)
            if current > best_score:
                best_score = current
                best_id = cid

    if best_score >= 720:
        return best_id

    return None


# ---------------------------------------------------------------------
# ALIAS-SENDER / PROGRAMME ERZEUGEN
# ---------------------------------------------------------------------

existing_ids = {
    channel.get("id")
    for channel in channels
    if channel.get("id")
}

created_ids = set()
new_channels = []
new_programmes = []

matched_real = 0
synthetic = 0
unmatched = []


def make_channel(name, cid):
    channel = ET.Element("channel", {"id": cid})
    display = ET.SubElement(channel, "display-name")
    display.text = name
    return channel


def xmltv_time(dt):
    return dt.strftime("%Y%m%d%H%M%S +0000")


def add_synthetic_programmes(cid, title):
    # 10 Tagesblöcke: gestern bis acht Tage in die Zukunft.
    now = datetime.now(timezone.utc)
    start_day = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)

    result = []

    for offset in range(10):
        start = start_day + timedelta(days=offset)
        stop = start + timedelta(days=1)

        programme = ET.Element(
            "programme",
            {
                "start": xmltv_time(start),
                "stop": xmltv_time(stop),
                "channel": cid,
            },
        )

        title_node = ET.SubElement(programme, "title", {"lang": "de"})
        title_node.text = title

        desc = ET.SubElement(programme, "desc", {"lang": "de"})
        desc.text = (
            "Platzhalter-EPG: Für diesen providerseitigen 24/7-/Eventkanal "
            "ist keine verlässliche externe Detail-EPG-Quelle verfügbar."
        )

        result.append(programme)

    return result


for request in ALIAS_REQUESTS:
    source_candidates = request["sources"]
    aliases = request["aliases"]
    fallback = request["fallback"]
    fallback_title = request["fallback_title"]

    source_id = resolve(source_candidates) if source_candidates else None

    source_channel = channels_by_id.get(source_id) if source_id else None
    source_programmes = programmes_by_channel.get(source_id, []) if source_id else []

    real_data_available = source_channel is not None and len(source_programmes) > 0

    for name in aliases:
        new_id = alias_id(name)
        original_id = new_id
        counter = 2

        while new_id in existing_ids or new_id in created_ids:
            new_id = f"{original_id}.{counter}"
            counter += 1

        if real_data_available:
            cloned_channel = copy.deepcopy(source_channel)
            cloned_channel.set("id", new_id)

            for node in list(cloned_channel.findall("display-name")):
                cloned_channel.remove(node)

            display = ET.Element("display-name")
            display.text = name
            cloned_channel.insert(0, display)

            new_channels.append(cloned_channel)

            for programme in source_programmes:
                cloned_programme = copy.deepcopy(programme)
                cloned_programme.set("channel", new_id)
                new_programmes.append(cloned_programme)

            matched_real += 1

        elif fallback:
            new_channels.append(make_channel(name, new_id))
            title = fallback_title or name
            new_programmes.extend(
                add_synthetic_programmes(new_id, title)
            )
            synthetic += 1

        else:
            unmatched.append(name)
            continue

        created_ids.add(new_id)


# Neue Channels vor dem ersten Programmeintrag einfügen.
first_programme = len(root)

for i, child in enumerate(list(root)):
    if child.tag == "programme":
        first_programme = i
        break

for offset, channel in enumerate(new_channels):
    root.insert(first_programme + offset, channel)

for programme in new_programmes:
    root.append(programme)


# ---------------------------------------------------------------------
# AUSGABE
# ---------------------------------------------------------------------

xml_output = ET.tostring(
    root,
    encoding="utf-8",
    xml_declaration=True,
)

with gzip.open(
    OUTPUT_FILE,
    "wb",
    compresslevel=9,
) as gz:
    gz.write(xml_output)

print()
print("FERTIG")
print(f"Original-Sender:     {len(channels)}")
print(f"Original-Programme:  {len(programmes)}")
print(f"Neue Alias-Sender:   {len(new_channels)}")
print(f"Neue Programme:      {len(new_programmes)}")
print(f"Echte Zuordnungen:   {matched_real}")
print(f"Platzhalter-Sender:  {synthetic}")
print(f"Nicht zugeordnet:    {len(unmatched)}")
print(f"Ausgabe:              {OUTPUT_FILE}")

if unmatched:
    print()
    print("Nicht zugeordnet:")
    for name in sorted(set(unmatched), key=str.lower):
        print(f"  - {name}")
