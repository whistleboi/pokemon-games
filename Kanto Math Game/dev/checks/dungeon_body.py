# Route dungeons (src/dungeon, src/states/overworld/dungeon.py): the walker itself - walking, battles, items, TM spots,
# story gates, followers, battle style, Mega on the map - on Kanto's first routes. Region parts: dungeon_kanto, dungeon_johto.
#   bash dev/checks/run.sh dungeon
exec(open("dev/checks/dungeon_lib.py", encoding="utf-8").read())



# ---- headless default: the old route screen (the other suites keep working)
story.current_area_key = "KANTO_ROUTE_1"
check(type(PlayState(g)) is PlayState, "headless: PlayState stays the route menu unless dungeon_routes is on")
g.dungeon_routes = True

# ---- Route 1
p = kanto("KANTO_ROUTE_1")
check(isinstance(p, DungeonState), f"Route 1 is a dungeon ({type(p).__name__})")
f = p.run.floor
targets = sorted(set(f.exits.values()))  # (our own map, Jordan 11-07: a road's width of tiles each way)
check(targets == ["PALLET_TOWN", "VIRIDIAN_CITY"], f"Route 1 exits {targets}")
entry = [xy for xy, t in f.exits.items() if t == "PALLET_TOWN"][0]
check(abs(entry[0] - p.run.player[0]) + abs(entry[1] - p.run.player[1]) <= 12, "you start beside the way you came in")
check(sum(m.kind == "wild" for m in f.movers) >= 4, "wild Pokemon wander the floor")
check(sum(m.kind == "trainer" for m in f.movers) == 0, "Route 1: no trainers (as in the games)")
check(any(m.kind == "figure" and m.payload.get("text") == "POKE MART CLERK" for m in f.movers),
      "...the Poke Mart clerk stands there (a free Potion)")
check(p.uses_keyboard, "the map takes the arrow keys")
for _ in range(40):
    frames(p)
    p.step(*_rnd.choice(core.DIRS))
    for _ in range(core.Run.SIGHT):
        frames(p)
    if p.mode != "MAP":
        break
check(True, f"walked about (mode {p.mode}, turn {p.run.turn})")

# quick catch: MATH, right answer
p = kanto("KANTO_ROUTE_1")
m, d = beside(p, "wild")
p.step(*d)
check(p.mode == "CHOICE" and p.encounter is m, "bumping a wild Pokemon brings up MATH / BATTLE")
frames(p)
orig = catching.window_throw
catching.window_throw = lambda *a, **k: (True, 3, False)
balls = story.balls_left
party = len(story.player_team)
p._pick(0)
check(p.mode == "MATH" and len(p.options) == 3, f"MATH: {p.problem_str} {p.options}")
frames(p)
p._answer(p.options.index(p.correct_ans))
check(p.mode == "THROW" and story.balls_left == balls - 1, "a right answer throws a ball")
for _ in range(80):
    frames(p)
    if p.mode != "THROW":
        break
check(len(story.player_team) == party + 1, f"caught {m.payload.display_name} (party {len(story.player_team)})")
check(m not in p.run.floor.movers, "the caught Pokemon is gone from the map")
talk(p)
frames(p, 3)
check(g.current_state is p and p.mode == "MAP", f"back on the map ({type(g.current_state).__name__})")
catching.window_throw = orig

# quick catch: wrong answer -> it runs away
m, d = beside(p, "wild")
m.payload.is_shiny = False  # (a shiny is caught even on a wrong answer: not what this checks)
p.step(*d)
p._pick(0)
wrong = next(i for i, o in enumerate(p.options) if o != p.correct_ans)
party = len(story.player_team)
p._answer(wrong)
for _ in range(80):
    frames(p)
    if p.mode != "THROW":
        break
check(len(story.player_team) == party and m not in p.run.floor.movers, "a wrong answer: it runs away")
talk(p)

