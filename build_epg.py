import copy
import gzip
import hashlib
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from io import BytesIO

SOURCE_URL = (
    "https://epgshare01.online/epgshare01/"
    "epg_ripper_DE1.xml.gz"
)

OUTPUT_FILE = "epg.xml.gz"

aliases = defaultdict(set)


def add(source_id, names, qualities=()):
    """Create exact channel-name aliases used by the IPTV provider."""
    for name in names:
        for prefix in ("", "DE: "):
            aliases[source_id].add(prefix + name)

            for quality in qualities:
                aliases[source_id].add(
                    f"{prefix}{name} {quality}"
                )


# ---------------------------------------------------------
# SKY SPORT 1-10
# ---------------------------------------------------------

for n in range(1, 11):
    add(
        f"Sky.Sport.{n}.de",
        [
            f"Sky Sport {n}",
            f"SKY SPORT {n}",
        ],
        ["HD", "FHD", "SD", "UHD", "HEVC"],
    )


# ---------------------------------------------------------
# SKY BUNDESLIGA 1-10
# Provider abbreviates "Bundesliga" as "Bndliga"
# ---------------------------------------------------------

for n in range(1, 11):
    add(
        f"Sky.Sport.Bundesliga.{n}.de",
        [
            f"Bndliga {n}",
            f"Bundesliga {n}",
            f"Sky Bundesliga {n}",
            f"Sky Sport Bundesliga {n}",
        ],
        [
            "HD",
            "FHD",
            "SD",
            "Mobile",
            "UHD",
            "FEED",
            "4K",
        ],
    )


# General Bundesliga / UHD channels
add(
    "Sky.Sport.Bundesliga.de",
    [
        "Bundesliga",
        "Bndliga",
        "Sky Bundesliga",
        "Sky Sport Bundesliga",
    ],
    ["HD", "FHD", "SD", "UHD"],
)

add(
    "Sky.Sport.Bundesliga.UHD.de",
    [
        "Bndliga UHD",
        "Bundesliga UHD",
        "Sky Bundesliga UHD",
        "Sky Sport Bundesliga UHD",
    ],
)


# ---------------------------------------------------------
# DAZN
# ---------------------------------------------------------

for n in (1, 2):
    add(
        f"DAZN.{n}.de",
        [
            f"DAZN {n}",
            f"DAZN SPORT {n}",
            f"DAZN Sport {n}",
        ],
        ["HD", "FHD", "SD", "UHD", "HEVC"],
    )

add(
    "DAZN.de",
    ["DAZN"],
    ["HD", "FHD", "UHD", "HEVC"],
)


# ---------------------------------------------------------
# SKY CINEMA / ENTERTAINMENT
# ---------------------------------------------------------

sky_channels = {
    "Sky.Cinema.Action.HD.de": [
        "Sky Cinema Action"
    ],
    "Sky.Cinema.Premiere.HD.de": [
        "Sky Cinema Premiere"
    ],
    "Sky.Cinema.Classics.HD.de": [
        "Sky Cinema Classics"
    ],
    "Sky.Cinema.Family.HD.de": [
        "Sky Cinema Family"
    ],
    "Sky.Cinema.Highlights.HD.de": [
        "Sky Cinema Highlights"
    ],
    "Sky.Atlantic.HD.de": [
        "Sky Atlantic"
    ],
    "Sky.One.de": [
        "Sky One",
        "Sky ONE"
    ],
    "Sky.Crime.de": [
        "Sky Crime"
    ],
    "Sky.Documentaries.de": [
        "Sky Documentaries"
    ],
    "Sky.Nature.de": [
        "Sky Nature"
    ],
    "Sky.Krimi.de": [
        "Sky Krimi"
    ],
}

for source_id, names in sky_channels.items():
    add(
        source_id,
        names,
        ["HD", "FHD", "SD", "UHD", "HEVC"],
    )


# ---------------------------------------------------------
# SPECIAL SKY SPORT CHANNELS
# ---------------------------------------------------------

special_sport = {
    "Sky.Sport.F1.de": ["Sky Sport F1"],
    "Sky.Sport.Golf.de": ["Sky Sport Golf"],
    "Sky.Sport.Mix.de": ["Sky Sport Mix"],
    "Sky.Sport.News.de": ["Sky Sport News"],
    "Sky.Sport.Premier.League.de": [
        "Sky Sport Premier League"
    ],
    "Sky.Sport.Tennis.de": ["Sky Sport Tennis"],
    "Sky.Sport.Top.Event.de": [
        "Sky Sport Top Event"
    ],
    "Sky.Sport.UHD.de": ["Sky Sport UHD"],
}

for source_id, names in special_sport.items():
    add(
        source_id,
        names,
        ["HD", "FHD", "UHD", "HEVC"],
    )


