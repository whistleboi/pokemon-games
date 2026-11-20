# Kanto and Sevii events PLAYED on their maps (11-19, ROADMAP_KANTO "Played, not only data-checked"): walk up to whoever it is,
# talk (walk into them), tap through what's said, pick from the lists a player would, fight the battles; then look at what
# you got. The data side of each is checked elsewhere (sevii_maps, kanto_maps, kanto_canon); this is the player's side.
#   bash dev/checks/run_par.sh kanto_events
import json
from src.states.overworld import PlayState, CityState as _CS
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.dungeon import core
from src.pokemon import moves as _mv

fails = 0
g.dungeon_routes = True
g.walk_towns = True
g.player_character = "red"
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


def play(picks=(), n=3000, until=None):
    """Run the game as a player: tap through what's said, answer each pick list with the next of picks (by value, or
    True for the first), fight battles with the right answers. Stops when nothing is left to do (or until() is true)."""
    picks = list(picks)
    quiet = 0
    for _ in range(n):
        if until and until():
            return True
        st = g.current_state
        name = type(st).__name__
        if name == "PickListState":
            v = picks.pop(0) if picks else None
            if v is None:
                st.done(None) if hasattr(st, "done") else None
            elif v is True:   # (the first choice on the list)
                c0 = (getattr(st, "choices", None) or [None])[0]
                st.pick(c0[1] if isinstance(c0, (tuple, list)) else c0)
            else:
                st.pick(v) if hasattr(st, "pick") else st.done(v)
            quiet = 0
        elif hasattr(st, "math_ui") and hasattr(st, "phase"):
            _fight(st)
            quiet = 0
        elif getattr(st, "npc_active", False):
            _note(st)
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            quiet = 0
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            _note(st)
            st.dialogue_box.advance()
            quiet = 0
        else:
            quiet += 1
            if quiet > 40 and until is None:
                return True
        st.update(); st.draw()
    return until() if until else True


def _fight(b, n=8000):
    for _k in range(n):
        if g.current_state is not b:
            return
        if b.phase == "SWITCH_PROMPT" and b.btn_no.visible and b.btn_no.callback:
            b.btn_no.callback()
        elif b.phase == "MENU" and not b.dialogue_box.visible:
            b.open_move_menu()
            b.choose_move(b.move_buttons[0].text.replace(" ", "-"))
            b.math_ui.on_click(b.options.index(b.correct_ans))
        elif b.dialogue_box.visible:
            _note(b)
            b.dialogue_box.is_finished = True
            if b.phase in ("OUTRO", "VICTORY_TEXT", "REWARD_TEXT"):
                b.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            elif b.dialogue_box.callback:
                cb = b.dialogue_box.callback; b.dialogue_box.callback = None; cb()
        b.feedback_timer = 0
        b.update(); b.draw()


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


def route(area, came, floor=0):
    core.ENTRANCE_INDEX, core.ENTRANCE_COUNT = 0, 0
    story.current_area_key, story.last_area_key = area, came
    p = PlayState(g)
    g.states["play"] = p
    g.change_state(p)
    frames(3); play()
    p = g.current_state
    if floor:
        p.run.enter_floor(floor); frames(2)
    return p


