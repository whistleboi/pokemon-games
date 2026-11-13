"""Soft soil and Berry trees (Jordan, 11-12: "implement the berry patches and berry system").

Where: a map's "berry_soil" [[x, y, berry], ...] (Hoenn: Emerald's own Berry-tree spots, each with the Berry Emerald
starts it with: dev/builders/town_maps/emerald.py). Each patch starts ripe, as in the games.

How it works (Emerald / ORAS):
- a ripe tree: pick its Berries (into the Berries pocket) and the soil is empty again;
- empty soil: plant a Berry from your Bag (src/states/berry_patch.py: PlantBerryState);
- a planted Berry grows on real time through five stages (planted, sprout, taller, flowering, Berries); each kind
  takes its own hours a stage (Essentials' berry plant data, from Pokemon Journeys V18's PBS/berryplants.txt);
- with the Wailmer Pail (Route 104's Pretty Petal flower shop), water it once in each stage: each watering raises
  the harvest from the kind's least toward its most.
State: story_flags["berry_patches"] {"AREA:x,y": {"berry": key or None, "t": planted (seconds), "water": [stages]}};
a patch with no record is still its first, ripe tree."""
import time

# hours a stage, (Essentials' drying rate, unused), least and most Berries
GROWTH = {
    "CHERI_BERRY": (3, 15, 2, 5), "CHESTO_BERRY": (3, 15, 2, 5), "PECHA_BERRY": (3, 15, 2, 5), "RAWST_BERRY": (3, 15, 2, 5),
    "ASPEAR_BERRY": (3, 15, 2, 5), "LEPPA_BERRY": (4, 15, 2, 5), "ORAN_BERRY": (4, 15, 2, 5), "PERSIM_BERRY": (4, 15, 2, 5),
    "LUM_BERRY": (12, 8, 2, 5), "SITRUS_BERRY": (8, 7, 2, 5), "FIGY_BERRY": (5, 10, 1, 5), "WIKI_BERRY": (5, 10, 1, 5),
    "MAGO_BERRY": (5, 10, 1, 5), "AGUAV_BERRY": (5, 10, 1, 5), "IAPAPA_BERRY": (5, 10, 1, 5), "RAZZ_BERRY": (2, 35, 2, 10),
    "BLUK_BERRY": (2, 35, 2, 10), "NANAB_BERRY": (2, 35, 2, 10), "WEPEAR_BERRY": (2, 35, 2, 10), "PINAP_BERRY": (2, 35, 2, 10),
    "POMEG_BERRY": (8, 8, 1, 5), "KELPSY_BERRY": (8, 8, 1, 5), "QUALOT_BERRY": (8, 8, 1, 5), "HONDEW_BERRY": (8, 8, 1, 5),
    "GREPA_BERRY": (8, 8, 1, 5), "TAMATO_BERRY": (8, 8, 1, 5), "CORNN_BERRY": (6, 10, 2, 10), "MAGOST_BERRY": (6, 10, 2, 10),
    "RABUTA_BERRY": (6, 10, 2, 10), "NOMEL_BERRY": (6, 10, 2, 10), "SPELON_BERRY": (15, 8, 2, 15), "PAMTRE_BERRY": (15, 8, 3, 15),
    "WATMEL_BERRY": (15, 8, 2, 15), "DURIN_BERRY": (15, 8, 3, 15), "BELUE_BERRY": (15, 8, 2, 15),
}
STAGES = ("planted", "sprout", "taller", "flowering", "berries")
RIPE = 4
STAGE_WORDS = {0: "{a} was planted here.", 1: "{a} has sprouted.", 2: "The {b} plant is growing bigger.",
               3: "The {b} plant is in bloom!"}

clock = time.time  # (the checks wind it on)


def name(berry):
    return str(berry).replace("_BERRY", "").title() + " Berry"


def a(word):
    return ("an " if word[:1].upper() in "AEIOU" else "a ") + word


def plural(word, n):
    return word if n == 1 else (word[:-1] + "ies" if word.endswith("y") else word + "s")


def _all(story):
    return story.story_flags.setdefault("berry_patches", {})


def record(story, area, xy, first):
    """This patch now: {"berry", "t", "water"} (no record: its first tree, ripe with the Berry it starts with)."""
    rec = _all(story).get(f"{area}:{xy[0]},{xy[1]}")
    return rec if rec is not None else {"berry": first, "t": None, "water": []}


def stage(rec, now=None):
    """0-4 (STAGES), or None for empty soil."""
    if not rec.get("berry"):
        return None
    if rec.get("t") is None:
        return RIPE
    hours = GROWTH.get(rec["berry"], (3, 0, 2, 5))[0]
    return min(RIPE, int(((now if now is not None else clock()) - rec["t"]) // (hours * 3600)))


def harvest_size(rec):
    lo, hi = GROWTH.get(rec.get("berry"), (3, 0, 2, 5))[2:]
    if rec.get("t") is None:  # (the tree it starts with)
        return lo + 1
    return lo + round((hi - lo) * len(set(rec.get("water") or [])) / 4)


def watered(rec, now=None):
    st = stage(rec, now)
    return st is not None and st < RIPE and st in (rec.get("water") or [])


def touch(story, area, xy, first):
    """Walk up to a patch: (lines, wants_planting). Picks ripe Berries, or waters (with the Wailmer Pail)."""
    key = f"{area}:{xy[0]},{xy[1]}"
    rec = dict(record(story, area, xy, first))
    st = stage(rec)
    inv = story.inventory
    if st is None:
        return ["It's soft, loamy soil."], True
    b = name(rec["berry"])
    if st == RIPE:
        n = harvest_size(rec)
        inv[rec["berry"]] = inv.get(rec["berry"], 0) + n
        _all(story)[key] = {"berry": None, "t": None, "water": []}
        return [f"It's {a(b)} tree!", f"You picked {n} {plural(b, n)}!",
                "The soil is soft and empty again."], False
    lines = [STAGE_WORDS[st].format(b=b, a=a(b).capitalize())]
    if inv.get("WAILMER_PAIL", 0) > 0:
        if st in (rec.get("water") or []):
            lines.append("The soil is still damp.")
        else:
            rec["water"] = list(rec.get("water") or []) + [st]
            _all(story)[key] = rec
            lines.append(f"You watered the {b} with the Wailmer Pail.")
    else:
        lines.append("It would grow better with some water.")
    return lines, False


def plant(story, area, xy, berry):
    inv = story.inventory
    if inv.get(berry, 0) <= 0:
        return [f"You don't have {a(name(berry))}."]
    inv[berry] -= 1
    if inv[berry] <= 0:
        del inv[berry]
    _all(story)[f"{area}:{xy[0]},{xy[1]}"] = {"berry": berry, "t": clock(), "water": []}
    hours = GROWTH.get(berry, (3,))[0] * 4
    return [f"You planted {a(name(berry))} in the soft soil.", f"It should bear Berries in about {hours} hours."]


def plantable(story):
    """The Berries in your Bag that can be planted (the kinds with a tree)."""
    return [b for b in GROWTH if story.inventory.get(b, 0) > 0]