# ---------------------------------------------------------
# IMPORTANT GERMAN FREE-TV CHANNELS
# Especially provider variants ending in HEVC/FHD
# ---------------------------------------------------------

german_channels = {
    "Das.Erste.de": [
        "Das Erste",
        "DAS ERSTE"
    ],
    "ZDF.de": ["ZDF"],
    "RTL.de": ["RTL"],
    "ProSieben.de": [
        "ProSieben",
        "PROSIEBEN"
    ],
    "RTLZWEI.de": [
        "RTL ZWEI",
        "RTLZWEI",
        "RTL 2"
    ],
    "SAT.1.de": [
        "SAT.1",
        "SAT 1"
    ],
    "VOX.de": ["VOX"],
    "kabel.eins.de": [
        "Kabel Eins",
        "KABEL EINS"
    ],
    "ProSieben.MAXX.de": [
        "Pro7 MAXX",
        "ProSieben MAXX"
    ],
    "sixx.de": [
        "SIXX",
        "sixx"
    ],
    "SAT.1.Gold.de": [
        "SAT 1 GOLD",
        "SAT.1 GOLD",
        "SAT.1 Gold"
    ],
    "Tele.5.de": [
        "TELE 5",
        "Tele 5"
    ],
    "NITRO.de": ["NITRO"],
    "SUPER.RTL.de": [
        "SUPER RTL"
    ],
    "WELT.de": ["WELT"],
    "ntv.de": [
        "N-TV",
        "NTV",
        "n-tv"
    ],
    "ZDFneo.de": [
        "ZDFneo",
        "ZDF NEO"
    ],
    "ZDFinfo.de": [
        "ZDFinfo",
        "ZDF INFO"
    ],
}

for source_id, names in german_channels.items():
    add(
        source_id,
        names,
        ["HD", "FHD", "SD", "HEVC", "UHD"],
    )


# ---------------------------------------------------------
# DOWNLOAD XMLTV
# ---------------------------------------------------------

request = urllib.request.Request(
    SOURCE_URL,
    headers={"User-Agent": "Mozilla/5.0"},
)

with urllib.request.urlopen(request, timeout=60) as response:
    compressed = response.read()

xml_data = gzip.decompress(compressed)

root = ET.fromstring(xml_data)


# ---------------------------------------------------------
# LOCATE CHANNELS
# ---------------------------------------------------------

channel_elements = {}

for element in root.findall("channel"):
    channel_id = element.get("id")
    if channel_id:
        channel_elements[channel_id] = element


# ---------------------------------------------------------
# CREATE ALIAS CHANNELS
# ---------------------------------------------------------

source_to_alias_ids = defaultdict(list)

used_names = set()

new_channels = []

for source_id, names in aliases.items():

    if source_id not in channel_elements:
        print(f"Source channel not found: {source_id}")
        continue

    for name in sorted(names):

        key = name.casefold()

        if key in used_names:
            continue

        used_names.add(key)

        digest = hashlib.sha1(
            f"{source_id}|{name}".encode("utf-8")
        ).hexdigest()[:16]

        alias_id = f"alias.{digest}"

        channel = ET.Element(
            "channel",
            {"id": alias_id}
        )

        display = ET.SubElement(
            channel,
            "display-name"
        )

        display.text = name

        new_channels.append(channel)

        source_to_alias_ids[source_id].append(
            alias_id
        )


# XMLTV convention:
# channels should appear before programme entries.

children = list(root)

first_programme_index = next(
    (
        i
        for i, item in enumerate(children)
        if item.tag == "programme"
    ),
    len(children),
)

for offset, channel in enumerate(new_channels):
    root.insert(
        first_programme_index + offset,
        channel
    )


# ---------------------------------------------------------
# DUPLICATE PROGRAMMES FOR ALIAS CHANNELS
# ---------------------------------------------------------

original_programmes = list(
    root.findall("programme")
)

created_programmes = 0

for programme in original_programmes:

    source_id = programme.get("channel")

    alias_ids = source_to_alias_ids.get(
        source_id,
        []
    )

    for alias_id in alias_ids:

        duplicate = copy.deepcopy(programme)

        duplicate.set(
            "channel",
            alias_id
        )

        root.append(duplicate)

        created_programmes += 1


# ---------------------------------------------------------
# WRITE COMPRESSED XMLTV FILE
# ---------------------------------------------------------

result = ET.tostring(
    root,
    encoding="utf-8",
    xml_declaration=True,
)

with gzip.open(
    OUTPUT_FILE,
    "wb",
    compresslevel=9,
) as output:
    output.write(result)


print(
    f"Created {len(new_channels)} alias channels "
    f"and {created_programmes} alias programmes."
)

print(f"Saved: {OUTPUT_FILE}")
