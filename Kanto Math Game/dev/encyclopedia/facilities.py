"""The battle facilities' lists, made from the game's own data files (region/encyclopedia, 11-24): five extra pages for the
Mechanics list, next to the written Battle Facilities page (mechanics/battle-facilities.html).

    pages(B, F, items=None) -> {slug: {"title", "group", "blurb", "html", "toc"}}   (the shape build_site.mechanics() makes)

  battle-cds            assets/orre_battle_cds.json    (src/world/battle_cd.py)
  trainer-tower-floors  assets/trainer_tower.json      (src/world/trainer_tower.py)
  pwt-tournaments       assets/b2_pwt.json             (src/world/pwt.py)
  battle-subway-lines   assets/b2_subway.json          (src/world/battle_subway.py)
  frontier-trainers     assets/frontier_gen3.json, frontier_gen4.json and the Brains in src/world/frontier.py

items: the item slugs that have an item page (an item is linked only when it has one)."""
import ast
import importlib.util
import json
import os
import re

GROUP = "Battle facility lists"


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")


class _Out:
    """The little helpers every page uses: Pokemon, moves and items as links, tables."""

    def __init__(self, B, F, items):
        self.B, self.F = B, F
        self.items = set(items or ())
        self.moves = json.load(open(os.path.join(F.A, "moves.json"), encoding="utf-8"))
        self.old = {}   # (older spellings some trainer sets use: src/pokemon/moves.py OLD_NAMES, as the game reads them)
        try:
            src = open(os.path.join(F.ROOT, "src", "pokemon", "moves.py"), encoding="utf-8").read()
            m = re.search(r"^OLD_NAMES = (\{.*?\})", src, re.S | re.M)
            self.old = ast.literal_eval(m.group(1)) if m else {}
        except Exception:
            pass
        try:
            import more_data
            self.move_name = more_data.move_name
        except Exception:   # (more_data is beside this file; a plain fallback all the same)
            self.move_name = lambda k: " ".join(w.capitalize() for w in str(k).split("-"))

    def esc(self, s):
        return self.B.esc(s)

    def mon(self, pid, extra=""):
        F, B = self.F, self.B
        b = F.base_id(pid)
        name = B.esc(F.mon_name(pid))
        link = f'<a class="x" href="#pokemon-{b}">{name}</a>' if 0 < b <= 1025 else name
        return f'<span class="mon">{B.icon("p", f"{b}.png")}{link}{extra}</span>'

    def chip(self, pid):
        F, B = self.F, self.B
        b = F.base_id(pid)
        return f'<a href="#pokemon-{b}">{B.icon("p", f"{b}.png")}{B.esc(F.mon_name(pid))}</a>'

    def chips(self, pids):
        seen, out = set(), []
        for p in sorted(pids, key=lambda p: self.F.base_id(p)):
            if p not in seen:
                seen.add(p)
                out.append(self.chip(p))
        return f'<div class="chips">{"".join(out)}</div>'

    def move(self, k):
        k = self.old.get(str(k).upper(), k)
        name = self.B.esc(self.move_name(k))
        return f'<a class="x" href="#move-{_slug(k)}">{name}</a>' if str(k).upper() in self.moves else name

    def moves_line(self, ks):
        return ", ".join(self.move(k) for k in ks or [])

    def item_key(self, k):
        return {"UP_GRADE": "UPGRADE"}.get(k, k)   # (FireRed's key; the game gives the UPGRADE: trainer_tower.py)

    def item(self, k):
        if not k:
            return ""
        k = self.item_key(k)
        name = self.B.esc(self.F.item_name(k))
        s = _slug(k)
        return f'<a class="x" href="#item-{s}">{name}</a>' if s in self.items else name

    def mon_set(self, pid, moves=None, item=None, level=None):
        """One Pokemon with what it holds and knows, for a team cell."""
        bits = []
        if level:
            bits.append(f"Lv {level}")
        if item:
            bits.append("holds " + self.item(item))
        head = self.mon(pid, f' <span class="small">{", ".join(bits)}</span>' if bits else "")
        return head + (f'<div class="small">{self.moves_line(moves)}</div>' if moves else "")

    def table(self, caption, heads, rows):
        th = "".join(f"<th>{h}</th>" for h in heads)
        body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
        return (f'<div class="frame"><table><caption>{caption}</caption><thead><tr>{th}</tr></thead>'
                f"<tbody>{body}</tbody></table></div>")

    def page(self, slug, title, blurb, body):
        html, box = self.B.toc(body, "m-" + slug)
        box = re.sub(r'href="#([^"]+)"', r'href="#\1" data-scroll="\1"', box)
        return {"title": title, "group": GROUP, "blurb": blurb, "html": html, "toc": box}


