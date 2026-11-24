# Kanto + Sevii's overworld looks (11-23, Jordan: "are there any missing assets in kanto/sevii? overworld trainer sprites
# that show as the battle sprite? overworld pokemon sprites?"). Every person, trainer and Pokemon standing on every Kanto
# and Sevii map (dev/builders/town_maps/firered.py KANTO), looked up the way the game draws them
# (src/states/overworld/dungeon.py _trainer_img / _figure_img / region_sheet_paths, the town maps' _figure_img too):
#   - a trainer on a route or in a cave: its "sprite" must have an overworld sheet (dungeon_sprites.json trainers_KANTO /
#     trainers), else the map draws the BATTLE PORTRAIT;
#   - a person in a town or a room: its own sheet ("AREA:name" figures), else the stock townsperson;
#   - a Pokemon (a boss, a legend, someone who is a Pokemon, a "mon:" look): its following-Pokemon sheet, else its PARTY
#     ICON;
#   - every sheet named must exist in assets/dungeon/characters.
#        bash dev/checks/run.sh kanto_looks
import json, os, collections
from src.states.overworld import dungeon as dn

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True
story.starting_region = "KANTO"
_fr = {}
exec(open("dev/builders/town_maps/firered.py", encoding="utf-8").read(), _fr)
KEYS = sorted(_fr["KANTO"])
TM = json.load(open("assets/town_maps.json", encoding="utf-8"))
AREAS = g.loader.area_data["STORY_PROGRESSION"]
SM = dn.sprite_map(g)
CH = os.path.join(g.assets.assets_dir, "dungeon", "characters")
OWN = dict(SM.get("trainers") or {}); OWN.update(SM.get("trainers_KANTO") or {})
FIG = SM.get("figures") or {}
story.current_area_key = "PALLET_TOWN"   # (Kanto's own sheets first, as in the game)


class _P:
    def __init__(self, pid):
        self.id, self.form, self.gender = int(pid), "normal", None


def has_follower(pid):
    return any(os.path.isfile(p) for p in dn.region_sheet_paths(g, dn.follower_names(g, _P(pid))))


def sheet_ok(name):
    return bool(name) and os.path.isfile(os.path.join(CH, name))


portrait, stock, icons, missing = collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(list)
counted = collections.Counter()


def person(area, text, opt=None):
    """A person or thing in a town / room / on a route as a figure: how it's drawn."""
    opt = opt or {}
    spec = FIG.get(f"{area}:{text}") or {}
    counted["people"] += 1
    if spec.get("item") or spec.get("pic") or spec.get("draw"):
        return
    if str(text).startswith(("door:",)) or str(opt.get("_look") or "").endswith("item_ball.png"):
        return
    pid = spec.get("pokemon")
    if pid is None and str(spec.get("sheet") or "").startswith("mon:"):
        pid = int(str(spec["sheet"])[4:])
    if pid is None and opt.get("action") == "BOSS" and not spec.get("sheet"):
        pid = (opt.get("boss") or AREAS.get(area, {}).get("area_boss") or {}).get("id")
    if pid is None:
        pid = dn.species_named(g, text)
    if pid is not None:
        counted["pokemon"] += 1
        if not has_follower(pid):
            icons[area].append(f"{text} (#{pid})")
        return
    sh = dn.scene_sheet(g, spec.get("sheet")) if spec.get("sheet") else None
    if sh:
        if not sheet_ok(sh):
            missing[area].append(f"{text}: {sh}")
        return
    if opt.get("event", {}).get("battle") or opt.get("action") in ("EVENT", "NPC", None) or True:
        stock[area].append(text)


def trainer(area, t):
    counted["trainers"] += 1
    name = t.get("sprite") or "rival.png"
    if name in ("{rival_character}",) or "{" in name:
        return
    sh = OWN.get(name)
    if not sh:
        portrait[area].append(f"{t.get('name')} ({name})")
    elif not sheet_ok(sh):
        missing[area].append(f"{t.get('name')}: {sh}")


