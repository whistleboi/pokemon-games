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

REGIONS = [("kanto", "Kanto + Sevii Islands", "FireRed and LeafGreen, with HeartGold/SoulSilver and Yellow extras"),
           ("johto", "Johto", "HeartGold and SoulSilver, on SoulSilver's maps, with Crystal extras"),
           ("orange", "Orange Islands", "the anime and the fan game Pokémon Orange Islands"),
           ("hoenn", "Hoenn", "Omega Ruby and Alpha Sapphire's story on Emerald's maps, with Ruby, Sapphire and Emerald extras"),
           ("sinnoh", "Sinnoh", "Diamond, Pearl and Platinum on Platinum's maps, with Brilliant Diamond and Shining Pearl's story"),
           ("unova", "Unova", "Black 2 and White 2 on their own maps, with Black and White's places")]
# ("orre", "Orre", "Colosseum and XD: Gale of Darkness as one journey, on the Orre fan game's maps"): once its parts are written
LATER = ["Orre"]
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


EDGES = {"^": "N", "v": "S", "<": "W", ">": "E"}   # (a map's edge exits; town_maps "exits")
OTHER = {"n": "Entrance", "w": "By water", "u": "Stairs", "d": "Stairs"}


def connections(k, f):
    """The places next door: by the map's edges (north / south / west / east, the map and its floors), then the other
    ways (a cave mouth or a door "n", the water "w", stairs, a building's letter), then the area's travel options
    (ferries, Fly spots...)."""
    m = F.MAPS.get(k) or {}
    out = {"N": [], "S": [], "W": [], "E": [], "other": []}
    seen = {k}
    for ex in [m.get("exits") or {}] + [fl.get("exits") or {} for fl in m.get("floors") or [] if isinstance(fl, dict)]:
        for sym, v in ex.items():
            if not isinstance(v, str) or v not in B.FACTS or v in seen:
                continue
            seen.add(v)
            if sym in EDGES:
                out[EDGES[sym]].append(v)
            else:
                out["other"].append([OTHER.get(sym, "Door"), v])
    for t in f.get("travel") or []:
        v = t.get("target_area") if isinstance(t, dict) else None
        if isinstance(v, str) and v in B.FACTS and v not in seen:
            seen.add(v)
            out["other"].append(["Travel", v])
    return out


# The region boxes (like Bulbapedia's): badges, then Settlements / Routes / Landmarks, then the regions you can reach.
NAV = {"kanto": [("Kanto", "KANTO", "kanto", "Settlements", ["Sevii Islands", "Johto", "Orange Islands"]),
                 ("Sevii Islands", "SEVII", None, "Islands", ["Kanto"])],
       "johto": [("Johto", "JOHTO", "johto", "Settlements", ["Kanto", "Orange Islands"])],
       "orange": [("Orange Islands", "ORANGE", "orange", "Islands", ["Kanto", "Johto"])],
       "hoenn": [("Hoenn", "HOENN", "hoenn", "Settlements", [])],
       "sinnoh": [("Sinnoh", "SINNOH", list(range(25, 33)), "Settlements", [])],
       "unova": [("Unova", "UNOVA", list(range(33, 41)), "Settlements", [])],
       "orre": [("Orre", "ORRE", None, "Settlements", [])]}   # (Sinnoh's badges: REGION_START badge_images