def _load(F, name):
    return json.load(open(os.path.join(F.A, name), encoding="utf-8"))


def _class_words(c):
    w = str(c).replace("_", " ").title()
    return re.sub(r"\bP(?:ke)?mn\b|\bPokemon\b", "Pokémon", w)


BACK = '<p class="small">How the facilities work: <a href="#mechanic-battle-facilities">Battle Facilities</a>.</p>'


# ---------------------------------------------------------------------------------------------------- Orre's Battle CDs
def battle_cds(o):
    cds = _load(o.F, "orre_battle_cds.json")
    tiers = [(1, "One-star CDs"), (2, "Two-star CDs"), (3, "Three-star CDs"), (0, "CDs without stars")]
    body = ['<p>XD\'s fifty Battle CDs are puzzle battles. You find the CDs around Orre and play them on the Battle CD '
            'player at the Pokémon HQ Lab. Each CD lends you its own team (your own Pokémon sit it out) and sets you '
            'against a Sim Trainer\'s team. Some CDs give you only a few turns: win before they run out to clear the CD. '
            'Win or lose, your own team comes straight back, and nothing is caught, earned or lost.</p>',
            '<p>The stars are the CD\'s difficulty, from one to three. CDs 33 to 50 have no stars.</p>', BACK]
    for stars, head in tiers:
        rows = []
        for k in sorted(cds):
            cd = cds[k]
            if int(cd.get("stars") or 0) != stars:
                continue
            title = str(cd["title"]).replace("�", "É")   # (the data's "POK?MON": the accent lost on the way in)
            ck = f"BATTLE_CD_{k}"
            name = (f'<a class="x" href="#item-{_slug(ck)}">CD {k}</a>' if _slug(ck) in o.items else f"CD {k}")
            kind = "Double" if cd.get("double") else "Single"
            lim = int(cd.get("turn_limit") or 0)
            rule = f"{kind} battle<br>" + (f"win within {lim} turn{'s' if lim != 1 else ''}" if lim else "no turn limit")
            you = "".join(o.mon_set(m["id"], m.get("moves"), m.get("item"), m.get("level")) for m in cd["you"])
            foe = "".join(o.mon_set(m["id"], m.get("moves"), m.get("item"), m.get("level")) for m in cd["foe"])
            rows.append([f"{name}<br><b>{o.esc(title)}</b>", rule, you, f'<span class="small">{o.esc(cd.get("foe_name") or "")}</span>{foe}'])
        if rows:
            body.append(f"<h2>{head}</h2>")
            body.append(o.table(head, ["CD", "Battle", "Your team", "The foe's team"], rows))
    return o.page("battle-cds", "Orre's Battle CDs", "All fifty of XD's Battle CDs: the battle, the team you're lent and the team you face.",
                  "\n".join(body))


