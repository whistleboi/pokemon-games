# Orange Islands events PLAYED on their maps (11-23, batch O4; AUDIT_GUIDE step 8): walk up to whoever it is, talk, tap
# through, pick, fight; then look at what you got. The data side is checked by orange_canon / orange_maps; this is the
# player's side. Helpers (play, meet, place, team, ace) copied from kanto_events_body.py.
#   bash dev/checks/run_par.sh orange_events
import json, os
from src.states.overworld import PlayState, CityState as _CS
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.dungeon import core
from src.pokemon import moves as _mv

fails = 0
g.dungeon_routes = True
g.walk_towns = True
g.player_character = "red"   # (any look will do)
said = []


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def frames(n=1):
    for _ in range(n):
        g.current_state.update()
        g.current_state.draw()


def _note(st):
    box = getattr(st, "npc_dialogue", None) if getattr(st, "npc_active", False) else getattr(st, "dialogue_box", None)
    if box is not None and getattr(box, "visible", True):
        for line in getattr(box, "text_lines", []) or []:
            if not said or said[-1] != line:
                said.append(line)


exec(open("dev/checks/events_lib.py", encoding="utf-8").read())   # (meet, play, _fight, route: shared, Checks C5)


def town(area, came, room=None):
    g.walk_town_pos = g.walk_town_exit = g.walk_town_room = None
    story.current_area_key, story.last_area_key = area, came
    t = _CS(g); g.change_state(t); frames(2); play()
    if room:
        t._go(room, ""); frames(2)
    return t


def place(area, came):
    """Open an area the way the game does: a town's walking map, or a route's."""
    a = g.loader.area_data["STORY_PROGRESSION"].get(area, {})
    return town(area, came) if a.get("area_type") == "town" else route(area, came)


def team(*ids, level=50):
    story.player_team = [mk(i) for i in ids]
    for p in story.player_team:
        p.level = level
        p.heal_full()
    return story.player_team


def ace():
    """A team that wins (as kanto_maps' Mewtwo): Lv 100, Psychic and Ice Beam."""
    a = mk(150); a.level = 100; a.moves = ["PSYCHIC", "ICE-BEAM"]; a.heal_full()
    story.player_team = [a]
    return a


# ---------------------------------------------------------------- Orange (11-23, batch O4; AUDIT_GUIDE step 8)
from src.pokemon import tms as _tmsmod
story.enter_region("ORANGE") if hasattr(story, "enter_region") else None
_P = g.loader.area_data["STORY_PROGRESSION"]
_DEX = g.loader.area_data["REGION_START"]["ORANGE"]["dex_list"]
_flags0, _inv0, _team0, _money0 = dict(story.story_flags), dict(story.inventory), list(story.player_team), story.money
story.balls_left = 20


_TM = json.load(open("assets/town_maps.json", encoding="utf-8"))
story.story_flags["received_starter_orange"] = True


def _scenes_seen(area):
    """A player who comes back to a place has seen its story scenes: mark the map's scenes (and its rooms' and floors')
    as played, so none holds you on arrival (the test starts from a fresh Orange save)."""
    m = _TM.get(area) or {}
    parts = [m] + list(m.get("floors") or []) + list((m.get("rooms") or {}).values())
    for part in parts:
        for sc in part.get("scenes") or []:
            if sc.get("flag"):
                story.story_flags[sc["flag"]] = True


_place = place


def place(area, came):
    _scenes_seen(area)
    return _place(area, came)


def _came(area):
    """A neighbour to arrive from: the first area the map's own exits name (else Valencia)."""
    m = json.load(open("assets/town_maps.json", encoding="utf-8")).get(area) or {}
    for f in (m.get("floors") or [m]):
        for v in (f.get("exits") or {}).values():
            v = str(v)
            if v and not v.startswith(("OUT", "ROOM")) and v in _P:
                return v
    return "VALENCIA_ISLAND"


_meet = meet


