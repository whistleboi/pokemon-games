"""Build the walkthrough page from the written parts and the game's facts (region/encyclopedia, 11-24).

    python dev/encyclopedia/build.py kanto OUT.html

Reads dev/encyclopedia/<region>/part*.html (our own words) and fills their markers from facts.py:

    {{tables:KEY}}            the place's Available Pokemon table(s) and its Items table, side by side
    {{wild:KEY}} {{items:KEY}} one of them on its own ({{items:KEY:Room title}} = that room's items only)
    {{trainers:KEY}}          the trainers on the place's map (and in its rooms, Gym Leaders left out);
                              {{trainers:KEY:Room title}} = one room's only
    {{battle:KEY:Name}}       a story battle box (a Leader, the rival, a boss), found by name
    {{battle:KEY:Name|text}}  ...with a line under it
    {{journal:ID}}            the Journal's own mission text, in its box
    {{mart}} {{prizes}}       the Poke Mart counter by badges; route trainers' prizes by badges

Each part file starts with <!--title: ...-->; its h2 / h3 headings make its contents box. Every icon goes into the page
once, as a CSS class, so the page stays small.
"""
import base64
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import facts as F  # noqa: E402

SPR = os.path.join(F.A, "sprites")
ICONS = {}


def icon(kind, fname):
    """A CSS class for one sprite (embedded once)."""
    if not fname:
        return ""
    path = os.path.join(SPR, "icons" if kind == "p" else "items", fname)
    if not os.path.exists(path):
        return ""
    cls = kind + re.sub(r"[^a-z0-9]", "_", fname.lower().rsplit(".", 1)[0])
    if cls not in ICONS:
        from io import BytesIO
        from PIL import Image
        im = Image.open(path).convert("RGBA")
        if kind == "p" and im.width == 2 * im.height:   # (party icons: two frames side by side, the first one)
            im = im.crop((0, 0, im.height, im.height))
        box = im.getbbox()
        if box:
            im = im.crop(box)
        buf = BytesIO()
        im.save(buf, "PNG", optimize=True)
        ICONS[cls] = base64.b64encode(buf.getvalue()).decode()
    return f'<i class="ic {cls}" aria-hidden="true"></i>'


def esc(s):
    return html.escape(str(s), quote=False)


def ours():
    return '<span class="ours">ours</span>'


def rate(v):
    if v < 0.95:
        return "&lt;1%"
    return f"{int(v + 0.5)}%"


def lv(r):
    a, b = r["lv"]
    return f"{a}" if a == b else f"{a}–{b}"


def mon_link(pid, name):
    b = F.base_id(pid)
    return f'<a class="x" href="#mon-{b}">{esc(name)}</a>' if 0 < b <= 1025 else esc(name)


def item_link(key, name):
    return f'<a class="x" href="#item-{str(key).lower()}">{esc(name)}</a>'


def mon_cell(r):
    tags = ""
    if r.get("after"):
        tags += f' <span class="when">after {esc(r["after"].title())}</span>'
    if r.get("ours") or r.get("after"):
        tags += " " + ours()
    return f'<span class="mon">{icon("p", r["icon"])}{mon_link(r["id"], r["name"])}</span>{tags}'


# ---------------------------------------------------------------- the story level cap (src/world/levels.py)
_LV = open(os.path.join(F.ROOT, "src", "world", "levels.py"), encoding="utf-8").read()
GYM_ACE = eval(re.search(r'"KANTO": (\[[\d, ]+\])', _LV).group(1))
CHAMP_ACE = int(re.search(r'CHAMPION_ACE = \{"KANTO": (\d+)', _LV).group(1))
CAP_OVER = int(re.search(r"CAP_OVER_ACE = (\d+)", _LV).group(1))
LIFT_BELOW = int(re.search(r"CAP_LIFT_BELOW = (\d+)", _LV).group(1))
LIFT_ABOVE = int(re.search(r"CAP_LIFT_ABOVE = (\d+)", _LV).group(1))
REMATCH_FLOOR = int(re.search(r'LEAGUE_REMATCH_FLOOR = \{"KANTO": (\d+)', _LV).group(1))
CAP = {"badges": 0, "post": False}   # set as the parts go, by {{badges:N}} / {{badges:post}}