# ---------------------------------------------------------------------------------------------------- the Trainer Tower
def trainer_tower(o):
    d = _load(o.F, "trainer_tower.json")
    words = {"SINGLE": "Single Battle", "DOUBLE": "Double Battle", "KNOCKOUT": "Knockout", "MIXED": "Mixed"}
    body = ['<p>The Trainer Tower on Seven Island has eight floors for each of its four climbs. Every trainer here has six '
            'Pokémon, and the floor decides which of them come out: one trainer with three in a Single floor, a pair with '
            'one each in a Double floor, three trainers with one each in a Knockout floor. A Mixed climb borrows floors '
            'from the other three. All of the tower\'s Pokémon battle at the level of your strongest Pokémon.</p>',
            BACK]
    prize_rows = []
    for c in ("SINGLE", "DOUBLE", "KNOCKOUT", "MIXED"):
        p = d["prizes"].get(c)
        note = " (once you have the National Pokédex)" if o.item_key(p) == "UPGRADE" else ""
        prize_rows.append([words[c], o.item(p) + note])
    body.append("<h2>Prizes</h2><p>The owner on the roof gives each climb's prize the first time you finish it.</p>")
    body.append(o.table("The owner's prizes", ["Climb", "Prize"], prize_rows))
    for c in ("SINGLE", "DOUBLE", "KNOCKOUT", "MIXED"):
        rows = []
        for n, key in enumerate(d["climbs"][c], 1):
            f = d["floors"][key]
            kind = f["type"]
            pick = d["pick"][kind][n - 1]
            ts = f["trainers"]
            if kind == "SINGLE":
                who = f'{o.esc(_class_words(ts[0]["class"]))} {o.esc(ts[0]["name"])}'
                team = "".join(o.mon_set(ts[0]["mons"][i]["id"], ts[0]["mons"][i].get("moves"), ts[0]["mons"][i].get("item"))
                               for i in pick)
            elif kind == "DOUBLE":
                who = f'{o.esc(_class_words(ts[0]["class"]))} {o.esc(ts[0]["name"])}'
                team = "".join(o.mon_set(ts[j]["mons"][pick[j]]["id"], ts[j]["mons"][pick[j]].get("moves"),
                                         ts[j]["mons"][pick[j]].get("item")) for j in (0, 1))
            else:
                who = "<br>".join(f'{o.esc(_class_words(t["class"]))} {o.esc(t["name"])}' for t in ts)
                team = "".join(o.mon_set(t["mons"][pick[j]]["id"], t["mons"][pick[j]].get("moves"), t["mons"][pick[j]].get("item"))
                               for j, t in enumerate(ts))
            rows.append([f"{n}F", words[kind], who, team])
        body.append(f"<h2>{words[c]} climb</h2>")
        body.append(o.table(f"The {words[c]} climb, floor by floor", ["Floor", "Kind", "Trainers", "Their Pokémon"], rows))
    return o.page("trainer-tower-floors", "Trainer Tower Floors", "Every floor of the Sevii Trainer Tower's four climbs: who waits there and with what.",
                  "\n".join(body))