# BATTLE: the full battle, then back to the same walk
m, d = beside(p, "wild")
p.step(*d)
p._pick(1)
b = g.current_state
check(isinstance(b, WildBattleState), f"BATTLE opens the battle screen ({type(b).__name__})")
check(b.play_state_data.get("dungeon"), "the battle knows to come back to the map")
b.on_flee_complete()
check(g.current_state is p and p.mode == "MAP", f"fled: back to the same walk ({type(g.current_state).__name__})")
check(m not in p.run.floor.movers, "the wild Pokemon from the battle is gone")
frames(p, 3)

# trainers: bump -> trainer battle; beaten -> gone (Route 3's: Route 1 has none)
p = kanto("KANTO_ROUTE_3", came="PEWTER_CITY")
t, d = beside(p, "trainer")
p.step(*d)
check(type(g.current_state).__name__ in ("TrainerIntroState", "TrainerBattleState", "BattleTransitionState"),
      f"bumping a trainer starts a trainer battle ({type(g.current_state).__name__})")
story.mark_trainer_defeated("KANTO_ROUTE_3", t.payload[0])
back = PlayState(g, restore_data={"rounds_completed": 1})
check(back is p and t not in p.run.floor.movers, "a beaten trainer is gone when you come back")
g.change_state(p)
# line of sight
t = next(x for x in p.run.floor.movers if x.kind == "trainer")
t.facing = (1, 0)
f = p.run.floor
spot = None
for y in range(f.h):
    for x in range(f.w - 3):
        if all(f.walkable(x + k, y) and not f.occupied(x + k, y) for k in range(4)):
            spot = (x, y)
            break
    if spot:
        break
t.x, t.y = spot
p.run.player = (spot[0] + 3, spot[1])
ev = p.run.others_act()
check(any(e[0] == "spotted" for e in ev), "walking into a trainer's line of sight: spotted")

# items and Honey
p = kanto("KANTO_ROUTE_1")
f = p.run.floor
f.movers.clear()  # (no wild Pokemon jumping in)
px, py = p.run.player
d = next(dd for dd in core.DIRS if f.walkable(px + dd[0], py + dd[1]) and not f.occupied(px + dd[0], py + dd[1]))
f.items[(px + d[0], py + d[1])] = "POTION"
had = story.inventory.get("POTION", 0)
p.step(*d)
check(story.inventory.get("POTION", 0) == had + 1, "walking over an item picks it up")
frames(p, 10)  # (the step's walk animation)
story.inventory["HONEY"] = 1
check(p._scent_source() == "HONEY" and {"HONEY", "WAIT"} <= {b[1] for b in p._buttons()}
      and next(b for b in p._buttons() if b[1] == "HONEY")[4] and len(p._buttons()) >= 4,
      "HONEY in the Bag; the map's buttons: POKeMON, POKeDEX, HONEY (Jordan, 11-06: back), WAIT")
check(p.HONEY_PACK in [k for f in p.run.floors for k in f.items.values()] or
      any(p.HONEY_PACK in str(v) for f in p.run.floors for v in f.items.values()) or not p._get_wild_pool(p.area_data),
      "3 HONEY lying on the floor (where wild Pokemon live)")
from src.states.systems import BagState as _Bag
_bag = _Bag(g, p)
_bag._use_field_item("HONEY")  # used from the Bag: back to the map, and it draws them in
check(g.current_state is p, "HONEY from the Bag: back on the map")
talk(p)
for _ in range(600):   # (region/systems 11-23: the three walk up to you first, then the catch screen: walkup suite)
    if p.mode == "CATCH":
        break
    frames(p)
check(p.mode == "CATCH" and sum(x is not None for x in p.p_data) == 3,
      f"HONEY draws three wild Pokemon to catch ({[getattr(x, 'name', None) for x in p.p_data]})")
check(story.inventory.get("HONEY") == 0 and not p.uses_keyboard, "the Honey is used up; the catch screen takes the keys")
p.action_flee()
for _ in range(200):
    frames(p)
    talk(p, 2)
    if p.mode == "MAP":
        break
check(p.mode == "MAP" and g.current_state is p, "after the catch screen: back on the map")
p.scent_floor = -1
story.player_team[0].moves = ["SCRATCH", "SWEET-SCENT"]
check(p._scent_source() == "SWEET SCENT", "a Pokemon that knows Sweet Scent: once a floor")
p.scent_floor = p.run.index
check(p._scent_source() is None, "Sweet Scent used on this floor (and no Honey): nothing")