def meet(st, text, picks=(), n=3000):
    """Walk into whoever is called text on this map (from an open tile beside them) and play out what follows."""
    said.clear()
    if isinstance(st, _WTS):
        spot = next((s for s, o in st._people().items() if o.get("text") == text), None)
        if spot is None:   # (in one of the town's rooms: go in)
            for room in (st.town_map.get("rooms") or {}):
                st._go(room, ""); frames(2)
                spot = next((s for s, o in st._people().items() if o.get("text") == text), None)
                if spot is not None:
                    break
        if spot is None:
            return None
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            b = (spot[0] + dx, spot[1] + dy)
            if st._open(b) and b not in st.exits:
                st.player = st.anim_from = b; st.anim = 0; st.walk_goal = None
                st.step(-dx, -dy)
                break
        else:
            return None
    else:
        hit = lambda fl: next((m for m in fl.movers if m.kind in ("figure", "trainer") and isinstance(m.payload, dict) and m.payload.get("text") == text), None)
        if hit(st.run.floor) is None:   # (on another floor, or in a room of the route: rooms are floors after the map's own)
            for i in range(st.run.n_floors):
                if hit(st.run.made(i)) is not None:
                    st.run.enter_floor(i); frames(2)
                    break
        f = st.run.floor
        f.movers = [m for m in f.movers if m.kind != "wild"]
        m = hit(f)
        if m is None:
            return None
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            b = (m.x + dx, m.y + dy)
            if f.walkable(*b) and f.mover_at(*b) is None and b not in f.exits:
                st.run.player = b; st.anim = 0
                st.step(-dx, -dy)
                break
        else:
            return None
    play(picks, n)
    return list(said)


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


_flags0, _inv0, _team0, _money0 = dict(story.story_flags), dict(story.inventory), list(story.player_team), story.money
story.balls_left = 20

print("1) The move tutors: Body Slam (Four Island's house) and Swords Dance (Seven Island)")
for area, came, room, who, move, mon, flag in (("FOUR_ISLAND", "ICEFALL_CAVE", "bodyslam", "Body Slam Tutor", "BODY-SLAM", 143, "frlg_tutor_body_slam"),
                                               ("SEVEN_ISLAND", "SEVAULT_CANYON", None, "Swords Dance Tutor", "SWORDS-DANCE", 123, "frlg_tutor_swords_dance")):
    story.story_flags.pop(flag, None)
    t = town(area, came, room)
    team(mon, level=5)   # (young: it doesn't know the move yet)
    before = move in _mv.move_pool(g, story.player_team[0])
    w = meet(t, who, picks=["teach", True, True])
    check(w is not None and not before and story.story_flags.get(flag) and move in _mv.move_pool(g, story.player_team[0]),
          f"{area}: walk up to the {who}, and your {story.player_team[0].display_name if hasattr(story.player_team[0], 'display_name') else mon} learns {move} ({w and w[:2]}, {getattr(story.player_team[0], 'moves', None)})")

print("2) Memorial Pillar: a Lemonade for Tectonix, TM025 Facade back (FireRed)")
story.story_flags.pop("got_tm_facade_pillar", None)
story.inventory.pop("LEMONADE", None); story.inventory.pop("TM025", None)
team(25)
p = route("MEMORIAL_PILLAR", "FIVE_ISLE_MEADOW")
w1 = meet(p, "Memorial man")
none_yet = not story.inventory.get("TM025")
story.inventory["LEMONADE"] = 2
w2 = meet(p, "Memorial man")
check(w1 is not None and none_yet and story.inventory.get("TM025") == 1 and story.inventory.get("LEMONADE") == 1 and story.story_flags.get("got_tm_facade_pillar"),
      f"...no Lemonade, no TM; with one, he takes it and gives TM025 ({(w1 or [])[:1]}, {(w2 or [])[-1:]})")

print("3) Water Labyrinth: the old man's Egg (Togepi) for a lead Pokemon that loves you")
story.story_flags.pop("got_sevii_togepi", None)
team(25)
story.player_team[0].friendship = 70
p = route("WATER_LABYRINTH", "FIVE_ISLAND")
meet(p, "THE OLD MAN'S EGG")
early = len(story.player_team) == 1
story.player_team[0].friendship = 255
w = meet(p, "THE OLD MAN'S EGG")
egg = story.player_team[-1] if len(story.player_team) > 1 else None
check(early and egg is not None and egg.id == 175 and (getattr(egg, "is_egg", False) or getattr(egg, "egg_steps", None) is not None),
      f"...not yet at friendship 70; at 255 an Egg, and it's a Togepi ({(w or [])[:1]}, {egg and egg.id})")