def meet(st, text, picks=(), n=3000):
    """As kanto_events' meet, tried again when nothing was said (a Feat pop-up on arrival can swallow the first step)."""
    for _ in range(3):
        w = _meet(g.current_state if g.current_state is not st and type(g.current_state) is type(st) else st, text, picks, n)
        if w:
            return w
    return w


def _learner(move):
    """A young Pokemon from Orange's dex that can learn this move and doesn't know it yet."""
    tm = _tmsmod.key_for_move(g, move)
    for pid in _DEX:
        p = mk(pid); p.level = 5
        if tm and _tmsmod.can_learn(g, p, tm) and move not in _mv.move_pool(g, p):
            return pid
    return None


print("1) 5.7's twelve move tutors: walk up, LEARN IT NOW, and the move is learned (each sells its TM too: orange suite 6b)")
TUTORS = [("ORANGE_ROUTE_62", "Swimmer", "WATERFALL"), ("ASCORBIA_ISLAND", "Body Slam kid", "BODY-SLAM"),
          ("BUTWAL_ISLAND", "Rock Slide hiker", "ROCK-SLIDE"), ("KUMQUAT_ISLAND", "Swords Dance man", "SWORDS-DANCE"),
          ("PUMMELO_ISLAND", "Dragon Dance tutor", "DRAGON-DANCE"), ("PUMMELO_ISLAND", "Seismic Toss tutor", "SEISMIC-TOSS"),
          ("PUMMELO_ISLAND", "Substitute tutor", "SUBSTITUTE"), ("PUMMELO_ISLAND", "Double-Edge tutor", "DOUBLE-EDGE"),
          ("PUMMELO_ISLAND", "Crunch tutor", "CRUNCH"), ("ORANGE_ROUTE_70", "Mega Punch man", "MEGA-PUNCH"),
          ("ORANGE_ROUTE_70", "Mega Kick man", "MEGA-KICK"), ("TROVITOPOLIS_SEWERS", "Sewer man", "THUNDER-WAVE")]
for area, who, move in TUTORS:
    for fl in [k for k in list(story.story_flags) if k.startswith("orange_tutor_") or k.startswith("bp_tutor_")]:
        story.story_flags.pop(fl, None)
    pid = _learner(move)
    team(pid or 25, level=5)
    story.money = 99999
    st = place(area, _came(area))
    w = meet(st, who, picks=["teach", True, True])
    got = move in _mv.move_pool(g, story.player_team[0])
    check(pid is not None and w is not None and got,
          f"{area}: the {who} teaches {move} to #{pid} ({(w or [])[:1]}, {getattr(story.player_team[0], 'moves', None)})")

print("2) The six Orange trades (5.7's own), each from its trader, holding 5.7's item")
TRADES = [("NAVEL_ISLAND", "Trader", 124, 126, "CHARCOAL"), ("YAMBERA", "Trader", 81, 100, "BRIGHT_POWDER"),
          ("ORANGE_ROUTE_64", "Trader", 115, 113, "LUCKY_PUNCH"), ("SHAMOUTI_ISLAND", "Trader", 85, 26, "FOCUS_BAND"),
          ("TARROCO_ISLAND", "Trader", 105, 82, "METAL_COAT"), ("TARROCO_ISLAND", "Girl", 39, 35, "LUCKY_EGG")]
for area, who, want, give, item in TRADES:
    ev = next((o for k in ("explore_options", "route_menu") for o in _P[area].get(k, []) if o.get("text") == who and (o.get("event") or {}).get("trade")), None)
    fl = (ev or {}).get("event", {}).get("flag")
    if fl:
        story.story_flags.pop(fl, None)
    team(25, want, level=20)
    st = place(area, _came(area))
    w = meet(st, who, picks=[want, True, True])
    ids = [p.id for p in story.player_team]
    new = next((p for p in story.player_team if p.id == give), None)
    check(new is not None and want not in ids and getattr(new, "held_item", None) == item,
          f"{area}: {who} - your #{want} for #{give} holding {item} ({(w or [])[:1]}, {ids}, {getattr(new, 'held_item', None)})")
    _after = next((o for k in ("explore_options", "route_menu") for o in _P[area].get(k, []) if o.get("text") == who + " "), None)
    _line = ((_after or {}).get("event") or {}).get("lines", [""])[0] or ((ev or {}).get("event", {}).get("done") or [""])[0]
    w2 = meet(place(area, _came(area)), who + " ") or meet(place(area, _came(area)), who)
    check(bool(_line) and any(_line[:30] in l for l in (w2 or [])),
          f"...and talked to again, the {who} says the after-trade line (11-23: Navel, Yambera, Route 64 had lost it) ({(w2 or [])[:1]})")

