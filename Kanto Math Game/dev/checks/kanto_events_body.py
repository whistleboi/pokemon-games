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
                                                ("CINNABAR_ISLAND", "KANTO_ROUTE_21", "Young Trader", 77, 86, "SEELOR", None),
                                                ("POWER_PLANT", "KANTO_ROUTE_10", "Trader", 51, 82, "MAGGIE", "METAL_COAT")):   # (11-23: SoulSilver's Power Plant trade, Jordan's Gen 1 pick)
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

# SoulSilver's Volty: Lt. Surge at Saffron's Magnet Train station after the title, his Pikachu for yours (11-23)
story.story_flags.pop("saffron_volty_trade", None); story.story_flags.pop("beat_champion", None)
st = place("SAFFRON_CITY", "KANTO_ROUTE_5")
_pre = [o.get("text") for o in st._door_options("station")]
story.story_flags["beat_champion"] = True
st = place("SAFFRON_CITY", "KANTO_ROUTE_5")
_post = [o.get("text") for o in st._door_options("station")]
_sv = next(o for o in st._door_options("station") if o.get("text") == "Lt. Surge")
team(25, 25, level=20)
said.clear()
st._get_callback_for_option(_sv)()
play(picks=[25, True, True], n=1500, until=lambda: story.story_flags.get("saffron_volty_trade"))
play(n=200)
_pk = next((p for p in story.player_team if p.id == 25 and str(getattr(p, "nickname", "")).upper() == "VOLTY"), None)
check("Lt. Surge" not in _pre and "Lt. Surge" in _post and _pk is not None and getattr(_pk, "held_item", None) == "YELLOW_SHARD",
      f"SAFFRON_CITY: Lt. Surge at the Magnet Train station after the title - your Pikachu for his Volty holding a Yellow Shard ({_pre}, {_post}, {said[:1]})")

# SoulSilver's 9 Kanto swarms, from the start (no National Pokedex needed), the Gen 1 lock still filtering (11-23)
from src.world import swarms as _SW
_nd = story.story_flags.pop("unlocked_national_dex", None)
_kt = _SW.SWARMS.get("KANTO") or {}
_tday = _SW.today(story, "KANTO")
if _nd: story.story_flags["unlocked_national_dex"] = _nd
check(len(_kt) == 9 and _kt.get("KANTO_ROUTE_13") == 113 and _kt.get("VIRIDIAN_FOREST") == 401 and _tday is not None and _tday[0] in _kt,
      f"Kanto's swarms: SoulSilver's nine, running from the start ({sorted(_kt)}, today {_tday})")

print("11) The VS Seeker as FireRed plays it: the pose, the bubbles, then the message (11-19)")
from src.world import vs_seeker as _V
story.inventory["VS_SEEKER"] = 1
story.story_flags["vs_seeker_steps"] = _V.CHARGE
g.player_character = "red"
ace()
p = route("KANTO_ROUTE_3", "PEWTER_CITY")
_tr = sorted([m for m in p.run.floor.movers if m.kind == "trainer"], key=lambda m: abs(m.x - p.run.player[0]) + abs(m.y - p.run.player[1]))
if _tr:
    p.run.player = (_tr[0].x, _tr[0].y + 2) if p.run.floor.walkable(_tr[0].x, _tr[0].y + 2) else p.run.player
    story.mark_trainer_defeated("KANTO_ROUTE_3", _tr[0].payload[0])
    p.run.floor.movers.remove(_tr[0])
_rc, _ch = _V.READY_CHANCE, dict(_V.CHANCE)
_V.READY_CHANCE = 1.0; _V.CHANCE.clear()
_btn = "VS SEEKER" in [b[1] for b in p._buttons()]
p.use_vs_seeker()
_pose = p._player_img() is not None and p._vs_pose() is not None
_hidden = all(getattr(m, "_vs_hidden", False) for m in p._vs_anim["res"]["rematch"])
p._vs_anim["t"] -= p.VS_POP + 10
p.update()
_bub = dict(p._vs_bubbles())
p._vs_anim["t"] -= p.VS_HOLD
p.update()
_said = list(p.dialogue_box.text_lines) if p.dialogue_box.visible else []
_V.READY_CHANCE = _rc; _V.CHANCE.update(_ch)
check(_btn and _pose and _hidden and "!!" in _bub.values() and _said[:1] == ["You used the VS Seeker!"],
      f"...a VS SEEKER button; Red holds it up (FireRed's frames); the rematch steps out with \"!!\", others in view get \"!\"; then the message ({_btn}, {_pose}, {sorted(set(_bub.values()))}, {_said[:2]})")
play()

print("12) The Hall of Fame: the team, the record, Mom's call (11-19)")
from src.states.hall_of_fame import HallOfFameState, records as _hof_records
story.player_team = [mk(i) for i in (6, 25, 131)]
_n0 = len(_hof_records(g))
_out = []
_hs = HallOfFameState(g, "KANTO", lambda ls: _out.extend(ls + ["(done)"]))
g.current_state = _hs
for _ in range(4000):
    if _out:
        break
    _hs.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
    _hs.update(); _hs.draw()
