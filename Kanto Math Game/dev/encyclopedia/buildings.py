"""The encyclopedia's building pages (region/encyclopedia, 11-24): every building of a walked place, from its rooms in
town_maps.json (one building = the rooms that share a key: "dept", "dept_2" ... "dept_roof"), each floor with its picture,
the people in it and what they do, its items and its trainers. A written description comes first where the region's
buildings.html has one: <section data-building="ID" [data-title="Name"]>...</section>.

Used by build_site.py; facts come from facts.py / build.py like the rest."""
import os
import re

import build as B
import facts as F

HERE = os.path.dirname(os.path.abspath(__file__))
FLOOR_WORDS = r"\s*(?:\d+F|B\d+F|Roof|Rooftop|Lift|Upstairs|Downstairs|Basement|Lobby)$"
KINDS = [("pokemon-centers", r"^center|pokecenter|pokemon_center"), ("poke-marts", r"^mart|pokemart"),
         ("gyms", r"^gym(?:$|_?\d|_hall|_lobby)"), ("department-stores", r"^dept"), ("game-corners", r"game_corner|^casino|^prize"),
         ("day-care", r"daycare|day_care"), ("contests", r"contest"), ("safari-game", r"safari")]
ROLE_ACTIONS = {"SHOP": "Runs the shop counter", "HEAL": "Heals your team", "BP_SHOP": "Trades items for Battle Points",
                "LEAGUE": "Takes you on to the League", "GYM": "Takes you into the Gym"}


def base_of(rk):
    b = rk
    for _ in range(3):
        b = re.sub(r"_(?:\d{1,2}f?|b\d+f?|roof|top)$", "", b)   # (not "_0501": Platinum's building number)
    return b


def kind_of(base, title, people=()):
    """Its kind, for the link to a mechanics page: by its key or name; a Center must have its nurse (HEAL) and a Mart its
    counter (SHOP), else it's only a room that kept the key (Resort Area's "center_0101", Veilstone's Dept. Store 1F)."""
    acts = {str(p.get("action") or "").upper() for p in people if isinstance(p, dict)}
    for kind, pat in KINDS:
        if re.search(pat, base) or (kind == "gyms" and re.search(r"\bGym$", title or "")):
            if kind == "pokemon-centers" and "HEAL" not in acts:
                continue
            if kind == "poke-marts" and "SHOP" not in acts:
                continue
            return kind
    return None


def _items_words(d):
    out = []
    for k, v in (d or {}).items():
        mm = re.match(r"^(?:POKEMON_?)?(\d+)$", str(k))
        nm = F.mon_name(mm.group(1)) if mm else F.item_name(k)
        out.append(f"{nm} ×{v}" if isinstance(v, int) and v > 1 else nm)
    return ", ".join(out)


def does(p):
    """What a person does, in a few words of our own (never their lines); one who changes with the story ("alternatives")
    does everything any of their versions does."""
    if p.get("alternatives"):
        seen = []
        for a in p["alternatives"]:
            for w in does(a).split(" · "):
                if w != "Chats" and w not in seen:
                    seen.append(w)
        return " · ".join(seen) or "Chats"
    ev = p.get("event") if isinstance(p.get("event"), dict) else {}
    out = []
    if p.get("action") in ROLE_ACTIONS:
        out.append(ROLE_ACTIONS[p["action"]])
    if ev.get("heal"):
        out.append("Heals your team")
    if ev.get("battle"):
        out.append("Battles you")
    if ev.get("trade"):
        out.append("Trades Pokémon")
    if ev.get("gift_item"):
        words = _items_words(ev["gift_item"])
        out.append(f"Sells {words} for ${ev['pay']}" if ev.get("pay") else f"Gives {words}")
    if ev.get("gift_pokemon"):
        gp = ev["gift_pokemon"]
        pid = gp if isinstance(gp, (int, str)) else (gp.get("id") if isinstance(gp, dict) else None)
        out.append(f"Gives you {F.mon_name(pid)}" if pid and str(pid).isdigit() else "Gives you a Pokémon")
    if ev.get("stock"):
        st = ev["stock"]
        names = [F.item_name(x if isinstance(x, str) else (x.get("item") or "")) for x in (st if isinstance(st, list) else st.keys() if isinstance(st, dict) else [])]
        out.append("Sells " + ", ".join(n for n in names if n) if names else "Runs a shop")
    if ev.get("tutor"):
        out.append("Teaches a move (sells its TM)")
    if ev.get("name_rater"):
        out.append("Rates and changes nicknames")
    if ev.get("daily") or ev.get("daily_gift"):
        out.append("(once a day)")
    if ev.get("world") and not out:
        out.append("Part of a game mechanic")
    return " · ".join(out) or "Chats"


def _is_pickup(p):
    t = str(p.get("text") or "")
    return t.isupper() and not (p.get("event") or {}) or (t.isupper() and isinstance(p.get("event"), dict) and p["event"].get("gift_item") and t.replace(" ", "_") in p["event"]["gift_item"])


