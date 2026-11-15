"""Hoenn's real wild Pokemon (Jordan, 11-14: "use the real wild pools ... the bulbapedia hoenn pages"): each area's pools
from its saved Bulbapedia page, Omega Ruby / Alpha Sapphire's tables first, Emerald's where ORAS has none.

The pages are read first, outside the game, by kanto_handoff/hoenn_rom_tools/bulba_wild.py (python -I: Downloads are
untrusted), into one JSON of rows. This turns those rows into the area's pools, by its rates:
- walking (grass, long grass, caves, sand...): the area's pool (its "wild_pool_percentages");
- surfing: <AREA>_SURF_PERCENTAGES (the area's "surf_pool_percentages": wild Pokemon out on the water, dungeon.py), or the
  area's own pool where there is no walking at all (the sea routes);
- fishing: <AREA>_OLD_ROD_PERCENTAGES / _GOOD_ROD_ / _SUPER_ROD_ (route_actions._fishing_pool reads those names);
- Rock Smash: <AREA>_ROCK_SMASH_PERCENTAGES (the area's "rock_smash_pool_percentages").
Horde encounters, DexNav-only (hidden) Pokemon, gifts and one-off Pokemon are left out. Both versions' Pokemon are kept.
A pool's rare special forms (ids 2000 on) stay as they were. Only the pools are rewritten, in place.
    python dev/builders/build_hoenn_wild.py <rows JSON from bulba_wild.dump_all>
Prints what it changed and the areas with no information.
"""
import json
import os
import re
import sys

DATA = os.path.join("assets", "hoenn_area_data.json")
# a page for an area whose name differs; the Safari Zone's areas by its page's parts
PAGE = {"HOENN_VICTORY_ROAD": "Victory Road (Hoenn)", "HOENN_MAGMA_HIDEOUT": "Team Magma Hideout",
        "HOENN_ABANDONED_SHIP": "Sea Mauville", "HOENN_SAFARI_ZONE": "Hoenn Safari Zone"}
SKIP_LOC = ("horde", "gift", "trade", "only one", "headbutt")
RODS = {"old rod": "OLD_ROD", "good rod": "GOOD_ROD", "super rod": "SUPER_ROD"}


def norm(name):
    n = name.lower().replace("♀", "-f").replace("♂", "-m").replace("é", "e").replace(".", "").replace("'", "").replace("’", "")
    return re.sub(r"\s+", "-", n.strip())


def rate(cells):
    vals = [float(m.group(1)) for c in cells for m in [re.match(r"(\d+(?:\.\d+)?)%", c.strip())] if m]
    return sum(vals) / len(vals) if vals else None


def kind_of(loc, note):
    l, n = loc.lower(), note.lower()
    if any(s in l for s in SKIP_LOC) or "hidden" in n or "special" in n or "dexnav" in n:
        return None
    for k, v in RODS.items():
        if k in l:
            return v
    if "surf" in l:
        return "SURF"
    if "rock smash" in l:
        return "ROCK_SMASH"
    if "dive" in l or "seaweed" in l:
        return "DIVE"
    return "WALK"


def pools_from(rows, names, part=None, emerald=False):
    """{kind: {species id: weight}} from a page's rows (one part of it: a Safari Zone area); unknown names returned too."""
    out, unknown = {}, set()
    for r in rows:
        if emerald:
            mon, loc, _lv, rates, note, pt = r
        else:
            mon, loc, _lv, rates, _or, _as, note, pt = r
        if part is not None and not (pt == part or pt.startswith(part + " ")):   # (Emerald's "Area 5 - East")
            continue
        k = kind_of(loc, note)
        w = rate(rates)
        if k is None or not w:
            continue
        pid = names.get(norm(mon))
        if pid is None:
            unknown.add(mon)
            continue
        out.setdefault(k, {})
        out[k][pid] = out[k].get(pid, 0) + w
    return {k: {str(p): max(1, round(w)) for p, w in v.items()} for k, v in out.items()}, unknown


def set_pool(text, key, pool, anchor_key):
    """Write pool `key` into the data text: replace its object if there, else add it after anchor_key's."""
    body = json.dumps(pool)
    m = re.search(r'"%s":\s*\{[^{}]*\}' % re.escape(key), text)
    if m:
        return text[:m.start()] + f'"{key}": {body}' + text[m.end():]
    a = re.search(r'"%s":\s*\{[^{}]*\}' % re.escape(anchor_key), text)
    return text[:a.end()] + f',\n  "{key}": {body}' + text[a.end():]