print("3) Gifts from people: talk, and the item is in the Bag (once)")
GIFTS = [("VALENCIA_ISLAND", "Old Rod fisherman", "OLD_ROD", {}), ("KINNOW_ISLAND", "Fisherman", "GOOD_ROD", {}),
         ("TROVITA_ISLAND", "Fisherman", "SUPER_ROD", {}), ("TANGELO_JUNGLE", "Collector", "MIRACLE_SEED", {"orange_parachuted": True}),
         ("SUNBURST_ISLAND", "Brick Break man", "TM058", {}), ("MANDARIN_NORTH", "Climber", "CLIMB_KIT", {"orange_mandarin_cleared": True}),
         ("KINNOW_ISLAND", "Growlithe's owner", "TM172", {}), ("KUMQUAT_ISLAND", "Iron Tail man", "TM265", {}),
         ("KUMQUAT_ISLAND", "Return boy", "TM274", {}), ("KUMQUAT_ISLAND", "Frustration girl", "TM273", {}),
         ("SHAMOUTI_ISLAND", "Kindler", "TM157", {}), ("PUMMELO_ISLAND", "Dragon Tamer", "TM078", {})]
for area, who, item, need in GIFTS:
    ev = next((o for k in ("explore_options", "route_menu") for o in _P[area].get(k, []) if o.get("text") == who), None)
    fl = (ev or {}).get("event", {}).get("flag")
    if fl:
        story.story_flags.pop(fl, None)
    story.inventory.pop(item, None)
    story.story_flags.update(need)
    ace()
    st = place(area, _came(area))
    w = meet(st, who, picks=[True, True])
    once = story.inventory.get(item, 0)
    w2 = meet(place(area, _came(area)), who, picks=[True, True])
    check(once == 1 and story.inventory.get(item, 0) == 1 and (not fl or story.story_flags.get(fl)),
          f"{area}: the {who} gives {item}, and only once ({(w or [])[:1]}, again: {(w2 or [])[:1]})")

print("4) Trovitopolis's roof: the Egg seller sells an Egg for $2,000")
story.story_flags.pop("orange_roof_egg_last", None)
team(25)
story.money = 5000
st = place("TROVITOPOLIS", _came("TROVITOPOLIS"))
st._go("roof", "") if hasattr(st, "_go") and "roof" in (st.town_map.get("rooms") or {}) else None
frames(2)
w = meet(st, "Egg seller", picks=[175, True, True])
egg = story.player_team[-1] if len(story.player_team) > 1 else None
check(egg is not None and egg.id == 175 and story.money == 3000,
      f"...pick Togepi, pay $2,000, and an Egg joins you ({(w or [])[:1]}, {egg and egg.id}, ${story.money})")

print("5) An item on the ground: walk to it and pick it up (Crystal Cave's Hard Stone)")
story.story_flags.pop("got_hard_stone_crystal_cave", None)
story.inventory.pop("HARD_STONE", None)
st = place("CRYSTAL_CAVE", "SUNBURST_ISLAND")
w = meet(st, "HARD STONE")
check(story.inventory.get("HARD_STONE") == 1, f"...the Hard Stone is in the Bag ({w})")

print("6) The Orange League's Hall of Fame: the team one by one, the record kept as Orange's (5.7: FireRed's machine)")
from src.states.hall_of_fame import HallOfFameState, records as _hof_records
story.player_team = [mk(i) for i in (131, 25, 143)]
_n0 = len(_hof_records(g))
_out = []
_hs = HallOfFameState(g, "ORANGE", lambda ls: _out.extend(ls + ["(done)"]))
g.current_state = _hs
for _ in range(4000):
    if _out:
        break
    _hs.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
    _hs.update(); _hs.draw()
