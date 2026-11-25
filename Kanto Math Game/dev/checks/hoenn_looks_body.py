# Hoenn's overworld looks and battle portraits (11-24, Dev Map clean-hoenn-portraits-looks; Johto's johto_looks made Hoenn's):
# every person, trainer and Pokemon standing on every Hoenn map (dev/builders/town_maps/emerald.py HOENN), looked up the way
# the game draws them:
#   - a trainer on a route or in a cave: its "sprite" must have an overworld sheet (dungeon_sprites.json trainers_HOENN /
#     trainers), else the map draws the BATTLE PORTRAIT;
#   - a person in a town or a room: its own sheet ("AREA:name" figures), else the stock townsperson;
#   - a Pokemon (a boss, a legend, someone who is a Pokemon, a "mon:" look): its following-Pokemon sheet, else its PARTY ICON;
#   - every sheet named must exist in assets/dungeon/characters;
#   - battle portraits: Emerald's own (assets/sprites/trainers/em_tp_*.png, hoenn_rom_tools/em_trainer_pics.py, h_portraits.py).
#        bash dev/checks/run.sh hoenn_looks
import json, os, collections
_ev = lambda o: o.get("event") if isinstance(o.get("event"), dict) else {}   # (Hoenn names some events by a string: story_events.py)
from src.states.overworld import dungeon as dn

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True
story.starting_region = "HOENN"
_ho = {}
exec(open("dev/builders/town_maps/emerald.py", encoding="utf-8").read(), _ho)
KEYS = sorted(_ho["HOENN"])
TM = json.load(open("assets/town_maps.json", encoding="utf-8"))
AREAS = g.loader.area_data["STORY_PROGRESSION"]
SM = dn.sprite_map(g)
CH = os.path.join(g.assets.assets_dir, "dungeon", "characters")
OWN = dict(SM.get("trainers") or {}); OWN.update(SM.get("trainers_HOENN") or {})
FIG = SM.get("figures") or {}
story.current_area_key = "LITTLEROOT_TOWN"


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
    if _ev(opt).get("battle") or opt.get("action") in ("EVENT", "NPC", None) or True:
        stock[area].append(text)


exec(open("dev/checks/looks_lib.py", encoding="utf-8").read())   # (people_of, trainer: shared, Checks C5)


for k in KEYS:
    m, a = TM.get(k) or {}, AREAS.get(k) or {}
    opts = {o.get("text"): o for o in (a.get("explore_options") or []) + (a.get("route_menu") or []) + (a.get("travel_options") or []) if isinstance(o, dict)}
    seen = set()
    for text, p in people_of(m):
        if not text or (text in seen and not p):
            continue
        seen.add(text)
        o = opts.get(text) or p
        if o.get("action") in ("EXIT", "TRAVEL", "CATCH", "BATTLE", "TRAINER", "FISH", "HEADBUTT", "HEAL", "SHOP", "CENTER", "GYM", "LEAGUE") and not _ev(p):
            continue
        if _ev(o).get("battle") and _ev(o)["battle"].get("sprite") and not FIG.get(f"{k}:{text}"):
            trainer(k, dict(_ev(o)["battle"], name=text))   # (a trainer standing in a town: drawn as a figure, by its own look)
            continue
        person(k, text, o)
    if a.get("area_type") != "town":
        for t in a.get("trainer_pool") or []:
            if not (t.get("villain") or t.get("villain_by_version")):   # (dressed per version at load: hoenn.py VERSIONS)
                trainer(k, t)
        for o in a.get("route_menu") or []:   # (figures on a route's map: bosses, story people, things to pick)
            if o.get("action") in dn.FIGURE_ACTIONS and o.get("text") not in seen and not o.get("found") and not o.get("not_on_map"):
                seen.add(o.get("text"))
                person(k, o.get("text"), o)
    for part in [m] + list((m.get("rooms") or {}).values()) + list(m.get("floors") or []):
        for b in part.get("barred") or []:   # (a Pokemon or person standing in the way: "mon:79", "sheet:...")
            look = str(b.get("look") or "")
            if look.startswith("mon:"):
                counted["pokemon"] += 1
                if not has_follower(int(look[4:].split(":")[0])):
                    icons[k].append(f"barred {b.get('tiles', [[None]])[0]} (#{look[4:]})")
            elif look.startswith("sheet:") and not sheet_ok(dn.scene_sheet(g, look[6:]) if look[6:].startswith("@") else look[6:]):
                missing[k].append(f"barred look {look[6:]}")   # ("@grunt", "@legend_primal": the version's own, resolved as the game does)