# ---------------------------------------------------------------------------------------------------- the PWT
def pwt(o):
    d = _load(o.F, "b2_pwt.json")
    tn = {t["key"]: t["name"] for t in d["tournaments"]}

    def opens(t):
        out = []
        for need in t["opens"]:
            if need.startswith("won10:"):
                out.append(f"win the {tn[need[6:]]} ten times")
            elif need.startswith("won:"):
                out.append(f"win the {tn[need[4:]]}")
            elif need == "beat_unova_champion":
                out.append("become Unova's Champion")
            else:
                out.append(need)
        if not out:
            return "from the start"
        return out[0] if len(out) == 1 else ", ".join(out[:-1]) + " and " + out[-1]

    def roster(t):
        r = t["roster"]
        if r == "driftveil":
            return "the Driftveil regulars (below)"
        if r == "type":
            return "the Leaders and Champions of the type you pick"
        return ", ".join(o.esc(n) for n in r)

    rows = [[o.esc(t["name"]), "left" if t["desk"] == "left" else "right", str(t["level"]),
             f'{t["bp"][0]} / {t["bp"][1]}', roster(t), o.esc(opens(t))] for t in d["tournaments"]]
    body = ['<p>Each tournament draws three opponents from its list of entrants, one per round. A Leader or Champion '
            'brings six Pokémon: in a Single tournament they use their first two and one of the other four, in a Double '
            'tournament their first four. Every opponent\'s Pokémon are at the tournament\'s level.</p>', BACK,
            "<h2>Tournaments</h2>",
            o.table("Tournaments", ["Tournament", "Desk", "Level", "BP (Single / Double)", "Entrants", "Opens after you"], rows)]

    types = {}
    for n, e in d["trainers"].items():
        if e.get("type"):
            types.setdefault(e["type"], []).append(n)
    body.append("<h3>Type Expert entrants</h3>")
    body.append(o.table("Type Expert Tournament: entrants by type", ["Type", "Entrants"],
                        [[t.title(), ", ".join(o.esc(n) for n in sorted(ns))] for t, ns in sorted(types.items())]))

    def team(e, pool):
        sets = d["sets"][pool]
        return "".join(o.mon_set(sets[str(s)]["species"], sets[str(s)].get("moves"), sets[str(s)].get("item"))
                       for s in e["sets"] if str(s) in sets)

    # the Driftveil Tournament
    body.append("<h2>The Driftveil Tournament</h2>")
    body.append("<p>Your first visit is the story's tournament: your rival, Cheren and Colress in turn. Your rival's team "
                "depends on your first partner Pokémon.</p>")
    st = d["story"]
    sets = d["sets"]["drift"]
    rows = []
    h = st.get("Hugh")
    if h:
        starters = {"495": 495, "498": 498, "501": 501}
        for sk, ids in h.get("by_starter", {}).items():
            rows.append([f"Your rival (if you chose {o.esc(o.F.mon_name(starters.get(sk, sk)))})",
                         "".join(o.mon_set(sets[str(s)]["species"], sets[str(s)].get("moves"), sets[str(s)].get("item"))
                                 for s in ids if str(s) in sets)])
    for n in ("Cheren", "Colress"):
        if n in st:
            rows.append([o.esc(n), team(st[n], "drift")])
    body.append(o.table("The story's Driftveil Tournament", ["Opponent", "Team"], rows))
    notable = ("Cheren", "Roxie", "Burgh", "Elesa", "Clay")
    body.append("<p>After that, the Driftveil, Rental and Mix Tournaments draw from these regulars: one of the others in the "
                f"first round, then two of {', '.join(notable[:-1])} and {notable[-1]}.</p>")
    rows = [[f'{o.esc(_class_words(e["class"]))} {o.esc(e["name"])}', team(e, "drift")] for e in d["drift"].values()]
    body.append(f'<details><summary>The Driftveil regulars ({len(rows)})</summary>'
                + o.table("The Driftveil regulars", ["Trainer", "Six Pokémon"], rows) + "</details>")

    # Leaders and Champions by region
    body.append("<h2>Leaders and Champions</h2>")
    regions = [("unova", "Unova's Leaders"), ("kanto", "Kanto's Leaders"), ("johto", "Johto's Leaders"),
               ("hoenn", "Hoenn's Leaders"), ("sinnoh", "Sinnoh's Leaders"), ("champions", "The Champions")]
    done = set()
    for key, head in regions:
        t = next(x for x in d["tournaments"] if x["key"] == key)
        names = [n for n in t["roster"] if n in d["trainers"]]
        done |= set(names)
        rows = [[o.esc(n), team(d["trainers"][n], "main")] for n in names]
        body.append(f"<h3>{head}</h3>")
        body.append(f'<details><summary>{len(rows)} trainers</summary>'
                    + o.table(head, ["Trainer", "Six Pokémon, in order"], rows) + "</details>")
    rest = [n for n in d["trainers"] if n not in done]
    if rest:
        rows = [[o.esc(n), team(d["trainers"][n], "main")] for n in rest]
        body.append("<h3>Others</h3>")
        body.append(o.table("Other entrants", ["Trainer", "Six Pokémon, in order"], rows))
    return o.page("pwt-tournaments", "PWT Tournaments", "The Pokémon World Tournament's tournaments, who enters each one and their teams.",
                  "\n".join(body))