_rec = _hof_records(g)[-1] if len(_hof_records(g)) > _n0 else {}
check(_out[-1:] == ["(done)"] and _rec.get("region") == "ORANGE" and [m["id"] for m in _rec.get("team", [])] == [131, 25, 143],
      f"...Lapras, Pikachu, Snorlax shown and saved as an Orange League win ({_rec.get('region')}, {len(_rec.get('team', []))})")

print("7) Orange's own music (5.7's songs, rendered by omusic.py): the island's theme, a Center's, the battles")
from src.core.music import MusicManager, REGION_MUSIC
REGION_MUSIC.clear()
_mm = getattr(g, "music", None) or MusicManager(g)
_t = place("VALENCIA_ISLAND", "VALENCIA_PARK")
_town = _mm.region_track("town", "ORANGE")
_t._go("center", ""); frames(2)
_cen = _mm.region_track("town", "ORANGE")
_kinds = {k: _mm.region_track(k, "ORANGE") for k in ("wild", "trainer", "gym", "final", "victory")}
_b = lambda p: os.path.basename(p) if p else None
check(_b(_town) == "oi_314.ogg" and _b(_cen) == "oi_303.ogg" and all(_kinds.values()),
      f"...Valencia plays 5.7's town theme, its Center the Center theme, and every battle kind has its track ({_b(_town)}, {_b(_cen)}, {[_b(v) for v in _kinds.values()]})")

print("8) Journeys (Jordan 11-24): Professor Oak's errand - Ivy hands over the GS Ball, and it goes with you to Johto")
for _f in ("orange_ivy_met", "received_starter_orange", "orange_lab_done", "orange_park_done", "orange_ivy_thanks", "oak_gs_errand"):
    story.story_flags[_f] = True
story.story_flags.pop("got_gs_ball_ivy", None); story.inventory.pop("GS_BALL", None)
_t = place("VALENCIA_ISLAND", "VALENCIA_PARK")
story.story_flags.pop("got_gs_ball_ivy", None)
said.clear(); _t._go("lab", ""); frames(2)
play(n=4000, until=lambda: story.inventory.get("GS_BALL")); play()   # (she sees you, walks over: longer than play's quiet wait)
_said = list(said)
check(story.inventory.get("GS_BALL") == 1 and story.story_flags.get("got_gs_ball_ivy") and any("Kurt" in l for l in _said),
      f"...walk into her lab: Ivy comes over, gives you the GS Ball and sends you to Kurt ({story.inventory.get('GS_BALL')}, {_said[:1]})")
_t = place("VALENCIA_ISLAND", "VALENCIA_PARK"); said.clear(); _t._go("lab", ""); frames(2); play(n=2000)
_bars = (_t.town_map.get("rooms") or {}).get("lab", {}).get("barred") or []
check(_bars and all(_t._bar_met(b) for b in _bars), "...the GS Ball is gone from her table")
check(story.inventory.get("GS_BALL") == 1 and not any("GS Ball" in l for l in said), f"...and she doesn't give a second one ({list(said)[:1]})")
_said = meet(_t, "Prof. Ivy") or []
check(bool(_said), f"...she still talks to you as before ({_said[:1]})")
_links0, _stores0 = set(story.linked_regions), set(story.region_stores)   # (this save links its regions' Bags: check two apart)
story.linked_regions = set()
story.inventory["GS_BALL"] = 1   # (in Orange's own Bag now)
story.prepare_travel("AZALEA_TOWN")
check(story._store("JOHTO")["bag"].get("GS_BALL", 0) >= 1, "...and it goes with you from Orange's Bag into Johto's, for Kurt")
story.linked_regions = _links0
for _k in set(story.region_stores) - _stores0:
    story.region_stores.pop(_k, None)

story.story_flags.clear(); story.story_flags.update(_flags0)
story.inventory.clear(); story.inventory.update(_inv0)
story.player_team, story.money = _team0, _money0
print(f"##### {fails} failures")
