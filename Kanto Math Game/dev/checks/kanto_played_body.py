# Kanto K5's played checks (11-23, ROADMAP_KANTO "To do: checks still to run"): what the other Kanto suites only read or
# count as won, played here the way a player would, battles fought turn by turn (the first move, the right answer to
# each sum: kanto_maps' _fight), on the walked maps.
#   1. Jordan's own old Kanto saves (copies, read only: the main folder's game_data_1 backups from before the FireRed
#      rebuild) load on the walked maps, and every Kanto + Sevii place they had is still reachable through today's gates
#   2. every Gym, trainer by trainer, then its Leader: the badge and the Leader's own TM
#   3. the Elite Four and the Champion, room by room
#   4. Silph Co.'s Proton, Archer and Ariana, at their fixed levels (DECISIONS follow-up 2)
#   5. sailing to Sevii from Cinnabar with the Volcano Badge: Bill's Seagallop, then his walk into One Island
#   6. the Lucky Egg (Route 15's aide) and the Stick (Vermilion's Farfetch'd) end up in the Bag, where the Bag shows them
#   7. after the title: Mewtwo, Lugia, Ho-Oh, Deoxys, Lorelei at home, the League rematch (Lv 70+, not raised to yours),
#      Red on Mt. Silver (Johto's title taken as won - its flags set, not played: Jordan 11-23)
#        bash dev/checks/run.sh kanto_played
import json, os, copy
_src = open("dev/checks/kanto_playthrough_body.py", encoding="utf-8").read()
exec(_src[_src.index("import json, time"):_src.index("def play_through():")])   # (a new Kanto game, and the playthrough's driver)
_km = open("dev/checks/kanto_maps_body.py", encoding="utf-8").read()
exec(_km[_km.index("def _fight(b, n=8000):"):_km.index("# ---- the Hall of Fame")])   # (a battle fought as a player would)
_kg = open("dev/checks/kanto_gates_body.py", encoding="utf-8").read()
exec(_kg[_kg.index("BADGES = ["):_kg.index("_D = {")])   # (kanto_gates' story steps: at(step) sets the story just before one)


def frames(n=1):
    for _ in range(n):
        g.current_state.update(); g.current_state.draw()

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


FOUGHT = []


def _win(b):   # (the driver's battles: fought, not counted as won)
    STATE["battles"] += 1
    name = getattr(b, "trainer_name", None) or getattr(b, "trainer_class", "?")
    lv = [getattr(p, "level", None) for p in (getattr(b, "opponent_team", None) or [])]
    FOUGHT.append((name, lv))
    if g.current_state is not b:
        g.change_state(b)
    for _round in range(6):
        _fight(b)
        st = g.current_state
        if type(st).__name__ == "PokemonPartyMenuState" and getattr(st, "context", None) == "forced_switch":
            nxt = next((i for i, p in enumerate(story.player_team) if p and getattr(p, "current_hp", 0) > 0 and p is not getattr(b, "player_pokemon", None)), None)
            if nxt is None:
                break
            st.on_select(nxt)   # (one fainted: the next one in, as a player picks)
            if g.current_state is not b:
                g.change_state(b)
            continue
        break
    if g.current_state is b:   # (the fight didn't finish: say so, then end it so the run goes on)
        FOUGHT[-1] = (name + " (UNFINISHED)", lv)
        b.player_won = True
        b.exit_battle()


def ace():
    a = mk(150); a.level = 100; a.moves = ["PSYCHIC", "ICE-BEAM", "THUNDERBOLT", "FLAMETHROWER"]
    if hasattr(a, "recalculate_stats"):
        a.recalculate_stats()
    a.heal_full()
    a.max_hp = a.get_max_hp()
    return a


def walk_town(area, came, room=None, at=None):
    story.current_area_key, story.last_area_key = area, came
    g.walk_town_pos = (area, tuple(at), (0, -1)) if at else None
    g.walk_town_room = (area, room) if room else None
    g.change_state(CityState(g))
    return settle()


def people(st):
    return {o.get("text"): p for p, o in st._people().items()}


def talk_to(st, spot):
    """Stand beside someone (an open tile next to them) facing them, and talk."""
    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        n = (spot[0] + dx, spot[1] + dy)
        if st._open(n):
            st.player = n; st.anim = 0; st.anim_from = n; st.facing = (-dx, -dy)
            st._talk(tuple(spot))
            return settle()
    return None


