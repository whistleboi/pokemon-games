"""Where items are sold or exchanged (region/encyclopedia, 11-24), for the item pages, from the game's own tables:
  - the Poke Mart counter that grows with a region's badges (src/pokemon/items.py STANDARD_MART + SPECIALTY_BALLS;
    the Orange Islands' Marts keep their own shelves instead);
  - each Game Corner's prize counter (src/states/game_corner.py PRIZES), in coins;
  - each BP exchange counter (src/world/battle_points.py SHOPS), where a person or menu option has "action": "BP_SHOP";
plus the type chart page, from the area data's TYPE_CHART (the one src/pokemon/mechanics.TypeAdvantage reads)."""
import json
import os
import re
import sys

import facts as F

MART_REGIONS = ("KANTO", "JOHTO", "HOENN", "SINNOH", "UNOVA", "ORRE")


def _src(*parts):
    return open(os.path.join(F.ROOT, "src", *parts), encoding="utf-8").read()


def mart():
    """[(badges, item)] on the shared counter."""
    src = _src("pokemon", "items.py")
    std = eval(re.search(r"STANDARD_MART = (\[.*?\n\])", src, re.S).group(1))
    spc = eval(re.search(r"SPECIALTY_BALLS = (\[.*?\])\n", src, re.S).group(1))
    return [(n, i) for n, its in std + spc for i in its]


def prizes():
    src = _src("states", "game_corner.py")
    return eval(re.search(r"^PRIZES = (\{.*?\n\})", src, re.S | re.M).group(1))


def bp_shops():
    """{shop: (name, [(item key, BP)])}, with the game's own stock() rules (TMs by move; derived lists)."""
    if F.ROOT not in sys.path:
        sys.path.insert(0, F.ROOT)
    from src.world import battle_points as bp
    out = {}
    for key, (name, lst) in bp.SHOPS.items():
        if lst is None:   # (Platinum's corners: derived in battle_points from HGSS's)
            try:
                lst = bp._list(key) if hasattr(bp, "_list") else None
            except Exception:
                lst = None
        if lst is None:
            base = {"plat_items": "hgss_items", "plat_tms": "hgss_tms"}.get(key)
            lst = [x for x in (bp.SHOPS.get(base, (None, []))[1] or []) if x[0] != "TM:U-TURN"]
        items = []
        by_move = {v.get("move"): tm for tm, v in F.TMS.items()}
        for what, cost in lst:
            if what.startswith("TM:"):
                what = by_move.get(what[3:])
                if not what:
                    continue
            items.append((what, cost))
        out[key] = (name, items)
    return out


def bp_places():
    """{shop: [place keys]} from the maps' people and the area data's menus."""
    out = {}

    def walk(o, k):
        if isinstance(o, dict):
            if o.get("action") == "BP_SHOP" and o.get("shop"):
                out.setdefault(o["shop"], [])
                if k not in out[o["shop"]]:
                    out[o["shop"]].append(k)
            for v in o.values():
                walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, k)
    for k, v in F.MAPS.items():
        walk(v, k)
    for k, v in F.PLACES.items():
        walk(v, k)
    return out


def entries(region_keys):
    """[(item key, place key or None, words, link html or None)] for one site region (its F.region_of names)."""
    out = []
    regions = set(region_keys)
    if regions & set(MART_REGIONS):
        for n, item in mart():
            out.append((item, None, f"Poké Mart counter, from {n} badge{'s' if n != 1 else ''}" if n else "Poké Mart counter, from the start",
                        '<a href="#mechanic-poke-marts">Every Poké Mart</a>'))
    for place, rows in prizes().items():
        if F.region_of(place) in regions:
            for kind, what, cost in rows:
                if kind == "ITEM":
                    out.append((what, place, f"Game Corner prize: {cost:,} coins", None))
    places = bp_places()
    for shop, (name, items) in bp_shops().items():
        for place in places.get(shop, []):
            if F.region_of(place) in regions:
                for item, cost in items:
                    out.append((item, place, f"{name}: {cost} BP", None))
    return out


def type_chart_page():
    chart = F.DATA.get("TYPE_CHART") or {}
    types = list(chart)
    for t in chart.values():
        for d in t:
            if d not in types:
                types.append(d)
    ab = lambda t: t[:3].title()
    sym = {2: "2", 0.5: "½", 0: "0"}
    rows = []
    for a in types:
        cells = "".join(f'<td class="tc tc{str(chart.get(a, {}).get(d, 1)).replace(".", "")}">'
                        f'{sym.get(chart.get(a, {}).get(d, 1), "")}</td>' for d in types)
        rows.append(f"<tr><th>{a.title()}</th>{cells}</tr>")
    head = "".join(f'<th title="{d.title()}">{ab(d)}</th>' for d in types)
    table = (f'<div class="frame tchart"><table><caption>Attacking type (rows) against defending type (columns)</caption>'
             f'<thead><tr><th></th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
    strong = []
    for a in types:
        s = [d.title() for d in types if chart.get(a, {}).get(d, 1) == 2]
        w = [d.title() for d in types if chart.get(a, {}).get(d, 1) == 0.5]
        z = [d.title() for d in types if chart.get(a, {}).get(d, 1) == 0]
        strong.append(f"<tr><td><b>{a.title()}</b></td><td>{', '.join(s) or '—'}</td><td>{', '.join(w) or '—'}</td>"
                      f"<td>{', '.join(z) or '—'}</td></tr>")
    lst = ('<div class="frame"><table><caption>Each attacking type at a glance</caption><thead><tr><th>Move type</th>'
           '<th>Hits hard (×2)</th><th>Not very effective (×½)</th><th>No effect</th></tr></thead>'
           f'<tbody>{"".join(strong)}</tbody></table></div>')
    html = ("<p>Every move has a type, and so does every Pokémon (one or two). A move hits twice as hard against a type "
            "it's strong against, half as hard against one it's weak against, and not at all against one it can't touch. "
            "Against a Pokémon with two types, both count: strong against both is four times the damage. This is the "
            "game's own chart, the one every battle uses.</p>"
            "<h2>The chart</h2><p class=\"small\">2 = twice the damage, ½ = half, 0 = no effect, empty = normal.</p>"
            + table + "<h2>Type by type</h2>" + lst +
            '<p>See <a href="#mechanic-math-battles">Math battles</a> for how a move lands, and each '
            '<a href="#list-moves">move</a>\'s page for its type.</p>')
    css = ('<style>.tchart table{font-size:12px} .tchart td.tc{text-align:center;padding:2px 4px} '
           '.tchart td.tc2{background:#2e7d3240} .tchart td.tc05{background:#c6282840} .tchart td.tc0{background:#00000060}</style>')
    return {"title": "Type chart", "group": "Start here", "blurb": "What each type of move is strong and weak against.",
            "html": css + html, "toc": ""}