def story_ace(badges):
    """levels.story_ace: the next Leader's ace (never lower than an earlier one), the Champion's with all eight."""
    return max(GYM_ACE[:badges + 1]) if badges < len(GYM_ACE) else CHAMP_ACE


def cap_band(f):
    """levels.capped_band: once your lead has reached the ace, the place's wild Pokemon come at ace-3..ace+1 (not where
    the place's own level is already above that)."""
    if CAP["post"]:
        return None
    ace = story_ace(CAP["badges"])
    if f["level"] > ace + LIFT_ABOVE:
        return None
    return ace - LIFT_BELOW, ace + LIFT_ABOVE


RODS = {"Old Rod": 5, "Good Rod": 10, "Super Rod": 15}


def at_cap(r, band, fixed_land):
    if not band or (fixed_land and r["how"] not in RODS and r["how"] != "Surfing"):
        return "—"
    lo, hi = band
    need = RODS.get(r["how"])
    if need:
        lo, hi = max(lo, need), max(hi, need)
    return f"{lo}" if lo == hi else f"{lo}–{hi}"


def cap_html():
    if CAP["post"]:
        return ('<div class="note cap"><b>Level cap: your team.</b> After the title the cap follows your own team: it\'s your '
                f'highest level, and never below Lv {REMATCH_FLOOR}. Wild Pokémon rise to your team\'s level (its average, '
                'your lowest Pokémon left out) wherever that\'s above the place\'s own. Legendary Pokémon stay at Lv 70, and '
                'trainers keep their own levels.</div>')
    n = CAP["badges"]
    ace = story_ace(n)
    who = (f"your {['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth'][n]} badge" if n < 8
           else "the Champion")
    return (f'<div class="note cap"><b>Level cap: Lv {ace + CAP_OVER}</b> until {who}. Your Pokémon stop gaining Exp. there, '
            f'and Rare Candies stop working. The next Leader\'s best Pokémon is Lv {ace}. Once your lead Pokémon reaches '
            f'Lv {ace}, wild Pokémon in places below that level come at Lv {ace - LIFT_BELOW}–{ace + LIFT_ABOVE}: '
            'the "At the cap" column in the tables. Trainers keep their own levels.</div>')