BADGES = ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL", "MARSH", "VOLCANO", "EARTH"]
GYMS = [("PEWTER_CITY", "KANTO_ROUTE_2", "ROCK-TOMB"), ("CERULEAN_CITY", "KANTO_ROUTE_4", "WATER-PULSE"),
        ("VERMILLION_CITY", "KANTO_ROUTE_6", "SHOCK-WAVE"), ("CELADON_CITY", "KANTO_ROUTE_7", "GIGA-DRAIN"),
        ("FUCHSIA_CITY", "KANTO_ROUTE_18", "TOXIC"), ("SAFFRON_CITY", "KANTO_ROUTE_5", "CALM-MIND"),
        ("CINNABAR_ISLAND", "KANTO_ROUTE_21", "FIRE-BLAST"), ("VIRIDIAN_CITY", "KANTO_ROUTE_1", "EARTHQUAKE")]   # (each Leader's FireRed TM)


_TMS = json.load(open("assets/tms.json", encoding="utf-8"))


def tm_moves():
    """Every TM in the Bag: how many, and the move it holds (this game's own TM numbers: assets/tms.json)."""
    return {k: (q, (_TMS.get(k) or {}).get("move")) for k, q in story.inventory.items() if str(k).startswith("TM") and q}


# ================================================================================ 1. Jordan's old saves
print("1) Jordan's old Kanto saves (copies of the main folder's backups, from before the FireRed rebuild)")
_main = (os.path.normpath(os.path.join(os.getcwd(), "..", "..", "..", "..", "Kanto Math Game"))   # (a worktree: the main
         if ".claude" in os.getcwd() else os.getcwd())   # folder's own game folder, where Jordan's saves are)
_saves = [os.path.join(_main, f) for f in ("game_data_1.json.bak_money_20261102_184633", "game_data_1.json.bak_moltres_1104")]
_new_game, _story0 = copy.deepcopy(g.data.data), g.story_manager   # (the new game: put back after the old saves)
for _p in _saves:
    if not os.path.exists(_p):
        print(f"   --   not found: {_p}")
        continue
    _d = json.load(open(_p, encoding="utf-8"))
    g.data.data = copy.deepcopy(_d)
    try:
        ok = g.load_game_data()
        story = g.story_manager
        st = settle()
        where_ = (story.current_area_key, type(st).__name__)
        check(ok and is_map(st) and story.current_area_key == _d["story"].get("current_area_key") and story.player_team,
              f"{os.path.basename(_p)}: Continue lands on the walked map where it was saved ({where_}, {len(story.player_team)} in the party)")
        exec(open("dev/checks/reach_lib.py", encoding="utf-8").read())
        _fr = {}
        exec(open("dev/builders/town_maps/firered.py", encoding="utf-8").read(), _fr)
        _keys = set(_fr["KANTO"])
        _had = {k[8:] for k, v in story.story_flags.items() if k.startswith("visited_") and v and k[8:] in _keys}
        _seen, _gyms = reach(story.current_area_key)
        _lost = sorted(_had - set(_seen))
        check(not _lost, f"...every Kanto/Sevii place it had been to is still reachable through today's gates ({len(_had)} visited; cut off: {_lost})")
    except Exception as ex:
        import traceback
        check(False, f"{os.path.basename(_p)}: loading it crashed: {type(ex).__name__}: {ex} @ {traceback.extract_tb(ex.__traceback__)[-1].lineno}")
g.data.data = _new_game
g.story_manager = story = _story0   # (back to the new game: a load would keep the last old save's story)
g.change_state(CityState(g) if AREAS.get(story.current_area_key, {}).get("area_type") == "town" else PlayState(g)); settle()

