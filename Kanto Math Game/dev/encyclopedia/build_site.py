"""The encyclopedia site: one page that shows many linked pages, from the game's own data (region/encyclopedia, 11-24).

    python dev/encyclopedia/build_site.py OUT_DIR

Writes OUT_DIR/index.html (the page and its views), OUT_DIR/icons.css (every icon once), OUT_DIR/data/species.json (every
Pokemon: types, kind, size, base stats, evolutions) and OUT_DIR/data/<region>.json (a region: its walkthrough parts,
place pages, where each Pokemon and item turns up, its important trainers). A new region is one more data file and one
more line in REGIONS; the page needs no change.

Views (the page's hash, plain names only as the artifact allows): #home, #part-<region>-<n>, #place-<key>, #pokemon-<id>,
#item-<key>, #trainer-<slug>, #list-places, #list-pokemon, #list-items, #list-trainers.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build as B   # noqa: E402
import facts as F   # noqa: E402

REGIONS = [("kanto", "Kanto + Sevii Islands", "FireRed and LeafGreen, with HeartGold/SoulSilver and Yellow extras")]
LATER = ["Johto", "Orange Islands", "Hoenn", "Sinnoh", "Unova", "Orre"]
IMPORTANT = ("GYM_LEADER", "ELITE_FOUR", "CHAMPION", "RIVAL", "ROCKET_LEADER")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")


def place_route(k):
    return "place-" + slug(k)


# ---------------------------------------------------------------- links inside the written parts, as views
B.mon_link = lambda pid, name: (f'<a class="x" href="#pokemon-{F.base_id(pid)}">{B.esc(name)}</a>'
                                if 0 < F.base_id(pid) <= 1025 else B.esc(name))
B.item_link = lambda key, name: f'<a class="x" href="#item-{slug(key)}">{B.esc(name)}</a>'


def species_json():
    """Every species the game knows (1-1025): name, types, kind, size, stats, evolutions (pokemon_levels.json pairs)."""
    ms = json.load(open(os.path.join(F.A, "pokemon_movesets.json"), encoding="utf-8"))
    dex = json.load(open(os.path.join(F.A, "dex_info.json"), encoding="utf-8"))
    out = {}
    for pid in range(1, 1026):
        m = ms.get(str(pid)) or {}
        d = dex.get(str(pid)) or {}
        if not m and not d:
            continue
        out[pid] = {"n": F.mon_name(pid), "t": [t.title() for t in m.get("types", [])], "k": d.get("kind"), "h": d.get("height"),
                    "w": d.get("weight"), "s": [m.get("stats", {}).get(x) for x in ("HP", "ATTACK", "DEFENSE", "SPECIAL-ATTACK",
                                                                                      "SPECIAL-DEFENSE", "SPEED")],
                    "i": B.icon("p", f"{pid}.png") != ""}
    evo = []
    for k, how in F.EVO.get("pairs", {}).items():
        a, b = (int(x) for x in k.split(">"))
        if a in out and b in out:
            evo.append([a, b, evo_words(how)])
    return {"species": out, "evo": evo}


def evo_words(how):
    if how.get("level"):
        w = f"Lv {how['level']}"
    elif how.get("item"):
        w = F.item_name(how["item"])
    elif how.get("friendship"):
        w = "friendship"
    elif how.get("trade"):
        w = "trade"
    else:
        w = ", ".join(f"{k.replace('_', ' ')}" for k in how) or "special"
    for k in ("time", "held", "move", "location", "gender"):
        if how.get(k) and k not in ("level", "item"):
            w += f" ({k}: {str(how[k]).replace('_', ' ').lower()})"
    return w


def item_desc(key):
    """The game's own description (items.describe); a TM's move from moves.json; an evolution item's Pokemon."""
    key = str(key)
    if re.match(r"^TM\d+$", key):
        move = (F.TMS.get(key) or {}).get("move") or ""
        mv = MOVES.get(move) or {}
        power = f", power {mv['power']}" if mv.get("power") else ""
        return (f"Teaches {move.replace('-', ' ').title()} ({str(mv.get('type', '')).title()}{power}). "
                f"{mv.get('effect') or ''} It can be used again and again.").replace("  ", " ")
    try:
        from src.pokemon import items as I
        d = I.describe("POKE_BALLS" if key == "balls" else key) or ""
    except Exception:
        d = ""
    evos = [f"{F.mon_name(k.split('>')[0])} into {F.mon_name(k.split('>')[1])}" for k, how in F.EVO.get("pairs", {}).items()
            if how.get("item") == key]
    if evos:
        d = (d + " " if d else "") + "It evolves " + ", ".join(evos) + "."
    return F.fix(d).replace("Pokemon", "Pokémon")