_rec = _hof_records(g)[-1] if len(_hof_records(g)) > _n0 else {}
check(len(_hof_records(g)) == _n0 + 1 and [m["id"] for m in _rec.get("team", [])] == [6, 25, 131] and _rec.get("region") == "KANTO"
      and _out[-1:] == ["(done)"] and any("pack your bags" in l for l in _hs.call_lines),
      f"...each Pokemon, the group, the music cut and Mom's call to pack for the move; the team saved in this save's records ({_rec.get('team') and len(_rec['team'])}, {_hs.call_lines[1:2]})")

print("13) A new game's opening talk: the professor knows your name and your rival's (11-19)")
from src.states.intro_speech import IntroSpeechState, INTROS
g.player_name, g.rival_name = "ASH", "GARY"
_ok = []
for _reg in ("KANTO", "JOHTO", "HOENN", "SINNOH", "ORANGE", "ORRE", "UNOVA"):
    _d = []
    _is = IntroSpeechState(g, _reg, lambda: _d.append(1))
    _lines = []
    for _ in range(400):
        if _d:
            break
        _who, _txt = _is._line()
        if _txt and (not _lines or _lines[-1] != _txt):
            _lines.append(_txt)
        _is.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        _is.update(); _is.draw()
        if _who == "out":
            _is.t_line -= 5000
    _ok.append((_reg, bool(_d) and any("ASH" in l for l in _lines) and (_reg in ("JOHTO", "ORRE") or any("GARY" in l for l in _lines))))
check(all(o for _, o in _ok), f"...every region's opening plays through, by name ({_ok})")

print("\n== Celadon Dept. Store's 5F and roof (11-23 cleanup: FireRed's clerks, vending machines and the thirsty girl's TMs)")
for _k in ("FRESH_WATER", "SODA_POP", "LEMONADE", "TM075", "TM236", "TM074"):
    story.inventory.pop(_k, None)
for _f in ("got_celadon_roof_tm_water", "got_celadon_roof_tm_soda", "got_celadon_roof_tm_lemonade"):
    story.story_flags.pop(_f, None)
story.money = 1000
_t = town("CELADON_CITY", "KANTO_ROUTE_7", room="dept_roof")
said.clear(); _t._read((10, 3)); play()
check(story.money == 800 and story.inventory.get("FRESH_WATER") == 1, f"a roof vending machine sells Fresh Water for $200 (money {story.money}, {story.inventory.get('FRESH_WATER')})")
said.clear(); _t._read((12, 3)); play()
check(story.money == 450 and story.inventory.get("LEMONADE") == 1, f"...and the next-but-one Lemonade for $350 ({story.money})")
_s = meet(_t, "Little girl") or []
check(story.inventory.get("TM075") == 1 and not story.inventory.get("FRESH_WATER"), f"the thirsty girl takes the Fresh Water and gives TM Light Screen ({_s[-2:]})")
_s = meet(_t, "Little girl") or []
check(story.inventory.get("TM074") == 1 and not story.inventory.get("LEMONADE"), "...then the Lemonade for TM Reflect, one TM per drink")
_s = meet(_t, "Little girl") or []
check(not story.inventory.get("TM236") and any("thirsty" in l for l in _s), f"...with no drink left she's still thirsty ({_s[-1:]})")
story.money = 3
said.clear(); _t._read((11, 3)); play()
check(story.money == 3 and not story.inventory.get("SODA_POP"), "...and the machines want the money first")
_t = town("CELADON_CITY", "KANTO_ROUTE_7", room="dept_5")
_shelves = {o.get("text"): o.get("stock") for o in _t._people().values() if o.get("action") == "SHOP"}
check(_shelves.get("Vitamin clerk") == ["HP_UP", "PROTEIN", "IRON", "CARBOS", "CALCIUM"] and "X_ATTACK" in (_shelves.get("Battle item clerk") or []),
      f"5F's two clerks sell FireRed's vitamins and X items ({_shelves})")
_cb = _t._get_callback_for_option(next(o for o in _t._people().values() if o.get("text") == "Vitamin clerk")); _cb()
check(type(g.current_state).__name__ == "PokeMartState" and g.current_state.stock[:1] == ["HP_UP"], f"...talking to the vitamin clerk opens her shelf ({type(g.current_state).__name__})")
_ng = next(t for t in g.loader.area_data["STORY_PROGRESSION"]["KANTO_ROUTE_24"]["trainer_pool"] if t["name"] == "Team Rocket Grunt")
check(_ng["rewards"].get("NUGGET") == 1, "the Nugget Bridge Grunt gives the nugget he talks about")
_up = town("UNDERGROUND_PATH", "KANTO_ROUTE_5")
_up._get_callback_for_option({"action": "NPC", "target": "stoneman"})()
_m = list(getattr(getattr(_up, "npc_dialogue", None), "text_lines", None) or getattr(_up, "npc_messages", None) or [])
check(not any("fossil lab" in str(l) for l in _m) and _m, f"the Underground Path's Fossil Maniac doesn't call it the fossil lab ({_m[:1]})")
story.inventory.clear(); story.inventory.update(_inv0)

story.story_flags.clear(); story.story_flags.update(_flags0)
story.inventory.clear(); story.inventory.update(_inv0)
story.player_team, story.money = _team0, _money0
print(f"FAILURES: {fails}")