# ================================================================================ 2. the Gyms, trainer by trainer
print("\n2) every Gym, trainer by trainer, then its Leader (battles fought turn by turn)")
for _i, (_town, _came, _tm) in enumerate(GYMS):
    at(BADGES[_i].lower())   # (the story just before this badge: what opens the Gym - Bill for Misty, the Secret Key...)
    for _k in [k for k in story.story_flags if _town in k and ("gym" in k or "leader" in k)]:
        story.story_flags.pop(_k)
    from src import minigames as _mg   # (the Gym's challenge minigame - a random pick - counts as won: this part plays the trainers and
    story.story_flags[_mg.done_flag(_town)] = True   #  the Leader; 11-24, Fish Escape stalled Erika's Gym)
    story.player_team = [ace()]
    v = walk_town(_town, _came)
    if not isinstance(v, _WTS):
        check(False, f"{_town}: no walked town ({type(v).__name__})"); continue
    v._go("gym", ""); settle(); v = g.current_state
    _pp = people(v)
    _ev = {p.get("text"): p for p in (v.town_map["rooms"]["gym"].get("people") or []) if isinstance(p, dict)}
    _trainers = [n for n, p in _ev.items() if (p.get("event") or {}).get("battle")]
    _won = []
    for _n in _trainers:
        FOUGHT.clear()
        _pp = people(v) if isinstance(v, _WTS) else _pp   # (where they stand now: Viridian's trainers walk about)
        if _n not in _pp:
            _won.append(False); continue
        talk_to(v, _pp[_n]); v = g.current_state
        _f = (_ev[_n]["event"] or {}).get("flag")
        _won.append(bool(FOUGHT) and not FOUGHT[0][0].endswith("(UNFINISHED)") and (not _f or story.story_flags.get(_f)))
        FOUGHT.clear()
        if isinstance(v, _WTS) and v.room == "gym" and _n in people(v):
            talk_to(v, people(v)[_n]); v = g.current_state
        _won[-1] = _won[-1] and not FOUGHT   # (beaten: talking again is no second battle)
    _tms0 = tm_moves()
    FOUGHT.clear()
    v = g.current_state
    if isinstance(v, _WTS) and v.room != "gym":
        v._go("gym", ""); settle(); v = g.current_state
    for _try in range(2):   # (a scene first - Viridian's Jessie & James - then the Leader: talk again)
        _v2 = g.current_state if isinstance(g.current_state, _WTS) else v
        talk_to(_v2, people(_v2).get("Gym") or _pp.get("Gym"))
        if BADGES[_i] in story.badges["KANTO"]:
            break
    _got = {k: mv for k, (q, mv) in tm_moves().items() if q > (_tms0.get(k) or (0, None))[0]}
    _tm_ok = _tm in _got.values()
    check(all(_won) and BADGES[_i] in story.badges["KANTO"] and _tm_ok,
          f"{_town}: {len(_trainers)} trainers fought one by one ({sum(_won)} won, none fights twice), then the Leader "
          f"({[f[0] for f in FOUGHT][:3]}): the {BADGES[_i].title()} Badge and {_got or 'no TM'}")

# ================================================================================ 3. the Elite Four and the Champion
print("\n3) the Elite Four and the Champion, room by room (battles fought turn by turn)")
at("earth", also=True)
story.player_team = [ace(), ace()]
for _k in [k for k in story.story_flags if "INDIGO_PLATEAU" in k] + ["beat_elite_four", "beat_champion"]:
    story.story_flags.pop(_k, None)
v = walk_town("INDIGO_PLATEAU", "KANTO_ROUTE_23")
for _i, (_room, _who) in enumerate((("league_lorelei", "Lorelei"), ("league_bruno", "Bruno"), ("league_agatha", "Agatha"),
                                     ("league_lance", "Lance"), ("league_champion", "{rival_name}")), 1):
    v = g.current_state
    if not isinstance(v, _WTS):
        check(False, f"{_who}: not on the Plateau's map ({type(v).__name__})"); break
    v._go(_room, ""); settle(); v = g.current_state
    for _p in story.player_team:
        _p.heal_full()
    FOUGHT.clear()
    talk_to(v, people(v)[_who])
    _flag = "beat_champion" if _i == 5 else f"league_won_INDIGO_PLATEAU_{_i}"
    _ok = bool(FOUGHT) and not FOUGHT[0][0].endswith("(UNFINISHED)") and story.story_flags.get(_flag)
    check(_ok, f"{_who.replace('{rival_name}', 'the Champion')}: fought and beaten ({FOUGHT[:1]}; {_flag}: {story.story_flags.get(_flag)})")
    if not _ok:
        break
check(story.story_flags.get("beat_elite_four") and story.story_flags.get("beat_champion"), "...the title: the Elite Four and the Champion beaten")

