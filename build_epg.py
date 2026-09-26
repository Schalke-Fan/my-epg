import copy
import gzip
import html
import re
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from io import BytesIO

SOURCE_URL = (
    "https://epgshare01.online/epgshare01/"
    "epg_ripper_DE1.xml.gz"
)
OUTPUT_FILE = "epg.xml.gz"

QUALITY_WORDS = {
    "hd", "fhd", "sd", "uhd", "4k", "mobile",
    "feed", "vip", "raw", "backup", "event", "only"
}


def clean_text(value):
    if not value:
        return ""
    old = value
    for _ in range(2):
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


ALIAS_REQUESTS = []


def add(source_candidates, *aliases):
    if isinstance(source_candidates, str):
        source_candidates = [source_candidates]
    ALIAS_REQUESTS.append(
        (list(source_candidates), list(aliases))
    )


# ------------------------------------------------------------
# SKY BUNDESLIGA
# ------------------------------------------------------------

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
            f"Sky Sport Bundesliga {n}",
            f"Sky Bundesliga {n}",
            f"Bundesliga {n}",
        ],
        *aliases,
    )


# ------------------------------------------------------------
# DAZN
# ------------------------------------------------------------

for n in (1, 2):
    add(
        [f"DAZN {n}", f"DAZN{n}"],
        f"DAZN {n} Vip",
        f"DAZN {n} FHD",
        f"DAZN {n} HD",
        f"DAZN {n} SD",
    )


# ------------------------------------------------------------
# SKY CINEMA / ENTERTAINMENT
# ------------------------------------------------------------

add(
    "Sky Cinema Action",
    "Sky Cinema Action HD",
    "Sky Cinema Action FHD",
)
add(
    ["Sky Cinema Feelgood", "Sky Cinema Feel Good"],
    "Sky Cinema Feelgood HD",
    "Sky Cinema Feelgood FHD",
)
add(
    "Sky Cinema Premiere",
    "Sky Cinema Premiere HD",
    "Sky Cinema Premiere FHD",
)
add(
    "Sky Cinema Blockbuster",
    "Sky Cinema Blockbuster HD",
    "Sky Cinema Blockbuster FHD",
)
add(
    "Sky One",
    "Sky ONE HD",
    "Sky One FHD",
)
add(
    "Sky Atlantic",
    "Sky Atlantic HD",
    "Sky Atlantic FHD",
)


# ------------------------------------------------------------
# SPORT
# ------------------------------------------------------------

SPORT_MAP = [
    (
        ["Eurosport 1", "EuroSport 1"],
        ["Eurosport 1 FHD", "Eurosport 1 HD"],
    ),
    (
        ["Eurosport 2", "EuroSport 2"],
        [
            "Eurosport 2 FHD",
            "Eurosport 2 HD",
            "EuroSport 2 Xtra HD",
        ],
    ),
    (
        ["Sport1", "Sport 1"],
        ["Sport1 Vip", "Sport1 FHD", "Sport1 HD"],
    ),
    (
        [
            "sportdigital FUSSBALL",
            "Sportdigital",
            "Sport Digital",
        ],
        ["Sport Digital FHD", "Sport Digital HD"],
    ),
    (
        ["Auto Motor und Sport", "auto motor und sport"],
        ["Auto Motor und Sport"],
    ),
    (
        ["Motorvision TV", "Motorvision"],
        ["Motorvision TV FHD", "Motorvision TV HD"],
    ),
    (
        "Red Bull TV",
        ["Red Bull TV", "RED BULL TV FHD"],
    ),
    (
        "More Than Sports TV",
        ["More Than Sports TV FHD", "More Than Sports TV HD"],
    ),
    (
        ["eSports1", "eSports 1"],
        ["eSports 1 FHD", "eSports 1 HD"],
    ),
    (
        ["BR24Sport", "BR24 Sport"],
        ["BR24Sport"],
    ),
    (
        ["FC Bayern TV", "FC Bayern.tv"],
        ["FC Bayern TV"],
    ),
    (
        "DFB Play",
        ["DFB Play"],
    ),
    (
        ["ServusTV", "Servus TV"],
        [
            "SERVUS TV MOTORSPORT FHD",
            "SERVUS TV MOTORSPORT HD",
        ],
    ),
    (
        ["MS Sport", "MagentaSport", "Magenta Sport"],
        ["MS SPORT"],
    ),
]

for sources, aliases in SPORT_MAP:
    add(sources, *aliases)


# ------------------------------------------------------------
# REGULÄRE FILM-/SERIENSENDER
# ------------------------------------------------------------