def captable_html():
    """The cap for each badge count, with the Leader usually next (levels.GYM_ORDER) and his best Pokemon."""
    order = re.findall(r'"([A-Z_]+)"', re.search(r'"KANTO": \[([^\]]+)\]', _LV[_LV.index("GYM_ORDER"):]).group(1))
    rows = []
    for n in range(9):
        ace = story_ace(n)
        if n < 8:
            leader = ((F.PLACES.get(order[n]) or {}).get("gym") or {}).get("leader") or {}
            nxt = f"{leader.get('name', '?')} ({FACTS[order[n]]['name'] if order[n] in FACTS else order[n].title()})"
        else:
            nxt = "the Elite Four and the Champion"
        rows.append(f"<tr><td>{n}</td><td><b>Lv {ace + CAP_OVER}</b></td><td>{esc(nxt)}</td><td>Lv {ace}</td>"
                    f"<td>Lv {ace - LIFT_BELOW}–{ace + LIFT_ABOVE}</td></tr>")
    rows.append(f"<tr><td>Champion</td><td><b>Your team</b></td><td>the post-game</td><td>—</td><td>your team's level</td></tr>")
    return ('<div class="frame captab"><table><caption>The story level cap</caption><thead><tr><th>Badges</th><th>Cap</th>'
            '<th>Next (usual order)</th><th>Their best</th><th>Wild at the cap</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def wild_table(rows, caption, water=False, band=None, fixed_land=False):
    if not rows:
        return ""
    cap_col = band is not None
    body = "".join(f'<tr><td>{mon_cell(r)}</td><td><span class="how">{esc(r["how"])}</span></td><td>{lv(r)}</td>'
                   + (f'<td>{at_cap(r, band, fixed_land)}</td>' if cap_col else "")
                   + f'<td class="rate">{rate(r["rate"])}</td></tr>' for r in rows)
    return (f'<div class="frame{" water" if water else ""}"><table><caption>{esc(caption)}</caption>'
            '<thead><tr><th>Pokémon</th><th>How</th><th>Levels</th>' + ("<th>At the cap</th>" if cap_col else "")
            + '<th>Rate</th></tr></thead>'
            f'<tbody>{body}</tbody></table></div>')


def wild_html(f):
    w = f["wild"]
    out = []
    band = cap_band(f)
    fixed = any("wild_levels" in n for n in w.get("notes", []))
    if w["land"]:
        out.append(wild_table(w["land"], "Available Pokémon", band=band, fixed_land=fixed))
    for z in w["zones"]:
        out.append(wild_table(z["rows"], f"Available Pokémon: {z['zone']}", band=band, fixed_land=fixed))
    if w["trees"]:
        out.append(wild_table(w["trees"], "Headbutt trees", band=band, fixed_land=fixed))
    if w["water"]:
        out.append(wild_table(w["water"], "On the water" if (w["land"] or w["zones"]) else "Available Pokémon (water)", water=True,
                              band=band, fixed_land=fixed))
    return "".join(out)


def human_cond(c):
    """A condition from the data, in words (only the kinds we can say for sure); None when we can't."""
    if not c:
        return None
    cs = c if isinstance(c, list) else [c]
    words = []
    for x in cs:
        x = str(x)
        m = re.match(r"caught_range:(\d+)-(\d+)", x)
        if m:
            words.append(f"Catch all {int(m.group(2)) - int(m.group(1)) + 1} Pokémon from #{m.group(1)} to #{m.group(2)}")
            continue
        m = re.match(r"(?:not:|not )?has_(\w+)_badge$", x)
        if m:
            words.append(("Before" if x.startswith("not") else "After") + f" the {m.group(1).title()} Badge")
            continue
        if x.startswith(("not got_", "not received_", "not:got_", "not:received_")):
            continue   # (just "once")
        return None
    return "; ".join(words) or None


def item_rows(f, room=None):
    rows, seen = [], set()
    for i in f["items"]:
        if room and i["where"] != room:
            continue
        key = (i["item"], i["where"], i.get("at"), i.get("who"), i.get("flag"))
        if key in seen:
            continue
        seen.add(key)
        place = "" if i["where"] == "outside" else i["where"]
        if i.get("hidden"):
            how = "Hidden: step on the spot (the Itemfinder beeps near it)"
        elif i.get("found"):
            how = "On the ground"
        else:
            who = re.sub(r"^(Talk to |Show )", "", i.get("who") or "")
            if who.split(" ")[0] in ("A", "An", "The", "Return", "Give", "Visit", "Trade", "Bring", "Take", "Use", "Look"):
                who = ""   # (a menu label, not a person: "Return the Gold Teeth")
            how = f"From {' '.join(w.capitalize() for w in who.split()) if who.isupper() else who}" if who else "Given"
        where = f"{place}: {how}" if place else how
        when = WHEN.get(f"{f['key']}:{i['item']}:{i['where']}") or human_cond(i.get("needs")) or ""
        qty = f" ×{i['qty']}" if isinstance(i.get("qty"), int) and i["qty"] > 1 else ""
        rows.append((i, where, when, qty))
    return rows


def items_html(f, room=None):
    rows = item_rows(f, room)
    if not rows:
        return ""
    has_when = any(w for _, _, w, _ in rows)
    head = "<th>Item</th><th>Where</th>" + ("<th>When</th>" if has_when else "")
    body = "".join(f'<tr><td><span class="item">{icon("i", i.get("sprite"))}{item_link(i["item"], i["name"])}{qty}</span></td><td>{esc(where)}</td>'
                   + (f"<td>{esc(when)}</td>" if has_when else "") + "</tr>" for i, where, when, qty in rows)
    return f'<div class="frame"><table><caption>Items</caption><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def team_html(team):
    return " ".join(f'<span class="mon sm">{icon("p", m["icon"])}{mon_link(m["id"], m["name"])}'
                    + (f' <span class="lv">Lv {m["lv"]}</span>' if m.get("lv") else "") + "</span>" for m in team)


CLASS_WORDS = {"GYM_LEADER": "Gym Leader", "ROCKET": "Team Rocket", "ROCKET_GRUNT": "Team Rocket Grunt", "ACE_TRAINER": "Ace Trainer",
               "COOLTRAINER": "Cooltrainer", "BLACKBELT": "Black Belt", "BUG_CATCHER": "Bug Catcher", "POKEMANIAC": "PokéManiac",
               "SUPER_NERD": "Super Nerd", "BIRD_KEEPER": "Bird Keeper", "CUE_BALL": "Cue Ball", "PSYCHIC_M": "Psychic",
               "PSYCHIC_F": "Psychic", "ELITE_FOUR": "Elite Four", "RIVAL": "Rival", "CHAMPION": "Champion"}


def class_word(c):
    c = str(c or "")
    return CLASS_WORDS.get(c, c.replace("_", " ").title())


def trainer_name(t):
    who = t.get("who") or ""
    n = (t["name"] if who.isupper() and t.get("name") else who) or t["name"] or ""
    n = n.replace("{rival_name}", "Your rival").strip()
    cw = class_word(t.get("class"))
    if n.lower() in cw.lower().split() or n.lower() == cw.lower():
        return cw
    if len(n.split()) >= 2 and t.get("class") not in ("ROCKET", "ROCKET_GRUNT"):
        return n   # (the name already says who: "Karate Master Koichi", "Camper Liam")
    return n if n.lower().startswith(cw.lower().split()[0]) or t.get("class") in ("RIVAL", "GYM_LEADER", None) else f"{cw} {n}"


def all_trainers(f):
    """Every trainer once; a Gym trainer's copy in the Gym room wins over the gym data's (so room tables find it)."""
    seen, out = {}, []
    for t in f["battles"] + f["trainers"]:
        k = (trainer_name(t), tuple(m["id"] for m in t["team"]))
        if k in seen:
            if t.get("by_starter") and not out[seen[k]].get("by_starter"):   # (keep the copy with the teams by starter)
                t = dict(t, where=out[seen[k]]["where"], who=out[seen[k]].get("who"))
                out[seen[k]] = t
            continue
        seen[k] = len(out)
        out.append(t)
    return out


def trainers_html(f, room=None):
    """The place's trainers as a table: all of them (a Where column when they're on several floors / in rooms), or one
    room's / floor's ({{trainers:KEY:Title}}). Leaders, rivals and story battles get boxes instead."""
    picked = []
    for t in all_trainers(f):
        if t["where"] in ("Gym Leader", "Gym") or t.get("class") in ("GYM_LEADER", "RIVAL", "CHAMPION", "ELITE_FOUR", "ROCKET_LEADER", "ROCKET_BOSS"):
            continue
        if id(t) in BOXED:
            continue   # (it has its own battle box somewhere in the walkthrough)
        if t["where"].startswith("story") or (t.get("boss") and "Gym" not in t["where"]):
            continue   # (bosses get a battle box: Jessie & James, a Rocket admin)
        if room and t["where"] != room:
            continue
        picked.append(t)
    if not picked:
        return ""
    wheres = {t["where"] for t in picked}
    show = not room and len(wheres) > 1
    rows = []
    for t in picked:
        w = "" if t["where"] in ("on the map", "outside") else t["where"]
        rows.append(f'<tr><td><b>{esc(trainer_name(t))}</b></td>' + (f'<td>{esc(w)}</td>' if show else "")
                    + f'<td>{team_html(t["team"])}</td></tr>')
    town = (F.PLACES.get(f["key"]) or {}).get("area_type") == "town"
    cap = "Trainers" + (f": {esc(room)}" if room else "") + f'<span class="style">{"battle screen" if town else "on the map"}</span>'
    return (f'<div class="frame"><table><caption>{cap}</caption><thead><tr><th>Trainer</th>' + ("<th>Where</th>" if show else "")
            + f'<th>Pokémon</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def find_trainer(f, name):
    """By name (or who); "Name@2" = the second one with that name (the late Route 22 rival)."""
    nth = 1
    if "@" in name:
        name, nth = name.rsplit("@", 1)
        nth = int(nth)
        hits = [t for t in all_trainers(f) if name.lower() in ((t.get("who") or "") + " " + (t["name"] or "")).lower()]
        return hits[nth - 1] if len(hits) >= nth else None
    n = name.lower().strip()
    for t in all_trainers(f):
        if n == (t.get("who") or "").lower() or n == (t["name"] or "").lower():
            return t
    for t in all_trainers(f):
        if n in (t.get("who") or "").lower() or n in (t["name"] or "").lower():
            return t
    return None


def reward_words(t):
    out = []
    for k, v in (t.get("reward_keys") or {}).items():
        if k == "message":
            continue
        nm = F.item_name(k)
        out.append(f"{nm} ×{v}" if isinstance(v, int) and v > 1 else nm)
    if t.get("badge"):
        out.insert(0, f"the {t['badge'].title()} Badge")
    return ", ".join(out)


def battle_html(f, name, note=None, pick=None):
    t = find_trainer(f, name)
    if t is None:
        raise SystemExit(f"battle not found: {f['key']} {name}")
    who = trainer_name(t)
    if t.get("by_starter"):
        teams = "".join(f'<div class="small">If you chose {esc(s)}:</div><div>{team_html(tm)}</div>'
                        for s, tm in t["by_starter"].items())
    else:
        teams = f"<div>{team_html(t['team'])}</div>"
    rw = reward_words(t)
    rw_html = f'<div class="small">Rewards: {esc(rw)}</div>' if rw else ""
    note_html = f'<div class="small">{note}</div>' if note else ""
    return (f'<div class="battle"><div><div class="who">{esc(who)}</div><div class="small">{esc(class_word(t.get("class")))}'
            ' · battle screen</div>'
            f'{rw_html}</div><div class="teams">{teams}{note_html}</div></div>')


def journal_html(mid):
    m = next((x for x in F.MISSIONS if x.get("id") == mid), None)
    if m is None:
        raise SystemExit(f"journal mission not found: {mid}")
    m = F.deep_fix(m)
    kind = {"MAIN": "Main", "SIDE": "Side"}.get(m.get("type"), (m.get("type") or "").title())
    desc = (m.get("desc") or m.get("description") or "").replace("{rival_name}", "your rival").replace("{player_name}", "you")
    title = (m.get("text") or m.get("title") or "").replace("{rival_name}", "Your rival")
    return (f'<div class="journal"><span class="tag">Journal · {esc(kind)}</span><br><b>{esc(title)}</b>: '
            f'<q>{esc(desc)}</q></div>')


def mart_html():
    from_items = []
    import importlib.util
    spec = importlib.util.spec_from_file_location("itemsmod", os.path.join(F.ROOT, "src", "pokemon", "items.py"))
    src = open(spec.origin, encoding="utf-8").read()
    std = eval(re.search(r"STANDARD_MART = (\[.*?\n\])", src, re.S).group(1))
    spc = eval(re.search(r"SPECIALTY_BALLS = (\[.*?\])\n", src, re.S).group(1))
    rows = []
    for need in sorted({n for n, _ in std + spc}):
        items = [i for n, its in std + spc if n == need for i in its] + (["EVERSTONE"] if need == 2 else [])
        cells = " ".join(f'<span class="item">{icon("i", F.item_sprite(i))}{esc(F.item_name(i))}</span>' for i in items)
        rows.append(f"<tr><td>{need}</td><td class=\"wrapcell\">{cells}</td></tr>")
    return ('<div class="frame"><table><caption>Poké Mart counter</caption><thead><tr><th>Badges</th><th>Added to the shelf</th></tr>'
            f'</thead><tbody>{"".join(rows)}</tbody></table></div>')


def prizes_html():
    src = open(os.path.join(F.ROOT, "src", "pokemon", "items.py"), encoding="utf-8").read()
    pr = eval(re.search(r"TRAINER_PRIZES = (\[.*?\])\n", src, re.S).group(1))
    rows = "".join(f"<tr><td>{n}+</td><td>" + ", ".join(f"{F.item_name(k)} ×{v}" if v > 1 else F.item_name(k) for k, v in p.items())
                   + "</td></tr>" for n, p in pr)
    return ('<div class="frame"><table><caption>Route trainers\' prize</caption><thead><tr><th>Badges</th><th>You get</th></tr>'
            f'</thead><tbody>{rows}</tbody></table></div>')


WHEN = {}
FACTS = {}
BOXED = set()   # trainers with a {{battle}} box: left out of the trainer tables
PLACE_ID = {}      # KEY -> the anchor of its first section
used_places = set()


def place_id(key):
    return "place-" + key.lower().replace("_", "-")


def link_places(body):
    """Link place names in the text (first mention in each paragraph) to their section, not to the one you're in."""
    names = sorted(((FACTS[k]["name"], k) for k in PLACE_ID if k in FACTS), key=lambda nk: -len(nk[0]))
    alias = {"Vermillion City": "Vermilion City"}
    pats = [(re.compile(r"(?<![\w-])" + re.escape(alias.get(n, n)) + r"(?![\w-])"), k) for n, k in names]
    here = [None]

    def para(m):
        inner = m.group(2)
        done = set()
        pieces = re.split(r"(<[^>]+>)", inner)
        depth = 0
        for i, piece in enumerate(pieces):
            if piece.startswith("<"):
                depth += 1 if re.match(r"<a[\s>]", piece) else -1 if piece.startswith("</a") else 0
                continue
            if depth:
                continue
            for pat, k in pats:
                if k in done or k == here[0]:
                    continue
                mm = pat.search(piece)
                if mm:
                    done.add(k)
                    piece = piece[:mm.start()] + '[[PL:' + k + '|' + mm.group(0) + ']]' + piece[mm.end():]
            pieces[i] = piece
        txt = "".join(pieces)
        txt = re.sub(r"\[\[PL:(\w+)\|(.*?)\]\]", lambda q: f'<a class="x" href="#{PLACE_ID[q.group(1)]}">{q.group(2)}</a>', txt)
        return m.group(1) + txt + m.group(3)

    out = []
    for chunk in re.split(r"(<h2[^>]*>)", body):
        dp = re.search(r'data-place="([^"]+)"', chunk) if chunk.startswith("<h2") else None
        if chunk.startswith("<h2"):
            here[0] = dp.group(1) if dp else None
            out.append(chunk)
            continue
        out.append(re.sub(r"(<(?:p|li|q)(?:\s[^>]*)?>)(.*?)(</(?:p|li|q)>)", para, chunk, flags=re.S))
    return "".join(out)


def fill(text):
    def rep(m):
        kind, arg = m.group(1), m.group(2) or ""
        note = None
        if "|" in arg:
            arg, note = arg.split("|", 1)
        parts = arg.split(":", 1) if arg else []
        key = parts[0] if parts else ""
        sub = parts[1] if len(parts) > 1 else None
        if kind in ("tables", "wild", "items", "trainers", "battle") and key not in FACTS:
            raise SystemExit(f"no facts for {key}")
        f = FACTS.get(key)
        if kind == "tables":
            inner = wild_html(f) + items_html(f, sub)
            return f'<div class="grid">{inner}</div>' if inner else ""
        if kind == "wild":
            inner = wild_html(f)
            return f'<div class="grid">{inner}</div>' if inner else ""
        if kind == "items":
            inner = items_html(f, sub)
            return f'<div class="grid">{inner}</div>' if inner else ""
        if kind == "trainers":
            inner = trainers_html(f, sub)
            return f'<div class="grid">{inner}</div>' if inner else ""
        if kind == "battle":
            return battle_html(f, sub or "", note)
        if kind == "journal":
            return journal_html(arg)
        if kind == "mart":
            return f'<div class="grid">{mart_html()}</div>'
        if kind == "badges":
            CAP.update(post=(arg == "post"), badges=8 if arg == "post" else int(arg))
            return ""
        if kind == "cap":
            return cap_html()
        if kind == "captable":
            return f'<div class="grid">{captable_html()}</div>'
        if kind == "prizes":
            return f'<div class="grid">{prizes_html()}</div>'
        raise SystemExit(f"unknown marker {kind}")
    return re.sub(r"\{\{(\w+)(?::([^}]*))?\}\}", rep, text)


def place_ref(k):
    nm = esc(FACTS[k]["name"])
    return f'<a href="#{PLACE_ID[k]}">{nm}</a>' if k in PLACE_ID else nm


def index_html():
    """Where every Pokemon and item turns up, from the same facts as the tables."""
    mons, items = {}, {}
    for k, f in FACTS.items():
        w = f["wild"]
        for r in w["land"] + w["water"] + w["trees"] + [r for z in w["zones"] for r in z["rows"]]:
            b = F.base_id(r["id"])
            if not 0 < b <= 1025:
                continue
            e = mons.setdefault(b, {"name": F.mon_name(b), "at": {}})
            e["at"].setdefault(k, set()).add(r["how"] + (" (" + r["name"] + ")" if r["name"] != F.mon_name(b) else ""))
        for t in all_trainers(f):
            for m in [m for tm in ((t.get("by_starter") or {}).values() or [t["team"]]) for m in tm] or t["team"]:
                b = F.base_id(m["id"])
                if not 0 < b <= 1025 or str(m["id"]) in F.PLACEHOLDER:
                    continue
                e = mons.setdefault(b, {"name": F.mon_name(b), "at": {}})
                e.setdefault("by", {}).setdefault(k, set()).add(trainer_name(t))
        for (i, where, when, qty) in item_rows(f):
            e = items.setdefault(i["item"], {"name": i["name"], "sprite": i.get("sprite"), "at": {}})
            e["at"].setdefault(k, []).append(where + (f" ({when})" if when else ""))
    rows = []
    for b in sorted(mons):
        e = mons[b]
        at = "; ".join(f"{place_ref(k)} <span class=\"small\">{esc(', '.join(sorted(h)))}</span>" for k, h in e["at"].items())
        by = "; ".join(f"{place_ref(k)} <span class=\"small\">{esc(', '.join(sorted(h)))}</span>" for k, h in (e.get("by") or {}).items())
        rows.append(f'<tr id="mon-{b}"><td>#{b:03d}</td><td><span class="mon">{icon("p", f"{b}.png")}{esc(e["name"])}</span></td>'
                    f'<td class="places">{at or "<span class=small>not in the wild</span>"}</td><td class="places">{by}</td></tr>')
    mon_t = ('<div class="frame idx"><table><caption>Pokémon</caption><thead><tr><th>No.</th><th>Pokémon</th><th>In the wild</th><th>Trainers who use it</th></tr>'
             f'</thead><tbody>{"".join(rows)}</tbody></table></div>')
    rows = []
    for key in sorted(items, key=lambda k: items[k]["name"]):
        e = items[key]
        at = "; ".join(f"{place_ref(k)} <span class=\"small\">{esc(' / '.join(ws))}</span>" for k, ws in e["at"].items())
        rows.append(f'<tr id="item-{key.lower()}"><td><span class="item">{icon("i", e["sprite"])}{esc(e["name"])}</span></td>'
                    f'<td class="places">{at}</td></tr>')
    item_t = ('<div class="frame idx"><table><caption>Items found and given</caption><thead><tr><th>Item</th><th>Where</th></tr>'
              f'</thead><tbody>{"".join(rows)}</tbody></table></div>')
    return ('<h2 id="index-pokemon">Pokémon</h2><p>Every Pokémon you can meet in Kanto and the Sevii Islands: where it lives in the wild, and which trainers use it.</p>'
            + mon_t + '<h2 id="index-items">Items</h2><p>Every item lying on the ground, hidden, or handed to you.</p>' + item_t)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", html.unescape(re.sub("<[^>]+>", "", s)).lower()).strip("-")


def toc(body, pid):
    """Contents box from the part's h2/h3 headings (giving each an id)."""
    items, used = [], set()

    def add_id(m):
        tag, attrs, inner = m.group(1), m.group(2) or "", m.group(3)
        mm = re.search(r'id="([^"]+)"', attrs)
        dp = re.search(r'data-place="([^"]+)"', attrs)
        hid = mm.group(1) if mm else PLACE_ID.get(dp.group(1)) if dp and dp.group(1) not in used_places else f"{pid}-{slug(inner)}"
        if dp:
            used_places.add(dp.group(1))
        while hid in used:
            hid += "-2"
        used.add(hid)
        items.append((tag, hid, re.sub("<[^>]+>", "", inner)))
        attrs = re.sub(r'\s*id="[^"]+"', "", attrs)
        return f'<{tag} id="{hid}"{attrs}>{inner}</{tag}>'
    body = re.sub(r"<(h2|h3)([^>]*)>(.*?)</\1>", add_id, body, flags=re.S)
    out, open3 = ["<ol>"], False
    for tag, hid, label in items:
        if tag == "h2":
            if open3:
                out.append("</ol></li>")
                open3 = False
            elif len(out) > 1:
                out.append("</li>")
            out.append(f'<li><a href="#{hid}">{label}</a>')
        else:
            if not open3:
                out.append("<ol>")
                open3 = True
            out.append(f'<li><a href="#{hid}">{label}</a></li>')
    out.append("</ol></li>" if open3 else "</li>" if len(out) > 1 else "")
    out.append("</ol>")
    return body, f'<nav class="toc" aria-label="Contents"><b>Contents</b>{"".join(out)}</nav>'


CSS = open(os.path.join(HERE, "page.css"), encoding="utf-8").read()


def build(region, out, only=None):
    global FACTS, WHEN
    import tempfile
    keys = [k for r in (["KANTO", "SEVII"] if region == "kanto" else [region.upper()]) for k in F.region_keys(r)]
    FACTS = {k: F.place(k) for k in keys}
    WHEN = {}
    for fn in sorted(os.listdir(os.path.join(HERE, region))):
        if re.match(r"when.*\.json$", fn):
            WHEN.update(json.load(open(os.path.join(HERE, region, fn), encoding="utf-8")))
    pdir = os.path.join(HERE, region)
    files = sorted(fn for fn in os.listdir(pdir) if re.match(r"part\d+\.html$", fn))
    if only:
        files = [fn for fn in files if int(re.search(r"\d+", fn).group()) in only or fn == "part01.html"]
    for fn in files:
        for k in re.findall(r'data-place="([^"]+)"', open(os.path.join(pdir, fn), encoding="utf-8").read()):
            PLACE_ID.setdefault(k, place_id(k))
    for fn in os.listdir(pdir):   # (every part, so a box in another part counts too)
        if re.match(r"part\d+\.html$", fn):
            for key, name in re.findall(r"\{\{battle:(\w+):([^}|]+)", open(os.path.join(pdir, fn), encoding="utf-8").read()):
                t = find_trainer(FACTS[key], name) if key in FACTS else None
                if t is not None:
                    BOXED.add(id(t))
    parts = []
    for fn in files:
        n = int(re.search(r"\d+", fn).group())
        text = open(os.path.join(pdir, fn), encoding="utf-8").read()
        title = re.search(r"<!--title:\s*(.*?)-->", text).group(1).strip()
        body, box = toc(link_places(fill(text)), f"p{n}")
        parts.append((n, title, body, box))
    n_idx = (parts[-1][0] + 1) if parts else 1
    body, box = toc(index_html(), f"p{n_idx}")
    parts.append((n_idx, "Index: Pokémon and items", body, box))
    head = open(os.path.join(pdir, "head.html"), encoding="utf-8").read()
    nav = "".join(f'<li><a href="#part-{n}">Part {n}</a>: {esc(t)}</li>' for n, t, _, _ in parts)
    sections = "".join(f'<section class="part" id="part-{n}"><div class="crumb">Part {n}</div><h1 class="ph">{esc(t)}</h1>{box}{body}'
                       f'<p class="back"><a href="#top">Back to the parts list</a></p></section>' for n, t, body, box in parts)
    icons_css = "".join(f".{c}{{background-image:url(data:image/png;base64,{b})}}" for c, b in ICONS.items())
    page = (head.replace("/*CSS*/", CSS + icons_css).replace("<!--PARTS-->", f'<ol class="parts">{nav}</ol>')
            + sections + open(os.path.join(pdir, "foot.html"), encoding="utf-8").read())
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page)
    print(f"{len(parts)} parts, {len(ICONS)} icons, {len(page) // 1024} KB -> {out}")


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], [int(a) for a in sys.argv[3:]] or None)