# ================================================================================ 4. Silph Co.'s story trainers
print("\n4) Silph Co.: Proton, Archer and Ariana (our story trainers, fixed levels: DECISIONS follow-up 2)")
at("silph", flags=["visited_SILPH_CITY"])
story.player_team = [ace()]
_WANT = {"Admin Proton": [30] * 3, "Archer": [31] * 3, "Executive Ariana": [33] * 4}
for _who, _lv in _WANT.items():
    story.current_area_key, story.last_area_key = "SILPH_CITY", "SAFFRON_CITY"
    g.change_state(PlayState(g)); r = settle()
    _ix = next((i for i, t in enumerate(r.area_data.get("trainer_pool") or []) if t.get("name") == _who), None)
    _m = None
    for _f in range(12):
        try:
            while len(r.run.floors) <= _f:
                r.run.enter_floor(len(r.run.floors))
            r.run.enter_floor(_f); frames(2)
        except Exception:
            break
        _m = next((m for m in r.run.floor.movers if m.kind == "trainer" and m.payload and isinstance(m.payload[1], dict) and (m.payload[1].get("spot_name") or m.payload[1].get("name")) == _who), None)
        if _m:
            break
    if _m is None:
        check(False, f"{_who}: not standing on any Silph Co. floor (pool index {_ix})"); continue
    f = r.run.floor
    f.movers = [m for m in f.movers if m.kind != "wild"]
    _n = next(((_m.x - dx, _m.y - dy, dx, dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))
               if f.walkable(_m.x - dx, _m.y - dy) and f.mover_at(_m.x - dx, _m.y - dy) is None and (_m.x - dx, _m.y - dy) not in f.exits), None)
    FOUGHT.clear()
    r.run.player = (_n[0], _n[1]); r.anim = 0; r.anim_from = r.partner = r.partner_from = r.run.player
    r.step(_n[2], _n[3]); settle()
    _got = next((lv for n, lv in FOUGHT if _who.split()[-1] in str(n)), None)
    check(_got == _lv, f"{_who} (Silph Co. floor {r.run.index}): walked into, fought, levels {_got} (want {_lv}) ({FOUGHT[:2]})")

# ================================================================================ 5. sailing to Sevii from Cinnabar
print("\n5) sailing to Sevii from Cinnabar: the Volcano Badge, Bill's Seagallop, his walk into One Island")
at("volcano", also=True)
story.player_team = [ace()]
story.inventory.pop("TRI_PASS", None)
for _k in ("one_island_bill_walk", "visited_ONE_ISLAND"):
    story.story_flags.pop(_k, None)
v = walk_town("CINNABAR_ISLAND", "KANTO_ROUTE_21")
_pp = people(v)   # (the harbour sailor: shown as the one boat he offers, or as "door:harbor" when there are several)
_sailor = _pp.get("Seagallop to One Island") or _pp.get("door:harbor")
_picked = "Seagallop to One Island" if "Seagallop to One Island" in _pp else None
if _sailor:
    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        _nb = (_sailor[0] + dx, _sailor[1] + dy)
        if v._open(_nb):
            v.player = _nb; v.anim = 0; v.anim_from = _nb; v.facing = (-dx, -dy)
            break
    v._talk(tuple(_sailor))
    for _ in range(300):
        st = g.current_state
        _hb = list(getattr(st, "hover_buttons", []) or [])
        _b1 = next((b for b in _hb if "One Island" in str(b.text)), None)
        if _b1:
            _picked = str(_b1.text); st.clear_hover_menu(); _b1.callback(); break
        if getattr(getattr(st, "dialogue_box", None), "visible", False):
            st.dialogue_box.advance()
        st.update(); st.draw()
st = settle()
check(bool(_picked) and story.current_area_key == "ONE_ISLAND", f"Cinnabar's harbour sailor: {_picked!r} with the Volcano Badge (no Tri-Pass yet): now {here()}")
if story.current_area_key == "ONE_ISLAND" and isinstance(st, _WTS):
    if st.room == "harbor":   # (still inside the harbour building: out, as a player walks out)
        st._go(None, "OUT:12,19"); st = settle()
    for _ in range(40):
        st = settle()
        if story.story_flags.get("one_island_bill_walk"):
            break
        st.update(); st.draw()
    st = settle()
    check(story.story_flags.get("one_island_bill_walk") and getattr(st, "room", None) == "center",
          f"...One Island: out of the harbour, Bill walks you into the Network Center ({getattr(st, 'room', None)}, {getattr(st, 'player', None)})")

