"""Canon movesets for important battles (Gym Leaders, Elite Four, Champions, rivals, villains), taken
from Bulbapedia's party blocks for the game each region follows, and written as a "movesets" field
(by species id) on each trainer. moves.ensure_moves uses them; moves this game can't use are skipped.

Run from the game folder:  python dev/builders/build_canon_movesets.py dev/builders
Pages are cached in dev/builders/bulbapedia_cache/ (re-runs don't download again). Safe to re-run.
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, sys.argv[1])
from textjson import TextJSON  # noqa: E402

CACHE = os.path.join(sys.argv[1], "bulbapedia_cache")
os.makedirs(CACHE, exist_ok=True)

# The games each region's teams follow (first = preferred).
GAMES = {"KANTO": ["FRLG", "RGB", "Yellow", "Y"], "JOHTO": ["HGSS", "hgss", "GSC"],
         "HOENN": ["E", "RSE", "RS", "Ru", "Sa", "ORAS", "OR", "AS"], "SINNOH": ["Pt", "DP", "BDSP"],
         "UNOVA": ["BW", "Bl", "Black and White", "B2W2"], "KALOS": ["XY"],
         "ALOLA": ["USUM", "US", "UM", "SM", "SMUSUM", "MUM"], "GALAR": ["SwSh", "Sw", "Sh"],
         "PALDEA": ["SV", "Sc"], "ORRE": ["Colo", "XD"]}
IMPORTANT = {"GYM_LEADER", "ELITE_FOUR", "CHAMPION", "RIVAL", "BOSS", "ROCKET_LEADER", "BB_CHAMPION",
             "BB_ELITE_FOUR", "TOURNAMENT_CHAMPION", "CIPHER_BOSS", "CIPHER_ADMIN"}
# Our trainer name -> Bulbapedia page(s).
PAGES = {"Lt. Surge": ["Lt. Surge"], "Tate & Liza": ["Tate and Liza"], "Crasher Wake": ["Crasher Wake"],
         "Trio (Cilan / Chili / Cress)": ["Cilan", "Chili", "Cress"],
         "Bea (Fighting) / Allister (Ghost)": ["Bea", "Allister"], "Gordie (Rock) / Melony (Ice)": ["Gordie", "Melony"],
         "Professor Kukui (The Royal Mask)": ["Kukui"], "Lorekeeper Zinnia": ["Zinnia"],
         "Aqua Leader Archie": ["Archie"], "Magma Leader Maxie": ["Maxie"], "Admin Courtney": ["Courtney"],
         "Aqua Admin Matt": ["Matt"], "Steven Stone": ["Steven Stone"], "Steven": ["Steven Stone"],
         "Executive Ariana": ["Ariana"], "Chairman Rose": ["Rose"], "Professor Sada": ["Sada"],
         "{rival_name}": ["Silver (game)"], "Silver": ["Silver (game)"], "Rival": ["Brendan (game)", "May (game)"],
         "Wally": ["Wally"], "Team Leader": [], "Cipher Head Evice": ["Evice"], "Grand Master Greevil": ["Greevil"],
         "Miror B.": ["Miror B."],
         "Champion": ["Blue (game)"], "Lance": ["Lance"], "Koga": ["Koga"]}
# Teams picked in code by the player's starter: every species they can have.
EXTRA_SPECIES = {("KANTO", "Champion"): [18, 65, 112, 103, 130, 59, 6, 3, 9]}
STRIP = re.compile(r"^(Elite Four|Champion|Leader|Gym Leader|Cipher Admin|Cipher Cmdr|Cipher Head)\s+|\s*\(.*\)$")
ALIASES = {"VISE-GRIP": "VICE-GRIP", "SOLARBEAM": "SOLAR-BEAM", "HI-JUMP-KICK": "HIGH-JUMP-KICK",
           "FAINT-ATTACK": "FEINT-ATTACK", "SMELLINGSALT": "SMELLING-SALTS", "THUNDERPUNCH": "THUNDER-PUNCH",
           "THUNDERSHOCK": "THUNDER-SHOCK", "DOUBLESLAP": "DOUBLE-SLAP", "SELFDESTRUCT": "SELF-DESTRUCT",
           "DYNAMICPUNCH": "DYNAMIC-PUNCH", "EXTREMESPEED": "EXTREME-SPEED", "ANCIENTPOWER": "ANCIENT-POWER"}


def page_names(name, cls):
    if name in PAGES:
        return PAGES[name]
    if cls == "CHAMPION" and name == "Champion":
        return ["Blue (game)"]
    return [STRIP.sub("", name).strip()]


def fetch(title):
    path = os.path.join(CACHE, re.sub(r"[^A-Za-z0-9_.-]", "_", title) + ".txt")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    text = ""
    for _ in range(3):  # follow #REDIRECTs
        url = "https://bulbapedia.bulbagarden.net/w/index.php?" + urllib.parse.urlencode(
            {"title": title.replace(" ", "_"), "action": "raw"})
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (KantoMathGame movesets builder)"})
        try:
            text = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
        except Exception as e:
            print("  fetch failed:", title, e)
            return ""
        time.sleep(1.0)
        m = re.match(r"#REDIRECT\s*\[\[([^\]#|]+)", text, re.I)
        if not m:
            break
        title = m.group(1)
    open(path, "w", encoding="utf-8").write(text)
    return text


def norm_move(name):
    m = name.strip().upper().replace("'", "").replace(" ", "-").replace(".", "")
    return ALIASES.get(m, m)


def blocks(text):
    """[(game, [(ndex, [moves])])] for each {{Party}} ... {{Party/end}} block."""
    out = []
    for chunk in re.split(r"\{\{Party\s*\n", text)[1:]:
        chunk = chunk.split("{{Party/end}}")[0]
        g = re.search(r"\|\s*game\s*=\s*([^\n|}]+)", chunk)
        game = g.group(1).strip() if g else ""
        mons = []
        for mon in re.split(r"\{\{Pokémon(?:/\d)?\s*\n", chunk)[1:]:
            n = re.search(r"\|\s*ndex\s*=\s*(\d+)", mon)
            if not n:
                continue
            moves = [norm_move(x) for _, x in sorted(re.findall(r"\|\s*move(\d)\s*=\s*([^|\n}]+)", mon))]
            mons.append((int(n.group(1)), [m for m in moves if m]))
        if mons:
            out.append((game, mons))
    return out


def species(pid, form_map):
    pid = int(pid)
    return int((form_map.get(str(pid)) or {}).get("id", pid)) if pid >= 2000 else pid


def best_sets(pages, region, team_ids, form_map):
    """{our id: moves} from the best-matching party blocks of the region's games."""
    prefs = GAMES.get(region, [])
    cands = []
    for title in pages:
        for game, mons in blocks(fetch(title)):
            if game not in prefs:
                continue
            want = {species(t, form_map) for t in team_ids}
            overlap = len(want & {n for n, _ in mons})
            cands.append((overlap * 10 - prefs.index(game), mons))
    cands.sort(key=lambda c: -c[0])
    sets = {}
    for tid in team_ids:
        sp = species(tid, form_map)
        for score, mons in cands:
            if score < 10:
                break
            hit = next((mv for n, mv in mons if n == sp and mv), None)
            if hit:
                sets[str(tid)] = hit
                break
    return sets


