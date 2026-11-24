"""The encyclopedia's Journal pages (region/encyclopedia, 11-24; asked by the Journal branch for Jordan): built from the
game's own data every time, since the Journal's wording and rewards keep changing (region/journal):
  assets/quest_book.json   STORY: arcs of chapters, each over a mission (its page text is the game's own Journal text)
  JOURNAL_MISSIONS         the missions: start conditions, targets, steps, done flag / badge, rewards (SIDE ones too)
  assets/quest_feats.json  FEATS: tiered goals and their rewards
"How to complete" sits under a fold (the book itself hides future chapters), with the walkthrough part that plays it."""
import json
import os
import re

import build as B
import facts as F

QB = F.load("quest_book.json")
FEATS = F.load("quest_feats.json")
TITLES = {"KANTO": "Kanto + Sevii Islands", "JOHTO": "Johto", "ORANGE": "Orange Islands", "HOENN": "Hoenn",
          "SINNOH": "Sinnoh", "UNOVA": "Unova"}
ORD = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth"]


def words(t):
    t = F.fix(str(t or ""))
    t = re.sub(r"([Yy]our rival),? \{rival_name\}", lambda q: q.group(1), t)
    t = t.replace("{rival_name}", "your rival").replace("{player_name}", "you").replace("{rival_character}", "your rival")
    t = re.sub(r"(^|[.!?]\s+)your rival", lambda q: q.group(1) + "Your rival", t)   # (a sentence's first word)
    return t


def mission(mid):
    return next((m for m in F.MISSIONS if m.get("id") == mid), None)


def region_of_mission(m):
    c = m.get("condition") or {}
    r = c.get("required_region") or m.get("region")
    return str(r).upper() if r else "KANTO"   # (Kanto's own list, GAME_CONFIG: no region; the Sevii Islands' too)


def place_link(k, slug):
    if isinstance(k, (list, tuple)):
        return " or ".join(place_link(x, slug) for x in k if isinstance(x, str))
    if not isinstance(k, str):
        return ""
    nm = (F.PLACES.get(k) or {}).get("route_name") or k.replace("_", " ").title()
    return f'<a href="#place-{slug(k)}">{B.esc(F.fix(nm))}</a>' if k in F.MAPS else B.esc(F.fix(nm))


def cond_words(c, slug):
    """A mission's start condition in words: only the kinds we can say for sure (badges, places, items)."""
    out = []
    if not isinstance(c, dict):
        return out
    for key in ("badges_min", "region_badges_min"):
        if c.get(key):
            n = int(c[key])
            out.append(f"with {n} badge{'s' if n != 1 else ''}")
    for key in ("badges_less", "region_badges_less"):
        if c.get(key):
            n = int(c[key])
            out.append(f"before your {ORD[n - 1] if 0 < n <= 8 else str(n) + 'th'} badge" if n else "")
    if c.get("visited"):
        out.append("once you've reached " + place_link(c["visited"], slug))
    if c.get("visited_not"):
        out.append("until you reach " + place_link(c["visited_not"], slug))
    if c.get("item"):
        out.append(f"with the {B.esc(F.item_name(c['item']))}")
    if c.get("item_not"):
        out.append(f"until you have the {B.esc(F.item_name(c['item_not']))}")
    if c.get("badge"):
        out.append(f"with the {B.esc(str(c['badge']).replace('_', ' ').title())} Badge")
    return [o for o in out if o]


def done_words(d, slug):
    if isinstance(d, dict) and "any" in d:
        parts = [done_words(x, slug) for x in d["any"]]
        return " or ".join(p for p in parts if p)
    if isinstance(d, list):
        return " and ".join(p for p in (done_words(x, slug) for x in d) if p)
    d = str(d or "")
    m = re.match(r"visited_(\w+)$", d)
    if m:
        return "reach " + place_link(m.group(1), slug)
    m = re.match(r"beat:(\w+):\d+$", d)
    if m:
        return "win a battle in " + place_link(m.group(1), slug)
    if d == "beat_champion" or d.startswith("beat_") and "champion" in d:
        return "become Champion"
    return ""


def reward_words(r):
    if not r:
        return ""
    if isinstance(r, str):
        return F.fix(r)
    if isinstance(r, dict):
        out = []
        if r.get("money"):
            out.append(f"${r['money']:,}")
        tms = r.get("tm")
        for t in ([tms] if isinstance(tms, str) else tms or []):
            out.append(F.item_name(t))
        for k, v in (r.get("items") or {}).items():
            out.append(f"{F.item_name(k)} ×{v}" if v > 1 else F.item_name(k))
        return ", ".join(out)
    return ""