# leaving
p = kanto("KANTO_ROUTE_1")
f = p.run.floor
goal = [xy for xy, t in f.exits.items() if t == "VIRIDIAN_CITY"][0]
f.movers.clear()
for _ in range(400):
    if not isinstance(g.current_state, DungeonState):
        break
    f.movers.clear()  # (no wild Pokemon wandering in on the way)
    s = p.run.walk_toward(goal)
    p.anim = 0
    p.step(*s)
check(isinstance(g.current_state, AreaTransitionState), f"the far sign leads on ({type(g.current_state).__name__})")
for _ in range(400):
    g.current_state.update()
    if not isinstance(g.current_state, AreaTransitionState):
        break
    if getattr(g.current_state, "dialogue_box", None) and g.current_state.dialogue_box.visible:
        g.current_state.dialogue_box.is_finished = True
check(story.current_area_key == "VIRIDIAN_CITY" and story.last_area_key == "KANTO_ROUTE_1",
      f"now in {story.current_area_key}, came from {getattr(story, 'last_area_key', None)}")

# Route 2: entered from Viridian City, a TM spot
p = kanto("KANTO_ROUTE_2", came="VIRIDIAN_CITY")
check(isinstance(p, DungeonState), "Route 2 is a dungeon")
f = p.run.floor
check(len(f.tm_spots) == 1, f"Route 2 has its TM spot {list(f.tm_spots.values())}")
spot = list(f.tm_spots.values())[0]
f.tm_spots.clear()
px, py = p.run.player
d = next(dd for dd in core.DIRS if f.walkable(px + dd[0], py + dd[1]) and not f.occupied(px + dd[0], py + dd[1]))
f.tm_spots[(px + d[0], py + d[1])] = spot
owned = set(tms.owned(story))
p.step(*d)
got = story.story_flags.get(f"dungeon_tm_{spot}")
check(tms.is_tm(got) and got in tms.owned(story) and got not in owned, f"the TM spot gave {got}")
talk(p)
again = core.pick_tm(story.story_flags["dungeon_seed"], spot, tms.table(g), owned, 0)
check(again == got, "the same save picks the same TM there (no rerolls)")
p2 = kanto("KANTO_ROUTE_2", came="VIRIDIAN_CITY")
check(not p2.run.floor.tm_spots, "a taken TM spot stays taken")

# Viridian Forest: laid out from FireRed's own map (11-11), one floor; both its gates open onto Route 2, which runs on south to Viridian
p = kanto("VIRIDIAN_FOREST", came="KANTO_ROUTE_2")
check(p.run.n_floors == 1 and {"KANTO_ROUTE_2"} == set(p.run.floor.exits.values()),
      "Viridian Forest: one open map, out to Route 2 by its north gate and its south gate")
check(sum(m.kind == "trainer" for m in p.run.floor.movers) == 7, "...its five Bug Catchers (and the school kids), and Pokemon Yellow's two")
for mode in ("MAP", "CHOICE", "MATH", "THROW", "SPOTTED"):
    m = next((x for x in p.run.floor.movers if x.kind == ("trainer" if mode == "SPOTTED" else "wild")), None)
    p.encounter, p.mode = m, mode
    p.problem_str, p.correct_ans, p.options = p.generate_math_set(0, num_options=3)
    p.throw_result, p.throw_timer = "caught", 30
    try:
        p.draw()
        ok = True
    except Exception as e:
        ok = False
        print(e)
    check(ok, f"draws in {mode}")
p.mode = "MAP"

# the map replaces the route menu everywhere (Jordan, 11-05): no CLASSIC button
check(not any(b[1] == "CLASSIC" for b in p._buttons()), "no CLASSIC button: the map is the way")
story.current_area_key = "KANTO_ROUTE_1"
check(isinstance(PlayState(g), DungeonState) and type(PlayState(g, classic=True)) is PlayState,
      "PlayState(game) is the map; classic=True is the route menu underneath")