# ---------------------------------------------------------------------------------------------------- the Battle Subway
def subway(o):
    d = _load(o.F, "b2_subway.json")
    T, S = d["trainers"], d["sets"]
    lv = d["level"]
    body = [f'<p>On the Battle Subway every Pokémon battles at <b>Lv {lv}</b>. Which trainer walks into your car depends on '
            'how far your streak has gone: the further you ride, the tougher the group they come from. A trainer never '
            'boards twice in one train. They bring three Pokémon in a Single Train, four in a Double Train, and two each '
            'in a Multi Train (two trainers against you and your partner), picked at random from their list with no two '
            'of the same kind.</p>', BACK]
    body.append("<h2>Lines</h2>")
    body.append(o.table("The lines", ["Line", "Battles", "Opens"], [
        ["Single Train", "Single, three Pokémon each", "from the start"],
        ["Double Train", "Double, four Pokémon each", "from the start"],
        ["Multi Train", "Double, two trainers a side", "from the start"],
        ["Super Single Train", "as the Single Train", "after you beat Ingo on the Single Train"],
        ["Super Double Train", "as the Double Train", "after you beat Emmet on the Double Train"],
        ["Super Multi Train", "as the Multi Train", "after you beat Ingo and Emmet on the Multi Train"]]))

    groups = [(1, 50), (51, 70), (71, 110), (111, 160), (161, 180), (181, 200), (201, 220), (221, 300)]
    gname = {g: f"Group {chr(65 + i)}" for i, g in enumerate(groups)}

    def spans_words(spans):
        out = []
        for a, b in spans:
            inside = [g for g in groups if a <= g[0] and g[1] <= b]
            out += [gname[g] for g in inside]
        return " + ".join(out) or "?"

    body.append("<h2>Who boards when</h2>")
    for tier, head in (("normal", "Single, Double and Multi Trains"), ("super", "Super Trains")):
        rows = []
        for a, b, spans in d["ranges"][tier]:
            when = f"{a}" if a == b else (f"{a} and on" if b >= 999 else f"{a}–{b}")
            rows.append([when, spans_words(spans)])
        body.append(o.table(f"{head}: battle number and trainer group", ["Battle of the streak", "Trainers from"], rows))
    body.append("<p>The Subway Bosses are the 21st opponent of the Single, Double and Multi Trains and the 49th of the Super "
                "Trains.</p>")

    body.append("<h2>The Subway Bosses</h2>")

    def boss_team(tid):
        t = T[str(tid)]
        return "".join(o.mon_set(S[str(s)]["species"], S[str(s)].get("moves"), S[str(s)].get("item")) for s in t["pool"] if str(s) in S)

    b = d["bosses"]
    rows = []
    for i, tr in ((0, "Normal"), (1, "Super")):
        rows.append([f"{tr} Single Train", o.esc(T[str(b['single'][i])]["name"]), boss_team(b["single"][i])])
        rows.append([f"{tr} Double Train", o.esc(T[str(b['double'][i])]["name"]), boss_team(b["double"][i])])
        for tid in b["multi"][i]:
            rows.append([f"{tr} Multi Train", o.esc(T[str(tid)]["name"]), boss_team(tid)])
    body.append(o.table("Ingo and Emmet's teams", ["Line", "Boss", "Team"], rows))

    body.append("<h2>Your Multi Train partner</h2>")
    body.append("<p>Nate rides with a girl and Rosa with a boy. Before boarding you choose the kind of team they bring; "
                "they pick two from that list each battle.</p>")
    rows = []
    for who, ids in d["partners"].items():
        for style, tid in zip(("Attack", "Defence", "Balance"), ids):
            t = T[str(tid)]
            rows.append([who.title(), style, o.chips([S[str(s)]["species"] for s in t["pool"] if str(s) in S])])
    body.append(o.table("The partners' teams", ["Partner", "Team", "Pokémon they may bring"], rows))

    body.append("<h2>Subway Trainers</h2>")
    body.append("<p>Every Subway Trainer, by group, with the Pokémon the group's trainers may bring.</p>")
    for g in groups:
        ts = [T[str(i)] for i in range(g[0], g[1] + 1) if str(i) in T]
        names = ", ".join(o.esc(re.sub(r"\bPokemon\b", "Pokémon", t["name"])) for t in ts)
        sp = {S[str(s)]["species"] for t in ts for s in t["pool"] if str(s) in S}
        body.append(f"<h3>{gname[g]}</h3>")
        body.append(f'<p class="small">{len(ts)} trainers: {names}.</p>')
        body.append(f'<details><summary>{len(sp)} Pokémon</summary>{o.chips(sp)}</details>')
    return o.page("battle-subway-lines", "Battle Subway Lines", "The Battle Subway's lines: who boards at each stage of a streak, the Subway Bosses' teams and every Subway Trainer.",
                  "\n".join(body))