# ================================================================================ 6. the Lucky Egg and the Stick in the Bag
print("\n6) the Lucky Egg and the Stick, in the Bag")
from src.states.systems.bag import BagState
from src.states.overworld import _run_story_event
at("soul")
story.kanto_caught_count = lambda: 50
story.inventory.pop("LUCKY_EGG", None); story.story_flags.pop("got_lucky_egg_kanto", None)
_ev = next(o for o in AREAS["KANTO_ROUTE_15"]["route_menu"] if o.get("text") == "OAK'S AIDE")["event"]
_run_story_event(g.current_state, _ev, lambda c: story.check_condition(c) if hasattr(story, "check_condition") else True, lambda l: said.extend(l))
settle()
story.player_team = [ace(), mk(21)]
_tr = next(o for o in AREAS["VERMILLION_CITY"]["explore_options"] if o.get("text") == "Trader" and (o.get("event") or {}).get("trade"))
story.story_flags.pop(_tr["event"].get("flag"), None); story.inventory.pop("STICK", None)
_run_story_event(g.current_state, _tr["event"], lambda c: True, lambda l: said.extend(l))
st = settle()
_far = next((p for p in story.player_team if getattr(p, "id", None) == 83), None)
bag = BagState(g, g.current_state)
_items = dict(bag.pocket_items(bag.pocket_of("LUCKY_EGG")))
_items.update(dict(bag.pocket_items(bag.pocket_of("STICK"))))
check(story.inventory.get("LUCKY_EGG") and "LUCKY_EGG" in _items, f"Route 15's aide: the Lucky Egg is in the Bag ({bag.pocket_of('LUCKY_EGG')}: {_items.get('LUCKY_EGG')})")
check(_far is not None and getattr(_far, "held_item", None) == "STICK" and "STICK" in _items,
      f"Vermilion's trade: Farfetch'd comes holding the Stick, and the Bag shows it ({bag.pocket_of('STICK')}: {_items.get('STICK')}; held {getattr(_far, 'held_item', None)})")

# ================================================================================ 7. after the title
print("\n7) after the title: Mewtwo, Navel Rock, Birth Island, Lorelei at home, the League rematch, Red (Johto's title set, not played)")


def post_title(**more):
    """The story after Kanto's title and Celio's Network Machine (what the playthrough ends with)."""
    at("earth", also=True, flags=["beat_champion", "beat_elite_four", "network_machine_fixed", "met_celio", "unlocked_national_dex",
                                  "got_tri_pass", "got_rainbow_pass", "sevii_icefall_cleared", "sevii_warehouse_cleared",
                                  "visited_ONE_ISLAND", "visited_CERULEAN_CAVE"] + list(more.get("flags", [])),
       items=["TRI_PASS", "RAINBOW_PASS"] + list(more.get("items", [])))
    story.player_team = [ace(), ace()]


def battle_drive(limit=12000):
    """A battle the map started (a legend, a boss): fought turn by turn; its words tapped through; back on the map."""
    for _ in range(limit):
        st = g.current_state
        if isinstance(st, TrainerBattleState):   # (a wild legend's battle is one too: WildBattleState)
            _win(st)
            continue
        if is_map(st) and not getattr(st, "_busy", lambda: False)() and (not hasattr(st, "_ready") or st._ready()):
            return st
        if getattr(getattr(st, "dialogue_box", None), "visible", False):
            st.dialogue_box.advance()
        elif hasattr(st, "handle_events") and not is_map(st):
            _click(st)
        st.update(); st.draw()
    return g.current_state