# Story gates on the map (Jordan, 11-06): what's in the way stands on the locked way out
_inv = dict(story.inventory)
story.inventory.pop("POKE_FLUTE", None)
_r12 = kanto("KANTO_ROUTE_12", came="LAVENDER_TOWN")
check(_r12._boss_spot() == (14, 70) and _r12.run.floor.exits.get((14, 70)) == "BOSS" and not any(
    m.kind == "figure" and m.payload.get("action") == "BOSS" for f in _r12.run.floors for m in f.movers),
      "Route 12: Snorlax asleep on the pier where FireRed has him, in the way south and west (11-11; not a figure somewhere else on the map)")
_r12._try_exit("BOSS")
check(_r12.dialogue_box.visible and "asleep" in " ".join(_r12.dialogue_box.text_lines), "walking into it: it's sound asleep")
frames(_r12, 2)
story.player_team = [mk(4)]
# (Rusturf Tunnel's cracked rock: dev/checks/hoenn_maps_body.py)
story.inventory.clear(); story.inventory.update(_inv)

# Overworld Pokemon (Everlasting X's following Pokemon): your partner and the wild ones walk on the map
_p = kanto("KANTO_ROUTE_1")
_img = _p._follower_img(story.player_team[0], (0, 1))
check(_img is not None and _img.get_height() >= 40, "the partner's overworld sprite, at the trainer's scale")

# Hyperspace Lumiose (Jordan, 11-06): a donut opens a zone; big open floors, a clock
from src.world import donuts as _dn
_d = _dn.bake(["PECHA_BERRY"] * 3)
check(_d["recipe"] == "perfect" and _d["stars"] == 1 and _dn.zone_for(g, _d) == "HYPERSPACE_VERDANT",
      "a Perfect Sweet donut (1 star) opens the Verdant Rift")
_r = _dn.bake(["CHERI_BERRY", "PECHA_BERRY", "ASPEAR_BERRY"])
check(_r["recipe"] == "rainbow" and _r["bonus_seconds"] == 30, "a Rainbow donut: 30 more seconds a floor")
check(_dn.zone_for(g, _dn.bake(["CHESTO_BERRY"] * 3)) is None and
      _dn.zone_for(g, _dn.bake(["CHESTO_BERRY", "NANAB_BERRY", "CHESTO_BERRY"], burnt=False) | {"stars": 2}) == "HYPERSPACE_FROST",
      "the Frost Rift needs 2 stars (star berries)")
story.player_team = [mk(4)]
story.player_team[0].level = 10  # (under the level cap: the win's XP shows)
story.story_flags[_dn.FLAG] = _d
story.current_area_key = "HYPERSPACE_VERDANT"
_h = PlayState(g); g.change_state(_h)
check(type(_h).__name__ == "HyperspaceState" and _h.run.fog is False and _h.run.floor.w >= 40
      and _h._enemies() and story.story_flags.get(_dn.FLAG) is None, "into the Verdant Rift: big, open, the donut eaten")
check(_h._stairs_blocked(), "the stairs wait until the floor is clear")
_w = next(m for m in _h.run.floor.movers if m.kind == "wild")
_h._meet_wild(_w)
check(_h.mode == "CHOICE", "a wild one: the usual catch-or-battle choice (battles are turn-based, Jordan 11-07)")
_h.mode, _h.encounter = "MAP", None
_h.clock = 1
_h.update()
check(_h.dialogue_box.visible, "the clock runs out: back to the hub")


def fight(b, n=8000):
    """Play a turn-based battle as a player would: each turn the first move and the right answer; tap through
    its text. Returns how many math questions were answered."""
    asked = 0
    for _k in range(n):
        if g.current_state is not b:
            break
        if b.phase == "SWITCH_PROMPT" and b.btn_no.visible and b.btn_no.callback:
            b.btn_no.callback()  # ("Change Pokemon?" NO, as a player would)
        elif b.phase == "MENU" and not b.dialogue_box.visible:
            b.open_move_menu()
            b.choose_move(b.move_buttons[0].text.replace(" ", "-"))
            b.math_ui.on_click(b.options.index(b.correct_ans))
            asked += 1
        elif b.dialogue_box.visible:
            b.dialogue_box.is_finished = True
            if b.phase in ("OUTRO", "VICTORY_TEXT", "REWARD_TEXT"):
                b.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            else:
                _cb = b.dialogue_box.callback
                if _cb:
                    b.dialogue_box.callback = None
                    _cb()
                else:
                    b.dialogue_box.advance()
        b.feedback_timer = 0
        if g.current_state is b:
            b.update()
            b.draw()
    return asked