REGULAR_MAP = [
    (["TELE 5", "Tele 5"], ["TELE 5"]),
    ("Silverline", ["Silverline"]),
    ("AXN Black", ["AXN Black"]),
    ("AXN White", ["AXN White"]),
    (["Universal TV", "Universal"], ["Universal FHD"]),
    (["Kinowelt TV", "Kinowelt"], ["Kinowelt Tv"]),
]

for sources, aliases in REGULAR_MAP:
    add(sources, *aliases)


# ------------------------------------------------------------
# AMAZON PRIME
# ------------------------------------------------------------

add(
    ["Prime Video", "Amazon Prime Video", "Amazon Prime"],
    "AMAZON PRIME RAW",
    "AMAZON PRIME FHD",
    "AMAZON PRIME HD",
    "AMAZON PRIME SD",
    "AMAZON PRIME BACKUP",
)


# ------------------------------------------------------------
# DYN SPORTS 1-25
# ------------------------------------------------------------

for n in range(1, 26):
    add(
        [
            f"DYN Sport {n}",
            f"DYN Sports {n}",
            "DYN Sport",
            "DYN Sports",
        ],
        f"DYN SPORT {n}",
    )


# ------------------------------------------------------------
# MAGENTA / MYTEAM
# ------------------------------------------------------------

for n in (1, 2):
    add(
        [
            f"Magenta Golf {n}",
            f"MagentaSport Golf {n}",
            "MagentaSport",
        ],
        f"MS GOLF {n} FHD",
        f"MS GOLF {n} HD",
    )

for n in range(1, 19):
    add(
        [
            f"MyTeam TV {n}",
            f"MyTeamTV {n}",
            "MagentaSport",
            "Magenta Sport",
        ],
        f"MyTeam TV - {n}",
    )


# ------------------------------------------------------------
# DEL2 EVENT 01-20
# ------------------------------------------------------------

for n in range(1, 21):
    add(
        [
            f"DEL2 {n}",
            f"DEL2 Event {n}",
            "DEL2",
        ],
        f"DEL2 EVENT {n:02d}",
    )


# ------------------------------------------------------------
# SKY SELECT PREMIERE
# ------------------------------------------------------------

add(
    ["Sky Select", "Sky Select Premiere"],
    "Sky Select Premiere Vitrine HD",
)

for n in range(1, 19):
    add(
        [
            f"Sky Select {n}",
            f"Sky Select Premiere {n}",
            "Sky Select",
        ],
        f"Sky Select Premiere {n} FHD",
    )


# ------------------------------------------------------------
# PROVIDER-EIGENE 24/7-SERIEN UND FILMREIHEN
#
# Diese Einträge werden nur dann verbunden, wenn die EPG-Quelle
# tatsächlich einen gleichnamigen Sender enthält.
# ------------------------------------------------------------

CUSTOM_NAMES = """
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
    add(name, name)


# ------------------------------------------------------------
# VERA / REDBOX / MAX / KINOPORTAL
# ------------------------------------------------------------

for n in range(1, 14):
    add(
        [f"Select Filme {n}", f"Select Kino {n}"],
        f"SELECT FILME {n}",
    )

for n in range(1, 11):
    add(f"Select Kino {n}", f"Select Kino {n}")

VERA_KINO = """
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
    add(name, name)

for n in range(1, 11):
    add(
        [f"Vera Marvel {n}", "Vera Kino Marvel"],
        f"Vera Marvel {n}",
    )

for n in range(1, 7):
    add(
        [f"KinoPortal {n}", f"Kino Portal {n}"],
        f"KinoPortal {n}",
    )

for n in range(1, 13):
    add(f"Redbox Kino {n}", f"REDBOX Kino {n}")

add("MAX Premiere", "MAX Premiere HD")
for n in (2, 3):
    add(f"MAX Premiere {n}", f"MAX Premiere {n} HD")

add("MAX Kino Collection", "MAX KINO COLLECTION")
for n in range(1, 6):
    add(f"MAX Kino {n}", f"MAX KINO {n}")

add("MAX Plus", "MAX Plus HD")

for n in range(1, 5):
    add(f"MAX Select {n}", f"Max Select {n} 4K")

for n in range(1, 8):
    add(f"MAX Select {n}", f"MAX SELECT HD {n}")


# ------------------------------------------------------------
# EPG LADEN
# ------------------------------------------------------------

print("EPG wird geladen:")
print(SOURCE_URL)

request = urllib.request.Request(
    SOURCE_URL,
    headers={
        "User-Agent":
        "Mozilla/5.0 (GitHub Actions EPG Builder)"
    },
)