print("4) Water Path: the Heracross fan's Nest Ball")
story.story_flags.pop("got_nestball_waterpath", None)
story.inventory.pop("NEST_BALL", None)
team(25)
p = route("WATER_PATH", "SIX_ISLAND")
meet(p, "HERACROSS FAN")
none_yet = not story.inventory.get("NEST_BALL")
team(25, 214)
w = meet(p, "HERACROSS FAN")
check(none_yet and story.inventory.get("NEST_BALL") == 1, f"...nothing without a Heracross; show her one, a Nest Ball ({(w or [])[:1]})")

print("5) Sevault Canyon: the Lucky Punch")
story.story_flags.pop("got_luckypunch_sevault", None)
story.inventory.pop("LUCKY_PUNCH", None)
p = route("SEVAULT_CANYON", "CANYON_ENTRANCE")
w = meet(p, "LUCKY PUNCH")
check(story.inventory.get("LUCKY_PUNCH") == 1, f"...picked up where it lies ({w})")

print("6) Seven Island: Psychic Dario and Psychic Rodette")
for who, flag in (("Psychic Dario", "beat_dario_seven"), ("Psychic Rodette", "beat_rodette_seven")):
    story.story_flags.pop(flag, None)
    ace()
    t = town("SEVEN_ISLAND", "SEVAULT_CANYON")
    w = meet(t, who)
    check(w is not None and story.story_flags.get(flag), f"...{who}: talk, battle, win ({(w or [])[:1]}, {(w or [])[-1:]})")

print("7) The Lost Cave: Lady Selphy's battle, then her villa")
story.story_flags.pop("rescued_selphy", None); story.story_flags.pop("selphy_home", None)
ace()
p = route("LOST_CAVE", "RESORT_GORGEOUS")
w = meet(p, "LADY SELPHY")
spot = p.run.index
check(spot is not None and story.story_flags.get("rescued_selphy"), f"...found in the cave's last room (floor {spot}), battled and beaten ({(w or [])[:1]}, {(w or [])[-1:]})")

print("8) Mt. Ember: the Grunts let the first password slip")
story.story_flags["met_ember_researchers"] = True
story.story_flags.pop("ember_password", None)
p = route("MT_EMBER", "KINDLE_ROAD")
said.clear()
sc = next((s for s in json.load(open("assets/town_maps.json", encoding="utf-8"))["MT_EMBER"]["floors"][0].get("scenes", []) if s.get("flag") == "ember_password"), None)
if sc:
    z = sc["trigger"]["zone"]
    p.run.player = (z[0], z[1] + 1); p.anim = 0
    p.step(0, -1)
    play(n=2000, until=lambda: story.story_flags.get("ember_password") and any("Goldeen" in l for l in said))
    play()
check(sc is not None and story.story_flags.get("ember_password") and any("Goldeen need log" in l for l in said),
      f"...walk past them and you hear 'Goldeen need log' ({said[:3]})")

print("7b) ...then home: she waits by her villa, and inside wishes to see a Pokemon")
t = route("RESORT_GORGEOUS", "LOST_CAVE")   # (a route map, as the game opens it)
w = meet(t, "Lady Selphy")
home = story.story_flags.get("selphy_home")
story.story_flags["selphy_wish"] = 25
team(25)
inv = dict(story.inventory)
t = route("RESORT_GORGEOUS", "LOST_CAVE")
w2 = meet(t, "SELPHY'S VILLA")
got = {k: v - inv.get(k, 0) for k, v in story.inventory.items() if v > inv.get(k, 0)}
check(home and sum(got.values()) == 1 and set(got) <= {"NUGGET", "PEARL", "BIG_PEARL", "STARDUST", "STAR_PIECE", "RARE_CANDY"}
      and story.story_flags.get("selphy_wish") != 25,
      f"...outside her villa she thanks you (home); inside, show her the Pikachu she wished for and get one of her gifts ({(w or [])[:1]}, {got}, {(w2 or [])[:1]})")

