"""The music library (Jordan, 11-15: "bring in all of the sounds from all of the fan game and rom
sources into an our game folder ... organized alphabetically and by generation").

Builds assets/music/library/ on this PC from the sources in Downloads:
    gen<N>/<source>/<track>.ogg|.mid     songs (bgm), fanfares (me) and background loops (bgs)
    sounds/<source>/<path>.ogg|.wav|.mp3 every sound effect (cries, moves, menus)
    manifest.json                        track -> name, generation, source, original file (kept in git)
The audio itself is too big for git (about a gigabyte), so it stays out of it; run this again on a
new PC. src/core/music_library.py reads the manifest and offers the tracks that are there, by
generation then name (the Options jukebox).

Sources
  fan games (RPG Maker XP / Pokemon Essentials Audio folders): Pokemon Journeys V18, Pokemon Orre
    2.1.1, Pokemon Everlasting X Devastating Y beta 1.5, Banished Platinum (Hisui update), Pokemon
    Essentials v21.1 and its Generation 9 Pack (sound effects only).
  game files (3DS, decrypted): Omega Ruby, Ultra Sun, Ultra Moon, Pokemon Mystery Dungeon: Gates to
    Infinity - their .bcstm music streams, rendered with vgmstream-cli.
  Not rendered (see NOT_RENDERED below): the DS and GBA games' sequenced music, Super Mystery Dungeon
    (encrypted), and the Game Boy / GBA fan hacks.

Generation = the generation of the game the recording is from (FRLG remakes are Gen 3, HGSS Gen 4);
an untagged track takes its fan game's home generation; tunes that aren't from a Pokemon game are
"Other" (gen 0). Identical files (same bytes) are kept once; the manifest lists where else they were.
Long files are re-encoded to Ogg Vorbis (quality 3) and cut at 10 minutes (the hour-long rips).

Run from the game folder (tools: ffmpeg and vgmstream-cli, kept in kanto_handoff/music_tools):
    python -I dev/builders/build_music_library.py [--downloads DIR] [--journeys DIR]
        [--ffmpeg EXE] [--vgmstream EXE] [--work DIR] [--only SOURCE,...] [--no-sounds]
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(GAME, "assets", "music", "library")
def _pokemon_games():
    """pokemon-games: the first folder up from the game that holds kanto_handoff (works from a worktree too)."""
    d = GAME
    while os.path.dirname(d) != d:
        d = os.path.dirname(d)
        if os.path.isdir(os.path.join(d, "kanto_handoff")):
            return d
    return os.path.normpath(os.path.join(GAME, "..", ".."))


PG = _pokemon_games()
TOOLS = os.path.join(PG, "kanto_handoff", "music_tools")
DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")
MAX_SECONDS = 600
SHORTEST_SONG = 20       # seconds: anything shorter is a fanfare (kind "me"), not a song
QUALITY = "3"            # Ogg Vorbis quality (about 110 kbps)
KEEP_KBPS = 170          # an .ogg at or under this (and under MAX_SECONDS) is copied as it is
MUSIC_EXT = (".ogg", ".mp3", ".wav", ".mid", ".midi")

# key: (title, credit, where (Downloads-relative unless absolute), home generation)
FAN = {
    "journeys": ("Pokemon Journeys V18", "Pokemon Journeys V18 fan game (Pokemon Essentials v18)",
                 os.path.join(PG, "Pokemon Journeys V18", "Audio"), 4),   # (REG0_ tracks: Kanto, Gen 1)
    "orre": ("Pokemon Orre 2.1.1", "Pokemon Orre 2.1.1 fan game",
             r"orre\Pokemon_Orre_2.1.1\Pokemon_Orre_2.1.1_reupload\Audio", 3),
    "everlasting_xy": ("Pokemon Everlasting X Devastating Y", "Pokemon Everlasting X Devastating Y beta 1.5 fan game",
                       r"kalos\(Beta v1.5) Pokemon Everlasting X Devastating Y\(Beta v1.5) Pokemon Everlasting X Devastating Y\Audio", 6),
    "banished_platinum": ("Banished Platinum", "Banished Platinum (Hisui Update) fan game",
                          r"sinnoh\Banished Platinum Hisui Update\Banished Platinum\Audio", 4),
    "essentials": ("Pokemon Essentials v21.1", "Pokemon Essentials v21.1 (Maruno and the Essentials team)",
                   r"Pokemon Essentials v21.1 2023-07-30\Pokemon Essentials v21.1 2023-07-30\Audio", 4),
    "gen9pack": ("Generation 9 Pack", "Generation 9 Pack v3.3.8 for Pokemon Essentials",
                 r"Pokemon Essentials v21.1 2023-07-30\Generation 9 Pack v3.3.8\Audio", 9),
}
# key: (title, credit, .3ds file, generation, stream-name filter)
ROMS = {
    "omega_ruby": ("Omega Ruby", "Pokemon Omega Ruby (Game Freak, 2014) - Jordan's game file",
                   r"hoenn\Pokemon Omega Ruby (USA) (En,Ja,Fr,De,Es,It,Ko) (Rev 2).3ds", 6, r"(bgm|me)_"),
    "ultra_moon": ("Ultra Moon", "Pokemon Ultra Moon (Game Freak, 2017) - Jordan's game file",
                   r"alola\Pokemon Ultra Moon (USA) (EnJaFrDeEsItZhKo)\Pokemon Ultra Moon (USA) (En,Ja,Fr,De,Es,It,Zh,Ko).3ds", 7, r"(bgm|me|strm)_"),
    "ultra_sun": ("Ultra Sun", "Pokemon Ultra Sun (Game Freak, 2017) - Jordan's game file",
                  r"alola\Pokemon Ultra Sun (USA) (EnJaFrDeEsItZhKo)\Pokemon Ultra Sun (USA) (En,Ja,Fr,De,Es,It,Zh,Ko).3ds", 7, r"(bgm|me|strm)_"),
    "pmd_gti": ("PMD: Gates to Infinity", "Pokemon Mystery Dungeon: Gates to Infinity (Spike Chunsoft, 2012) - Jordan's game file",
                r"PMD Sky\Pokemon Mystery Dungeon - Gates to Infinity (USA).3ds", 5, r"(BGM|ME)_(?!.*TEST)"),
}
NOT_RENDERED = {
    "FireRed, Emerald (GBA)": "m4a/MP2K sequences + instrument banks: needs a sequencer and synth "
        "(agbplay has no Windows build; VGMusicStudio exports WAV one song at a time by hand).",
    "SoulSilver, Platinum, Diamond, Pearl, Black 2, White, White 2, PMD Blue Rescue Team (DS)":
        "SDAT SSEQ sequences + SBNK/SWAR banks: needs an SSEQ player (VGMusicStudio by hand, or "
        "NDS to NCSF + an NCSF player). No batch renderer runs here.",
    "Super Mystery Dungeon (.cia)": "encrypted: would need decrypting on a 3DS first.",
    "GBA/GB fan hacks (Sun-Moon FireRed, Sword and Shield Ultimate GBA, Omega Ruby GBA, Mega Emerald X/Y, "
    "Orange Generation, Scarlet+Violet GBA, Black & White Advanced, Island Walker, Scarlet GB Demake, "
    "Black 2 251 Edition)": "same engines as the GBA/DS games above (plus Game Boy sound for the .gb/.gbc).",
    "Zeak Map Pack, Eevee Expo tilesets, Tileset Collection": "art only, no audio.",
}

# A tagged fan-game file ("RSE 245 Battle! (Elite Four).ogg"): its game's generation.
TAGS = {"FRLG": 3, "RSE": 3, "XD": 3, "HGSS": 4, "DPPT": 4, "BR": 4, "SM": 7, "PB": 1}
# Not from a Pokemon game.
OTHER = {"bomberman", "dkc2cave", "triple triad", "vine boom", "018-field01", "021-field04",
         "021-field04_n", "022-field05"}
GEN_OF = {  # (source, original stem, lowercase) -> generation, where the home one is wrong
    ("everlasting_xy", "battle! eternatus - phase 1"): 8, ("everlasting_xy", "battle! eternatus - phase 2"): 8,
    ("everlasting_xy", "battle! eternatus - phase 3"): 8, ("everlasting_xy", "battle! legendary raid"): 8,
    ("everlasting_xy", "battle! max raid"): 8, ("everlasting_xy", "dynamax adventure"): 8,
    ("everlasting_xy", "max raid intro"): 8, ("everlasting_xy", "battle! ultra necrozma"): 7,
    ("everlasting_xy", "vs_legendary_pokemon_pokemon_bl_(getmp3.pro)"): 5,
    ("journeys", "pkmrs-btower"): 3, ("journeys", "surfing"): 4,
}
NAME_OF = {  # readable names where tidying the file name isn't enough
    "vs_legendary_pokemon_pokemon_bl_(getmp3.pro)": "Battle! Legendary Pokemon (Black and White)",
    "pokmon_x_y_-_route_2_stereo_(getmp3.pro)": "Route 2 (extended)",
    "pokemon_xy_vaniville_town_extended_(getmp3.pro)": "Vaniville Town (extended)",
    "pokemon_xy_aquacorde_town_extended_(getmp3.pro)": "Aquacorde Town (extended)",
    "pokemon xy vaniville town extended": "Vaniville Town (extended, MIDI)",
    "kalos route 4": "Kalos Route 4", "ingido plateau": "Indigo Plateau", "pkmrs-btower": "Battle Tower (RS)",
    "dkc2cave": "Cave (DKC2)", "pmc": "Pokemon Mansion Club", "pmc_n": "Pokemon Mansion Club (Night)",
    "title_dppt": "Title (DPPt)", "bomberman": "Bomberman", "ultrafail": "Ultra Fail",
    "obtainedberry": "Berry Get", "levelup": "Level Up", "colosseumbattle": "Colosseum Battle",
    "evice_battle": "Evice Battle", "snagem_hideout": "Snagem Hideout", "krabbyklubradio": "Krabby Klub Radio",
    "cavesound": "Cave Sound", "outskirtengine": "Outskirt Engine", "outskirtengine2": "Outskirt Engine 2",
    "windloop1": "Wind Loop 1", "windloop2": "Wind Loop 2", "mirror b_s theme": "Mirror B.'s Theme",
    "ruins of alph": "Ruins of Alph",
}
JOURNEYS_NAME = {"HallofFame": "Hall of Fame", "SSAnne": "S.S. Anne", "MtMoon": "Mt. Moon", "OakLab": "Oak's Lab",
                 "MaleTrainAppear": "Trainer Appears (Boy)", "FemaleTrainAppear": "Trainer Appears (Girl)",
                 "EvilTrainAppear": "Team Rocket Appears", "JessieJamesTheme": "Jessie and James",
                 "PokemonCenter": "Pokemon Center", "PokemonGym": "Pokemon Gym", "ProfessorOak": "Professor Oak"}

# 3DS stream names (Game Freak's own romanised words) -> English
WORDS = {"vs": "Battle!", "norapoke": "Wild Pokemon", "trainer": "Trainer", "gymleader": "Gym Leader",
         "champ": "Champion", "shitenno": "Elite Four", "rival": "Rival", "legend": "Legendary Pokemon",
         "eye": "Trainers' Eyes Meet", "win": "Victory", "pokecen": "Pokemon Center", "naminori": "Surfing",
         "shinka": "Evolution", "shinkaome": "Evolution Fanfare", "dendouiri": "Hall of Fame", "kaifuku": "Healed",
         "lvup": "Level Up", "tamago": "Egg", "get": "Get", "kinomi": "Berry Get", "wasure": "Forgot a Move",
         "waza": "TM Get", "hyouka": "Rating", "koukan": "Trade", "labo": "Lab", "ajito": "Team Hideout",
         "karakuri": "Trick House", "sora": "Soaring", "starting": "Opening", "title": "Title", "ending": "Ending",
         "epilogue": "Epilogue", "gym": "Gym", "bicycle": "Bicycle", "diving": "Dive", "safari": "Safari Zone",
         "museum": "Museum", "school": "Trainers' School", "island": "Island", "contest": "Contest",
         "lobby": "Lobby", "result": "Results", "aqua": "Team Aqua", "magma": "Team Magma", "leader": "Leader",
         "higana": "Zinnia", "haruka": "May", "yuuki": "Brendan", "tsureteke": "Come Along", "secret": "Secret",
         "zone": "Zone", "sky": "Sky", "art": "Art", "gallery": "Gallery", "battle": "Battle", "resort": "Resort",
         "house": "House", "bfrontier": "Battle Frontier", "special": "Special", "demo": "Scene", "track": "Track",
         "item": "Item Get", "keyitem": "Key Item Get", "badge": "Badge Get", "bpget": "BP Get", "ball": "Ball",
         "massage": "Massage", "mega": "Mega", "stone": "Stone", "acce": "Accessory", "o": "O-", "power": "Power",
         "dressup": "Dress Up", "mystery": "Mystery Gift", "danlvup": "Rank Up", "secretitem": "Secret Item",
         "ribbon2": "Ribbon", "con": "Contest", "fs": "Friend Safari", "legendroom": "Legend Room",
         "champroad": "Victory Road", "gts": "GTS", "miracle": "Wonder", "random": "Random", "match": "Match",
         "pokemon": "Pokemon", "theme": "Theme", "link": "Link", "game": "Game", "sync": "Sync", "wifi": "Wi-Fi",
         "present": "Present", "silence": "Silence", "sp": "Super", "clear": "Clear", "gameover": "Game Over",
         "gamestart": "Start", "menu": "Menu", "stage": "Stage", "open": "Open", "handsome": "Looker",
         "boutique": "Boutique", "salon": "Salon", "sushi": "Restaurant", "beast": "Ultra Beast",
         "broyal": "Battle Royal", "croyal": "Battle Royal Dome", "ether": "Aether", "friend": "Friend",
         "giver": "Totem Pokemon", "mother": "Lusamine", "motherbeast": "Lusamine (merged)", "redgreen": "Red and Blue",
         "scull": "Team Skull", "scullboss": "Team Skull Boss", "scullelite": "Team Skull Admin", "base": "Base",
         "battletree": "Battle Tree", "canyon": "Canyon", "cave": "Cave", "desert": "Desert", "endcave": "Cave (end)",
         "doctor": "Doctor", "farm": "Farm", "festa": "Festival Plaza", "event": "Event", "eventend": "Event End",
         "harbor": "Harbor", "hole": "Hole", "islandfes": "Island Festival", "istarting": "Opening (island)",
         "lake": "Lake", "league": "Pokemon League", "lilii": "Lillie", "fes": "Festival", "malasada": "Malasada Shop",
         "market": "Market", "megafloat": "Megamart", "niji": "Ultra Space", "pisland": "Poke Pelago",
         "pokeride": "Ride Pokemon", "refre": "Pokemon Refresh", "ruin": "Ruins", "studium": "Stadium",
         "divezone": "Ultra Space Wilds", "sys": "System", "chime": "Chime", "failure": "Failure", "newshop": "New Shop",
         "nc": "(no chime)", "success": "Success", "uranai": "Fortune", "oyasumi": "Good Night", "finish": "Finish",
         "syoukan": "Summon", "zygarde": "Zygarde", "quest": "Quest", "finder": "Poke Finder", "update": "Update",
         "f": "F", "renrakusen": "Ferry", "e": "Event", "ev": "Scene", "c": "City", "t": "Town", "r": "Route",
         "d": "Dungeon", "m": "Map", "s": "Scene", "g": "Area", "n": "(Night)", "st": "(short)",
         "dun": "Dungeon", "eve": "Event", "map": "Map", "paradise": "Paradise", "town": "Town", "boss": "Boss",
         "bossappear": "Boss Appears", "monsterhouse": "Monster House", "shop": "Shop", "steal": "Thief",
         "kyuremu": "Kyurem", "hyoushoku": "Frozen", "intro": "(intro)", "staff": "Staff", "credit": "Credits",
         "theme_": "Theme", "despair": "Despair", "hope": "Hope", "march": "March", "zetsubou": "Despair",
         "return": "Returns", "daihyouga": "Great Glacier", "okusoko": "Depths", "nazo": "Mystery",
         "fear": "Fear", "fuon": "Unease", "ganbare": "Do Your Best", "glide": "Glide", "goodnight": "Good Night",
         "happy": "Happy", "magnagate": "Magnagate", "metamorphosis": "Transformation", "offensiv": "Offensive",
         "reform": "Rebuild", "sazandora": "Hydreigon", "send": "Send", "off": "Off", "skydiving": "Skydiving",
         "tension": "Tension", "titlecatch": "Title Catch", "toride": "Fortress", "calm": "Calm", "comical": "Comical",
         "dogfight": "Dogfight", "end": "End", "benri": "Useful", "opening": "Opening", "minigame": "Minigame",
         "dungeon": "Dungeon", "evolution": "Evolution", "enemy": "Enemy", "evt": "Event", "dan": "Team",
         "meroetta": "Meloetta", "ta": "Ta", "dah": "Dah", "v": "V", "echo": "Echo", "fanfare": "Fanfare",
         "gameclear": "Game Clear", "information": "Information", "important": "Important", "levelup": "Level Up",
         "bad": "Bad", "good": "Good", "perfect": "Perfect", "soso": "So-So", "party": "Party", "rankup": "Rank Up",
         "reward": "Reward", "seeyou": "See You", "wind": "Wind", "limit": "Limit", "hv1": "(heavy 1)",
         "vsdivezone": "Battle! Ultra Space Wilds", "aq": "Team Aqua", "mg": "Team Magma", "l": "Leader",
         "houou": "Ho-Oh", "suikun": "Suicune", "pss": "(PSS)", "hv2": "(heavy 2)", "l1": "(part 1)", "l2": "(part 2)", "l3": "(part 3)", "clear_": "Clear"}
SKIP_WORDS = {"bgm", "me", "strm", "sg", "xy", "nj", "mj", "dspadpcm"}
GAME_TAG = {"sg": "ORAS", "xy": "XY", "nj": "Sun and Moon", "mj": "USUM"}


# ---------------------------------------------------------------------------------- names
def tidy(stem):
    """A fan-game file name -> a readable track name."""
    key = stem.lower()
    if key in NAME_OF:
        return NAME_OF[key]
    s = stem.replace("�", "e").replace("Pokmon", "Pokemon").replace("Pokémon", "Pokemon")
    s = re.sub(r"\s*\(getmp3\.pro\)", "", s).replace("Trainers_ ", "Trainers' ")
    night = s.endswith("_n")
    if night:
        s = s[:-2]
    s = s.replace("_", " ").strip()
    s = re.sub(r"\s+", " ", s)
    if s and s == s.lower():
        s = s.title()
    return s + (" (Night)" if night else "")


def fan_track(source, stem, home, ext=""):
    """(readable name, generation) for a fan-game file."""
    m = re.match(r"^(FRLG|RSE|XD|HGSS|DPPT|BR|SM|PB) \d+ (.+)$", stem)
    if m:
        return tidy(m.group(2)), TAGS[m.group(1)]
    m = re.match(r"^REG0_\d+_(.+)$", stem, re.I)
    if m:
        w = m.group(1)
        name = JOURNEYS_NAME.get(w) or re.sub(r"(?<=[a-z])(?=[A-Z0-9])|(?<=[0-9])(?=[A-Z])", " ", w)
        return name, 1
    key = stem.lower()
    if key in OTHER:
        return tidy(stem), 0
    if source == "everlasting_xy" and ext in (".mid", ".midi") and "vaniville" not in key:
        home = 4   # (its MIDIs are Pokemon Essentials' sample tunes, Gen 4 style)
    m = re.match(r"^\d{3} - (.+)$", stem)       # Orre's own numbered maps ("024 - Waterfall Cave")
    if m:
        stem = m.group(1)
    return tidy(stem), GEN_OF.get((source, key), home)


def stream_name(stem):
    """A 3DS stream name ("bgm_sg_vs_norapoke_sg") -> a readable one ("Battle! Wild Pokemon")."""
    raw = stem.replace(".dspadpcm", "")
    parts = [p for p in re.split(r"_", raw.lower()) if p]
    tag = next((GAME_TAG[p] for p in parts[:3] if p in GAME_TAG), "")
    words, prev = [], ""
    for p in parts:
        if p in SKIP_WORDS:
            continue
        m = re.match(r"^([a-z]+?)(\d+)$", p)
        if prev == "r" and len(p) == 1:   # (ORAS's routes r_a ... r_g)
            words.append(p.upper())
        elif p in WORDS:
            words.append(WORDS[p])
        elif m and m.group(1) in WORDS:
            words += [WORDS[m.group(1)], str(int(m.group(2)))]
        elif p.isdigit():
            words.append(str(int(p)))
        else:
            words.append(p.title())
        prev = p
    if all(w.isdigit() for w in words):
        words.insert(0, "Fanfare" if raw.lower().startswith("me_") else "Track")
    name = " ".join(words).replace("O- Power", "O-Power").replace("Ta Dah", "Ta-Dah")
    if tag in ("XY", "USUM"):
        name += f" ({tag})"
    return name or raw


def slug(name):
    s = re.sub(r"[^a-z0-9]+", "_", name.lower().replace("'", "")).strip("_")
    return s or "track"


# ---------------------------------------------------------------------------------- tools
def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def probe(ffprobe, path):
    """(seconds, kbps) or (None, None)."""
    r = run([ffprobe, "-v", "error", "-show_entries", "format=duration,bit_rate", "-of", "json", path])
    try:
        f = json.loads(r.stdout)["format"]
        return float(f.get("duration") or 0), float(f.get("bit_rate") or 0) / 1000
    except (ValueError, KeyError):
        return None, None


def encode(ffmpeg, src, dest, seconds, quality=QUALITY):
    """Re-encode to Ogg Vorbis, cut at MAX_SECONDS (with a short fade) when longer."""
    cmd = [ffmpeg, "-v", "error", "-y", "-i", src, "-vn", "-map_metadata", "-1"]
    trimmed = bool(seconds and seconds > MAX_SECONDS + 1)
    if trimmed:
        cmd += ["-t", str(MAX_SECONDS), "-af", f"afade=t=out:st={MAX_SECONDS - 4}:d=4"]
    cmd += ["-c:a", "libvorbis", "-q:a", quality, dest]
    r = run(cmd)
    if r.returncode != 0 or not os.path.isfile(dest):
        raise RuntimeError(r.stderr.strip()[:300])
    return trimmed


def sha1(path=None, data=None):
    h = hashlib.sha1()
    if data is not None:
        h.update(data)
    else:
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(1 << 20), b""):
                h.update(block)
    return h.hexdigest()


class Rom:
    """Minimal reader for a decrypted (NoCrypto) .3ds: its RomFS files. (Same as the one in
    kanto_handoff/alola_rom_tools/romfs.py.)"""
    def __init__(self, path):
        self.f = f = open(path, "rb")
        f.seek(0x120)
        o0 = struct.unpack("<I", f.read(4))[0] * 0x200
        f.seek(o0 + 0x188)
        if not f.read(8)[7] & 4:
            raise ValueError("encrypted")
        f.seek(o0 + 0x1B0)
        base = o0 + struct.unpack("<I", f.read(4))[0] * 0x200
        f.seek(base)
        ivfc = f.read(0x60)
        if ivfc[:4] != b"IVFC":
            raise ValueError("no RomFS")
        mhs = struct.unpack_from("<I", ivfc, 8)[0]
        bs = 1 << struct.unpack_from("<I", ivfc, 0x4C)[0]
        self.l3 = base + ((0x60 + mhs + bs - 1) // bs) * bs
        f.seek(self.l3)
        h = struct.unpack("<10I", f.read(0x28))
        self.data = h[9]
        f.seek(self.l3 + h[3])
        self.dm = f.read(h[4])
        f.seek(self.l3 + h[7])
        self.fm = f.read(h[8])
        self.files = {}
        self._walk(0, "")

    def _walk(self, d, path):
        _par, _sib, child, ffile, _nh, nl = struct.unpack_from("<6I", self.dm, d)
        name = self.dm[d + 0x18:d + 0x18 + nl].decode("utf-16le")
        p = path + name + "/" if d else ""
        fo = ffile
        while fo != 0xFFFFFFFF:
            _fp, fs, off, size, _fnh, fnl = struct.unpack_from("<IIQQII", self.fm, fo)
            self.files[p + self.fm[fo + 0x20:fo + 0x20 + fnl].decode("utf-16le")] = (off, size)
            fo = fs
        c = child
        while c != 0xFFFFFFFF:
            self._walk(c, p)
            c = struct.unpack_from("<I", self.dm, c + 4)[0]

    def read(self, name):
        off, size = self.files[name]
        self.f.seek(self.l3 + self.data + off)
        return self.f.read(size)


# ---------------------------------------------------------------------------------- building
class Library:
    def __init__(self, args):
        self.a = args
        self.ffmpeg = args.ffmpeg
        self.ffprobe = os.path.join(os.path.dirname(args.ffmpeg), "ffprobe" + (".exe" if os.name == "nt" else ""))
        self.tracks, self.sounds, self.by_sha, self.used = [], [], {}, set()
        self.sources, self.problems = {}, []
        old = os.path.join(OUT, "manifest.json")
        self.old = {}
        if os.path.isfile(old):
            with open(old, encoding="utf-8") as f:
                prev = json.load(f)
            self.old = {t["sha1"]: t for t in prev.get("tracks", []) + prev.get("sounds", [])}

    def _dest(self, gen, source, name, ext):
        base = f"gen{gen}/{source}/{slug(name)}"
        dest, n = base + ext, 2
        while dest in self.used:
            dest, n = f"{base}_{n}{ext}", n + 1
        self.used.add(dest)
        return dest

    def _dupe(self, digest, source, original):
        hit = self.by_sha.get(digest)
        if hit is not None:
            hit.setdefault("also_in", []).append(f"{source}: {original}")
            return True
        return False

    def add_track(self, source, kind, name, gen, original, digest, make):
        """make(dest_abs) writes the file and returns {'trimmed': bool}; skipped when it's already built."""
        if self._dupe(digest, source, original):
            return
        prev = self.old.get(digest)
        ext = ".mid" if original.lower().endswith((".mid", ".midi")) else ".ogg"
        if prev and prev.get("source") == source and os.path.isfile(os.path.join(OUT, prev["file"])) \
                and prev["file"] not in self.used:
            dest = prev["file"]
            self.used.add(dest)
            info = {"trimmed": prev.get("trimmed", False)}
        else:
            dest = self._dest(gen, source, name, ext)
            path = os.path.join(OUT, dest)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            try:
                info = make(path)
            except Exception as e:  # (a broken file: say so, carry on)
                self.problems.append(f"{source}: {original}: {e}")
                self.used.discard(dest)
                return
        entry = {"file": dest, "name": name, "gen": gen, "source": source, "kind": kind,
                 "original": original, "sha1": digest}
        if info.get("trimmed"):
            entry["trimmed"] = True
        self.tracks.append(entry)
        self.by_sha[digest] = entry

    # ---- fan games
    def fan(self, key):
        title, credit, where, home = FAN[key]
        root = where if os.path.isabs(where) else os.path.join(self.a.downloads, where)
        if not os.path.isdir(root):
            self.problems.append(f"{key}: not found at {root}")
            return
        self.sources[key] = {"title": title, "credit": credit, "where": root, "kind": "fan game"}
        print(f"{title}: {root}")
        for folder in sorted(os.listdir(root)):
            kind = folder.lower()
            if kind not in ("bgm", "me", "bgs", "se"):
                continue
            for dp, _dn, fn in sorted(os.walk(os.path.join(root, folder))):
                for f in sorted(fn):
                    stem, ext = os.path.splitext(f)
                    if ext.lower() not in MUSIC_EXT:
                        continue
                    src = os.path.join(dp, f)
                    original = os.path.relpath(src, os.path.dirname(root)).replace("\\", "/")
                    if kind == "se":
                        self.add_sound(key, src, os.path.relpath(src, os.path.join(root, folder)), original)
                        continue
                    name, gen = fan_track(key, stem, home, ext.lower())
                    self.add_track(key, kind, name, gen, original, sha1(src),
                                   lambda dest, src=src, ext=ext.lower(): self._convert(src, dest, ext))

    def _convert(self, src, dest, ext):
        if ext in (".mid", ".midi"):
            shutil.copyfile(src, dest)
            return {}
        seconds, kbps = probe(self.ffprobe, src)
        if ext == ".ogg" and seconds is not None and seconds <= MAX_SECONDS + 1 and kbps <= KEEP_KBPS:
            shutil.copyfile(src, dest)
            return {}
        return {"trimmed": encode(self.ffmpeg, src, dest, seconds)}

    def add_sound(self, source, src, rel, original):
        if self.a.no_sounds:
            return
        digest = sha1(src)
        if self._dupe(digest, source, original):
            return
        stem, ext = os.path.splitext(rel.replace("\\", "/"))
        ext = ext.lower()
        out_ext = ".ogg" if ext == ".wav" else ext
        base = "sounds/" + source + "/" + "/".join(slug(p) for p in stem.split("/"))
        dest, n = base + out_ext, 2
        while dest in self.used:
            dest, n = f"{base}_{n}{out_ext}", n + 1
        self.used.add(dest)
        path = os.path.join(OUT, dest)
        if not os.path.isfile(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            try:
                if ext == ".wav":
                    encode(self.ffmpeg, src, path, None, quality="4")
                else:
                    shutil.copyfile(src, path)
            except Exception as e:
                self.problems.append(f"{source}: {original}: {e}")
                return
        entry = {"file": dest, "name": tidy(os.path.basename(stem)), "source": source, "kind": "sound",
                 "original": original, "sha1": digest}
        self.sounds.append(entry)
        self.by_sha[digest] = entry

    # ---- 3DS game files
    def rom(self, key):
        title, credit, where, gen, pattern = ROMS[key]
        path = where if os.path.isabs(where) else os.path.join(self.a.downloads, where)
        if not os.path.isfile(path):
            self.problems.append(f"{key}: not found at {path}")
            return
        try:
            rom = Rom(path)
        except (ValueError, struct.error, OSError) as e:
            self.problems.append(f"{key}: can't read {path}: {e}")
            return
        self.sources[key] = {"title": title, "credit": credit, "where": path, "kind": "game file"}
        work = os.path.join(self.a.work, key)
        os.makedirs(work, exist_ok=True)
        names = sorted(n for n in rom.files if n.lower().endswith(".bcstm")
                       and re.match(pattern, n.rsplit("/", 1)[-1]) and "test" not in n.lower())
        print(f"{title}: {len(names)} streams")
        for n in names:
            data = rom.read(n)
            stem = n.rsplit("/", 1)[-1][:-len(".bcstm")]
            raw = stem.replace(".dspadpcm", "")
            kind = "me" if raw.lower().startswith("me_") else "bgm"
            name = stream_name(stem)
            g = gen
            if key != "pmd_gti":
                g = 6 if "_xy_" in raw.lower() or "_sg_" in raw.lower() else 7
            self.add_track(key, kind, name, g, n, sha1(data=data),
                           lambda dest, data=data, stem=stem: self._render(data, stem, work, dest))

    def _render(self, data, stem, work, dest):
        src = os.path.join(work, stem + ".bcstm")
        wav = os.path.join(work, stem + ".wav")
        with open(src, "wb") as f:
            f.write(data)
        r = run([self.a.vgmstream, "-i", "-o", wav, src])     # -i: once through, no loop repeats
        if r.returncode != 0 or not os.path.isfile(wav):
            raise RuntimeError((r.stderr or r.stdout).strip()[:300])
        seconds, _ = probe(self.ffprobe, wav)
        try:
            return {"trimmed": encode(self.ffmpeg, wav, dest, seconds)}
        finally:
            for p in (src, wav):
                try:
                    os.remove(p)
                except OSError:
                    pass

    # ---- the manifest
    def write(self):
        from collections import Counter
        for t in self.tracks:  # each track's length; a "song" under 20 seconds is a fanfare (no jukebox)
            path = os.path.join(OUT, t["file"])
            if "seconds" not in t and not t["file"].endswith(".mid") and os.path.isfile(path):
                seconds, _ = probe(self.ffprobe, path)
                if seconds:
                    t["seconds"] = round(seconds, 1)
            if t["kind"] == "bgm" and t.get("seconds", 999) < SHORTEST_SONG:
                t["kind"] = "me"
        self.tracks.sort(key=lambda t: (t["gen"] == 0, t["gen"], t["name"].casefold(), t["source"]))
        self.sounds.sort(key=lambda t: (t["source"], t["file"]))
        size = sum(os.path.getsize(os.path.join(OUT, t["file"])) for t in self.tracks + self.sounds
                   if os.path.isfile(os.path.join(OUT, t["file"])))
        for k in self.sources:
            self.sources[k]["where"] = self.sources[k]["where"].replace(os.path.expanduser("~"), "~")
        data = {
            "about": "Kanto Math Game music library, built by dev/builders/build_music_library.py. "
                     "Tracks: by generation (0 = not from a Pokemon game) then name.",
            "summary": {"tracks": len(self.tracks), "sounds": len(self.sounds), "megabytes": round(size / 2 ** 20),
                        "by_generation": {str(g): n for g, n in sorted(Counter(t["gen"] for t in self.tracks).items())},
                        "by_source": dict(sorted(Counter(t["source"] for t in self.tracks).items()))},
            "sources": self.sources,
            "not_rendered": NOT_RENDERED,
            "problems": self.problems,
            "tracks": self.tracks,
            "sounds": self.sounds,
        }
        with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print(json.dumps(data["summary"], indent=1))
        for p in self.problems:
            print("  problem:", p)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--downloads", default=DOWNLOADS)
    ap.add_argument("--ffmpeg", default=os.path.join(TOOLS, "ffmpeg", "bin", "ffmpeg.exe"))
    ap.add_argument("--vgmstream", default=os.path.join(TOOLS, "vgmstream", "vgmstream-cli.exe"))
    ap.add_argument("--work", default=os.path.join(TOOLS, "work"))
    ap.add_argument("--only", default="", help="comma-separated source keys")
    ap.add_argument("--no-sounds", action="store_true", help="skip the sound effects")
    a = ap.parse_args(argv)
    for tool in (a.ffmpeg, a.vgmstream):
        if not os.path.isfile(tool):
            sys.exit(f"missing tool: {tool}")
    only = set(filter(None, a.only.split(",")))
    lib = Library(a)
    os.makedirs(OUT, exist_ok=True)
    if only:  # (a partial run keeps the other sources' entries)
        prev = os.path.join(OUT, "manifest.json")
        if os.path.isfile(prev):
            with open(prev, encoding="utf-8") as f:
                p = json.load(f)
            for t in p.get("tracks", []) + p.get("sounds", []):
                if t["source"] not in only:
                    (lib.sounds if t["kind"] == "sound" else lib.tracks).append(t)
                    lib.by_sha[t["sha1"]] = t
                    lib.used.add(t["file"])
            lib.sources = {k: v for k, v in p.get("sources", {}).items() if k not in only}
    for key in FAN:
        if not only or key in only:
            lib.fan(key)
    for key in ROMS:
        if not only or key in only:
            lib.rom(key)
    lib.write()


if __name__ == "__main__":
    main(sys.argv[1:])
