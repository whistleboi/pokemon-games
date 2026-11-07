"""Legends: Z-A's new Mega Evolutions (Jordan, 11-06: their Mega Stones are found in Hyperspace Lumiose):
stats and types from PokeAPI's tables (dev/builders/out/pokeapi_csv: pokemon, pokemon_stats, pokemon_types,
items) -> assets/mega_forms.json (added to), and the stones in GAME_CONFIG's KEY_ITEMS (pokemon_area_data.json).
No sprites (Jordan, 11-06: PokeAPI's are 3D renders, not pixel art): these Megas show their species' own sprite
until pixel art is found. Each stone's picture is the game's own Venusaurite (30 x 30 pixel art) recoloured to
its Mega's first type -> assets/sprites/items/<stone>.png.

    python dev/builders/import_za_megas.py
"""
import csv
import json
import os
import urllib.request

CSV = os.path.join("dev", "builders", "out", "pokeapi_csv")
SPRITES = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/"
FIRST, LAST = 10278, 10303  # clefable-mega .. falinks-mega (Legends: Z-A; not the Mega Dimension DLC's)
STAT = {"1": "HP", "2": "ATTACK", "3": "DEFENSE", "4": "SPECIAL-ATTACK", "5": "SPECIAL-DEFENSE", "6": "SPEED"}
TYPES = {"1": "NORMAL", "2": "FIGHTING", "3": "FLYING", "4": "POISON", "5": "GROUND", "6": "ROCK", "7": "BUG",
         "8": "GHOST", "9": "STEEL", "10": "FIRE", "11": "WATER", "12": "GRASS", "13": "ELECTRIC", "14": "PSYCHIC",
         "15": "ICE", "16": "DRAGON", "17": "DARK", "18": "FAIRY"}
STONE = {"floette": "floettite", "zygarde": "zygardite"}


def rows(name):
    with open(os.path.join(CSV, name + ".csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fetch(url, path):
    if os.path.exists(path):
        return True
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = r.read()
    except Exception:
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return True


TYPE_COLOR = {"NORMAL": (200, 196, 172), "FIRE": (240, 120, 48), "WATER": (96, 144, 240), "GRASS": (120, 200, 80),
              "ELECTRIC": (248, 208, 48), "ICE": (152, 216, 216), "FIGHTING": (192, 48, 40), "POISON": (160, 64, 160),
              "GROUND": (224, 192, 104), "FLYING": (168, 144, 240), "PSYCHIC": (248, 88, 136), "BUG": (168, 184, 32),
              "ROCK": (184, 160, 56), "GHOST": (112, 88, 152), "DRAGON": (112, 56, 248), "DARK": (112, 88, 72),
              "STEEL": (184, 184, 208), "FAIRY": (238, 153, 172)}


def stone_picture(stone, kind):
    """The stone's picture: the Venusaurite's pixels, its colourful ones moved to the type's colour."""
    import colorsys
    import pygame
    pal = pygame.image.load(os.path.join("assets", "sprites", "items", "venusaurite.png"))
    src = pygame.Surface(pal.get_size(), pygame.SRCALPHA, 32)  # (out of its palette: full colour, see-through)
    src.blit(pal, (0, 0))
    out = src.copy()
    tr, tg, tb = (c / 255 for c in TYPE_COLOR.get(kind, (200, 200, 200)))
    th, ts, _tv = colorsys.rgb_to_hsv(tr, tg, tb)
    for y in range(src.get_height()):
        for x in range(src.get_width()):
            r, g, b, a = src.get_at((x, y))
            if not a:
                continue
            h, sat, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if sat > 0.25:  # (the stone's colour; the white symbol and dark outline stay)
                nr, ng, nb = colorsys.hsv_to_rgb(th, max(sat, ts * 0.8), v)
                out.set_at((x, y), (int(nr * 255), int(ng * 255), int(nb * 255), a))
    pygame.image.save(out, os.path.join("assets", "sprites", "items", f"{stone}.png"))


def main():
    mons = {int(r["id"]): r for r in rows("pokemon") if FIRST <= int(r["id"]) <= LAST}
    stats, types = {}, {}
    for r in rows("pokemon_stats"):
        if int(r["pokemon_id"]) in mons:
            stats.setdefault(int(r["pokemon_id"]), {})[STAT[r["stat_id"]]] = int(r["base_stat"])
    for r in sorted(rows("pokemon_types"), key=lambda r: int(r["slot"])):
        if int(r["pokemon_id"]) in mons:
            types.setdefault(int(r["pokemon_id"]), []).append(TYPES[r["type_id"]])
    items = {r["identifier"] for r in rows("items")}
    path = os.path.join("assets", "mega_forms.json")
    forms = json.load(open(path, encoding="utf-8"))
    stones, missing = [], []
    out_dir = os.path.join("assets", "sprites", "pokemon", "mega")
    for pid, r in sorted(mons.items()):
        species = int(r["species_id"])
        base = r["identifier"].replace("-mega", "")
        stone = STONE.get(base, base + "ite")
        if stone not in items:
            stone = next((i for i in items if i.startswith(base[:5]) and i.endswith("ite")), stone)
        key = stone.upper().replace("-", "_")
        name = "MEGA " + base.upper().replace("-", " ")
        sprite = f"{species}_mega.png"
        stone_picture(stone, types[pid][0])
        entry = {"form": "mega", "name": name, "item": key, "types": types[pid], "stats": stats[pid], "sprite": sprite,
                 "source": "Legends: Z-A"}
        have = forms.setdefault(str(species), [])
        if not any(e.get("item") == key for e in have):
            have.append(entry)
        stones.append(key)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(forms, f, indent=1, ensure_ascii=False)
    # the stones are key items
    p = os.path.join("assets", "pokemon_area_data.json")
    text = open(p, encoding="utf-8", newline="").read()
    data = json.loads(text)
    keys = data["GAME_CONFIG"]["KEY_ITEMS"]
    new = [k for k in stones if k not in keys]
    if new:
        anchor = '"KEY_ITEMS": ['
        i = text.index(anchor) + len(anchor)
        text = text[:i] + "".join(f'"{k}", ' for k in new) + text[i:]
        json.loads(text)
        open(p, "w", encoding="utf-8", newline="").write(text)
    print(len(stones), "Megas:", stones, "| sprites missing:", missing)


if __name__ == "__main__":
    main()