def build_region(region, title):
    pdir, files = B.prepare(region)
    site_ids = {k: place_route(k) for k in B.PLACE_ID}
    parts, places, first_part = [], {}, {}
    for fn in files:
        n = int(re.search(r"\d+", fn).group())
        text = open(os.path.join(pdir, fn), encoding="utf-8").read()
        ptitle = re.search(r"<!--title:\s*(.*?)-->", text).group(1).strip()
        body = B.link_places(B.fill(text))
        for k, anchor in B.PLACE_ID.items():   # (a place's name in the text opens its own page)
            body = body.replace(f'href="#{anchor}"', f'href="#{site_ids[k]}"')
        body, box = B.toc(body, f"p{n}")
        box = re.sub(r'href="#([^"]+)"', r'href="#\1" data-scroll="\1"', box)
        parts.append({"n": n, "title": ptitle, "html": body, "toc": box})
        # each place's own section(s), for its place page
        chunks = re.split(r"(?=<h2[\s>])", body)
        for c in chunks:
            m = re.match(r'<h2[^>]*data-place="([^"]+)"', c)
            if m:
                k = m.group(1)
                places.setdefault(k, {"html": "", "part": n})
                places[k]["html"] += c
                first_part.setdefault(k, n)
    for k in B.FACTS:
        f = B.FACTS[k]
        if k not in places:   # (no written section: the data's own tables)
            places[k] = {"html": f"<h2>{B.esc(f['name'])}</h2>" + B.fill(f"{{{{tables:{k}}}}}{{{{trainers:{k}}}}}"), "part": None}
        exits = []
        for v in list((f.get("exits") or {}).values()) + [t.get("target_area") for t in (f.get("travel") or []) if isinstance(t, dict)]:
            if isinstance(v, str) and v in B.FACTS and v != k and v not in exits:
                exits.append(v)
        places[k].update(name=f["name"], exits=exits, level=f["level"], sevii=k in F.SEVII["STORY_PROGRESSION"])

    # where each Pokemon and item turns up, and who uses each Pokemon
    mons, items, trainers = {}, {}, {}
    for k, f in B.FACTS.items():
        w = f["wild"]
        for r in w["land"] + w["water"] + w["trees"] + [dict(r, zone=z["zone"]) for z in w["zones"] for r in z["rows"]]:
            b = F.base_id(r["id"])
            if not 0 < b <= 1025:
                continue
            mons.setdefault(b, {"wild": [], "used": []})["wild"].append(
                {"p": k, "how": r["how"] + (f" ({r['zone']})" if r.get("zone") else ""), "lv": B.lv(r), "rate": B.rate(r["rate"]),
                 "form": r["name"] if r["name"] != F.mon_name(b) else "", "after": (r.get("after") or "").title(),
                 "ours": bool(r.get("ours") or r.get("after"))})
        for t in B.all_trainers(f):
            for m in [m for tm in ((t.get("by_starter") or {}).values() or [t["team"]]) for m in tm] or t["team"]:
                b = F.base_id(m["id"])
                if 0 < b <= 1025 and str(m["id"]) not in F.PLACEHOLDER:
                    u = mons.setdefault(b, {"wild": [], "used": []})["used"]
                    e = {"p": k, "who": B.trainer_name(t), "lv": m.get("lv")}
                    if e not in u:
                        u.append(e)
            if (str(t.get("class") or "").upper() in IMPORTANT or (t.get("boss") and "Gym" not in t["where"])
                    or "Jessie" in (t.get("name") or "")) and any(m.get("lv") for m in t["team"]):
                name = B.trainer_name(t)
                tr = trainers.setdefault(slug(name), {"name": name, "cls": B.class_word(t.get("class")), "battles": []})
                tr["battles"].append({"p": k, "html": B.battle_box(f, t)})
        for (i, where, when, qty) in B.item_rows(f):
            e = items.setdefault(slug(i["item"]), {"key": i["item"], "name": i["name"], "ic": B.icon("i", i.get("sprite")),
                                                   "desc": item_desc(i["item"]), "where": []})
            e["where"].append({"p": k, "w": where + (f" ({when})" if when else "") + (qty and f" {qty}")})
    for e in mons.values():
        e["wild"].sort(key=lambda r: first_part.get(r["p"], 99))
    return {"key": region, "title": title, "parts": parts, "places": places, "mons": mons, "items": items,
            "trainers": trainers, "order": sorted(places, key=lambda k: (first_part.get(k, 99), list(B.FACTS).index(k)))}


MOVES = json.load(open(os.path.join(F.A, "moves.json"), encoding="utf-8"))


def main(out):
    os.makedirs(os.path.join(out, "data"), exist_ok=True)
    regions = []
    for key, title, src in REGIONS:
        data = build_region(key, title)
        data["src"] = src
        with open(os.path.join(out, "data", f"{key}.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        regions.append({"key": key, "title": title, "src": src, "parts": len(data["parts"]), "places": len(data["places"])})
    sp = species_json()   # (after the regions: their icons are in, and every species with an icon gets one)
    with open(os.path.join(out, "data", "species.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(sp, fh, ensure_ascii=False, separators=(",", ":"))
    css = "".join(f".{c}{{background-image:url(data:image/png;base64,{b})}}" for c, b in B.ICONS.items())
    with open(os.path.join(out, "icons.css"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(css)
    page = open(os.path.join(HERE, "site.html"), encoding="utf-8").read()
    # (the icons go in the page's own style: the viewer won't apply a style the page adds after it loads, 11-24)
    page = page.replace("/*CSS*/", B.CSS + "\n" + css).replace("/*REGIONS*/", json.dumps({"live": regions, "later": LATER}))
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page)
    sizes = {fn: os.path.getsize(os.path.join(out, fn)) // 1024 for fn in ("index.html", "icons.css")}
    sizes.update({f"data/{fn}": os.path.getsize(os.path.join(out, "data", fn)) // 1024 for fn in os.listdir(os.path.join(out, "data"))})
    print(sizes, len(B.ICONS), "icons")


if __name__ == "__main__":
    main(sys.argv[1])