def fight_figure(area, came, text, floors=24):
    """Into area from came, find the figure named text on any floor, walk into it, and fight what it starts."""
    story.current_area_key, story.last_area_key = area, came
    g.change_state(PlayState(g)); r = settle()
    if not is_dun(r):
        return None, f"{area}: no walked map ({type(r).__name__})"
    found = None
    for _f in range(floors):
        try:
            while len(r.run.floors) <= _f:
                r.run.enter_floor(len(r.run.floors))
            r.run.enter_floor(_f); frames(2)
        except Exception:
            break
        found = next((m for m in r.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == text), None)
        if found:
            break
    if found is None:
        return None, f"{text}: not standing on any floor of {area}"
    f = r.run.floor
    f.movers = [m for m in f.movers if m.kind not in ("wild", "trainer")]
    n = next(((found.x - dx, found.y - dy, dx, dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))
              if f.walkable(found.x - dx, found.y - dy) and f.mover_at(found.x - dx, found.y - dy) is None
              and (found.x - dx, found.y - dy) not in f.exits), None)
    if n is None:
        return None, f"{text}: nowhere to stand beside it ({found.x}, {found.y})"
    r.run.player = (n[0], n[1]); r.anim = 0; r.anim_from = r.partner = r.partner_from = r.run.player
    r.encounter_free = 999
    FOUGHT.clear()
    r.step(n[2], n[3])
    battle_drive()
    return (r.run.index, found.x, found.y), None


# Mewtwo: Cerulean Cave, open to a Champion once the Network Machine works (the guard's gate is in kanto_gates)
for _area, _came, _text, _flag, _extra in (("CERULEAN_CAVE", "CERULEAN_CITY", "CHALLENGE MEWTWO", None, {}),
                                           ("NAVEL_ROCK", "ONE_ISLAND", "SEEK LUGIA", "navel_rock_lugia", {"items": ["MYSTIC_TICKET"]}),
                                           ("NAVEL_ROCK", "ONE_ISLAND", "SEEK HO-OH", "navel_rock_ho_oh", {"items": ["MYSTIC_TICKET"]}),
                                           ("BIRTH_ISLAND", "ONE_ISLAND", "SEEK DEOXYS", "birth_island_deoxys", {"items": ["AURORA_TICKET"]})):
    post_title(**_extra)
    if _flag is None:   # (Mewtwo's own victory flag, as the map reads it)
        _it = next(o for o in AREAS[_area]["route_menu"] if o.get("text") == _text)
        _flag = ((_it.get("boss") or AREAS[_area].get("area_boss") or {}).get("victory_flag") or f"{_area}_boss_defeated")   # (route_encounters._boss_flag_for's rule)
    story.story_flags.pop(_flag, None)
    _at, _why = fight_figure(_area, _came, _text)
    _won = bool(FOUGHT) and not FOUGHT[0][0].endswith("(UNFINISHED)")
    check(_at and _won and story.story_flags.get(_flag),
          f"{_area}: {_text} - walked into and fought turn by turn ({_why or _at}; {FOUGHT[:1]}; {_flag}: {story.story_flags.get(_flag)})")

# Lorelei at home: after Icefall Cave and the title, a battle just for fun
post_title()
story.story_flags.pop("beat_lorelei_home", None)
v = walk_town("FOUR_ISLAND", "ICEFALL_CAVE")
v._go("lorelei", ""); settle(); v = g.current_state
_pp = people(v)
_lo = _pp.get("Battle Lorelei")
FOUGHT.clear()
if _lo:
    talk_to(v, _lo)
_bl = next(o for o in AREAS["FOUR_ISLAND"]["explore_options"] if o.get("text") == "Battle Lorelei")
check(_lo and FOUGHT and not FOUGHT[0][0].endswith("(UNFINISHED)") and (not _bl["event"].get("flag") or story.story_flags.get(_bl["event"]["flag"])),
      f"Four Island: Lorelei at home, Icefall Cave cleared - talked to and fought ({_lo}; {FOUGHT[:1]})")

# the League rematch: after the title the run starts over, each Pokemon at least Lv 70, never raised to yours (Jordan 11-21)
post_title()
story.story_flags["gym_progress_INDIGO_PLATEAU"] = 5   # (the League beaten once: its doors' flags stay set, as in a real save)
for _i in range(1, 5):
    story.story_flags[f"league_won_INDIGO_PLATEAU_{_i}"] = True