print(f"Hoenn: {len(KEYS)} maps; {counted['trainers']} trainers, {counted['people']} people and things, {counted['pokemon']} Pokemon looked up")
print("\n1) trainers drawn on the map with their BATTLE PORTRAIT (no overworld sheet for their sprite):")
_by = collections.Counter(x.split("(")[-1].rstrip(")") for v in portrait.values() for x in v)
for k, v in sorted(portrait.items()):
    print(f"   {k}: {len(v)}: {', '.join(v[:6])}{' ...' if len(v) > 6 else ''}")
print(f"   by picture: {dict(_by.most_common())}")
_wait = {"Lorekeeper Zinnia (zinnia.png)", "BATTLE ZINNIA"}   # (Zinnia: no overworld art yet - questions/HOENN.md #7, Jordan is looking)
portrait = {k: [x for x in v if x not in _wait] for k, v in portrait.items() if [x for x in v if x not in _wait]}
stock = {k: [x for x in v if x not in _wait] for k, v in stock.items() if [x for x in v if x not in _wait]}
check(not portrait, f"no trainer stands on a Hoenn map as its battle portrait ({sum(len(v) for v in portrait.values())} do; Zinnia waits for art)")
print("\n2) Pokemon on the maps drawn with their PARTY ICON (no following-Pokemon sheet):")
for k, v in sorted(icons.items()):
    print(f"   {k}: {', '.join(v)}")
check(not icons, f"every Pokemon on a Hoenn map has its following-Pokemon sheet ({sum(len(v) for v in icons.values())} don't)")
print("\n3) sheets named but missing from assets/dungeon/characters:")
for k, v in sorted(missing.items()):
    print(f"   {k}: {', '.join(v)}")
check(not missing, f"every sheet named for a Hoenn person exists ({sum(len(v) for v in missing.values())} missing)")
print("\n4) people with no look of their own (drawn as the stock townsperson):")
for k, v in sorted(stock.items()):
    print(f"   {k}: {len(v)}: {', '.join(map(str, v[:8]))}{' ...' if len(v) > 8 else ''}")
check(not stock, f"every Hoenn person or thing on a map has its own look: Emerald's sprite, an item, a Pokemon, or none for a spot to look at ({sum(len(v) for v in stock.values())} drawn as the stock townsperson)")

print("\n5) battle portraits: Emerald's own (assets/sprites/trainers/em_tp_*.png); ORAS-only people keep theirs; villains by version")
_bp = collections.Counter()
def _walk_tr(o):
    if isinstance(o, dict):
        if isinstance(o.get("sprite"), str) and ("team" in o or "class" in o) and not (o.get("villain") or o.get("villain_by_version")):
            _bp[o["sprite"]] += 1
        for v in o.values():
            _walk_tr(v)
    elif isinstance(o, list):
        for v in o:
            _walk_tr(v)
_hd = json.load(open("assets/hoenn_area_data.json", encoding="utf-8"))
_walk_tr({k: v for k, v in _hd["STORY_PROGRESSION"].items() if isinstance(v, dict) and v.get("region") == "HOENN"})
_walk_tr(json.load(open("assets/hoenn_oras.json", encoding="utf-8")).get("AREAS", {}))
_kept = {"steven.png", "zinnia.png", "courtney.png", "tate_liza.png", "ranger_m.png", "biker.png", "school_kid_f.png", "{rival_character}"}
_other = {k: v for k, v in _bp.items() if not k.startswith("em_tp_") and k not in _kept}
_gone = [k for k in _bp if "{" not in k and not os.path.isfile(os.path.join(g.assets.assets_dir, "sprites", "trainers", k))]
check(not _other and not _gone, f"every Hoenn trainer battles with Emerald's picture ({sum(v for k, v in _bp.items() if k.startswith('em_tp_'))} do; others {_other}; missing files {_gone})")
from src.world import hoenn as _hn
_vs = [v[k] if isinstance(v[k], str) else v[k][1] for v in _hn.VERSIONS.values() for k in ("grunt_sprite", "leader_sprite", "admin_a", "admin_b")]
check(all(os.path.isfile(os.path.join(g.assets.assets_dir, "sprites", "trainers", f)) for f in _vs) and sum(f.startswith("em_tp_") for f in _vs) == 7,
      f"the villains' pictures by version: Emerald's (Courtney, ORAS's own, keeps hers) {_vs}")

print(f"##### {len(fails)} failures")
for m in fails:
    print("   FAIL " + m)