with urllib.request.urlopen(
    request,
    timeout=90,
) as response:
    compressed = response.read()

print(f"Download: {len(compressed):,} Bytes")

with gzip.GzipFile(
    fileobj=BytesIO(compressed)
) as gz:
    xml_data = gz.read()

print(f"Entpackt: {len(xml_data):,} Bytes")

root = ET.fromstring(xml_data)
fix_entities(root)


# ------------------------------------------------------------
# INDEX AUFBAUEN
# ------------------------------------------------------------

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

    names = channel_names(
        channels_by_id[cid]
    ) + [cid]

    best = -1

    for name in names:
        c = normalize(name)

        if q == c:
            return 1000

        if q and c and (
            q in c or c in q
        ):
            best = max(
                best,
                800 - abs(len(q) - len(c)),
            )

        q_words = set(q.split())
        c_words = set(c.split())

        if q_words and c_words:
            common = len(q_words & c_words)
            union = len(q_words | c_words)
            best = max(
                best,
                int((common / union) * 700),
            )

    return best


def resolve(source_candidates):
    # 1. Exakter normalisierter Treffer.
    for candidate in source_candidates:
        key = normalize(candidate)
        ids = normalized_to_ids.get(key, [])

        if ids:
            ids = sorted(
                set(ids),
                key=lambda cid:
                len(
                    programmes_by_channel.get(
                        cid,
                        [],
                    )
                ),
                reverse=True,
            )
            return ids[0]

    # 2. Vorsichtige Ähnlichkeitssuche.
    best_id = None
    best_score = -1

    for candidate in source_candidates:
        for cid in channels_by_id:
            current = score(candidate, cid)
            if current > best_score:
                best_score = current
                best_id = cid

    if best_score >= 560:
        return best_id

    return None


# ------------------------------------------------------------
# ALIAS-SENDER UND PROGRAMME ERZEUGEN
# ------------------------------------------------------------

existing_ids = {
    channel.get("id")
    for channel in channels
}

created_ids = set()
new_channels = []
new_programmes = []
unmatched = []
matched = 0

for source_candidates, aliases in ALIAS_REQUESTS:
    source_id = resolve(source_candidates)

    if not source_id:
        unmatched.extend(aliases)
        continue

    source_channel = channels_by_id[source_id]
    source_programmes = (
        programmes_by_channel.get(
            source_id,
            [],
        )
    )

    for name in aliases:
        new_id = alias_id(name)
        original_id = new_id
        counter = 2

        while (
            new_id in existing_ids
            or new_id in created_ids
        ):
            new_id = (
                f"{original_id}.{counter}"
            )
            counter += 1

        cloned_channel = copy.deepcopy(
            source_channel
        )
        cloned_channel.set("id", new_id)

        for node in list(
            cloned_channel.findall(
                "display-name"
            )
        ):
            cloned_channel.remove(node)

        display = ET.Element(
            "display-name"
        )
        display.text = name
        cloned_channel.insert(0, display)

        new_channels.append(
            cloned_channel
        )
        created_ids.add(new_id)

        for programme in source_programmes:
            cloned_programme = copy.deepcopy(
                programme
            )
            cloned_programme.set(
                "channel",
                new_id,
            )
            new_programmes.append(
                cloned_programme
            )

        matched += 1


# Neue Channels vor dem ersten Programmeintrag einfügen.
first_programme = len(root)

for i, child in enumerate(list(root)):
    if child.tag == "programme":
        first_programme = i
        break

for offset, channel in enumerate(
    new_channels
):
    root.insert(
        first_programme + offset,
        channel,
    )

for programme in new_programmes:
    root.append(programme)


# ------------------------------------------------------------
# AUSGABE
# ------------------------------------------------------------

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
print(
    f"Original-Sender: "
    f"{len(channels)}"
)
print(
    f"Original-Programme: "
    f"{len(programmes)}"
)
print(
    f"Neue Alias-Sender: "
    f"{len(new_channels)}"
)
print(
    f"Neue Programme: "
    f"{len(new_programmes)}"
)
print(
    f"Alias-Zuordnungen: "
    f"{matched}"
)
print(
    f"Nicht zugeordnet: "
    f"{len(unmatched)}"
)
print(
    f"Ausgabe: {OUTPUT_FILE}"
)

if unmatched:
    print()
    print(
        "Nicht in der EPG-Quelle "
        "gefunden:"
    )
    for name in sorted(
        set(unmatched),
        key=str.lower,
    ):
        print(f"  - {name}")