_big = ace(); _big.level = 100
story.player_team = [_big, ace()]
v = walk_town("INDIGO_PLATEAU", "KANTO_ROUTE_23")
_rm = []
for _i, (_room, _who) in enumerate((("league_lorelei", "Lorelei"), ("league_bruno", "Bruno"), ("league_agatha", "Agatha"),
                                     ("league_lance", "Lance"), ("league_champion", "{rival_name}")), 1):
    v = g.current_state
    if not isinstance(v, _WTS):
        break
    v._go(_room, ""); settle(); v = g.current_state
    for _p in story.player_team:
        _p.heal_full()
    FOUGHT.clear()
    talk_to(v, people(v)[_who])
    _rm.append((FOUGHT[0] if FOUGHT else (_who, None)))
_lvls = [lv for _n, lv in _rm if lv]
check(len(_lvls) == 5 and all(min(lv) >= 70 for lv in _lvls) and all(max(lv) <= 75 for lv in _lvls[:4]) and not any(str(n).endswith("(UNFINISHED)") for n, _l in _rm),
      f"the League rematch: all five fought again, every Pokemon at least Lv 70 and not raised to your Lv 100s ({_rm})")

# Red: Johto's title is taken as won (its flags set: not played here, Jordan 11-23); Route 28 to Mt. Silver, then the summit
post_title(flags=["beat_johto_champion", "beat_johto_elite_four", "visited_SILVER_LEAGUE_PLATEAU"])
story.badges["JOHTO"] = ["ZEPHYR", "HIVE", "PLAIN", "FOG", "STORMBADGE", "MINERAL", "GLACIER", "RISING"]   # (the game's own names: town_menu has_8_johto_badges)
story.story_flags[story.champion_flag("JOHTO")] = True   # (Johto's title: as the game records it, then its storage joined to
story.current_area_key = "KANTO_ROUTE_22"                # Kanto's as a second title does - one party, PC and Bag; Jordan 11-23)
story.link_champion_regions()
story.player_team = [ace(), ace()]
story.story_flags.pop("defeated_red", None)
exec(open("dev/checks/reach_lib.py", encoding="utf-8").read())
_seen, _g = reach("KANTO_ROUTE_22")
check({"KANTO_ROUTE_28", "MT_SILVER_CITY", "MT_SILVER"} <= set(_seen), f"Red's way: Route 22 to Route 28, Mt. Silver's Center and the mountain open with Johto's title ({sorted(x for x in _seen if 'SILVER' in x or x.endswith('_28'))})")
_at, _why = fight_figure("MT_SILVER", "MT_SILVER_CITY", "CHALLENGE RED")
check(_at and FOUGHT and not FOUGHT[0][0].endswith("(UNFINISHED)") and story.story_flags.get("defeated_red"),
      f"Mt. Silver's summit: Red, walked up to and fought turn by turn ({_why or _at}; {FOUGHT[:1]}; defeated_red: {story.story_flags.get('defeated_red')})")

# ================================================================================ 8. the Leaders' rematches
print("\n8) after the title: each Leader's rematch (HGSS's teams, Koga Janine's and Giovanni Blue's, Gen 1 swaps; Jordan 11-24)")
post_title()
story.story_flags.pop(story.champion_flag("JOHTO"), None)   # (Kanto's title only: a second title opens the League Redo instead)
for _town, _came, _tm in GYMS:
    _ld = g.loader.area_data["STORY_PROGRESSION"][_town]["gym"]["leader"]
    _w = _ld.get("rematch") or {}
    story.player_team = [ace(), ace(), ace()]
    for _p in story.player_team:
        _p.heal_full()
    _b0 = list(story.badges.get("KANTO", []))
    v = walk_town(_town, _came)
    if not isinstance(v, _WTS):
        check(False, f"{_town}: no walked town ({type(v).__name__})"); continue
    v._go("gym", ""); settle(); v = g.current_state
    FOUGHT.clear()
    _gp = people(v).get("Gym")
    if _gp is not None:
        talk_to(v, _gp)
    _f = FOUGHT[0] if FOUGHT else (None, None)
    check(len(FOUGHT) == 1 and str(_f[0]).startswith(_ld["name"]) and _f[1] == _w.get("levels") and all(t <= 151 for t in _w.get("team", [0]))
          and story.badges.get("KANTO", []) == _b0,
          f"{_town}: {_ld['name']} alone with the rematch team (Lv {_f[1]}), all Gen 1, no badge again ({FOUGHT})")

print(f"##### {len(fails)} failures")
for m in fails:
    print("   FAIL " + m)