def walk(obj, path, out):
    if isinstance(obj, dict):
        if isinstance(obj.get("team"), list) and ("class" in obj or "name" in obj):
            out.append((path, obj))
        for k, v in obj.items():
            walk(v, path + [k], out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, path + [i], out)


all_maps = {}
for f in os.listdir("assets"):
    if f.endswith("_area_data.json"):
        all_maps.update(json.load(open(f"assets/{f}", encoding="utf-8")).get("FORM_MAP", {}))

total = 0
for fname in sorted(os.listdir("assets")):
    if not fname.endswith("_area_data.json"):
        continue
    t = TextJSON(f"assets/{fname}")
    sp = t.data()["STORY_PROGRESSION"]
    dirty = set()
    for area, a in sp.items():
        region = str(a.get("region") or "KANTO").upper()
        found = []
        walk(a, [], found)
        for path, tr in found:
            cls = tr.get("class") or ""
            leader = path[-2:] == ["gym", "leader"] if len(path) >= 2 else False
            if cls not in IMPORTANT and not leader:
                continue
            pages = page_names(str(tr.get("name") or ""), cls)
            if not pages:
                continue
            team = list(tr.get("team") or []) + [x for c in (tr.get("team_choice") or {}).values() for x in c]
            team += EXTRA_SPECIES.get((region, str(tr.get("name"))), [])
            sets = best_sets(pages, region, team, all_maps)
            changed = bool(sets and sets != tr.get("movesets"))
            if changed:
                tr["movesets"] = sets
                dirty.add(path[0])
                total += 1
            rm = tr.get("rematch")
            if isinstance(rm, dict) and rm.get("team"):
                rsets = best_sets(pages, region, rm["team"], all_maps)
                if rsets and rsets != rm.get("movesets"):
                    rm["movesets"] = rsets
                    dirty.add(path[0])
            print(f"{'*' if changed else ' '}{fname[:10]:10} {area:26} {tr.get('name')!s:32} {len(sets)}/{len(set(map(str, team)))} species")
        for key in dirty:
            t.set(area, key, a[key])
        dirty.clear()
    t.save()
print("trainers with canon movesets:", total)