def how_to(m, slug, parts):
    rows = []
    if m.get("desc") or m.get("description"):
        rows.append(f"<p>{B.esc(words(m.get('desc') or m.get('description')))}</p>")
    facts = []
    tg = m.get("target") or (m.get("targets") or [None])[0]
    if tg:
        facts.append("<b>Where:</b> " + place_link(tg, slug))
    cw = cond_words(m.get("condition"), slug)
    if cw:
        facts.append("<b>Opens:</b> " + ", ".join(cw))
    if m.get("completed_badge"):
        facts.append(f"<b>Done:</b> win the {B.esc(str(m['completed_badge']).replace('_', ' ').title())}"
                     + ("" if str(m["completed_badge"]).lower().endswith("badge") else " Badge"))
    steps = [s.get("label") for s in m.get("steps") or [] if isinstance(s, dict) and s.get("label")]
    if steps:
        facts.append("<b>Way-points:</b> " + " → ".join(B.esc(words(s)) for s in steps))
    rw = reward_words(m.get("reward"))
    if rw:
        facts.append(f"<b>Reward:</b> {B.esc(rw)}")
    pt = parts.get(m["id"])
    if pt:
        facts.append(f'<b>In the walkthrough:</b> <a href="#part-{pt[0]}-{pt[1]}">Part {pt[1]}</a>')
    if facts:
        rows.append('<p class="small">' + "<br>".join(facts) + "</p>")
    return "".join(rows)


def region_page(region, slug, parts):
    """The region's Journal: its story arcs, its side missions, its feats."""
    out = []
    arcs = QB.get(region) or []
    in_book = set()
    if arcs:
        out.append('<h2 id="story">Story</h2><p>The STORY tab, arc by arc. Each chapter shows the Journal\'s own page for it; '
                   'open "How to complete" for where to go and what to do.</p>')
        for a in arcs:
            out.append(f"<h3>{B.esc(words(a.get('title')))}</h3><ol class=\"chapters\">")
            for ch in a.get("chapters") or []:
                m = mission(ch.get("mission")) or {"id": ch.get("mission")}
                in_book.add(m["id"])
                extra = done_words(ch.get("done"), slug) if ch.get("done") else ""
                inner = how_to(m, slug, parts) + (f'<p class="small"><b>This chapter ends when you</b> {extra}.</p>' if extra else "")
                out.append(f"<li><b>{B.esc(words(ch.get('title')))}</b><br><q>{B.esc(words(ch.get('say')))}</q>"
                           + (f"<details class=\"howto\"><summary>How to complete</summary>{inner}</details>" if inner else "") + "</li>")
            out.append("</ol>")
    mains = [m for m in F.MISSIONS if m.get("type") == "MAIN" and region_of_mission(m) == region and m["id"] not in in_book]
    if mains and not arcs:
        out.append('<h2 id="story">Story</h2><ol class="chapters">' + "".join(
            f"<li><b>{B.esc(words(m.get('title') or m.get('text')))}</b><details class=\"howto\"><summary>How to complete</summary>"
            f"{how_to(m, slug, parts)}</details></li>" for m in mains) + "</ol>")
    sides = [m for m in F.MISSIONS if m.get("type") == "SIDE" and region_of_mission(m) == region]
    if sides:
        out.append('<h2 id="side">Side missions</h2><p>The SIDE tab: errands you don\'t need for the League.</p><ul class="sides">')
        for m in sides:
            out.append(f"<li><b>{B.esc(words(m.get('title') or m.get('text')))}</b>"
                       f"<details class=\"howto\"><summary>How to complete</summary>{how_to(m, slug, parts)}</details></li>")
        out.append("</ul>")
    feats = FEATS.get(region) or []
    if feats:
        out.append('<h2 id="feats">Feats</h2><p>The FEATS tab: goals with tiers. Reach a tier\'s goal for its reward.</p>')
        for ft in feats:
            rows = "".join(f"<tr><td>{B.esc('All' if str(g) == 'all' else str(g))}</td><td>{B.esc(reward_words(r))}</td></tr>"
                           for g, r, *_ in ft.get("tiers") or [])
            out.append(f'<div class="frame"><table><caption>{B.esc(words(ft.get("name")))}</caption>'
                       f'<thead><tr><th>Goal</th><th>Reward</th></tr></thead><tbody>{rows}</tbody></table>'
                       f'<p class="small">{B.esc(words(ft.get("desc")))}</p></div>')
    return "".join(out)


def mission_parts(here):
    """{mission id: (region key, part n)}: the walkthrough part whose text carries the mission's Journal box."""
    out = {}
    for reg in ("kanto", "johto", "orange", "hoenn", "sinnoh", "unova"):
        d = os.path.join(here, reg)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            m = re.match(r"part(\d+)\.html$", fn)
            if m:
                for mid in re.findall(r"\{\{journal:([\w]+)\}\}", open(os.path.join(d, fn), encoding="utf-8").read()):
                    out.setdefault(mid, (reg, int(m.group(1))))
    return out


def pages(here, slug):
    parts = mission_parts(here)
    out = {}
    for reg, title in TITLES.items():
        F.CUR["region"] = reg
        body, box = B.toc(region_page(reg, slug, parts), "j-" + reg.lower())
        box = re.sub(r'href="#([^"]+)"', r'href="#\1" data-scroll="\1"', box)
        out[reg.lower()] = {"title": f"{title} Journal", "html": body, "toc": box}
    return out