def set_field(text, area, field, value):
    """Add / set a flat string field in an area's entry (right after its wild_pool_percentages)."""
    i = text.index(f'"{area}": {{')
    j = text.index('"wild_pool_percentages"', i)
    k = text.index('"', text.index(':', j) + 1)
    end = text.index('"', k + 1) + 1
    seg = text[i:text.index('"route_menu"', i)] if '"route_menu"' in text[i:i + 20000] else text[i:end]
    if f'"{field}"' in seg:
        f0 = text.index(f'"{field}"', i)
        v0 = text.index('"', text.index(':', f0) + 1)
        v1 = text.index('"', v0 + 1)
        return text[:v0] + f'"{value}' + text[v1:]
    return text[:end] + f', "{field}": "{value}"' + text[end:]


def main(rows_path):
    pages = json.load(open(rows_path, encoding="utf-8"))
    names = {norm(v): int(k) for k, v in json.load(open(os.path.join("assets", "pokemon_names.json"), encoding="utf-8")).items()
             if int(k) <= 1025}
    names.update({norm(v).replace("-", ""): int(k) for k, v in json.load(open(os.path.join("assets", "pokemon_names.json"),
                                                                                 encoding="utf-8")).items() if int(k) <= 1025})
    data = json.load(open(DATA, encoding="utf-8"))
    text = open(DATA, "rb").read().decode("utf-8")
    sp = data["STORY_PROGRESSION"]
    done, none, unknown_all = [], [], set()
    for area, a in sp.items():
        pool_key = a.get("wild_pool_percentages")
        if not pool_key or a.get("region") != "HOENN" or pool_key == "NO_WILD_INDOORS_PERCENTAGES":
            continue
        rn = a.get("route_name", "")
        title = PAGE.get(area) or (("Hoenn " + rn) if rn.startswith("Route") else rn)
        page = pages.get(title) or {}
        zones = a.get("zone_pools") or {}
        targets = [(None, pool_key, area)] if area != "HOENN_SAFARI_ZONE" else [
            (z["name"], zones[z["key"]], f"{area}_{z['key'].upper()}") for z in a.get("zones", [])]
        for part, pkey, prefix in targets:
            src = "ORAS"
            p, unk = pools_from(page.get("oras") or [], names, part)
            if not any(k in p for k in ("WALK", "SURF")):
                p, unk = pools_from(page.get("emerald") or [], names, part, emerald=True)
                src = "Emerald"
            unknown_all |= unk
            if not p:
                none.append(area + (f" {part}" if part else ""))
                continue
            old = data.get(pkey) or {}
            keep = {k: v for k, v in old.items() if int(k) >= 2000}   # (the rare special forms)
            sea = a.get("battle_type") in ("ocean", "sea", "water")
            if not p.get("WALK") and not sea and old:   # (only water Pokemon on the page, on dry ground: keep its own: the Magma Hideout)
                none.append(f"{area} (only its water Pokemon on the page; walking pool kept as it was)")
                p = {k: v for k, v in p.items() if k != "SURF"}
                walk = None
            else:
                walk = p.get("WALK") or p.get("SURF")
            made = []
            if walk:
                text = set_pool(text, pkey, dict(walk, **keep), pkey if pkey in data else "HOENN_SUPER_ROD_POOL_PERCENTAGES")
                made = [f"{pkey} ({src})"]
            if p.get("WALK") and p.get("SURF") and part is None:
                k = f"{prefix}_SURF_PERCENTAGES"
                text = set_pool(text, k, p["SURF"], pkey)
                text = set_field(text, area, "surf_pool_percentages", k)
                made.append(k)
            if p.get("ROCK_SMASH") and part is None:
                k = f"{prefix}_ROCK_SMASH_PERCENTAGES"
                text = set_pool(text, k, p["ROCK_SMASH"], pkey)
                text = set_field(text, area, "rock_smash_pool_percentages", k)
                made.append(k)
            for rod in ("OLD_ROD", "GOOD_ROD", "SUPER_ROD"):
                if p.get(rod) and part is None:
                    k = f"{area}_{rod}_PERCENTAGES"
                    text = set_pool(text, k, p[rod], pkey)
                    made.append(k)
            done.append((area, made))
    json.loads(text)
    open(DATA, "wb").write(text.encode("utf-8"))
    for area, made in done:
        print(area, made)
    print("NO INFORMATION:", none)
    print("names not found:", sorted(unknown_all))


if __name__ == "__main__":
    main(sys.argv[1])