# ---------------------------------------------------------------------------------------------------- the Frontiers
def _frontier_code(F):
    path = os.path.join(F.ROOT, "src", "world", "frontier.py")
    spec = importlib.util.spec_from_file_location("_enc_frontier", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def frontier(o):
    g3, g4 = _load(o.F, "frontier_gen3.json"), _load(o.F, "frontier_gen4.json")
    body = ['<p>The Battle Frontiers of Hoenn, Johto and Sinnoh, and Orre\'s Battle Tower, send random trainers with '
            'three random Pokémon at you. The trainers come from the main games\' Frontier lists: Emerald\'s for Hoenn '
            'and Orre, Platinum, HeartGold and SoulSilver\'s for Johto and Sinnoh. The Pokémon come from Emerald\'s four '
            'groups everywhere, weakest (group 1) to strongest (group 4).</p>', BACK]

    body.append("<h2>How the opponents get stronger</h2>")
    body.append(o.table("Pokémon groups by streak (Hoenn, Johto, Sinnoh)", ["Streak", "Pokémon from"], [
        ["Before the Silver battle: wins 0–1", "groups 1 and 2"],
        ["Before the Silver battle: wins 2–3", "groups 2 and 3"],
        ["Before the Silver battle: win 4", "groups 3 and 4"],
        ["After the Silver: wins 0–4", "groups 3 and 4"],
        ["After the Silver: wins 5–9", "group 4"]]))
    body.append("<p>Which trainer you meet goes by the main games' columns, seven battles each: battles 1 to 7 bring a "
                "trainer from the first column, battles 8 to 14 from the second. Streaks here end at a Brain after 5 or "
                "10 wins, so only those two columns' trainers turn up in the Frontiers. Orre's Battle Tower (single "
                "battles and 2-on-2 doubles at Lv 50) picks any of Emerald's trainers, with Pokémon from groups 3 and 4 "
                "for the first ten wins and then group 4 only; its Little Cup uses first-stage Pokémon at Lv 5 instead.</p>")

    body.append("<h2>Pokémon groups</h2>")
    for k in sorted(g3["groups"]):
        ids = g3["groups"][k]
        body.append(f"<h3>Group {int(k) + 1}</h3>")
        body.append(f'<details><summary>{len(set(ids))} Pokémon</summary>{o.chips(ids)}</details>')
    body.append('<p class="small">In group 4 some Pokémon are listed several times, so they turn up more often: '
                + ", ".join(f"{o.esc(o.F.mon_name(p))} ×{n}" for p, n in sorted(
                    ((p, g3["groups"]["3"].count(p)) for p in set(g3["groups"]["3"])), key=lambda x: -x[1]) if n >= 5)
                + ".</p>")

    def trainer_lists(data, head, note):
        body.append(f"<h2>{head}</h2>")
        body.append(f"<p>{note}</p>")
        cols = [(0, "Battles 1–7 (first column)"), (1, "Battles 8–14 (second column)")]
        for c, h in cols:
            ts = [t for t in data["trainers"] if c in t["cols"]]
            names = ", ".join(f'{o.esc(t["class"].rstrip("♂♀").strip())} {o.esc(t["name"])}' for t in ts)
            body.append(f"<h3>{h}</h3><p class=\"small\">{len(ts)} trainers: {names}.</p>")
        rest = [t for t in data["trainers"] if not ({0, 1} & set(t["cols"]))]
        if rest:
            names = ", ".join(f'{o.esc(t["class"].rstrip("♂♀").strip())} {o.esc(t["name"])}' for t in rest)
            return rest, names
        return [], ""

    rest, names = trainer_lists(g3, "Emerald's Frontier trainers", "Hoenn's Battle Frontier and Orre's Battle Tower.")
    if rest:
        body.append(f"<h3>Later columns</h3><p>These trainers belong to the main games' later columns. In Hoenn they "
                    f"don't reach you, but Orre's Battle Tower can send any of them.</p>"
                    f'<details><summary>{len(rest)} trainers</summary><p class="small">{names}.</p></details>')
    rest, names = trainer_lists(g4, "Platinum, HeartGold and SoulSilver's Frontier trainers",
                                "Johto's and Sinnoh's Battle Frontiers.")
    if rest:
        body.append(f"<h3>Later columns</h3><p>These trainers belong to the main games' later columns, which a streak "
                    f"here never reaches.</p>"
                    f'<details><summary>{len(rest)} trainers</summary><p class="small">{names}.</p></details>')

    try:
        fr = _frontier_code(o.F)
    except Exception:
        fr = None
    if fr is not None:
        body.append("<h2>The Frontier Brains' teams</h2>")
        body.append("<p>After 5 wins the Brain's Silver team, after 10 more the Gold team. A Brain with no set team in its "
                    "own game battles with three random Pokémon from group 4.</p>")
        rows = []
        for fac, (title, _sp, silver, gold, _sym) in fr.BRAINS.items():
            if fac.startswith("s"):   # (Sinnoh's are Johto's own: the same Brains, the same teams)
                continue
            where = "Johto and Sinnoh" if fac.startswith("j") else "Hoenn"
            cells = []
            for i, team in enumerate((silver, gold)):
                if not team:
                    cells.append("three random Pokémon")
                    continue
                mv = fr.BRAIN_MOVES.get(fac, ({}, {}))[i]
                held = fr.BRAIN_HELD.get(fac, ([], []))[i]
                cells.append("".join(o.mon_set(p, mv.get(str(p)), held[j] if j < len(held) else None)
                                     for j, p in enumerate(team)))
            rows.append([f"{o.esc(title)}<br><span class=\"small\">{o.esc(fr.NAMES.get(fac, fac))}, {where}</span>"] + cells)
        body.append(o.table("Frontier Brains", ["Brain", "Silver team", "Gold team"], rows))
    return o.page("frontier-trainers", "Frontier Trainers", "Who you meet in the Battle Frontiers: the trainer lists, the Pokémon groups and the Brains' teams.",
                  "\n".join(body))


def pages(B, F, items=None):
    o = _Out(B, F, items)
    out = {}
    for slug, fn in (("battle-cds", battle_cds), ("trainer-tower-floors", trainer_tower), ("pwt-tournaments", pwt),
                     ("battle-subway-lines", subway), ("frontier-trainers", frontier)):
        out[slug] = fn(o)
    return out
