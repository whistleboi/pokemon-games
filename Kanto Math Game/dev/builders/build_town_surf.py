"""Towns' own Surf tables (11-18, Jordan: "if a player is able to Surf it in the game I want them to be able to Surf it in
our game"): the wild Pokemon on a walked town's water, from its saved Bulbapedia page, in its region's source game:
Hoenn Omega Ruby / Alpha Sapphire (Emerald where ORAS has none), Sinnoh Brilliant Diamond / Shining Pearl (Platinum,
then Diamond / Pearl), Johto HeartGold / SoulSilver, Kanto FireRed / LeafGreen. Each version is summed on its own and
the versions averaged, in whole percents (every species at least 1).
The pages are read first, outside the game, by kanto_handoff/hoenn_rom_tools/town_surf_rows.py (python -I).
    python dev/builders/build_town_surf.py <rows JSON> [--write] [--routes REGION]
--routes REGION: the region's routes, caves and lakes instead of its towns (11-18: Sinnoh's had no Surf tables, so its
water met the route's land Pokemon); a mostly-sea route is skipped (its whole table is its water's).
Writes <AREA>_SURF_PERCENTAGES (a region prefix as the file's others have: JOHTO_) and the town's
"surf_pool_percentages"; a town that has one already is left alone. Towns with no page or no Surf rows keep walk_town's
fallback (the nearest route's table).
"""
import json
import os
import re
import sys

FILES = {"HOENN": "hoenn_area_data.json", "SINNOH": "sinnoh_area_data.json", "JOHTO": "johto_area_data.json",
         "KANTO": "pokemon_area_data.json"}
PREFIX = {"JOHTO": "JOHTO_"}
GAMES = {"HOENN": [("OR", "AS"), ("E",)], "SINNOH": [("BD", "SP"), ("PT",), ("D", "P")], "JOHTO": [("HG", "SS")],
         "KANTO": [("FR", "LG")]}
TITLE = {"SINNOH_POKEMON_LEAGUE": "Pokemon League (Sinnoh)", "POKEATHLON_DOME": "Pokeathlon Dome", "MT_CORONET_BASE": "Mount Coronet",
         "VICTORY_ROAD_SINNOH": "Victory Road (Sinnoh)"}


def plain(t):
    """A page title without its accents (the file names' é may come through as anything)."""
    return re.sub(r"[^a-z0-9()]+", "", t.lower().replace("é", "e"))


def norm(name):
    n = name.lower().replace("♀", "-f").replace("♂", "-m").replace("é", "e").replace(".", "").replace("'", "").replace("’", "")
    return re.sub(r"\s+", "-", n.strip())


def table(rows, region, names):
    """{species id: percent} from a page's Surf rows, by the region's games; (table, games used) or (None, None)."""
    for group in GAMES[region]:
        per = {}
        for mon, _lv, rates, games in rows:
            vals = [float(m.group(1)) for c in rates for m in [re.match(r"(\d+(?:\.\d+)?)%", c.strip())] if m]
            if not vals:
                continue
            pid = names.get(norm(mon)) or names.get(norm(mon).replace("-", ""))
            if pid is None:
                continue
            for v in group:
                if games.get(v):
                    per.setdefault(v, {})
                    per[v][pid] = per[v].get(pid, 0) + sum(vals) / len(vals)
        if per:
            tot = {}
            for t in per.values():
                for p, w in t.items():
                    tot[p] = tot.get(p, 0) + w / len(per)
            whole = sum(tot.values()) or 1   # (a page of several parts, Mount Coronet's: scaled to 100)
            return {str(p): max(1, round(w * 100 / whole)) for p, w in sorted(tot.items(), key=lambda kv: -kv[1])}, "/".join(group)
    return None, None


def main(rows_path, write, routes=None):
    pages = {plain(k): v for k, v in json.load(open(rows_path, encoding="utf-8")).items()}
    raw_names = json.load(open(os.path.join("assets", "pokemon_names.json"), encoding="utf-8"))
    names = {norm(v): int(k) for k, v in raw_names.items() if int(k) <= 1025}
    names.update({norm(v).replace("-", ""): int(k) for k, v in raw_names.items() if int(k) <= 1025})
    tm = json.load(open(os.path.join("assets", "town_maps.json"), encoding="utf-8"))
    for region, fname in FILES.items():
        path = os.path.join("assets", fname)
        text = open(path, "rb").read().decode("utf-8")
        data = json.loads(text)
        changed = False
        for area, a in (data.get("STORY_PROGRESSION") or {}).items():
            if routes and region != routes:
                continue
            if (not isinstance(a, dict) or (a.get("area_type") == "town") == bool(routes) or a.get("surf_pool_percentages")
                    or f"{PREFIX.get(region, '')}{area}_SURF_PERCENTAGES" in data or f"{area}_SURF_PERCENTAGES" in data):
                continue
            m = tm.get(area)
            arts = [m.get("art") or []] + [f.get("art") or [] for f in m.get("floors") or [] if isinstance(f, dict)] if isinstance(m, dict) else []
            cells = [c for art in arts for r in art for c in r]
            wet = sum(c in "o[]{}:" for c in cells)
            if not wet or (routes and wet * 2 > len(cells)):   # (a sea route: its whole table is its water's already)
                continue
            title = TITLE.get(area) or a.get("route_name") or area.title().replace("_", " ")
            rows = next((pages[plain(t)] for t in (title, f"{region.title()} {title}", f"{title} ({region.title()})")
                         if plain(t) in pages), None)
            if rows is None:
                print(f"{area}: no page ({title})")
                continue
            t, used = table(rows, region, names)
            if not t:
                print(f"{area}: no Surf rows on its page (the games have none): fallback stays")
                continue
            key = f"{PREFIX.get(region, '')}{area}_SURF_PERCENTAGES"
            print(f"{area}: {key} from {used}: {t}")
            if key in data:
                continue
            nl = "\r\n" if "\r\n" in text else "\n"
            i = text.index(f'"{area}": {{') + len(f'"{area}": {{')
            text = text[:i] + f'"surf_pool_percentages": "{key}", ' + text[i:]
            j = text.index("{") + 1
            text = text[:j] + f'{nl}  "{key}": {json.dumps(t)},' + text[j:]
            changed = True
        if changed and write:
            json.loads(text)
            open(path, "wb").write(text.encode("utf-8"))
            print("wrote", path)


if __name__ == "__main__":
    main(sys.argv[1], "--write" in sys.argv, sys.argv[sys.argv.index("--routes") + 1] if "--routes" in sys.argv else None)