def people_of(m):
    out = []
    def take(p):
        if isinstance(p, str):
            out.append((p, {}))
        elif isinstance(p, dict):
            if "any" in p:
                for q in p["any"]:
                    take(q)
            else:
                out.append((p.get("text"), p))
    for p in m.get("people") or []:
        take(p)
    for r in (m.get("rooms") or {}).values():
        for p in r.get("people") or []:
            take(p)
    for f in m.get("floors") or []:
        for p in f.get("people") or []:
            take(p)
    for sm_ in m.get("story_maps") or []:
        for p in (sm_.get("map") or {}).get("people") or []:
            take(p)
    return out


for k in KEYS:
    m, a = TM.get(k) or {}, AREAS.get(k) or {}
    opts = {o.get("text"): o for o in (a.get("explore_options") or []) + (a.get("route_menu") or []) + (a.get("travel_options") or []) if isinstance(o, dict)}
    seen = set()
    for text, p in people_of(m):
        if not text or (text in seen and not p):
            continue
        seen.add(text)
        o = opts.get(text) or p
        if o.get("action") in ("EXIT", "TRAVEL", "CATCH", "BATTLE", "TRAINER", "FISH", "HEADBUTT", "HEAL", "SHOP", "CENTER", "GYM", "LEAGUE") and not p.get("event"):
            continue
        if (o.get("event") or {}).get("battle") and (o.get("event") or {}).get("battle", {}).get("sprite") and not FIG.get(f"{k}:{text}"):
            trainer(k, dict(o["event"]["battle"], name=text))   # (a trainer standing in a town: drawn as a figure, by its own look)
            continue
        person(k, text, o)
    if a.get("area_type") != "town":
        for t in a.get("trainer_pool") or []:
            trainer(k, t)
        for o in a.get("route_menu") or []:   # (figures on a route's map: bosses, story people, things to pick)
            if o.get("action") in dn.FIGURE_ACTIONS and o.get("text") not in seen and not o.get("found"):
                seen.add(o.get("text"))
                person(k, o.get("text"), o)
    for part in [m] + list((m.get("rooms") or {}).values()) + list(m.get("floors") or []):
        for b in part.get("barred") or []:   # (a Pokemon or person standing in the way: "mon:79", "sheet:...")
            look = str(b.get("look") or "")
            if look.startswith("mon:"):
                counted["pokemon"] += 1
                if not has_follower(int(look[4:].split(":")[0])):
                    icons[k].append(f"barred {b.get('tiles', [[None]])[0]} (#{look[4:]})")
            elif look.startswith("sheet:") and not sheet_ok(look[6:]):
                missing[k].append(f"barred look {look[6:]}")

print(f"Kanto + Sevii: {len(KEYS)} maps; {counted['trainers']} trainers, {counted['people']} people and things, {counted['pokemon']} Pokemon looked up")
print("\n1) trainers drawn on the map with their BATTLE PORTRAIT (no overworld sheet for their sprite):")
_by = collections.Counter(x.split("(")[-1].rstrip(")") for v in portrait.values() for x in v)
for k, v in sorted(portrait.items()):
    print(f"   {k}: {len(v)}: {', '.join(v[:6])}{' ...' if len(v) > 6 else ''}")
print(f"   by picture: {dict(_by.most_common())}")
check(not portrait, f"no trainer stands on a Kanto/Sevii map as its battle portrait ({sum(len(v) for v in portrait.values())} do)")
print("\n2) Pokemon on the maps drawn with their PARTY ICON (no following-Pokemon sheet):")
for k, v in sorted(icons.items()):
    print(f"   {k}: {', '.join(v)}")
check(not icons, f"every Pokemon on a Kanto/Sevii map has its following-Pokemon sheet ({sum(len(v) for v in icons.values())} don't)")
print("\n3) sheets named but missing from assets/dungeon/characters:")
for k, v in sorted(missing.items()):
    print(f"   {k}: {', '.join(v)}")
check(not missing, f"every sheet named for a Kanto/Sevii person exists ({sum(len(v) for v in missing.values())} missing)")
print("\n4) people with no look of their own (drawn as the stock townsperson):")
for k, v in sorted(stock.items()):
    print(f"   {k}: {len(v)}: {', '.join(map(str, v[:8]))}{' ...' if len(v) > 8 else ''}")
print(f"   ({sum(len(v) for v in stock.values())} in all: listed, not failed - some are things, not people)")

print(f"##### {len(fails)} failures")
for m in fails:
    print("   FAIL " + m)