# Options > BATTLE STYLE (Jordan, 11-07): CLASSIC or OVERWORLD, trainer battles only; the same turns and math
from src.states.battle import TrainerBattleState, TrainerIntroState, WildBattleState
story.battle_style = "TRADITIONAL"
_p = kanto("KANTO_ROUTE_3", came="PEWTER_CITY")
_t = next((m for f in _p.run.floors for m in f.movers if m.kind == "trainer"), None)
_p._battle_trainer(_t)
check(isinstance(g.current_state, TrainerIntroState), "CLASSIC: a trainer battle on the battle screen (its intro first)")
story.battle_style = "OVERWORLD"
_p = kanto("KANTO_ROUTE_3", came="PEWTER_CITY")
_ow = mk(6)  # (a sure win: a Lv 100 Charizard; two Lv 2s keep the team's level, which foes follow, near 51)
_ow.level = 100
_ow.moves = ["FLAMETHROWER", "AIR-SLASH"]
_ow.heal_full()
story.player_team = [_ow, mk(132), mk(128)]  # (Ditto, Tauros: their shared XP starts no evolution)
for _pp in story.player_team[1:]:
    _pp.level = 2
    _pp.heal_full()
_t = next((m for f in _p.run.floors for m in f.movers if m.kind == "trainer"), None)
_money = story.money
from src.pokemon import items as _it
from src.states.overworld.route_encounters import _story_badges
_prize = _it.trainer_prize(_story_badges(g))
_inv0, _bl = {k: story.inventory.get(k, 0) for k in _prize}, story.balls_left
_p._battle_trainer(_t)
check(_p.dialogue_box.visible and g.current_state is _p, "OVERWORLD: the trainer's lines first, in the map's text box")
while _p.dialogue_box.visible:
    _p.dialogue_box.advance()
    _p.update()
_b = g.current_state
check(isinstance(_b, TrainerBattleState) and getattr(_b, "overworld", None) is not None,
      "...then the turn-based battle, drawn on the map")
_ov = _b.overworld
check(_ov.spot != _ov.mine and _p.run.player not in (_ov.spot, _ov.mine) and (_t.x, _t.y) not in (_ov.spot, _ov.mine),
      "...the two Pokemon on their own tiles (no one standing on anyone)")
_asked = fight(_b)
check(_asked >= 1 and g.current_state is _p and story.is_trainer_defeated("KANTO_ROUTE_3", _t.payload[0])
      and story.money > _money, f"...a math question every turn ({_asked}), won: back on the map, the trainer beaten, paid")
check(all(story.inventory.get(k, 0) == _inv0[k] + n for k, n in _prize.items()) and story.balls_left == _bl,
      f"...a route trainer's prize: healing items ({_prize}), no Poke Balls")
check(_it.route_rewards(1, {"balls": 3}) == {"POTION": 2, "balls": 0}
      and _it.route_rewards(3, None) == {"POTION": 1, "SUPER_POTION": 1, "balls": 0}
      and _it.route_rewards(5, {"balls": 2, "TM_X": 1}) == {"TM_X": 1, "SUPER_POTION": 2, "REVIVE": 1, "balls": 0}
      and _it.route_rewards(8, {}) == {"HYPER_POTION": 2, "REVIVE": 1, "balls": 0}
      and not any("MAX_REVIVE" in _it.route_rewards(b, {}) for b in range(9)),
      "prizes grow with the badges: Potions, Super Potions and Revives, Hyper Potions (never a Max Revive)")