print("9) Fishing from a town: a bite, the battle, and back on the same shore (Vermilion)")
from src.states.overworld.route_actions import RouteActions as _RA
story.inventory["SUPER_ROD"] = 1
ace()
t = town("VERMILLION_CITY", "KANTO_ROUTE_6")
shore = None
for y in range(t.h):
    for x in range(t.w):
        if t._open((x, y)) and (x, y) not in t.exits:
            t.player = t.anim_from = (x, y); t.facing = (0, 1)
            if t._fish_spot():
                shore = (x, y)
                break
    if shore:
        break
bit = None
for _try in range(40):
    if not shore:
        break
    t.player = t.anim_from = shore; t.anim = 0
    t.fish_here()
    play(n=400, until=lambda: hasattr(g.current_state, "math_ui"))
    if hasattr(g.current_state, "math_ui"):
        bit = g.current_state.opponent_pokemon.id
        break
    play()
play(n=6000, until=lambda: isinstance(g.current_state, _WTS) and not getattr(g.current_state, "npc_active", False))
back = g.current_state
check(shore and bit and isinstance(back, _WTS) and back.area_key == "VERMILLION_CITY" and tuple(back.player) == shore,
      f"...cast from {shore}, a bite (#{bit}), the battle won, and you stand where you cast ({type(back).__name__}, {getattr(back, 'player', None)})")

print("10) FireRed's nine trades, each from its trader on the map")
for area, came, who, want, give, nick, item in (("KANTO_ROUTE_2", "VIRIDIAN_CITY", "TRADER", 63, 122, "MIMIEN", None),
                                                ("CERULEAN_CITY", "KANTO_ROUTE_4", "Trader", 61, 124, "ZYNX", None),
                                                ("UNDERGROUND_PATH", "KANTO_ROUTE_5", "Trader", 32, 29, "MS. NIDO", "TINY_MUSHROOM"),
                                                ("VERMILLION_CITY", "KANTO_ROUTE_6", "Trader", 21, 83, "CH'DING", "STICK"),
                                                ("KANTO_ROUTE_11", "VERMILLION_CITY", "Trader", 33, 30, "NINA", None),
                                                ("KANTO_ROUTE_18", "FUCHSIA_CITY", "Trader", 55, 108, "MARC", None),
                                                ("CINNABAR_ISLAND", "KANTO_ROUTE_21", "Old Trader", 26, 101, "ESPHERE", None),
                                                ("CINNABAR_ISLAND", "KANTO_ROUTE_21", "Lab Trader", 48, 114, "TANGENY", "STARDUST"),
                                                ("CINNABAR_ISLAND", "KANTO_ROUTE_21", "Young Trader", 77, 86, "SEELOR", None)):
    ev = next((o for k in ("explore_options", "route_menu") for o in g.loader.area_data["STORY_PROGRESSION"][area].get(k, []) if o.get("text") == who and (o.get("event") or {}).get("trade")), None)
    fl = (ev or {}).get("event", {}).get("flag")
    if fl:
        story.story_flags.pop(fl, None)
    team(25, want, level=20)
    st = place(area, came)
    w = meet(st, who, picks=[want, True, True])
    ids = [p.id for p in story.player_team]
    new = next((p for p in story.player_team if p.id == give), None)
    nm = getattr(new, "nickname", None) or getattr(new, "name", None)
    check(new is not None and want not in ids and str(nm).upper() == nick and (item is None or getattr(new, "held_item", None) == item),
          f"{area}: {who} - your #{want} for #{give} {nick}{' holding ' + item if item else ''} ({(w or [])[:1]}, {ids}, {nm}, {getattr(new, 'held_item', None)})")

story.story_flags.clear(); story.story_flags.update(_flags0)
story.inventory.clear(); story.inventory.update(_inv0)
story.player_team, story.money = _team0, _money0
print(f"FAILURES: {fails}")