def people_html(people):
    rows = []
    for p in people or []:
        if not isinstance(p, dict) or p.get("_unresolved") or _is_pickup(p):
            continue
        who = F.fix(p.get("text") or "").strip()
        if not who:
            continue
        cond = B.human_cond(p.get("condition"))
        rows.append(f"<tr><td>{B.esc(who)}</td><td>{B.esc(does(p))}" + (f' <span class="small">({B.esc(cond)})</span>' if cond else "")
                    + "</td></tr>")
    if not rows:
        return ""
    return ('<div class="frame"><table><caption>People</caption><thead><tr><th>Who</th><th>What they do</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def descriptions(region):
    p = os.path.join(HERE, region, "buildings.html")
    if not os.path.exists(p):
        return {}
    text = open(p, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r'<section data-building="([^"]+)"(?: data-title="([^"]*)")?>(.*?)</section>', text, re.S):
        out[m.group(1)] = {"title": m.group(2), "html": m.group(3).strip()}
    return out


def buildings(k, f, slug, pictures):
    """[{id, name, kind, rooms, html}] for one place. pictures(room_dict, name_prefix) -> [{"src", "label", "w", "h"}]."""
    rooms = (F.MAPS.get(k) or {}).get("rooms") or {}
    groups = {}   # (one building: rooms with the same key stem and name, on different floors - "Dept. Store 2F";
    order = []    #  two rooms with the very same title are two buildings: "House" / "House", the S.S. Anne's "Cabin"s)
    last = {}     # (base key -> its latest group: where a floor of it goes)
    for rk, rv in rooms.items():
        if not isinstance(rv, dict):
            continue
        base = base_of(rk)
        title = F.fix(rv.get("title") or "")
        stem = re.sub(FLOOR_WORDS, "", title).strip()
        floorish = bool(re.search(r"_(?:\d+f|b\d+f?|roof|top)$", rk))   # ("_2f", "_b1", "_roof": always a floor of it)
        g = groups.get(last.get(base)) if base != rk else None
        if g is not None and (floorish or not title or not stem
                              or (stem == (re.sub(FLOOR_WORDS, "", F.fix(g[0][1].get("title") or "")).strip() or stem)
                                  and all(F.fix(x.get("title") or "") != title for _k2, x in g))):
            g.append((rk, rv))   # (another floor of the same building)
            continue
        key = (base, stem) if (base, stem) not in groups else (rk, stem)
        groups[key] = [(rk, rv)]
        order.append(key)
        last.setdefault(base, key)
    names = {}
    out = []
    for (base, _stem) in order:
        rs = groups[(base, _stem)]
        title = F.fix(next((x.get("title") for _k2, x in rs   # (the first floor with a name of its own, not "Upstairs")
                            if x.get("title") and re.sub(FLOOR_WORDS, "", F.fix(x["title"])).strip()), None)
                      or {"center": "Pokémon Center", "mart": "Poké Mart", "gym": "Gym"}.get(base_of(base))
                      or re.sub(r"\s+\d+$", "", base_of(base).replace("_", " ")).title())
        name = re.sub(FLOOR_WORDS, "", title).strip() or title
        names.setdefault(name, []).append(base)
        out.append({"base": base, "name": name, "rooms": rs})
    used = set()
    for b in out:
        if b["base"] in used:   # (one key stem, different buildings: Jubilife's "house_0101" TV and "house_0201" school)
            b["base"] = b["rooms"][0][0]
        used.add(b["base"])
    for b in out:
        if len(names[b["name"]]) > 1:   # (two "House"s in one town: told apart by their key)
            tag = re.sub(r"^(house|room|bldg)_?", "", b["base"]).replace("_", " ").strip().upper() or str(names[b["name"]].index(b["base"]) + 1)
            b["name"] = f"{b['name']} ({tag})"
        b["id"] = f"{slug(k)}--{slug(b['base'])}"
        b["kind"] = kind_of(b["base"], b["name"], [p for _rk, rv in b["rooms"] for p in ((f.get("rooms") or {}).get(_rk, {}).get("people") or [])])
    saved = set(B.BOXED)
    B.BOXED.clear()   # (on a building page every trainer shows, boxed in the walkthrough or not)
    try:
        for b in out:
            html = []
            if b["kind"] == "gyms":
                for t in B.all_trainers(f):
                    if t["where"] == "Gym Leader" or t.get("class") == "GYM_LEADER":
                        html.append(B.battle_box(f, t))
            for rk, rv in b["rooms"]:
                rt = F.fix(rv.get("title") or rk)
                sec = []
                for pic in pictures(rv, f"rooms/{b['id']}-{slug(rk)}"):
                    sec.append(f'<div class="mapfull"><img data-map="{pic["src"]}" alt="{B.esc(rt)}" width="{pic["w"]}" height="{pic["h"]}" loading="lazy"></div>')
                ppl = people_html((f.get("rooms") or {}).get(rk, {}).get("people") or rv.get("people"))
                mine = lambda x: x.get("rk") == rk if x.get("rk") else x["where"] == rt   # (this room's own, by its key)
                fr = dict(f, items=[i for i in f["items"] if mine(i)], trainers=[t for t in f["trainers"] if mine(t)],
                          battles=[t for t in f["battles"] if mine(t)])
                its = B.items_html(fr, rt) if fr["items"] else ""
                trs = B.trainers_html(fr, rt) if any(t["where"] == rt for t in B.all_trainers(fr)) else ""
                boxes = "".join(B.battle_box(f, t) for t in B.all_trainers(fr)
                                if t["where"] == rt and t.get("class") in ("RIVAL", "ROCKET_LEADER", "ELITE_FOUR", "CHAMPION"))
                grid = "".join(x for x in (ppl, its, trs) if x)
                if not (sec or grid or boxes):
                    continue
                html.append((f"<h3>{B.esc(rt)}</h3>" if len(b["rooms"]) > 1 or rt != b["name"] else "")
                            + "".join(sec) + (f'<div class="grid">{grid}</div>' if grid else "") + boxes)
            b["html"] = "".join(html)
    finally:
        B.BOXED.clear()
        B.BOXED.update(saved)
    return out