# (Jordan 11-24: the important story battles stay on the battle screen - Leaders, bosses, the rival, the League)
from src.states.overworld.dungeon import DungeonState as _DS
check(all(_DS.story_battle(i) for i in ({"class": "RIVAL"}, {"class": "ROCKET_LEADER"}, {"class": "GYM_LEADER"}, {"class": "ELITE_FOUR"},
                                       {"class": "CHAMPION"}, {"class": "GRUNT", "is_boss_battle": True}, {"class": "ADMIN", "villain": "leader"}))
      and not _DS.story_battle({"class": "YOUNGSTER"}), "story battles: Leaders, bosses, the rival, the Elite Four and the Champion (not a Youngster)")
_p = kanto("KANTO_ROUTE_3", came="PEWTER_CITY")
_t = next((m for f in _p.run.floors for m in f.movers if m.kind == "trainer" and not story.is_trainer_defeated("KANTO_ROUTE_3", m.payload[0])), None)
if _t is not None:
    _t.payload = (_t.payload[0], dict(_t.payload[1] or {}, **{"class": "RIVAL"}))
    _p._battle_trainer(_t)
    check(isinstance(g.current_state, TrainerIntroState) and not _p.dialogue_box.visible,
          f"OVERWORLD: a rival on a route map still battles on the battle screen ({type(g.current_state).__name__})")
_p = kanto("KANTO_ROUTE_1")
_ww, _ = beside(_p, "wild")
_p._meet_wild(_ww)
check(_p.mode == "CHOICE", "OVERWORLD: a wild one is still the catch-or-battle choice")
_p._pick(1)
check(isinstance(g.current_state, WildBattleState) and getattr(g.current_state, "overworld", None) is not None,
      "...and its battle is on the map too")
story.battle_style = "TRADITIONAL"

# Mega Evolution on the map (Legends: Z-A): a minute of walking, into battles that way, then the Key Stone rests
from src.pokemon import mega_clock, forms as _forms
from src.states.systems import PokemonPartyMenuState
_p = kanto("KANTO_ROUTE_3", came="PEWTER_CITY")
story.player_team = [mk(3)]
_v = story.player_team[0]
_v.level = 60
_v.moves = ["PETAL-BLIZZARD", "SLUDGE-BOMB"]
_v.heal_full()
story.inventory["MEGA_BRACELET"] = story.inventory["VENUSAURITE"] = 1
_img0 = _v.image
g.rt_mega = None
_mb = _p._map_mega_button()
check(_mb is not None and _mb[4] and _mb in _p._buttons(), "on the map: MEGA (the Venusaur following you can)")
_p.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=_mb[0].center)])
check(_v.form == "mega" and mega_clock.active(g), "...tapped: it Mega Evolves right there")
_mb = _p._map_mega_button()
check(_mb is not None and not _mb[4] and "left" in _mb[5], f"...the button counts its minute down ({_mb and _mb[5]})")
_party = PokemonPartyMenuState(g, _p, context="normal")
g.change_state(_party)
_party.update(); _party.draw()
check(_v.image is not _img0 and _v.display_name.upper().startswith("MEGA"), "the party menu shows the Mega")
g.change_state(_p)
_t = next((m for f in _p.run.floors for m in f.movers if m.kind == "trainer"), None)
_p._battle_trainer(_t)  # (CLASSIC)
_intro = g.current_state
_b = _intro.next_state
check(_b.mega_used["player"], "a battle: it comes in a Mega (that's the battle's one Mega)")
g.change_state(_b)
_left = mega_clock.state(g)["left"]
for _k in range(60):
    mega_clock.tick(g)
check(mega_clock.state(g)["left"] == _left, "...its minute waits while you battle")
fight(_b)
check(g.current_state is _p and _v.form == "mega" and mega_clock.active(g), "the battle won: still a Mega on the map")
for _k in range(mega_clock.SECONDS * 25):
    mega_clock.tick(g)
check(_v.form == "normal" and mega_clock.cooling(g), "a minute on: back to normal, the Key Stone resting")
check(story._pokemon_record(_v)["form"] == "normal", "(saved as its normal form)")
for _k in range(mega_clock.COOLDOWN * 25 + 2):
    mega_clock.tick(g)
