"""Town backgrounds from Bulbapedia (Jordan): every town without its own background gets the
overhead picture of that town from its region's games, the 2D pixel-art one where the region was
in several generations (Hoenn: Emerald/Ruby-Sapphire, Sinnoh: Platinum/Diamond-Pearl, Unova:
Black-White, Sevii: FireRed/LeafGreen, Johto: HeartGold/SoulSilver); Kalos, Alola, Galar and
Paldea only exist in 3D; the Orange and Decolore Islands only in the anime.

Saved as assets/backgrounds/<folder>/<area key>.png (the name CityState looks for), scaled up
with whole-pixel scaling so pixel art stays sharp. Already-present backgrounds are left alone.
Run from the game folder:  python dev/builders/fetch_town_backgrounds.py
"""
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

H = {"User-Agent": "Mozilla/5.0 (KantoMathGame town backgrounds)"}
# Picture tags to look for, best first, per region (the game the region follows; pixel art first).
PREFS = {
    "HOENN": ["E", "RS", "RSE", "ORAS"], "SINNOH": ["Pt", "DP", "BDSP", "PLA"], "UNOVA": ["BW", "Summer BW", "Summer B", "Summer W", "Spring BW", "B2W2", "Summer B2", "B", "W"],
    "KALOS": ["XY"], "ALOLA": ["SM", "USUM"], "GALAR": ["SwSh"], "PALDEA": ["SV"],
    "KANTO": ["FRLG", "RGBY"], "JOHTO": ["HGSS", "GSC"], "ORRE": ["Colosseum", "XD", "Coxd"],
    "ORANGE": ["anime"], "DECOLORE": ["anime"],
}
FOLDER = {"KANTO": "sevii", "ORANGE": "orange", "DECOLORE": "decolore", "ORRE": "orre"}
DECOLORE = {"HONEY_ISLAND", "SCALCHOP_ISLAND", "GRAND_SPECTRALA_ISLAND", "TOROM_ISLAND", "PALADIN_ISLAND"}
# Bulbapedia page names that differ from the game's area names.
PAGE = {
    "SINNOH_POKEMON_LEAGUE": "Pokémon League (Sinnoh)", "UNOVA_POKEMON_LEAGUE": "Pokémon League (Unova)",
    "KALOS_POKEMON_LEAGUE": "Pokémon League (Kalos)", "ALOLA_POKEMON_LEAGUE": "Pokémon League (Alola)",
    "OLIVINE_LIGHTHOUSE": "Glitter Lighthouse", "JUBILIFE_VILLAGE": "Jubilife Village",
    "MEETUP_SPOT": "Meetup Spot", "NARANJA_ACADEMY": "Naranja Academy", "PALDEA_RUINOUS_SHRINES": "Ruinous Shrines",
    "TERARIUM_CENTRAL_PLAZA": "Central Plaza", "SINJOH_CABIN": "Sinjoh Ruins", "BLACK_CITY": "Black City",
    "HAUOLI_CITY": "Hau'oli City", "STOW_ON_SIDE": "Stow-on-Side",
}
# Pictures that came out wrong (a warped strip, a photo of concept art): left to the generic town.
SKIP = {"SPIKEMUTH", "BLACK_CITY"}
TARGET_W = 1000  # about the size of the existing town maps


def api(**p):
    p.update(format="json")
    u = "https://bulbapedia.bulbagarden.net/w/api.php?" + urllib.parse.urlencode(p)
    for attempt in range(4):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30).read())
        except Exception:
            time.sleep(3 * (attempt + 1))
    return {}


def download(file_title):
    name = file_title[5:].replace(" ", "_")
    h = hashlib.md5(name.encode()).hexdigest()
    u = f"https://archives.bulbagarden.net/media/upload/{h[0]}/{h[:2]}/{urllib.parse.quote(name)}"
    for attempt in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=60).read()
        except Exception:
            time.sleep(3 * (attempt + 1))
    return None


def pick(images, page, tags):
    """The page's picture of the town from the region's game: '<Page> <TAG>.png' (any
    capitalisation), else the page's own '<Page>.png' (its infobox picture)."""
    base = page.split(" (")[0].lower()
    skip = ("annotated", "adventures", "pokemon center", "pokémon center", " gym", "map", "concept")
    stems = [(img, re.sub(r"\.(png|jpe?g)$", "", img[5:], flags=re.I).lower()) for img in images]
    stems = [(img, st) for img, st in stems if not any(w in st for w in skip)]
    for tag in tags:
        for img, st in stems:
            if st in (f"{base} {tag.lower()}", f"{page.lower()} {tag.lower()}"):
                return img
    for tag in tags:  # e.g. "Castelia City Gate BW": anything of that town from that game
        for img, st in stems:
            if st.startswith(base) and st.endswith(" " + tag.lower()):
                return img
    for img, st in stems:  # the infobox picture
        if st in (base, page.lower()):
            return img
    return None


def save(data, path):
    img = pygame.image.load(io.BytesIO(data))
    w, h = img.get_size()
    k = max(1, round(TARGET_W / w)) if w < TARGET_W else 1
    if k > 1:  # whole-pixel scaling keeps the pixel art sharp
        img = pygame.transform.scale(img, (w * k, h * k))
    elif w > 1600:  # huge 3D screenshots: smaller files
        img = pygame.transform.smoothscale(img, (1600, h * 1600 // w))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pygame.image.save(img, path)
    return img.get_size()


def main(missing_json):
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    missing = json.load(open(missing_json, encoding="utf-8"))  # [region, area key, ...] (see dev/checks)
    names = {}
    for f in os.listdir("assets"):
        if f.endswith("_area_data.json"):
            for k, a in json.load(open(os.path.join("assets", f), encoding="utf-8")).get("STORY_PROGRESSION", {}).items():
                names[k] = a.get("route_name")
    got, failed = [], []
    for region, key, *_ in missing:
        if key in SKIP:
            continue
        region = "DECOLORE" if key in DECOLORE else region
        page = PAGE.get(key) or names.get(key) or key.replace("_", " ").title()
        d = api(action="query", prop="images", titles=page, imlimit=500, redirects=1)
        images = [i["title"] for p in d.get("query", {}).get("pages", {}).values() for i in p.get("images", [])]
        img = pick(images, page, PREFS.get(region, []))
        time.sleep(1.0)
        if not img:
            failed.append((key, page))
            continue
        data = download(img)
        if not data:
            failed.append((key, img))
            continue
        folder = FOLDER.get(region, region.lower())
        size = save(data, f"assets/backgrounds/{folder}/{key.lower()}.png")
        got.append((key, img, size))
        print("ok", key, "<-", img, size, flush=True)
        time.sleep(1.0)
    print(f"\n{len(got)} saved, {len(failed)} not found:")
    for f in failed:
        print("  ", f)


if __name__ == "__main__":
    main(sys.argv[1])