def navboxes(region, places, first_part):
    out = []
    for title, reg, badges, towns_word, access in NAV.get(region, []):
        keys = [k for k in F.region_keys(reg) if k in places]
        keys.sort(key=lambda k: (first_part.get(k, 99), F.region_keys(reg).index(k)))
        towns, routes, marks = [], [], []
        for k in keys:
            m = re.search(r"ROUTE_(\d+)(_\w+)?$", k)
            if m and not m.group(2):
                routes.append([int(m.group(1)), k])
            elif m:
                continue   # (Route 10's south half: Route 10's own page covers it in the list)
            elif (F.PLACES.get(k) or {}).get("area_type") == "town" and (reg != "KANTO" or re.search(r"(Town|City|Island|Plateau)$", places[k]["name"])):
                towns.append(k)
            else:
                marks.append(k)
        seen = set()   # (one link per name: Fortree's treetop half, the Trick House's six puzzle rooms)
        towns = [k for k in towns if not (places[k]["name"] in seen or seen.add(places[k]["name"]))]
        marks = [k for k in marks if not (places[k]["name"] in seen or seen.add(places[k]["name"]))]
        groups = [[towns_word, [[places[k]["name"], k] for k in towns]],
                  ["Routes", [[str(n), k] for n, k in sorted(routes)]],
                  ["Landmarks", [[places[k]["name"], k] for k in marks]]]
        out.append({"title": title, "slug": slug(title), "keys": keys,
                    "badges": [i for i in (B.icon("b", f"{n}.png" if isinstance(badges, list) else f"{badges}_{n}.png")
                                           for n in (badges if isinstance(badges, list) else range(1, 9))) if i] if badges else [],
                    "groups": [g for g in groups if g[1]], "access": access})
    return out


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
        places[k].update(name=f["name"], conn=connections(k, f), level=f["level"], sevii=k in F.SEVII["STORY_PROGRESSION"])

    # the buildings of each place (buildings.py): a page each, with a written description where buildings.html has one
    import buildings as BL
    desc = BL.descriptions(region)
    blds = {}
    for k, f in B.FACTS.items():
        lst = BL.buildings(k, f, slug, lambda room, name: pictures_of(room, name, ROOMDATA))
        for b in lst:
            d = desc.get(b["id"]) or {}
            if d.get("title"):
                b["name"] = d["title"]
            body = (B.link_places(d["html"]) if d.get("html") else "") + b["html"]
            for kk, anchor in B.PLACE_ID.items():
                body = body.replace(f'href="#{anchor}"', f'href="#{site_ids[kk]}"')
            body = body.replace('<img data-map="rooms/', f'<img data-region="{region}-rooms" data-map="rooms/')
            blds[b["id"]] = {"name": b["name"], "p": k, "kind": b["kind"], "html": body, "written": bool(d.get("html"))}
        places[k]["buildings"] = [[b["id"], blds[b["id"]]["name"]] for b in lst if blds[b["id"]]["html"]]
    unknown = set(desc) - set(blds)
    if unknown:
        print("buildings.html: no such building:", sorted(unknown))

    # where each Pokemon and item turns up, and who uses each Pokemon
    mons, items, trainers = {}, {}, {}
    for k, f in B.FACTS.items():
        w = f["wild"]
        for r in w["land"] + w["water"] + w["trees"] + [dict(r, zone=z["zone"]) for z in w["zones"] for r in z["rows"]]:
            b = F.base_id(r["id"])
            if not 0 < b <= 1025:
                continue
            mons.setdefault(b, {"wild": [], "used": []})["wild"].append(
                {"p": k, "how": r["how"] + (f" ({r['zone']})" if r.get("zone") else ""), "lv": B.lv(r), "rate": (" / ".join(f"{t[0]} {B.rate(v)}" for t, v in r["times"].items()) if r.get("times") else B.rate(r["rate"])),
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
    return {"key": region, "title": title, "parts": parts, "places": places, "mons": mons, "items": items, "buildings": blds,
            "nav": navboxes(region, places, first_part),
            "trainers": trainers, "order": sorted(places, key=lambda k: (first_part.get(k, 99), list(B.FACTS).index(k)))}


MAPDATA = {}   # (the map pictures, as data: URIs in data/<region>-maps.json: loaded when a place page first opens)


def map_pictures(out, key):
    """The area's map as the game draws it: its ground picture with the top layer (trees, roofs) over it, one image per
    floor for caves and buildings (town_maps "_picture" + "overheads", 16-pixel tiles). Returns [{"src", "label"}]."""
    return pictures_of(F.MAPS.get(key) or {}, f"maps/{slug(key)}", MAPDATA)


ROOMDATA = {}   # (the building pages' room pictures: data/<region>-rooms-maps.json)


def pictures_of(m, prefix, store):
    from PIL import Image
    tiles = os.path.join(F.A, "tiles")
    names = m.get("floor_names") or []
    layers = [(m, "")] + [(fl, F.fix(names[i]) if i < len(names) and names[i] else f"Floor {i + 1}")
                          for i, fl in enumerate(m.get("floors") or []) if isinstance(fl, dict)]
    pics = []
    for i, (lay, label) in enumerate(layers):
        pic = ((lay.get("roofs") or {}).get("_picture") or {})
        if not pic.get("f") or not os.path.exists(os.path.join(tiles, pic["f"])):
            continue
        im = Image.open(os.path.join(tiles, pic["f"])).convert("RGBA")
        for o in lay.get("overheads") or []:
            if isinstance(o, dict) and o.get("kind") == "picture" and os.path.exists(os.path.join(tiles, o.get("f", ""))):
                top = Image.open(os.path.join(tiles, o["f"])).convert("RGBA")
                x, y = (int(v) * int(o.get("px") or pic.get("px") or 16) for v in (o.get("at") or [0, 0]))
                im.alpha_composite(top, (x, y))
        px = int(pic.get("px") or 16)
        if px != 16:   # (SoulSilver's pictures are 32 pixels a tile: drawn at FireRed's 16, like the rest)
            im = im.resize((im.width * 16 // px, im.height * 16 // px), Image.NEAREST)
        name = f"{prefix}{'-' + str(i) if i else ''}.png"
        import base64
        from io import BytesIO
        buf = BytesIO()
        im.convert("RGB").quantize(256).convert("RGB").save(buf, "WEBP", lossless=True, method=6)   # (lossless WebP of the 256-colour picture: smallest for pixel art)
        store[name] = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
        pics.append({"src": name, "label": label, "w": im.width, "h": im.height})
    return pics


MOVES = json.load(open(os.path.join(F.A, "moves.json"), encoding="utf-8"))


def mechanics(folder="mechanics"):
    """The mechanics pages: dev/encyclopedia/mechanics/<slug>.html, each with <!--title: -->, <!--group: --> and
    <!--blurb: --> (a line for the list), then its HTML. A building's kind (buildings.KINDS) opens the page of that slug."""
    out = {}
    d = os.path.join(HERE, folder)
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".html"):
            continue
        text = open(os.path.join(d, fn), encoding="utf-8").read()
        meta = {k: (re.search(rf"<!--{k}:\s*(.*?)-->", text) or [None, ""])[1].strip() for k in ("title", "group", "blurb")}
        body = re.sub(r"<!--\w+:.*?-->\s*", "", text)
        body, box = B.toc(body, "m-" + fn[:-5])
        box = re.sub(r'href="#([^"]+)"', r'href="#\1" data-scroll="\1"', box)
        out[fn[:-5]] = {"title": meta["title"] or fn[:-5], "group": meta["group"] or "Other", "blurb": meta["blurb"],
                        "html": body, "toc": box}
    return dict(sorted(out.items(), key=lambda kv: (kv[1]["group"], kv[1]["title"])))


def main(out):
    os.makedirs(os.path.join(out, "data"), exist_ok=True)
    regions = []
    for key, title, src in REGIONS:
        data = build_region(key, title)
        for k, p in data["places"].items():
            p["maps"] = map_pictures(out, k)
        with open(os.path.join(out, "data", f"{key}-maps.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(MAPDATA, fh, separators=(",", ":"))
        MAPDATA.clear()
        with open(os.path.join(out, "data", f"{key}-rooms-maps.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(ROOMDATA, fh, separators=(",", ":"))
        ROOMDATA.clear()
        data["src"] = src
        with open(os.path.join(out, "data", f"{key}.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        regions.append({"key": key, "title": title, "src": src, "parts": len(data["parts"]), "places": len(data["places"])})
    with open(os.path.join(out, "data", "mechanics.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(mechanics(), fh, ensure_ascii=False, separators=(",", ":"))
    import journal as J   # (the Journal pages, from quest_book.json / the missions / quest_feats.json every build)
    with open(os.path.join(out, "data", "journal.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(J.pages(HERE, slug), fh, ensure_ascii=False, separators=(",", ":"))
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