check(not mega_clock.cooling(g), "30 seconds on: MEGA is ready again")
g.rt_mega = None
story.player_team = [mk(25), _v]
check(_p._map_mega_button() is None, "a Pokemon with no Mega Stone following you: no MEGA button")
# the POKEMON list on the map: tap one to have it follow you; right-click (or its potion) heals it, strongest first
_p.qp_open = True
_pk = story.player_team[1]
_p.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=_p._qp_rects()[1].center)])
check(story.player_team[0] is _pk and _p.lead() is _pk and not _p.qp_open, "on the map: tap one, it follows you")
story.inventory.update({"POTION": 3, "HYPER_POTION": 1})
_pk.current_hp = 5
_p.qp_open = True
_p.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=_p._qp_rects()[0].center)])
check(story.inventory.get("HYPER_POTION", 0) == 0 and story.inventory.get("POTION") == 3 and _pk.current_hp > 5,
      "right-click: healed with the strongest potion (the Hyper Potion)")
_pk.current_hp = 5
_p.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=_p._qp_heal_rect(_p._qp_rects()[0]).center)])
check(story.inventory.get("POTION") == 2 and _pk.current_hp > 5, "...or tap its potion (now a Potion)")
story.player_team[1].current_hp = 0
story.inventory["REVIVE"] = 1
_p._quick_heal(1)
check(story.player_team[1].current_hp > 0 and not story.inventory.get("REVIVE"), "a fainted one: a Revive")
_p.qp_open = False
story.inventory.pop("VENUSAURITE", None); story.inventory.pop("MEGA_BRACELET", None)
story.battle_style = "TRADITIONAL"

# playtest fixes (Jordan, 11-07): a story battle on the map brings you back where you were
story.story_flags.pop("mt_moon_nerd_defeated", None)
_mm = kanto("MT_MOON", came="KANTO_ROUTE_3")
story.player_team[0].level = 40
while _mm.run.index < _mm.run.n_floors - 1:
    _mm._descend()
_nerd = next(m for m in _mm.run.floor.movers if m.kind == "figure" and m.payload.get("text") == "SUPER NERD")
_mm.run.player = _spot = (_nerd.x, _nerd.y - 1)
_mm._get_route_callback(_nerd.payload)()
_b = g.current_state.next_state
_b.player_won = True
_b.exit_battle()
check(g.current_state is _mm and _mm.run.index == _mm.run.n_floors - 1 and _mm.run.player == _spot,
      "the Super Nerd beaten: back where you were (not Mt. Moon's entrance)")
_fm = [m for m in _mm.run.floor.movers if m.kind == "figure" and "FOSSIL" in str(m.payload.get("text"))]   # (11-14: FireRed's item balls lie about too)
_fos = sorted(m.payload.get("text") for m in _fm)
check(_fos == ["TAKE DOME FOSSIL", "TAKE HELIX FOSSIL"]
      and max(abs(a.x - b.x) + abs(a.y - b.y) for a in _fm for b in _fm) <= 4, "...the two fossils side by side to pick from")
story.story_flags.pop("defeated_rival_nugget_bridge", None)
_bd = dict(story.badges)
story.badges["KANTO"] = ["BOULDER"]
_r24 = kanto("KANTO_ROUTE_24", came="CERULEAN_CITY")
_riv = next(m for f in _r24.run.floors for m in f.movers if m.kind == "figure" and m.payload.get("action") == "ARRIVAL")
_r24._use_figure(_riv)
_b = g.current_state.next_state
check(_b.background is not None, "the rival after Nugget Bridge: a battle background")
_b.player_won = True
_b.exit_battle()
check(g.current_state is _r24, "...and back on Route 24 where you were")
story.badges.clear(); story.badges.update(_bd)
_p = kanto("KANTO_ROUTE_3", came="PEWTER_CITY")
story.tracked_mission = None
check(_p._journal_rect() is not None and _p._minimap_rect().y > _p._journal_rect().bottom,
      "the Journal's mission stays on screen under MENU (the mini-map under it)")


print(f"##### {fails} failures")
